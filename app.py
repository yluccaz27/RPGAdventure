import os
import time
import uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Character, Equipment, BaseBuilding
from game_logic import (
    CLASSES,
    ARMAS_INICIAIS,
    CONFIG_TREINO,
    REGIOES_MAPA,
    MASMORRA_ANDAR_CHEFES,
    ROLETA_FATIAS,
    calcular_status_totais,
    verificar_level_up,
    gerar_inimigo_onda,
    gerar_itens_loja,
    gerar_item_aleatorio,
    calcular_custo_reroll,
    calcular_custo_atributo,
    obter_poeira_desmontar,
    calcular_custo_upgrade,
    random
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "rpg_super_legendary_database_secret_key")

# PREPARAÇÃO PARA DEPLOY: DATABASE_URL COM FALLBACK PARA SQLITE
database_url = os.environ.get("DATABASE_URL", "sqlite:///rpg.db")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

# FLASK-LOGIN
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# INICIALIZAÇÃO AUTOMÁTICA DAS TABELAS
with app.app_context():
    db.create_all()

# GERENCIAMENTO DE RECURSOS PASSIVOS NO BANCO
def sincronizar_esconderijo_db(character):
    if not character.building:
        b = BaseBuilding(character_id=character.id, ultima_coleta=int(time.time()))
        db.session.add(b)
        db.session.commit()
        return

    b = character.building
    agora = int(time.time())
    tempo_passado = max(0, agora - (b.ultima_coleta or agora))

    if tempo_passado > 0:
        mina_lvl = b.nivel_mina or 1
        taxa_moedas_segundo = (mina_lvl * 60) / 3600.0
        moedas_novas = int(tempo_passado * taxa_moedas_segundo)

        lab_lvl = b.nivel_lab or 1
        taxa_pocoes_segundo = (lab_lvl * 1.0) / 3600.0
        pocoes_novas = int(tempo_passado * taxa_pocoes_segundo)

        b.moedas_acumuladas = min(2000 * mina_lvl, (b.moedas_acumuladas or 0) + moedas_novas)
        b.pocoes_acumuladas = min(10 * lab_lvl, (b.pocoes_acumuladas or 0) + pocoes_novas)
        b.ultima_coleta = agora
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()

def empacotar_estado_jogador(user, character):
    if not character:
        return {
            "success": True,
            "authenticated": True,
            "username": user.username,
            "game_started": False,
            "classes": CLASSES,
            "armas_iniciais": ARMAS_INICIAIS
        }

    sincronizar_esconderijo_db(character)
    char_dict = character.to_dict()

    # Estado transitório de aventura na sessão
    adv_sess = session.get("aventura", {
        "ativa": False,
        "onda": 1,
        "status": "idle",
        "espolio_moedas": 0,
        "espolio_xp": 0,
        "bonus_temp": {"ataque": 0, "defesa": 0, "hp_max": 0},
        "inimigo": None,
        "ultimo_combate": None
    })

    # Estado transitório de masmorra na sessão
    masm_sess = session.get("masmorra", {
        "ativa": False,
        "andar": character.andar_masmorra or 1,
        "status": "idle",
        "chefe": None,
        "ultimo_combate": None
    })

    temp_buffs = adv_sess["bonus_temp"] if adv_sess.get("ativa") else None
    totais = calcular_status_totais(char_dict, temp_buffs)

    # Ajuste do HP atual no banco se exceder máximo total
    if character.hp_atual > totais["hp_max"]:
        character.hp_atual = totais["hp_max"]
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()

    char_dict["ataque_total"] = totais["ataque"]
    char_dict["defesa_total"] = totais["defesa"]
    char_dict["hp_max_total"] = totais["hp_max"]
    char_dict["esquiva_total"] = totais["esquiva"]
    char_dict["critico_total"] = totais["critico"]
    char_dict["temp_buffs"] = temp_buffs or {"ataque": 0, "defesa": 0, "hp_max": 0}
    char_dict["passiva"] = CLASSES.get(character.classe, {}).get("passiva", "")
    char_dict["icon"] = CLASSES.get(character.classe, {}).get("icon", "🛡️")
    char_dict["imagem"] = CLASSES.get(character.classe, {}).get("imagem", "/static/images/classes/guerreiro.svg")

    # Custos de Academia de Atributos
    custos_academia = {
        "forca": calcular_custo_atributo(character.forca or 0),
        "destreza": calcular_custo_atributo(character.destreza or 0),
        "vitalidade": calcular_custo_atributo(character.vitalidade or 0),
        "mente": calcular_custo_atributo(character.mente or 0)
    }

    # Treino AFK
    treino_data = {
        "ativo": character.treino_ativo or False,
        "chave": character.treino_chave,
        "nome": character.treino_nome or "",
        "timestamp_inicio": character.tempo_treino_inicio or 0,
        "duracao_segundos": character.tempo_treino_duracao or 0,
        "timestamp_fim": character.tempo_treino_fim or 0,
        "recompensas": CONFIG_TREINO.get(character.treino_chave, {}).get("bonus_stats", {}) if character.treino_chave else {}
    }

    # Loja gerada para o usuário (persistida na sessão ou gerada)
    loja_itens = session.get("loja_itens")
    if not loja_itens:
        loja_itens = gerar_itens_loja(character.nivel)
        session["loja_itens"] = loja_itens

    custo_reroll = calcular_custo_reroll(character.loja_reroll_count or 0)

    logs = session.get("logs", [f"Bem-vindo de volta, {character.nome}! Seu herói foi carregado do banco de dados com sucesso."])

    return {
        "success": True,
        "authenticated": True,
        "username": user.username,
        "game_started": True,
        "player": char_dict,
        "custos_academia": custos_academia,
        "aventura": adv_sess,
        "masmorra": masm_sess,
        "masmorra_catalogo": MASMORRA_ANDAR_CHEFES,
        "roleta_fatias": ROLETA_FATIAS,
        "treino": treino_data,
        "loja": {
            "reroll_count": character.loja_reroll_count or 0,
            "custo_reroll": custo_reroll,
            "itens": loja_itens,
            "preco_pocao": 20
        },
        "logs": logs[:40],
        "classes": CLASSES,
        "armas_iniciais": ARMAS_INICIAIS,
        "opcoes_treino": CONFIG_TREINO,
        "regioes_mapa": REGIOES_MAPA,
        "tempo_servidor": int(time.time())
    }

# ==========================================================
# ROTAS PRINCIPAIS & AUTENTICAÇÃO (FLASK-LOGIN)
# ==========================================================
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"success": False, "message": "Preencha o usuário e a senha."}), 400

    if len(username) < 3 or len(password) < 4:
        return jsonify({"success": False, "message": "O usuário deve ter ao menos 3 caracteres e a senha ao menos 4."}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"success": False, "message": "Este nome de usuário já está cadastrado."}), 400

    try:
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        login_user(user, remember=True)
        session["logs"] = [f"Conta '{username}' criada com sucesso! Crie seu herói para desbravar o reino."]
        return jsonify({"success": True, "message": "Registrado com sucesso!", "username": username})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Erro ao registrar: {str(e)}"}), 500

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({"success": False, "message": "Usuário ou senha incorretos."}), 401

    login_user(user, remember=True)
    session["logs"] = [f"Bem-vindo de volta, {username}! Dados carregados do banco de dados."]
    return jsonify({"success": True, "message": "Login efetuado com sucesso!", "username": username})

@app.route("/logout", methods=["GET", "POST"])
def logout():
    session.clear()
    logout_user()
    return jsonify({"success": True, "message": "Desconectado com sucesso."})

@app.route("/api/me", methods=["GET"])
def api_me():
    if current_user.is_authenticated:
        return jsonify({"authenticated": True, "username": current_user.username})
    return jsonify({"authenticated": False, "username": None})

# ==========================================================
# API DE ESTADO
# ==========================================================
@app.route("/api/estado", methods=["GET"])
def api_estado():
    if not current_user.is_authenticated:
        return jsonify({
            "success": True,
            "authenticated": False,
            "game_started": False,
            "classes": CLASSES,
            "armas_iniciais": ARMAS_INICIAIS,
            "opcoes_treino": CONFIG_TREINO,
            "regioes_mapa": REGIOES_MAPA,
            "roleta_fatias": ROLETA_FATIAS,
            "masmorra_catalogo": MASMORRA_ANDAR_CHEFES,
            "tempo_servidor": int(time.time())
        })

    character = current_user.character
    return jsonify(empacotar_estado_jogador(current_user, character))

# ==========================================================
# CRIAÇÃO DE PERSONAGEM NO BANCO DE DADOS
# ==========================================================
@app.route("/api/criar", methods=["POST"])
def api_criar():
    if not current_user.is_authenticated:
        return jsonify({"success": False, "message": "Você precisa estar conectado para criar um herói."}), 401

    if current_user.character:
        return jsonify({"success": False, "message": "Você já possui um herói cadastrado."}), 400

    data = request.get_json() or {}
    nome = data.get("nome", "").strip()
    classe = data.get("classe", "")
    arma = data.get("arma", "")

    if not nome or classe not in CLASSES or arma not in ARMAS_INICIAIS:
        return jsonify({"success": False, "message": "Dados de criação inválidos."}), 400

    try:
        classe_info = CLASSES[classe]
        arma_info = ARMAS_INICIAIS[arma]

        char = Character(
            user_id=current_user.id,
            nome=nome,
            classe=classe,
            nivel=1,
            xp=0,
            xp_proximo=60,
            moedas=80,
            poeira_arcana=15,
            pocoes=3,
            giros_gratis_roleta=1,
            hp_max_base=classe_info["hp_base"],
            hp_atual=classe_info["hp_base"],
            ataque_base=classe_info["ataque_base"],
            defesa_base=classe_info["defesa_base"],
            esquiva_base=classe_info["esquiva_base"],
            critico_base=classe_info["critico_base"],
            regiao_atual="floresta",
            andar_masmorra=1,
            masmorras_completadas=0
        )
        db.session.add(char)
        db.session.flush()

        # Adiciona a arma inicial equipada
        eq_arma = Equipment(
            character_id=char.id,
            item_key=arma_info["id"],
            nome=arma_info["nome"],
            tipo="arma",
            raridade=arma_info["raridade"],
            bonus_ataque=arma_info["bonus_ataque"],
            bonus_defesa=arma_info.get("bonus_defesa", 0),
            bonus_hp=arma_info.get("bonus_hp", 0),
            bonus_critico=arma_info.get("bonus_critico", 0),
            bonus_esquiva=arma_info.get("bonus_esquiva", 0),
            preco=arma_info["preco"],
            imagem=arma_info["imagem"],
            descricao=arma_info["descricao"],
            nivel_upgrade=0,
            equipado=True
        )
        db.session.add(eq_arma)

        # Adiciona o edifício inicial do esconderijo
        building = BaseBuilding(
            character_id=char.id,
            nivel_mina=1,
            nivel_lab=1,
            ultima_coleta=int(time.time()),
            moedas_acumuladas=0,
            pocoes_acumuladas=0
        )
        db.session.add(building)

        db.session.commit()
        session["logs"] = [f"Herói {nome} ({classe}) despertou com a sua {arma}! Gravado com sucesso no banco de dados."]
        return jsonify(empacotar_estado_jogador(current_user, char))

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Erro no banco ao criar herói: {str(e)}"}), 500

# ==========================================================
# ACADEMIA DE ATRIBUTOS COM COMMIT
# ==========================================================
@app.route("/api/atributos/upar", methods=["POST"])
def api_atributos_upar():
    if not current_user.is_authenticated or not current_user.character:
        return jsonify({"success": False, "message": "Personagem não encontrado."}), 400

    char = current_user.character
    data = request.get_json() or {}
    atributo = data.get("atributo")

    if atributo not in ["forca", "destreza", "vitalidade", "mente"]:
        return jsonify({"success": False, "message": "Atributo inválido."}), 400

    valor_atual = getattr(char, atributo, 0) or 0
    custo = calcular_custo_atributo(valor_atual)

    if char.moedas < custo:
        return jsonify({"success": False, "message": f"Moedas insuficientes ({custo} 🪙)."}), 400

    try:
        char.moedas -= custo
        setattr(char, atributo, valor_atual + 1)
        
        if atributo == "vitalidade":
            char.hp_atual = min(char.hp_max_base + 8, char.hp_atual + 8)

        db.session.commit()
        logs = session.get("logs", [])
        logs.insert(0, f"💪 [ACADEMIA] Você treinou {atributo.capitalize()} por {custo} 🪙! (Nível {valor_atual + 1})")
        session["logs"] = logs
        return jsonify(empacotar_estado_jogador(current_user, char))
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Erro ao aprimorar atributo: {str(e)}"}), 500

# ==========================================================
# FERREIRO: DESMONTAR E UPGRADE NO BANCO
# ==========================================================
@app.route("/api/ferreiro/desmontar", methods=["POST"])
def api_ferreiro_desmontar():
    if not current_user.is_authenticated or not current_user.character:
        return jsonify({"success": False, "message": "Personagem não encontrado."}), 400

    char = current_user.character
    data = request.get_json() or {}
    item_id = data.get("item_id")

    eq = None
    if isinstance(item_id, int) or (isinstance(item_id, str) and item_id.isdigit()):
        eq = Equipment.query.filter_by(character_id=char.id, id=int(item_id), equipado=False).first()
    if not eq:
        eq = Equipment.query.filter_by(character_id=char.id, item_key=str(item_id), equipado=False).first()
    if not eq:
        return jsonify({"success": False, "message": "Item não encontrado no inventário."}), 404

    try:
        poeira_ganha = obter_poeira_desmontar(eq.raridade)
        char.poeira_arcana = (char.poeira_arcana or 0) + poeira_ganha
        db.session.delete(eq)
        db.session.commit()

        logs = session.get("logs", [])
        logs.insert(0, f"🔨 [FERREIRO] Você desmontou {eq.nome} e extraiu +{poeira_ganha} 🔮 Poeira Arcana!")
        session["logs"] = logs
        return jsonify(empacotar_estado_jogador(current_user, char))
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Erro ao desmontar item: {str(e)}"}), 500

@app.route("/api/ferreiro/upgrade", methods=["POST"])
def api_ferreiro_upgrade():
    if not current_user.is_authenticated or not current_user.character:
        return jsonify({"success": False, "message": "Personagem não encontrado."}), 400

    char = current_user.character
    data = request.get_json() or {}
    slot = data.get("slot")
    item_id = data.get("item_id")

    eq = None
    if slot:
        eq = Equipment.query.filter_by(character_id=char.id, tipo=slot, equipado=True).first()
    elif item_id:
        eq = Equipment.query.filter_by(character_id=char.id, item_key=item_id).first()

    if not eq:
        return jsonify({"success": False, "message": "Equipamento não encontrado."}), 404

    if eq.nivel_upgrade >= 10:
        return jsonify({"success": False, "message": "Este item já atingiu a melhoria máxima (+10)!"}), 400

    custo_poeira, custo_moedas = calcular_custo_upgrade(eq.nivel_upgrade)

    if (char.poeira_arcana or 0) < custo_poeira:
        return jsonify({"success": False, "message": f"Poeira Arcana insuficiente ({custo_poeira} 🔮)."}), 400

    if char.moedas < custo_moedas:
        return jsonify({"success": False, "message": f"Moedas insuficientes ({custo_moedas} 🪙)."}), 400

    try:
        char.poeira_arcana -= custo_poeira
        char.moedas -= custo_moedas
        eq.nivel_upgrade += 1

        nome_base = eq.nome.split(" +")[0]
        eq.nome = f"{nome_base} +{eq.nivel_upgrade}"

        db.session.commit()
        logs = session.get("logs", [])
        logs.insert(0, f"✨ [FERREIRO] Sucesso! {eq.nome} aprimorado para +{eq.nivel_upgrade} (+10% em todos os status)!")
        session["logs"] = logs
        return jsonify(empacotar_estado_jogador(current_user, char))
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Erro no upgrade: {str(e)}"}), 500

# ==========================================================
# EQUIPAR, DESEQUIPAR E VENDER
# ==========================================================
@app.route("/api/equipar", methods=["POST"])
def api_equipar():
    if not current_user.is_authenticated or not current_user.character:
        return jsonify({"success": False, "message": "Personagem não encontrado."}), 400

    char = current_user.character
    data = request.get_json() or {}
    acao = data.get("acao")

    try:
        if acao == "equipar":
            item_id = data.get("item_id")
            item_alvo = Equipment.query.filter_by(character_id=char.id, item_key=item_id).first()
            if not item_alvo:
                return jsonify({"success": False, "message": "Item não encontrado."}), 404

            slot = item_alvo.tipo
            # Desequipa item atual do mesmo slot
            item_atual = Equipment.query.filter_by(character_id=char.id, tipo=slot, equipado=True).first()
            if item_atual:
                item_atual.equipado = False

            item_alvo.equipado = True
            db.session.commit()
            logs = session.get("logs", [])
            logs.insert(0, f"🛡️ Você equipou: {item_alvo.nome} no slot {slot}!")
            session["logs"] = logs
            return jsonify(empacotar_estado_jogador(current_user, char))

        elif acao == "desequipar":
            slot = data.get("slot")
            item_atual = Equipment.query.filter_by(character_id=char.id, tipo=slot, equipado=True).first()
            if not item_atual:
                return jsonify({"success": False, "message": "Nenhum item equipado neste slot."}), 400

            item_atual.equipado = False
            db.session.commit()
            logs = session.get("logs", [])
            logs.insert(0, f"📦 Você desequipou: {item_atual.nome} e guardou na mochila.")
            session["logs"] = logs
            return jsonify(empacotar_estado_jogador(current_user, char))

        return jsonify({"success": False, "message": "Ação inválida."}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Erro ao equipar: {str(e)}"}), 500

@app.route("/api/vender", methods=["POST"])
def api_vender():
    if not current_user.is_authenticated or not current_user.character:
        return jsonify({"success": False, "message": "Personagem não encontrado."}), 400

    char = current_user.character
    data = request.get_json() or {}
    item_id = data.get("item_id")

    eq = None
    if isinstance(item_id, int) or (isinstance(item_id, str) and item_id.isdigit()):
        eq = Equipment.query.filter_by(character_id=char.id, id=int(item_id), equipado=False).first()
    if not eq:
        eq = Equipment.query.filter_by(character_id=char.id, item_key=str(item_id), equipado=False).first()
    if not eq:
        return jsonify({"success": False, "message": "Item não encontrado no inventário."}), 404

    try:
        valor_venda = max(5, int(eq.preco * 0.5))
        char.moedas += valor_venda
        nome_item = eq.nome
        db.session.delete(eq)
        db.session.commit()

        logs = session.get("logs", [])
        logs.insert(0, f"💰 Você vendeu {nome_item} por {valor_venda} 🪙 (50% do valor).")
        session["logs"] = logs
        return jsonify(empacotar_estado_jogador(current_user, char))
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Erro ao vender item: {str(e)}"}), 500

# ==========================================================
# LOJA COM PERSISTÊNCIA DE ITENS COMPRADOS
# ==========================================================
@app.route("/api/loja", methods=["POST"])
def api_loja():
    if not current_user.is_authenticated or not current_user.character:
        return jsonify({"success": False, "message": "Personagem não encontrado."}), 400

    char = current_user.character
    data = request.get_json() or {}
    acao = data.get("acao")

    try:
        if acao == "reroll":
            custo = calcular_custo_reroll(char.loja_reroll_count or 0)
            if char.moedas < custo:
                return jsonify({"success": False, "message": f"Moedas insuficientes ({custo} 🪙)."}), 400

            char.moedas -= custo
            char.loja_reroll_count = (char.loja_reroll_count or 0) + 1
            db.session.commit()

            novos_itens = gerar_itens_loja(char.nivel)
            session["loja_itens"] = novos_itens

            logs = session.get("logs", [])
            texto_custo = "GRÁTIS" if custo == 0 else f"{custo} 🪙"
            logs.insert(0, f"🔄 Loja atualizada ({texto_custo})!")
            session["logs"] = logs
            return jsonify(empacotar_estado_jogador(current_user, char))

        elif acao == "comprar":
            item_id = data.get("item_id")
            loja_itens = session.get("loja_itens", [])
            item_selecionado = next((i for i in loja_itens if i["id"] == item_id), None)

            if not item_selecionado:
                return jsonify({"success": False, "message": "Item não encontrado na loja."}), 404

            if char.moedas < item_selecionado["preco"]:
                return jsonify({"success": False, "message": "Moedas insuficientes."}), 400

            char.moedas -= item_selecionado["preco"]
            session["loja_itens"] = [i for i in loja_itens if i["id"] != item_id]

            slot = item_selecionado["tipo"]
            # Desequipa o item antigo do mesmo slot
            item_antigo = Equipment.query.filter_by(character_id=char.id, tipo=slot, equipado=True).first()
            if item_antigo:
                item_antigo.equipado = False

            # Cria e equipa o novo item no banco
            novo_eq = Equipment(
                character_id=char.id,
                item_key=item_selecionado["id"],
                nome=item_selecionado["nome"],
                tipo=item_selecionado["tipo"],
                raridade=item_selecionado["raridade"],
                bonus_ataque=item_selecionado.get("bonus_ataque", 0),
                bonus_defesa=item_selecionado.get("bonus_defesa", 0),
                bonus_hp=item_selecionado.get("bonus_hp", 0),
                bonus_critico=item_selecionado.get("bonus_critico", 0),
                bonus_esquiva=item_selecionado.get("bonus_esquiva", 0),
                preco=item_selecionado["preco"],
                imagem=item_selecionado["imagem"],
                descricao=item_selecionado["descricao"],
                nivel_upgrade=0,
                equipado=True
            )
            db.session.add(novo_eq)
            db.session.commit()

            logs = session.get("logs", [])
            logs.insert(0, f"🛍️ Você comprou e equipou: {item_selecionado['nome']} ({item_selecionado['raridade']})!")
            session["logs"] = logs
            return jsonify(empacotar_estado_jogador(current_user, char))

        elif acao == "comprar_pocao":
            custo_pocao = 20
            if char.moedas < custo_pocao:
                return jsonify({"success": False, "message": "Moedas insuficientes."}), 400

            char.moedas -= custo_pocao
            char.pocoes = (char.pocoes or 0) + 1
            db.session.commit()

            logs = session.get("logs", [])
            logs.insert(0, f"🧪 Poção comprada por {custo_pocao} 🪙! Total: {char.pocoes}.")
            session["logs"] = logs
            return jsonify(empacotar_estado_jogador(current_user, char))

        return jsonify({"success": False, "message": "Ação inválida."}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Erro na loja: {str(e)}"}), 500

# ==========================================================
# ROLETA DA SORTE COM SALVAMENTO NO BANCO
# ==========================================================
@app.route("/api/roleta/girar", methods=["POST"])
def api_roleta_girar():
    if not current_user.is_authenticated or not current_user.character:
        return jsonify({"success": False, "message": "Personagem não encontrado."}), 400

    char = current_user.character
    giros_gratis = char.giros_gratis_roleta or 0
    custo_giro = 50

    if giros_gratis > 0:
        char.giros_gratis_roleta -= 1
    else:
        if char.moedas < custo_giro:
            return jsonify({"success": False, "message": f"Moedas insuficientes ({custo_giro} 🪙)."}), 400
        char.moedas -= custo_giro

    pesos = [25, 20, 18, 15, 10, 6, 4, 2]
    fatia_sorteada_idx = random.choices(range(len(ROLETA_FATIAS)), weights=pesos, k=1)[0]
    fatia = ROLETA_FATIAS[fatia_sorteada_idx]

    tipo = fatia["tipo"]
    qtd = fatia["qtd"]
    logs = session.get("logs", [])

    try:
        if tipo == "moedas":
            char.moedas += qtd
            msg_premio = f"+{qtd} 🪙 Moedas de Ouro"
        elif tipo == "xp":
            char.xp += qtd
            verificar_level_up(char.to_dict(), logs)
            msg_premio = f"+{qtd} ✨ Experiência (XP)"
        elif tipo == "pocoes":
            char.pocoes = (char.pocoes or 0) + qtd
            msg_premio = f"+{qtd} 🧪 Poções de Cura"
        elif tipo == "poeira":
            char.poeira_arcana = (char.poeira_arcana or 0) + qtd
            msg_premio = f"+{qtd} 🔮 Poeira Arcana"
        elif tipo == "equipamento":
            item_lendario = gerar_item_aleatorio(char.nivel, raridade_forcada="Lendário")
            eq = Equipment(
                character_id=char.id,
                item_key=item_lendario["id"],
                nome=item_lendario["nome"],
                tipo=item_lendario["tipo"],
                raridade=item_lendario["raridade"],
                bonus_ataque=item_lendario.get("bonus_ataque", 0),
                bonus_defesa=item_lendario.get("bonus_defesa", 0),
                bonus_hp=item_lendario.get("bonus_hp", 0),
                bonus_critico=item_lendario.get("bonus_critico", 0),
                bonus_esquiva=item_lendario.get("bonus_esquiva", 0),
                preco=item_lendario["preco"],
                imagem=item_lendario["imagem"],
                descricao=item_lendario["descricao"],
                nivel_upgrade=0,
                equipado=False
            )
            db.session.add(eq)
            msg_premio = f"👑 EQUIPAMENTO LENDÁRIO: {item_lendario['nome']}!"

        db.session.commit()
        logs.insert(0, f"🎰 [ROLETA DA SORTE] A roleta parou na fatia #{fatia_sorteada_idx + 1}! Você ganhou: {msg_premio}!")
        session["logs"] = logs

        res = empacotar_estado_jogador(current_user, char)
        res["roleta_resultado"] = {
            "fatia_index": fatia_sorteada_idx,
            "fatia": fatia,
            "mensagem": msg_premio
        }
        return jsonify(res)
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Erro ao girar roleta: {str(e)}"}), 500

# ==========================================================
# ESCONDERIJO IDLE NO BANCO
# ==========================================================
@app.route("/api/qg/coletar", methods=["POST"])
def api_qg_coletar():
    if not current_user.is_authenticated or not current_user.character:
        return jsonify({"success": False, "message": "Personagem não encontrado."}), 400

    char = current_user.character
    sincronizar_esconderijo_db(char)
    b = char.building

    m_coletadas = b.moedas_acumuladas or 0
    p_coletadas = b.pocoes_acumuladas or 0

    if m_coletadas == 0 and p_coletadas == 0:
        return jsonify({"success": False, "message": "Nenhum recurso novo acumulado no momento."}), 400

    try:
        char.moedas += m_coletadas
        char.pocoes = (char.pocoes or 0) + p_coletadas
        b.moedas_acumuladas = 0
        b.pocoes_acumuladas = 0
        b.ultima_coleta = int(time.time())
        db.session.commit()

        logs = session.get("logs", [])
        logs.insert(0, f"🏰 [ESCONDERIJO] Produção recolhida: +{m_coletadas} 🪙 Moedas e +{p_coletadas} 🧪 Poções!")
        session["logs"] = logs
        return jsonify(empacotar_estado_jogador(current_user, char))
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Erro na coleta: {str(e)}"}), 500

@app.route("/api/qg/upgrade", methods=["POST"])
def api_qg_upgrade():
    if not current_user.is_authenticated or not current_user.character:
        return jsonify({"success": False, "message": "Personagem não encontrado."}), 400

    char = current_user.character
    sincronizar_esconderijo_db(char)
    b = char.building
    data = request.get_json() or {}
    construcao = data.get("construcao") or data.get("tipo")

    try:
        if construcao == "mina":
            lvl = b.nivel_mina or 1
            custo_moedas = lvl * 120
            custo_poeira = lvl * 15
            if char.moedas < custo_moedas or (char.poeira_arcana or 0) < custo_poeira:
                return jsonify({"success": False, "message": f"Recursos insuficientes ({custo_moedas} 🪙 e {custo_poeira} 🔮)."}), 400
            char.moedas -= custo_moedas
            char.poeira_arcana -= custo_poeira
            b.nivel_mina = lvl + 1
        elif construcao == "laboratorio":
            lvl = b.nivel_lab or 1
            custo_moedas = lvl * 160
            custo_poeira = lvl * 20
            if char.moedas < custo_moedas or (char.poeira_arcana or 0) < custo_poeira:
                return jsonify({"success": False, "message": f"Recursos insuficientes ({custo_moedas} 🪙 e {custo_poeira} 🔮)."}), 400
            char.moedas -= custo_moedas
            char.poeira_arcana -= custo_poeira
            b.nivel_lab = lvl + 1
        else:
            return jsonify({"success": False, "message": "Construção desconhecida."}), 400

        db.session.commit()
        logs = session.get("logs", [])
        logs.insert(0, f"🏰 [ESCONDERIJO] {construcao.capitalize()} evoluída com sucesso!")
        session["logs"] = logs
        return jsonify(empacotar_estado_jogador(current_user, char))
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Erro ao aprimorar construção: {str(e)}"}), 500

# ==========================================================
# MASMORRA (TORRE DOS 20 CHEFES) COM SALVAMENTO
# ==========================================================
@app.route("/api/masmorra/iniciar", methods=["POST"])
def api_masmorra_iniciar():
    if not current_user.is_authenticated or not current_user.character:
        return jsonify({"success": False, "message": "Personagem não encontrado."}), 400

    char = current_user.character
    andar = char.andar_masmorra or 1
    if andar > len(MASMORRA_ANDAR_CHEFES):
        return jsonify({"success": False, "message": "Você já conquistou todos os 20 Andares da Masmorra!"}), 400

    chefe_base = MASMORRA_ANDAR_CHEFES[andar - 1]
    chefe = {
        "andar": andar,
        "nome": chefe_base["nome"],
        "hp_max": chefe_base["hp"],
        "hp_atual": chefe_base["hp"],
        "ataque": chefe_base["ataque"],
        "defesa": chefe_base["defesa"],
        "poder": chefe_base["poder"],
        "icon": chefe_base["icon"],
        "imagem": chefe_base["imagem"],
        "xp": chefe_base["xp"],
        "moedas": chefe_base["moedas"]
    }

    session["masmorra"] = {
        "ativa": True,
        "andar": andar,
        "status": "em_batalha",
        "chefe": chefe,
        "ultimo_combate": None
    }

    totais = calcular_status_totais(char.to_dict())
    char.hp_atual = totais["hp_max"]
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()

    logs = session.get("logs", [])
    logs.insert(0, f"💀 [MASMORRA] Você adentrou o Andar {andar}! O Chefe {chefe['nome']} bloqueia a passagem!")
    session["logs"] = logs
    return jsonify(empacotar_estado_jogador(current_user, char))

@app.route("/api/masmorra/atacar", methods=["POST"])
def api_masmorra_atacar():
    if not current_user.is_authenticated or not current_user.character:
        return jsonify({"success": False, "message": "Personagem não encontrado."}), 400

    char = current_user.character
    masm = session.get("masmorra", {})
    if not masm.get("ativa") or masm.get("status") != "em_batalha":
        return jsonify({"success": False, "message": "Nenhum confronto de masmorra ativo."}), 400

    chefe = masm["chefe"]
    totais = calcular_status_totais(char.to_dict())
    logs = session.get("logs", [])

    # Monge cura turno
    cura_monge = 0
    if char.classe == "Monge":
        cura_monge = max(5, int(totais["hp_max"] * 0.08))
        char.hp_atual = min(totais["hp_max"], char.hp_atual + cura_monge)
        logs.insert(0, f"🧘 [PASSIVA MONGE] Regeneração do Chi curou +{cura_monge} HP!")

    # 1. Ataque do Jogador
    dano_jogador = max(1, totais["ataque"] - chefe["defesa"] + random.randint(-2, 4))
    chance_crit = totais["critico"] / 100.0
    deu_critico = random.random() <= chance_crit

    if char.classe == "Ninja" and (deu_critico or random.random() <= 0.30):
        dano_jogador *= 3
        logs.insert(0, f"🥷 [PASSIVA NINJA] CRÍTICO TRIPLO! Dano ampliado para {dano_jogador}!")
    elif deu_critico:
        dano_jogador = int(dano_jogador * 1.5)
        logs.insert(0, f"⚡ GOLPE CRÍTICO! Dano aumentado para {dano_jogador}!")

    chefe["hp_atual"] = max(0, chefe["hp_atual"] - dano_jogador)
    logs.insert(0, f"🗡️ Você golpeou o Chefe {chefe['nome']} causando {dano_jogador} de dano!")

    dano_chefe = 0
    esquivou = False
    contra_dano_viking = 0

    try:
        # Chefe Morreu?
        if chefe["hp_atual"] <= 0:
            masm["status"] = "vitoria"
            masm["ativa"] = False

            char.xp += chefe["xp"]
            char.moedas += chefe["moedas"]

            # BAÚ LENDÁRIO NO BANCO DE DADOS
            item_bau = gerar_item_aleatorio(char.nivel, raridade_forcada=random.choice(["Épico", "Lendário"]))
            novo_eq = Equipment(
                character_id=char.id,
                item_key=item_bau["id"],
                nome=item_bau["nome"],
                tipo=item_bau["tipo"],
                raridade=item_bau["raridade"],
                bonus_ataque=item_bau.get("bonus_ataque", 0),
                bonus_defesa=item_bau.get("bonus_defesa", 0),
                bonus_hp=item_bau.get("bonus_hp", 0),
                bonus_critico=item_bau.get("bonus_critico", 0),
                bonus_esquiva=item_bau.get("bonus_esquiva", 0),
                preco=item_bau["preco"],
                imagem=item_bau["imagem"],
                descricao=item_bau["descricao"],
                nivel_upgrade=0,
                equipado=False
            )
            db.session.add(novo_eq)

            andar_vencido = masm["andar"]
            char.masmorras_completadas = max(char.masmorras_completadas or 0, andar_vencido)
            if (char.andar_masmorra or 1) <= andar_vencido:
                char.andar_masmorra = min(20, andar_vencido + 1)

            db.session.commit()

            logs.insert(0, f"🏆 [MASMORRA] O Chefe {chefe['nome']} foi destruído! +{chefe['xp']} XP, +{chefe['moedas']} 🪙!")
            logs.insert(0, f"👑 [BAÚ LENDÁRIO] Você abriu o baú e obteve: {item_bau['nome']} ({item_bau['raridade']})!")
            verificar_level_up(char.to_dict(), logs)

            masm["ultimo_combate"] = {
                "dano_jogador": dano_jogador,
                "critico": deu_critico,
                "esquivou": False,
                "dano_inimigo": 0,
                "viking_retaliacao": 0,
                "monge_cura": cura_monge,
                "chefe_derrotado": True
            }
            session["masmorra"] = masm
            session["logs"] = logs
            return jsonify(empacotar_estado_jogador(current_user, char))

        # 2. Turno do Chefe
        chance_esquiva = totais["esquiva"] / 100.0
        esquivou = random.random() <= chance_esquiva

        if esquivou:
            logs.insert(0, f"💨 ESQUIVA FANTÁSTICA! Você evitou o golpe avassalador de {chefe['nome']}!")
        else:
            dano_chefe = max(2, chefe["ataque"] - totais["defesa"] + random.randint(-1, 3))
            if char.classe == "Guerreiro" and (char.hp_atual / max(1, totais["hp_max"])) < 0.40:
                dano_chefe = max(1, int(dano_chefe * 0.65))

            if char.classe == "Viking":
                absorvido = max(1, int(dano_chefe * 0.25))
                contra_dano_viking = max(1, int(dano_chefe * 0.50))
                dano_chefe = max(1, dano_chefe - absorvido)
                chefe["hp_atual"] = max(0, chefe["hp_atual"] - contra_dano_viking)
                logs.insert(0, f"🪓 [RETALIAÇÃO VIKING] Devolveu {contra_dano_viking} dano ao chefe!")

            char.hp_atual = max(0, char.hp_atual - dano_chefe)
            logs.insert(0, f"💥 O Chefe {chefe['nome']} causou {dano_chefe} de dano!")

            if char.hp_atual <= 0:
                masm["status"] = "derrota"
                masm["ativa"] = False
                logs.insert(0, f"💀 Você foi derrotado no Andar {masm['andar']}. Fortaleça seus atributos e tente novamente!")
                totais_acamp = calcular_status_totais(char.to_dict())
                char.hp_atual = totais_acamp["hp_max"]

        db.session.commit()
        masm["ultimo_combate"] = {
            "dano_jogador": dano_jogador,
            "critico": deu_critico,
            "esquivou": esquivou,
            "dano_inimigo": dano_chefe,
            "viking_retaliacao": contra_dano_viking,
            "monge_cura": cura_monge,
            "chefe_derrotado": False
        }
        session["masmorra"] = masm
        session["logs"] = logs
        return jsonify(empacotar_estado_jogador(current_user, char))

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Erro na masmorra: {str(e)}"}), 500

# ==========================================================
# AVENTURA / ONDAS COM PERSISTÊNCIA DE LOOT DROP NO BANCO
# ==========================================================
@app.route("/api/aventura", methods=["POST"])
def api_aventura():
    if not current_user.is_authenticated or not current_user.character:
        return jsonify({"success": False, "message": "Personagem não encontrado."}), 400

    char = current_user.character
    adv = session.get("aventura", {
        "ativa": False,
        "onda": 1,
        "status": "idle",
        "espolio_moedas": 0,
        "espolio_xp": 0,
        "bonus_temp": {"ataque": 0, "defesa": 0, "hp_max": 0},
        "inimigo": None,
        "ultimo_combate": None
    })
    logs = session.get("logs", [])
    data = request.get_json() or {}
    acao = data.get("acao")
    regiao_atual = char.regiao_atual or "floresta"

    if acao == "iniciar":
        adv["ativa"] = True
        adv["onda"] = 1
        adv["status"] = "em_batalha"
        adv["espolio_moedas"] = 0
        adv["espolio_xp"] = 0
        adv["bonus_temp"] = {"ataque": 0, "defesa": 0, "hp_max": 0}
        adv["ultimo_combate"] = None

        totais = calcular_status_totais(char.to_dict())
        char.hp_atual = totais["hp_max"]
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()

        inimigo = gerar_inimigo_onda(1, regiao_atual)
        adv["inimigo"] = inimigo
        logs.insert(0, f"⚔️ Expedição iniciada em {REGIOES_MAPA[regiao_atual]['nome']}! Onda 1: Você encontrou um {inimigo['nome']}!")
        session["aventura"] = adv
        session["logs"] = logs
        return jsonify(empacotar_estado_jogador(current_user, char))

    elif acao == "proxima_onda":
        if not adv.get("ativa") or adv.get("status") != "onda_vencida":
            return jsonify({"success": False, "message": "Você precisa vencer a onda atual para prosseguir."}), 400

        adv["onda"] += 1
        adv["status"] = "em_batalha"
        adv["ultimo_combate"] = None
        inimigo = gerar_inimigo_onda(adv["onda"], regiao_atual)
        adv["inimigo"] = inimigo
        logs.insert(0, f"🔥 Entrando na Onda {adv['onda']}! {inimigo['nome']} ruge na sua frente!")
        session["aventura"] = adv
        session["logs"] = logs
        return jsonify(empacotar_estado_jogador(current_user, char))

    elif acao == "atacar":
        if not adv.get("ativa") or adv.get("status") != "em_batalha":
            return jsonify({"success": False, "message": "Nenhuma batalha ativa."}), 400

        inimigo = adv["inimigo"]
        totais = calcular_status_totais(char.to_dict(), adv["bonus_temp"])

        cura_monge = 0
        if char.classe == "Monge":
            cura_monge = max(4, int(totais["hp_max"] * 0.08))
            char.hp_atual = min(totais["hp_max"], char.hp_atual + cura_monge)
            logs.insert(0, f"🧘 [PASSIVA MONGE] Regeneração do Chi restaurou +{cura_monge} HP!")

        dano_jogador = totais["ataque"] + random.randint(-2, 3)
        chance_crit = totais["critico"] / 100.0
        deu_critico = random.random() <= chance_crit

        if char.classe == "Berserker":
            hp_perdido_pct = ((totais["hp_max"] - char.hp_atual) / max(1, totais["hp_max"])) * 100
            bonus_furia = int(dano_jogador * (hp_perdido_pct / 180))
            if bonus_furia > 0:
                dano_jogador += bonus_furia
                logs.insert(0, f"🪓 [PASSIVA BERSERKER] Fúria Ativada! +{bonus_furia} dano!")

        if char.classe == "Ninja" and (deu_critico or random.random() <= 0.30):
            dano_jogador *= 3
            logs.insert(0, f"🥷 [PASSIVA NINJA] CRÍTICO TRIPLO! Dano ampliado para {dano_jogador}!")
        elif deu_critico:
            dano_jogador = int(dano_jogador * 1.5)
            logs.insert(0, f"⚡ GOLPE CRÍTICO! Dano aumentado para {dano_jogador}!")

        if "Esqueleto" in inimigo["nome"]:
            dano_jogador = max(1, dano_jogador - 4)
        elif "Golem" in inimigo["nome"]:
            dano_jogador = max(1, dano_jogador - 6)

        inimigo["hp_atual"] = max(0, inimigo["hp_atual"] - dano_jogador)
        logs.insert(0, f"🗡️ Você atacou {inimigo['nome']} causando {dano_jogador} de dano!")

        dano_inimigo = 0
        esquivou = False
        contra_dano_viking = 0

        try:
            if inimigo["hp_atual"] <= 0:
                xp_ganho = inimigo["xp"]
                moedas_ganhas = inimigo["moedas"]
                adv["espolio_xp"] += xp_ganho
                adv["espolio_moedas"] += moedas_ganhas
                adv["bonus_temp"]["ataque"] += 2
                adv["bonus_temp"]["defesa"] += 1
                adv["bonus_temp"]["hp_max"] += 10

                novos_totais = calcular_status_totais(char.to_dict(), adv["bonus_temp"])
                char.hp_atual = min(novos_totais["hp_max"], char.hp_atual + 15)
                adv["status"] = "onda_vencida"

                logs.insert(0, f"🏆 Onda {adv['onda']} Vencida! {inimigo['nome']} sucumbiu!")
                logs.insert(0, f"💰 Espólio: +{moedas_ganhas} 🪙 e +{xp_ganho} XP (Bônus: +2 Atq, +1 Def, +10 HP Max)")

                # 30% LOOT DROP SALVO DIRETO NO BANCO DE DADOS
                if random.random() <= 0.30:
                    item_drop = gerar_item_aleatorio(char.nivel)
                    novo_eq = Equipment(
                        character_id=char.id,
                        item_key=item_drop["id"],
                        nome=item_drop["nome"],
                        tipo=item_drop["tipo"],
                        raridade=item_drop["raridade"],
                        bonus_ataque=item_drop.get("bonus_ataque", 0),
                        bonus_defesa=item_drop.get("bonus_defesa", 0),
                        bonus_hp=item_drop.get("bonus_hp", 0),
                        bonus_critico=item_drop.get("bonus_critico", 0),
                        bonus_esquiva=item_drop.get("bonus_esquiva", 0),
                        preco=item_drop["preco"],
                        imagem=item_drop["imagem"],
                        descricao=item_drop["descricao"],
                        nivel_upgrade=0,
                        equipado=False
                    )
                    db.session.add(novo_eq)
                    logs.insert(0, f"🎁 [LOOT DROP] O monstro derrubou: {item_drop['nome']} ({item_drop['raridade']})! Salvo na sua mochila.")

                db.session.commit()

                adv["ultimo_combate"] = {
                    "dano_jogador": dano_jogador,
                    "critico": deu_critico,
                    "esquivou": False,
                    "dano_inimigo": 0,
                    "viking_retaliacao": 0,
                    "monge_cura": cura_monge,
                    "inimigo_derrotado": True
                }
                session["aventura"] = adv
                session["logs"] = logs
                return jsonify(empacotar_estado_jogador(current_user, char))

            # Turno Inimigo
            chance_esquiva = totais["esquiva"] / 100.0
            esquivou = random.random() <= chance_esquiva

            if esquivou:
                logs.insert(0, f"💨 ESQUIVA PERFEITA! Você desviou do golpe de {inimigo['nome']}!")
            else:
                dano_inimigo = max(1, inimigo["ataque"] - totais["defesa"] + random.randint(-1, 2))
                if char.classe == "Guerreiro" and (char.hp_atual / max(1, totais["hp_max"])) < 0.40:
                    dano_inimigo = max(1, int(dano_inimigo * 0.65))

                if char.classe == "Viking":
                    absorvido = max(1, int(dano_inimigo * 0.25))
                    contra_dano_viking = max(1, int(dano_inimigo * 0.50))
                    dano_inimigo = max(1, dano_inimigo - absorvido)
                    inimigo["hp_atual"] = max(0, inimigo["hp_atual"] - contra_dano_viking)
                    logs.insert(0, f"🪓 [RETALIAÇÃO VIKING] Absorveu {absorvido} e contra-atacou causando {contra_dano_viking} dano!")

                char.hp_atual = max(0, char.hp_atual - dano_inimigo)
                logs.insert(0, f"💥 {inimigo['nome']} causou {dano_inimigo} de dano!")

                if char.hp_atual <= 0:
                    adv["status"] = "derrota"
                    adv["ativa"] = False
                    char.moedas += adv["espolio_moedas"]
                    char.xp += adv["espolio_xp"]
                    logs.insert(0, f"💀 Você caiu em combate! Espólio resgatado: +{adv['espolio_moedas']} Moedas e +{adv['espolio_xp']} XP.")
                    verificar_level_up(char.to_dict(), logs)
                    adv["bonus_temp"] = {"ataque": 0, "defesa": 0, "hp_max": 0}
                    totais_acamp = calcular_status_totais(char.to_dict())
                    char.hp_atual = totais_acamp["hp_max"]

            db.session.commit()
            adv["ultimo_combate"] = {
                "dano_jogador": dano_jogador,
                "critico": deu_critico,
                "esquivou": esquivou,
                "dano_inimigo": dano_inimigo,
                "viking_retaliacao": contra_dano_viking,
                "monge_cura": cura_monge,
                "inimigo_derrotado": False
            }
            session["aventura"] = adv
            session["logs"] = logs
            return jsonify(empacotar_estado_jogador(current_user, char))

        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "message": f"Erro na batalha: {str(e)}"}), 500

    elif acao == "pocao":
        if (char.pocoes or 0) <= 0:
            return jsonify({"success": False, "message": "Você não possui poções restantes."}), 400

        try:
            totais = calcular_status_totais(char.to_dict(), adv.get("bonus_temp") if adv.get("ativa") else None)
            cura = 50
            char.hp_atual = min(totais["hp_max"], char.hp_atual + cura)
            char.pocoes -= 1
            db.session.commit()

            logs.insert(0, f"🧪 Você consumiu uma poção e recuperou {cura} de HP! (Poções restantes: {char.pocoes})")
            adv["ultimo_combate"] = {"pocao_cura": cura}
            session["aventura"] = adv
            session["logs"] = logs
            return jsonify(empacotar_estado_jogador(current_user, char))
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "message": f"Erro ao usar poção: {str(e)}"}), 500

    elif acao == "recuar":
        if not adv.get("ativa"):
            return jsonify({"success": False, "message": "Nenhuma expedição em andamento."}), 400

        try:
            char.moedas += adv["espolio_moedas"]
            char.xp += adv["espolio_xp"]
            logs.insert(0, f"🏃 Expedição finalizada! Retornou com todo o espólio: +{adv['espolio_moedas']} Moedas e +{adv['espolio_xp']} XP!")
            verificar_level_up(char.to_dict(), logs)

            adv["ativa"] = False
            adv["status"] = "idle"
            adv["bonus_temp"] = {"ataque": 0, "defesa": 0, "hp_max": 0}
            totais = calcular_status_totais(char.to_dict())
            char.hp_atual = totais["hp_max"]

            db.session.commit()
            session["aventura"] = adv
            session["logs"] = logs
            return jsonify(empacotar_estado_jogador(current_user, char))
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "message": f"Erro ao recuar: {str(e)}"}), 500

    return jsonify({"success": False, "message": "Ação inválida."}), 400

# ==========================================================
# VIAGEM ENTRE REGIÕES COM COMMIT NO BANCO
# ==========================================================
@app.route("/api/viajar", methods=["POST"])
def api_viajar():
    if not current_user.is_authenticated or not current_user.character:
        return jsonify({"success": False, "message": "Personagem não encontrado."}), 400

    char = current_user.character
    data = request.get_json() or {}
    regiao_id = data.get("regiao_id")

    if regiao_id not in REGIOES_MAPA:
        return jsonify({"success": False, "message": "Região desconhecida."}), 404

    regiao = REGIOES_MAPA[regiao_id]
    if char.nivel < regiao["nivel_minimo"]:
        return jsonify({"success": False, "message": f"Nível insuficiente. Requer Nível {regiao['nivel_minimo']}."}), 400

    try:
        char.regiao_atual = regiao_id
        db.session.commit()
        logs = session.get("logs", [])
        logs.insert(0, f"🗺️ Você viajou até {regiao['nome']} ({regiao['icone']})!")
        session["logs"] = logs
        return jsonify(empacotar_estado_jogador(current_user, char))
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Erro na viagem: {str(e)}"}), 500

# ==========================================================
# TREINAMENTO AFK COM PERSISTÊNCIA NO BANCO
# ==========================================================
@app.route("/api/treino", methods=["POST"])
def api_treino():
    if not current_user.is_authenticated or not current_user.character:
        return jsonify({"success": False, "message": "Personagem não encontrado."}), 400

    char = current_user.character
    data = request.get_json() or {}
    acao = data.get("acao")
    logs = session.get("logs", [])

    try:
        if acao == "iniciar":
            if char.treino_ativo:
                return jsonify({"success": False, "message": "Já existe um treino em andamento."}), 400

            chave = data.get("chave")
            if chave not in CONFIG_TREINO:
                return jsonify({"success": False, "message": "Opção de treino inválida."}), 400

            cfg = CONFIG_TREINO[chave]
            agora = int(time.time())
            duracao = cfg["duracao_segundos"]

            char.treino_ativo = True
            char.treino_chave = chave
            char.treino_nome = cfg["nome"]
            char.tempo_treino_inicio = agora
            char.tempo_treino_duracao = duracao
            char.tempo_treino_fim = agora + duracao

            db.session.commit()
            logs.insert(0, f"⏱️ Treino iniciado: {cfg['nome']} ({duracao}s)!")
            session["logs"] = logs
            return jsonify(empacotar_estado_jogador(current_user, char))

        elif acao == "cancelar":
            if not char.treino_ativo:
                return jsonify({"success": False, "message": "Nenhum treino ativo."}), 400

            char.treino_ativo = False
            char.treino_chave = None
            char.tempo_treino_fim = 0
            db.session.commit()
            logs.insert(0, "❌ O treino foi cancelado.")
            session["logs"] = logs
            return jsonify(empacotar_estado_jogador(current_user, char))

        elif acao == "coletar":
            if not char.treino_ativo:
                return jsonify({"success": False, "message": "Não há treino ativo."}), 400

            agora = int(time.time())
            if agora < (char.tempo_treino_fim or 0):
                tempo_restante = int(char.tempo_treino_fim - agora)
                return jsonify({"success": False, "message": f"Treino ainda em andamento. Restam {tempo_restante}s."}), 400

            cfg = CONFIG_TREINO.get(char.treino_chave, {})
            xp_ganho = cfg.get("xp", 0)
            moedas_ganhas = cfg.get("moedas", 0)
            bonus_stats = cfg.get("bonus_stats", {})

            char.xp += xp_ganho
            char.moedas += moedas_ganhas
            char.treino_bonus_ataque = (char.treino_bonus_ataque or 0) + bonus_stats.get("ataque", 0)
            char.treino_bonus_defesa = (char.treino_bonus_defesa or 0) + bonus_stats.get("defesa", 0)
            char.treino_bonus_hp_max = (char.treino_bonus_hp_max or 0) + bonus_stats.get("hp_max", 0)

            char.treino_ativo = False
            char.treino_chave = None
            char.tempo_treino_fim = 0

            db.session.commit()
            logs.insert(0, f"🎁 Treino finalizado! Conquistou +{xp_ganho} XP, +{moedas_ganhas} 🪙 e bônus permanentes (+{bonus_stats.get('ataque', 0)} Atq, +{bonus_stats.get('defesa', 0)} Def)!")
            verificar_level_up(char.to_dict(), logs)
            session["logs"] = logs
            return jsonify(empacotar_estado_jogador(current_user, char))

        return jsonify({"success": False, "message": "Ação inválida."}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Erro no treino: {str(e)}"}), 500

# ==========================================================
# RESET DO PERSONAGEM (CASCATA NO BANCO)
# ==========================================================
@app.route("/api/reset", methods=["POST"])
def api_reset():
    if not current_user.is_authenticated or not current_user.character:
        return jsonify({"success": False, "message": "Nenhum personagem ativo para resetar."}), 400

    try:
        db.session.delete(current_user.character)
        db.session.commit()
        session.pop("aventura", None)
        session.pop("masmorra", None)
        session.pop("loja_itens", None)
        session["logs"] = ["Personagem resetado com sucesso no banco de dados. Inicie um novo campeão!"]
        return jsonify(empacotar_estado_jogador(current_user, None))
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Erro ao resetar: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
