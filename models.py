from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacionamento 1 para 1 com o personagem
    character = db.relationship('Character', backref='user', uselist=False, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


class Character(db.Model):
    __tablename__ = 'character'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)

    nome = db.Column(db.String(50), nullable=False)
    classe = db.Column(db.String(30), nullable=False)
    nivel = db.Column(db.Integer, default=1)
    xp = db.Column(db.Integer, default=0)
    xp_proximo = db.Column(db.Integer, default=60)

    # Atributos Base
    hp_max_base = db.Column(db.Integer, default=100)
    hp_atual = db.Column(db.Integer, default=100)
    ataque_base = db.Column(db.Integer, default=10)
    defesa_base = db.Column(db.Integer, default=2)
    esquiva_base = db.Column(db.Integer, default=5)
    critico_base = db.Column(db.Integer, default=10)

    # Recursos
    moedas = db.Column(db.Integer, default=80)
    poeira_arcana = db.Column(db.Integer, default=15)
    pocoes = db.Column(db.Integer, default=3)
    giros_gratis_roleta = db.Column(db.Integer, default=1)

    # Região e Masmorra
    regiao_atual = db.Column(db.String(30), default='floresta')
    andar_masmorra = db.Column(db.Integer, default=1)
    masmorras_completadas = db.Column(db.Integer, default=0)

    # Academia de Atributos (Pontos comprados manualmente)
    forca = db.Column(db.Integer, default=0)
    destreza = db.Column(db.Integer, default=0)
    vitalidade = db.Column(db.Integer, default=0)
    mente = db.Column(db.Integer, default=0)

    # Treino AFK
    treino_ativo = db.Column(db.Boolean, default=False)
    treino_chave = db.Column(db.String(20), nullable=True)
    treino_nome = db.Column(db.String(100), nullable=True)
    tempo_treino_inicio = db.Column(db.Integer, default=0)
    tempo_treino_fim = db.Column(db.Integer, default=0)
    tempo_treino_duracao = db.Column(db.Integer, default=0)
    treino_bonus_ataque = db.Column(db.Integer, default=0)
    treino_bonus_defesa = db.Column(db.Integer, default=0)
    treino_bonus_hp_max = db.Column(db.Integer, default=0)

    # Loja
    loja_reroll_count = db.Column(db.Integer, default=0)

    # Relacionamentos
    equipments = db.relationship('Equipment', backref='character', cascade='all, delete-orphan', lazy=True)
    building = db.relationship('BaseBuilding', backref='character', uselist=False, cascade='all, delete-orphan')

    def to_dict(self):
        equipados_dict = {
            "cabeca": None,
            "peitoral": None,
            "arma": None,
            "anel": None
        }
        inventario_list = []

        for eq in self.equipments:
            eq_dict = eq.to_dict()
            if eq.equipado:
                equipados_dict[eq.tipo] = eq_dict
            else:
                inventario_list.append(eq_dict)

        building_dict = self.building.to_dict() if self.building else {
            "mina_lvl": 1,
            "laboratorio_lvl": 1,
            "moedas_acumuladas": 0,
            "pocoes_acumuladas": 0
        }

        return {
            "id": self.id,
            "nome": self.nome,
            "classe": self.classe,
            "nivel": self.nivel,
            "xp": self.xp,
            "xp_proximo": self.xp_proximo,
            "moedas": self.moedas,
            "poeira_arcana": self.poeira_arcana,
            "pocoes": self.pocoes,
            "giros_gratis_roleta": self.giros_gratis_roleta,
            "hp_max_base": self.hp_max_base,
            "hp_atual": self.hp_atual,
            "ataque_base": self.ataque_base,
            "defesa_base": self.defesa_base,
            "esquiva_base": self.esquiva_base,
            "critico_base": self.critico_base,
            "regiao_atual": self.regiao_atual,
            "masmorra_andar_atual": self.andar_masmorra,
            "masmorras_completadas": self.masmorras_completadas,
            "forca": self.forca,
            "destreza": self.destreza,
            "vitalidade": self.vitalidade,
            "mente": self.mente,
            "atributos_academia": {
                "forca": self.forca,
                "destreza": self.destreza,
                "vitalidade": self.vitalidade,
                "mente": self.mente
            },
            "treino_bonus": {
                "ataque": self.treino_bonus_ataque,
                "defesa": self.treino_bonus_defesa,
                "hp_max": self.treino_bonus_hp_max
            },
            "esconderijo": building_dict,
            "equipados": equipados_dict,
            "inventario": inventario_list
        }


class Equipment(db.Model):
    __tablename__ = 'equipment'

    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)

    item_key = db.Column(db.String(50), nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(30), nullable=False) # cabeca, peitoral, arma, anel
    raridade = db.Column(db.String(30), nullable=False) # Comum, Raro, Épico, Lendário
    bonus_ataque = db.Column(db.Integer, default=0)
    bonus_defesa = db.Column(db.Integer, default=0)
    bonus_hp = db.Column(db.Integer, default=0)
    bonus_critico = db.Column(db.Integer, default=0)
    bonus_esquiva = db.Column(db.Integer, default=0)
    preco = db.Column(db.Integer, default=30)
    imagem = db.Column(db.String(200), default='')
    descricao = db.Column(db.String(255), default='')
    nivel_upgrade = db.Column(db.Integer, default=0)
    equipado = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            "id": self.item_key,
            "db_id": self.id,
            "nome": self.nome,
            "tipo": self.tipo,
            "raridade": self.raridade,
            "upgrade_lvl": self.nivel_upgrade,
            "bonus_ataque": self.bonus_ataque,
            "bonus_defesa": self.bonus_defesa,
            "bonus_hp": self.bonus_hp,
            "bonus_critico": self.bonus_critico,
            "bonus_esquiva": self.bonus_esquiva,
            "preco": self.preco,
            "imagem": self.imagem,
            "descricao": self.descricao,
            "equipado": self.equipado
        }


class BaseBuilding(db.Model):
    __tablename__ = 'base_building'

    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey('character.id'), unique=True, nullable=False)

    nivel_mina = db.Column(db.Integer, default=1)
    nivel_lab = db.Column(db.Integer, default=1)
    ultima_coleta = db.Column(db.Integer, default=0)
    moedas_acumuladas = db.Column(db.Integer, default=0)
    pocoes_acumuladas = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            "mina_lvl": self.nivel_mina,
            "laboratorio_lvl": self.nivel_lab,
            "timestamp_coleta": self.ultima_coleta,
            "moedas_acumuladas": self.moedas_acumuladas,
            "pocoes_acumuladas": self.pocoes_acumuladas
        }
