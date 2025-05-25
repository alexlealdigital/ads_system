/**
 * Sistema de Anúncios para Jogos Unity WebGL
 * Versão: 2.0.0
 * 
 * Este script gerencia a exibição de banners (360x47px) e anúncios de tela cheia (360x640px)
 * em jogos Unity WebGL, com suporte a rastreamento de impressões e cliques.
 * 
 * Corrigido para garantir visibilidade dentro da área do jogo e compatibilidade com o backend.
 */

// Namespace isolado para evitar conflitos
const AdSystem = (function() {
    // Configurações
    const config = {
        apiBaseUrl: 'https://ads-system-backend.onrender.com',
        bannerEndpoint: '/api/banners',
        fullscreenEndpoint: '/api/fullscreen',
        impressionEndpoint: '/api/impression',
        clickEndpoint: '/api/click',
        bannerRotationInterval: 5000, // 5 segundos
        retryInterval: 10000, // 10 segundos
        debug: true
    };

    // Estado interno
    const state = {
        banners: [],
        fullscreenAds: [],
        currentBannerIndex: 0,
        bannerContainer: null,
        fullscreenContainer: null,
        bannerRotationTimer: null,
        retryTimer: null,
        unityInstance: null,
        unityCanvas: null,
        initialized: false,
        loading: false
    };

    // Sistema de logs
    const log = {
        info: function(message) {
            if (config.debug) {
                console.log(`[AdSystem ${new Date().toLocaleTimeString()}] ℹ️ ${message}`);
            }
        },
        warn: function(message) {
            if (config.debug) {
                console.log(`[AdSystem ${new Date().toLocaleTimeString()}] ⚠️ ${message}`);
            }
        },
        error: function(message) {
            if (config.debug) {
                console.log(`[AdSystem ${new Date().toLocaleTimeString()}] ❌ ${message}`);
            }
        }
    };

    // Utilitários
    const utils = {
        // Cria um elemento DOM com atributos
        createElement: function(tag, attributes = {}, styles = {}) {
            const element = document.createElement(tag);
            
            // Aplicar atributos
            Object.keys(attributes).forEach(key => {
                element.setAttribute(key, attributes[key]);
            });
            
            // Aplicar estilos
            Object.keys(styles).forEach(key => {
                element.style[key] = styles[key];
            });
            
            return element;
        },
        
        // Encontra o canvas do Unity
        findUnityCanvas: function() {
            // Tentar encontrar pelo ID padrão
            let canvas = document.getElementById('unity-canvas');
            
            // Se não encontrar pelo ID, procurar por qualquer canvas
            if (!canvas) {
                const canvases = document.getElementsByTagName('canvas');
                if (canvases.length > 0) {
                    canvas = canvases[0];
                }
            }
            
            // Se ainda não encontrou, procurar pelo container do Unity
            if (!canvas) {
                const unityContainer = document.getElementById('unity-container');
                if (unityContainer) {
                    const canvases = unityContainer.getElementsByTagName('canvas');
                    if (canvases.length > 0) {
                        canvas = canvases[0];
                    }
                }
            }
            
            return canvas;
        },
        
        // Faz uma requisição fetch com tratamento de erros
        fetchWithTimeout: async function(url, options = {}, timeout = 5000) {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), timeout);
            
            options.signal = controller.signal;
            
            try {
                const response = await fetch(url, options);
                clearTimeout(timeoutId);
                
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                
                return await response.json();
            } catch (error) {
                clearTimeout(timeoutId);
                throw error;
            }
        }
    };

    // Funções principais
    const api = {
        // Inicializa o sistema de anúncios
        init: function(unityInstance = null) {
            if (state.initialized) {
                log.warn('Sistema de anúncios já inicializado');
                return;
            }
            
            log.info('Inicializando sistema de anúncios...');
            
            // Armazenar referência ao Unity
            state.unityInstance = unityInstance;
            
            // Encontrar o canvas do Unity
            state.unityCanvas = utils.findUnityCanvas();
            if (!state.unityCanvas) {
                log.warn('Canvas do Unity não encontrado. Tentando novamente em 1 segundo...');
                setTimeout(() => api.init(unityInstance), 1000);
                return;
            }
            
            log.info('Canvas do Unity encontrado');
            
            // Criar containers para os anúncios
            api.createAdContainers();
            
            // Carregar anúncios
            api.loadBanners();
            api.loadFullscreenAds();
            
            state.initialized = true;
        },
        
        // Cria os containers para os anúncios
        createAdContainers: function() {
            // Criar container para banners
            if (!state.bannerContainer) {
                state.bannerContainer = utils.createElement('div', {
                    id: 'ad-banner-container'
                }, {
                    position: 'absolute',
                    top: '0',
                    left: '50%',
                    transform: 'translateX(-50%)',
                    width: '360px',
                    height: '47px',
                    zIndex: '9999',
                    display: 'none',
                    overflow: 'hidden',
                    backgroundColor: 'transparent'
                });
                
                // Anexar ao DOM
                if (state.unityCanvas && state.unityCanvas.parentElement) {
                    state.unityCanvas.parentElement.appendChild(state.bannerContainer);
                    log.info('Container de banner criado e anexado ao DOM');
                } else {
                    document.body.appendChild(state.bannerContainer);
                    log.warn('Container de banner anexado ao body (canvas parent não encontrado)');
                }
            }
            
            // Criar container para anúncios de tela cheia
            if (!state.fullscreenContainer) {
                state.fullscreenContainer = utils.createElement('div', {
                    id: 'ad-fullscreen-container'
                }, {
                    position: 'absolute',
                    top: '0',
                    left: '0',
                    width: '100%',
                    height: '100%',
                    zIndex: '10000',
                    display: 'none',
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    justifyContent: 'center',
                    alignItems: 'center'
                });
                
                // Anexar ao DOM
                if (state.unityCanvas && state.unityCanvas.parentElement) {
                    state.unityCanvas.parentElement.appendChild(state.fullscreenContainer);
                    log.info('Container de anúncio de tela cheia criado e anexado ao DOM');
                } else {
                    document.body.appendChild(state.fullscreenContainer);
                    log.warn('Container de anúncio de tela cheia anexado ao body (canvas parent não encontrado)');
                }
            }
        },
        
        // Carrega os banners do servidor
        loadBanners: function() {
            if (state.loading) return;
            state.loading = true;
            
            log.info('Carregando banners...');
            
            fetch(`${config.apiBaseUrl}${config.bannerEndpoint}`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Resposta não ok');
                    }
                    return response.json();
                })
                .then(data => {
                    state.banners = data;
                    log.info(`${state.banners.length} banners carregados`);
                    
                    if (state.banners.length > 0) {
                        api.startBannerRotation();
                    }
                    
                    state.loading = false;
                })
                .catch(error => {
                    log.error(`Erro ao carregar banners: ${error.message}`);
                    state.loading = false;
                    
                    // Tentar novamente após um intervalo
                    if (!state.retryTimer) {
                        state.retryTimer = setTimeout(() => {
                            state.retryTimer = null;
                            api.loadBanners();
                        }, config.retryInterval);
                    }
                });
        },
        
        // Carrega os anúncios de tela cheia do servidor
        loadFullscreenAds: function() {
            log.info('Carregando anúncios de tela cheia...');
            
            fetch(`${config.apiBaseUrl}${config.fullscreenEndpoint}`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Resposta não ok');
                    }
                    return response.json();
                })
                .then(data => {
                    state.fullscreenAds = data;
                    log.info(`${state.fullscreenAds.length} anúncios de tela cheia carregados`);
                })
                .catch(error => {
                    log.error(`Erro ao carregar anúncios de tela cheia: ${error.message}`);
                });
        },
        
        // Inicia a rotação de banners
        startBannerRotation: function() {
            if (state.bannerRotationTimer) {
                clearInterval(state.bannerRotationTimer);
            }
            
            // Mostrar o primeiro banner
            api.showNextBanner();
            
            // Iniciar rotação
            state.bannerRotationTimer = setInterval(() => {
                api.showNextBanner();
            }, config.bannerRotationInterval);
            
            log.info('Rotação de banners iniciada');
        },
        
        // Mostra o próximo banner na rotação
        showNextBanner: function() {
            if (state.banners.length === 0) {
                log.warn('Nenhum banner disponível para exibição');
                return;
            }
            
            // Avançar para o próximo banner
            state.currentBannerIndex = (state.currentBannerIndex + 1) % state.banners.length;
            const banner = state.banners[state.currentBannerIndex];
            
            // Mostrar o banner
            api.showBanner(banner);
        },
        
        // Mostra um banner específico
        showBanner: function(banner) {
            if (!state.bannerContainer) {
                log.error('Container de banner não inicializado');
                return;
            }
            
            // Limpar container
            state.bannerContainer.innerHTML = '';
            
            // Criar elemento de banner
            const bannerElement = utils.createElement('div', {
                class: 'ad-banner',
                'data-id': banner.id
            }, {
                width: '100%',
                height: '100%',
                cursor: 'pointer',
                position: 'relative'
            });
            
            // Criar imagem do banner
            const bannerImage = utils.createElement('img', {
                src: banner.imageUrl,
                alt: banner.title
            }, {
                width: '100%',
                height: '100%',
                objectFit: 'cover'
            });
            
            // Adicionar evento de clique
            bannerElement.addEventListener('click', () => {
                api.handleBannerClick(banner);
            });
            
            // Montar banner
            bannerElement.appendChild(bannerImage);
            state.bannerContainer.appendChild(bannerElement);
            
            // Exibir container
            state.bannerContainer.style.display = 'block';
            
            // Registrar impressão
            api.recordImpression(banner.id, 'banner');
            
            log.info(`Banner exibido: ${banner.title} (ID: ${banner.id})`);
        },
        
        // Mostra um anúncio de tela cheia
        showFullscreenAd: function() {
            if (state.fullscreenAds.length === 0) {
                log.warn('Nenhum anúncio de tela cheia disponível');
                return false;
            }
            
            // Selecionar um anúncio aleatório
            const randomIndex = Math.floor(Math.random() * state.fullscreenAds.length);
            const ad = state.fullscreenAds[randomIndex];
            
            if (!state.fullscreenContainer) {
                log.error('Container de anúncio de tela cheia não inicializado');
                return false;
            }
            
            // Limpar container
            state.fullscreenContainer.innerHTML = '';
            
            // Criar wrapper para centralizar o anúncio
            const adWrapper = utils.createElement('div', {
                class: 'ad-fullscreen-wrapper'
            }, {
                position: 'relative',
                width: '360px',
                height: '640px',
                margin: '0 auto',
                backgroundColor: '#fff',
                boxShadow: '0 0 20px rgba(0, 0, 0, 0.5)'
            });
            
            // Criar elemento de anúncio
            const adElement = utils.createElement('div', {
                class: 'ad-fullscreen',
                'data-id': ad.id
            }, {
                width: '100%',
                height: '100%',
                cursor: 'pointer',
                position: 'relative'
            });
            
            // Criar imagem do anúncio
            const adImage = utils.createElement('img', {
                src: ad.imageUrl,
                alt: ad.title
            }, {
                width: '100%',
                height: '100%',
                objectFit: 'cover'
            });
            
            // Criar botão de fechar
            const closeButton = utils.createElement('button', {
                class: 'ad-close-button',
                title: 'Fechar'
            }, {
                position: 'absolute',
                top: '10px',
                right: '10px',
                width: '30px',
                height: '30px',
                borderRadius: '50%',
                backgroundColor: 'rgba(0, 0, 0, 0.5)',
                color: '#fff',
                border: 'none',
                fontSize: '20px',
                cursor: 'pointer',
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                zIndex: '1'
            });
            closeButton.innerHTML = '&times;';
            
            // Adicionar evento de clique no anúncio
            adElement.addEventListener('click', (e) => {
                // Ignorar clique se for no botão de fechar
                if (e.target !== closeButton && !closeButton.contains(e.target)) {
                    api.handleFullscreenAdClick(ad);
                }
            });
            
            // Adicionar evento de clique no botão de fechar
            closeButton.addEventListener('click', (e) => {
                e.stopPropagation();
                api.hideFullscreenAd();
            });
            
            // Montar anúncio
            adElement.appendChild(adImage);
            adElement.appendChild(closeButton);
            adWrapper.appendChild(adElement);
            state.fullscreenContainer.appendChild(adWrapper);
            
            // Exibir container
            state.fullscreenContainer.style.display = 'flex';
            
            // Registrar impressão
            api.recordImpression(ad.id, 'fullscreen');
            
            log.info(`Anúncio de tela cheia exibido: ${ad.title} (ID: ${ad.id})`);
            
            return true;
        },
        
        // Esconde o anúncio de tela cheia
        hideFullscreenAd: function() {
            if (state.fullscreenContainer) {
                state.fullscreenContainer.style.display = 'none';
                log.info('Anúncio de tela cheia fechado');
            }
        },
        
        // Trata o clique em um banner
        handleBannerClick: function(banner) {
            log.info(`Banner clicado: ${banner.title} (ID: ${banner.id})`);
            
            // Registrar clique
            api.recordClick(banner.id, 'banner');
            
            // Abrir URL de destino
            const targetUrl = banner.targetUrl || banner.linkUrl;
            if (targetUrl) {
                window.open(targetUrl, '_blank');
            }
        },
        
        // Trata o clique em um anúncio de tela cheia
        handleFullscreenAdClick: function(ad) {
            log.info(`Anúncio de tela cheia clicado: ${ad.title} (ID: ${ad.id})`);
            
            // Registrar clique
            api.recordClick(ad.id, 'fullscreen');
            
            // Abrir URL de destino
            const targetUrl = ad.targetUrl || ad.linkUrl;
            if (targetUrl) {
                window.open(targetUrl, '_blank');
            }
            
            // Fechar anúncio
            api.hideFullscreenAd();
        },
        
        // Registra uma impressão
        recordImpression: function(adId, adType) {
            fetch(`${config.apiBaseUrl}${config.impressionEndpoint}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    adId: adId,
                    type: adType
                })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Resposta não ok');
                }
                return response.json();
            })
            .then(data => {
                log.info(`Impressão registrada: ${adType} ${adId}`);
            })
            .catch(error => {
                log.error(`Erro ao registrar impressão: ${error.message}`);
            });
        },
        
        // Registra um clique
        recordClick: function(adId, adType) {
            fetch(`${config.apiBaseUrl}${config.clickEndpoint}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    adId: adId,
                    type: adType
                })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Resposta não ok');
                }
                return response.json();
            })
            .then(data => {
                log.info(`Clique registrado: ${adType} ${adId}`);
            })
            .catch(error => {
                log.error(`Erro ao registrar clique: ${error.message}`);
            });
        },
        
        // Mostra um anúncio de tela cheia após game over
        showGameOverAd: function() {
            return api.showFullscreenAd();
        },
        
        // Diagnóstico do sistema
        diagnose: function() {
            log.info('--- Diagnóstico do Sistema de Anúncios ---');
            log.info(`Inicializado: ${state.initialized}`);
            log.info(`Banners carregados: ${state.banners.length}`);
            log.info(`Anúncios de tela cheia carregados: ${state.fullscreenAds.length}`);
            log.info(`Container de banner existe: ${!!state.bannerContainer}`);
            log.info(`Container de anúncio de tela cheia existe: ${!!state.fullscreenContainer}`);
            log.info(`Canvas do Unity encontrado: ${!!state.unityCanvas}`);
            
            if (state.bannerContainer) {
                log.info(`Visibilidade do container de banner: ${state.bannerContainer.style.display}`);
                log.info(`Z-index do container de banner: ${state.bannerContainer.style.zIndex}`);
                log.info(`Posição do container de banner: top=${state.bannerContainer.style.top}, left=${state.bannerContainer.style.left}`);
            }
            
            return {
                initialized: state.initialized,
                bannersLoaded: state.banners.length,
                fullscreenAdsLoaded: state.fullscreenAds.length,
                bannerContainerExists: !!state.bannerContainer,
                fullscreenContainerExists: !!state.fullscreenContainer,
                unityCanvasFound: !!state.unityCanvas
            };
        },
        
        // Verifica e corrige a visibilidade dos containers
        checkVisibility: function() {
            if (!state.initialized) return;
            
            if (state.bannerContainer) {
                // Garantir que o container de banner esteja visível
                if (state.bannerContainer.style.display === 'none' && state.banners.length > 0) {
                    state.bannerContainer.style.display = 'block';
                    log.info('Visibilidade do container de banner corrigida');
                }
                
                // Garantir que o z-index seja alto o suficiente
                if (parseInt(state.bannerContainer.style.zIndex) < 9999) {
                    state.bannerContainer.style.zIndex = '9999';
                    log.info('Z-index do container de banner corrigido');
                }
            }
        }
    };

    // Iniciar verificação periódica de visibilidade
    setInterval(() => {
        api.checkVisibility();
    }, 5000);

    // Inicializar quando o documento estiver pronto
    if (document.readyState === 'complete' || document.readyState === 'interactive') {
        setTimeout(() => api.init(), 1000);
    } else {
        document.addEventListener('DOMContentLoaded', () => {
            setTimeout(() => api.init(), 1000);
        });
    }

    // Interface pública
    return {
        init: api.init,
        showBanner: api.showBanner,
        showFullscreenAd: api.showFullscreenAd,
        hideFullscreenAd: api.hideFullscreenAd,
        showGameOverAd: api.showGameOverAd,
        diagnose: api.diagnose
    };
})();

// Compatibilidade com Unity
function showBanner() {
    return AdSystem.showBanner();
}

function showFullscreenAd() {
    return AdSystem.showFullscreenAd();
}

function hideFullscreenAd() {
    return AdSystem.hideFullscreenAd();
}

function showGameOverAd() {
    return AdSystem.showGameOverAd();
}

// Inicializar quando o Unity estiver pronto
window.addEventListener('unityReady', function(e) {
    AdSystem.init(e.detail.unityInstance);
});

// Log de inicialização
console.log('[AdSystem] Sistema de anúncios carregado e pronto para inicialização');
