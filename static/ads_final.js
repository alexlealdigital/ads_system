/**
 * Sistema de Anúncios para jogos Unity WebGL
 * Versão: 2.0.0
 * Autor: Manus AI
 * 
 * Este script gerencia a exibição de banners e anúncios de tela cheia
 * dentro do canvas do Unity, com tamanho e posicionamento otimizados.
 */

// Configuração do sistema de anúncios
const ADS_CONFIG = {
  // URLs da API
  API_URL: 'https://ads-system-backend.onrender.com',
  BANNERS_ENDPOINT: '/api/banners',
  FULLSCREEN_ENDPOINT: '/api/fullscreen',
  IMPRESSION_ENDPOINT: '/api/impression',
  CLICK_ENDPOINT: '/api/click',
  
  // Configurações de banner
  BANNER_WIDTH: 360,
  BANNER_HEIGHT: 47,
  BANNER_ROTATION_INTERVAL: 5000, // 5 segundos
  
  // Configurações de debug
  DEBUG: true,
  LOG_PREFIX: '[AdSystem]',
  
  // Configurações de retry
  MAX_RETRIES: 3,
  RETRY_DELAY: 2000 // 2 segundos
};

// Sistema de anúncios
class AdSystem {
  constructor() {
    // Estado interno
    this.banners = [];
    this.fullscreenAds = [];
    this.currentBannerIndex = 0;
    this.bannerContainer = null;
    this.fullscreenContainer = null;
    this.bannerRotationInterval = null;
    this.unityInstance = null;
    this.gameIsPaused = false;
    this.retryCount = 0;
    this.isInitialized = false;
    
    // Inicializar quando o DOM estiver pronto
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => this.init());
    } else {
      this.init();
    }
  }
  
  /**
   * Inicializa o sistema de anúncios
   */
  init() {
    this.log('Inicializando sistema de anúncios...');
    
    // Criar containers para os anúncios
    this.createAdContainers();
    
    // Carregar anúncios
    this.loadBanners();
    this.loadFullscreenAds();
    
    // Configurar detecção do Unity
    this.setupUnityDetection();
    
    // Configurar listeners de eventos
    window.addEventListener('resize', () => this.repositionBanner());
    
    // Verificar visibilidade periodicamente
    setInterval(() => this.checkVisibility(), 5000);
    
    this.isInitialized = true;
    this.log('Sistema de anúncios inicializado');
  }
  
  /**
   * Cria os containers para os anúncios
   */
  createAdContainers() {
    // Container para banners
    this.bannerContainer = document.createElement('div');
    this.bannerContainer.id = 'ad-banner-container';
    this.bannerContainer.style.position = 'absolute';
    this.bannerContainer.style.width = `${ADS_CONFIG.BANNER_WIDTH}px`;
    this.bannerContainer.style.height = `${ADS_CONFIG.BANNER_HEIGHT}px`;
    this.bannerContainer.style.overflow = 'hidden';
    this.bannerContainer.style.zIndex = '9999';
    this.bannerContainer.style.display = 'block';
    this.bannerContainer.style.visibility = 'visible';
    this.bannerContainer.style.opacity = '1';
    this.bannerContainer.style.top = '0';
    this.bannerContainer.style.left = '50%';
    this.bannerContainer.style.transform = 'translateX(-50%)';
    this.bannerContainer.style.backgroundColor = 'transparent';
    document.body.appendChild(this.bannerContainer);
    
    // Container para anúncios de tela cheia
    this.fullscreenContainer = document.createElement('div');
    this.fullscreenContainer.id = 'ad-fullscreen-container';
    this.fullscreenContainer.style.position = 'absolute';
    this.fullscreenContainer.style.width = '100%';
    this.fullscreenContainer.style.height = '100%';
    this.fullscreenContainer.style.top = '0';
    this.fullscreenContainer.style.left = '0';
    this.fullscreenContainer.style.zIndex = '10000';
    this.fullscreenContainer.style.display = 'none';
    this.fullscreenContainer.style.backgroundColor = 'rgba(0, 0, 0, 0.8)';
    this.fullscreenContainer.style.justifyContent = 'center';
    this.fullscreenContainer.style.alignItems = 'center';
    document.body.appendChild(this.fullscreenContainer);
    
    this.log('Containers de anúncios criados');
  }
  
  /**
   * Configura a detecção do Unity
   */
  setupUnityDetection() {
    // Verificar se o Unity já está disponível
    if (window.unityInstance) {
      this.unityInstance = window.unityInstance;
      this.log('Unity já está disponível');
      this.repositionBanner();
      return;
    }
    
    // Observar quando o Unity estiver disponível
    const checkUnity = setInterval(() => {
      if (window.unityInstance) {
        this.unityInstance = window.unityInstance;
        this.log('Unity detectado');
        this.repositionBanner();
        clearInterval(checkUnity);
      }
    }, 1000);
    
    this.log('Configurada detecção do Unity');
  }
  
  /**
   * Carrega os banners da API
   */
  loadBanners() {
    this.log('Carregando banners...');
    
    fetch(`${ADS_CONFIG.API_URL}${ADS_CONFIG.BANNERS_ENDPOINT}`)
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
      })
      .then(data => {
        this.banners = data;
        this.log(`${this.banners.length} banners carregados`);
        
        if (this.banners.length > 0) {
          this.showBanner(this.currentBannerIndex);
          this.startBannerRotation();
        }
      })
      .catch(error => {
        this.error(`Erro ao carregar banners: ${error.message}`);
        
        // Retry
        if (this.retryCount < ADS_CONFIG.MAX_RETRIES) {
          this.retryCount++;
          this.log(`Tentando novamente em ${ADS_CONFIG.RETRY_DELAY / 1000} segundos... (${this.retryCount}/${ADS_CONFIG.MAX_RETRIES})`);
          
          setTimeout(() => this.loadBanners(), ADS_CONFIG.RETRY_DELAY);
        }
      });
  }
  
  /**
   * Carrega os anúncios de tela cheia da API
   */
  loadFullscreenAds() {
    this.log('Carregando anúncios de tela cheia...');
    
    fetch(`${ADS_CONFIG.API_URL}${ADS_CONFIG.FULLSCREEN_ENDPOINT}`)
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
      })
      .then(data => {
        this.fullscreenAds = data;
        this.log(`${this.fullscreenAds.length} anúncios de tela cheia carregados`);
      })
      .catch(error => {
        this.error(`Erro ao carregar anúncios de tela cheia: ${error.message}`);
        
        // Retry
        if (this.retryCount < ADS_CONFIG.MAX_RETRIES) {
          this.retryCount++;
          this.log(`Tentando novamente em ${ADS_CONFIG.RETRY_DELAY / 1000} segundos... (${this.retryCount}/${ADS_CONFIG.MAX_RETRIES})`);
          
          setTimeout(() => this.loadFullscreenAds(), ADS_CONFIG.RETRY_DELAY);
        }
      });
  }
  
  /**
   * Exibe um banner específico
   * @param {number} index - Índice do banner a ser exibido
   */
  showBanner(index) {
    if (!this.banners || this.banners.length === 0) {
      this.log('Nenhum banner disponível para exibir');
      return;
    }
    
    if (index >= this.banners.length) {
      index = 0;
    }
    
    const banner = this.banners[index];
    this.currentBannerIndex = index;
    
    // Criar HTML do banner
    const bannerHTML = `
      <a href="${banner.targetUrl || banner.linkUrl}" target="_blank" id="ad-banner-link">
        <img src="${banner.imageUrl}" alt="${banner.title}" style="width:${ADS_CONFIG.BANNER_WIDTH}px;height:${ADS_CONFIG.BANNER_HEIGHT}px;">
      </a>
    `;
    
    // Atualizar container
    if (this.bannerContainer) {
      this.bannerContainer.innerHTML = bannerHTML;
      this.bannerContainer.style.display = 'block';
      
      // Garantir que o banner esteja visível
      this.bannerContainer.style.visibility = 'visible';
      this.bannerContainer.style.opacity = '1';
      
      // Posicionar o banner
      this.repositionBanner();
      
      // Registrar impressão
      this.recordImpression(banner.id, 'banner');
      
      // Adicionar evento de clique
      const bannerLink = document.getElementById('ad-banner-link');
      if (bannerLink) {
        bannerLink.addEventListener('click', () => {
          this.recordClick(banner.id, 'banner');
        });
      }
      
      this.log(`Banner exibido: ${banner.title}`);
    } else {
      this.error('Container de banner não encontrado');
    }
  }
  
  /**
   * Exibe um anúncio de tela cheia aleatório
   */
  showFullscreenAd() {
    if (!this.fullscreenAds || this.fullscreenAds.length === 0) {
      this.log('Nenhum anúncio de tela cheia disponível');
      return;
    }
    
    // Pausar o jogo
    this.pauseGame();
    
    // Selecionar um anúncio aleatório
    const randomIndex = Math.floor(Math.random() * this.fullscreenAds.length);
    const ad = this.fullscreenAds[randomIndex];
    
    // Criar HTML do anúncio
    const adHTML = `
      <div style="position:relative;width:360px;height:640px;background-color:white;border-radius:10px;overflow:hidden;">
        <a href="${ad.targetUrl || ad.linkUrl}" target="_blank" id="ad-fullscreen-link">
          <img src="${ad.imageUrl}" alt="${ad.title}" style="width:100%;height:100%;object-fit:cover;">
        </a>
        <button id="ad-close-button" style="position:absolute;top:10px;right:10px;width:30px;height:30px;background-color:rgba(0,0,0,0.5);color:white;border:none;border-radius:15px;font-size:16px;cursor:pointer;">X</button>
      </div>
    `;
    
    // Atualizar container
    if (this.fullscreenContainer) {
      this.fullscreenContainer.innerHTML = adHTML;
      this.fullscreenContainer.style.display = 'flex';
      
      // Registrar impressão
      this.recordImpression(ad.id, 'fullscreen');
      
      // Adicionar evento de clique no anúncio
      const adLink = document.getElementById('ad-fullscreen-link');
      if (adLink) {
        adLink.addEventListener('click', () => {
          this.recordClick(ad.id, 'fullscreen');
        });
      }
      
      // Adicionar evento de clique no botão de fechar
      const closeButton = document.getElementById('ad-close-button');
      if (closeButton) {
        closeButton.addEventListener('click', (e) => {
          e.preventDefault();
          this.hideFullscreenAd();
        });
      }
      
      this.log(`Anúncio de tela cheia exibido: ${ad.title}`);
    } else {
      this.error('Container de anúncio de tela cheia não encontrado');
    }
  }
  
  /**
   * Esconde o anúncio de tela cheia
   */
  hideFullscreenAd() {
    if (this.fullscreenContainer) {
      this.fullscreenContainer.style.display = 'none';
      this.fullscreenContainer.innerHTML = '';
      
      // Retomar o jogo
      this.resumeGame();
      
      this.log('Anúncio de tela cheia fechado');
    }
  }
  
  /**
   * Inicia a rotação de banners
   */
  startBannerRotation() {
    if (this.bannerRotationInterval) {
      clearInterval(this.bannerRotationInterval);
    }
    
    this.bannerRotationInterval = setInterval(() => {
      this.currentBannerIndex = (this.currentBannerIndex + 1) % this.banners.length;
      this.showBanner(this.currentBannerIndex);
    }, ADS_CONFIG.BANNER_ROTATION_INTERVAL);
    
    this.log('Rotação de banners iniciada');
  }
  
  /**
   * Pausa a rotação de banners
   */
  stopBannerRotation() {
    if (this.bannerRotationInterval) {
      clearInterval(this.bannerRotationInterval);
      this.bannerRotationInterval = null;
      this.log('Rotação de banners pausada');
    }
  }
  
  /**
   * Registra uma impressão de anúncio
   * @param {string} adId - ID do anúncio
   * @param {string} type - Tipo do anúncio ('banner' ou 'fullscreen')
   */
  recordImpression(adId, type) {
    fetch(`${ADS_CONFIG.API_URL}${ADS_CONFIG.IMPRESSION_ENDPOINT}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        adId: adId,
        type: type
      })
    })
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
      })
      .then(data => {
        this.log(`Impressão registrada: ${type} ${adId}`);
      })
      .catch(error => {
        this.error(`Erro ao registrar impressão: ${error.message}`);
      });
  }
  
  /**
   * Registra um clique em anúncio
   * @param {string} adId - ID do anúncio
   * @param {string} type - Tipo do anúncio ('banner' ou 'fullscreen')
   */
  recordClick(adId, type) {
    fetch(`${ADS_CONFIG.API_URL}${ADS_CONFIG.CLICK_ENDPOINT}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        adId: adId,
        type: type
      })
    })
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
      })
      .then(data => {
        this.log(`Clique registrado: ${type} ${adId}`);
      })
      .catch(error => {
        this.error(`Erro ao registrar clique: ${error.message}`);
      });
  }
  
  /**
   * Pausa o jogo
   */
  pauseGame() {
    if (this.gameIsPaused) {
      return;
    }
    
    this.gameIsPaused = true;
    
    // Tentar pausar via unityInstance
    if (this.unityInstance && typeof this.unityInstance.SendMessage === 'function') {
      try {
        this.unityInstance.SendMessage('GameManager', 'PauseGame');
        this.log('Jogo pausado via unityInstance.SendMessage');
        return;
      } catch (e) {
        this.error(`Erro ao pausar jogo via unityInstance: ${e.message}`);
      }
    }
    
    // Tentar pausar via função global
    if (typeof window.pauseGame === 'function') {
      try {
        window.pauseGame();
        this.log('Jogo pausado via função global');
        return;
      } catch (e) {
        this.error(`Erro ao pausar jogo via função global: ${e.message}`);
      }
    }
    
    this.log('Não foi possível pausar o jogo automaticamente');
  }
  
  /**
   * Retoma o jogo
   */
  resumeGame() {
    if (!this.gameIsPaused) {
      return;
    }
    
    this.gameIsPaused = false;
    
    // Tentar retomar via unityInstance
    if (this.unityInstance && typeof this.unityInstance.SendMessage === 'function') {
      try {
        this.unityInstance.SendMessage('GameManager', 'ResumeGame');
        this.log('Jogo retomado via unityInstance.SendMessage');
        return;
      } catch (e) {
        this.error(`Erro ao retomar jogo via unityInstance: ${e.message}`);
      }
    }
    
    // Tentar retomar via função global
    if (typeof window.resumeGame === 'function') {
      try {
        window.resumeGame();
        this.log('Jogo retomado via função global');
        return;
      } catch (e) {
        this.error(`Erro ao retomar jogo via função global: ${e.message}`);
      }
    }
    
    this.log('Não foi possível retomar o jogo automaticamente');
  }
  
  /**
   * Reposiciona o banner para ficar dentro do canvas do Unity
   */
  repositionBanner() {
    if (!this.bannerContainer) {
      return;
    }
    
    // Encontrar o canvas do Unity
    const unityCanvas = document.getElementById('unity-canvas');
    if (!unityCanvas) {
      this.log('Canvas do Unity não encontrado, usando posicionamento padrão');
      return;
    }
    
    // Obter dimensões e posição do canvas
    const canvasRect = unityCanvas.getBoundingClientRect();
    
    // Posicionar o banner no topo do canvas
    this.bannerContainer.style.position = 'absolute';
    this.bannerContainer.style.top = `${canvasRect.top}px`;
    this.bannerContainer.style.left = `${canvasRect.left + (canvasRect.width - ADS_CONFIG.BANNER_WIDTH) / 2}px`;
    this.bannerContainer.style.width = `${ADS_CONFIG.BANNER_WIDTH}px`;
    this.bannerContainer.style.height = `${ADS_CONFIG.BANNER_HEIGHT}px`;
    
    this.log(`Banner reposicionado: top=${this.bannerContainer.style.top}, left=${this.bannerContainer.style.left}`);
  }
  
  /**
   * Verifica e corrige a visibilidade dos anúncios
   */
  checkVisibility() {
    if (!this.bannerContainer) {
      return;
    }
    
    // Verificar se o banner está visível
    const style = window.getComputedStyle(this.bannerContainer);
    if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') {
      this.log('Banner não está visível, corrigindo...');
      
      this.bannerContainer.style.display = 'block';
      this.bannerContainer.style.visibility = 'visible';
      this.bannerContainer.style.opacity = '1';
      
      // Reposicionar o banner
      this.repositionBanner();
    }
  }
  
  /**
   * Registra uma mensagem de log
   * @param {string} message - Mensagem a ser registrada
   */
  log(message) {
    if (ADS_CONFIG.DEBUG) {
      const timestamp = new Date().toLocaleTimeString();
      console.log(`${ADS_CONFIG.LOG_PREFIX} ${timestamp} ℹ️ ${message}`);
    }
  }
  
  /**
   * Registra uma mensagem de erro
   * @param {string} message - Mensagem de erro a ser registrada
   */
  error(message) {
    if (ADS_CONFIG.DEBUG) {
      const timestamp = new Date().toLocaleTimeString();
      console.error(`${ADS_CONFIG.LOG_PREFIX} ${timestamp} ❌ ${message}`);
    }
  }
  
  /**
   * Exibe informações de diagnóstico
   */
  diagnose() {
    this.log('Diagnóstico do sistema de anúncios:');
    this.log(`- Banners carregados: ${this.banners.length}`);
    this.log(`- Anúncios de tela cheia carregados: ${this.fullscreenAds.length}`);
    this.log(`- Banner container existe: ${!!this.bannerContainer}`);
    this.log(`- Fullscreen container existe: ${!!this.fullscreenContainer}`);
    this.log(`- Unity detectado: ${!!this.unityInstance}`);
    
    if (this.bannerContainer) {
      const style = window.getComputedStyle(this.bannerContainer);
      this.log(`- Banner visibilidade: display=${style.display}, visibility=${style.visibility}, opacity=${style.opacity}`);
      this.log(`- Banner posição: top=${style.top}, left=${style.left}, z-index=${style.zIndex}`);
    }
    
    const unityCanvas = document.getElementById('unity-canvas');
    if (unityCanvas) {
      const rect = unityCanvas.getBoundingClientRect();
      this.log(`- Canvas do Unity: top=${rect.top}, left=${rect.left}, width=${rect.width}, height=${rect.height}`);
    } else {
      this.log('- Canvas do Unity não encontrado');
    }
  }
}

// Inicializar o sistema de anúncios
const adSystem = new AdSystem();

// Expor funções para o Unity
window.showBanner = () => {
  if (adSystem) {
    adSystem.showBanner(0);
    return true;
  }
  return false;
};

window.hideBanner = () => {
  if (adSystem && adSystem.bannerContainer) {
    adSystem.bannerContainer.style.display = 'none';
    return true;
  }
  return false;
};

window.showFullscreenAd = () => {
  if (adSystem) {
    adSystem.showFullscreenAd();
    return true;
  }
  return false;
};

window.diagnoseAds = () => {
  if (adSystem) {
    adSystem.diagnose();
    return true;
  }
  return false;
};
