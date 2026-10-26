# ⚔️ RPG Legends — Reino dos Campeões

<p align="center">
  <img src="static/images/classes/guerreiro.svg" width="80" alt="RPG Legends" />
</p>

<p align="center">
  <strong>Um RPG de navegador completo, full-stack, construído com Flask + SQLAlchemy + Vanilla JS</strong><br>
  Dark Fantasy / Cyberpunk UI · Persistência em banco de dados · Deploy-ready no Render / Heroku
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python" />
  <img src="https://img.shields.io/badge/Flask-3.0%2B-black?style=flat-square&logo=flask" />
  <img src="https://img.shields.io/badge/SQLAlchemy-3.1%2B-red?style=flat-square" />
  <img src="https://img.shields.io/badge/SQLite%20%2F%20PostgreSQL-supported-green?style=flat-square&logo=postgresql" />
  <img src="https://img.shields.io/badge/Vanilla%20JS-ES6%2B-yellow?style=flat-square&logo=javascript" />
  <img src="https://img.shields.io/badge/Deploy-Render%20%2F%20Heroku-purple?style=flat-square" />
</p>

---

## 📖 Sobre o Projeto

**RPG Legends** é um jogo de RPG por navegador desenvolvido como projeto full-stack de Programação Orientada a Objetos. O jogador cria um herói, escolhe entre **8 classes únicas**, enfrenta **ondas de inimigos**, explora **masmorras com 20 andares de chefes**, treina atributos, constrói um esconderijo idle, coleta equipamentos por loot e muito mais — tudo persistido em banco de dados relacional com sistema de autenticação completo.

---

## 🎮 Funcionalidades

### 🧙 Sistema de Personagem
- **8 Classes jogáveis:** Guerreiro, Mago, Ladino, Berserker, Ninja, Viking, Monge e Paladino — cada uma com passivas e mecânicas únicas
- **Academia de Atributos:** Invista moedas em Força, Destreza, Vitalidade e Mente
- **Paperdoll com 4 slots:** Cabeça, Peitoral, Arma e Anel
- **Mochila com grade de inventário** e funcionalidades de vender (50% do valor) ou desmontar itens

### ⚔️ Aba Aventura — Modo Ondas
- Ondas sequenciais de inimigos com dificuldade crescente por região
- Acúmulo de moedas e XP por onda; resgate total ao recuar ou ao morrer
- **Drop de loot (30%)** a cada onda vencida, direto para a mochila
- Bônus temporários de atributos acumulados por onda concluída

### 💀 Aba Masmorra — Torre dos Titãs
- 20 andares com chefes únicos, progressivamente mais poderosos
- Cada andar conquistado concede um **Baú Lendário** (item Épico ou Lendário garantido)
- Progresso permanente salvo no banco de dados

### 🛒 Aba Loja & Equipamentos
- Catálogo com 3–4 itens aleatórios (Armas, Armaduras, Capacetes, Anéis)
- **Raridades:** Comum · Raro · Épico · Lendário (com brilhos visuais distintos)
- **Reroll:** 1ª atualização grátis; subsequentes com custo dobrado a cada vez
- **Tooltip comparativo:** Hover sobre um item exibe card com status atual vs. novo (verde = melhora, vermelho = piora)

### 🏋️ Aba Treinamento — AFK Real Time
- Opções de 1 min, 5 min, 15 min e 30 min
- Cronômetro regressivo em JS (`setInterval`) com barra de progresso animada
- Animação CSS do herói atacando um dummy durante o treino
- Botão de coleta de recompensas ao concluir; cancelamento disponível

### 🏰 Aba Esconderijo — Idle Passivo
- **Mina de Ouro:** Gera moedas passivamente (offline também)
- **Laboratório Alquímico:** Gera poções passivamente
- Construções evolutivas com custo em moedas + Poeira Arcana
- "Coletar Recursos" resgata tudo acumulado desde a última visita

### 🎰 Roleta da Sorte
- Roleta animada em Canvas com 8 fatias de recompensas
- 1 giro gratuito por sessão; giros extras custam moedas
- Recompensas: Moedas, XP, Poções, Poeira Arcana e itens Lendários

### 🗺️ Mapa do Mundo
- Mapa SVG interativo com 4 regiões desbloqueáveis por nível
- **Floresta dos Goblins** (Nível 1+) · **Montanha dos Vikings** (Nível 3+) · **Castelo do Lich** (Nível 5+) · **Vulcão do Dragão** (Nível 8+)
- Cada região tem inimigos, recompensas e dificuldade próprios

### 🔨 Ferreiro & Crafting
- **Desmontar item** → gera Poeira Arcana
- **Melhorar equipamento (+1 a +10)** → gasta Poeira Arcana + Moedas → bônus de +10% por nível

### 🔐 Autenticação Completa
- Registro e login com hash seguro de senha (`werkzeug.security`)
- Persistência total via **Flask-Login** + **Flask-SQLAlchemy**
- Estado do personagem completamente restaurado a cada login

---

## 🛠️ Tecnologias

| Camada | Tecnologia |
|---|---|
| **Backend** | Python 3.10+, Flask 3.0+, Flask-SQLAlchemy, Flask-Login |
| **Banco de Dados** | SQLite (dev local) · PostgreSQL (produção) |
| **ORM** | SQLAlchemy 3.1+ com migrations automáticas via `db.create_all()` |
| **Auth** | Flask-Login + Werkzeug password hashing |
| **Frontend** | HTML5 semântico, CSS3 (Grid, Flexbox, Keyframes, Glassmorphism), Vanilla JS ES6+ |
| **Fontes** | Google Fonts: Cinzel (títulos), Exo 2 (HUD), Inter (corpo) |
| **Canvas** | Roleta da Sorte animada via Canvas API |
| **SVG** | Mapa do mundo interativo via SVG inline |
| **Deploy** | Gunicorn + Procfile (Render / Heroku ready) |

---

## 🗂️ Estrutura de Arquivos

```
RPG/
├── app.py                  # Aplicação Flask principal + todas as rotas REST
├── models.py               # ORM SQLAlchemy: User, Character, Equipment, BaseBuilding
├── game_logic.py           # Lógica de jogo: combate, XP, loot, regiões, masmorra
├── main.py                 # Ponto de entrada alternativo
├── requirements.txt        # Dependências Python
├── Procfile                # Configuração de deploy (gunicorn)
├── .gitignore              # Arquivos ignorados pelo Git
│
├── templates/
│   └── index.html          # SPA — Single Page Application (8 abas, modais, HUD)
│
└── static/
    ├── css/
    │   └── style.css       # Tema Dark Fantasy / Cyberpunk completo (~1600 linhas)
    ├── js/
    │   └── game.js         # Engine frontend: fetch, renderização, animações
    └── images/
        ├── classes/        # SVGs das 8 classes (guerreiro, mago, ladino...)
        ├── enemies/        # SVGs dos inimigos (goblin, orc, dragão, lich...)
        └── items/          # SVGs de equipamentos e itens
```

---

## 🗃️ Modelagem do Banco de Dados

```mermaid
erDiagram
    User ||--o| Character : "possui"
    Character ||--o{ Equipment : "carrega"
    Character ||--o| BaseBuilding : "constrói"

    User {
        int id PK
        string username
        string password_hash
        datetime created_at
    }

    Character {
        int id PK
        int user_id FK
        string nome
        string classe
        int nivel
        int xp
        int moedas
        int poeira_arcana
        int pocoes
        int hp_max_base
        int hp_atual
        int ataque_base
        int defesa_base
        int forca
        int destreza
        int vitalidade
        int mente
        string regiao_atual
        int andar_masmorra
        bool treino_ativo
        int tempo_treino_fim
    }

    Equipment {
        int id PK
        int character_id FK
        string nome
        string tipo
        string raridade
        int bonus_ataque
        int bonus_defesa
        int bonus_hp
        int bonus_critico
        int bonus_esquiva
        int nivel_upgrade
        bool equipado
    }

    BaseBuilding {
        int id PK
        int character_id FK
        int nivel_mina
        int nivel_lab
        int ultima_coleta
        int moedas_acumuladas
        int pocoes_acumuladas
    }
```

---

## 🚀 Como Executar Localmente

### Pré-requisitos
- Python 3.10 ou superior
- pip

### Instalação

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/rpg-legends.git
cd rpg-legends

# Crie e ative um ambiente virtual
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux / macOS
source .venv/bin/activate

# Instale as dependências
pip install -r requirements.txt

# Execute o servidor
python app.py
```

Acesse **http://localhost:5000** no navegador.

> O banco de dados SQLite (`rpg.db`) é criado automaticamente na primeira execução via `db.create_all()`.

---

## ☁️ Deploy no Render / Heroku

### 1. Variáveis de Ambiente

| Variável | Descrição |
|---|---|
| `DATABASE_URL` | URL de conexão com PostgreSQL (ex: `postgresql://user:pass@host/db`) |
| `SECRET_KEY` | Chave secreta Flask para sessões seguras |

> O app converte automaticamente `postgres://` → `postgresql://` para compatibilidade com SQLAlchemy 1.4+.

### 2. Render

1. Conecte o repositório GitHub ao Render
2. Adicione um banco **PostgreSQL Managed** e copie a `DATABASE_URL`
3. O `Procfile` já está configurado:
   ```
   web: gunicorn app:app
   ```
4. Clique em **Deploy** ✅

### 3. Heroku

```bash
heroku create rpg-legends
heroku addons:create heroku-postgresql:mini
heroku config:set SECRET_KEY="sua-chave-secreta-aqui"
git push heroku main
```

---

## 🌐 Rotas da API REST

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/` | Página principal (SPA) |
| `POST` | `/register` | Registrar nova conta |
| `POST` | `/login` | Autenticar usuário |
| `POST` | `/logout` | Encerrar sessão |
| `GET` | `/api/estado` | Estado completo do jogador |
| `POST` | `/api/criar` | Criar personagem |
| `POST` | `/api/aventura` | Ação de combate na aventura |
| `POST` | `/api/masmorra/iniciar` | Iniciar andar da masmorra |
| `POST` | `/api/masmorra/atacar` | Atacar chefe da masmorra |
| `GET` | `/api/loja` | Obter itens da loja |
| `POST` | `/api/equipar` | Equipar / desequipar item |
| `POST` | `/api/vender` | Vender item do inventário |
| `POST` | `/api/ferreiro/desmontar` | Desmontar item → Poeira Arcana |
| `POST` | `/api/ferreiro/upgrade` | Melhorar item equipado |
| `POST` | `/api/atributos/upar` | Comprar ponto de atributo |
| `POST` | `/api/treino` | Iniciar / coletar treino AFK |
| `POST` | `/api/qg/coletar` | Coletar recursos do esconderijo |
| `POST` | `/api/qg/upgrade` | Evoluir construção do esconderijo |
| `POST` | `/api/roleta/girar` | Girar a roleta da sorte |
| `POST` | `/api/viajar` | Viajar para outra região do mapa |
| `POST` | `/api/reset` | Reiniciar personagem |

---

## 🎨 Design System

O tema **Dark Fantasy / Cyberpunk** segue uma paleta rigorosa:

| Token | Valor | Uso |
|---|---|---|
| `--bg-void` | `#07080b` | Fundo mais escuro |
| `--bg-dark` | `#0b0c10` | Fundo principal |
| `--neon-cyan` | `#66fcf1` | Destaque neon / HUD |
| `--neon-teal` | `#45a29e` | Secundário |
| `--gold` | `#c5a059` | Moedas / itens valiosos |
| `--gold-bright` | `#ffd700` | Lendário / destaque máximo |
| `--danger` | `#ff4757` | HP / Ataque / Perigo |
| `--arcane-purple` | `#a855f7` | Magia / Poeira Arcana |
| `--success` | `#2ed573` | Cura / Conquistas |

**Fontes:**
- `Cinzel` — Títulos épicos e nomes de seção
- `Exo 2` — HUD, stats, badges e valores
- `Inter` — Textos corridos e descrições

---

## 📚 Contexto Acadêmico

Este projeto foi desenvolvido para a disciplina de **Programação Orientada a Objetos (POO)**, demonstrando na prática:

- ✅ **Herança e Polimorfismo** — Classes de personagem com passivas únicas
- ✅ **Encapsulamento** — Modelos ORM com métodos `to_dict()`, `set_password()`, `check_password()`
- ✅ **Abstração** — `game_logic.py` separa completamente a lógica de negócio das rotas
- ✅ **Padrão MVC** — Models (`models.py`) · Controllers (`app.py`) · Views (`templates/`)
- ✅ **REST API** — Comunicação stateless via JSON entre frontend e backend
- ✅ **Persistência Relacional** — ORM com relacionamentos 1:1 e 1:N com cascade delete
- ✅ **Segurança** — Hash de senhas, proteção de rotas com `@login_required`, rollback em transações

---

## 👤 Autor

Desenvolvido como projeto de POO — 2026.

---

*Que sua lâmina nunca esmoreça, campeão.* ⚔️

