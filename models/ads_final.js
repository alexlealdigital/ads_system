/**
 * Sistema de Anúncios para Jogos Unity WebGL
 * Versão: 1.2.0
 * 
 * Este script gerencia a exibição de anúncios em jogos Unity WebGL:
 * - Banners rotativos no topo da página (1080px × 140px)
 * - Anúncios de tela cheia após game overs (1080px × 1920px)
 * - Rastreamento de impressões e cliques
 * 
 * Otimizado para máxima robustez e compatibilidade
 */

// Configuração do sistema de anúncios - Namespace isolado para evitar conflitos
const adSystem = (function() {
  // Configurações padrão
  const defaultConfig = {
    apiUrl: 'https://ads-system-backend.onrender.com',
    bannerRotationInterval: 7000, // 7 segundos
    fullscreenDuration: 5000,     // 5 segundos
    gameOverCountThreshold: 5,    // Mostrar anúncio a cada 5 game overs
    debug: true,                  // Ativar logs de depuração
    retryAttempts: 3,             // Número de tentativas para carregar anúncios
    retryDelay: 3000,             // Tempo entre tentativas (ms)
    fallbackImageUrl: '',         // URL de imagem de fallback (opcional)
    fallbackTargetUrl: 'https://alexlealdigital.github.io', // URL de destino de fallback
    containerZIndex: {
      banner: 9999,               // Z-index muito alto para garantir que fique acima do canvas
      fullscreen: 10000           // Z-index ainda mais alto para tela cheia
    }
  };
  
  // Estado do sistema
  let state = {
    banners: [],
    fullscreenAds: [],
    currentBannerIndex: 0,
    gameOverCount: 0,
    bannerRotationTimer: null,
    isGameScreen: false,
    unityInstance: null,
    initialized: false,
    loadAttempts: {
      banners: 0,
      fullscreen: 0
    },
    pendingTimers: [],
    observer: null
  };
  
  // Cache de elementos DOM
  const domElements = {
    bannerContainer: null,
    fullscreenContainer: null,
    fullscreenContent: null,
    gameScreenIndicator: null
  };
  
  // Utilitários privados
  const utils = {
    // Função segura para obter propriedades de objetos, com valor padrão
    safeGet: function(obj, path, defaultValue) {
      if (!obj) return defaultValue;
      
      const keys = path.split('.');
      let current = obj;
      
      for (let i = 0; i < keys.length; i++) {
        if (current === null || current === undefined) {
          return defaultValue;
        }
        current = current[keys[i]];
      }
      
      return (current === undefined || current === null) ? defaultValue : current;
    },
    
    // Função para criar elemento com estilos
    createElement: function(tag, id, styles, parent) {
      const element = document.createElement(tag);
      if (id) element.id = id;
      
      if (styles) {
        Object.keys(styles).forEach(key => {
          element.style[key] = styles[key];
        });
      }
      
      if (parent) {
        parent.appendChild(element);
      }
      
      return element;
    },
    
    // Função para limpar timers
    clearAllTimers: function() {
      if (state.bannerRotationTimer) {
        clearInterval(state.bannerRotationTimer);
        state.bannerRotationTimer = null;
      }
      
      state.pendingTimers.forEach(timer => {
        clearTimeout(timer);
      });
      
      state.pendingTimers = [];
    },
    
    // Função para adicionar timer à lista de pendentes
    addTimer: function(timer) {
      state.pendingTimers.push(timer);
      return timer;
    },
    
    // Função para remover timer da lista de pendentes
    removeTimer: function(timer) {
      const index = state.pendingTimers.indexOf(timer);
      if (index !== -1) {
        state.pendingTimers.splice(index, 1);
      }
    },
    
    // Função para verificar se um elemento existe no DOM
    elementExists: function(element) {
      return element !== null && document.body.contains(element);
    },
    
    // Função para verificar se uma URL é válida
    isValidUrl: function(url) {
      if (!url) return false;
      
      try {
        new URL(url);
        return true;
      } catch (e) {
        return false;
      }
    },
    
    // Função para tentar novamente uma operação após um atraso
    retry: function(fn, delay, maxAttempts, attemptCount, context) {
      if (attemptCount >= maxAttempts) {
        publicAPI.log(`Máximo de tentativas (${maxAttempts}) atingido para operação`, 'warn');
        return;
      }
      
      const timer = setTimeout(() => {
        utils.removeTimer(timer);
        fn.call(context);
      }, delay);
      
      utils.addTimer(timer);
    },
    
    // Função para garantir que um elemento esteja visível
    ensureElementVisibility: function(element) {
      if (!element) return;
      
      // Forçar visibilidade
      element.style.display = 'block';
      element.style.visibility = 'visible';
      element.style.opacity = '1';
      
      // Garantir que esteja acima de outros elementos
      const computedZIndex = parseInt(window.getComputedStyle(element).zIndex, 10);
      if (isNaN(computedZIndex) || computedZIndex < 9000) {
        element.style.zIndex = '9999';
      }
      
      // Verificar se o elemento está realmente visível
      const rect = element.getBoundingClientRect();
      const isVisible = rect.width > 0 && rect.height > 0;
      
      if (!isVisible) {
        publicAPI.log(`Elemento ${element.id} tem dimensões zero, ajustando...`, 'warn');
        element.style.width = '100%';
        element.style.height = '140px'; // Altura do banner
      }
      
      // Verificar se o elemento está anexado ao DOM
      if (!document.body.contains(element)) {
        publicAPI.log(`Elemento ${element.id} não está no DOM, reapendendo...`, 'warn');
        document.body.appendChild(element);
      }
    }
  };
  
  // API pública
  const publicAPI = {
    // Configurações
    config: { ...defaultConfig },
    
    // Inicialização do sistema
    init: function(customConfig) {
      try {
        // Evitar inicialização duplicada
        if (state.initialized) {
          this.log('Sistema de anúncios já inicializado, ignorando chamada duplicada');
          return;
        }
        
        this.log('Inicializando sistema de anúncios...');
        
        // Mesclar configurações personalizadas
        if (customConfig && typeof customConfig === 'object') {
          Object.keys(customConfig).forEach(key => {
            if (this.config[key] !== undefined) {
              if (typeof this.config[key] === 'object' && !Array.isArray(this.config[key])) {
                this.config[key] = { ...this.config[key], ...customConfig[key] };
              } else {
                this.config[key] = customConfig[key];
              }
            }
          });
        }
        
        // Criar elementos de UI
        this.createBannerContainer();
        this.createFullscreenContainer();
        
        // Configurar eventos
        this.setupEventListeners();
        
        // Carregar anúncios do backend
        this.loadBanners();
        this.loadFullscreenAds();
        
        // Iniciar rotação de banners
        this.startBannerRotation();
        
        // Verificar visibilidade periodicamente
        this.startVisibilityCheck();
        
        state.initialized = true;
        this.log('Sistema de anúncios inicializado com sucesso');
      } catch (error) {
        this.log(`Erro durante inicialização: ${error.message}`, 'error');
        console.error(error);
      }
    },
    
    // Iniciar verificação periódica de visibilidade
    startVisibilityCheck: function() {
      const checkInterval = setInterval(() => {
        if (state.isGameScreen && domElements.bannerContainer) {
          utils.ensureElementVisibility(domElements.bannerContainer);
          this.log('Verificação de visibilidade do banner executada');
        }
      }, 5000); // Verificar a cada 5 segundos
      
      utils.addTimer(checkInterval);
    },
    
    // Reinicializar o sistema (útil após mudanças de configuração)
    reset: function() {
      this.log('Reiniciando sistema de anúncios...');
      
      // Limpar timers
      utils.clearAllTimers();
      
      // Desconectar observer
      if (state.observer) {
        state.observer.disconnect();
        state.observer = null;
      }
      
      // Remover elementos do DOM
      if (domElements.bannerContainer && document.body.contains(domElements.bannerContainer)) {
        document.body.removeChild(domElements.bannerContainer);
      }
      
      if (domElements.fullscreenContainer && document.body.contains(domElements.fullscreenContainer)) {
        document.body.removeChild(domElements.fullscreenContainer);
      }
      
      // Resetar estado
      state = {
        banners: [],
        fullscreenAds: [],
        currentBannerIndex: 0,
        gameOverCount: 0,
        bannerRotationTimer: null,
        isGameScreen: false,
        unityInstance: null,
        initialized: false,
        loadAttempts: {
          banners: 0,
          fullscreen: 0
        },
        pendingTimers: [],
        observer: null
      };
      
      // Resetar cache de elementos DOM
      Object.keys(domElements).forEach(key => {
        domElements[key] = null;
      });
      
      // Reinicializar
      setTimeout(() => {
        this.init();
      }, 100);
    },
    
    // Criar container para banners
    createBannerContainer: function() {
      try {
        // Verificar se o container já existe
        const existingContainer = document.getElementById('ad-banner-container');
        if (existingContainer) {
          domElements.bannerContainer = existingContainer;
          this.log('Container de banner já existe, reutilizando');
          
          // Garantir que o container tenha os estilos corretos
          Object.assign(existingContainer.style, {
            position: 'fixed', // Alterado para fixed para garantir posicionamento absoluto na viewport
            top: '0',
            left: '0',
            width: '100%',
            height: '140px',
            zIndex: this.config.containerZIndex.banner.toString(),
            display: 'none',
            overflow: 'hidden',
            pointerEvents: 'auto',
            backgroundColor: 'transparent', // Fundo transparente
            textAlign: 'center', // Centralizar o conteúdo
            boxSizing: 'border-box', // Garantir que padding não afete dimensões
            margin: '0', // Remover margens
            padding: '0', // Remover padding
            border: 'none', // Remover bordas
            visibility: 'visible', // Garantir visibilidade
            opacity: '1' // Garantir opacidade total
          });
          
          return;
        }
        
        // Criar novo container
        const container = utils.createElement('div', 'ad-banner-container', {
          position: 'fixed', // Alterado para fixed para garantir posicionamento absoluto na viewport
          top: '0',
          left: '0',
          width: '100%',
          height: '140px',
          zIndex: this.config.containerZIndex.banner.toString(),
          display: 'none',
          overflow: 'hidden',
          pointerEvents: 'auto',
          backgroundColor: 'transparent', // Fundo transparente
          textAlign: 'center', // Centralizar o conteúdo
          boxSizing: 'border-box', // Garantir que padding não afete dimensões
          margin: '0', // Remover margens
          padding: '0', // Remover padding
          border: 'none', // Remover bordas
          visibility: 'visible', // Garantir visibilidade
          opacity: '1' // Garantir opacidade total
        }, document.body);
        
        // Adicionar um elemento de debug para visualização
        const debugElement = utils.createElement('div', 'ad-banner-debug', {
          position: 'absolute',
          top: '0',
          left: '0',
          width: '100%',
          height: '100%',
          backgroundColor: 'rgba(255, 0, 0, 0.1)', // Vermelho transparente para debug
          color: 'white',
          fontSize: '12px',
          textAlign: 'center',
          lineHeight: '140px',
          pointerEvents: 'none',
          display: 'none' // Inicialmente oculto
        }, container);
        
        debugElement.textContent = 'Área de Banner (1080×140px)';
        
        // Mostrar elemento de debug se em modo de depuração
        if (this.config.debug) {
          debugElement.style.display = 'block';
        }
        
        domElements.bannerContainer = container;
        this.log('Container de banner criado com sucesso');
        
        // Garantir que o container esteja no topo do DOM para máxima visibilidade
        document.body.appendChild(container);
      } catch (error) {
        this.log(`Erro ao criar container de banner: ${error.message}`, 'error');
      }
    },
    
    // Criar container para anúncios de tela cheia
    createFullscreenContainer: function() {
      try {
        // Verificar se o container já existe
        const existingContainer = document.getElementById('ad-fullscreen-container');
        if (existingContainer) {
          domElements.fullscreenContainer = existingContainer;
          domElements.fullscreenContent = document.getElementById('ad-fullscreen-content');
          this.log('Container de anúncio de tela cheia já existe, reutilizando');
          
          // Garantir que o container tenha os estilos corretos
          Object.assign(existingContainer.style, {
            position: 'fixed',
            top: '0',
            left: '0',
            width: '100%',
            height: '100%',
            zIndex: this.config.containerZIndex.fullscreen.toString(),
            display: 'none',
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            justifyContent: 'center',
            alignItems: 'center',
            pointerEvents: 'auto',
            visibility: 'visible', // Garantir visibilidade
            opacity: '1' // Garantir opacidade total
          });
          
          return;
        }
        
        const container = utils.createElement('div', 'ad-fullscreen-container', {
          position: 'fixed',
          top: '0',
          left: '0',
          width: '100%',
          height: '100%',
          zIndex: this.config.containerZIndex.fullscreen.toString(),
          display: 'none',
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          justifyContent: 'center',
          alignItems: 'center',
          pointerEvents: 'auto',
          visibility: 'visible', // Garantir visibilidade
          opacity: '1' // Garantir opacidade total
        }, document.body);
        
        const adContent = utils.createElement('div', 'ad-fullscreen-content', {
          position: 'relative',
          width: '1080px',
          height: '1920px',
          maxWidth: '90%',
          maxHeight: '90%',
          backgroundSize: 'contain',
          backgroundPosition: 'center',
          backgroundRepeat: 'no-repeat',
          cursor: 'pointer'
        }, container);
        
        const closeButton = utils.createElement('div', 'ad-fullscreen-close', {
          position: 'absolute',
          top: '10px',
          right: '10px',
          width: '40px',
          height: '40px',
          backgroundColor: 'rgba(0, 0, 0, 0.5)',
          color: 'white',
          fontSize: '30px',
          lineHeight: '40px',
          textAlign: 'center',
          cursor: 'pointer',
          borderRadius: '20px',
          zIndex: (parseInt(this.config.containerZIndex.fullscreen) + 1).toString()
        }, container);
        
        closeButton.innerHTML = '×';
        closeButton.addEventListener('click', (e) => {
          e.stopPropagation();
          this.hideFullscreenAd();
        });
        
        domElements.fullscreenContainer = container;
        domElements.fullscreenContent = adContent;
        
        this.log('Container de anúncio de tela cheia criado com sucesso');
        
        // Garantir que o container esteja no topo do DOM para máxima visibilidade
        document.body.appendChild(container);
      } catch (error) {
        this.log(`Erro ao criar container de anúncio de tela cheia: ${error.message}`, 'error');
      }
    },
    
    // Configurar event listeners
    setupEventListeners: function() {
      try {
        // Detectar quando o Unity está pronto
        window.addEventListener('unityInstance', (event) => {
          state.unityInstance = event.detail;
          this.log('Unity instance detectada e registrada');
        });
        
        // Verificar se o indicador de tela de jogo já existe
        domElements.gameScreenIndicator = document.querySelector('.game-screen-indicator');
        
        // Criar o indicador se não existir
        if (!domElements.gameScreenIndicator) {
          domElements.gameScreenIndicator = utils.createElement('div', null, {
            display: 'none'
          }, document.body);
          
          domElements.gameScreenIndicator.className = 'game-screen-indicator';
          this.log('Indicador de tela de jogo criado');
        }
        
        // Configurar observer para monitorar mudanças no indicador
        state.observer = new MutationObserver((mutations) => {
          mutations.forEach((mutation) => {
            if (mutation.target.className === 'game-screen-indicator') {
              const newIsGameScreen = (mutation.target.style.display === 'block');
              
              // Só atualizar se o estado realmente mudou
              if (state.isGameScreen !== newIsGameScreen) {
                state.isGameScreen = newIsGameScreen;
                this.log(`Estado da tela de jogo alterado: ${state.isGameScreen}`);
                
                if (state.isGameScreen) {
                  this.showBanner();
                } else {
                  this.hideBanner();
                }
              }
            }
          });
        });
        
        // Iniciar observação do indicador
        state.observer.observe(domElements.gameScreenIndicator, { 
          attributes: true, 
          attributeFilter: ['style'] 
        });
        
        // Verificar estado inicial
        state.isGameScreen = (domElements.gameScreenIndicator.style.display === 'block');
        if (state.isGameScreen) {
          this.showBanner();
        }
        
        // Adicionar listener para redimensionamento da janela
        window.addEventListener('resize', () => {
          if (state.isGameScreen && domElements.bannerContainer) {
            // Reposicionar banner após redimensionamento
            setTimeout(() => {
              utils.ensureElementVisibility(domElements.bannerContainer);
            }, 100);
          }
        });
        
        this.log('Event listeners configurados com sucesso');
      } catch (error) {
        this.log(`Erro ao configurar event listeners: ${error.message}`, 'error');
      }
    },
    
    // Carregar banners do backend
    loadBanners: function() {
      try {
        this.log('Carregando banners...');
        state.loadAttempts.banners++;
        
        fetch(`${this.config.apiUrl}/api/banners`)
          .then(response => {
            if (!response.ok) {
              throw new Error(`Resposta do servidor não ok: ${response.status}`);
            }
            return response.json();
          })
          .then(data => {
            if (!Array.isArray(data)) {
              throw new Error('Formato de dados inválido: esperava um array');
            }
            
            state.banners = data;
            this.log(`${data.length} banners carregados com sucesso`);
            
            // Verificar e corrigir URLs
            state.banners.forEach((banner, index) => {
              // Verificar imageUrl
              if (!utils.isValidUrl(banner.imageUrl)) {
                this.log(`Banner ${index} tem imageUrl inválida: ${banner.imageUrl}`, 'warn');
                banner.imageUrl = this.config.fallbackImageUrl;
              }
              
              // Verificar targetUrl vs linkUrl (compatibilidade com diferentes versões)
              if (!banner.targetUrl && banner.linkUrl) {
                banner.targetUrl = banner.linkUrl;
              } else if (!banner.targetUrl && !banner.linkUrl) {
                this.log(`Banner ${index} não tem URL de destino`, 'warn');
                banner.targetUrl = this.config.fallbackTargetUrl;
              }
            });
            
            if (data.length > 0 && state.isGameScreen) {
              this.showBanner();
            }
            
            // Resetar contador de tentativas
            state.loadAttempts.banners = 0;
          })
          .catch(error => {
            this.log(`Erro ao carregar banners: ${error.message}`, 'error');
            
            // Tentar novamente se não excedeu o limite de tentativas
            if (state.loadAttempts.banners < this.config.retryAttempts) {
              this.log(`Tentando carregar banners novamente (${state.loadAttempts.banners}/${this.config.retryAttempts})...`);
              utils.retry(this.loadBanners, this.config.retryDelay, this.config.retryAttempts, state.loadAttempts.banners, this);
            }
          });
      } catch (error) {
        this.log(`Erro ao iniciar carregamento de banners: ${error.message}`, 'error');
      }
    },
    
    // Carregar anúncios de tela cheia do backend
    loadFullscreenAds: function() {
      try {
        this.log('Carregando anúncios de tela cheia...');
        state.loadAttempts.fullscreen++;
        
        fetch(`${this.config.apiUrl}/api/fullscreen`)
          .then(response => {
            if (!response.ok) {
              throw new Error(`Resposta do servidor não ok: ${response.status}`);
            }
            return response.json();
          })
          .then(data => {
            if (!Array.isArray(data)) {
              throw new Error('Formato de dados inválido: esperava um array');
            }
            
            state.fullscreenAds = data;
            this.log(`${data.length} anúncios de tela cheia carregados com sucesso`);
            
            // Verificar e corrigir URLs
            state.fullscreenAds.forEach((ad, index) => {
              // Verificar imageUrl
              if (!utils.isValidUrl(ad.imageUrl)) {
                this.log(`Anúncio de tela cheia ${index} tem imageUrl inválida: ${ad.imageUrl}`, 'warn');
                ad.imageUrl = this.config.fallbackImageUrl;
              }
              
              // Verificar targetUrl vs linkUrl (compatibilidade com diferentes versões)
              if (!ad.targetUrl && ad.linkUrl) {
                ad.targetUrl = ad.linkUrl;
              } else if (!ad.targetUrl && !ad.linkUrl) {
                this.log(`Anúncio de tela cheia ${index} não tem URL de destino`, 'warn');
                ad.targetUrl = this.config.fallbackTargetUrl;
              }
            });
            
            // Resetar contador de tentativas
            state.loadAttempts.fullscreen = 0;
          })
          .catch(error => {
            this.log(`Erro ao carregar anúncios de tela cheia: ${error.message}`, 'error');
            
            // Tentar novamente se não excedeu o limite de tentativas
            if (state.loadAttempts.fullscreen < this.config.retryAttempts) {
              this.log(`Tentando carregar anúncios de tela cheia novamente (${state.loadAttempts.fullscreen}/${this.config.retryAttempts})...`);
              utils.retry(this.loadFullscreenAds, this.config.retryDelay, this.config.retryAttempts, state.loadAttempts.fullscreen, this);
            }
          });
      } catch (error) {
        this.log(`Erro ao iniciar carregamento de anúncios de tela cheia: ${error.message}`, 'error');
      }
    },
    
    // Iniciar rotação de banners
    startBannerRotation: function() {
      try {
        // Limpar timer existente
        if (state.bannerRotationTimer) {
          clearInterval(state.bannerRotationTimer);
        }
        
        // Iniciar novo timer
        state.bannerRotationTimer = setInterval(() => {
          this.rotateBanner();
        }, this.config.bannerRotationInterval);
        
        this.log(`Rotação de banners iniciada com intervalo de ${this.config.bannerRotationInterval}ms`);
      } catch (error) {
        this.log(`Erro ao iniciar rotação de banners: ${error.message}`, 'error');
      }
    },
    
    // Rotacionar para o próximo banner
    rotateBanner: function() {
      try {
        if (state.banners.length === 0) {
          return;
        }
        
        // Avançar para o próximo banner
        state.currentBannerIndex = (state.currentBannerIndex + 1) % state.banners.length;
        
        // Mostrar o banner atual se estiver na tela de jogo
        if (state.isGameScreen) {
          this.showBanner();
        }
        
        this.log(`Banner rotacionado para índice ${state.currentBannerIndex}`);
      } catch (error) {
        this.log(`Erro ao rotacionar banner: ${error.message}`, 'error');
      }
    },
    
    // Mostrar banner atual
    showBanner: function() {
      try {
        if (!domElements.bannerContainer) {
          this.log('Container de banner não encontrado', 'warn');
          return;
        }
        
        if (state.banners.length === 0) {
          this.log('Nenhum banner disponível para exibição', 'warn');
          return;
        }
        
        const currentBanner = state.banners[state.currentBannerIndex];
        
        // Verificar se o banner é válido
        if (!currentBanner || !currentBanner.imageUrl) {
          this.log('Banner atual inválido', 'warn');
          return;
        }
        
        // Configurar o container
        domElements.bannerContainer.style.backgroundImage = `url('${currentBanner.imageUrl}')`;
        domElements.bannerContainer.style.backgroundSize = 'contain';
        domElements.bannerContainer.style.backgroundPosition = 'center';
        domElements.bannerContainer.style.backgroundRepeat = 'no-repeat';
        
        // Garantir que o container esteja visível
        domElements.bannerContainer.style.display = 'block';
        domElements.bannerContainer.style.visibility = 'visible';
        domElements.bannerContainer.style.opacity = '1';
        
        // Garantir que o z-index seja alto o suficiente
        domElements.bannerContainer.style.zIndex = this.config.containerZIndex.banner.toString();
        
        // Limpar event listeners existentes
        const newContainer = domElements.bannerContainer.cloneNode(true);
        domElements.bannerContainer.parentNode.replaceChild(newContainer, domElements.bannerContainer);
        domElements.bannerContainer = newContainer;
        
        // Adicionar event listener para cliques
        domElements.bannerContainer.addEventListener('click', () => {
          this.handleBannerClick(currentBanner);
        });
        
        // Garantir que o container esteja no topo do DOM
        document.body.appendChild(domElements.bannerContainer);
        
        // Verificar visibilidade após um curto atraso
        setTimeout(() => {
          utils.ensureElementVisibility(domElements.bannerContainer);
        }, 100);
        
        this.log(`Banner exibido: ${currentBanner.id}`);
        
        // Registrar impressão
        this.recordImpression(currentBanner.id, 'banner');
      } catch (error) {
        this.log(`Erro ao exibir banner: ${error.message}`, 'error');
      }
    },
    
    // Esconder banner
    hideBanner: function() {
      try {
        if (!domElements.bannerContainer) {
          return;
        }
        
        domElements.bannerContainer.style.display = 'none';
      } catch (error) {
        this.log(`Erro ao esconder banner: ${error.message}`, 'error');
      }
    },
    
    // Mostrar anúncio de tela cheia
    showFullscreenAd: function() {
      try {
        if (!domElements.fullscreenContainer || !domElements.fullscreenContent) {
          this.log('Container de anúncio de tela cheia não encontrado', 'warn');
          return false;
        }
        
        if (state.fullscreenAds.length === 0) {
          this.log('Nenhum anúncio de tela cheia disponível', 'warn');
          return false;
        }
        
        // Selecionar um anúncio aleatório
        const randomIndex = Math.floor(Math.random() * state.fullscreenAds.length);
        const ad = state.fullscreenAds[randomIndex];
        
        // Verificar se o anúncio é válido
        if (!ad || !ad.imageUrl) {
          this.log('Anúncio de tela cheia selecionado é inválido', 'warn');
          return false;
        }
        
        // Pausar o jogo se possível
        this.pauseGame();
        
        // Configurar o container
        domElements.fullscreenContent.style.backgroundImage = `url('${ad.imageUrl}')`;
        
        // Garantir que o container esteja visível
        domElements.fullscreenContainer.style.display = 'flex';
        domElements.fullscreenContainer.style.visibility = 'visible';
        domElements.fullscreenContainer.style.opacity = '1';
        
        // Garantir que o z-index seja alto o suficiente
        domElements.fullscreenContainer.style.zIndex = this.config.containerZIndex.fullscreen.toString();
        
        // Limpar event listeners existentes
        const newContent = domElements.fullscreenContent.cloneNode(true);
        domElements.fullscreenContent.parentNode.replaceChild(newContent, domElements.fullscreenContent);
        domElements.fullscreenContent = newContent;
        
        // Adicionar event listener para cliques
        domElements.fullscreenContent.addEventListener('click', () => {
          this.handleFullscreenAdClick(ad);
        });
        
        // Garantir que o container esteja no topo do DOM
        document.body.appendChild(domElements.fullscreenContainer);
        
        // Configurar fechamento automático
        const timer = setTimeout(() => {
          utils.removeTimer(timer);
          this.hideFullscreenAd();
        }, this.config.fullscreenDuration);
        
        utils.addTimer(timer);
        
        this.log(`Anúncio de tela cheia exibido: ${ad.id}`);
        
        // Registrar impressão
        this.recordImpression(ad.id, 'fullscreen');
        
        return true;
      } catch (error) {
        this.log(`Erro ao exibir anúncio de tela cheia: ${error.message}`, 'error');
        return false;
      }
    },
    
    // Esconder anúncio de tela cheia
    hideFullscreenAd: function() {
      try {
        if (!domElements.fullscreenContainer) {
          return;
        }
        
        domElements.fullscreenContainer.style.display = 'none';
        
        // Retomar o jogo
        this.resumeGame();
      } catch (error) {
        this.log(`Erro ao esconder anúncio de tela cheia: ${error.message}`, 'error');
      }
    },
    
    // Manipular clique em banner
    handleBannerClick: function(banner) {
      try {
        if (!banner || (!banner.targetUrl && !banner.linkUrl)) {
          return;
        }
        
        const url = banner.targetUrl || banner.linkUrl;
        
        // Registrar clique
        this.recordClick(banner.id, 'banner');
        
        // Abrir URL em nova aba
        window.open(url, '_blank');
      } catch (error) {
        this.log(`Erro ao manipular clique em banner: ${error.message}`, 'error');
      }
    },
    
    // Manipular clique em anúncio de tela cheia
    handleFullscreenAdClick: function(ad) {
      try {
        if (!ad || (!ad.targetUrl && !ad.linkUrl)) {
          return;
        }
        
        const url = ad.targetUrl || ad.linkUrl;
        
        // Registrar clique
        this.recordClick(ad.id, 'fullscreen');
        
        // Esconder o anúncio
        this.hideFullscreenAd();
        
        // Abrir URL em nova aba
        window.open(url, '_blank');
      } catch (error) {
        this.log(`Erro ao manipular clique em anúncio de tela cheia: ${error.message}`, 'error');
      }
    },
    
    // Registrar impressão
    recordImpression: function(adId, type) {
      try {
        if (!adId || !type) {
          return;
        }
        
        fetch(`${this.config.apiUrl}/api/impression`, {
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
              throw new Error(`Resposta do servidor não ok: ${response.status}`);
            }
            return response.json();
          })
          .then(() => {
            this.log(`Impressão registrada: ${adId} (${type})`);
          })
          .catch(error => {
            this.log(`Erro ao registrar impressão: ${error.message}`, 'error');
          });
      } catch (error) {
        this.log(`Erro ao iniciar registro de impressão: ${error.message}`, 'error');
      }
    },
    
    // Registrar clique
    recordClick: function(adId, type) {
      try {
        if (!adId || !type) {
          return;
        }
        
        fetch(`${this.config.apiUrl}/api/click`, {
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
              throw new Error(`Resposta do servidor não ok: ${response.status}`);
            }
            return response.json();
          })
          .then(() => {
            this.log(`Clique registrado: ${adId} (${type})`);
          })
          .catch(error => {
            this.log(`Erro ao registrar clique: ${error.message}`, 'error');
          });
      } catch (error) {
        this.log(`Erro ao iniciar registro de clique: ${error.message}`, 'error');
      }
    },
    
    // Manipular game over
    handleGameOver: function() {
      try {
        state.gameOverCount++;
        this.log(`Game over detectado (${state.gameOverCount}/${this.config.gameOverCountThreshold})`);
        
        if (state.gameOverCount >= this.config.gameOverCountThreshold) {
          state.gameOverCount = 0;
          
          // Mostrar anúncio de tela cheia
          const adShown = this.showFullscreenAd();
          
          if (!adShown) {
            this.log('Nenhum anúncio de tela cheia disponível', 'warn');
          }
        }
      } catch (error) {
        this.log(`Erro ao manipular game over: ${error.message}`, 'error');
      }
    },
    
    // Pausar o jogo
    pauseGame: function() {
      try {
        // Tentar pausar via Unity
        if (state.unityInstance) {
          if (typeof state.unityInstance.SendMessage === 'function') {
            state.unityInstance.SendMessage('GameManager', 'PauseGame');
          }
        }
        
        // Tentar pausar via função global
        if (typeof window.pauseGame === 'function') {
          window.pauseGame();
        }
      } catch (error) {
        this.log(`Erro ao pausar jogo: ${error.message}`, 'error');
      }
    },
    
    // Retomar o jogo
    resumeGame: function() {
      try {
        // Tentar retomar via Unity
        if (state.unityInstance) {
          if (typeof state.unityInstance.SendMessage === 'function') {
            state.unityInstance.SendMessage('GameManager', 'ResumeGame');
          }
        }
        
        // Tentar retomar via função global
        if (typeof window.resumeGame === 'function') {
          window.resumeGame();
        }
      } catch (error) {
        this.log(`Erro ao retomar jogo: ${error.message}`, 'error');
      }
    },
    
    // Função de log
    log: function(message, level = 'info') {
      if (!this.config.debug) {
        return;
      }
      
      const timestamp = new Date().toLocaleTimeString();
      const prefix = `[AdSystem ${timestamp}]`;
      
      switch (level) {
        case 'error':
          console.error(`${prefix} ❌ ${message}`);
          break;
        case 'warn':
          console.warn(`${prefix} ⚠️ ${message}`);
          break;
        default:
          console.log(`${prefix} ℹ️ ${message}`);
      }
    },
    
    // Diagnóstico do sistema
    diagnose: function() {
      this.log('Executando diagnóstico do sistema de anúncios...');
      
      const report = {
        initialized: state.initialized,
        banners: {
          count: state.banners.length,
          currentIndex: state.currentBannerIndex,
          rotationActive: !!state.bannerRotationTimer
        },
        fullscreenAds: {
          count: state.fullscreenAds.length
        },
        gameState: {
          isGameScreen: state.isGameScreen,
          gameOverCount: state.gameOverCount,
          unityInstanceDetected: !!state.unityInstance
        },
        domElements: {
          bannerContainer: !!domElements.bannerContainer,
          fullscreenContainer: !!domElements.fullscreenContainer,
          gameScreenIndicator: !!domElements.gameScreenIndicator
        },
        config: { ...this.config }
      };
      
      // Verificar visibilidade do banner
      if (domElements.bannerContainer) {
        const bannerStyle = window.getComputedStyle(domElements.bannerContainer);
        report.bannerVisibility = {
          display: bannerStyle.display,
          visibility: bannerStyle.visibility,
          opacity: bannerStyle.opacity,
          zIndex: bannerStyle.zIndex,
          position: bannerStyle.position,
          width: bannerStyle.width,
          height: bannerStyle.height,
          top: bannerStyle.top,
          left: bannerStyle.left,
          inDOM: document.body.contains(domElements.bannerContainer)
        };
      }
      
      console.log('Diagnóstico do sistema de anúncios:', report);
      return report;
    }
  };
  
  // Inicialização automática quando o documento estiver pronto
  if (document.readyState === 'complete' || document.readyState === 'interactive') {
    publicAPI.log('Documento já carregado, iniciando com atraso...');
    setTimeout(() => {
      publicAPI.init();
    }, 500);
  } else {
    document.addEventListener('DOMContentLoaded', () => {
      publicAPI.log('Documento carregado, iniciando...');
      publicAPI.init();
    });
  }
  
  return publicAPI;
})();

// Expor funções globais para integração com o Unity
window.gameOver = function() {
  adSystem.handleGameOver();
};

window.pauseGame = function() {
  // Implementação específica do jogo, se necessário
};

window.resumeGame = function() {
  // Implementação específica do jogo, se necessário
};
