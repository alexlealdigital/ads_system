"""
Aplicação principal para o sistema de anúncios.
Gerencia banners e anúncios de tela cheia.
"""
import os
import sys
import json
import logging
import datetime
from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_cors import CORS

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('app')

# Inicializar Flask
app = Flask(__name__)
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
    logger.error(f"❌ Erro ao importar models.ads: {e}")
    # Definir classe AdModel localmente como fallback
    class AdModel:
        def __init__(self, data_file=None):
            self.banners = []
            self.fullscreen_ads = []
            self.impressions = {}
            self.clicks = {}
            self.data_file = data_file or os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'ads_data.json')
            self.ensure_data_dir()
            self.load_data()
        
        def ensure_data_dir(self):
            data_dir = os.path.dirname(self.data_file)
            if not os.path.exists(data_dir):
                os.makedirs(data_dir)
        
        def load_data(self):
            if os.path.exists(self.data_file):
                try:
                    with open(self.data_file, 'r') as f:
                        data = json.load(f)
                        self.banners = data.get('banners', [])
                        self.fullscreen_ads = data.get('fullscreen_ads', [])
                        self.impressions = data.get('impressions', {})
                        self.clicks = data.get('clicks', {})
                except Exception as e:
                    logger.error(f"❌ Erro ao carregar dados: {e}")
        
        def save_data(self):
            try:
                with open(self.data_file, 'w') as f:
                    json.dump({
                        'banners': self.banners,
                        'fullscreen_ads': self.fullscreen_ads,
                        'impressions': self.impressions,
                        'clicks': self.clicks
                    }, f, indent=2)
            except Exception as e:
                logger.error(f"❌ Erro ao salvar dados: {e}")
        
        def add_banner(self, title, image_url, target_url):
            banner_id = str(len(self.banners) + 1)
            banner = {
                'id': banner_id,
                'title': title,
                'imageUrl': image_url,
                'targetUrl': target_url,
                'createdAt': datetime.datetime.now().isoformat()
            }
            self.banners.append(banner)
            self.impressions[f"banner_{banner_id}"] = 0
            self.clicks[f"banner_{banner_id}"] = 0
            self.save_data()
            return banner
        
        def add_fullscreen_ad(self, title, image_url, target_url):
            ad_id = str(len(self.fullscreen_ads) + 1)
            ad = {
                'id': ad_id,
                'title': title,
                'imageUrl': image_url,
                'targetUrl': target_url,
                'createdAt': datetime.datetime.now().isoformat()
            }
            self.fullscreen_ads.append(ad)
            self.impressions[f"fullscreen_{ad_id}"] = 0
            self.clicks[f"fullscreen_{ad_id}"] = 0
            self.save_data()
            return ad
        
        def get_banners(self):
            return self.banners
        
        def get_fullscreen_ads(self):
            return self.fullscreen_ads
        
        def record_impression(self, ad_id, ad_type):
            key = f"{ad_type}_{ad_id}"
            self.impressions[key] = self.impressions.get(key, 0) + 1
            self.save_data()
            return self.impressions[key]
        
        def record_click(self, ad_id, ad_type):
            key = f"{ad_type}_{ad_id}"
            self.clicks[key] = self.clicks.get(key, 0) + 1
            self.save_data()
            return self.clicks[key]
        
        def get_metrics(self):
            # Preparar métricas para banners
            banner_ads = []
            total_banner_impressions = 0
            total_banner_clicks = 0
            
            for banner in self.banners:
                banner_id = banner['id']
                key = f"banner_{banner_id}"
                impressions = self.impressions.get(key, 0)
                clicks = self.clicks.get(key, 0)
                
                total_banner_impressions += impressions
                total_banner_clicks += clicks
                
                banner_with_metrics = banner.copy()
                banner_with_metrics['impressions'] = impressions
                banner_with_metrics['clicks'] = clicks
                banner_with_metrics['linkUrl'] = banner['targetUrl']  # Compatibilidade com o template
                banner_with_metrics['lastShown'] = banner.get('createdAt', '')
                
                banner_ads.append(banner_with_metrics)
            
            # Calcular CTR para banners
            banner_ctr = 0
            if total_banner_impressions > 0:
                banner_ctr = round((total_banner_clicks / total_banner_impressions) * 100, 2)
            
            # Preparar métricas para anúncios de tela cheia
            fullscreen_ads = []
            total_fullscreen_impressions = 0
            total_fullscreen_clicks = 0
            
            for ad in self.fullscreen_ads:
                ad_id = ad['id']
                key = f"fullscreen_{ad_id}"
                impressions = self.impressions.get(key, 0)
                clicks = self.clicks.get(key, 0)
                
                total_fullscreen_impressions += impressions
                total_fullscreen_clicks += clicks
                
                ad_with_metrics = ad.copy()
                ad_with_metrics['impressions'] = impressions
                ad_with_metrics['clicks'] = clicks
                ad_with_metrics['linkUrl'] = ad['targetUrl']  # Compatibilidade com o template
                ad_with_metrics['lastShown'] = ad.get('createdAt', '')
                
                fullscreen_ads.append(ad_with_metrics)
            
            # Calcular CTR para anúncios de tela cheia
            fullscreen_ctr = 0
            if total_fullscreen_impressions > 0:
                fullscreen_ctr = round((total_fullscreen_clicks / total_fullscreen_impressions) * 100, 2)
            
            # Estrutura final de métricas
            return {
                'banner': {
                    'ads': banner_ads,
                    'ads_count': len(self.banners),
                    'total_impressions': total_banner_impressions,
                    'total_clicks': total_banner_clicks,
                    'ctr': banner_ctr
                },
                'fullscreen': {
                    'ads': fullscreen_ads,
                    'ads_count': len(self.fullscreen_ads),
                    'total_impressions': total_fullscreen_impressions,
                    'total_clicks': total_fullscreen_clicks,
                    'ctr': fullscreen_ctr
                }
            }

# Inicializar modelo de anúncios
try:
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    data_file = os.path.join(data_dir, 'ads_data.json')
    ads_model = AdModel(data_file)
    logger.info("✅ Modelo de anúncios inicializado com sucesso.")
    
    # Adicionar banners e anúncios de exemplo se não existirem
    if not ads_model.get_banners():
        ads_model.add_banner(
            "Banner de Exemplo", 
            "https://placehold.co/360x47/orange/white?text=Anuncio+Exemplo", 
            "https://alexlealdigital.github.io"
        )
        logger.info("✅ Banner de exemplo adicionado.")
    
    if not ads_model.get_fullscreen_ads():
        ads_model.add_fullscreen_ad(
            "Anúncio de Tela Cheia de Exemplo", 
            "https://placehold.co/1080x1920/blue/white?text=Anuncio+Tela+Cheia", 
            "https://alexlealdigital.github.io"
        )
        logger.info("✅ Anúncio de tela cheia de exemplo adicionado.")
except Exception as e:
    logger.error(f"🔥 ERRO ao inicializar o modelo de anúncios: {e}")
    ads_model = None

# Rotas da API
@app.route('/api/banners', methods=['GET', 'OPTIONS'])
def get_banners():
    if request.method == 'OPTIONS':
        return '', 200
    
    if not ads_model:
        return jsonify([]), 500
    
    return jsonify(ads_model.get_banners())

@app.route('/api/fullscreen', methods=['GET', 'OPTIONS'])
def get_fullscreen_ads():
    if request.method == 'OPTIONS':
        return '', 200
    
    if not ads_model:
        return jsonify([]), 500
    
    return jsonify(ads_model.get_fullscreen_ads())

# Rotas de compatibilidade (antigas)
@app.route('/api/ads/banner', methods=['GET', 'OPTIONS'])
def get_banners_compat():
    return get_banners()

@app.route('/api/ads/fullscreen', methods=['GET', 'OPTIONS'])
def get_fullscreen_ads_compat():
    return get_fullscreen_ads()

@app.route('/api/impression', methods=['POST', 'OPTIONS'])
def record_impression():
    if request.method == 'OPTIONS':
        return '', 200
    
    if not ads_model:
        return jsonify({"error": "Modelo de anúncios não inicializado"}), 500
    
    data = request.json
    ad_id = data.get('adId')
    ad_type = data.get('type') or data.get('adType')
    
    if not ad_id or not ad_type:
        return jsonify({"error": "ID e tipo do anúncio são obrigatórios"}), 400
    
    count = ads_model.record_impression(ad_id, ad_type)
    return jsonify({"count": count})

@app.route('/api/click', methods=['POST', 'OPTIONS'])
def record_click():
    if request.method == 'OPTIONS':
        return '', 200
    
    if not ads_model:
        return jsonify({"error": "Modelo de anúncios não inicializado"}), 500
    
    data = request.json
    ad_id = data.get('adId')
    ad_type = data.get('type') or data.get('adType')
    
    if not ad_id or not ad_type:
        return jsonify({"error": "ID e tipo do anúncio são obrigatórios"}), 400
    
    count = ads_model.record_click(ad_id, ad_type)
    return jsonify({"count": count})

# Rotas do dashboard
@app.route('/')
def dashboard():
    try:
        if not ads_model:
            return render_template('error.html', message="Modelo de anúncios não inicializado")
        
        metrics = ads_model.get_metrics()
        return render_template('dashboard.html', metrics=metrics)
    except Exception as e:
        logger.error(f"Erro ao renderizar dashboard: {e}")
        return render_template('error.html', message=str(e))

@app.route('/add/banner', methods=['GET', 'POST'])
def add_banner():
    if request.method == 'POST':
        title = request.form.get('title')
        image_url = request.form.get('imageUrl')
        target_url = request.form.get('targetUrl')
        
        if not title or not image_url or not target_url:
            return render_template('error.html', message="Todos os campos são obrigatórios")
        
        ads_model.add_banner(title, image_url, target_url)
        return redirect(url_for('dashboard'))
    
    return render_template('add_banner.html')

@app.route('/add/fullscreen', methods=['GET', 'POST'])
def add_fullscreen():
    if request.method == 'POST':
        title = request.form.get('title')
        image_url = request.form.get('imageUrl')
        target_url = request.form.get('targetUrl')
        
        if not title or not image_url or not target_url:
            return render_template('error.html', message="Todos os campos são obrigatórios")
        
        ads_model.add_fullscreen_ad(title, image_url, target_url)
        return redirect(url_for('dashboard'))
    
    return render_template('add_fullscreen.html')

# Rota para diagnóstico
@app.route('/debug')
def debug():
    info = {
        "app_dir": os.path.dirname(os.path.abspath(__file__)),
        "current_dir": os.getcwd(),
        "python_path": sys.path,
        "ads_model": str(ads_model),
        "banners": ads_model.get_banners() if ads_model else [],
        "fullscreen_ads": ads_model.get_fullscreen_ads() if ads_model else [],
        "metrics": ads_model.get_metrics() if ads_model else {}
    }
    return jsonify(info)

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')
