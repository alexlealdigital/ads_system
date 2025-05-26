import firebase_admin
from firebase_admin import credentials, db as firebase_rtdb # Renomeado para evitar conflito com 'db' local se houver
from flask import Flask, render_template, request, redirect, url_for, jsonify # jsonify adicionado
import os
import logging
from flask_cors import CORS # Se for usar CORS, mantenha

# --- CONFIGURAÇÃO INICIAL DA APLICAÇÃO E LOGGING ---
app = Flask(__name__)
app.logger.setLevel(logging.INFO) # Ou DEBUG para mais detalhes

# --- CONFIGURAÇÃO CORS (se necessário para este app, adapte do seu server.py) ---
# Exemplo simples, ajuste conforme a necessidade para este dashboard
CORS(app, resources={r"/*": {"origins": "*"}}) # Permite todas as origens para todas as rotas deste app

# --- CONFIGURAÇÃO DAS CREDENCIAIS FIREBASE (adaptado do seu server.py) ---
FIREBASE_CREDENTIALS = {
    "type": os.getenv("FIREBASE_TYPE"),
    "project_id": os.getenv("FIREBASE_PROJECT_ID"),
    "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
    "private_key": os.getenv("FIREBASE_PRIVATE_KEY", "").replace('\\n', '\n'),
    "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
    "client_id": os.getenv("FIREBASE_CLIENT_ID"),
    "auth_uri": os.getenv("FIREBASE_AUTH_URI"),
    "token_uri": os.getenv("FIREBASE_TOKEN_URI"),
    "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER"),
    "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_CERT")
}

FIREBASE_DB_URL = os.getenv("FIREBASE_DB_URL")

# --- INICIALIZAÇÃO FIREBASE ---
def init_firebase():
    if not FIREBASE_DB_URL:
        app.logger.error("🔥 ERRO Firebase: FIREBASE_DB_URL não configurada nas variáveis de ambiente.")
        return False
    if not firebase_admin._apps: # Verifica se já existe uma app default inicializada
        try:
            # Verifica se todas as credenciais essenciais estão presentes
            required_creds = ["type", "project_id", "private_key_id", "private_key", "client_email", "client_id", "auth_uri", "token_uri", "auth_provider_x509_cert_url", "client_x509_cert_url"]
            missing_creds = [key for key in required_creds if not FIREBASE_CREDENTIALS.get(key)]
            if missing_creds:
                app.logger.error(f"🔥 ERRO Firebase: Credenciais faltando nas variáveis de ambiente: {', '.join(missing_creds)}")
                return False

            cred = credentials.Certificate(FIREBASE_CREDENTIALS)
            firebase_admin.initialize_app(cred, {
                'databaseURL': FIREBASE_DB_URL
            })
            app.logger.info("✅ Firebase Admin SDK inicializado com sucesso para o Dashboard!")
            return True
        except Exception as e:
            app.logger.error(f"🔥 ERRO Firebase ao inicializar: {str(e)}", exc_info=True)
            return False
    app.logger.info("✅ Firebase Admin SDK já estava inicializado.")
    return True

# Chamada de inicialização do Firebase (importante para Render)
# Gunicorn (usado pelo Render) pode não executar o bloco if __name__ == '__main__' da mesma forma.
# É mais seguro chamar a inicialização uma vez no escopo global ou no início da criação do app.
# No entanto, para evitar problemas com o reloader do Flask em desenvolvimento local,
# a função init_firebase() será chamada no início de cada rota que precisa do Firebase,
# e ela própria impede re-inicializações.

def calculate_ctr(clicks, impressions):
    if impressions == 0:
        return 0.0
    return round((clicks / impressions) * 100, 2)

# --- ROTAS DO DASHBOARD DE ANÚNCIOS ---

@app.route('/')
def dashboard():
    app.logger.info("Acessando a rota do Dashboard ('/')")
    if not init_firebase():
        return render_template('error.html', message="Falha ao conectar com o Firebase. Verifique os logs do servidor."), 500

    banner_ads_list = []
    fullscreen_ads_list = []
    try:
        # Buscar banners do Firebase RTDB
        banners_ref = firebase_rtdb.reference('ads/banners')
        all_banners = banners_ref.order_by_child('created_at').get() # Ordena por 'created_at'
        if all_banners:
            for ad_id, ad_data in all_banners.items():
                if isinstance(ad_data, dict): # Garante que é um dicionário de anúncio
                    ad_data['id'] = ad_id
                    banner_ads_list.append(ad_data)
            banner_ads_list.reverse() # Para mostrar os mais recentes primeiro (se created_at for timestamp crescente)
        app.logger.debug(f"Banners carregados do Firebase: {len(banner_ads_list)} itens.")

        # Buscar anúncios de tela cheia do Firebase RTDB
        fullscreen_ref = firebase_rtdb.reference('ads/fullscreen_ads')
        all_fullscreen = fullscreen_ref.order_by_child('created_at').get()
        if all_fullscreen:
            for ad_id, ad_data in all_fullscreen.items():
                if isinstance(ad_data, dict):
                    ad_data['id'] = ad_id
                    fullscreen_ads_list.append(ad_data)
            fullscreen_ads_list.reverse()
        app.logger.debug(f"Anúncios de tela cheia carregados do Firebase: {len(fullscreen_ads_list)} itens.")

    except Exception as e:
        app.logger.error(f"Erro ao buscar dados do Firebase para o dashboard: {e}", exc_info=True)
        # Considerar renderizar a página de erro aqui também ou apenas com listas vazias
        # return render_template('error.html', message="Erro ao carregar dados do Firebase."), 500


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
    app.logger.info(f"Dados finais enviados para o template dashboard.html: {metrics_data}")
    return render_template('dashboard.html', metrics=metrics_data)

@app.route('/add-banner', methods=['GET', 'POST'])
def add_banner():
    app.logger.info(f"Acessando a rota '/add-banner' com o método: {request.method}")
    if not init_firebase():
        return render_template('error.html', message="Falha ao conectar com o Firebase."), 500

    if request.method == 'POST':
        try:
            title = request.form['title']
            imageUrl = request.form['imageUrl']
            targetUrl = request.form['targetUrl']
            app.logger.info(f"Dados recebidos do formulário de banner: Título='{title}', ImageURL='{imageUrl}', TargetURL='{targetUrl}'")

            ads_ref = firebase_rtdb.reference('ads/banners')
            new_ad_ref = ads_ref.push({
                'title': title,
                'imageUrl': imageUrl,
                'targetUrl': targetUrl,
                'impressions': 0,
                'clicks': 0,
                'created_at': firebase_rtdb.SERVER_TIMESTAMP # Timestamp do servidor Firebase
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
        return render_template('error.html', message="Falha ao conectar com o Firebase."), 500

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
                # Não atualizamos impressions, clicks ou created_at aqui intencionalmente
            })
            app.logger.info(f"Banner ID {ad_id} atualizado no Firebase RTDB.")
            return redirect(url_for('dashboard'))
        except Exception as e:
            app.logger.error(f"Erro ao editar banner ID {ad_id} no Firebase RTDB: {e}", exc_info=True)
            return render_template('error.html', message="Erro ao salvar as alterações do banner.")

    # GET request
    try:
        banner_data = banner_ref.get()
        if not banner_data:
            app.logger.warning(f"Tentativa de editar banner com ID {ad_id} não encontrado no Firebase RTDB.")
            return render_template('error.html', message=f"Banner com ID {ad_id} não encontrado."), 404
        
        # Adiciona o ID aos dados para o template, caso ele precise (o template original usa banner.id)
        banner_data['id'] = ad_id 
        app.logger.debug(f"Renderizando formulário de edição para o banner: {banner_data}")
        return render_template('edit_banner.html', banner=banner_data)
    except Exception as e:
        app.logger.error(f"Erro ao buscar banner ID {ad_id} para edição: {e}", exc_info=True)
        return render_template('error.html', message="Erro ao carregar dados do banner para edição."), 500


@app.route('/delete-banner/<string:ad_id>', methods=['POST'])
def delete_banner(ad_id):
    app.logger.info(f"Acessando a rota POST '/delete-banner/{ad_id}'")
    if not init_firebase():
        return render_template('error.html', message="Falha ao conectar com o Firebase."), 500
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
        return render_template('error.html', message="Falha ao conectar com o Firebase."), 500

    if request.method == 'POST':
        try:
            title = request.form['title']
            imageUrl = request.form['imageUrl']
            targetUrl = request.form['targetUrl']
            app.logger.info(f"Dados recebidos do formulário de tela cheia: Título='{title}', ImageURL='{imageUrl}', TargetURL='{targetUrl}'")

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
        return render_template('error.html', message="Falha ao conectar com o Firebase."), 500
    
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
        if not ad_data:
            app.logger.warning(f"Tentativa de editar anúncio de tela cheia com ID {ad_id} não encontrado no Firebase RTDB.")
            return render_template('error.html', message=f"Anúncio de tela cheia com ID {ad_id} não encontrado."), 404
        
        ad_data['id'] = ad_id
        app.logger.debug(f"Renderizando formulário de edição para o anúncio de tela cheia: {ad_data}")
        return render_template('edit_fullscreen.html', ad=ad_data) # 'ad' é a variável usada no template edit_fullscreen.html
    except Exception as e:
        app.logger.error(f"Erro ao buscar anúncio de tela cheia ID {ad_id} para edição: {e}", exc_info=True)
        return render_template('error.html', message="Erro ao carregar dados do anúncio para edição."), 500

@app.route('/delete-fullscreen/<string:ad_id>', methods=['POST'])
def delete_fullscreen(ad_id):
    app.logger.info(f"Acessando a rota POST '/delete-fullscreen/{ad_id}'")
    if not init_firebase():
        return render_template('error.html', message="Falha ao conectar com o Firebase."), 500
    try:
        ad_ref = firebase_rtdb.reference(f'ads/fullscreen_ads/{ad_id}')
        ad_ref.delete()
        app.logger.info(f"Anúncio de tela cheia com ID {ad_id} deletado do Firebase RTDB com sucesso.")
    except Exception as e:
        app.logger.error(f"Erro ao deletar anúncio de tela cheia ID {ad_id} no Firebase RTDB: {e}", exc_info=True)
        return render_template('error.html', message=f"Erro ao deletar anúncio de tela cheia ID {ad_id}.")
    return redirect(url_for('dashboard'))


# --- ROTAS PARA API (se o jogo for consumir dados daqui) ---
# Exemplo:
# @app.route('/api/get-active-banner', methods=['GET'])
# def get_active_banner():
#     if not init_firebase():
#         return jsonify({"error": "Firebase connection failed"}), 500
#     try:
#         # Lógica para buscar um banner ativo do Firebase RTDB
#         # Ex: banners_ref = firebase_rtdb.reference('ads/banners')
#         # active_banner = banners_ref.order_by_child('impressions').limit_to_first(1).get() # Exemplo simplista
#         # ... processar e retornar o banner ...
#         # Este é apenas um placeholder, a lógica de qual banner é "ativo" precisa ser definida
        
#         # Por enquanto, vamos pegar o mais recente como exemplo
#         banners_ref = firebase_rtdb.reference('ads/banners')
#         latest_banner_query = banners_ref.order_by_child('created_at').limit_to_last(1)
#         latest_banner_data = latest_banner_query.get()

#         if latest_banner_data:
#             banner_id = list(latest_banner_data.keys())[0]
#             active_banner = latest_banner_data[banner_id]
#             active_banner['id'] = banner_id # Inclui o ID do banner

#             # Incrementar impressão aqui
#             impression_ref = firebase_rtdb.reference(f'ads/banners/{banner_id}/impressions')
#             impression_ref.transaction(lambda current_value: (current_value or 0) + 1)
            
#             return jsonify(active_banner)
#         else:
#             return jsonify({"message": "Nenhum banner ativo encontrado"}), 404
#     except Exception as e:
#         app.logger.error(f"Erro na API get-active-banner: {e}", exc_info=True)
#         return jsonify({"error": "Erro ao buscar banner"}), 500

# @app.route('/api/register-click/banner/<string:ad_id>', methods=['POST'])
# def register_banner_click(ad_id):
#     if not init_firebase():
#         return jsonify({"error": "Firebase connection failed"}), 500
#     try:
#         click_ref = firebase_rtdb.reference(f'ads/banners/{ad_id}/clicks')
#         # Usar transação para incrementar o contador de cliques de forma atômica
#         click_ref.transaction(lambda current_value: (current_value or 0) + 1)
#         app.logger.info(f"Clique registrado para banner ID {ad_id}")
#         return jsonify({"success": True, "message": "Clique registrado"})
#     except Exception as e:
#         app.logger.error(f"Erro ao registrar clique para banner {ad_id}: {e}", exc_info=True)
#         return jsonify({"error": "Erro ao registrar clique"}), 500

# Adicione rotas similares para fullscreen ads se necessário


# --- INICIALIZAÇÃO DA APLICAÇÃO ---
if __name__ == '__main__':
    # A inicialização do Firebase é chamada dentro das rotas agora para garantir
    # que ela ocorra antes de qualquer operação de banco de dados,
    # e a função init_firebase() em si impede múltiplas inicializações.
    # Se init_firebase() falhar no início, as rotas retornarão um erro.
    # Para um deploy em produção com Gunicorn, o Gunicorn lida com o início do app.
    # A chamada init_firebase() no início de cada rota que usa o DB é uma salvaguarda.
    
    # Para desenvolvimento local, garantir que as credenciais estejam acessíveis
    # (ex: via um arquivo .env carregado com python-dotenv se não estiverem no ambiente)
    # from dotenv import load_dotenv
    # load_dotenv() # Carrega variáveis de .env se você usar para desenvolvimento local

    # Apenas para confirmar que a tentativa de init ocorre ao iniciar localmente também:
    if not init_firebase():
        app.logger.critical("❌ Aplicação pode não funcionar corretamente: Falha na inicialização do Firebase no startup.")
    
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)), debug=True)
else:
    # Isso é relevante quando o Gunicorn importa 'app' no Render
    # Força uma tentativa de inicialização quando o módulo é carregado pelo Gunicorn
    if not init_firebase():
        # Isso pode não impedir o Gunicorn de tentar rodar, mas logará o erro.
        # O tratamento de erro em cada rota é a defesa principal.
        logging.getLogger().critical("❌ (Gunicorn Load) Aplicação pode não funcionar corretamente: Falha na inicialização do Firebase.")
