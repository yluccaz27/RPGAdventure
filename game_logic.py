import time
import random
import math

CLASSES = {
    "Guerreiro": {
        "hp_base": 130,
        "ataque_base": 14,
        "defesa_base": 6,
        "esquiva_base": 5,
        "critico_base": 10,
        "passiva": "Baluarte: Reduz 35% do dano sofrido quando estiver abaixo de 40% de vida.",
        "icon": "🛡️",
        "imagem": "/static/images/classes/guerreiro.svg",
        "descricao": "Mestre da espada e do escudo, capaz de resistir aos golpes mais brutais."
    },
    "Berserker": {
        "hp_base": 115,
        "ataque_base": 18,
        "defesa_base": 2,
        "esquiva_base": 5,
        "critico_base": 15,
        "passiva": "Fúria: Ganha +1% de dano extra para cada 2% de HP perdido.",
        "icon": "🪓",
        "imagem": "/static/images/classes/berserker.svg",
        "descricao": "Guerreiro sanguinário que fica muito mais letal à beira da morte."
    },
    "Mago": {
        "hp_base": 85,
        "ataque_base": 22,
        "defesa_base": 1,
        "esquiva_base": 8,
        "critico_base": 25,
        "passiva": "Fluxo Arcano: 25% de chance de causar Crítico com dano dobrado (2x).",
        "icon": "🔮",
        "imagem": "/static/images/classes/mago.svg",
        "descricao": "Conjurador com feitiços explosivos e alto potencial de dano crítico."
    },
    "Ladino": {
        "hp_base": 95,
        "ataque_base": 16,
        "defesa_base": 3,
        "esquiva_base": 20,
        "critico_base": 20,
        "passiva": "Esquiva Sombria: 20% de chance de esquivar completamente de qualquer golpe.",
        "icon": "🗡️",
        "imagem": "/static/images/classes/ladino.svg",
        "descricao": "Assassino ágil que desliza pelas sombras evitando dano mortal."
    },
    "Ninja": {
        "hp_base": 90,
        "ataque_base": 17,
        "defesa_base": 2,
        "esquiva_base": 25,
        "critico_base": 30,
        "passiva": "Sombra Veloz: 25% de esquiva natural e 30% de chance de Crítico triplo (3x de dano).",
        "icon": "🥷",
        "imagem": "/static/images/classes/ninja.svg",
        "descricao": "Guerreiro veloz das sombras focado em esquivas extremas e acertos críticos mortais."
    },
    "Viking": {
        "hp_base": 140,
        "ataque_base": 15,
        "defesa_base": 5,
        "esquiva_base": 5,
        "critico_base": 12,
        "passiva": "Escudo Nórdico & Retaliação: Absorve 25% do dano e contra-ataca devolvendo 50% do dano recebido.",
        "icon": "🛡️",
        "imagem": "/static/images/classes/viking.svg",
        "descricao": "Bárbaro de constituição massiva que devolve os golpes sofridos contra seus agressores."
    },
    "Monge": {
        "hp_base": 110,
        "ataque_base": 13,
        "defesa_base": 4,
        "esquiva_base": 15,
        "critico_base": 15,
        "passiva": "Regeneração do Chi: Canaliza energia interior e recupera 8% do HP máximo a cada turno de batalha.",
        "icon": "🧘",
        "imagem": "/static/images/classes/monge.svg",
        "descricao": "Lutador espiritual que regenera constantemente sua energia vital durante a peleja."
    },
    "Paladino": {
        "hp_base": 125,
        "ataque_base": 14,
        "defesa_base": 8,
        "esquiva_base": 5,
        "critico_base": 10,
        "passiva": "Luz Sagrada: Defesa impenetrável e +60% de dano bônus devastador contra mortos-vivos.",
        "icon": "⚔️",
        "imagem": "/static/images/classes/paladino.svg",
        "descricao": "Campeão da retidão revestido em armadura sacra, temido por todas as abominações necróticas."
    }
}

ARMAS_INICIAIS = {
    "Espada de Ferro": {
        "id": "arma_ini_1",
        "nome": "Espada de Ferro",
        "tipo": "arma",
        "raridade": "Comum",
        "upgrade_lvl": 0,
        "bonus_ataque": 6,
        "bonus_defesa": 0,
        "bonus_hp": 0,
        "bonus_critico": 2,
        "bonus_esquiva": 0,
        "preco": 30,
        "imagem": "/static/images/items/espada.svg",
        "descricao": "Lâmina afiada tradicional de aço temperado."
    },
    "Machado de Batalha": {
        "id": "arma_ini_2",
        "nome": "Machado de Batalha",
        "tipo": "arma",
        "raridade": "Comum",
        "upgrade_lvl": 0,
        "bonus_ataque": 9,
        "bonus_defesa": 0,
        "bonus_hp": 0,
        "bonus_critico": 4,
        "bonus_esquiva": 0,
        "preco": 35,
        "imagem": "/static/images/items/machado.svg",
        "descricao": "Lâmina pesada de duas mãos com alto impacto de corte."
    },
    "Cajado Místico": {
        "id": "arma_ini_3",
        "nome": "Cajado Místico",
        "tipo": "arma",
        "raridade": "Comum",
        "upgrade_lvl": 0,
        "bonus_ataque": 8,
        "bonus_defesa": 0,
        "bonus_hp": 10,
        "bonus_critico": 5,
        "bonus_esquiva": 0,
        "preco": 35,
        "imagem": "/static/images/items/cajado.svg",
        "descricao": "Madeira encantada que ressoa com poder arcano."
    },
    "Adaga Sorrateira": {
        "id": "arma_ini_4",
        "nome": "Adaga Sorrateira",
        "tipo": "arma",
        "raridade": "Comum",
        "upgrade_lvl": 0,
        "bonus_ataque": 5,
        "bonus_defesa": 1,
        "bonus_hp": 0,
        "bonus_critico": 8,
        "bonus_esquiva": 4,
        "preco": 28,
        "imagem": "/static/images/items/adaga.svg",
        "descricao": "Rápida e mortal nas mãos de quem busca pontos fracos."
    }
}

REGIOES_MAPA = {
    "floresta": {
        "id": "floresta",
        "nome": "Floresta dos Goblins",
        "nivel_minimo": 1,
        "icone": "🌲",
        "descricao": "Bosque nebuloso e traiçoeiro repleto de emboscadas e ladrões de trilha.",
        "mult_xp": 1.0,
        "mult_moedas": 1.0,
        "inimigos": [
            {"nome": "Goblin Ladrão", "hp_base": 42, "ataque_base": 9, "xp_base": 32, "moedas_base": 16, "poder": "Ataque Furtivo (25% chance de Crítico)", "icon": "👺", "imagem": "/static/images/enemies/goblin.svg", "tipo_criatura": "humanoide"},
            {"nome": "Lobo Sombrio", "hp_base": 55, "ataque_base": 12, "xp_base": 45, "moedas_base": 22, "poder": "Mordida Feroz (Dano rápido com sangramento)", "icon": "🐺", "imagem": "/static/images/enemies/lobo.svg", "tipo_criatura": "fera"},
            {"nome": "Orc das Matas", "hp_base": 85, "ataque_base": 16, "xp_base": 75, "moedas_base": 35, "poder": "Porrete Pesado (Causa 1.4x de dano)", "icon": "👹", "imagem": "/static/images/enemies/orc.svg", "tipo_criatura": "humanoide"}
        ]
    },
    "montanha": {
        "id": "montanha",
        "nome": "Montanha dos Vikings",
        "nivel_minimo": 3,
        "icone": "🏔️",
        "descricao": "Picos escarpados e gélidos dominados por invasores nórdicos e feras da neve.",
        "mult_xp": 1.4,
        "mult_moedas": 1.4,
        "inimigos": [
            {"nome": "Saqueador Viking", "hp_base": 95, "ataque_base": 19, "xp_base": 110, "moedas_base": 50, "poder": "Grito de Batalha Nórdico (+4 de Ataque)", "icon": "🪓", "imagem": "/static/images/enemies/viking_enemy.svg", "tipo_criatura": "humanoide"},
            {"nome": "Urso Glacial", "hp_base": 120, "ataque_base": 22, "xp_base": 135, "moedas_base": 60, "poder": "Patada Destruidora (Ignora 3 de armadura)", "icon": "🐻", "imagem": "/static/images/enemies/lobo.svg", "tipo_criatura": "fera"},
            {"nome": "Berserker da Nevasca", "hp_base": 150, "ataque_base": 26, "xp_base": 170, "moedas_base": 80, "poder": "Fúria de Thor (Crítico violento de 1.8x)", "icon": "⚡", "imagem": "/static/images/enemies/viking_enemy.svg", "tipo_criatura": "humanoide"}
        ]
    },
    "castelo": {
        "id": "castelo",
        "nome": "Castelo do Lich",
        "nivel_minimo": 5,
        "icone": "🏰",
        "descricao": "Fortaleza sombria e esquecida, infestada por legiões de mortos-vivos.",
        "mult_xp": 1.9,
        "mult_moedas": 1.8,
        "inimigos": [
            {"nome": "Esqueleto Guardião", "hp_base": 135, "ataque_base": 25, "xp_base": 190, "moedas_base": 90, "poder": "Armadura Óssea (Absorve 4 de dano físico)", "icon": "💀", "imagem": "/static/images/enemies/esqueleto.svg", "tipo_criatura": "morto_vivo"},
            {"nome": "Cavaleiro Maldito", "hp_base": 175, "ataque_base": 30, "xp_base": 240, "moedas_base": 115, "poder": "Espada Espectral (Dano necrótico penetrante)", "icon": "⚰️", "imagem": "/static/images/enemies/esqueleto.svg", "tipo_criatura": "morto_vivo"},
            {"nome": "Lich Sombrio Ancião", "hp_base": 230, "ataque_base": 36, "xp_base": 330, "moedas_base": 160, "poder": "Dreno de Vida Supremo (Recupera 50% do dano)", "icon": "🧙‍♂️", "imagem": "/static/images/enemies/lich.svg", "tipo_criatura": "morto_vivo"}
        ]
    },
    "vulcao": {
        "id": "vulcao",
        "nome": "Vulcão do Dragão",
        "nivel_minimo": 8,
        "icone": "🌋",
        "descricao": "Cratera incandescente habitada por monstros de puro fogo e o Dragão Ancião.",
        "mult_xp": 2.6,
        "mult_moedas": 2.5,
        "inimigos": [
            {"nome": "Salamandra de Magma", "hp_base": 210, "ataque_base": 38, "xp_base": 380, "moedas_base": 180, "poder": "Cuspe de Fogo Contínuo", "icon": "🦎", "imagem": "/static/images/enemies/goblin.svg", "tipo_criatura": "fera"},
            {"nome": "Golem de Lava Ardente", "hp_base": 290, "ataque_base": 44, "xp_base": 490, "moedas_base": 240, "poder": "Corpo de Magma (Absorve 6 de dano)", "icon": "🗿", "imagem": "/static/images/enemies/golem.svg", "tipo_criatura": "elemental"},
            {"nome": "Dragão Vermelho Milenar", "hp_base": 420, "ataque_base": 56, "xp_base": 750, "moedas_base": 400, "poder": "Sopro de Fogo Devastador (2x de dano)", "icon": "🐉", "imagem": "/static/images/enemies/dragao.svg", "tipo_criatura": "dragao"}
        ]
    }
}

# 20 ANDARES DE CHEFES NA MASMORRA
MASMORRA_ANDAR_CHEFES = [
    {"andar": 1, "nome": "Gárgula de Pedra", "hp": 120, "ataque": 18, "defesa": 8, "poder": "Pele Pétrea (-5 Dano)", "icon": "🦇", "imagem": "/static/images/enemies/goblin.svg", "xp": 150, "moedas": 80},
    {"andar": 2, "nome": "Lobo Alfa das Sombras", "hp": 160, "ataque": 24, "defesa": 6, "poder": "Mordida Hemorrágica", "icon": "🐺", "imagem": "/static/images/enemies/lobo.svg", "xp": 220, "moedas": 120},
    {"andar": 3, "nome": "Carniceiro Orc", "hp": 210, "ataque": 29, "defesa": 10, "poder": "Golpe Decapitador (1.5x Dano)", "icon": "👹", "imagem": "/static/images/enemies/orc.svg", "xp": 300, "moedas": 160},
    {"andar": 4, "nome": "Banshee Lamuriante", "hp": 260, "ataque": 34, "defesa": 8, "poder": "Grito Ensudecedor (Reduz Atq)", "icon": "👻", "imagem": "/static/images/enemies/lich.svg", "xp": 400, "moedas": 210},
    {"andar": 5, "nome": "Jarl Esqueleto Rei", "hp": 330, "ataque": 40, "defesa": 15, "poder": "Armadura de Mil Ossos", "icon": "👑", "imagem": "/static/images/enemies/esqueleto.svg", "xp": 520, "moedas": 280},
    {"andar": 6, "nome": "Quimera Abissal", "hp": 400, "ataque": 46, "defesa": 12, "poder": "Veneno de Serpente Triplo", "icon": "🦁", "imagem": "/static/images/enemies/lobo.svg", "xp": 650, "moedas": 350},
    {"andar": 7, "nome": "Viking Berserker Ancestral", "hp": 480, "ataque": 53, "defesa": 14, "poder": "Ira Valquíria (+15 Atq)", "icon": "🪓", "imagem": "/static/images/enemies/viking_enemy.svg", "xp": 800, "moedas": 420},
    {"andar": 8, "nome": "Golem de Obsidiana", "hp": 580, "ataque": 58, "defesa": 22, "poder": "Defesa de Rocha Impenetrável", "icon": "🗿", "imagem": "/static/images/enemies/golem.svg", "xp": 980, "moedas": 500},
    {"andar": 9, "nome": "Necromante das Catacumbas", "hp": 680, "ataque": 65, "defesa": 16, "poder": "Explosão de Almas Negras", "icon": "🧙‍♂️", "imagem": "/static/images/enemies/lich.svg", "xp": 1200, "moedas": 600},
    {"andar": 10, "nome": "Lorde Vampiro Vlad", "hp": 800, "ataque": 72, "defesa": 18, "poder": "Banquete de Sangue (60% Cura)", "icon": "🧛", "imagem": "/static/images/enemies/lich.svg", "xp": 1500, "moedas": 750},
    {"andar": 11, "nome": "Minotauro do Labirinto", "hp": 950, "ataque": 80, "defesa": 22, "poder": "Investida Esmagadora", "icon": "🐂", "imagem": "/static/images/enemies/orc.svg", "xp": 1850, "moedas": 900},
    {"andar": 12, "nome": "Hydra Venenosa de 5 Cabeças", "hp": 1120, "ataque": 88, "defesa": 20, "poder": "Multi-Ataque Dilacerante", "icon": "🐍", "imagem": "/static/images/enemies/goblin.svg", "xp": 2250, "moedas": 1100},
    {"andar": 13, "nome": "Cavaleiro do Apocalipse", "hp": 1300, "ataque": 96, "defesa": 26, "poder": "Lâmina da Praga Mortal", "icon": "🏇", "imagem": "/static/images/enemies/esqueleto.svg", "xp": 2700, "moedas": 1300},
    {"andar": 14, "nome": "Colosso de Magma Puro", "hp": 1500, "ataque": 105, "defesa": 30, "poder": "Onda Incandescente Devastadora", "icon": "🌋", "imagem": "/static/images/enemies/golem.svg", "xp": 3200, "moedas": 1550},
    {"andar": 15, "nome": "Dragão de Gelo Cristalino", "hp": 1750, "ataque": 115, "defesa": 28, "poder": "Sopro do Zero Absoluto", "icon": "❄️", "imagem": "/static/images/enemies/dragao.svg", "xp": 3800, "moedas": 1850},
    {"andar": 16, "nome": "Arquidemônio Ignis", "hp": 2050, "ataque": 126, "defesa": 32, "poder": "Inferno Eterno (Chamas Negras)", "icon": "😈", "imagem": "/static/images/enemies/orc.svg", "xp": 4500, "moedas": 2200},
    {"andar": 17, "nome": "Titã do Caos Primordial", "hp": 2400, "ataque": 138, "defesa": 36, "poder": "Fenda Gravitacional Colossal", "icon": "🌌", "imagem": "/static/images/enemies/golem.svg", "xp": 5300, "moedas": 2600},
    {"andar": 18, "nome": "Lich Imperador Malakor", "hp": 2800, "ataque": 150, "defesa": 38, "poder": "Palavra da Morte Absoluta", "icon": "💀", "imagem": "/static/images/enemies/lich.svg", "xp": 6200, "moedas": 3100},
    {"andar": 19, "nome": "Dragão Ancião Cataclísmico", "hp": 3300, "ataque": 165, "defesa": 42, "poder": "Supernova Dracônica Tripla", "icon": "🐉", "imagem": "/static/images/enemies/dragao.svg", "xp": 7400, "moedas": 3700},
    {"andar": 20, "nome": "Soberano do Vazio Cósmico", "hp": 4000, "ataque": 185, "defesa": 48, "poder": "Aniquilação da Existência (Chefe Supremo)", "icon": "👁️", "imagem": "/static/images/enemies/lich.svg", "xp": 10000, "moedas": 5000}
]

# 8 FATIAS DA ROLETA DA SORTE
ROLETA_FATIAS = [
    {"id": 0, "tipo": "moedas", "qtd": 100, "label": "100 🪙 Moedas", "cor": "#1e272e"},
    {"id": 1, "tipo": "xp", "qtd": 250, "label": "250 ✨ EXP", "cor": "#2f3542"},
    {"id": 2, "tipo": "pocoes", "qtd": 2, "label": "2 🧪 Poções", "cor": "#2ed573"},
    {"id": 3, "tipo": "poeira", "qtd": 25, "label": "25 🔮 Poeira", "cor": "#8854d0"},
    {"id": 4, "tipo": "moedas", "qtd": 300, "label": "300 🪙 Moedas", "cor": "#ffa502"},
    {"id": 5, "tipo": "xp", "qtd": 600, "label": "600 ✨ EXP", "cor": "#3867d6"},
    {"id": 6, "tipo": "poeira", "qtd": 60, "label": "60 🔮 Poeira", "cor": "#a55eea"},
    {"id": 7, "tipo": "equipamento", "qtd": 1, "label": "👑 Item Lendário", "cor": "#f39c12"}
]

CONFIG_TREINO = {
    "30s": {"chave": "30s", "nome": "Treino Básico de Reflexos", "duracao_segundos": 30, "xp": 45, "moedas": 25, "bonus_stats": {"ataque": 1, "defesa": 0, "hp_max": 4}, "descricao": "Aquecimento rápido golpeando o boneco de madeira com precisão."},
    "1m": {"chave": "1m", "nome": "Combate com Boneco de Palha", "duracao_segundos": 60, "xp": 110, "moedas": 50, "bonus_stats": {"ataque": 1, "defesa": 1, "hp_max": 8}, "descricao": "Exercício de técnicas marciais e posturas defensivas básicas."},
    "5m": {"chave": "5m", "nome": "Sparring Pesado na Guilda", "duracao_segundos": 300, "xp": 580, "moedas": 250, "bonus_stats": {"ataque": 4, "defesa": 3, "hp_max": 25}, "descricao": "Combate vigoroso com veteranos para calejar o corpo e aprimorar esquivas."},
    "15m": {"chave": "15m", "nome": "Sobrevivência Selvagem Extrema", "duracao_segundos": 900, "xp": 1950, "moedas": 800, "bonus_stats": {"ataque": 10, "defesa": 8, "hp_max": 65}, "descricao": "Isolamento rigoroso enfrentando os elementos naturais e feras vorazes."},
    "30m": {"chave": "30m", "nome": "Imersão no Santuário dos Titãs", "duracao_segundos": 1800, "xp": 4800, "moedas": 1900, "bonus_stats": {"ataque": 22, "defesa": 16, "hp_max": 140}, "descricao": "Meditação cósmica sob quedas d'água sagradas que eleva atributos ao ápice."}
}

NOMES_PREFIXOS = {
    "arma": ["Espada", "Lâmina", "Gládio", "Machado", "Martelo", "Adaga", "Cajado"],
    "peitoral": ["Cota de Malha", "Armadura de Placas", "Manto Protetor", "Couraça", "Túnica Rúnica"],
    "cabeca": ["Elmo Fechado", "Capacete de Ferro", "Tiara Mágica", "Capuz das Sombras", "Coroa de Mithril"],
    "anel": ["Anel Sinete", "Amuleto Ancestral", "Talismã Sagrado", "Aliança Arcana", "Relíquia da Fúria"]
}

SUFIXOS_POR_RARIDADE = {
    "Comum": ["de Ferro", "do Recruta", "do Caçador", "Simples", "do Viajante"],
    "Raro": ["das Sombras", "do Trovão", "da Chama", "Dracônico", "de Mithril", "do Vento"],
    "Épico": ["dos Titãs", "do Crepúsculo", "dos Deuses Antigos", "Solar Cósmico", "do Rei Imortal"],
    "Lendário": ["do Apocalipse", "do Dragão Primordial", "Celestial Infinito", "do Campeão Eterno"]
}

def criar_novo_jogador(nome, classe_nome, arma_nome):
    classe_info = CLASSES[classe_nome]
    arma_info = ARMAS_INICIAIS[arma_nome]

    player = {
        "nome": nome,
        "classe": classe_nome,
        "nivel": 1,
        "xp": 0,
        "xp_proximo": 60,
        "moedas": 80,
        "poeira_arcana": 15,
        "giros_gratis_roleta": 1,
        "hp_max_base": classe_info["hp_base"],
        "hp_atual": classe_info["hp_base"],
        "ataque_base": classe_info["ataque_base"],
        "defesa_base": classe_info["defesa_base"],
        "esquiva_base": classe_info["esquiva_base"],
        "critico_base": classe_info["critico_base"],
        # Academia de Atributos (Pontos comprados manualmente)
        "atributos_academia": {
            "forca": 0,       # +1 Atq
            "destreza": 0,    # +0.5% Crit e +0.5% Esquiva
            "vitalidade": 0,  # +8 HP Max
            "mente": 0        # +1 Defesa
        },
        "passiva": classe_info["passiva"],
        "icon": classe_info["icon"],
        "imagem": classe_info["imagem"],
        "descricao": classe_info["descricao"],
        "regiao_atual": "floresta",
        "masmorra_andar_atual": 1,
        "masmorras_completadas": 0,
        # Esconderijo (Gerações passivas)
        "esconderijo": {
            "mina_lvl": 1,           # Gera moedas
            "laboratorio_lvl": 1,     # Gera poções
            "timestamp_coleta": int(time.time()),
            "moedas_acumuladas": 0,
            "pocoes_acumuladas": 0
        },
        "pocoes": 3,
        "treino_bonus": {"ataque": 0, "defesa": 0, "hp_max": 0},
        "equipados": {
            "cabeca": None,
            "peitoral": None,
            "arma": arma_info,
            "anel": None
        },
        "inventario": []
    }
    return player

def calcular_status_totais(player, temp_buffs=None):
    treino = player.get("treino_bonus", {})
    acad = player.get("atributos_academia", {"forca": 0, "destreza": 0, "vitalidade": 0, "mente": 0})
    
    # Base + Treino AFK + Academia de Atributos
    ataque = player.get("ataque_base", 10) + treino.get("ataque", 0) + acad.get("forca", 0)
    defesa = player.get("defesa_base", 2) + treino.get("defesa", 0) + acad.get("mente", 0)
    hp_max = player.get("hp_max_base", 100) + treino.get("hp_max", 0) + (acad.get("vitalidade", 0) * 8)
    
    esquiva = player.get("esquiva_base", 5) + (acad.get("destreza", 0) * 0.5)
    critico = player.get("critico_base", 10) + (acad.get("destreza", 0) * 0.5)

    equipados = player.get("equipados", {})
    for slot, item in equipados.items():
        if item:
            # Bônus de upgrade do ferreiro (+10% por nível)
            up_mult = 1.0 + (item.get("upgrade_lvl", 0) * 0.10)
            ataque += int(item.get("bonus_ataque", 0) * up_mult)
            defesa += int(item.get("bonus_defesa", 0) * up_mult)
            hp_max += int(item.get("bonus_hp", 0) * up_mult)
            esquiva += item.get("bonus_esquiva", 0)
            critico += item.get("bonus_critico", 0)

    if temp_buffs:
        ataque += temp_buffs.get("ataque", 0)
        defesa += temp_buffs.get("defesa", 0)
        hp_max += temp_buffs.get("hp_max", 0)

    return {
        "ataque": ataque,
        "defesa": defesa,
        "hp_max": hp_max,
        "esquiva": min(75, int(esquiva)),
        "critico": min(85, int(critico))
    }

def verificar_level_up(player, logs):
    upou = False
    while player["xp"] >= player["xp_proximo"]:
        player["nivel"] += 1
        player["xp"] -= player["xp_proximo"]
        player["xp_proximo"] = int(player["xp_proximo"] * 1.55)
        player["hp_max_base"] += 20
        player["ataque_base"] += 3
        player["defesa_base"] += 2
        totais = calcular_status_totais(player)
        player["hp_atual"] = totais["hp_max"]
        upou = True
        logs.insert(0, f"🌟 LEVEL UP! {player['nome']} avançou para o Nível {player['nivel']}! (+20 HP Max, +3 Ataque, +2 Defesa e Vida Restaurada!)")
    return upou

def calcular_custo_atributo(pontos_atuais):
    # Custo progressivo de treino de atributo na Academia: 15, 25, 40, 60...
    return int(15 * (1.18 ** pontos_atuais))

def atualizar_recursos_esconderijo(player):
    esc = player.get("esconderijo")
    if not esc:
        return
    agora = int(time.time())
    tempo_passado = max(0, agora - esc.get("timestamp_coleta", agora))
    
    # Mina: 60 moedas/hora por nível
    mina_lvl = esc.get("mina_lvl", 1)
    taxa_moedas_segundo = (mina_lvl * 60) / 3600.0
    moedas_novas = int(tempo_passado * taxa_moedas_segundo)
    
    # Laboratório: 1 poção a cada (3600 / lab_lvl) segundos
    lab_lvl = esc.get("laboratorio_lvl", 1)
    taxa_pocoes_segundo = (lab_lvl * 1.0) / 3600.0
    pocoes_novas = int(tempo_passado * taxa_pocoes_segundo)
    
    esc["moedas_acumuladas"] = min(2000 * mina_lvl, esc.get("moedas_acumuladas", 0) + moedas_novas)
    esc["pocoes_acumuladas"] = min(10 * lab_lvl, esc.get("pocoes_acumuladas", 0) + pocoes_novas)
    esc["timestamp_coleta"] = agora

def gerar_inimigo_onda(onda, regiao_id="floresta"):
    regiao = REGIOES_MAPA.get(regiao_id, REGIOES_MAPA["floresta"])
    inimigos_regiao = regiao["inimigos"]

    if onda % 5 == 0:
        base = inimigos_regiao[-1]
        prefixo = f"CHEFE DA ONDA {onda}: "
    else:
        idx = min(len(inimigos_regiao) - 1, (onda - 1) % len(inimigos_regiao))
        base = inimigos_regiao[idx]
        prefixo = ""

    mult_regiao_xp = regiao.get("mult_xp", 1.0)
    mult_regiao_moedas = regiao.get("mult_moedas", 1.0)

    escala_hp = 1.0 + (onda - 1) * 0.28
    escala_atq = 1.0 + (onda - 1) * 0.20
    escala_xp = (1.0 + (onda - 1) * 0.30) * mult_regiao_xp
    escala_moedas = (1.0 + (onda - 1) * 0.35) * mult_regiao_moedas

    hp_total = int(base["hp_base"] * escala_hp)
    atq_total = int(base["ataque_base"] * escala_atq)
    xp_total = int(base["xp_base"] * escala_xp)
    moedas_total = int(base["moedas_base"] * escala_moedas)

    return {
        "nome": f"{prefixo}{base['nome']}",
        "regiao_id": regiao_id,
        "onda": onda,
        "hp_max": hp_total,
        "hp_atual": hp_total,
        "ataque": atq_total,
        "xp": xp_total,
        "moedas": moedas_total,
        "poder": base["poder"],
        "icon": base["icon"],
        "imagem": base["imagem"],
        "tipo_criatura": base.get("tipo_criatura", "monstro")
    }

def gerar_item_aleatorio(player_level, slot_especifico=None, raridade_forcada=None):
    tipos = ["cabeca", "peitoral", "arma", "anel"]
    tipo = slot_especifico if slot_especifico in tipos else random.choice(tipos)

    if raridade_forcada:
        raridade = raridade_forcada
        if raridade == "Lendário":
            mult_status, mult_preco = 3.8, 7.5
        elif raridade == "Épico":
            mult_status, mult_preco = 2.6, 4.2
        elif raridade == "Raro":
            mult_status, mult_preco = 1.7, 2.2
        else:
            mult_status, mult_preco = 1.0, 1.0
    else:
        roll = random.random()
        if roll < 0.50:
            raridade = "Comum"
            mult_status, mult_preco = 1.0, 1.0
        elif roll < 0.80:
            raridade = "Raro"
            mult_status, mult_preco = 1.7, 2.2
        elif roll < 0.95:
            raridade = "Épico"
            mult_status, mult_preco = 2.6, 4.2
        else:
            raridade = "Lendário"
            mult_status, mult_preco = 3.8, 7.5

    sufixo = random.choice(SUFIXOS_POR_RARIDADE[raridade])
    prefixo = random.choice(NOMES_PREFIXOS[tipo])
    nome = f"{prefixo} {sufixo}"

    bonus_atq = 0
    bonus_def = 0
    bonus_hp = 0
    bonus_esquiva = 0
    bonus_critico = 0

    base_val = max(2, int((player_level * 2.5 + random.randint(2, 6)) * mult_status))

    if tipo == "arma":
        bonus_atq = base_val
        bonus_critico = max(2, int(base_val * 0.6))
        if raridade in ["Épico", "Lendário"]:
            bonus_hp = int(base_val * 1.5)
            bonus_esquiva = max(1, base_val // 4)
        img_choices = ["/static/images/items/espada.svg", "/static/images/items/machado.svg", "/static/images/items/cajado.svg", "/static/images/items/adaga.svg"]
        imagem = random.choice(img_choices)

    elif tipo == "peitoral":
        bonus_def = max(2, int(base_val * 0.65))
        bonus_hp = base_val * 5
        if raridade in ["Épico", "Lendário"]:
            bonus_atq = max(1, base_val // 4)
        imagem = "/static/images/items/armadura.svg"

    elif tipo == "cabeca":
        bonus_def = max(1, int(base_val * 0.5))
        bonus_hp = base_val * 3
        if raridade in ["Raro", "Épico", "Lendário"]:
            bonus_esquiva = max(2, base_val // 3)
        if raridade == "Lendário":
            bonus_atq = max(2, base_val // 3)
        imagem = "/static/images/items/capacete.svg"

    else: # anel / amuleto
        bonus_atq = max(1, int(base_val * 0.45))
        bonus_def = max(1, int(base_val * 0.45))
        bonus_hp = base_val * 3
        bonus_critico = max(2, int(base_val * 0.5))
        bonus_esquiva = max(1, int(base_val * 0.35))
        imagem = "/static/images/items/anel.svg"

    preco = int(max(25, (bonus_atq * 8 + bonus_def * 9 + bonus_hp * 0.8 + bonus_critico * 6 + bonus_esquiva * 6) * mult_preco))
    item_id = f"item_{int(time.time() * 1000)}_{random.randint(100, 999)}"

    return {
        "id": item_id,
        "nome": nome,
        "tipo": tipo,
        "raridade": raridade,
        "upgrade_lvl": 0,
        "bonus_ataque": bonus_atq,
        "bonus_defesa": bonus_def,
        "bonus_hp": bonus_hp,
        "bonus_critico": bonus_critico,
        "bonus_esquiva": bonus_esquiva,
        "preco": preco,
        "imagem": imagem,
        "descricao": f"Equipamento {raridade} forjado para aventureiros de nível {player_level}."
    }

def gerar_itens_loja(player_level, count=4):
    tipos = ["cabeca", "peitoral", "arma", "anel"]
    itens = []
    for i in range(count):
        slot = tipos[i % len(tipos)]
        itens.append(gerar_item_aleatorio(player_level, slot_especifico=slot))
    return itens

def calcular_custo_reroll(reroll_count):
    if reroll_count == 0:
        return 0
    return 10 * (2 ** (reroll_count - 1))

def obter_poeira_desmontar(raridade):
    tabela = {
        "Comum": 5,
        "Raro": 15,
        "Épico": 35,
        "Lendário": 85
    }
    return tabela.get(raridade, 5)

def calcular_custo_upgrade(upgrade_atual):
    # Custo de upgrade +1 a +10
    lvl = upgrade_atual + 1
    custo_poeira = lvl * 6
    custo_moedas = lvl * 35
    return custo_poeira, custo_moedas
