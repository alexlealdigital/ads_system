# Sistema de Anúncios para Jogo WebGL Unity

Este sistema permite a exibição de anúncios em jogos WebGL Unity, com dois formatos principais:
1. **Banner rotativo** no topo da página do jogo (1080px × 140px)
2. **Anúncio de tela cheia** após game over (1080px × 1920px)

O sistema inclui um dashboard para gerenciamento de anúncios e visualização de métricas.

## Estrutura do Projeto

```
ads_system/
├── app.py                 # Aplicação principal Flask
├── models/
│   └── ads.py             # Modelo de dados para anúncios
├── static/
│   └── ads.js             # Script de integração com o jogo
└── templates/
    ├── dashboard.html     # Dashboard principal
    ├── add_banner.html    # Formulário para adicionar banner
    ├── add_fullscreen.html # Formulário para adicionar anúncio de tela cheia
    └── error.html         # Página de erro
```

## Requisitos

- Python 3.6+
- Flask
- Firebase Admin SDK
- Acesso ao Firebase Realtime Database
- Imgur para hospedagem de imagens

## Configuração

1. Configure as variáveis de ambiente para o Firebase:
   ```
   FIREBASE_TYPE=service_account
   FIREBASE_PROJECT_ID=seu-projeto
   FIREBASE_PRIVATE_KEY_ID=chave-privada-id
   FIREBASE_PRIVATE_KEY=chave-privada
   FIREBASE_CLIENT_EMAIL=email-cliente
   FIREBASE_CLIENT_ID=id-cliente
   FIREBASE_AUTH_URI=https://accounts.google.com/o/oauth2/auth
   FIREBASE_TOKEN_URI=https://oauth2.googleapis.com/token
   FIREBASE_AUTH_PROVIDER=https://www.googleapis.com/oauth2/v1/certs
   FIREBASE_CLIENT_CERT=url-certificado-cliente
   FIREBASE_DB_URL=https://seu-projeto.firebaseio.com
   ```

2. Instale as dependências:
   ```
   pip install flask firebase-admin flask-cors
   ```

3. Inicie o servidor:
   ```
   python app.py
   ```

## Integração com o Jogo Unity

1. Adicione o script `ads.js` ao seu HTML do jogo:
   ```html
   <script src="ads.js"></script>
   ```

2. Modifique o HTML do jogo para incluir o script após o carregamento do Unity:
   ```javascript
   // Após a criação da instância do Unity
   createUnityInstance(canvas, config, (progress) => {
     // Código existente
   }).then((unityInstance) => {
     // Código existente
     
     // Disparar evento para o sistema de anúncios
     window.dispatchEvent(new CustomEvent('unityInstance', { detail: unityInstance }));
   });
   ```

3. No seu jogo Unity, adicione chamadas para JavaScript:
   ```csharp
   // Quando ocorrer um game over
   Application.ExternalCall("gameOver");
   
   // Para mostrar/esconder banner manualmente
   Application.ExternalCall("showBanner");
   Application.ExternalCall("hideBanner");
   
   // Para pausar/retomar o jogo (implemente estes métodos no Unity)
   // O sistema de anúncios chamará estes métodos automaticamente
   // PauseGame()
   // ResumeGame()
   ```

## Funcionalidades

### Banner Rotativo
- Exibido apenas na tela de jogo, não no menu
- Formato: 1080px × 140px
- Rotação automática a cada 7 segundos
- Clicável, direcionando para o site do anunciante

### Anúncio de Tela Cheia
- Exibido a cada 5 game overs
- Formato: 1080px × 1920px
- Duração: 5 segundos
- Clicável, direcionando para o site do anunciante
- Pausa automaticamente o jogo durante a exibição

### Dashboard
- Visualização de métricas (impressões, cliques, CTR)
- Gráficos de desempenho
- Formulários para adicionar novos anúncios
- Listagem detalhada de todos os anúncios

### Rastreamento
- Registro automático de impressões
- Registro de cliques
- Cálculo de CTR (Click-Through Rate)

## Uso do Dashboard

1. Acesse a página inicial para ver as métricas
2. Use o menu para adicionar novos anúncios
3. Preencha o formulário com:
   - URL da imagem (hospedada no Imgur)
   - URL de destino (site do anunciante)
4. Visualize o desempenho dos anúncios nas tabelas e gráficos

## Personalização

Você pode personalizar o sistema editando:

- `static/ads.js`: Configurações de intervalo, contadores, etc.
- `templates/*.html`: Aparência do dashboard e formulários
- `app.py`: Rotas e lógica do servidor
- `models/ads.py`: Estrutura de dados e interação com Firebase

## Suporte

Para dúvidas ou problemas, entre em contato com o desenvolvedor.
