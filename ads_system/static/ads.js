/**
 * Sistema de Anúncios para Jogo WebGL Unity
 * 
 * Este script gerencia a exibição de anúncios no jogo:
 * - Banner rotativo no topo da página (1080×140px)
 * - Anúncios de tela cheia após game over (1080×1920px)
 * - Rastreamento de impressões e cliques
 */

// Configuração
const CONFIG = {
    // Intervalo de rotação do banner em milissegundos (7 segundos)
    BANNER_ROTATION_INTERVAL: 7000,
    
    // Número de game overs antes de mostrar anúncio de tela cheia
    GAMEOVER_COUNT_THRESHOLD: 5,
    
    // Duração do anúncio de tela cheia em milissegundos (5 segundos)
    FULLSCREEN_AD_DURATION: 5000,
    
    // URL da API para obter anúncios
    API_URL: window.location.hostname.includes('localhost') 
        ? 'http://localhost:5000/api'
        : 'https://seu-servidor-de-producao.com/api',
    
    // Seletor para o elemento do jogo Unity
    GAME_CONTAINER_SELECTOR: '#unity-container',
    
    // Seletor para o canvas do jogo Unity
    GAME_CANVAS_SELECTOR: '#unity-canvas'
};

// Estado do sistema de anúncios
const adSystem = {
    // Anúncios carregados
    bannerAds: [],
    fullscreenAds: [],
    
    // Índice do banner atual
    currentBannerIndex: 0,
    
    // Contador de game overs
    gameOverCount: 0,
    
    // Intervalo de rotação do banner
    bannerRotationInterval: null,
    
    // Elementos DOM
    bannerContainer: null,
    fullscreenContainer: null,
    
    // Instância do Unity
    unityInstance: null,
    
    // Flag para verificar se estamos na tela de jogo
    isInGameScreen: false,
    
    // Inicializa o sistema de anúncios
    init: function() {
        console.log('Inicializando sistema de anúncios...');
        
        // Criar elementos de contêiner
        this.createAdContainers();
        
        // Carregar anúncios do servidor
        this.loadAds();
        
        // Configurar comunicação com o Unity
        this.setupUnityConnection();
        
        // Verificar periodicamente se estamos na tela de jogo
        setInterval(() => this.checkGameScreen(), 1000);
    },
    
    // Cria os contêineres de anúncios
    createAdContainers: function() {
        // Criar contêiner de banner
        this.bannerContainer = document.createElement('div');
        this.bannerContainer.id = 'ad-banner-container';
        this.bannerContainer.style.cssText = `
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 140px;
            z-index: 1000;
            display: none;
            overflow: hidden;
        `;
        document.body.appendChild(this.bannerContainer);
        
        // Criar contêiner de anúncio de tela cheia
        this.fullscreenContainer = document.createElement('div');
        this.fullscreenContainer.id = 'ad-fullscreen-container';
        this.fullscreenContainer.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 2000;
            display: none;
            background-color: rgba(0, 0, 0, 0.8);
            justify-content: center;
            align-items: center;
        `;
        document.body.appendChild(this.fullscreenContainer);
    },
    
    // Carrega anúncios do servidor
    loadAds: async function() {
        try {
            // Carregar banners
            const bannerResponse = await fetch(`${CONFIG.API_URL}/ads/banner`);
            const bannerData = await bannerResponse.json();
            this.bannerAds = bannerData.ads || [];
            
            // Carregar anúncios de tela cheia
            const fullscreenResponse = await fetch(`${CONFIG.API_URL}/ads/fullscreen`);
            const fullscreenData = await fullscreenResponse.json();
            this.fullscreenAds = fullscreenData.ads || [];
            
            console.log(`Anúncios carregados: ${this.bannerAds.length} banners, ${this.fullscreenAds.length} tela cheia`);
            
            // Iniciar rotação de banners se houver anúncios
            if (this.bannerAds.length > 0) {
                this.startBannerRotation();
            }
        } catch (error) {
            console.error('Erro ao carregar anúncios:', error);
        }
    },
    
    // Configura comunicação com o Unity
    setupUnityConnection: function() {
        // Aguardar a instância do Unity ser criada
        window.addEventListener('unityInstance', (e) => {
            this.unityInstance = e.detail;
            console.log('Conexão com Unity estabelecida');
            
            // Adicionar função para o Unity chamar quando ocorrer game over
            window.gameOver = () => {
                this.handleGameOver();
            };
        });
    },
    
    // Verifica se estamos na tela de jogo
    checkGameScreen: function() {
        // Lógica para detectar se estamos na tela de jogo
        // Esta é uma implementação simplificada, você pode precisar ajustar
        // com base na estrutura específica do seu jogo
        
        // Exemplo: verificar se existe algum elemento específico da tela de jogo
        const isInGame = document.querySelector('.game-screen-indicator') !== null;
        
        // Alternativamente, o Unity pode enviar mensagens para indicar a tela atual
        
        // Se mudou de estado
        if (isInGame !== this.isInGameScreen) {
            this.isInGameScreen = isInGame;
            
            if (isInGame) {
                // Mostrar banner quando entrar na tela de jogo
                this.showBanner();
            } else {
                // Esconder banner quando sair da tela de jogo
                this.hideBanner();
            }
        }
    },
    
    // Inicia a rotação de banners
    startBannerRotation: function() {
        // Limpar intervalo existente
        if (this.bannerRotationInterval) {
            clearInterval(this.bannerRotationInterval);
        }
        
        // Mostrar o primeiro banner
        this.showCurrentBanner();
        
        // Configurar intervalo para rotação
        this.bannerRotationInterval = setInterval(() => {
            this.rotateToNextBanner();
        }, CONFIG.BANNER_ROTATION_INTERVAL);
    },
    
    // Mostra o banner atual
    showCurrentBanner: function() {
        if (this.bannerAds.length === 0) return;
        
        const ad = this.bannerAds[this.currentBannerIndex];
        
        // Limpar contêiner
        this.bannerContainer.innerHTML = '';
        
        // Criar elemento de banner
        const banner = document.createElement('div');
        banner.style.cssText = `
            width: 100%;
            height: 100%;
            background-image: url('${ad.imageUrl}');
            background-size: cover;
            background-position: center;
            cursor: pointer;
            position: relative;
        `;
        
        // Adicionar botão
        const button = document.createElement('a');
        button.href = ad.linkUrl;
        button.target = '_blank';
        button.style.cssText = `
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background-color: rgba(0, 123, 255, 0.7);
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            text-decoration: none;
            font-family: Arial, sans-serif;
        `;
        
        // Extrair domínio para o texto do botão
        try {
            const url = new URL(ad.linkUrl);
            const domain = url.hostname.replace('www.', '');
            button.textContent = `Visitar ${domain}`;
        } catch (e) {
            button.textContent = 'Visitar Site';
        }
        
        banner.appendChild(button);
        this.bannerContainer.appendChild(banner);
        
        // Registrar impressão
        this.recordImpression(ad.id, 'banner');
        
        // Adicionar evento de clique para rastreamento
        button.addEventListener('click', () => {
            this.recordClick(ad.id, 'banner');
        });
    },
    
    // Rotaciona para o próximo banner
    rotateToNextBanner: function() {
        if (this.bannerAds.length <= 1) return;
        
        this.currentBannerIndex = (this.currentBannerIndex + 1) % this.bannerAds.length;
        this.showCurrentBanner();
    },
    
    // Mostra o banner
    showBanner: function() {
        if (this.bannerAds.length === 0) return;
        this.bannerContainer.style.display = 'block';
    },
    
    // Esconde o banner
    hideBanner: function() {
        this.bannerContainer.style.display = 'none';
    },
    
    // Manipula evento de game over
    handleGameOver: function() {
        this.gameOverCount++;
        
        // Verificar se deve mostrar anúncio de tela cheia
        if (this.gameOverCount >= CONFIG.GAMEOVER_COUNT_THRESHOLD) {
            this.gameOverCount = 0; // Resetar contador
            this.showFullscreenAd();
        }
    },
    
    // Mostra anúncio de tela cheia
    showFullscreenAd: function() {
        if (this.fullscreenAds.length === 0) return;
        
        // Selecionar um anúncio aleatório
        const randomIndex = Math.floor(Math.random() * this.fullscreenAds.length);
        const ad = this.fullscreenAds[randomIndex];
        
        // Limpar contêiner
        this.fullscreenContainer.innerHTML = '';
        
        // Criar elemento de anúncio
        const adElement = document.createElement('div');
        adElement.style.cssText = `
            width: 100%;
            height: 100%;
            max-width: 1080px;
            max-height: 1920px;
            background-image: url('${ad.imageUrl}');
            background-size: contain;
            background-position: center;
            background-repeat: no-repeat;
            position: relative;
        `;
        
        // Adicionar botão
        const button = document.createElement('a');
        button.href = ad.linkUrl;
        button.target = '_blank';
        button.style.cssText = `
            position: absolute;
            bottom: 10%;
            left: 50%;
            transform: translateX(-50%);
            background-color: rgba(0, 123, 255, 0.7);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 4px;
            text-decoration: none;
            font-family: Arial, sans-serif;
            font-size: 18px;
            text-align: center;
            min-width: 200px;
        `;
        
        // Extrair domínio para o texto do botão
        try {
            const url = new URL(ad.linkUrl);
            const domain = url.hostname.replace('www.', '');
            button.textContent = `Visitar ${domain}`;
        } catch (e) {
            button.textContent = 'Visitar Site';
        }
        
        // Adicionar contador
        const counter = document.createElement('div');
        counter.style.cssText = `
            position: absolute;
            top: 20px;
            right: 20px;
            background-color: rgba(0, 0, 0, 0.5);
            color: white;
            padding: 5px 10px;
            border-radius: 20px;
            font-family: Arial, sans-serif;
        `;
        counter.textContent = '5';
        
        adElement.appendChild(button);
        adElement.appendChild(counter);
        this.fullscreenContainer.appendChild(adElement);
        
        // Mostrar anúncio
        this.fullscreenContainer.style.display = 'flex';
        
        // Pausar o jogo se possível
        if (this.unityInstance && typeof this.unityInstance.SendMessage === 'function') {
            this.unityInstance.SendMessage('GameManager', 'PauseGame');
        }
        
        // Registrar impressão
        this.recordImpression(ad.id, 'fullscreen');
        
        // Adicionar evento de clique para rastreamento
        button.addEventListener('click', () => {
            this.recordClick(ad.id, 'fullscreen');
        });
        
        // Iniciar contador regressivo
        let secondsLeft = 5;
        const countdownInterval = setInterval(() => {
            secondsLeft--;
            counter.textContent = secondsLeft;
            
            if (secondsLeft <= 0) {
                clearInterval(countdownInterval);
                this.hideFullscreenAd();
            }
        }, 1000);
        
        // Fechar automaticamente após o tempo definido
        setTimeout(() => {
            clearInterval(countdownInterval);
            this.hideFullscreenAd();
        }, CONFIG.FULLSCREEN_AD_DURATION);
    },
    
    // Esconde anúncio de tela cheia
    hideFullscreenAd: function() {
        this.fullscreenContainer.style.display = 'none';
        
        // Retomar o jogo se possível
        if (this.unityInstance && typeof this.unityInstance.SendMessage === 'function') {
            this.unityInstance.SendMessage('GameManager', 'ResumeGame');
        }
    },
    
    // Registra impressão de anúncio
    recordImpression: async function(adId, adType) {
        try {
            await fetch(`${CONFIG.API_URL}/ads/impression`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    adId: adId,
                    adType: adType
                })
            });
        } catch (error) {
            console.error('Erro ao registrar impressão:', error);
        }
    },
    
    // Registra clique em anúncio
    recordClick: async function(adId, adType) {
        try {
            await fetch(`${CONFIG.API_URL}/ads/click`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    adId: adId,
                    adType: adType
                })
            });
        } catch (error) {
            console.error('Erro ao registrar clique:', error);
        }
    }
};

// Inicializar sistema de anúncios quando a página carregar
document.addEventListener('DOMContentLoaded', () => {
    adSystem.init();
});

// Expor funções para o Unity chamar
window.showBanner = () => adSystem.showBanner();
window.hideBanner = () => adSystem.hideBanner();
window.gameOver = () => adSystem.handleGameOver();
window.showFullscreenAd = () => adSystem.showFullscreenAd();
