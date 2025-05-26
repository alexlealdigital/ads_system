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
        
        def get_banner_by_id(self, banner_id):
            for banner in self.banners:
                if banner['id'] == banner_id:
                    return banner
            return None
        
        def get_fullscreen_by_id(self, ad_id):
            for ad in self.fullscreen_ads:
                if ad['id'] == ad_id:
                    return ad
            return None
        
        def update_banner(self, banner_id, title, image_url, target_url):
            for i, banner in enumerate(self.banners):
                if banner['id'] == banner_id:
                    self.banners[i] = {
                        'id': banner_id,
                        'title': title,
                        'imageUrl': image_url,
                        'targetUrl': target_url,
                        'createdAt': banner.get('createdAt', datetime.datetime.now().isoformat()),
                        'lastUpdated': datetime.datetime.now().isoformat()
                    }
                    self.save_data()
                    return True
            return False
        
        def update_fullscreen_ad(self, ad_id, title, image_url, target_url):
            for i, ad in enumerate(self.fullscreen_ads):
                if ad['id'] == ad_id:
                    self.fullscreen_ads[i] = {
                        'id': ad_id,
                        'title': title,
                        'imageUrl': image_url,
                        'targetUrl': target_url,
                        'createdAt': ad.get('createdAt', datetime.datetime.now().isoformat()),
                        'lastUpdated': datetime.datetime.now().isoformat()
                    }
                    self.save_data()
                    return True
            return False
        
        def delete_banner(self, banner_id):
            for i, banner in enumerate(self.banners):
                if banner['id'] == banner_id:
                    del self.banners[i]
                    self.save_data()
                    return True
            return False
        
        def delete_fullscreen_ad(self, ad_id):
            for i, ad in enumerate(self.fullscreen_ads):
                if ad['id'] == ad_id:
                    del self.fullscreen_ads[i]
                    self.save_data()
                    return True
            return False
        
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
            banner_metrics = []
            for banner in self.banners:
                banner_id = banner['id']
                key = f"banner_{banner_id}"
                banner_with_metrics = banner.copy()
                banner_with_metrics.update({
                    'impressions': self.impressions.get(key, 0),
                    'clicks': self.clicks.get(key, 0),
                    'linkUrl': banner.get('targetUrl', '')  # Garantir compatibilidade com ambos os campos
                })
                banner_metrics.append(banner_with_metrics)
            
            fullscreen_metrics = []
            for ad in self.fullscreen_ads:
                ad_id = ad['id']
                key = f"fullscreen_{ad_id}"
                ad_with_metrics = ad.copy()
                ad_with_metrics.update({
                    'impressions': self.impressions.get(key, 0),
                    'clicks': self.clicks.get(key, 0),
                    'linkUrl': ad.get('targetUrl', '')  # Garantir compatibilidade com ambos os campos
                })
                fullscreen_metrics.append(ad_with_metrics)
            
            return {
                'banner': {
                    'ads': banner_metrics,
                    'ads_count': len(banner_metrics),
                    'total_impressions': sum(ad['impressions'] for ad in banner_metrics),
                    'total_clicks': sum(ad['clicks'] for ad in banner_metrics),
                    'ctr': self._calculate_ctr(sum(ad['impressions'] for ad in banner_metrics), 
                                              sum(ad['clicks'] for ad in banner_metrics))
                },
                'fullscreen': {
                    'ads': fullscreen_metrics,
                    'ads_count': len(fullscreen_metrics),
                    'total_impressions': sum(ad['impressions'] for ad in fullscreen_metrics),
                    'total_clicks': sum(ad['clicks'] for ad in fullscreen_metrics),
                    'ctr': self._calculate_ctr(sum(ad['impressions'] for ad in fullscreen_metrics), 
                                              sum(ad['clicks'] for ad in fullscreen_metrics))
                }
            }
        
        def _calculate_ctr(self, impressions, clicks):
            if impressions > 0:
                return round((clicks / impressions) * 100, 2)
            return 0.0

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
            "https://placehold.co/360x640/blue/white?text=Anuncio+Tela+Cheia", 
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
    ad_id = data.get('id')
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
    ad_id = data.get('id')
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

# Rotas para adicionar anúncios
@app.route('/add-banner', methods=['GET', 'POST'])
def add_banner():
    if request.method == 'POST':
        title = request.form.get('title')
        image_url = request.form.get('imageUrl')
        target_url = request.form.get('targetUrl')
        
        if not title or not image_url or not target_url:
            return render_template('add_banner.html', error="Todos os campos são obrigatórios")
        
        ads_model.add_banner(title, image_url, target_url)
        return redirect(url_for('dashboard'))
    
    return render_template('add_banner.html')

@app.route('/add-fullscreen', methods=['GET', 'POST'])
def add_fullscreen():
    if request.method == 'POST':
        title = request.form.get('title')
        image_url = request.form.get('imageUrl')
        target_url = request.form.get('targetUrl')
        
        if not title or not image_url or not target_url:
            return render_template('add_fullscreen.html', error="Todos os campos são obrigatórios")
        
        ads_model.add_fullscreen_ad(title, image_url, target_url)
        return redirect(url_for('dashboard'))
    
    return render_template('add_fullscreen.html')

# Rotas para editar anúncios
@app.route('/edit-banner/<banner_id>', methods=['GET', 'POST'])
def edit_banner(banner_id):
    if not ads_model:
        return render_template('error.html', message="Modelo de anúncios não inicializado")
    
    banner = ads_model.get_banner_by_id(banner_id)
    if not banner:
        return render_template('error.html', message=f"Banner com ID {banner_id} não encontrado")
    
    if request.method == 'POST':
        title = request.form.get('title')
        image_url = request.form.get('imageUrl')
        target_url = request.form.get('targetUrl')
        
        if not title or not image_url or not target_url:
            return render_template('edit_banner.html', banner=banner, error="Todos os campos são obrigatórios")
        
        success = ads_model.update_banner(banner_id, title, image_url, target_url)
        if success:
            return redirect(url_for('dashboard'))
        else:
            return render_template('error.html', message=f"Falha ao atualizar banner com ID {banner_id}")
    
    return render_template('edit_banner.html', banner=banner)

@app.route('/edit-fullscreen/<ad_id>', methods=['GET', 'POST'])
def edit_fullscreen(ad_id):
    if not ads_model:
        return render_template('error.html', message="Modelo de anúncios não inicializado")
    
    ad = ads_model.get_fullscreen_by_id(ad_id)
    if not ad:
        return render_template('error.html', message=f"Anúncio de tela cheia com ID {ad_id} não encontrado")
    
    if request.method == 'POST':
        title = request.form.get('title')
        image_url = request.form.get('imageUrl')
        target_url = request.form.get('targetUrl')
        
        if not title or not image_url or not target_url:
            return render_template('edit_fullscreen.html', ad=ad, error="Todos os campos são obrigatórios")
        
        success = ads_model.update_fullscreen_ad(ad_id, title, image_url, target_url)
        if success:
            return redirect(url_for('dashboard'))
        else:
            return render_template('error.html', message=f"Falha ao atualizar anúncio de tela cheia com ID {ad_id}")
    
    return render_template('edit_fullscreen.html', ad=ad)

# Rotas para excluir anúncios
@app.route('/delete-banner/<banner_id>', methods=['POST'])
def delete_banner(banner_id):
    if not ads_model:
        return render_template('error.html', message="Modelo de anúncios não inicializado")
    
    success = ads_model.delete_banner(banner_id)
    if success:
        return redirect(url_for('dashboard'))
    else:
        return render_template('error.html', message=f"Falha ao excluir banner com ID {banner_id}")

@app.route('/delete-fullscreen/<ad_id>', methods=['POST'])
def delete_fullscreen(ad_id):
    if not ads_model:
        return render_template('error.html', message="Modelo de anúncios não inicializado")
    
    success = ads_model.delete_fullscreen_ad(ad_id)
    if success:
        return redirect(url_for('dashboard'))
    else:
        return render_template('error.html', message=f"Falha ao excluir anúncio de tela cheia com ID {ad_id}")

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
    app.run(debug=True, host='0.0.0.0')
