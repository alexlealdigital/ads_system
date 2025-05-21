/**
 * Sistema de Anúncios para Jogos Unity WebGL - Versão Corrigida
 * Modificações focadas na correção do banner invisível
 */

// Configuração do sistema de anúncios - Namespace isolado para evitar conflitos
const adSystem = (function() {
  // Adicionado: Solução para conflito com WebGL
  if (typeof window.unityInstance !== 'undefined') {
    window.unityInstance.Module.canvas.style.zIndex = '0';
  }

  // Configurações padrão (com ajustes)
  const defaultConfig = {
    apiUrl: 'https://ads-system-backend.onrender.com',
    bannerRotationInterval: 7000,
    fullscreenDuration: 5000,
    gameOverCountThreshold: 5,
    debug: true,
    retryAttempts: 3,
    retryDelay: 3000,
    fallbackImageUrl: 'https://via.placeholder.com/1080x140', // Adicionado fallback padrão
    fallbackTargetUrl: 'https://alexlealdigital.github.io',
    containerZIndex: {
      banner: 2147483647, // Valor máximo modificado
      fullscreen: 2147483647
    }
  };
  
  // [O restante das variáveis de estado permanece igual...]
  
  // API pública
  const publicAPI = {
    // [Outras funções permanecem iguais até createBannerContainer...]

    // Função createBannerContainer MODIFICADA
    createBannerContainer: function() {
      try {
        const existingContainer = document.getElementById('ad-banner-container');
        if (existingContainer) {
          domElements.bannerContainer = existingContainer;
          this.log('Container de banner já existe, reutilizando');
          return;
        }
        
        // Container modificado para fixed position e estilos de debug
        const container = utils.createElement('div', 'ad-banner-container', {
          position: 'fixed', // Alterado de absolute para fixed
          bottom: '0', // Posiciona na parte inferior
          left: '0',
          width: '100%',
          height: '140px',
          zIndex: this.config.containerZIndex.banner.toString(),
          display: 'block', // Mostrar imediatamente para debug
          overflow: 'hidden',
          pointerEvents: 'auto',
          backgroundColor: '#FF0000', // Cor de fundo para teste
          borderTop: '3px solid yellow' // Destaque visual
        }, document.body);
        
        // Adiciona texto de teste
        container.innerHTML = '<div style="color:white;text-align:center;padding:10px">BANNER TESTE</div>';
        
        domElements.bannerContainer = container;
        this.log('Container de banner criado com sucesso');
      } catch (error) {
        this.log(`Erro ao criar container de banner: ${error.message}`, 'error');
      }
    },

    // Função showBanner MODIFICADA
    showBanner: function() {
      try {
        if (!state.isGameScreen) {
          this.log('Não está na tela de jogo, banner não será exibido');
          return;
        }
        
        if (state.banners.length === 0) {
          this.log('Nenhum banner disponível para exibição', 'warn');
          return;
        }
        
        // Verificação robusta do container
        if (!domElements.bannerContainer || !utils.elementExists(domElements.bannerContainer)) {
          this.log('Container de banner não encontrado, recriando...', 'warn');
          this.createBannerContainer();
          
          // Forçar redimensionamento
          setTimeout(() => {
            if (domElements.bannerContainer) {
              domElements.bannerContainer.style.height = '140px';
            }
          }, 100);
        }
        
        const currentBanner = state.banners[state.currentBannerIndex];
        if (!currentBanner) {
          this.log(`Banner de índice ${state.currentBannerIndex} não encontrado`, 'error');
          return;
        }
        
        // Usar fallback se necessário
        const bannerImage = currentBanner.imageUrl || this.config.fallbackImageUrl;
        if (!bannerImage) {
          this.log('Nenhuma imagem disponível para o banner', 'error');
          return;
        }
        
        domElements.bannerContainer.innerHTML = '';
        
        // Criar elemento img em vez de background
        const img = new Image();
        img.src = bannerImage;
        img.style.width = '100%';
        img.style.height = '100%';
        img.style.objectFit = 'cover';
        img.onerror = () => {
          this.log(`Falha ao carregar imagem: ${bannerImage}`, 'error');
          domElements.bannerContainer.innerHTML = 
            '<div style="color:white;padding:10px;text-align:center">Anúncio</div>';
        };
        
        // Adicionar evento de clique
        img.addEventListener('click', () => {
          this.handleBannerClick(currentBanner);
        });
        
        domElements.bannerContainer.appendChild(img);
        domElements.bannerContainer.style.display = 'block';
        
        // Verificação final
        setTimeout(() => this.checkVisibility(), 50);
        
        this.registerImpression(currentBanner.id, 'banner');
        this.log(`Banner exibido: ${currentBanner.id}`);
      } catch (error) {
        this.log(`Erro ao exibir banner: ${error.message}`, 'error');
      }
    },

    // NOVA FUNÇÃO ADICIONADA
    checkVisibility: function() {
      if (!domElements.bannerContainer) {
        this.log('Container de banner não existe', 'error');
        return false;
      }
      
      const rect = domElements.bannerContainer.getBoundingClientRect();
      const isVisible = rect.top < window.innerHeight && rect.bottom >= 0;
      
      this.log(`Status de visibilidade do banner: ${isVisible}`, 'info');
      this.log(`Posição/Dimensões: top:${rect.top}, bottom:${rect.bottom}, height:${rect.height}`, 'info');
      
      return isVisible;
    },

    // [O restante das funções permanece igual...]
  };

  return publicAPI;
})();

// Inicialização (mantida igual)
document.addEventListener('DOMContentLoaded', function() {
  console.log('[AdSystem] Sistema de anúncios carregado');
  setTimeout(function() {
    try {
      adSystem.init();
    } catch (error) {
      console.error('[AdSystem] Erro durante inicialização:', error);
    }
  }, 1000);
});

if (document.readyState === 'complete' || document.readyState === 'interactive') {
  console.log('[AdSystem] Documento já carregado, iniciando com atraso...');
  setTimeout(function() {
    try {
      adSystem.init();
    } catch (error) {
      console.error('[AdSystem] Erro durante inicialização:', error);
    }
  }, 1000);
}