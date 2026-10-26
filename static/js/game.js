/**
 * RPG Engine - Full-Stack Interactive Frontend
 * Damage Floaters, Screen Shake, Academia de Atributos, Ferreiro & Crafting,
 * Masmorra 20 Andares, Roleta da Sorte Canvas e Esconderijo Idle
 */

let gameState = null;
let trainingTimerInterval = null;
let serverTimeOffset = 0;
let currentSelectedMapRegion = 'floresta';

// ESTADO DA ROLETA DA SORTE
let wheelAngle = 0;
let isSpinningWheel = false;

document.addEventListener('DOMContentLoaded', () => {
    fetchGameState();
});

// SINCRONIZAÇÃO GERAL COM O BACKEND
async function fetchGameState() {
    try {
        const response = await fetch('/api/estado');
        const data = await response.json();
        if (data.success) {
            gameState = data;
            if (data.tempo_servidor) {
                serverTimeOffset = Math.floor(Date.now() / 1000) - data.tempo_servidor;
            }
            renderGame();
        }
    } catch (err) {
        console.error('Erro ao sincronizar estado:', err);
    }
}

// ==========================================================
// 0. AUTENTICAÇÃO (LOGIN / REGISTRO / LOGOUT COM SQLALCHEMY)
// ==========================================================
function showAuthModal() {
    const overlay = document.getElementById('authModalOverlay');
    if (overlay) overlay.classList.remove('hidden');
}

function hideAuthModal() {
    const overlay = document.getElementById('authModalOverlay');
    if (overlay) overlay.classList.add('hidden');
}

function switchAuthTab(tab) {
    const loginBtn = document.getElementById('tabAuthLogin');
    const regBtn = document.getElementById('tabAuthRegister');
    const loginForm = document.getElementById('loginForm');
    const regForm = document.getElementById('registerForm');
    const errorBox = document.getElementById('authErrorMessage');
    if (errorBox) errorBox.classList.add('hidden');

    if (tab === 'login') {
        loginBtn.classList.add('active');
        regBtn.classList.remove('active');
        loginForm.classList.remove('hidden');
        regForm.classList.add('hidden');
    } else {
        loginBtn.classList.remove('active');
        regBtn.classList.add('active');
        loginForm.classList.add('hidden');
        regForm.classList.remove('hidden');
    }
}

function showAuthError(msg) {
    const errorBox = document.getElementById('authErrorMessage');
    if (errorBox) {
        errorBox.textContent = msg;
        errorBox.classList.remove('hidden');
    }
}

async function handleLogin(e) {
    e.preventDefault();
    const username = document.getElementById('loginUsername').value.trim();
    const password = document.getElementById('loginPassword').value;

    try {
        const res = await fetch('/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        const data = await res.json();
        if (data.success) {
            await fetchGameState();
        } else {
            showAuthError(data.message || 'Falha no login.');
        }
    } catch (err) {
        showAuthError('Erro de conexão ao efetuar login.');
    }
}

async function handleRegister(e) {
    e.preventDefault();
    const username = document.getElementById('regUsername').value.trim();
    const password = document.getElementById('regPassword').value;

    try {
        const res = await fetch('/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        const data = await res.json();
        if (data.success) {
            await fetchGameState();
        } else {
            showAuthError(data.message || 'Falha no registro.');
        }
    } catch (err) {
        showAuthError('Erro de conexão ao criar conta.');
    }
}

async function handleLogout() {
    try {
        const res = await fetch('/logout', { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            await fetchGameState();
        }
    } catch (err) {
        console.error('Erro ao sair:', err);
    }
}

// RENDERIZAÇÃO GERAL
function renderGame() {
    if (!gameState) return;

    if (!gameState.authenticated) {
        showAuthModal();
        hideCharacterCreation();
        const app = document.getElementById('gameApp');
        if (app) app.classList.add('hidden');
        return;
    }

    hideAuthModal();

    if (!gameState.game_started) {
        showCharacterCreation();
        const app = document.getElementById('gameApp');
        if (app) app.classList.add('hidden');
        return;
    } else {
        hideCharacterCreation();
        const app = document.getElementById('gameApp');
        if (app) app.classList.remove('hidden');
    }

    renderHUD();
    renderAventura();
    renderMasmorra();
    renderPerfil();
    renderEsconderijo();
    renderRoleta();
    renderMapa();
    renderTreino();
    renderLoja();
    renderLogs();
}

// ==========================================================
// 1. HUD GLOBAL (CABEÇALHO PERSISTENTE)
// ==========================================================
function renderHUD() {
    const p = gameState.player;
    if (!p) return;

    document.getElementById('hudAvatarImg').src = p.imagem || '/static/images/classes/guerreiro.svg';
    document.getElementById('hudClassIcon').textContent = p.icon || '🛡️';
    document.getElementById('hudHeroName').textContent = p.nome;
    document.getElementById('hudHeroClass').textContent = p.classe;
    document.getElementById('hudHeroLevel').textContent = `Lvl ${p.nivel}`;

    const regiaoAtual = (gameState.regioes_mapa && gameState.regioes_mapa[p.regiao_atual]) 
        ? gameState.regioes_mapa[p.regiao_atual] 
        : { nome: 'Floresta dos Goblins', icone: '🌲' };
    document.getElementById('hudCurrentRegion').textContent = `${regiaoAtual.icone} ${regiaoAtual.nome}`;

    // Barra de XP
    const xpPct = Math.min(100, Math.max(0, (p.xp / p.xp_proximo) * 100));
    document.getElementById('hudXpFill').style.width = `${xpPct}%`;
    document.getElementById('hudXpNumbers').textContent = `${p.xp} / ${p.xp_proximo}`;

    // Barra de HP
    const hpMax = p.hp_max_total || 100;
    const hpCur = Math.max(0, Math.min(hpMax, p.hp_atual));
    const hpPct = Math.min(100, Math.max(0, (hpCur / hpMax) * 100));
    document.getElementById('hudHpFill').style.width = `${hpPct}%`;
    document.getElementById('hudHpNumbers').textContent = `${hpCur} / ${hpMax}`;

    // Buff Temporário da Expedição
    const buffBadge = document.getElementById('hudBuffBadge');
    const buffs = p.temp_buffs || { ataque: 0, defesa: 0, hp_max: 0 };
    if (buffs.ataque > 0 || buffs.defesa > 0 || buffs.hp_max > 0) {
        buffBadge.classList.remove('hidden');
        document.getElementById('buffAtq').textContent = buffs.ataque;
        document.getElementById('buffDef').textContent = buffs.defesa;
        document.getElementById('buffHp').textContent = buffs.hp_max;
    } else {
        buffBadge.classList.add('hidden');
    }

    // Atributos no HUD
    document.getElementById('hudTotalAtk').textContent = p.ataque_total;
    document.getElementById('hudTotalDef').textContent = p.defesa_total;
    document.getElementById('hudTotalDodge').textContent = `${p.esquiva_total}%`;
    document.getElementById('hudTotalCrit').textContent = `${p.critico_total}%`;
    document.getElementById('hudGold').textContent = p.moedas;
    document.getElementById('hudDust').textContent = p.poeira_arcana || 0;
    document.getElementById('hudPotions').textContent = p.pocoes;

    const authUser = document.getElementById('hudAuthUsername');
    if (authUser) {
        authUser.textContent = gameState.username || (gameState.user && gameState.user.username) || 'Jogador';
    }

    // Subtítulos nas Abas
    document.getElementById('waveSubBadge').textContent = gameState.aventura.ativa 
        ? `Onda ${gameState.aventura.onda}` : 'Pronto';
    document.getElementById('dungeonSubBadge').textContent = `Andar ${p.masmorra_andar_atual || 1}`;
    document.getElementById('spinSubBadge').textContent = p.giros_gratis_roleta > 0 ? '1 Giro Grátis!' : '50 🪙 Giro';
    document.getElementById('trainSubBadge').textContent = gameState.treino.ativo ? 'Em Curso' : 'Inativo';
    document.getElementById('shopSubBadge').textContent = `${gameState.loja.itens.length} Itens`;
}

// ==========================================================
// 2. NAVEGAÇÃO POR ABAS (SPA)
// ==========================================================
function switchTab(tabId) {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-pane').forEach(pane => pane.classList.remove('active'));

    const tabButtons = {
        'aventura': 'tabBtnAventura',
        'masmorra': 'tabBtnMasmorra',
        'perfil': 'tabBtnPerfil',
        'esconderijo': 'tabBtnEsconderijo',
        'roleta': 'tabBtnRoleta',
        'mapa': 'tabBtnMapa',
        'treino': 'tabBtnTreino',
        'loja': 'tabBtnLoja'
    };

    const tabPanes = {
        'aventura': 'tabContentAventura',
        'masmorra': 'tabContentMasmorra',
        'perfil': 'tabContentPerfil',
        'esconderijo': 'tabContentEsconderijo',
        'roleta': 'tabContentRoleta',
        'mapa': 'tabContentMapa',
        'treino': 'tabContentTreino',
        'loja': 'tabContentLoja'
    };

    if (tabButtons[tabId] && tabPanes[tabId]) {
        document.getElementById(tabButtons[tabId]).classList.add('active');
        document.getElementById(tabPanes[tabId]).classList.add('active');
    }

    if (tabId === 'roleta') {
        drawWheelCanvas();
    }
}

// ==========================================================
// 3. FEEDBACK VISUAL DE COMBATE (FLOATERS & SCREEN SHAKE)
// ==========================================================
function spawnDamageFloater(containerId, text, type = 'normal') {
    const box = document.getElementById(containerId);
    if (!box) return;

    const floater = document.createElement('div');
    floater.className = `damage-floater ${type}`;
    floater.textContent = text;
    box.appendChild(floater);

    setTimeout(() => {
        if (floater.parentNode) {
            floater.parentNode.removeChild(floater);
        }
    }, 1200);
}

function triggerScreenShake(elementId) {
    const el = document.getElementById(elementId);
    if (!el) return;
    el.classList.remove('screen-shake');
    // Force reflow
    void el.offsetWidth;
    el.classList.add('screen-shake');
    setTimeout(() => el.classList.remove('screen-shake'), 450);
}

function processCombatFloaters(combatData, isDungeon = false) {
    if (!combatData) return;

    const playerBox = isDungeon ? 'dungeonPlayerFloaterBox' : 'playerFloaterBox';
    const enemyBox = isDungeon ? 'dungeonBossFloaterBox' : 'enemyFloaterBox';
    const playerCard = isDungeon ? 'dungeonPlayerCard' : 'playerCombatCard';
    const enemyCard = isDungeon ? 'dungeonBossCard' : 'enemyCombatCard';

    // Cura de Poção
    if (combatData.pocao_cura) {
        spawnDamageFloater(playerBox, `+${combatData.pocao_cura} HP`, 'heal');
        return;
    }

    // Cura Monge
    if (combatData.monge_cura && combatData.monge_cura > 0) {
        spawnDamageFloater(playerBox, `+${combatData.monge_cura} Chi`, 'heal');
    }

    // Dano causado pelo Jogador
    if (combatData.dano_jogador && combatData.dano_jogador > 0) {
        if (combatData.critico) {
            spawnDamageFloater(enemyBox, `CRÍTICO! -${combatData.dano_jogador}`, 'crit');
            triggerScreenShake(enemyCard);
        } else {
            spawnDamageFloater(enemyBox, `-${combatData.dano_jogador}`, 'normal');
            triggerScreenShake(enemyCard);
        }
    }

    // Contra-ataque Viking
    if (combatData.viking_retaliacao && combatData.viking_retaliacao > 0) {
        setTimeout(() => {
            spawnDamageFloater(enemyBox, `RETALIAÇÃO! -${combatData.viking_retaliacao}`, 'counter');
            triggerScreenShake(enemyCard);
        }, 250);
    }

    // Turno do Inimigo
    if (combatData.esquivou) {
        spawnDamageFloater(playerBox, 'ESQUIVOU!', 'dodge');
    } else if (combatData.dano_inimigo && combatData.dano_inimigo > 0) {
        setTimeout(() => {
            spawnDamageFloater(playerBox, `-${combatData.dano_inimigo}`, 'normal');
            triggerScreenShake(playerCard);
        }, 200);
    }
}

// ==========================================================
// 4. ABA 1: AVENTURA (MODO ONDAS NA REGIÃO ATUAL)
// ==========================================================
function renderAventura() {
    const adv = gameState.aventura;
    const p = gameState.player;
    if (!adv || !p) return;

    const regiaoAtual = (gameState.regioes_mapa && gameState.regioes_mapa[p.regiao_atual]) 
        ? gameState.regioes_mapa[p.regiao_atual] 
        : { nome: 'Floresta dos Goblins', icone: '🌲', descricao: 'Região de combate.' };

    document.getElementById('advRegionName').textContent = `${regiaoAtual.icone} ${regiaoAtual.nome}`;
    document.getElementById('advWaveTitle').textContent = `Onda ${adv.onda}`;
    document.getElementById('advLootGold').textContent = adv.espolio_moedas;
    document.getElementById('advLootXp').textContent = adv.espolio_xp;
    document.getElementById('advPotionCount').textContent = p.pocoes;

    document.getElementById('idleRegionIcon').textContent = regiaoAtual.icone;
    document.getElementById('idleRegionTitle').textContent = `Acampamento: ${regiaoAtual.nome}`;
    document.getElementById('idleRegionDesc').innerHTML = `${regiaoAtual.descricao}<br>
    Enfrente ondas e acumule espólio. <strong>Chance de 30% de Loot Drop direto para sua mochila!</strong>`;

    const idlePanel = document.getElementById('advIdlePanel');
    const battlePanel = document.getElementById('advBattlePanel');
    const turnActions = document.getElementById('combatTurnActions');
    const waveWonActions = document.getElementById('combatWaveWonActions');
    const defeatActions = document.getElementById('combatDefeatActions');

    if (!adv.ativa && adv.status === 'idle') {
        idlePanel.classList.remove('hidden');
        battlePanel.classList.add('hidden');
        return;
    }

    idlePanel.classList.add('hidden');
    battlePanel.classList.remove('hidden');

    // Jogador na Arena
    document.getElementById('advPlayerImg').src = p.imagem || '/static/images/classes/guerreiro.svg';
    document.getElementById('advPlayerName').textContent = `${p.nome} (Lvl ${p.nivel})`;
    const playerHpMax = p.hp_max_total || 100;
    const playerHpCur = Math.max(0, p.hp_atual);
    const pPct = (playerHpCur / playerHpMax) * 100;
    document.getElementById('advPlayerHpFill').style.width = `${pPct}%`;
    document.getElementById('advPlayerHpText').textContent = `${playerHpCur} / ${playerHpMax} HP`;
    document.getElementById('advPlayerPassive').textContent = `⚡ ${p.passiva}`;

    // Inimigo na Arena
    const enemy = adv.inimigo;
    if (enemy) {
        document.getElementById('advEnemyImg').src = enemy.imagem || '/static/images/enemies/goblin.svg';
        document.getElementById('advEnemyName').textContent = enemy.nome;
        const ePct = Math.max(0, (enemy.hp_atual / enemy.hp_max) * 100);
        document.getElementById('advEnemyHpFill').style.width = `${ePct}%`;
        document.getElementById('advEnemyHpText').textContent = `${enemy.hp_atual} / ${enemy.hp_max} HP`;
        document.getElementById('advEnemyPower').textContent = `🔥 ${enemy.poder}`;
    }

    turnActions.classList.add('hidden');
    waveWonActions.classList.add('hidden');
    defeatActions.classList.add('hidden');

    if (adv.status === 'em_batalha') {
        turnActions.classList.remove('hidden');
    } else if (adv.status === 'onda_vencida') {
        waveWonActions.classList.remove('hidden');
        document.getElementById('nextWaveNum').textContent = adv.onda + 1;
    } else if (adv.status === 'derrota') {
        defeatActions.classList.remove('hidden');
    }
}

async function startAdventure() {
    try {
        const res = await fetch('/api/aventura', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ acao: 'iniciar' })
        });
        const data = await res.json();
        if (data.success) {
            gameState = data;
            renderGame();
        }
    } catch (err) {
        console.error(err);
    }
}

async function adventureAction(acao) {
    try {
        const res = await fetch('/api/aventura', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ acao })
        });
        const data = await res.json();
        if (data.success) {
            gameState = data;
            renderGame();
            if (data.aventura && data.aventura.ultimo_combate) {
                processCombatFloaters(data.aventura.ultimo_combate, false);
            }
        } else {
            alert(data.message || 'Erro ao executar ação.');
        }
    } catch (err) {
        console.error(err);
    }
}

async function retreatAdventure() {
    const adv = gameState.aventura;
    if (!adv.ativa) return;
    if (!confirm(`Deseja recuar agora e resgatar ${adv.espolio_moedas} Moedas e ${adv.espolio_xp} XP acumulados?`)) {
        return;
    }
    try {
        const res = await fetch('/api/aventura', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ acao: 'recuar' })
        });
        const data = await res.json();
        if (data.success) {
            gameState = data;
            renderGame();
        }
    } catch (err) {
        console.error(err);
    }
}

// ==========================================================
// 5. ABA 2: MASMORRA (TORRE DOS 20 CHEFES)
// ==========================================================
function renderMasmorra() {
    const p = gameState.player;
    const masm = gameState.masmorra;
    const floorsList = document.getElementById('dungeonFloorsList');
    const battlePanel = document.getElementById('dungeonBattlePanel');
    if (!p || !gameState.masmorra_catalogo) return;

    const andarAtual = p.masmorra_andar_atual || 1;
    document.getElementById('dungeonFloorHeader').textContent = `Andar ${andarAtual} / 20`;

    // Arena do Chefe Ativa?
    if (masm && masm.ativa && masm.chefe) {
        battlePanel.classList.remove('hidden');
        document.getElementById('dungeonPlayerImg').src = p.imagem || '/static/images/classes/guerreiro.svg';
        document.getElementById('dungeonPlayerName').textContent = `${p.nome} (Lvl ${p.nivel})`;
        const pMax = p.hp_max_total || 100;
        const pCur = Math.max(0, p.hp_atual);
        document.getElementById('dungeonPlayerHpFill').style.width = `${(pCur / pMax) * 100}%`;
        document.getElementById('dungeonPlayerHpText').textContent = `${pCur} / ${pMax} HP`;

        const b = masm.chefe;
        document.getElementById('dungeonBossImg').src = b.imagem || '/static/images/enemies/goblin.svg';
        document.getElementById('dungeonBossName').textContent = `Andar ${b.andar}: ${b.nome}`;
        document.getElementById('dungeonBossPower').textContent = `👑 Poder: ${b.poder}`;
        const bPct = Math.max(0, (b.hp_atual / b.hp_max) * 100);
        document.getElementById('dungeonBossHpFill').style.width = `${bPct}%`;
        document.getElementById('dungeonBossHpText').textContent = `${b.hp_atual} / ${b.hp_max} HP`;

        const turnActions = document.getElementById('dungeonTurnActions');
        const vicActions = document.getElementById('dungeonVictoryActions');
        const defActions = document.getElementById('dungeonDefeatActions');

        turnActions.classList.add('hidden');
        vicActions.classList.add('hidden');
        defActions.classList.add('hidden');

        if (masm.status === 'em_batalha') {
            turnActions.classList.remove('hidden');
        } else if (masm.status === 'vitoria') {
            vicActions.classList.remove('hidden');
        } else if (masm.status === 'derrota') {
            defActions.classList.remove('hidden');
        }
    } else {
        battlePanel.classList.add('hidden');
    }

    // Renderiza lista dos 20 andares
    floorsList.innerHTML = '';
    gameState.masmorra_catalogo.forEach(f => {
        const card = document.createElement('div');
        const isCompleted = f.andar < andarAtual;
        const isCurrent = f.andar === andarAtual;
        const isLocked = f.andar > andarAtual;

        card.className = `floor-card ${isCompleted ? 'completed' : isCurrent ? 'current' : 'locked'}`;

        let statusText = isCompleted ? '✅ Conquistado' : isCurrent ? '⚔️ Desafio Atual' : '🔒 Bloqueado';

        card.innerHTML = `
            <div class="floor-number-badge">${f.andar}</div>
            <div class="floor-card-info">
                <h5>${f.icon} ${f.nome}</h5>
                <small>HP: ${f.hp} | Atq: ${f.ataque} | Recompensa: Baú Lendário</small>
                <div style="font-size: 0.72rem; font-weight: bold; color: ${isCurrent ? '#f1c40f' : isCompleted ? '#2ed573' : '#8c92b2'};">
                    ${statusText}
                </div>
            </div>
            ${isCurrent ? `<button class="btn btn-warning btn-sm" onclick="initDungeonFloor()">Desafiar</button>` : ''}
        `;
        floorsList.appendChild(card);
    });
}

async function initDungeonFloor() {
    try {
        const res = await fetch('/api/masmorra/iniciar', { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            gameState = data;
            renderGame();
        } else {
            alert(data.message || 'Erro ao iniciar masmorra.');
        }
    } catch (err) {
        console.error(err);
    }
}

async function dungeonAction(acao) {
    try {
        const res = await fetch('/api/masmorra/atacar', { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            gameState = data;
            renderGame();
            if (data.masmorra && data.masmorra.ultimo_combate) {
                processCombatFloaters(data.masmorra.ultimo_combate, true);
            }
        } else {
            alert(data.message || 'Erro ao atacar o chefe.');
        }
    } catch (err) {
        console.error(err);
    }
}

async function dungeonQuickPotion() {
    await quickUsePotion();
}

// ==========================================================
// 6. ABA 3: PERFIL, ACADEMIA DE ATRIBUTOS E FERREIRO
// ==========================================================
function renderPerfil() {
    const p = gameState.player;
    if (!p) return;

    // Perfil
    document.getElementById('profileHeroImg').src = p.imagem || '/static/images/classes/guerreiro.svg';
    document.getElementById('profileHeroName').textContent = p.nome;
    document.getElementById('profileHeroClass').textContent = `${p.icon} ${p.classe}`;
    document.getElementById('profileHeroLvl').textContent = `Nível ${p.nivel}`;
    document.getElementById('profilePassiveDesc').textContent = `⚡ ${p.passiva}`;

    document.getElementById('profileStatHp').textContent = p.hp_max_total;
    document.getElementById('profileStatAtk').textContent = p.ataque_total;
    document.getElementById('profileStatDef').textContent = p.defesa_total;
    document.getElementById('profileStatDodge').textContent = `${p.esquiva_total}%`;
    document.getElementById('profileStatCrit').textContent = `${p.critico_total}%`;
    document.getElementById('profileStatGold').textContent = p.moedas;

    // Academia de Atributos
    const acad = p.atributos_academia || { forca: 0, destreza: 0, vitalidade: 0, mente: 0 };
    const custos = gameState.custos_academia || {};

    document.getElementById('acadValForca').textContent = `${acad.forca} pts`;
    document.getElementById('acadCostForca').textContent = custos.forca || 15;

    document.getElementById('acadValDestreza').textContent = `${acad.destreza} pts`;
    document.getElementById('acadCostDestreza').textContent = custos.destreza || 15;

    document.getElementById('acadValVitalidade').textContent = `${acad.vitalidade} pts`;
    document.getElementById('acadCostVitalidade').textContent = custos.vitalidade || 15;

    document.getElementById('acadValMente').textContent = `${acad.mente} pts`;
    document.getElementById('acadCostMente').textContent = custos.mente || 15;

    // Paperdoll 4 Slots
    renderPaperdollSlot('cabeca', p.equipados.cabeca);
    renderPaperdollSlot('peitoral', p.equipados.peitoral);
    renderPaperdollSlot('arma', p.equipados.arma);
    renderPaperdollSlot('anel', p.equipados.anel);

    // Mochila / Forja
    renderMochila(p.inventario);
}

function renderPaperdollSlot(slotKey, item) {
    const capKey = slotKey.charAt(0).toUpperCase() + slotKey.slice(1);
    const bodyEl = document.getElementById(`pdBody${capKey}`);
    const unequipBtn = document.getElementById(`btnPdUnequip${capKey}`);
    const upgradeBtn = document.getElementById(`btnUpgrade${capKey}`);

    if (item) {
        unequipBtn.classList.remove('hidden');
        upgradeBtn.classList.remove('hidden');
        upgradeBtn.textContent = `✨ +${(item.upgrade_lvl || 0) + 1}`;

        bodyEl.innerHTML = `
            <div class="equipped-item-display">
                <div class="equipped-thumb">
                    <img src="${item.imagem}" alt="${item.nome}">
                </div>
                <div class="equipped-info">
                    <strong>${item.nome}</strong>
                    <div style="font-size: 0.7rem; color: #2ed573;">
                        ${item.bonus_ataque ? `+${item.bonus_ataque} Atq ` : ''}
                        ${item.bonus_defesa ? `+${item.bonus_defesa} Def ` : ''}
                        ${item.bonus_hp ? `+${item.bonus_hp} HP ` : ''}
                        ${item.bonus_critico ? `+${item.bonus_critico}% Crit ` : ''}
                        ${item.bonus_esquiva ? `+${item.bonus_esquiva}% Esq` : ''}
                    </div>
                </div>
            </div>
        `;
    } else {
        unequipBtn.classList.add('hidden');
        upgradeBtn.classList.add('hidden');
        bodyEl.innerHTML = `<span class="slot-empty">Nenhum item equipado</span>`;
    }
}

function renderMochila(inventario) {
    const invGrid = document.getElementById('profileInventoryGrid');
    const capLabel = document.getElementById('invCapacityLabel');
    invGrid.innerHTML = '';
    capLabel.textContent = `${inventario.length} Itens`;

    if (!inventario || inventario.length === 0) {
        invGrid.innerHTML = `<div class="inv-empty-msg">Sua mochila está vazia. Obtenha itens na Aventura, Masmorra ou Loja!</div>`;
        return;
    }

    inventario.forEach(item => {
        const card = document.createElement('div');
        card.className = `item-card rarity-${item.raridade}`;
        
        card.addEventListener('mouseenter', (e) => showComparisonTooltip(e, item));
        card.addEventListener('mouseleave', hideComparisonTooltip);
        card.addEventListener('mousemove', (e) => positionTooltip(e));

        const sellPrice = Math.max(5, Math.floor(item.preco * 0.5));
        const dustGained = item.raridade === 'Lendário' ? 85 : item.raridade === 'Épico' ? 35 : item.raridade === 'Raro' ? 15 : 5;

        card.innerHTML = `
            <div class="item-header">
                <span class="rarity-badge">${item.raridade}</span>
                <span style="font-size: 0.65rem; color: #a4b0be; text-transform: uppercase;">${item.tipo}</span>
            </div>

            <div class="item-image-wrap">
                <img src="${item.imagem}" alt="${item.nome}">
            </div>

            <div class="item-details">
                <h4>${item.nome}</h4>
                <div class="item-stats-chips">
                    ${item.bonus_ataque ? `<span class="stat-chip">⚔️ +${item.bonus_ataque}</span>` : ''}
                    ${item.bonus_defesa ? `<span class="stat-chip">🛡️ +${item.bonus_defesa}</span>` : ''}
                    ${item.bonus_hp ? `<span class="stat-chip">❤️ +${item.bonus_hp}</span>` : ''}
                </div>
            </div>

            <div class="item-card-footer">
                <button class="btn btn-primary btn-sm" onclick="equipInventoryItem('${item.id}')">
                    🛡️ Equipar
                </button>
                <button class="btn btn-dismantle btn-sm" onclick="dismantleItem('${item.id}')" title="Desmontar em Poeira Arcana">
                    🔮 Desmontar (+${dustGained})
                </button>
                <button class="btn btn-outline-danger btn-sm" onclick="sellInventoryItem('${item.id}')" title="Vender por Moedas">
                    💰 Vender (${sellPrice} 🪙)
                </button>
            </div>
        `;
        invGrid.appendChild(card);
    });
}

async function upgradeAttribute(atributo) {
    try {
        const res = await fetch('/api/atributos/upar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ atributo })
        });
        const data = await res.json();
        if (data.success) {
            gameState = data;
            renderGame();
        } else {
            alert(data.message || 'Moedas insuficientes.');
        }
    } catch (err) {
        console.error(err);
    }
}

async function dismantleItem(itemId) {
    hideComparisonTooltip();
    try {
        const res = await fetch('/api/ferreiro/desmontar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ item_id: itemId })
        });
        const data = await res.json();
        if (data.success) {
            gameState = data;
            renderGame();
        } else {
            alert(data.message || 'Erro ao desmontar item.');
        }
    } catch (err) {
        console.error(err);
    }
}

async function upgradeEquippedSlot(slot) {
    try {
        const res = await fetch('/api/ferreiro/upgrade', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ slot })
        });
        const data = await res.json();
        if (data.success) {
            gameState = data;
            renderGame();
        } else {
            alert(data.message || 'Recursos insuficientes para aprimoramento.');
        }
    } catch (err) {
        console.error(err);
    }
}

// ==========================================================
// 7. ABA 4: ESCONDERIJO DO HERÓI (IDLE / PASSIVO)
// ==========================================================
function renderEsconderijo() {
    const p = gameState.player;
    if (!p) return;
    const esc = p.esconderijo || { mina_lvl: 1, laboratorio_lvl: 1, moedas_acumuladas: 0, pocoes_acumuladas: 0 };

    document.getElementById('minaTitle').textContent = `Mina de Ouro (Nível ${esc.mina_lvl})`;
    document.getElementById('minaRate').textContent = `Produção: ${esc.mina_lvl * 60} moedas / hora`;
    document.getElementById('minaStored').textContent = `${esc.moedas_acumuladas || 0} 🪙`;
    document.getElementById('minaNextLvl').textContent = esc.mina_lvl + 1;
    document.getElementById('minaCostText').textContent = `Custo: ${esc.mina_lvl * 120} 🪙 | ${esc.mina_lvl * 15} 🔮`;

    document.getElementById('labTitle').textContent = `Laboratório Alquímico (Nível ${esc.laboratorio_lvl})`;
    document.getElementById('labRate').textContent = `Produção: ${esc.laboratorio_lvl} poção a cada 60 min`;
    document.getElementById('labStored').textContent = `${esc.pocoes_acumuladas || 0} 🧪`;
    document.getElementById('labNextLvl').textContent = esc.laboratorio_lvl + 1;
    document.getElementById('labCostText').textContent = `Custo: ${esc.laboratorio_lvl * 160} 🪙 | ${esc.laboratorio_lvl * 20} 🔮`;

    document.getElementById('qgSubBadge').textContent = `${(esc.moedas_acumuladas || 0)} 🪙 prontas`;
}

async function collectHideoutResources() {
    try {
        const res = await fetch('/api/qg/coletar', { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            gameState = data;
            renderGame();
        } else {
            alert(data.message || 'Nenhum recurso novo acumulado no momento.');
        }
    } catch (err) {
        console.error(err);
    }
}

async function upgradeBuilding(construcao) {
    try {
        const res = await fetch('/api/qg/upgrade', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ construcao })
        });
        const data = await res.json();
        if (data.success) {
            gameState = data;
            renderGame();
        } else {
            alert(data.message || 'Recursos insuficientes.');
        }
    } catch (err) {
        console.error(err);
    }
}

// ==========================================================
// 8. ABA 5: ROLETA DA SORTE DIÁRIA (CANVAS ANIMADO)
// ==========================================================
function renderRoleta() {
    const p = gameState.player;
    if (!p) return;

    const giros = p.giros_gratis_roleta || 0;
    const badge = document.getElementById('wheelSpinsBadge');
    if (giros > 0) {
        badge.textContent = `⭐ ${giros} Giro Grátis Disponível!`;
        document.getElementById('spinCostNotice').textContent = "Seu próximo giro é 100% GRATUITO!";
    } else {
        badge.textContent = "🪙 Giros extras: 50 Moedas";
        document.getElementById('spinCostNotice').textContent = "Giros adicionais custam 50 🪙 moedas de ouro.";
    }
    drawWheelCanvas();
}

function drawWheelCanvas() {
    const canvas = document.getElementById('wheelCanvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const fatias = gameState.roleta_fatias || [];
    if (!fatias.length) return;

    const numSlices = fatias.length;
    const sliceAngle = (2 * Math.PI) / numSlices;
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const radius = centerX - 12;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    ctx.save();
    ctx.translate(centerX, centerY);
    ctx.rotate(wheelAngle);

    // Desenha as 8 fatias
    for (let i = 0; i < numSlices; i++) {
        const fatia = fatias[i];
        const start = i * sliceAngle;
        const end = start + sliceAngle;

        ctx.beginPath();
        ctx.moveTo(0, 0);
        ctx.arc(0, 0, radius, start, end);
        ctx.closePath();
        ctx.fillStyle = fatia.cor || '#2c3e50';
        ctx.fill();

        ctx.strokeStyle = '#f1c40f';
        ctx.lineWidth = 2.5;
        ctx.stroke();

        // Texto da fatia
        ctx.save();
        ctx.rotate(start + sliceAngle / 2);
        ctx.textAlign = 'right';
        ctx.fillStyle = '#ffffff';
        ctx.font = 'bold 13px Segoe UI, sans-serif';
        ctx.shadowColor = '#000';
        ctx.shadowBlur = 4;
        ctx.fillText(fatia.label, radius - 16, 5);
        ctx.restore();
    }

    // Centro da Roleta
    ctx.beginPath();
    ctx.arc(0, 0, 24, 0, 2 * Math.PI);
    ctx.fillStyle = '#f39c12';
    ctx.fill();
    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 3;
    ctx.stroke();

    ctx.restore();
}

async function spinWheelOfFortune() {
    if (isSpinningWheel) return;

    const btn = document.getElementById('btnSpinWheel');
    btn.disabled = true;

    try {
        const res = await fetch('/api/roleta/girar', { method: 'POST' });
        const data = await res.json();
        if (!data.success) {
            alert(data.message || 'Erro ao girar roleta.');
            btn.disabled = false;
            return;
        }

        const fatiaIdx = data.roleta_resultado.fatia_index;
        const numSlices = (gameState.roleta_fatias || []).length || 8;
        const sliceAngle = (2 * Math.PI) / numSlices;

        // O ponteiro fica no topo (3 * PI / 2 radianos ou 270 graus)
        const pointerAngle = 3 * Math.PI / 2;
        const targetSliceCenter = (fatiaIdx * sliceAngle) + (sliceAngle / 2);

        // Calcula voltas completas (5 a 8 voltas para efeito visual dramático)
        const extraRotations = 6 * 2 * Math.PI;
        const targetAngle = extraRotations + (pointerAngle - targetSliceCenter);

        const startAngle = wheelAngle % (2 * Math.PI);
        const totalDistance = targetAngle - startAngle;
        const duration = 4000;
        const startTime = performance.now();
        isSpinningWheel = true;

        function animateWheel(now) {
            const elapsed = now - startTime;
            const progress = Math.min(1, elapsed / duration);

            // Easing Out Cubic
            const easeOut = 1 - Math.pow(1 - progress, 3);
            wheelAngle = startAngle + totalDistance * easeOut;
            drawWheelCanvas();

            if (progress < 1) {
                requestAnimationFrame(animateWheel);
            } else {
                isSpinningWheel = false;
                btn.disabled = false;
                gameState = data;
                renderGame();
                alert(`🎉 PARABÉNS! Você ganhou:\n${data.roleta_resultado.mensagem}`);
            }
        }

        requestAnimationFrame(animateWheel);

    } catch (err) {
        console.error(err);
        btn.disabled = false;
        isSpinningWheel = false;
    }
}

// ==========================================================
// 9. ABA 6: MAPA DO MUNDO (SVG INTERATIVO)
// ==========================================================
function renderMapa() {
    const p = gameState.player;
    const regioes = gameState.regioes_mapa;
    if (!p || !regioes) return;

    for (const [rId, rData] of Object.entries(regioes)) {
        const nodeEl = document.getElementById(`node_${rId}`);
        if (!nodeEl) continue;
        const baseCircle = nodeEl.querySelector('.map-node-base');
        if (baseCircle) {
            if (p.regiao_atual === rId) {
                baseCircle.classList.add('node-active');
            } else {
                baseCircle.classList.remove('node-active');
            }
        }
    }

    const regiaoAtualData = regioes[p.regiao_atual] || regioes['floresta'];
    document.getElementById('mapCurrentLocationLabel').textContent = `${regiaoAtualData.icone} ${regiaoAtualData.nome}`;
    updateSelectedRegionInfo(currentSelectedMapRegion || p.regiao_atual);
}

function selectMapRegion(regiaoId) {
    currentSelectedMapRegion = regiaoId;
    updateSelectedRegionInfo(regiaoId);
}

function updateSelectedRegionInfo(regiaoId) {
    const regioes = gameState.regioes_mapa;
    const p = gameState.player;
    if (!regioes || !regioes[regiaoId] || !p) return;

    const r = regioes[regiaoId];
    document.getElementById('infoRegionIcon').textContent = r.icone;
    document.getElementById('infoRegionName').textContent = r.nome;
    document.getElementById('infoRegionReqLvl').textContent = `Requer Nível ${r.nivel_minimo}`;
    document.getElementById('infoRegionDesc').textContent = r.descricao;

    const monstersDiv = document.getElementById('infoRegionMonsters');
    monstersDiv.innerHTML = '';
    r.inimigos.forEach(m => {
        const span = document.createElement('span');
        span.className = 'monster-mini-pill';
        span.textContent = `${m.icon} ${m.nome}`;
        monstersDiv.appendChild(span);
    });

    const travelBtn = document.getElementById('btnTravelToRegion');
    if (p.regiao_atual === regiaoId) {
        travelBtn.disabled = true;
        travelBtn.textContent = '📍 Você já está nesta Região';
        travelBtn.className = 'btn btn-secondary btn-large';
    } else if (p.nivel < r.nivel_minimo) {
        travelBtn.disabled = true;
        travelBtn.textContent = `🔒 Requer Nível ${r.nivel_minimo}`;
        travelBtn.className = 'btn btn-secondary btn-large';
    } else {
        travelBtn.disabled = false;
        travelBtn.textContent = `🚶 Viajar para ${r.nome}`;
        travelBtn.className = 'btn btn-primary btn-large btn-glow';
    }
}

async function travelToSelectedRegion() {
    try {
        const res = await fetch('/api/viajar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ regiao_id: currentSelectedMapRegion })
        });
        const data = await res.json();
        if (data.success) {
            gameState = data;
            renderGame();
            switchTab('aventura');
        } else {
            alert(data.message || 'Não foi possível viajar.');
        }
    } catch (err) {
        console.error(err);
    }
}

// ==========================================================
// 10. ABA 7: TREINAMENTO (VISUAL COM DUMMY)
// ==========================================================
function renderTreino() {
    const t = gameState.treino;
    const p = gameState.player;
    const grid = document.getElementById('trainingOptionsGrid');
    const activeCard = document.getElementById('activeTrainingCard');
    if (!t || !gameState.opcoes_treino || !p) return;

    document.getElementById('trainHeroImg').src = p.imagem || '/static/images/classes/guerreiro.svg';

    if (t.ativo) {
        activeCard.classList.remove('hidden');
        document.getElementById('trainActiveName').textContent = t.nome;
        const rew = t.recompensas || {};
        document.getElementById('trainRewXp').textContent = `✨ +${rew.xp || 0} XP`;
        document.getElementById('trainRewGold').textContent = `🪙 +${rew.moedas || 0} Moedas`;
        const b = rew.bonus_stats || {};
        document.getElementById('trainRewStats').textContent = `💪 +${b.ataque || 0} Atq | +${b.defesa || 0} Def | +${b.hp_max || 0} HP`;
        startTrainingCountdown();
    } else {
        activeCard.classList.add('hidden');
        stopTrainingCountdown();
    }

    grid.innerHTML = '';
    const opcoes = Object.values(gameState.opcoes_treino);
    opcoes.forEach(opt => {
        const card = document.createElement('div');
        card.className = 'train-card';
        const stats = opt.bonus_stats || {};
        const isLocked = t.ativo;

        card.innerHTML = `
            <div>
                <div class="train-card-header">
                    <h4>${opt.nome}</h4>
                    <span class="train-time-badge">⏱️ ${formatSeconds(opt.duracao_segundos)}</span>
                </div>
                <p class="train-card-desc">${opt.descricao}</p>
            </div>
            <div class="train-rewards-list">
                <div class="train-reward-row"><span>XP:</span><strong>+${opt.xp} XP</strong></div>
                <div class="train-reward-row"><span>Moedas:</span><strong>+${opt.moedas} 🪙</strong></div>
                <div class="train-reward-row"><span>Atributos:</span><strong>+${stats.ataque || 0} Atq | +${stats.defesa || 0} Def</strong></div>
            </div>
            <button class="btn btn-primary" ${isLocked ? 'disabled' : ''} onclick="startTraining('${opt.chave}')">
                ${isLocked ? '🔒 Treino Ativo' : '▶️ Iniciar'}
            </button>
        `;
        grid.appendChild(card);
    });
}

function startTrainingCountdown() {
    stopTrainingCountdown();
    const t = gameState.treino;
    if (!t || !t.ativo) return;

    const btnCollect = document.getElementById('btnCollectTrain');
    const btnCancel = document.getElementById('btnCancelTrain');
    const countdownEl = document.getElementById('trainCountdown');
    const progressEl = document.getElementById('trainProgressFill');

    function update() {
        const now = Math.floor(Date.now() / 1000) - serverTimeOffset;
        const total = t.duracao_segundos;
        const remaining = Math.max(0, t.timestamp_fim - now);

        countdownEl.textContent = formatTimer(remaining);
        const elapsed = total - remaining;
        const pct = Math.min(100, Math.max(0, (elapsed / total) * 100));
        progressEl.style.width = `${pct}%`;

        if (remaining <= 0) {
            btnCollect.classList.remove('hidden');
            btnCancel.classList.add('hidden');
            countdownEl.textContent = "00:00 (Concluído!)";
            progressEl.style.width = "100%";
        } else {
            btnCollect.classList.add('hidden');
            btnCancel.classList.remove('hidden');
        }
    }
    update();
    trainingTimerInterval = setInterval(update, 1000);
}

function stopTrainingCountdown() {
    if (trainingTimerInterval) {
        clearInterval(trainingTimerInterval);
        trainingTimerInterval = null;
    }
}

async function startTraining(chave) {
    try {
        const res = await fetch('/api/treino', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ acao: 'iniciar', chave })
        });
        const data = await res.json();
        if (data.success) {
            gameState = data;
            renderGame();
        } else {
            alert(data.message || 'Erro ao iniciar treino.');
        }
    } catch (err) {
        console.error(err);
    }
}

async function cancelTraining() {
    if (!confirm('Deseja realmente cancelar o treino em andamento? As recompensas serão perdidas.')) return;
    try {
        const res = await fetch('/api/treino', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ acao: 'cancelar' })
        });
        const data = await res.json();
        if (data.success) {
            gameState = data;
            renderGame();
        }
    } catch (err) {
        console.error(err);
    }
}

async function collectTraining() {
    try {
        const res = await fetch('/api/treino', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ acao: 'coletar' })
        });
        const data = await res.json();
        if (data.success) {
            gameState = data;
            renderGame();
        } else {
            alert(data.message || 'Erro ao coletar recompensas.');
        }
    } catch (err) {
        console.error(err);
    }
}

// ==========================================================
// 11. ABA 8: LOJA DO FERREIRO & TOOLTIPS
// ==========================================================
function renderLoja() {
    const loja = gameState.loja;
    const p = gameState.player;
    if (!loja || !p) return;

    const cost = loja.custo_reroll;
    document.getElementById('rerollCostLabel').textContent = cost === 0 ? 'Grátis' : `${cost} 🪙`;

    const shopGrid = document.getElementById('shopItemsGrid');
    shopGrid.innerHTML = '';

    loja.itens.forEach(item => {
        const card = document.createElement('div');
        card.className = `item-card rarity-${item.raridade}`;
        card.addEventListener('mouseenter', (e) => showComparisonTooltip(e, item));
        card.addEventListener('mouseleave', hideComparisonTooltip);
        card.addEventListener('mousemove', (e) => positionTooltip(e));

        card.innerHTML = `
            <div class="item-header">
                <span class="rarity-badge">${item.raridade}</span>
                <span style="font-size: 0.65rem; color: #a4b0be; text-transform: uppercase;">${item.tipo}</span>
            </div>
            <div class="item-image-wrap">
                <img src="${item.imagem}" alt="${item.nome}">
            </div>
            <div class="item-details">
                <h4>${item.nome}</h4>
                <div class="item-stats-chips">
                    ${item.bonus_ataque ? `<span class="stat-chip">⚔️ +${item.bonus_ataque} Atq</span>` : ''}
                    ${item.bonus_defesa ? `<span class="stat-chip">🛡️ +${item.bonus_defesa} Def</span>` : ''}
                    ${item.bonus_hp ? `<span class="stat-chip">❤️ +${item.bonus_hp} HP</span>` : ''}
                    ${item.bonus_critico ? `<span class="stat-chip">⚡ +${item.bonus_critico}%</span>` : ''}
                    ${item.bonus_esquiva ? `<span class="stat-chip">💨 +${item.bonus_esquiva}%</span>` : ''}
                </div>
            </div>
            <div class="item-card-footer">
                <div class="item-price">🪙 ${item.preco} Moedas</div>
                <button class="btn btn-warning btn-sm" onclick="buyItem('${item.id}')">
                    Comprar & Equipar
                </button>
            </div>
        `;
        shopGrid.appendChild(card);
    });
}

function showComparisonTooltip(e, newItem) {
    const tooltip = document.getElementById('itemComparisonTooltip');
    const p = gameState.player;
    if (!tooltip || !p) return;

    const slot = newItem.tipo;
    const equipped = p.equipados[slot];

    document.getElementById('ttItemName').textContent = newItem.nome;
    document.getElementById('ttRarityBadge').textContent = newItem.raridade;
    document.getElementById('ttRarityBadge').className = `rarity-badge rarity-${newItem.raridade}`;
    document.getElementById('ttSlotType').textContent = slot;
    document.getElementById('ttItemDesc').textContent = newItem.descricao;
    document.getElementById('ttPrice').textContent = `Valor: ${newItem.preco} 🪙`;

    const eqAtk = equipped ? equipped.bonus_ataque : 0;
    const eqDef = equipped ? equipped.bonus_defesa : 0;
    const eqHp = equipped ? equipped.bonus_hp : 0;
    const eqCrit = equipped ? equipped.bonus_critico || 0 : 0;
    const eqDodge = equipped ? equipped.bonus_esquiva || 0 : 0;

    document.getElementById('ttEquipAtk').textContent = eqAtk;
    document.getElementById('ttEquipDef').textContent = eqDef;
    document.getElementById('ttEquipHp').textContent = eqHp;
    document.getElementById('ttEquipCrit').textContent = `${eqCrit}%`;
    document.getElementById('ttEquipDodge').textContent = `${eqDodge}%`;

    const newAtk = newItem.bonus_ataque || 0;
    const newDef = newItem.bonus_defesa || 0;
    const newHp = newItem.bonus_hp || 0;
    const newCrit = newItem.bonus_critico || 0;
    const newDodge = newItem.bonus_esquiva || 0;

    document.getElementById('ttNewAtk').textContent = newAtk;
    document.getElementById('ttNewDef').textContent = newDef;
    document.getElementById('ttNewHp').textContent = newHp;
    document.getElementById('ttNewCrit').textContent = `${newCrit}%`;
    document.getElementById('ttNewDodge').textContent = `${newDodge}%`;

    applyDiffBadge('ttDiffAtk', newAtk - eqAtk);
    applyDiffBadge('ttDiffDef', newDef - eqDef);
    applyDiffBadge('ttDiffHp', newHp - eqHp);
    applyDiffBadge('ttDiffCrit', newCrit - eqCrit, '%');
    applyDiffBadge('ttDiffDodge', newDodge - eqDodge, '%');

    positionTooltip(e);
    tooltip.classList.remove('hidden');
}

function applyDiffBadge(elementId, diff, suffix = '') {
    const el = document.getElementById(elementId);
    if (!el) return;

    if (diff > 0) {
        el.textContent = `+${diff}${suffix}`;
        el.className = 'diff-badge diff-pos';
    } else if (diff < 0) {
        el.textContent = `${diff}${suffix}`;
        el.className = 'diff-badge diff-neg';
    } else {
        el.textContent = `0${suffix}`;
        el.className = 'diff-badge diff-neutral';
    }
}

function positionTooltip(e) {
    const tooltip = document.getElementById('itemComparisonTooltip');
    if (!tooltip || tooltip.classList.contains('hidden')) return;

    const x = e.clientX + 16;
    const y = e.clientY + 16;
    const rightOverflow = x + 330 > window.innerWidth;
    const bottomOverflow = y + 270 > window.innerHeight;

    tooltip.style.left = `${rightOverflow ? e.clientX - 330 : x}px`;
    tooltip.style.top = `${bottomOverflow ? e.clientY - 270 : y}px`;
}

function hideComparisonTooltip() {
    const tooltip = document.getElementById('itemComparisonTooltip');
    if (tooltip) tooltip.classList.add('hidden');
}

async function rerollShop() {
    try {
        const res = await fetch('/api/loja', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ acao: 'reroll' })
        });
        const data = await res.json();
        if (data.success) {
            gameState = data;
            renderGame();
        } else {
            alert(data.message || 'Moedas insuficientes.');
        }
    } catch (err) {
        console.error(err);
    }
}

async function buyItem(itemId) {
    hideComparisonTooltip();
    try {
        const res = await fetch('/api/loja', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ acao: 'comprar', item_id: itemId })
        });
        const data = await res.json();
        if (data.success) {
            gameState = data;
            renderGame();
        } else {
            alert(data.message || 'Erro ao comprar item.');
        }
    } catch (err) {
        console.error(err);
    }
}

async function buyPotion() {
    try {
        const res = await fetch('/api/loja', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ acao: 'comprar_pocao' })
        });
        const data = await res.json();
        if (data.success) {
            gameState = data;
            renderGame();
        } else {
            alert(data.message || 'Moedas insuficientes.');
        }
    } catch (err) {
        console.error(err);
    }
}

async function equipInventoryItem(itemId) {
    hideComparisonTooltip();
    try {
        const res = await fetch('/api/equipar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ acao: 'equipar', item_id: itemId })
        });
        const data = await res.json();
        if (data.success) {
            gameState = data;
            renderGame();
        }
    } catch (err) {
        console.error(err);
    }
}

async function unequipSlot(slot) {
    try {
        const res = await fetch('/api/equipar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ acao: 'desequipar', slot })
        });
        const data = await res.json();
        if (data.success) {
            gameState = data;
            renderGame();
        }
    } catch (err) {
        console.error(err);
    }
}

async function sellInventoryItem(itemId) {
    hideComparisonTooltip();
    try {
        const res = await fetch('/api/vender', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ item_id: itemId })
        });
        const data = await res.json();
        if (data.success) {
            gameState = data;
            renderGame();
        }
    } catch (err) {
        console.error(err);
    }
}

// ==========================================================
// 12. CRIAÇÃO DE PERSONAGEM
// ==========================================================
function showCharacterCreation() {
    const overlay = document.getElementById('characterCreationOverlay');
    overlay.classList.remove('hidden');

    const classGrid = document.getElementById('classSelectionGrid');
    const weaponGrid = document.getElementById('weaponSelectionGrid');
    classGrid.innerHTML = '';
    weaponGrid.innerHTML = '';

    const classes = gameState.classes || {};
    let firstClass = true;
    for (const [cName, cData] of Object.entries(classes)) {
        const cCard = document.createElement('div');
        cCard.className = `choice-card ${firstClass ? 'selected' : ''}`;
        cCard.onclick = () => selectCreationClass(cName, cCard);
        if (firstClass) {
            document.getElementById('selectedClass').value = cName;
            firstClass = false;
        }
        cCard.innerHTML = `
            <img src="${cData.imagem}" alt="${cName}" class="choice-thumb">
            <span class="choice-title">${cData.icon} ${cName}</span>
            <span class="choice-sub">HP ${cData.hp_base} | Atq ${cData.ataque_base}</span>
        `;
        classGrid.appendChild(cCard);
    }

    const weapons = gameState.armas_iniciais || {};
    let firstWeapon = true;
    for (const [wName, wData] of Object.entries(weapons)) {
        const wCard = document.createElement('div');
        wCard.className = `choice-card ${firstWeapon ? 'selected' : ''}`;
        wCard.onclick = () => selectCreationWeapon(wName, wCard);
        if (firstWeapon) {
            document.getElementById('selectedWeapon').value = wName;
            firstWeapon = false;
        }
        wCard.innerHTML = `
            <img src="${wData.imagem}" alt="${wName}" class="choice-thumb">
            <span class="choice-title">${wName}</span>
            <span class="choice-sub">+${wData.bonus_ataque} Atq</span>
        `;
        weaponGrid.appendChild(wCard);
    }
}

function selectCreationClass(className, cardEl) {
    document.querySelectorAll('#classSelectionGrid .choice-card').forEach(c => c.classList.remove('selected'));
    cardEl.classList.add('selected');
    document.getElementById('selectedClass').value = className;
}

function selectCreationWeapon(weaponName, cardEl) {
    document.querySelectorAll('#weaponSelectionGrid .choice-card').forEach(c => c.classList.remove('selected'));
    cardEl.classList.add('selected');
    document.getElementById('selectedWeapon').value = weaponName;
}

function hideCharacterCreation() {
    const overlay = document.getElementById('characterCreationOverlay');
    overlay.classList.add('hidden');
}

async function handleCharacterCreate(e) {
    e.preventDefault();
    const nome = document.getElementById('heroName').value.trim();
    const classe = document.getElementById('selectedClass').value;
    const arma = document.getElementById('selectedWeapon').value;

    if (!nome) {
        alert('Por favor, informe o nome do seu campeão!');
        return;
    }

    try {
        const res = await fetch('/api/criar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nome, classe, arma })
        });
        const data = await res.json();
        if (data.success) {
            gameState = data;
            renderGame();
        } else {
            alert(data.message || 'Erro ao criar herói.');
        }
    } catch (err) {
        console.error(err);
    }
}

function renderLogs() {
    const logBox = document.getElementById('combatLogBox');
    if (!logBox || !gameState.logs) return;

    logBox.innerHTML = '';
    gameState.logs.forEach(msg => {
        const line = document.createElement('div');
        line.className = 'log-line';

        if (msg.includes('🗡️') || msg.includes('✨') || msg.includes('🌟') || msg.includes('PASSIVA')) {
            line.classList.add('hero-action');
        } else if (msg.includes('💥') || msg.includes('PODER') || msg.includes('💀')) {
            line.classList.add('enemy-action');
        } else if (msg.includes('🎁') || msg.includes('💰') || msg.includes('🪙') || msg.includes('🛍️') || msg.includes('🎰')) {
            line.classList.add('loot-action');
        }

        line.textContent = msg;
        logBox.appendChild(line);
    });
}

function clearLocalLogs() {
    const logBox = document.getElementById('combatLogBox');
    if (logBox) logBox.innerHTML = '<div class="log-line" style="color:#8c92b2;">Visualização limpa.</div>';
}

async function quickUsePotion() {
    if (!gameState || !gameState.player) return;
    if (gameState.player.pocoes <= 0) {
        alert('Você não possui poções restantes! Adquira mais na aba Loja.');
        return;
    }
    await adventureAction('pocao');
}

async function confirmResetGame() {
    if (!confirm('Atenção: Deseja reiniciar totalmente o jogo e criar um novo herói? Todo o progresso será perdido.')) {
        return;
    }
    try {
        const res = await fetch('/api/reset', { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            gameState = data;
            renderGame();
        }
    } catch (err) {
        console.error(err);
    }
}

function formatSeconds(secs) {
    if (secs < 60) return `${secs}s`;
    const mins = Math.floor(secs / 60);
    return `${mins} min`;
}

function formatTimer(totalSeconds) {
    const m = Math.floor(totalSeconds / 60);
    const s = totalSeconds % 60;
    return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}
