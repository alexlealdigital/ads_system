"""
Aplicação principal para o sistema de anúncios e dashboard
"""
import os
import logging
from flask import Flask, jsonify, request, render_template, redirect, url_for
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, db

# Importar modelo de anúncios
from models.ads import AdModel

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicialização da aplicação Flask
app = Flask(__name__)

# Configuração de CORS
CORS(app, resources={
    r"/api/*": {
        "origins": ["*"], # Para produção, restrinja a origens específicas
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True,
        "max_age": 86400
    }
})

# Inicialização do Firebase
def init_firebase():
    """Inicializa a conexão com o Firebase"""
    if not firebase_admin._apps: # Evita reinicialização se já estiver inicializado
        try:
            # Usar arquivo JSON em vez de variáveis de ambiente para credenciais
            cred = credentials.Certificate('firebase-credentials.json')
            firebase_admin.initialize_app(cred, {
                'databaseURL': 'https://deepfish-counter-default-rtdb.firebaseio.com' # Sua Database URL
            })
            logger.info("✅ Firebase inicializado")
            return True
        except Exception as e:
            logger.error(f"🔥 ERRO Firebase: {str(e)}")
            return False
    return True

# Instância do modelo de anúncios
ads_model = None

# Inicialização do modelo de anúncios
def init_ads_model():
    """Inicializa o modelo de anúncios"""
    global ads_model
    if init_firebase(): # Garante que o Firebase está inicializado
        if ads_model is None: # Inicializa o modelo apenas se ainda não foi
            ads_ref = db.reference('ads') # Referência para o nó 'ads' no Firebase
            ads_model = AdModel(ads_ref)
        return True
    return False

# --- Rotas para API de anúncios ---
@app.route('/api/ads/banner', methods=['GET'])
def get_banner_ads():
    """Retorna todos os anúncios de banner"""
    if not init_ads_model():
        return jsonify({"error": "Falha ao inicializar Firebase"}), 500
    
    try:
        ads = ads_model.get_banner_ads()
        return jsonify({"ads": ads})
    except Exception as e:
        logger.error(f"Erro ao obter banners: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/ads/fullscreen', methods=['GET'])
def get_fullscreen_ads():
    """Retorna todos os anúncios de tela cheia"""
    if not init_ads_model():
        return jsonify({"error": "Falha ao inicializar Firebase"}), 500
    
    try:
        ads = ads_model.get_fullscreen_ads()
        return jsonify({"ads": ads})
    except Exception as e:
        logger.error(f"Erro ao obter anúncios de tela cheia: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/ads/impression', methods=['POST', 'OPTIONS'])
def record_impression():
    """Registra uma impressão de anúncio"""
    if request.method == 'OPTIONS': # Handle CORS preflight
        return '', 200
        
    if not init_ads_model():
        return jsonify({"error": "Falha ao inicializar Firebase"}), 500
    
    try:
        data = request.get_json()
        ad_id = data.get('adId')
        ad_type = data.get('adType') # 'banner' ou 'fullscreen'
        
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

@app.route('/api/ads/click', methods=['POST', 'OPTIONS'])
def record_click():
    """Registra um clique em anúncio"""
    if request.method == 'OPTIONS': # Handle CORS preflight
        return '', 200
        
    if not init_ads_model():
        return jsonify({"error": "Falha ao inicializar Firebase"}), 500
    
    try:
        data = request.get_json()
        ad_id = data.get('adId')
        ad_type = data.get('adType') # 'banner' ou 'fullscreen'
        
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

# --- Rotas para o dashboard ---
@app.route('/')
def dashboard_home():
    """Página inicial do dashboard"""
    if not init_ads_model():
        return render_template('error.html', message="Falha ao inicializar Firebase")
    
    try:
        metrics = ads_model.get_metrics()
        # Você também pode querer buscar a lista de anúncios aqui para exibir no dashboard
        banner_ads = ads_model.get_banner_ads()
        fullscreen_ads = ads_model.get_fullscreen_ads()
        return render_template('dashboard.html', metrics=metrics, banner_ads=banner_ads, fullscreen_ads=fullscreen_ads)
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
    
    return render_template('add_banner.html') # GET request mostra o formulário

@app.route('/edit-banner/<ad_id>', methods=['GET', 'POST'])
def edit_banner(ad_id):
    """Edita um anúncio de banner existente"""
    if not init_ads_model():
        return render_template('error.html', message="Falha ao inicializar Firebase")
    
    try:
        ad = ads_model.get_banner_ad(ad_id) # Busca o anúncio primeiro para POST e GET
        if not ad:
             return render_template('error.html', message="Anúncio não encontrado")

        if request.method == 'POST':
            image_url = request.form.get('imageUrl')
            link_url = request.form.get('linkUrl')
            
            if not image_url or not link_url:
                # Passa o 'ad' para o template para preencher os campos mesmo em erro
                return render_template('edit_banner.html', error="URL da imagem e URL de destino são obrigatórios", ad=ad) 
            
            success = ads_model.update_banner_ad(ad_id, image_url, link_url)
            
            if success:
                return redirect(url_for('dashboard_home'))
            else:
                return render_template('edit_banner.html', error="Falha ao atualizar anúncio", ad=ad)
        
        # GET request - mostrar formulário de edição
        return render_template('edit_banner.html', ad=ad)
    except Exception as e:
        logger.error(f"Erro ao editar banner: {str(e)}")
        return render_template('error.html', message=str(e))

@app.route('/delete-banner/<ad_id>', methods=['POST'])
def delete_banner(ad_id):
    """Exclui um anúncio de banner"""
    # Para exclusão via dashboard, geralmente é um POST de um formulário
    if not init_ads_model():
        # Se chamado via JS esperando JSON:
        # return jsonify({"error": "Falha ao inicializar Firebase"}), 500
        # Se for de um form submit que espera HTML:
        return render_template('error.html', message="Falha ao inicializar Firebase")

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
    
    return render_template('add_fullscreen.html') # GET request

@app.route('/edit-fullscreen/<ad_id>', methods=['GET', 'POST'])
def edit_fullscreen(ad_id):
    """Edita um anúncio de tela cheia existente"""
    if not init_ads_model():
        return render_template('error.html', message="Falha ao inicializar Firebase")
    
    try:
        ad = ads_model.get_fullscreen_ad(ad_id) # Busca o anúncio
        if not ad:
            return render_template('error.html', message="Anúncio não encontrado")

        if request.method == 'POST':
            image_url = request.form.get('imageUrl')
            link_url = request.form.get('linkUrl')
            
            if not image_url or not link_url:
                return render_template('edit_fullscreen.html', error="URL da imagem e URL de destino são obrigatórios", ad=ad)
            
            success = ads_model.update_fullscreen_ad(ad_id, image_url, link_url)
            
            if success:
                return redirect(url_for('dashboard_home'))
            else:
                return render_template('edit_fullscreen.html', error="Falha ao atualizar anúncio", ad=ad)
        
        # GET request - mostrar formulário de edição
        return render_template('edit_fullscreen.html', ad=ad)
    except Exception as e:
        logger.error(f"Erro ao editar anúncio de tela cheia: {str(e)}")
        return render_template('error.html', message=str(e))

@app.route('/delete-fullscreen/<ad_id>', methods=['POST'])
def delete_fullscreen(ad_id):
    """Exclui um anúncio de tela cheia"""
    if not init_ads_model():
        return render_template('error.html', message="Falha ao inicializar Firebase")
    
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
    # Tenta inicializar o Firebase e o AdModel uma vez no início
    if init_ads_model():
        # O host 0.0.0.0 torna a aplicação acessível externamente na rede
        # PORT é pego de variáveis de ambiente, ou 5000 como padrão
        # debug=True é útil para desenvolvimento, mas deve ser False em produção
        app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)), debug=True)
    else:
        logger.critical("❌ Servidor não iniciado: Firebase ou AdModel falhou na inicialização")
