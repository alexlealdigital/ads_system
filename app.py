"""
Aplicação principal para o sistema de anúncios.
Gerencia banners e anúncios de tela cheia.
Versão simplificada com armazenamento local.
"""
import os
import sys
import json
import logging
from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_cors import CORS

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('app')

# Inicializar Flask
app = Flask(__name__)

# Configurar CORS para permitir requisições de qualquer origem
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Adicionar headers CORS em todas as respostas
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE,OPTIONS'
    return response

# Garantir que o diretório atual esteja no PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Tentar importar o modelo de anúncios
try:
    from models.ads import AdModel
    logger.info("✅ Módulo models.ads importado com sucesso.")
except ImportError as e:
    logger.error(f"❌ Erro ao importar models.ads: {str(e)}")
    # Tentar importação alternativa
    try:
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        from models.ads import AdModel
        logger.info("✅ Módulo models.ads importado com sucesso (importação alternativa).")
    except ImportError as e:
        logger.error(f"❌ Erro na importação alternativa: {str(e)}")
        
        # Verificar existência do arquivo
        models_dir = os.path.join(os.path.dirname(__file__), 'models')
        ads_file = os.path.join(models_dir, 'ads.py')
        
        if os.path.exists(ads_file):
            logger.info(f"✅ Arquivo ads.py encontrado em: {ads_file}")
        else:
            logger.error(f"❌ Arquivo ads.py não encontrado em: {ads_file}")
            
            if os.path.exists(models_dir):
                logger.info(f"✅ Diretório models existe em: {models_dir}")
                logger.info(f"Arquivos no diretório models: {os.listdir(models_dir)}")
            else:
                logger.error(f"❌ Diretório models não encontrado em: {os.path.dirname(__file__)}")

# Inicializar modelo de anúncios
ad_model = None
try:
    # Criar diretório de dados se não existir
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    # Inicializar modelo com diretório de dados local
    ad_model = AdModel(data_dir=data_dir)
    logger.info("✅ Modelo de anúncios inicializado com sucesso.")
    
    # Adicionar alguns banners de exemplo se não existirem
    banners = ad_model.get_banners()
    if not banners:
        ad_model.add_banner(
            "Banner de Exemplo",
            "https://i.imgur.com/XqYGzDC.png",
            "https://alexlealdigital.github.io"
        )
        logger.info("✅ Banner de exemplo adicionado.")
    
    # Adicionar anúncios de tela cheia de exemplo se não existirem
    fullscreen_ads = ad_model.get_fullscreen_ads()
    if not fullscreen_ads:
        ad_model.add_fullscreen_ad(
            "Anúncio de Tela Cheia de Exemplo",
            "https://i.imgur.com/XqYGzDC.png",
            "https://alexlealdigital.github.io"
        )
        logger.info("✅ Anúncio de tela cheia de exemplo adicionado.")
except Exception as e:
    logger.error(f"🔥 ERRO ao inicializar o modelo de anúncios: {str(e)}")

# Rotas da API
@app.route('/api/banners', methods=['GET', 'OPTIONS'])
def get_banners():
    """
    Obtém todos os banners.
    """
    if request.method == 'OPTIONS':
        return '', 200
    
    if not ad_model:
        return jsonify({"error": "Modelo de anúncios não inicializado"}), 500
    
    try:
        banners = ad_model.get_banners()
        return jsonify(banners)
    except Exception as e:
        logger.error(f"Erro ao obter banners: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/fullscreen', methods=['GET', 'OPTIONS'])
def get_fullscreen_ads():
    """
    Obtém todos os anúncios de tela cheia.
    """
    if request.method == 'OPTIONS':
        return '', 200
    
    if not ad_model:
        return jsonify({"error": "Modelo de anúncios não inicializado"}), 500
    
    try:
        ads = ad_model.get_fullscreen_ads()
        return jsonify(ads)
    except Exception as e:
        logger.error(f"Erro ao obter anúncios de tela cheia: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Manter compatibilidade com rotas antigas
@app.route('/api/ads/banner', methods=['GET', 'OPTIONS'])
def get_banners_compat():
    """
    Rota de compatibilidade para obter banners.
    """
    return get_banners()

@app.route('/api/ads/fullscreen', methods=['GET', 'OPTIONS'])
def get_fullscreen_ads_compat():
    """
    Rota de compatibilidade para obter anúncios de tela cheia.
    """
    return get_fullscreen_ads()

@app.route('/api/impression', methods=['POST', 'OPTIONS'])
def record_impression():
    """
    Registra uma impressão de anúncio.
    """
    if request.method == 'OPTIONS':
        return '', 200
    
    if not ad_model:
        return jsonify({"error": "Modelo de anúncios não inicializado"}), 500
    
    try:
        data = request.json
        ad_id = data.get('adId')
        ad_type = data.get('type') or data.get('adType')  # Compatibilidade com diferentes formatos
        
        if not ad_id or not ad_type:
            return jsonify({"error": "ID do anúncio e tipo são obrigatórios"}), 400
        
        success = ad_model.record_impression(ad_id, ad_type)
        
        if success:
            return jsonify({"success": True})
        else:
            return jsonify({"error": "Falha ao registrar impressão"}), 500
    except Exception as e:
        logger.error(f"Erro ao registrar impressão: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/click', methods=['POST', 'OPTIONS'])
def record_click():
    """
    Registra um clique em anúncio.
    """
    if request.method == 'OPTIONS':
        return '', 200
    
    if not ad_model:
        return jsonify({"error": "Modelo de anúncios não inicializado"}), 500
    
    try:
        data = request.json
        ad_id = data.get('adId')
        ad_type = data.get('type') or data.get('adType')  # Compatibilidade com diferentes formatos
        
        if not ad_id or not ad_type:
            return jsonify({"error": "ID do anúncio e tipo são obrigatórios"}), 400
        
        success = ad_model.record_click(ad_id, ad_type)
        
        if success:
            return jsonify({"success": True})
        else:
            return jsonify({"error": "Falha ao registrar clique"}), 500
    except Exception as e:
        logger.error(f"Erro ao registrar clique: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Rotas do dashboard
@app.route('/')
def dashboard():
    """
    Página principal do dashboard.
    """
    if not ad_model:
        return render_template('error.html', error="Modelo de anúncios não inicializado")
    
    try:
        banner_stats = ad_model.get_banner_stats()
        fullscreen_stats = ad_model.get_fullscreen_stats()
        
        return render_template('dashboard.html', 
                              banners=banner_stats, 
                              fullscreen_ads=fullscreen_stats)
    except Exception as e:
        logger.error(f"Erro ao renderizar dashboard: {str(e)}")
        return render_template('error.html', error=str(e))

@app.route('/add/banner', methods=['GET', 'POST'])
def add_banner():
    """
    Adiciona um novo banner.
    """
    if not ad_model:
        return render_template('error.html', error="Modelo de anúncios não inicializado")
    
    if request.method == 'POST':
        try:
            title = request.form.get('title')
            image_url = request.form.get('imageUrl')
            target_url = request.form.get('targetUrl')
            
            if not title or not image_url or not target_url:
                return render_template('add_banner.html', error="Todos os campos são obrigatórios")
            
            ad_model.add_banner(title, image_url, target_url)
            
            return redirect(url_for('dashboard'))
        except Exception as e:
            logger.error(f"Erro ao adicionar banner: {str(e)}")
            return render_template('add_banner.html', error=str(e))
    
    return render_template('add_banner.html')

@app.route('/add/fullscreen', methods=['GET', 'POST'])
def add_fullscreen():
    """
    Adiciona um novo anúncio de tela cheia.
    """
    if not ad_model:
        return render_template('error.html', error="Modelo de anúncios não inicializado")
    
    if request.method == 'POST':
        try:
            title = request.form.get('title')
            image_url = request.form.get('imageUrl')
            target_url = request.form.get('targetUrl')
            
            if not title or not image_url or not target_url:
                return render_template('add_fullscreen.html', error="Todos os campos são obrigatórios")
            
            ad_model.add_fullscreen_ad(title, image_url, target_url)
            
            return redirect(url_for('dashboard'))
        except Exception as e:
            logger.error(f"Erro ao adicionar anúncio de tela cheia: {str(e)}")
            return render_template('add_fullscreen.html', error=str(e))
    
    return render_template('add_fullscreen.html')

# Iniciar aplicação
if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')
