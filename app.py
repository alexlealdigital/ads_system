"""
Aplicação principal para o sistema de anúncios.
Gerencia banners e anúncios de tela cheia.
Versão corrigida com suporte a métricas para o dashboard e botões de editar/deletar.
"""
import os
import sys
import json
import logging
from datetime import datetime
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
            "https://placehold.co/360x47/orange/white?text=Anuncio+Exemplo",
            "https://alexlealdigital.github.io"
        )
        logger.info("✅ Banner de exemplo adicionado.")
    
    # Adicionar anúncios de tela cheia de exemplo se não existirem
    fullscreen_ads = ad_model.get_fullscreen_ads()
    if not fullscreen_ads:
        ad_model.add_fullscreen_ad(
            "Anúncio de Tela Cheia de Exemplo",
            "https://placehold.co/360x640/blue/white?text=Anuncio+Tela+Cheia",
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
        # Obter estatísticas de banners e anúncios de tela cheia
        banner_stats = ad_model.get_banner_stats()
        fullscreen_stats = ad_model.get_fullscreen_stats()
        
        # Calcular métricas agregadas para banners
        total_banner_impressions = sum(banner.get('impressions', 0) for banner in banner_stats)
        total_banner_clicks = sum(banner.get('clicks', 0) for banner in banner_stats)
        banner_ctr = 0
        if total_banner_impressions > 0:
            banner_ctr = round(total_banner_clicks / total_banner_impressions * 100, 2)
        
        # Calcular métricas agregadas para anúncios de tela cheia
        total_fullscreen_impressions = sum(ad.get('impressions', 0) for ad in fullscreen_stats)
        total_fullscreen_clicks = sum(ad.get('clicks', 0) for ad in fullscreen_stats)
        fullscreen_ctr = 0
        if total_fullscreen_impressions > 0:
            fullscreen_ctr = round(total_fullscreen_clicks / total_fullscreen_impressions * 100, 2)
        
        # Construir objeto de métricas no formato esperado pelo template
        metrics = {
            'banner': {
                'ads_count': len(banner_stats),
                'total_impressions': total_banner_impressions,
                'total_clicks': total_banner_clicks,
                'ctr': banner_ctr,
                'ads': banner_stats
            },
            'fullscreen': {
                'ads_count': len(fullscreen_stats),
                'total_impressions': total_fullscreen_impressions,
                'total_clicks': total_fullscreen_clicks,
                'ctr': fullscreen_ctr,
                'ads': fullscreen_stats
            }
        }
        
        return render_template('dashboard.html', metrics=metrics)
    except Exception as e:
        logger.error(f"Erro ao renderizar dashboard: {str(e)}")
        return render_template('error.html', error=str(e))

# Rotas para adicionar anúncios
@app.route('/add-banner', methods=['GET', 'POST'])
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

@app.route('/add-fullscreen', methods=['GET', 'POST'])
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

# Rotas para editar anúncios
@app.route('/edit-banner/<ad_id>', methods=['GET', 'POST'])
def edit_banner(ad_id):
    """
    Edita um banner existente.
    """
    if not ad_model:
        return render_template('error.html', error="Modelo de anúncios não inicializado")
    
    # Obter todos os banners
    banners = ad_model.get_banners()
    
    # Encontrar o banner pelo ID
    banner = next((b for b in banners if b['id'] == ad_id), None)
    
    if not banner:
        return render_template('error.html', error=f"Banner com ID {ad_id} não encontrado")
    
    if request.method == 'POST':
        try:
            title = request.form.get('title')
            image_url = request.form.get('imageUrl')
            target_url = request.form.get('targetUrl')
            
            if not title or not image_url or not target_url:
                return render_template('edit_banner.html', banner=banner, error="Todos os campos são obrigatórios")
            
            # Atualizar banner
            banner['title'] = title
            banner['imageUrl'] = image_url
            banner['targetUrl'] = target_url
            banner['updatedAt'] = datetime.now().isoformat()
            
            # Salvar alterações
            ad_model._save_data(ad_model.banners_file, banners)
            
            return redirect(url_for('dashboard'))
        except Exception as e:
            logger.error(f"Erro ao editar banner: {str(e)}")
            return render_template('edit_banner.html', banner=banner, error=str(e))
    
    return render_template('edit_banner.html', banner=banner)

@app.route('/edit-fullscreen/<ad_id>', methods=['GET', 'POST'])
def edit_fullscreen(ad_id):
    """
    Edita um anúncio de tela cheia existente.
    """
    if not ad_model:
        return render_template('error.html', error="Modelo de anúncios não inicializado")
    
    # Obter todos os anúncios de tela cheia
    ads = ad_model.get_fullscreen_ads()
    
    # Encontrar o anúncio pelo ID
    ad = next((a for a in ads if a['id'] == ad_id), None)
    
    if not ad:
        return render_template('error.html', error=f"Anúncio com ID {ad_id} não encontrado")
    
    if request.method == 'POST':
        try:
            title = request.form.get('title')
            image_url = request.form.get('imageUrl')
            target_url = request.form.get('targetUrl')
            
            if not title or not image_url or not target_url:
                return render_template('edit_fullscreen.html', ad=ad, error="Todos os campos são obrigatórios")
            
            # Atualizar anúncio
            ad['title'] = title
            ad['imageUrl'] = image_url
            ad['targetUrl'] = target_url
            ad['updatedAt'] = datetime.now().isoformat()
            
            # Salvar alterações
            ad_model._save_data(ad_model.fullscreen_file, ads)
            
            return redirect(url_for('dashboard'))
        except Exception as e:
            logger.error(f"Erro ao editar anúncio de tela cheia: {str(e)}")
            return render_template('edit_fullscreen.html', ad=ad, error=str(e))
    
    return render_template('edit_fullscreen.html', ad=ad)

# Rotas para excluir anúncios
@app.route('/delete-banner/<ad_id>', methods=['POST'])
def delete_banner(ad_id):
    """
    Exclui um banner existente.
    """
    if not ad_model:
        return render_template('error.html', error="Modelo de anúncios não inicializado")
    
    try:
        # Obter todos os banners
        banners = ad_model.get_banners()
        
        # Filtrar o banner a ser excluído
        banners = [b for b in banners if b['id'] != ad_id]
        
        # Salvar alterações
        ad_model._save_data(ad_model.banners_file, banners)
        
        return redirect(url_for('dashboard'))
    except Exception as e:
        logger.error(f"Erro ao excluir banner: {str(e)}")
        return render_template('error.html', error=f"Erro ao excluir banner: {str(e)}")

@app.route('/delete-fullscreen/<ad_id>', methods=['POST'])
def delete_fullscreen(ad_id):
    """
    Exclui um anúncio de tela cheia existente.
    """
    if not ad_model:
        return render_template('error.html', error="Modelo de anúncios não inicializado")
    
    try:
        # Obter todos os anúncios de tela cheia
        ads = ad_model.get_fullscreen_ads()
        
        # Filtrar o anúncio a ser excluído
        ads = [a for a in ads if a['id'] != ad_id]
        
        # Salvar alterações
        ad_model._save_data(ad_model.fullscreen_file, ads)
        
        return redirect(url_for('dashboard'))
    except Exception as e:
        logger.error(f"Erro ao excluir anúncio de tela cheia: {str(e)}")
        return render_template('error.html', error=f"Erro ao excluir anúncio de tela cheia: {str(e)}")

# Iniciar aplicação
if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')
