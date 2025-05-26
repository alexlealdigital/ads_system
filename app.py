import firebase_admin
from firebase_admin import credentials, db as firebase_rtdb
from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
import logging
from flask_cors import CORS
import time # Para created_at manual se SERVER_TIMESTAMP não for ideal para ordenação complexa

# --- CONFIGURAÇÃO INICIAL DA APLICAÇÃO E LOGGING ---
app = Flask(__name__)
app.logger.setLevel(logging.INFO) # Use logging.DEBUG para mais detalhes durante o desenvolvimento

# --- CONFIGURAÇÃO CORS ---
# Permite todas as origens para todas as rotas. Ajuste para produção se necessário.
CORS(app, resources={r"/*": {"origins": "*"}})

# --- CONFIGURAÇÃO FIREBASE ---
# Caminho para o Secret File no Render.
# O Render normalmente monta os secret files em /etc/secrets/NOME_DO_ARQUIVO
# Se você definiu a variável de ambiente GOOGLE_APPLICATION_CREDENTIALS no Render
# apontando para este arquivo, o SDK pode encontrá-lo automaticamente.
FIREBASE_CRED_FILE_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "/etc/secrets/firebase_credentials.json")
FIREBASE_DB_URL = os.getenv("FIREBASE_DB_URL")

# Flag para controlar se o Firebase foi inicializado com sucesso
firebase_initialized_successfully = False

def init_firebase():
    global firebase_initialized_successfully
    if firebase_initialized_successfully: # Evita tentar reinicializar se já deu certo
        # app.logger.debug("Firebase já inicializado com sucesso anteriormente.")
        return True

    if not FIREBASE_DB_URL:
        app.logger.error("🔥 ERRO Firebase: FIREBASE_DB_URL não configurada nas variáveis de ambiente.")
        firebase_initialized_successfully = False
        return False
    
    if not os.path.exists(FIREBASE_CRED_FILE_PATH):
        app.logger.error(f"🔥 ERRO Firebase: Arquivo de credenciais não encontrado em {FIREBASE_CRED_FILE_PATH}. Verifique o caminho e a configuração do Secret File no Render.")
        firebase_initialized_successfully = False
        return False

    # Evita reinicializar se já existe uma app Firebase default (pode acontecer em alguns cenários de reload)
    if not firebase_admin._apps:
        try:
            cred = credentials.Certificate(FIREBASE_CRED_FILE_PATH)
            firebase_admin.initialize_app(cred, {
                'databaseURL': FIREBASE_DB_URL
            })
            app.logger.info("✅ Firebase Admin SDK inicializado com sucesso usando Secret File!")
            firebase_initialized_successfully = True
            return True
        except Exception as e:
            app.logger.error(f"🔥 ERRO Firebase ao inicializar com Secret File: {str(e)}", exc_info=True)
            firebase_initialized_successfully = False
            return False
    else:
        app.logger.info("✅ Firebase Admin SDK já estava inicializado (app default existente).")
        # Assume que a inicialização anterior foi bem-sucedida se chegou aqui e _apps não está vazio.
        # Para ser mais robusto, poderíamos verificar o nome da app default, mas isso já é um bom avanço.
        firebase_initialized_successfully = True 
        return True


def calculate_ctr(clicks, impressions):
    if impressions == 0:
        return 0.0
    return round((clicks / impressions) * 100, 2)

# --- ROTAS DO DASHBOARD DE ANÚNCIOS ---

@app.route('/')
def dashboard():
    app.logger.info("Acessando a rota do Dashboard ('/')")
    if not init_firebase(): # Tenta inicializar/verificar Firebase
        return render_template('error.html', message="Falha crítica ao conectar com o Firebase. Verifique os logs do servidor."), 500

    banner_ads_list = []
    fullscreen_ads_list = []
    try:
        # Buscar banners do Firebase RTDB
        banners_ref = firebase_rtdb.reference('ads/banners')
        all_banners_data = banners_ref.order_by_child('created_at').get() # Ordena por 'created_at'
        if all_banners_data:
            # O RTDB retorna um dicionário, precisamos converter para lista e adicionar o ID
            for ad_id, ad_data_item in all_banners_data.items():
                if isinstance(ad_data_item, dict): # Garante que é um dicionário de anúncio
                    ad_data_item['id'] = ad_id
                    banner_ads_list.append(ad_data_item)
            banner_ads_list.reverse() # Para mostrar os mais recentes primeiro (se created_at for timestamp crescente)
        app.logger.debug(f"Banners carregados do Firebase: {len(banner_ads_list)} itens.")

        # Buscar anúncios de tela cheia do Firebase RTDB
        fullscreen_ref = firebase_rtdb.reference('ads/fullscreen_ads')
        all_fullscreen_data = fullscreen_ref.order_by_child('created_at').get()
        if all_fullscreen_data:
            for ad_id, ad_data_item in all_fullscreen_data.items():
                if isinstance(ad_data_item, dict):
                    ad_data_item['id'] = ad_id
                    fullscreen_ads_list.append(ad_data_item)
            fullscreen_ads_list.reverse()
        app.logger.debug(f"Anúncios de tela cheia carregados do Firebase: {len(fullscreen_ads_list)} itens.")

    except Exception as e:
        app.logger.error(f"Erro ao buscar dados do Firebase para o dashboard: {e}", exc_info=True)
        # Renderiza o dashboard com listas vazias em caso de erro, mas loga o problema.
        # return render_template('error.html', message="Erro ao carregar dados dos anúncios do Firebase."), 500

    # Cálculo de métricas
    total_banner_impressions = sum(ad.get('impressions', 0) for ad in banner_ads_list)
    total_banner_clicks = sum(ad.get('clicks', 0) for ad in banner_ads_list)
    banner_ctr = calculate_ctr(total_banner_clicks, total_banner_impressions)

    metrics_banner = {
        "ads_count": len(banner_ads_list),
        "total_impressions": total_banner_impressions,
        "ctr": banner_ctr,
        "ads": banner_ads_list
    }

    total_fullscreen_impressions = sum(ad.get('impressions', 0) for ad in fullscreen_ads_list)
    total_fullscreen_clicks = sum(ad.get('clicks', 0) for ad in fullscreen_ads_list)
    fullscreen_ctr = calculate_ctr(total_fullscreen_clicks, total_fullscreen_impressions)

    metrics_fullscreen = {
        "ads_count": len(fullscreen_ads_list),
        "total_impressions": total_fullscreen_impressions,
        "ctr": fullscreen_ctr,
        "ads": fullscreen_ads_list
    }

    metrics_data = {
        "banner": metrics_banner,
        "fullscreen": metrics_fullscreen
    }
    app.logger.info(f"Dados finais enviados para o template dashboard.html: {len(banner_ads_list)} banners, {len(fullscreen_ads_list)} fullscreen.")
    return render_template('dashboard.html', metrics=metrics_data)

@app.route('/add-banner', methods=['GET', 'POST'])
def add_banner():
    app.logger.info(f"Acessando a rota '/add-banner' com o método: {request.method}")
    if not init_firebase():
        return render_template('error.html', message="Falha crítica ao conectar com o Firebase."), 500

    if request.method == 'POST':
        try:
            title = request.form['title']
            imageUrl = request.form['imageUrl']
            targetUrl = request.form['targetUrl']
            app.logger.info(f"Formulário de banner recebido: Título='{title}'")

            ads_ref = firebase_rtdb.reference('ads/banners')
            new_ad_ref = ads_ref.push({
                'title': title,
                'imageUrl': imageUrl,
                'targetUrl': targetUrl,
                'impressions': 0,
                'clicks': 0,
                'created_at': firebase_rtdb.SERVER_TIMESTAMP
            })
            app.logger.info(f"Novo banner adicionado ao Firebase RTDB com ID: {new_ad_ref.key}")
            return redirect(url_for('dashboard'))
        except Exception as e:
            app.logger.error(f"Erro ao adicionar banner ao Firebase RTDB: {e}", exc_info=True)
            return render_template('error.html', message="Erro ao adicionar o banner.")
    return render_template('add_banner.html')

@app.route('/edit-banner/<string:ad_id>', methods=['GET', 'POST'])
def edit_banner(ad_id):
    app.logger.info(f"Acessando a rota '/edit-banner/{ad_id}' com o método: {request.method}")
    if not init_firebase():
        return render_template('error.html', message="Falha crítica ao conectar com o Firebase."), 500

    banner_ref = firebase_rtdb.reference(f'ads/banners/{ad_id}')
    
    if request.method == 'POST':
        try:
            title = request.form['title']
            imageUrl = request.form['imageUrl']
            targetUrl = request.form['targetUrl']
            
            banner_ref.update({
                'title': title,
                'imageUrl': imageUrl,
                'targetUrl': targetUrl
            })
            app.logger.info(f"Banner ID {ad_id} atualizado no Firebase RTDB.")
            return redirect(url_for('dashboard'))
        except Exception as e:
            app.logger.error(f"Erro ao editar banner ID {ad_id} no Firebase RTDB: {e}", exc_info=True)
            return render_template('error.html', message="Erro ao salvar as alterações do banner.")

    # GET request
    try:
        banner_data = banner_ref.get()
        if not banner_data or not isinstance(banner_data, dict): # Verifica se existe e é um dicionário
            app.logger.warning(f"Banner com ID {ad_id} não encontrado ou dados inválidos no Firebase RTDB.")
            return render_template('error.html', message=f"Banner com ID {ad_id} não encontrado."), 404
        
        banner_data['id'] = ad_id 
        app.logger.debug(f"Renderizando formulário de edição para o banner: {banner_data.get('title')}")
        return render_template('edit_banner.html', banner=banner_data)
    except Exception as e:
        app.logger.error(f"Erro ao buscar banner ID {ad_id} para edição: {e}", exc_info=True)
        return render_template('error.html', message="Erro ao carregar dados do banner para edição."), 500

@app.route('/delete-banner/<string:ad_id>', methods=['POST'])
def delete_banner(ad_id):
    app.logger.info(f"Acessando a rota POST '/delete-banner/{ad_id}'")
    if not init_firebase():
        return render_template('error.html', message="Falha crítica ao conectar com o Firebase."), 500
    try:
        banner_ref = firebase_rtdb.reference(f'ads/banners/{ad_id}')
        banner_ref.delete()
        app.logger.info(f"Banner com ID {ad_id} deletado do Firebase RTDB com sucesso.")
    except Exception as e:
        app.logger.error(f"Erro ao deletar banner ID {ad_id} no Firebase RTDB: {e}", exc_info=True)
        return render_template('error.html', message=f"Erro ao deletar banner ID {ad_id}.")
    return redirect(url_for('dashboard'))

# --- ROTAS PARA FULLSCREEN ADS (similares às de banner) ---

@app.route('/add-fullscreen', methods=['GET', 'POST'])
def add_fullscreen():
    app.logger.info(f"Acessando a rota '/add-fullscreen' com o método: {request.method}")
    if not init_firebase():
        return render_template('error.html', message="Falha crítica ao conectar com o Firebase."), 500

    if request.method == 'POST':
        try:
            title = request.form['title']
            imageUrl = request.form['imageUrl']
            targetUrl = request.form['targetUrl']
            app.logger.info(f"Formulário de tela cheia recebido: Título='{title}'")

            ads_ref = firebase_rtdb.reference('ads/fullscreen_ads')
            new_ad_ref = ads_ref.push({
                'title': title,
                'imageUrl': imageUrl,
                'targetUrl': targetUrl,
                'impressions': 0,
                'clicks': 0,
                'created_at': firebase_rtdb.SERVER_TIMESTAMP
            })
            app.logger.info(f"Novo anúncio de tela cheia adicionado ao Firebase RTDB com ID: {new_ad_ref.key}")
            return redirect(url_for('dashboard'))
        except Exception as e:
            app.logger.error(f"Erro ao adicionar anúncio de tela cheia ao Firebase RTDB: {e}", exc_info=True)
            return render_template('error.html', message="Erro ao adicionar o anúncio de tela cheia.")
    return render_template('add_fullscreen.html')

@app.route('/edit-fullscreen/<string:ad_id>', methods=['GET', 'POST'])
def edit_fullscreen(ad_id):
    app.logger.info(f"Acessando a rota '/edit-fullscreen/{ad_id}' com o método: {request.method}")
    if not init_firebase():
        return render_template('error.html', message="Falha crítica ao conectar com o Firebase."), 500
    
    ad_ref = firebase_rtdb.reference(f'ads/fullscreen_ads/{ad_id}')

    if request.method == 'POST':
        try:
            title = request.form['title']
            imageUrl = request.form['imageUrl']
            targetUrl = request.form['targetUrl']
            
            ad_ref.update({
                'title': title,
                'imageUrl': imageUrl,
                'targetUrl': targetUrl
            })
            app.logger.info(f"Anúncio de tela cheia ID {ad_id} atualizado no Firebase RTDB.")
            return redirect(url_for('dashboard'))
        except Exception as e:
            app.logger.error(f"Erro ao editar anúncio de tela cheia ID {ad_id} no Firebase RTDB: {e}", exc_info=True)
            return render_template('error.html', message="Erro ao salvar as alterações do anúncio.")

    # GET request
    try:
        ad_data = ad_ref.get()
        if not ad_data or not isinstance(ad_data, dict):
            app.logger.warning(f"Anúncio de tela cheia com ID {ad_id} não encontrado ou dados inválidos no Firebase RTDB.")
            return render_template('error.html', message=f"Anúncio de tela cheia com ID {ad_id} não encontrado."), 404
        
        ad_data['id'] = ad_id
        app.logger.debug(f"Renderizando formulário de edição para o anúncio de tela cheia: {ad_data.get('title')}")
        return render_template('edit_fullscreen.html', ad=ad_data)
    except Exception as e:
        app.logger.error(f"Erro ao buscar anúncio de tela cheia ID {ad_id} para edição: {e}", exc_info=True)
        return render_template('error.html', message="Erro ao carregar dados do anúncio para edição."), 500

@app.route('/delete-fullscreen/<string:ad_id>', methods=['POST'])
def delete_fullscreen(ad_id):
    app.logger.info(f"Acessando a rota POST '/delete-fullscreen/{ad_id}'")
    if not init_firebase():
        return render_template('error.html', message="Falha crítica ao conectar com o Firebase."), 500
    try:
        ad_ref = firebase_rtdb.reference(f'ads/fullscreen_ads/{ad_id}')
        ad_ref.delete()
        app.logger.info(f"Anúncio de tela cheia com ID {ad_id} deletado do Firebase RTDB com sucesso.")
    except Exception as e:
        app.logger.error(f"Erro ao deletar anúncio de tela cheia ID {ad_id} no Firebase RTDB: {e}", exc_info=True)
        return render_template('error.html', message=f"Erro ao deletar anúncio de tela cheia ID {ad_id}.")
    return redirect(url_for('dashboard'))

# --- ROTAS DE API PARA O JOGO UNITY (Exemplos) ---
# Estas rotas podem ser usadas pelo seu jogo Unity para buscar anúncios e registrar interações.
# Adapte conforme a necessidade do seu jogo.

@app.route('/api/get-banner', methods=['GET'])
def api_get_banner():
    if not init_firebase():
        return jsonify({"error": "Firebase connection failed", "message": "Não foi possível conectar ao servidor de dados."}), 500
    
    try:
        banners_ref = firebase_rtdb.reference('ads/banners')
        # Lógica para selecionar um banner (ex: mais recente, aleatório, menos visualizado)
        # Exemplo: pegar o mais recente que tenha imageUrl e targetUrl
        all_banners = banners_ref.order_by_child('created_at').get()
        
        active_banner_data = None
        if all_banners:
            # Itera de forma reversa para pegar os mais recentes primeiro
            for ad_id, ad_data in reversed(list(all_banners.items())):
                if isinstance(ad_data, dict) and ad_data.get('imageUrl') and ad_data.get('targetUrl'):
                    active_banner_data = ad_data
                    active_banner_data['id'] = ad_id
                    break # Pega o primeiro válido (mais recente)
        
        if active_banner_data:
            # Incrementar impressão
            impression_ref = firebase_rtdb.reference(f'ads/banners/{active_banner_data["id"]}/impressions')
            impression_ref.transaction(lambda current_value: (current_value or 0) + 1)
            app.logger.info(f"Banner ID {active_banner_data['id']} servido via API e impressão registrada.")
            return jsonify(active_banner_data)
        else:
            app.logger.info("API: Nenhum banner ativo encontrado para servir.")
            return jsonify({"message": "Nenhum banner ativo encontrado"}), 404
            
    except Exception as e:
        app.logger.error(f"Erro na API /api/get-banner: {e}", exc_info=True)
        return jsonify({"error": "Erro interno ao buscar banner"}), 500

@app.route('/api/register-click/banner/<string:ad_id>', methods=['POST'])
def api_register_banner_click(ad_id):
    if not init_firebase():
        return jsonify({"error": "Firebase connection failed", "message": "Não foi possível conectar ao servidor de dados."}), 500
    try:
        click_ref = firebase_rtdb.reference(f'ads/banners/{ad_id}/clicks')
        click_ref.transaction(lambda current_value: (current_value or 0) + 1)
        app.logger.info(f"API: Clique registrado para banner ID {ad_id}")
        return jsonify({"success": True, "message": "Clique registrado"})
    except Exception as e:
        app.logger.error(f"Erro ao registrar clique para banner {ad_id} via API: {e}", exc_info=True)
        return jsonify({"error": "Erro ao registrar clique"}), 500

# Adicione rotas API similares para '/api/get-fullscreen' e '/api/register-click/fullscreen/<ad_id>'


# --- INICIALIZAÇÃO DA APLICAÇÃO (Bloco Principal) ---
if __name__ == '__main__':
    # Para desenvolvimento local, pode ser útil carregar variáveis de um arquivo .env
    # from dotenv import load_dotenv
    # load_dotenv()
    # app.logger.info("Variáveis de ambiente .env carregadas (se existentes).")

    # Tenta inicializar o Firebase ao iniciar o servidor localmente.
    # A função init_firebase() agora tem uma flag para evitar múltiplas tentativas se já falhou.
    if not init_firebase():
        app.logger.critical("❌ INICIALIZAÇÃO LOCAL FALHOU: Firebase não pôde ser inicializado. Verifique as credenciais e a URL do DB.")
        # Você pode decidir se quer que o app pare aqui ou continue (ele falhará nas rotas)
        # exit(1) # Descomente para parar o app se o Firebase não inicializar

    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)), debug=True)
else:
    # Este bloco é executado quando o Gunicorn (ou outro servidor WSGI) importa 'app' no Render
    # Tenta inicializar o Firebase uma vez quando o módulo é carregado.
    if not init_firebase():
        # Loga o erro crítico. As rotas ainda tentarão init_firebase() como uma salvaguarda,
        # mas se falhar aqui, provavelmente falhará lá também.
        logging.getLogger().critical("❌ (GUNICORN LOAD) INICIALIZAÇÃO FALHOU: Firebase não pôde ser inicializado. Verifique as credenciais e a URL do DB no ambiente do Render.")

