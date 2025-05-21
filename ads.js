// ads_final.js (ou ads.js)

(function() { // Usamos uma IIFE para encapsular e evitar poluir o escopo global desnecessariamente
    // Verifica se a variável adSystem já existe para evitar redeclaração
    if (typeof window.adSystem !== 'undefined') {
        console.warn('window.adSystem já está definido. Pulando a redeclaração.');
        return; // Sai se já estiver definido
    }

    const adSystem = (function() {
        // Objeto para armazenar referências aos elementos do DOM dos anúncios
        let domElements = {
            bannerContainer: null,
            fullscreenContainer: null
        };

        // Estado interno do sistema de anúncios
        let systemState = {
            initialized: false,
            adsData: null, // Armazenará os dados dos anúncios carregados
            currentBannerIndex: 0,
            gameOverCounter: 0,
            isShowingFullscreen: false,
            bannerRotationTimer: null
        };

        // Configurações padrão
        const defaultConfig = {
            apiUrl: 'https://ads-system-backend.onrender.com',
            bannerRotationInterval: 7000, // 7 segundos
            fullscreenDuration: 5000,    // 5 segundos
            gameOverCountThreshold: 5,   // Mostrar fullscreen a cada 5 game overs
            debug: true,                 // Ativa logs de depuração
            retryAttempts: 3,            // Tentativas para buscar anúncios
            retryDelay: 3000,            // Atraso entre as tentativas
            fallbackImageUrl: 'https://via.placeholder.com/1080x140?text=Anuncio+Padrao',
            fallbackTargetUrl: 'https://alexlealdigital.github.io',
            containerZIndex: {
                banner: 2147483647, // Valor máximo garantido
                fullscreen: 2147483647
            }
        };

        let currentConfig = {}; // Configuração final após a inicialização

        /**
         * Log de depuração condicional.
         * @param {...any} args - Argumentos a serem logados.
         */
        function debugLog(...args) {
            if (currentConfig.debug) {
                console.log('[AdSystem Debug]', ...args);
            }
        }

        /**
         * Cria e anexa um elemento de contêiner de anúncio ao DOM.
         * @param {string} id - ID do contêiner.
         * @param {number} zIndex - Z-index do contêiner.
         * @returns {HTMLElement} O elemento do contêiner criado.
         */
        function createAdContainer(id, zIndex) {
            let container = document.getElementById(id);
            if (!container) {
                container = document.createElement('div');
                container.id = id;
                container.style.cssText = `
                    position: fixed;
                    left: 0;
                    width: 100%;
                    background-color: rgba(0, 0, 0, 0.8); /* Fundo semi-transparente para destaque */
                    color: white;
                    text-align: center;
                    display: none; /* Inicia oculto */
                    z-index: ${zIndex};
                    box-sizing: border-box; /* Garante que padding e border não aumentem o tamanho */
                `;
                document.body.appendChild(container);
            }
            return container;
        }

        /**
         * Inicializa os contêineres de banner e fullscreen.
         */
        function setupAdContainers() {
            domElements.bannerContainer = createAdContainer('ad-banner-container', currentConfig.containerZIndex.banner);
            domElements.bannerContainer.style.height = '140px'; // Altura padrão para banner
            domElements.bannerContainer.style.top = '0'; // Posição no topo

            domElements.fullscreenContainer = createAdContainer('ad-fullscreen-container', currentConfig.containerZIndex.fullscreen);
            domElements.fullscreenContainer.style.top = '0';
            domElements.fullscreenContainer.style.left = '0';
            domElements.fullscreenContainer.style.width = '100%';
            domElements.fullscreenContainer.style.height = '100%';
            domElements.fullscreenContainer.style.display = 'flex'; // Usar flexbox para centralizar
            domElements.fullscreenContainer.style.justifyContent = 'center';
            domElements.fullscreenContainer.style.alignItems = 'center';
            domElements.fullscreenContainer.style.backgroundColor = 'black'; // Fundo preto para fullscreen
        }

        /**
         * Ajusta o z-index do canvas do Unity para garantir que os anúncios fiquem por cima.
         */
        const safeUnityCanvasZIndex = () => {
            if (typeof window.unityInstance !== 'undefined' &&
                window.unityInstance &&
                window.unityInstance.Module &&
                window.unityInstance.Module.canvas) {
                debugLog('Ajustando z-index do canvas do Unity para 0.');
                window.unityInstance.Module.canvas.style.zIndex = '0';
            } else {
                debugLog('Unity instance ou canvas não encontrado para ajustar z-index.');
            }
        };

        /**
         * Busca os dados dos anúncios da API.
         * Implementa lógica de retry.
         * @param {number} attempt - Tentativa atual.
         * @returns {Promise<Array>} Promessa que resolve com os dados dos anúncios.
         */
        async function fetchAdsData(attempt = 1) {
            debugLog(`Tentando buscar dados de anúncios (Tentativa ${attempt}/${currentConfig.retryAttempts})...`);
            try {
                const response = await fetch(`${currentConfig.apiUrl}/ads`);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const data = await response.json();
                systemState.adsData = data;
                debugLog('Dados de anúncios carregados:', data);
                return data;
            } catch (error) {
                console.error(`Erro ao buscar dados de anúncios na tentativa ${attempt}:`, error);
                if (attempt < currentConfig.retryAttempts) {
                    await new Promise(resolve => setTimeout(resolve, currentConfig.retryDelay));
                    return fetchAdsData(attempt + 1); // Tenta novamente
                } else {
                    console.error('Falha ao buscar dados de anúncios após todas as tentativas. Usando fallback.');
                    // Usar um anúncio de fallback se a API falhar
                    systemState.adsData = [{
                        type: 'banner',
                        imageUrl: currentConfig.fallbackImageUrl,
                        targetUrl: currentConfig.fallbackTargetUrl
                    }, {
                        type: 'fullscreen', // Pode ter um fallback fullscreen também
                        imageUrl: 'https://via.placeholder.com/1080x1920?text=Anuncio+Tela+Cheia+Padrao',
                        targetUrl: currentConfig.fallbackTargetUrl
                    }];
                    return systemState.adsData;
                }
            }
        }

        /**
         * Exibe um anúncio banner.
         */
        function showBanner() {
            if (!domElements.bannerContainer) {
                debugLog('Contêiner do banner não está pronto.');
                return;
            }

            if (!systemState.adsData || systemState.adsData.length === 0) {
                debugLog('Nenhum dado de anúncio disponível para banner. Exibindo fallback.');
                // Usar um banner de fallback se não houver dados
                const fallbackAd = {
                    imageUrl: currentConfig.fallbackImageUrl,
                    targetUrl: currentConfig.fallbackTargetUrl
                };
                displayAdInContainer(domElements.bannerContainer, fallbackAd, 'banner');
                return;
            }

            // Filtrar apenas anúncios do tipo banner
            const banners = systemState.adsData.filter(ad => ad.type === 'banner');

            if (banners.length === 0) {
                debugLog('Nenhum anúncio tipo banner encontrado. Exibindo fallback.');
                const fallbackAd = {
                    imageUrl: currentConfig.fallbackImageUrl,
                    targetUrl: currentConfig.fallbackTargetUrl
                };
                displayAdInContainer(domElements.bannerContainer, fallbackAd, 'banner');
                return;
            }

            // Exibir o banner atual e programar o próximo
            const adToShow = banners[systemState.currentBannerIndex];
            displayAdInContainer(domElements.bannerContainer, adToShow, 'banner');

            // Preparar para o próximo banner
            systemState.currentBannerIndex = (systemState.currentBannerIndex + 1) % banners.length;

            // Limpar timer anterior e iniciar novo para rotação
            if (systemState.bannerRotationTimer) {
                clearInterval(systemState.bannerRotationTimer);
            }
            systemState.bannerRotationTimer = setInterval(() => {
                debugLog('Rotacionando banner...');
                showBanner(); // Chama a si mesmo para rotacionar
            }, currentConfig.bannerRotationInterval);

            domElements.bannerContainer.style.display = 'block';
            debugLog('Banner visível.');
        }

        /**
         * Oculta o anúncio banner.
         */
        function hideBanner() {
            if (domElements.bannerContainer) {
                domElements.bannerContainer.style.display = 'none';
                if (systemState.bannerRotationTimer) {
                    clearInterval(systemState.bannerRotationTimer);
                    systemState.bannerRotationTimer = null;
                }
                debugLog('Banner oculto.');
            }
        }

        /**
         * Exibe um anúncio fullscreen.
         * @param {object} adData - Dados do anúncio a ser exibido.
         */
        async function showFullscreenAd(adData) {
            if (!domElements.fullscreenContainer || systemState.isShowingFullscreen) {
                debugLog('Contêiner fullscreen não está pronto ou já está exibindo um anúncio fullscreen.');
                return;
            }

            systemState.isShowingFullscreen = true;
            publicAPI.pauseGame(); // Pausa o jogo (chamada para o Unity)

            // Exibir o anúncio fullscreen
            await displayAdInContainer(domElements.fullscreenContainer, adData, 'fullscreen');
            domElements.fullscreenContainer.style.display = 'flex'; // Usar flex para centralização

            debugLog('Anúncio fullscreen visível. Ocultando em', currentConfig.fullscreenDuration / 1000, 'segundos.');

            // Ocultar após a duração e resumir o jogo
            setTimeout(() => {
                hideFullscreenAd();
                publicAPI.resumeGame(); // Resumir o jogo (chamada para o Unity)
            }, currentConfig.fullscreenDuration);
        }

        /**
         * Oculta o anúncio fullscreen.
         */
        function hideFullscreenAd() {
            if (domElements.fullscreenContainer) {
                domElements.fullscreenContainer.style.display = 'none';
                systemState.isShowingFullscreen = false;
                debugLog('Anúncio fullscreen oculto.');
            }
        }

        /**
         * Exibe um anúncio (banner ou fullscreen) em um contêiner específico.
         * @param {HTMLElement} container - O elemento DOM onde o anúncio será exibido.
         * @param {object} ad - Objeto de dados do anúncio.
         * @param {string} type - 'banner' ou 'fullscreen'.
         */
        function displayAdInContainer(container, ad, type) {
            container.innerHTML = ''; // Limpa o conteúdo anterior

            const link = document.createElement('a');
            link.href = ad.targetUrl || currentConfig.fallbackTargetUrl;
            link.target = '_blank'; // Abre em nova aba
            link.style.display = 'flex';
            link.style.justifyContent = 'center';
            link.style.alignItems = 'center';
            link.style.width = '100%';
            link.style.height = '100%';

            const img = document.createElement('img');
            img.src = ad.imageUrl || (type === 'banner' ? currentConfig.fallbackImageUrl : 'https://via.placeholder.com/1080x1920?text=Anuncio+Tela+Cheia+Padrao');
            img.style.maxWidth = '100%';
            img.style.maxHeight = '100%';
            img.style.objectFit = 'contain'; // Garante que a imagem se ajuste

            link.appendChild(img);
            container.appendChild(link);

            // Adicionar um botão de fechar para fullscreen (opcional, mas boa prática)
            if (type === 'fullscreen') {
                const closeButton = document.createElement('button');
                closeButton.textContent = 'X';
                closeButton.style.cssText = `
                    position: absolute;
                    top: 10px;
                    right: 10px;
                    background-color: rgba(255, 255, 255, 0.7);
                    border: none;
                    border-radius: 50%;
                    width: 30px;
                    height: 30px;
                    font-size: 18px;
                    cursor: pointer;
                    z-index: ${currentConfig.containerZIndex.fullscreen + 1}; /* Acima do anúncio */
                `;
                closeButton.onclick = (e) => {
                    e.stopPropagation(); // Evita que o clique vá para o link do anúncio
                    hideFullscreenAd();
                    publicAPI.resumeGame();
                };
                container.appendChild(closeButton);
            }
        }

        /**
         * Lida com o evento de Game Over do jogo.
         */
        function handleGameOver() {
            systemState.gameOverCounter++;
            debugLog('Game Over! Contador:', systemState.gameOverCounter);

            if (systemState.gameOverCounter >= currentConfig.gameOverCountThreshold) {
                systemState.gameOverCounter = 0; // Resetar contador
                const fullscreenAds = systemState.adsData.filter(ad => ad.type === 'fullscreen');
                if (fullscreenAds.length > 0) {
                    // Selecionar um anúncio fullscreen aleatoriamente
                    const adToShow = fullscreenAds[Math.floor(Math.random() * fullscreenAds.length)];
                    showFullscreenAd(adToShow);
                } else {
                    debugLog('Nenhum anúncio fullscreen disponível.');
                }
            }
        }

        const publicAPI = {
            /**
             * Inicializa o sistema de anúncios.
             * @param {object} customConfig - Configurações opcionais para sobrescrever as padrão.
             */
            init: async function(customConfig = {}) {
                if (systemState.initialized) {
                    debugLog('AdSystem já inicializado.');
                    return;
                }

                currentConfig = { ...defaultConfig, ...customConfig };
                debugLog('Inicializando AdSystem com configuração:', currentConfig);

                setupAdContainers(); // Cria os contêineres DOM
                safeUnityCanvasZIndex(); // Ajusta o z-index do canvas do Unity

                await fetchAdsData(); // Busca os dados dos anúncios

                systemState.initialized = true;
                debugLog('AdSystem inicialização completa.');

                // Dispara evento global para sinalizar que o sistema está pronto
                document.dispatchEvent(new CustomEvent('adSystemReady'));
            },

            showBanner: function() {
                if (!systemState.initialized) {
                    debugLog('AdSystem não inicializado, não pode mostrar banner.');
                    return;
                }
                showBanner();
            },

            hideBanner: function() {
                if (!systemState.initialized) {
                    debugLog('AdSystem não inicializado, não pode esconder banner.');
                    return;
                }
                hideBanner();
            },

            handleGameOver: function() {
                if (!systemState.initialized) {
                    debugLog('AdSystem não inicializado, não pode lidar com game over.');
                    return;
                }
                handleGameOver();
            },

            // Métodos que o AdSystem chama para o Unity (Unity chama setGameScreen, gameOver etc. e o AdSystem chama pauseGame/resumeGame)
            pauseGame: function() {
                debugLog('Chamando Unity para pausar o jogo...');
                if (window.unityInstance && typeof window.unityInstance.SendMessage === 'function') {
                    window.unityInstance.SendMessage('GameManager', 'PauseGame');
                } else {
                    console.warn('Unity instance não disponível para pausar o jogo.');
                }
            },

            resumeGame: function() {
                debugLog('Chamando Unity para resumir o jogo...');
                if (window.unityInstance && typeof window.unityInstance.SendMessage === 'function') {
                    window.unityInstance.SendMessage('GameManager', 'ResumeGame');
                } else {
                    console.warn('Unity instance não disponível para resumir o jogo.');
                }
            },

            // Para depuração:
            getSystemState: function() {
                return { ...systemState, config: currentConfig };
            }
        };

        return publicAPI;
    })();

    // Expõe o adSystem globalmente
    window.adSystem = adSystem;

    // Listener para o DOMContentLoaded para iniciar o AdSystem
    // Este script será injetado dinamicamente, então ele precisa saber quando o DOM está pronto.
    // Ou, se for carregado via <script defer> no head, o DOMContentLoaded já pode ter disparado.
    // O ideal é que este script seja carregado *antes* do script principal do Unity para garantir que window.adSystem esteja definido.
    // A inicialização (adSystem.init()) será disparada pelo `index.html` de forma robusta.

})();