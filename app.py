"""
Aplicação principal para o sistema de anúncios.
Gerencia banners e anúncios de tela cheia com suporte completo a edição e exclusão.
"""
import os
import sys
import json
import logging
import datetime
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_cors import CORS

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('app')

# Inicializar Flask
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'ads_system_secret_key')
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
        def __init__(self, data_dir='data', data_file=None):
            self.data_dir = data_dir
            self.banners_file = os.path.join(data_dir, 'banners.json')
            self.fullscreen_file = os.path.join(data_dir, 'fullscreen.json')
            self.stats_file = os.path.join(data_dir, 'stats.json')
            
            # Criar diretório de dados se não existir
            if not os.path.exists(data_dir):
                os.makedirs(data_dir)
            
            # Inicializar arquivos se não existirem
            self._init_file(self.banners_file, [])
            self._init_file(self.fullscreen_file, [])
            self._init_file(self.stats_file, {'impressions': {}, 'clicks': {}})
        
        def _init_file(self, file_path, default_data):
            if not os.path.exists(file_path):
                with open(file_path, 'w') as f:
                    json.dump(default_data, f)
        
        def _load_data(self, file_path):
            try:
                with open(file_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Erro ao carregar dados de {file_path}: {str(e)}")
                if file_path.endswith('stats.json'):
                    return {'impressions': {}, 'clicks': {}}
                return []
        
        def _save_data(self, file_path, data):
            try:
                with open(file_path, 'w') as f:
                    json.dump(data, f, indent=2)
                return True
            except Exception as e:
                logger.error(f"Erro ao salvar dados em {file_path}: {str(e)}")
                return False
        
        def get_banners(self):
            return self._load_data(self.banners_file)
        
        def get_fullscreen_ads(self):
            return self._load_data(self.fullscreen_file)
        
        def add_banner(self, title, image_url, target_url):
            banners = self.get_banners()
            
            # Gerar ID único
            banner_id = str(len(banners) + 1)
            
            # Criar banner
            banner = {
                'id': banner_id,
                'title': title,
                'imageUrl': image_url,
                'targetUrl': target_url,
                'createdAt': datetime.datetime.now().isoformat()
            }
            
            # Adicionar banner à lista
            banners.append(banner)
            
            # Salvar lista atualizada
            self._save_data(self.banners_file, banners)
            
            return banner
        
        def add_fullscreen_ad(self, title, image_url, target_url):
            ads = self.get_fullscreen_ads()
            
            # Gerar ID único
            ad_id = str(len(ads) + 1)
            
            # Criar anúncio
            ad = {
                'id': ad_id,
                'title': title,
                'imageUrl': image_url,
                'targetUrl': target_url,
                'createdAt': datetime.datetime.now().isoformat()
            }
            
            # Adicionar anúncio à lista
            ads.append(ad)
            
            # Salvar lista atualizada
            self._save_data(self.fullscreen_file, ads)
            
            return ad
        
        def update_banner(self, banner_id, title, image_url, target_url):
            banners = self.get_banners()
            
            for i, banner in enumerate(banners):
                if banner['id'] == banner_id:
                    banners[i]['title'] = title
                    banners[i]['imageUrl'] = image_url
                    banners[i]['targetUrl'] = target_url
                    banners[i]['updatedAt'] = datetime.datetime.now().isoformat()
                    
                    # Salvar lista atualizada
                    self._save_data(self.banners_file, banners)
                    return banners[i]
            
            return None
        
        def update_fullscreen_ad(self, ad_id, title, image_url, target_url):
            ads = self.get_fullscreen_ads()
            
            for i, ad in enumerate(ads):
                if ad['id'] == ad_id:
                    ads[i]['title'] = title
                    ads[i]['imageUrl'] = image_url
                    ads[i]['targetUrl'] = target_url
                    ads[i]['updatedAt'] = datetime.datetime.now().isoformat()
                    
                    # Salvar lista atualizada
                    self._save_data(self.fullscreen_file, ads)
                    return ads[i]
            
            return None
        
        def delete_banner(self, banner_id):
            banners = self.get_banners()
            
            for i, banner in enumerate(banners):
                if banner['id'] == banner_id:
                    # Remover banner da lista
                    del banners[i]
                    
                    # Salvar lista atualizada
                    self._save_data(self.banners_file, banners)
                    return True
            
            return False
        
        def delete_fullscreen_ad(self, ad_id):
            ads = self.get_fullscreen_ads()
            
            for i, ad in enumerate(ads):
                if ad['id'] == ad_id:
                    # Remover anúncio da lista
                    del ads[i]
                    
                    # Salvar lista atualizada
                    self._save_data(self.fullscreen_file, ads)
                    return True
            
            return False
        
        def get_banner(self, banner_id):
            banners = self.get_banners()
            
            for banner in banners:
                if banner['id'] == banner_id:
                    return banner
            
            return None
        
        def get_fullscreen_ad(self, ad_id):
            ads = self.get_fullscreen_ads()
            
            for ad in ads:
                if ad['id'] == ad_id:
                    return ad
            
            return None
        
        def record_impression(self, ad_id, ad_type):
            stats = self._load_data(self.stats_file)
            
            # Inicializar contadores se necessário
            if 'impressions' not in stats:
                stats['impressions'] = {}
            
            key = f"{ad_type}_{ad_id}"
            
            if key not in stats['impressions']:
                stats['impressions'][key] = 0
            
            # Incrementar contador
            stats['impressions'][key] += 1
            
            # Salvar estatísticas atualizadas
            self._save_data(self.stats_file, stats)
            
            return stats['impressions'][key]
        
        def record_click(self, ad_id, ad_type):
            stats = self._load_data(self.stats_file)
            
            # Inicializar contadores se necessário
            if 'clicks' not in stats:
                stats['clicks'] = {}
            
            key = f"{ad_type}_{ad_id}"
            
            if key not in stats['clicks']:
                stats['clicks'][key] = 0
            
            # Incrementar contador
            stats['clicks'][key] += 1
            
            # Salvar estatísticas atualizadas
            self._save_data(self.stats_file, stats)
            
            return stats['clicks'][key]
        
        def get_stats(self):
            return self._load_data(self.stats_file)
        
        def get_metrics(self):
            # Preparar métricas para banners
            banner_ads = []
            total_banner_impressions = 0
            total_banner_clicks = 0
            
            for banner in self.get_banners():
                banner_id = banner['id']
                key = f"banner_{banner_id}"
                stats = self.get_stats()
                impressions = stats.get('impressions', {}).get(key, 0)
                clicks = stats.get('clicks', {}).get(key, 0)
                
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
            
            for ad in self.get_fullscreen_ads():
                ad_id = ad['id']
                key = f"fullscreen_{ad_id}"
                stats = self.get_stats()
                impressions = stats.get('impressions', {}).get(key, 0)
                clicks = stats.get('clicks', {}).get(key, 0)
                
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
                    'ads_count': len(self.get_banners()),
                    'total_impressions': total_banner_impressions,
                    'total_clicks': total_banner_clicks,
                    'ctr': banner_ctr
                },
                'fullscreen': {
                    'ads': fullscreen_ads,
                    'ads_count': len(self.get_fullscreen_ads()),
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
    
    ads_model = AdModel(data_dir)
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
        logger.info(f"Métricas para dashboard: {metrics}")
        return render_template('dashboard.html', metrics=metrics)
    except Exception as e:
        logger.error(f"Erro ao renderizar dashboard: {e}")
        return render_template('error.html', message=str(e))

@app.route('/add-banner', methods=['GET', 'POST'])
def add_banner():
    if request.method == 'POST':
        title = request.form.get('title')
        image_url = request.form.get('imageUrl')
        target_url = request.form.get('targetUrl')
        
        if not title or not image_url or not target_url:
            return render_template('error.html', message="Todos os campos são obrigatórios")
        
        if not ads_model:
            return render_template('error.html', message="Modelo de anúncios não inicializado")
        
        banner = ads_model.add_banner(title, image_url, target_url)
        
        if banner:
            return redirect(url_for('dashboard'))
        else:
            return render_template('error.html', message="Erro ao adicionar banner")
    
    return render_template('add_banner.html')

@app.route('/add-fullscreen', methods=['GET', 'POST'])
def add_fullscreen():
    if request.method == 'POST':
        title = request.form.get('title')
        image_url = request.form.get('imageUrl')
        target_url = request.form.get('targetUrl')
        
        if not title or not image_url or not target_url:
            return render_template('error.html', message="Todos os campos são obrigatórios")
        
        if not ads_model:
            return render_template('error.html', message="Modelo de anúncios não inicializado")
        
        ad = ads_model.add_fullscreen_ad(title, image_url, target_url)
        
        if ad:
            return redirect(url_for('dashboard'))
        else:
            return render_template('error.html', message="Erro ao adicionar anúncio de tela cheia")
    
    return render_template('add_fullscreen.html')

@app.route('/edit-banner/<banner_id>', methods=['GET', 'POST'])
def edit_banner(banner_id):
    if not ads_model:
        return render_template('error.html', message="Modelo de anúncios não inicializado")
    
    banner = ads_model.get_banner(banner_id)
    
    if not banner:
        return render_template('error.html', message="Banner não encontrado")
    
    if request.method == 'POST':
        title = request.form.get('title')
        image_url = request.form.get('imageUrl')
        target_url = request.form.get('targetUrl')
        
        if not title or not image_url or not target_url:
            return render_template('error.html', message="Todos os campos são obrigatórios")
        
        updated_banner = ads_model.update_banner(banner_id, title, image_url, target_url)
        
        if updated_banner:
            return redirect(url_for('dashboard'))
        else:
            return render_template('error.html', message="Erro ao atualizar banner")
    
    return render_template('edit_banner.html', banner=banner)

@app.route('/edit-fullscreen/<ad_id>', methods=['GET', 'POST'])
def edit_fullscreen(ad_id):
    if not ads_model:
        return render_template('error.html', message="Modelo de anúncios não inicializado")
    
    ad = ads_model.get_fullscreen_ad(ad_id)
    
    if not ad:
        return render_template('error.html', message="Anúncio de tela cheia não encontrado")
    
    if request.method == 'POST':
        title = request.form.get('title')
        image_url = request.form.get('imageUrl')
        target_url = request.form.get('targetUrl')
        
        if not title or not image_url or not target_url:
            return render_template('error.html', message="Todos os campos são obrigatórios")
        
        updated_ad = ads_model.update_fullscreen_ad(ad_id, title, image_url, target_url)
        
        if updated_ad:
            return redirect(url_for('dashboard'))
        else:
            return render_template('error.html', message="Erro ao atualizar anúncio de tela cheia")
    
    return render_template('edit_fullscreen.html', ad=ad)

@app.route('/delete-banner/<banner_id>', methods=['POST'])
def delete_banner(banner_id):
    if not ads_model:
        return render_template('error.html', message="Modelo de anúncios não inicializado")
    
    success = ads_model.delete_banner(banner_id)
    
    if success:
        return redirect(url_for('dashboard'))
    else:
        return render_template('error.html', message="Erro ao excluir banner")

@app.route('/delete-fullscreen/<ad_id>', methods=['POST'])
def delete_fullscreen(ad_id):
    if not ads_model:
        return render_template('error.html', message="Modelo de anúncios não inicializado")
    
    success = ads_model.delete_fullscreen_ad(ad_id)
    
    if success:
        return redirect(url_for('dashboard'))
    else:
        return render_template('error.html', message="Erro ao excluir anúncio de tela cheia")

@app.route('/error')
def error():
    message = request.args.get('message', 'Erro desconhecido')
    return render_template('error.html', message=message)

# Iniciar aplicação
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
