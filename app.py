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
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "https://jade-lamington-63db57.netlify.app",
            "https://682d482f8ce48197b4658282--jade-lamington-63db57.netlify.app",
            "http://localhost:3000",
            "http://localhost:5000",
            "*"  # Mantido como fallback
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
            # Processar a chave privada para garantir o formato correto
            private_key = os.getenv("FIREBASE_PRIVATE_KEY", "")
            if private_key.startswith('"') and private_key.endswith('"'):
                private_key = private_key[1:-1]
            private_key = private_key.replace('\\n', '\n')
            
            # Criar credenciais a partir de variáveis de ambiente
            cred = credentials.Certificate({
                "type": os.getenv("FIREBASE_TYPE", "service_account"),
                "project_id": os.getenv("FIREBASE_PROJECT_ID"),
                "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
                "private_key": private_key,
                "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
                "client_id": os.getenv("FIREBASE_CLIENT_ID"),
                "auth_uri": os.getenv("FIREBASE_AUTH_URI", "https://accounts.google.com/o/oauth2/auth"),
                "token_uri": os.getenv("FIREBASE_TOKEN_URI", "https://oauth2.googleapis.com/token"),
                "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER", "https://www.googleapis.com/oauth2/v1/certs"),
                "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_CERT")
            })
            
            # Inicializar Firebase
            firebase_admin.initialize_app(cred, {
                'databaseURL': os.getenv('FIREBASE_DB_URL')
            })
            
            logger.info("✅ Firebase inicializado com sucesso usando variáveis de ambiente")
            return True
        except Exception as e:
            logger.error(f"🔥 ERRO Firebase: {str(e)}")
            return False
    return True

# Importar modelo de anúncios após configurar o path
try:
    from models.ads import AdModel
    logger.info("✅ Módulo models.ads importado com sucesso")
except ImportError as e:
    logger.error(f"❌ Erro ao importar models.ads: {str(e)}")
    # Verificar se o arquivo existe
    models_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models')
    ads_file = os.path.join(models_dir, 'ads.py')
    logger.info(f"Verificando existência do arquivo: {ads_file}")
    if os.path.exists(ads_file):
        logger.info(f"✅ Arquivo ads.py existe em: {ads_file}")
    else:
        logger.error(f"❌ Arquivo ads.py não encontrado em: {ads_file}")
        if os.path.exists(models_dir):
            logger.info(f"✅ Diretório models existe em: {models_dir}")
            logger.info(f"Arquivos no diretório models: {os.listdir(models_dir)}")
        else:
            logger.error(f"❌ Diretório models não encontrado em: {models_dir}")

# Instância do modelo de anúncios
ads_model = None

# Inicialização do modelo de anúncios
def init_ads_model():
    """Inicializa o modelo de anúncios"""
    global ads_model
    if init_firebase():
        try:
            ads_ref = db.reference('ads')
            ads_model = AdModel(ads_ref)
            return True
        except Exception as e:
            logger.error(f"🔥 ERRO ao inicializar modelo de anúncios: {str(e)}")
            return False
    return False

# Middleware para adicionar headers CORS em todas as respostas
@app.after_request
def add_cors_headers(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Requested-With,Accept,Origin')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

# Rotas para API de anúncios - CORRIGIDAS para compatibilidade com o frontend
@app.route('/api/banners', methods=['GET', 'OPTIONS'])
def get_banners():
    """Retorna todos os anúncios de banner"""
    if request.method == 'OPTIONS':
        return '', 200
        
    if not init_ads_model():
        return jsonify({"error": "Falha ao inicializar Firebase"}), 500
    
    try:
        ads = ads_model.get_banner_ads()
        return jsonify(ads)
    except Exception as e:
        logger.error(f"Erro ao obter banners: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/fullscreen', methods=['GET', 'OPTIONS'])
def get_fullscreen():
    """Retorna todos os anúncios de tela cheia"""
    if request.method == 'OPTIONS':
        return '', 200
        
    if not init_ads_model():
        return jsonify({"error": "Falha ao inicializar Firebase"}), 500
    
    try:
        ads = ads_model.get_fullscreen_ads()
        return jsonify(ads)
    except Exception as e:
        logger.error(f"Erro ao obter anúncios de tela cheia: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Rotas de compatibilidade para versões anteriores da API
@app.route('/api/ads/banner', methods=['GET', 'OPTIONS'])
def get_banner_ads_compat():
    """Rota de compatibilidade para versões anteriores"""
    if request.method == 'OPTIONS':
        return '', 200
    return get_banners()

@app.route('/api/ads/fullscreen', methods=['GET', 'OPTIONS'])
def get_fullscreen_ads_compat():
    """Rota de compatibilidade para versões anteriores"""
    if request.method == 'OPTIONS':
        return '', 200
    return get_fullscreen()

@app.route('/api/impression', methods=['POST', 'OPTIONS'])
def record_impression():
    """Registra uma impressão de anúncio"""
    if request.method == 'OPTIONS':
        return '', 200
        
    if not init_ads_model():
        return jsonify({"error": "Falha ao inicializar Firebase"}), 500
    
    try:
        data = request.get_json()
        ad_id = data.get('adId')
        ad_type = data.get('type', data.get('adType'))  # Compatibilidade com ambos os formatos
        
        if not ad_id or not ad_type:
            return jsonify({"error": "ID do anúncio e tipo são obrigatórios"}), 400
        
        if ad_type not in ['banner', 'fullscreen']:
            return jsonify({"error": "Tipo de anúncio inválido"}), 400
        
        success = ads_model.record_impression(ad_id, ad_type)
        
        if success:
            return jsonify({"success": True})
        else:
            return jsonify({"error": "Falha ao registrar impressão"}), 500
    except Exception as e:
        logger.error(f"Erro ao registrar impressão: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/click', methods=['POST', 'OPTIONS'])
def record_click():
    """Registra um clique em anúncio"""
    if request.method == 'OPTIONS':
        return '', 200
        
    if not init_ads_model():
        return jsonify({"error": "Falha ao inicializar Firebase"}), 500
    
    try:
        data = request.get_json()
        ad_id = data.get('adId')
        ad_type = data.get('type', data.get('adType'))  # Compatibilidade com ambos os formatos
        
        if not ad_id or not ad_type:
            return jsonify({"error": "ID do anúncio e tipo são obrigatórios"}), 400
        
        if ad_type not in ['banner', 'fullscreen']:
            return jsonify({"error": "Tipo de anúncio inválido"}), 400
        
        success = ads_model.record_click(ad_id, ad_type)
        
        if success:
            return jsonify({"success": True})
        else:
            return jsonify({"error": "Falha ao registrar clique"}), 500
    except Exception as e:
        logger.error(f"Erro ao registrar clique: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Rotas de compatibilidade para versões anteriores da API
@app.route('/api/ads/impression', methods=['POST', 'OPTIONS'])
def record_impression_compat():
    """Rota de compatibilidade para versões anteriores"""
    if request.method == 'OPTIONS':
        return '', 200
    return record_impression()

@app.route('/api/ads/click', methods=['POST', 'OPTIONS'])
def record_click_compat():
    """Rota de compatibilidade para versões anteriores"""
    if request.method == 'OPTIONS':
        return '', 200
    return record_click()

# Rotas para o dashboard
@app.route('/')
def dashboard_home():
    """Página inicial do dashboard"""
    if not init_ads_model():
        return render_template('error.html', message="Falha ao inicializar Firebase")
    
    try:
        metrics = ads_model.get_metrics()
        return render_template('dashboard.html', metrics=metrics)
    except Exception as e:
        logger.error(f"Erro ao carregar dashboard: {str(e)}")
        return render_template('error.html', message=str(e))

@app.route('/add-banner', methods=['GET', 'POST'])
def add_banner():
    """Adiciona um novo anúncio de banner"""
    if request.method == 'POST':
        if not init_ads_model():
            return render_template('error.html', message="Falha ao inicializar Firebase")
        
        try:
            image_url = request.form.get('imageUrl')
            link_url = request.form.get('linkUrl')
            
            if not image_url or not link_url:
                return render_template('add_banner.html', error="URL da imagem e URL de destino são obrigatórios")
            
            ad_id = ads_model.add_banner_ad(image_url, link_url)
            
            if ad_id:
                return redirect(url_for('dashboard_home'))
            else:
                return render_template('add_banner.html', error="Falha ao adicionar anúncio")
        except Exception as e:
            logger.error(f"Erro ao adicionar banner: {str(e)}")
            return render_template('add_banner.html', error=str(e))
    
    return render_template('add_banner.html')

@app.route('/edit-banner/<ad_id>', methods=['GET', 'POST'])
def edit_banner(ad_id):
    """Edita um anúncio de banner existente"""
    if not init_ads_model():
        return render_template('error.html', message="Falha ao inicializar Firebase")
    
    try:
        if request.method == 'POST':
            image_url = request.form.get('imageUrl')
            link_url = request.form.get('linkUrl')
            
            if not image_url or not link_url:
                return render_template('edit_banner.html', error="URL da imagem e URL de destino são obrigatórios", ad=ads_model.get_banner_ad(ad_id))
            
            success = ads_model.update_banner_ad(ad_id, image_url, link_url)
            
            if success:
                return redirect(url_for('dashboard_home'))
            else:
                return render_template('edit_banner.html', error="Falha ao atualizar anúncio", ad=ads_model.get_banner_ad(ad_id))
        
        # GET request - mostrar formulário de edição
        ad = ads_model.get_banner_ad(ad_id)
        if not ad:
            return render_template('error.html', message="Anúncio não encontrado")
        
        return render_template('edit_banner.html', ad=ad)
    except Exception as e:
        logger.error(f"Erro ao editar banner: {str(e)}")
        return render_template('error.html', message=str(e))

@app.route('/delete-banner/<ad_id>', methods=['POST'])
def delete_banner(ad_id):
    """Exclui um anúncio de banner"""
    if not init_ads_model():
        return jsonify({"error": "Falha ao inicializar Firebase"}), 500
    
    try:
        success = ads_model.delete_banner_ad(ad_id)
        
        if success:
            return redirect(url_for('dashboard_home'))
        else:
            return render_template('error.html', message="Falha ao excluir anúncio")
    except Exception as e:
        logger.error(f"Erro ao excluir banner: {str(e)}")
        return render_template('error.html', message=str(e))

@app.route('/add-fullscreen', methods=['GET', 'POST'])
def add_fullscreen():
    """Adiciona um novo anúncio de tela cheia"""
    if request.method == 'POST':
        if not init_ads_model():
            return render_template('error.html', message="Falha ao inicializar Firebase")
        
        try:
            image_url = request.form.get('imageUrl')
            link_url = request.form.get('linkUrl')
            
            if not image_url or not link_url:
                return render_template('add_fullscreen.html', error="URL da imagem e URL de destino são obrigatórios")
            
            ad_id = ads_model.add_fullscreen_ad(image_url, link_url)
            
            if ad_id:
                return redirect(url_for('dashboard_home'))
            else:
                return render_template('add_fullscreen.html', error="Falha ao adicionar anúncio")
        except Exception as e:
            logger.error(f"Erro ao adicionar anúncio de tela cheia: {str(e)}")
            return render_template('add_fullscreen.html', error=str(e))
    
    return render_template('add_fullscreen.html')

@app.route('/edit-fullscreen/<ad_id>', methods=['GET', 'POST'])
def edit_fullscreen(ad_id):
    """Edita um anúncio de tela cheia existente"""
    if not init_ads_model():
        return render_template('error.html', message="Falha ao inicializar Firebase")
    
    try:
        if request.method == 'POST':
            image_url = request.form.get('imageUrl')
            link_url = request.form.get('linkUrl')
            
            if not image_url or not link_url:
                return render_template('edit_fullscreen.html', error="URL da imagem e URL de destino são obrigatórios", ad=ads_model.get_fullscreen_ad(ad_id))
            
            success = ads_model.update_fullscreen_ad(ad_id, image_url, link_url)
            
            if success:
                return redirect(url_for('dashboard_home'))
            else:
                return render_template('edit_fullscreen.html', error="Falha ao atualizar anúncio", ad=ads_model.get_fullscreen_ad(ad_id))
        
        # GET request - mostrar formulário de edição
        ad = ads_model.get_fullscreen_ad(ad_id)
        if not ad:
            return render_template('error.html', message="Anúncio não encontrado")
        
        return render_template('edit_fullscreen.html', ad=ad)
    except Exception as e:
        logger.error(f"Erro ao editar anúncio de tela cheia: {str(e)}")
        return render_template('error.html', message=str(e))

@app.route('/delete-fullscreen/<ad_id>', methods=['POST'])
def delete_fullscreen(ad_id):
    """Exclui um anúncio de tela cheia"""
    if not init_ads_model():
        return jsonify({"error": "Falha ao inicializar Firebase"}), 500
    
    try:
        success = ads_model.delete_fullscreen_ad(ad_id)
        
        if success:
            return redirect(url_for('dashboard_home'))
        else:
            return render_template('error.html', message="Falha ao excluir anúncio")
    except Exception as e:
        logger.error(f"Erro ao excluir anúncio de tela cheia: {str(e)}")
        return render_template('error.html', message=str(e))

# Rota para verificação de saúde
@app.route('/health')
def health_check():
    """Verificação de saúde da aplicação"""
    return jsonify({"status": "healthy"}), 200

# Inicialização da aplicação
if __name__ == '__main__':
    if init_firebase():
        app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)), debug=False)
    else:
        logger.critical("❌ Servidor não iniciado: Firebase falhou")
