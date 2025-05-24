"""
Aplicação principal para o sistema de anúncios.
Versão: 3.0.0
Autor: Manus AI
"""

from flask import Flask, render_template, request, redirect, url_for, jsonify, abort
from flask_cors import CORS
import os
import json
import logging
import datetime
from models.ads import AdModel

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Inicializar modelo de dados
ad_model = AdModel()

@app.route('/')
def dashboard():
    """Renderiza o dashboard principal com métricas de desempenho."""
    try:
        metrics = ad_model.get_metrics()
        return render_template('dashboard.html', metrics=metrics)
    except Exception as e:
        logger.error(f"Erro ao renderizar dashboard: {str(e)}")
        return render_template('error.html', message=f"'AdModel' object has no attribute 'get_metrics'")

@app.route('/add-banner', methods=['GET', 'POST'])
def add_banner():
    """Adiciona um novo banner."""
    if request.method == 'POST':
        title = request.form.get('title')
        image_url = request.form.get('imageUrl')
        target_url = request.form.get('targetUrl')
        
        ad_model.add_banner(title, image_url, target_url)
        return redirect(url_for('dashboard'))
    
    return render_template('add_banner.html')

@app.route('/add-fullscreen', methods=['GET', 'POST'])
def add_fullscreen():
    """Adiciona um novo anúncio de tela cheia."""
    if request.method == 'POST':
        title = request.form.get('title')
        image_url = request.form.get('imageUrl')
        target_url = request.form.get('targetUrl')
        
        ad_model.add_fullscreen_ad(title, image_url, target_url)
        return redirect(url_for('dashboard'))
    
    return render_template('add_fullscreen.html')

@app.route('/edit-banner/<banner_id>', methods=['GET', 'POST'])
def edit_banner(banner_id):
    """Edita um banner existente."""
    banner = ad_model.get_banner(banner_id)
    
    if not banner:
        return render_template('error.html', message="Banner não encontrado")
    
    if request.method == 'POST':
        title = request.form.get('title')
        image_url = request.form.get('imageUrl')
        target_url = request.form.get('targetUrl')
        
        ad_model.update_banner(banner_id, title, image_url, target_url)
        return redirect(url_for('dashboard'))
    
    return render_template('edit_banner.html', banner=banner)

@app.route('/edit-fullscreen/<ad_id>', methods=['GET', 'POST'])
def edit_fullscreen(ad_id):
    """Edita um anúncio de tela cheia existente."""
    ad = ad_model.get_fullscreen_ad(ad_id)
    
    if not ad:
        return render_template('error.html', message="Anúncio não encontrado")
    
    if request.method == 'POST':
        title = request.form.get('title')
        image_url = request.form.get('imageUrl')
        target_url = request.form.get('targetUrl')
        
        ad_model.update_fullscreen_ad(ad_id, title, image_url, target_url)
        return redirect(url_for('dashboard'))
    
    return render_template('edit_fullscreen.html', ad=ad)

@app.route('/delete-banner/<banner_id>', methods=['POST'])
def delete_banner(banner_id):
    """Exclui um banner."""
    ad_model.delete_banner(banner_id)
    return redirect(url_for('dashboard'))

@app.route('/delete-fullscreen/<ad_id>', methods=['POST'])
def delete_fullscreen(ad_id):
    """Exclui um anúncio de tela cheia."""
    ad_model.delete_fullscreen_ad(ad_id)
    return redirect(url_for('dashboard'))

# API Routes
@app.route('/api/banners', methods=['GET'])
def get_banners():
    """Retorna todos os banners disponíveis."""
    banners = ad_model.get_banners()
    return jsonify(banners)

@app.route('/api/fullscreen', methods=['GET'])
def get_fullscreen_ads():
    """Retorna todos os anúncios de tela cheia disponíveis."""
    ads = ad_model.get_fullscreen_ads()
    return jsonify(ads)

@app.route('/api/impression', methods=['POST', 'OPTIONS'])
def record_impression():
    """Registra uma impressão de anúncio."""
    if request.method == 'OPTIONS':
        return '', 200
    
    data = request.json
    ad_id = data.get('adId')
    ad_type = data.get('type')
    
    if not ad_id or not ad_type:
        return jsonify({"error": "Dados incompletos"}), 400
    
    success = ad_model.record_impression(ad_id, ad_type)
    
    if success:
        return jsonify({"status": "success"}), 200
    else:
        return jsonify({"error": "Falha ao registrar impressão"}), 500

@app.route('/api/click', methods=['POST', 'OPTIONS'])
def record_click():
    """Registra um clique em anúncio."""
    if request.method == 'OPTIONS':
        return '', 200
    
    data = request.json
    ad_id = data.get('adId')
    ad_type = data.get('type')
    
    if not ad_id or not ad_type:
        return jsonify({"error": "Dados incompletos"}), 400
    
    success = ad_model.record_click(ad_id, ad_type)
    
    if success:
        return jsonify({"status": "success"}), 200
    else:
        return jsonify({"error": "Falha ao registrar clique"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
