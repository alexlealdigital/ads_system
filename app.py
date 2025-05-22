"""
Aplicação principal para o sistema de anúncios e dashboard
Versão corrigida e otimizada para deploy no Render usando variáveis de ambiente
Com configuração CORS específica para permitir o domínio do Netlify
"""
import os
import sys
import logging
from flask import Flask, jsonify, request, render_template, redirect, url_for
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, db

# Adicionar o diretório atual ao path do Python para garantir que os módulos sejam encontrados
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicialização da aplicação Flask
app = Flask(__name__)

# Configuração de CORS - específica para o domínio do Netlify
# Nota: Se "*" for mantido na lista de origins, pode permitir qualquer origem.
# Para produção restrita, remova "*" e deixe apenas os domínios específicos.
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "https://jade-lamington-63db57.netlify.app",
            "https://682d482f8ce48197b4658282--jade-lamington-63db57.netlify.app",
            "http://localhost:3000", # Para desenvolvimento frontend local
            "http://localhost:5000", # Para desenvolvimento backend local, se necessário
            # "*" # Remova para produção se quiser restringir apenas aos domínios acima
        ],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "X-Requested-With", "Accept", "Origin"],
        "expose_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True,
        "max_age": 86400
    }
})

# Inicialização do Firebase usando variáveis de ambiente
def init_firebase():
    """Inicializa a conexão com o Firebase usando variáveis de ambiente"""
    if not firebase_admin._apps:
        try:
            private_key_from_env = os.getenv("FIREBASE_PRIVATE_KEY", "")
            if not private_key_from_env:
                logger.error("🔥 ERRO Firebase: Variável de ambiente FIREBASE_PRIVATE_KEY não definida.")
                return False
            
            if private_key_from_env.startswith('"') and private_key_from_env.endswith('"'):
                private_key_from_env = private_key_from_env[1:-1]
            private_key = private_key_from_env.replace('\\n', '\n')
            
            cred_dict = {
                "type": os.getenv("FIREBASE_TYPE", "service_account"),
                "project_id": os.getenv("FIREBASE_PROJECT_ID"),
                "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
                "private_key": private_key,
                "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
                "client_id": os.getenv("FIREBASE_CLIENT_ID"),
                "auth_uri": os.getenv("FIREBASE_AUTH_URI", "https://accounts.google.com/o/oauth2/auth"),
                "token_uri": os.getenv("FIREBASE_TOKEN_URI", "https://oauth2.googleapis.com/token"),
                "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER_X509_CERT_URL", "https://www.googleapis.com/oauth2/v1/certs"),
                "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_X509_CERT_URL")
            }

            # Validação básica se as chaves essenciais estão presentes
            required_fields = ["project_id", "private_key_id", "private_key", "client_email", "client_id", "client_x509_cert_url"]
            for field in required_fields:
                if not cred_dict.get(field):
                    logger.error(f"🔥 ERRO Firebase: Variável de ambiente para '{field}' não definida ou vazia.")
                    return False
            
            cred = credentials.Certificate(cred_dict)
            
            database_url = os.getenv('FIREBASE_DATABASE_URL') # Consistente com sua sugestão anterior FIREBASE_DB_URL
            if not database_url:
                logger.error("🔥 ERRO Firebase: Variável de ambiente FIREBASE_DATABASE_URL não definida.")
                return False
                
            firebase_admin.initialize_app(cred, {
                'databaseURL': database_url
            })
            
            logger.info("✅ Firebase inicializado com sucesso usando variáveis de ambiente")
            return True
        except Exception as e:
            logger.error(f"🔥 ERRO Firebase ao inicializar: {str(e)}")
            logger.exception("Detalhes da exceção:")
            return False
    return True

# Importar modelo de anúncios após configurar o path
try:
    from models.ads import AdModel
    logger.info("✅ Módulo models.ads importado com sucesso")
except ImportError as e:
    logger.error(f"❌ Erro ao importar models.ads: {str(e)}")
    # Código de verificação de arquivo (opcional, mas útil para debug)
    # ... (seu código de verificação de arquivo aqui, se desejar mantê-lo) ...

# Instância do modelo de anúncios
ads_model = None

# Inicialização do modelo de anúncios
def init_ads_model():
    """Inicializa o modelo de anúncios"""
    global ads_model
    if init_firebase():
        if ads_model is None: # Evita reinicializar o modelo se já existir
            try:
                ads_ref = db.reference('ads')
                ads_model = AdModel(ads_ref)
                logger.info("✅ Modelo de anúncios inicializado.")
            except Exception as e:
                logger.error(f"🔥 ERRO ao inicializar modelo de anúncios: {str(e)}")
                return False
        return True
    return False

# --- ROTAS DA API ---
# Novas rotas (preferenciais)
@app.route('/api/banners', methods=['GET', 'OPTIONS'])
def get_banners():
    if request.method == 'OPTIONS': return '', 200
    if not init_ads_model(): return jsonify({"error": "Falha ao inicializar Firebase"}), 500
    try:
        ads = ads_model.get_banner_ads()
        return jsonify(ads if ads else []) # Retorna lista vazia se ads for None/False
    except Exception as e:
        logger.error(f"Erro ao obter banners: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/fullscreen', methods=['GET', 'OPTIONS'])
def get_fullscreen():
    if request.method == 'OPTIONS': return '', 200
    if not init_ads_model(): return jsonify({"error": "Falha ao inicializar Firebase"}), 500
    try:
        ads = ads_model.get_fullscreen_ads()
        return jsonify(ads if ads else []) # Retorna lista vazia se ads for None/False
    except Exception as e:
        logger.error(f"Erro ao obter anúncios de tela cheia: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Rotas de compatibilidade (mantendo o formato de resposta antigo)
@app.route('/api/ads/banner', methods=['GET', 'OPTIONS'])
def get_banner_ads_compat():
    if request.method == 'OPTIONS': return '', 200
    if not init_ads_model(): return jsonify({"error": "Falha ao inicializar Firebase"}), 500
    try:
        ads_list = ads_model.get_banner_ads()
        return jsonify({"ads": ads_list if ads_list else []}) # Mantém o wrapper {"ads": ...}
    except Exception as e:
        logger.error(f"Erro ao obter banners (compat): {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/ads/fullscreen', methods=['GET', 'OPTIONS'])
def get_fullscreen_ads_compat():
    if request.method == 'OPTIONS': return '', 200
    if not init_ads_model(): return jsonify({"error": "Falha ao inicializar Firebase"}), 500
    try:
        ads_list = ads_model.get_fullscreen_ads()
        return jsonify({"ads": ads_list if ads_list else []}) # Mantém o wrapper {"ads": ...}
    except Exception as e:
        logger.error(f"Erro ao obter fullscreen (compat): {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/impression', methods=['POST', 'OPTIONS'])
def record_impression():
    if request.method == 'OPTIONS': return '', 200
    if not init_ads_model(): return jsonify({"error": "Falha ao inicializar Firebase"}), 500
    try:
        data = request.get_json()
        ad_id = data.get('adId')
        ad_type = data.get('type', data.get('adType'))
        if not ad_id or not ad_type: return jsonify({"error": "ID do anúncio e tipo são obrigatórios"}), 400
        if ad_type not in ['banner', 'fullscreen']: return jsonify({"error": "Tipo de anúncio inválido"}), 400
        
        success = ads_model.record_impression(ad_id, ad_type)
        return jsonify({"success": True} if success else {"error": "Falha ao registrar impressão"}), (200 if success else 500)
    except Exception as e:
        logger.error(f"Erro ao registrar impressão: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/click', methods=['POST', 'OPTIONS'])
def record_click():
    if request.method == 'OPTIONS': return '', 200
    if not init_ads_model(): return jsonify({"error": "Falha ao inicializar Firebase"}), 500
    try:
        data = request.get_json()
        ad_id = data.get('adId')
        ad_type = data.get('type', data.get('adType'))
        if not ad_id or not ad_type: return jsonify({"error": "ID do anúncio e tipo são obrigatórios"}), 400
        if ad_type not in ['banner', 'fullscreen']: return jsonify({"error": "Tipo de anúncio inválido"}), 400
        
        success = ads_model.record_click(ad_id, ad_type)
        return jsonify({"success": True} if success else {"error": "Falha ao registrar clique"}), (200 if success else 500)
    except Exception as e:
        logger.error(f"Erro ao registrar clique: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Rotas de compatibilidade para /api/ads/impression e /api/ads/click
@app.route('/api/ads/impression', methods=['POST', 'OPTIONS'])
def record_impression_compat():
    if request.method == 'OPTIONS': return '', 200
    return record_impression()

@app.route('/api/ads/click', methods=['POST', 'OPTIONS'])
def record_click_compat():
    if request.method == 'OPTIONS': return '', 200
    return record_click()

# --- ROTAS DO DASHBOARD (JÁ INCLUEM EDITAR E DELETAR) ---
@app.route('/')
def dashboard_home():
    if not init_ads_model():
        return render_template('error.html', message="Falha ao inicializar Firebase ou AdModel")
    try:
        metrics = ads_model.get_metrics()
        # Para o dashboard, você precisará buscar os anúncios para listá-los
        # e permitir as ações de editar/deletar
        banner_ads_list = ads_model.get_banner_ads()
        fullscreen_ads_list = ads_model.get_fullscreen_ads()
        return render_template('dashboard.html', 
                               metrics=metrics, 
                               banner_ads=banner_ads_list if banner_ads_list else [], 
                               fullscreen_ads=fullscreen_ads_list if fullscreen_ads_list else [])
    except Exception as e:
        logger.error(f"Erro ao carregar dashboard: {str(e)}")
        return render_template('error.html', message=str(e))

@app.route('/add-banner', methods=['GET', 'POST'])
def add_banner():
    if request.method == 'POST':
        if not init_ads_model(): return render_template('error.html', message="Falha ao inicializar Firebase")
        try:
            image_url = request.form.get('imageUrl')
            link_url = request.form.get('linkUrl')
            if not image_url or not link_url:
                return render_template('add_banner.html', error="URL da imagem e URL de destino são obrigatórios")
            ad_id = ads_model.add_banner_ad(image_url, link_url)
            if ad_id: return redirect(url_for('dashboard_home'))
            else: return render_template('add_banner.html', error="Falha ao adicionar anúncio")
        except Exception as e:
            logger.error(f"Erro ao adicionar banner: {str(e)}")
            return render_template('add_banner.html', error=str(e))
    return render_template('add_banner.html')

@app.route('/edit-banner/<ad_id>', methods=['GET', 'POST'])
def edit_banner(ad_id):
    if not init_ads_model(): return render_template('error.html', message="Falha ao inicializar Firebase")
    try:
        ad = ads_model.get_banner_ad(ad_id) # Busca o anúncio para GET e para POST (em caso de erro de validação)
        if not ad: return render_template('error.html', message="Anúncio não encontrado")

        if request.method == 'POST':
            image_url = request.form.get('imageUrl')
            link_url = request.form.get('linkUrl')
            if not image_url or not link_url:
                return render_template('edit_banner.html', error="URL da imagem e URL de destino são obrigatórios", ad=ad)
            
            success = ads_model.update_banner_ad(ad_id, image_url, link_url)
            if success: return redirect(url_for('dashboard_home'))
            else: return render_template('edit_banner.html', error="Falha ao atualizar anúncio", ad=ad)
        
        return render_template('edit_banner.html', ad=ad) # GET request
    except Exception as e:
        logger.error(f"Erro ao editar banner: {str(e)}")
        return render_template('error.html', message=str(e))

@app.route('/delete-banner/<ad_id>', methods=['POST'])
def delete_banner(ad_id):
    if not init_ads_model(): return render_template('error.html', message="Falha ao inicializar Firebase") # Para form submit
    try:
        success = ads_model.delete_banner_ad(ad_id)
        if success: return redirect(url_for('dashboard_home'))
        else: return render_template('error.html', message="Falha ao excluir anúncio")
    except Exception as e:
        logger.error(f"Erro ao excluir banner: {str(e)}")
        return render_template('error.html', message=str(e))

# ... (Rotas para add_fullscreen, edit_fullscreen, delete_fullscreen seguem o mesmo padrão) ...
@app.route('/add-fullscreen', methods=['GET', 'POST'])
def add_fullscreen():
    if request.method == 'POST':
        if not init_ads_model(): return render_template('error.html', message="Falha ao inicializar Firebase")
        try:
            image_url = request.form.get('imageUrl')
            link_url = request.form.get('linkUrl')
            if not image_url or not link_url:
                return render_template('add_fullscreen.html', error="URL da imagem e URL de destino são obrigatórios")
            ad_id = ads_model.add_fullscreen_ad(image_url, link_url)
            if ad_id: return redirect(url_for('dashboard_home'))
            else: return render_template('add_fullscreen.html', error="Falha ao adicionar anúncio")
        except Exception as e:
            logger.error(f"Erro ao adicionar anúncio de tela cheia: {str(e)}")
            return render_template('add_fullscreen.html', error=str(e))
    return render_template('add_fullscreen.html')

@app.route('/edit-fullscreen/<ad_id>', methods=['GET', 'POST'])
def edit_fullscreen(ad_id):
    if not init_ads_model(): return render_template('error.html', message="Falha ao inicializar Firebase")
    try:
        ad = ads_model.get_fullscreen_ad(ad_id)
        if not ad: return render_template('error.html', message="Anúncio não encontrado")

        if request.method == 'POST':
            image_url = request.form.get('imageUrl')
            link_url = request.form.get('linkUrl')
            if not image_url or not link_url:
                return render_template('edit_fullscreen.html', error="URL da imagem e URL de destino são obrigatórios", ad=ad)
            success = ads_model.update_fullscreen_ad(ad_id, image_url, link_url)
            if success: return redirect(url_for('dashboard_home'))
            else: return render_template('edit_fullscreen.html', error="Falha ao atualizar anúncio", ad=ad)
        return render_template('edit_fullscreen.html', ad=ad)
    except Exception as e:
        logger.error(f"Erro ao editar anúncio de tela cheia: {str(e)}")
        return render_template('error.html', message=str(e))

@app.route('/delete-fullscreen/<ad_id>', methods=['POST'])
def delete_fullscreen(ad_id):
    if not init_ads_model(): return render_template('error.html', message="Falha ao inicializar Firebase")
    try:
        success = ads_model.delete_fullscreen_ad(ad_id)
        if success: return redirect(url_for('dashboard_home'))
        else: return render_template('error.html', message="Falha ao excluir anúncio")
    except Exception as e:
        logger.error(f"Erro ao excluir anúncio de tela cheia: {str(e)}")
        return render_template('error.html', message=str(e))

# Rota para verificação de saúde
@app.route('/health')
def health_check():
    firebase_ok = init_firebase() # Tenta inicializar o Firebase
    model_ok = False
    if firebase_ok:
        model_ok = init_ads_model() # Tenta inicializar o modelo se o Firebase estiver OK

    if firebase_ok and model_ok:
        return jsonify({"status": "healthy", "firebase": "ok", "ads_model": "ok"}), 200
    else:
        return jsonify({
            "status": "unhealthy", 
            "firebase": "ok" if firebase_ok else "failed", 
            "ads_model": "ok" if model_ok else ("not_attempted" if not firebase_ok else "failed")
        }), 503

# Inicialização da aplicação
if __name__ == '__main__':
    if not init_ads_model(): # Tenta pré-inicializar para logar erros cedo
        logger.warning("⚠️ Atenção: Falha na pré-inicialização do Firebase/AdModel durante o startup local. O servidor tentará iniciar, mas as rotas dependentes podem falhar.")
    
    # Para debug local, você pode querer debug=True. Em produção via Gunicorn, debug será False.
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)), debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true')
