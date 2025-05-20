/**
 * Sistema de Anúncios para Jogos Unity WebGL
 * Versão: 1.0.0
 * 
 * Este script gerencia a exibição de anúncios em jogos Unity WebGL:
 * - Banners rotativos no topo da página
 * - Anúncios de tela cheia após game overs
 */

// Configuração do sistema de anúncios
const adSystem = {
    // URL da API do backend (atualizada para o Render)
    apiUrl: 'https://ads-system-backend.onrender.com',
    
    // Configurações dos anúncios
    config: {
        // Banner rotativo
        banner: {
            enabled: true,
            rotationInterval: 7000, // 7 segundos
            container: null,
            currentIndex: 0,
            ads: [],
            timer: null
        },
        
        // Anúncio de tela cheia
        fullscreen: {
            enabled: true,
            displayDuration: 5000, // 5 segundos
            gameOverThreshold: 5, // Exibir a cada 5 game overs
            container: null,
            ads: []
        }
    },
    
    // Contador de game overs
    gameOverCount: 0,
    
    /**
     * Inicializa o sistema de anúncios
     */
    init: function() {
        console.log('Sistema de anúncios inicializando...');
        
        // Criar containers para os anúncios
        this.createAdContainers();
        
        // Carregar anúncios do backend
        this.loadAds();
        
        // Adicionar listener para detectar quando o Unity estiver pronto
        window.addEventListener('unityInstance', (e) => {
            console.log('Unity instance detectada, sistema de anúncios pronto');
        });
        
        console.log('Sistema de anúncios inicializado');
    },
    
    /**
     * Cria os containers para os anúncios
     */
    createAdContainers: function() {
        // Container para banner
        const bannerContainer = document.createElement('div');
        bannerContainer.id = 'ad-banner-container';
        bannerContainer.style.position = 'absolute';
        bannerContainer.style.top = '0';
        bannerContainer.style.left = '0';
        bannerContainer.style.width = '100%';
        bannerContainer.style.height = '140px';
        bannerContainer.style.zIndex = '999';
        bannerContainer.style.display = 'none';
        document.body.appendChild(bannerContainer);
        this.config.banner.container = bannerContainer;
        
        // Container para anúncios de tela cheia
        const fullscreenContainer = document.createElement('div');
        fullscreenContainer.id = 'ad-fullscreen-container';
        fullscreenContainer.style.position = 'fixed';
        fullscreenContainer.style.top = '0';
        fullscreenContainer.style.left = '0';
        fullscreenContainer.style.width = '100%';
        fullscreenContainer.style.height = '100%';
        fullscreenContainer.style.backgroundColor = 'rgba(0, 0, 0, 0.8)';
        fullscreenContainer.style.zIndex = '1000';
        fullscreenContainer.style.display = 'none';
        fullscreenContainer.style.justifyContent = 'center';
        fullscreenContainer.style.alignItems = 'center';
        document.body.appendChild(fullscreenContainer);
        this.config.fullscreen.container = fullscreenContainer;
    },
    
    /**
     * Carrega os anúncios do backend
     */
    loadAds: function() {
        console.log('Carregando anúncios do backend...');
        
        // Carregar banners
        fetch(`${this.apiUrl}/api/banners`)
            .then(response => response.json())
            .then(data => {
                console.log('Banners carregados:', data.length);
                this.config.banner.ads = data;
                if (data.length > 0) {
                    this.startBannerRotation();
                }
            })
            .catch(error => {
                console.error('Erro ao carregar banners:', error);
            });
        
        // Carregar anúncios de tela cheia
        fetch(`${this.apiUrl}/api/fullscreen`)
            .then(response => response.json())
            .then(data => {
                console.log('Anúncios de tela cheia carregados:', data.length);
                this.config.fullscreen.ads = data;
            })
            .catch(error => {
                console.error('Erro ao carregar anúncios de tela cheia:', error);
            });
    },
    
    /**
     * Inicia a rotação de banners
     */
    startBannerRotation: function() {
        if (!this.config.banner.enabled || this.config.banner.ads.length === 0) {
            return;
        }
        
        // Exibir o primeiro banner
        this.showBanner(0);
        
        // Iniciar timer para rotação
        this.config.banner.timer = setInterval(() => {
            this.config.banner.currentIndex = (this.config.banner.currentIndex + 1) % this.config.banner.ads.length;
            this.showBanner(this.config.banner.currentIndex);
        }, this.config.banner.rotationInterval);
    },
    
    /**
     * Exibe um banner específico
     * @param {number} index - Índice do banner a ser exibido
     */
    showBanner: function(index) {
        const container = this.config.banner.container;
        const ad = this.config.banner.ads[index];
        
        if (!ad || !container) {
            return;
        }
        
        // Verificar se estamos na tela de jogo
        const isGameScreen = document.querySelector('.game-screen-indicator') && 
                            document.querySelector('.game-screen-indicator').style.display === 'block';
        
        if (!isGameScreen) {
            container.style.display = 'none';
            return;
        }
        
        // Limpar container
        container.innerHTML = '';
        
        // Criar elemento do banner
        const banner = document.createElement('div');
        banner.style.width = '1080px';
        banner.style.height = '140px';
        banner.style.maxWidth = '100%';
        banner.style.margin = '0 auto';
        banner.style.position = 'relative';
        banner.style.backgroundImage = `url(${ad.imageUrl})`;
        banner.style.backgroundSize = 'cover';
        banner.style.backgroundPosition = 'center';
        banner.style.cursor = 'pointer';
        
        // Adicionar evento de clique
        banner.addEventListener('click', () => {
            this.recordAdClick(ad.id, 'banner');
            window.open(ad.linkUrl, '_blank');
        });
        
        // Adicionar ao container
        container.appendChild(banner);
        container.style.display = 'block';
        
        // Registrar impressão
        this.recordAdImpression(ad.id, 'banner');
    },
    
    /**
     * Manipula evento de game over
     */
    handleGameOver: function() {
        this.gameOverCount++;
        console.log('Game over detectado, contagem:', this.gameOverCount);
        
        // Verificar se deve exibir anúncio de tela cheia
        if (this.config.fullscreen.enabled && 
            this.gameOverCount % this.config.fullscreen.gameOverThreshold === 0 &&
            this.config.fullscreen.ads.length > 0) {
            
            // Pausar o jogo
            if (typeof window.pauseGame === 'function') {
                window.pauseGame();
            }
            
            // Exibir anúncio de tela cheia
            this.showFullscreenAd();
        }
    },
    
    /**
     * Exibe um anúncio de tela cheia
     */
    showFullscreenAd: function() {
        const container = this.config.fullscreen.container;
        
        // Selecionar um anúncio aleatório
        const randomIndex = Math.floor(Math.random() * this.config.fullscreen.ads.length);
        const ad = this.config.fullscreen.ads[randomIndex];
        
        if (!ad || !container) {
            return;
        }
        
        // Limpar container
        container.innerHTML = '';
        
        // Criar elemento do anúncio
        const adElement = document.createElement('div');
        adElement.style.width = '1080px';
        adElement.style.height = '1920px';
        adElement.style.maxWidth = '90%';
        adElement.style.maxHeight = '90%';
        adElement.style.position = 'relative';
        adElement.style.backgroundImage = `url(${ad.imageUrl})`;
        adElement.style.backgroundSize = 'contain';
        adElement.style.backgroundPosition = 'center';
        adElement.style.backgroundRepeat = 'no-repeat';
        adElement.style.cursor = 'pointer';
        
        // Adicionar evento de clique
        adElement.addEventListener('click', () => {
            this.recordAdClick(ad.id, 'fullscreen');
            window.open(ad.linkUrl, '_blank');
        });
        
        // Adicionar botão de fechar
        const closeButton = document.createElement('div');
        closeButton.style.position = 'absolute';
        closeButton.style.top = '10px';
        closeButton.style.right = '10px';
        closeButton.style.width = '30px';
        closeButton.style.height = '30px';
        closeButton.style.borderRadius = '50%';
        closeButton.style.backgroundColor = 'rgba(0, 0, 0, 0.5)';
        closeButton.style.color = 'white';
        closeButton.style.textAlign = 'center';
        closeButton.style.lineHeight = '30px';
        closeButton.style.cursor = 'pointer';
        closeButton.innerHTML = '✕';
        closeButton.addEventListener('click', (e) => {
            e.stopPropagation();
            this.hideFullscreenAd();
        });
        
        adElement.appendChild(closeButton);
        
        // Adicionar ao container
        container.appendChild(adElement);
        container.style.display = 'flex';
        
        // Registrar impressão
        this.recordAdImpression(ad.id, 'fullscreen');
        
        // Configurar timer para fechar automaticamente
        setTimeout(() => {
            this.hideFullscreenAd();
        }, this.config.fullscreen.displayDuration);
    },
    
    /**
     * Esconde o anúncio de tela cheia
     */
    hideFullscreenAd: function() {
        const container = this.config.fullscreen.container;
        if (container) {
            container.style.display = 'none';
        }
        
        // Retomar o jogo
        if (typeof window.resumeGame === 'function') {
            window.resumeGame();
        }
    },
    
    /**
     * Registra uma impressão de anúncio
     * @param {string} adId - ID do anúncio
     * @param {string} adType - Tipo do anúncio ('banner' ou 'fullscreen')
     */
    recordAdImpression: function(adId, adType) {
        fetch(`${this.apiUrl}/api/impression`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                adId: adId,
                adType: adType
            })
        })
        .catch(error => {
            console.error('Erro ao registrar impressão:', error);
        });
    },
    
    /**
     * Registra um clique em anúncio
     * @param {string} adId - ID do anúncio
     * @param {string} adType - Tipo do anúncio ('banner' ou 'fullscreen')
     */
    recordAdClick: function(adId, adType) {
        fetch(`${this.apiUrl}/api/click`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                adId: adId,
                adType: adType
            })
        })
        .catch(error => {
            console.error('Erro ao registrar clique:', error);
        });
    }
};

// Inicializar o sistema de anúncios quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM carregado, inicializando sistema de anúncios...');
    adSystem.init();
});

// Notificar que o script foi carregado
console.log('Sistema de anúncios carregado ou tentativa de carregamento concluída');
