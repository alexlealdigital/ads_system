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
    except ImportError as e_alt: # Renomear para evitar sombreamento
        logger.error(f"❌ Erro na importação alternativa: {str(e_alt)}")
        
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

# Definir classe AdModel de fallback caso a importação falhe
if 'AdModel' not in globals():
    logger.warning("⚠️ Usando AdModel de fallback interno em app.py.")
    class AdModel:
        def __init__(self, data_dir='data'):
            self.data_dir = data_dir
            if not os.path.exists(self.data_dir):
                os.makedirs(self.data_dir)
            self.banners_file = os.path.join(self.data_dir, 'banners.json')
            self.fullscreen_file = os.path.join(self.data_dir, 'fullscreen.json')
            self.stats_file = os.path.join(self.data_dir, 'stats.json') # stats.json não é usado ativamente nos métodos de stats
            
            # Inicializar arquivos se não existirem
            for file_path, default_data in [
                (self.banners_file, []),
                (self.fullscreen_file, []),
                (self.stats_file, {'impressions': {}, 'clicks': {}}) # Stats reais não são gravados por este fallback
            ]:
                if not os.path.exists(file_path):
                    try:
                        with open(file_path, 'w') as f:
                            json.dump(default_data, f, indent=2)
                        logger.info(f"✅ Arquivo de fallback criado: {file_path}")
                    except Exception as e_file:
                        logger.error(f"❌ Erro ao criar arquivo de fallback {file_path}: {str(e_file)}")
        
        def _load_data(self, file_path):
            try:
                if os.path.exists(file_path):
                    with open(file_path, 'r') as f:
                        return json.load(f)
                return [] # Retorna lista vazia se o arquivo não existir
            except json.JSONDecodeError:
                logger.error(f"Erro ao decodificar JSON de {file_path}. Retornando lista vazia.")
                return []
            except Exception as e_load:
                logger.error(f"Erro ao carregar dados de {file_path}: {str(e_load)}. Retornando lista vazia.")
                return []

        def get_banners(self):
            return self._load_data(self.banners_file)
        
        def get_fullscreen_ads(self):
            return self._load_data(self.fullscreen_file)
        
        # get_stats não é chamado diretamente, mas stats_file existe
        def get_stats_data(self): # Renomeado para evitar confusão com get_banner_stats etc.
            try:
                if os.path.exists(self.stats_file):
                    with open(self.stats_file, 'r') as f:
                        return json.load(f)
                return {'impressions': {}, 'clicks': {}}
            except json.JSONDecodeError:
                logger.error(f"Erro ao decodificar JSON de {self.stats_file}. Retornando stats vazios.")
                return {'impressions': {}, 'clicks': {}}
            except Exception as e_stat_load:
                logger.error(f"Erro ao carregar dados de {self.stats_file}: {str(e_stat_load)}. Retornando stats vazios.")
                return {'impressions': {}, 'clicks': {}}

        def _save_data(self, file_path, data):
            try:
                with open(file_path, 'w') as f:
                    json.dump(data, f, indent=2)
                return True
            except Exception as e_save:
                logger.error(f"Erro ao salvar dados em {file_path}: {str(e_save)}")
                return False
        
        def _generate_id(self, items_list):
            if not items_list:
                return "1"
            # Encontra o maior ID numérico existente e incrementa
            max_id = 0
            for item in items_list:
                try:
                    item_id_num = int(item.get('id', 0))
                    if item_id_num > max_id:
                        max_id = item_id_num
                except ValueError:
                    # Ignora IDs não numéricos na contagem para novo ID
                    pass
            return str(max_id + 1)

        def add_banner(self, title, image_url, target_url):
            banners = self.get_banners()
            banner_id = self._generate_id(banners) # ID mais robusto
            banner = {
                'id': banner_id,
                'title': title,
                'imageUrl': image_url,
                'targetUrl': target_url,
                'createdAt': datetime.now().isoformat(),
                'updatedAt': datetime.now().isoformat(),
                'impressions': 0, # Incluir stats iniciais
                'clicks': 0       # Incluir stats iniciais
            }
            banners.append(banner)
            self._save_data(self.banners_file, banners)
            return banner
        
        def add_fullscreen_ad(self, title, image_url, target_url):
            ads = self.get_fullscreen_ads()
            ad_id = self._generate_id(ads) # ID mais robusto
            ad = {
                'id': ad_id,
                'title': title,
                'imageUrl': image_url,
                'targetUrl': target_url,
                'createdAt': datetime.now().isoformat(),
                'updatedAt': datetime.now().isoformat(),
                'impressions': 0, # Incluir stats iniciais
                'clicks': 0       # Incluir stats iniciais
            }
            ads.append(ad)
            self._save_data(self.fullscreen_file, ads)
            return ad
        
        # Fallback AdModel não implementa lógica real de stats
        def record_impression(self, ad_id, ad_type):
            logger.info(f"Fallback AdModel: Impressão registrada para {ad_type} ID {ad_id} (sem gravação de stats).")
            return True 
        
        def record_click(self, ad_id, ad_type):
            logger.info(f"Fallback AdModel: Clique registrado para {ad_type} ID {ad_id} (sem gravação de stats).")
            return True
        
        def get_banner_stats(self):
            banners = self.get_banners()
            # No fallback, as stats são sempre 0 pois não são persistidas/atualizadas
            for banner in banners:
                banner.setdefault('impressions', 0)
                banner.setdefault('clicks', 0)
                banner.setdefault('ctr', 0.0)
            return banners
        
        def get_fullscreen_stats(self):
            ads = self.get_fullscreen_ads()
            # No fallback, as stats são sempre 0
            for ad in ads:
                ad.setdefault('impressions', 0)
                ad.setdefault('clicks', 0)
                ad.setdefault('ctr', 0.0)
            return ads

# Inicializar modelo de anúncios
ad_model = None
# Determinar o data_dir (considerar variável de ambiente para Render.com Disks)
data_dir_env = os.environ.get('ADS_DATA_DIR') 
if data_dir_env:
    data_dir = data_dir_env
    logger.info(f"Usando data_dir da variável de ambiente ADS_DATA_DIR: {data_dir}")
else:
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    logger.info(f"Variável de ambiente ADS_DATA_DIR não definida, usando data_dir local: {data_dir}")

if not os.path.exists(data_dir):
    try:
        os.makedirs(data_dir)
        logger.info(f"Diretório de dados criado: {data_dir}")
    except Exception as e_makedirs:
        logger.error(f"❌ Erro ao criar diretório de dados {data_dir}: {str(e_makedirs)}")
        # Se não conseguir criar o diretório, AdModel pode falhar ou usar um local inesperado
        # Isso pode ser um problema de permissão no Render.com se não usar um disco montado.

try:
    if 'AdModel' in globals() and AdModel.__module__ == 'models.ads': # Verifica se é o AdModel externo
        ad_model = AdModel(data_dir=data_dir)
        logger.info("✅ Modelo de anúncios externo (models.ads.AdModel) inicializado com sucesso.")
    elif 'AdModel' in globals(): # É o AdModel de fallback
        ad_model = AdModel(data_dir=data_dir) # AdModel de fallback interno
        logger.info("✅ Modelo de anúncios de fallback (interno em app.py) inicializado com sucesso.")
    else:
        raise RuntimeError("Nenhuma classe AdModel disponível para inicialização.")

    # Adicionar alguns banners de exemplo se não existirem
    banners = ad_model.get_banners()
    if not banners:
        ad_model.add_banner(
            "Banner de Exemplo",
            "https://placehold.co/360x47/orange/white?text=Anuncio+Exemplo+1",
            "https://alexlealdigital.github.io"
        )
        logger.info("✅ Banner de exemplo adicionado (pois a lista estava vazia).")
    
    # Adicionar anúncios de tela cheia de exemplo se não existirem
    fullscreen_ads = ad_model.get_fullscreen_ads()
    if not fullscreen_ads:
        ad_model.add_fullscreen_ad(
            "Anúncio de Tela Cheia de Exemplo",
            "https://placehold.co/360x640/blue/white?text=Anuncio+Tela+Cheia+1",
            "https://alexlealdigital.github.io"
        )
        logger.info("✅ Anúncio de tela cheia de exemplo adicionado (pois a lista estava vazia).")

except Exception as e:
    logger.error(f"🔥 ERRO CRÍTICO ao inicializar o modelo de anúncios: {str(e)}")
    logger.exception("Detalhes da exceção na inicialização do AdModel:")
    # Se tudo falhar, ad_model permanecerá None, e as rotas devem lidar com isso.

# --- Rotas da API (sem alterações significativas, mantendo a correção de URL de imagem) ---
@app.route('/api/banners', methods=['GET', 'OPTIONS'])
def get_api_banners(): # Renomeado para evitar conflito com a variável banners
    if request.method == 'OPTIONS':
        return '', 200
    if not ad_model:
        return jsonify({"error": "Modelo de anúncios não inicializado"}), 500
    try:
        banners_list = ad_model.get_banners()
        for banner in banners_list:
            if 'imageUrl' in banner and ('imgur.com' in banner['imageUrl'] or not banner['imageUrl'].startswith('http')):
                banner['imageUrl'] = "https://placehold.co/360x47/orange/white?text=Imagem+Corrigida"
        return jsonify(banners_list)
    except Exception as e:
        logger.error(f"Erro ao obter banners via API: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/fullscreen', methods=['GET', 'OPTIONS'])
def get_api_fullscreen_ads(): # Renomeado
    if request.method == 'OPTIONS':
        return '', 200
    if not ad_model:
        return jsonify({"error": "Modelo de anúncios não inicializado"}), 500
    try:
        ads_list = ad_model.get_fullscreen_ads()
        for ad in ads_list:
            if 'imageUrl' in ad and ('imgur.com' in ad['imageUrl'] or not ad['imageUrl'].startswith('http')):
                ad['imageUrl'] = "https://placehold.co/360x640/blue/white?text=Imagem+Corrigida"
        return jsonify(ads_list)
    except Exception as e:
        logger.error(f"Erro ao obter anúncios de tela cheia via API: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/ads/banner', methods=['GET', 'OPTIONS'])
def get_banners_compat():
    return get_api_banners()

@app.route('/api/ads/fullscreen', methods=['GET', 'OPTIONS'])
def get_fullscreen_ads_compat():
    return get_api_fullscreen_ads()

@app.route('/api/impression', methods=['POST', 'OPTIONS'])
def record_impression():
    if request.method == 'OPTIONS': return '', 200
    if not ad_model: return jsonify({"error": "Modelo de anúncios não inicializado"}), 500
    try:
        data = request.json
        ad_id = data.get('adId')
        ad_type = data.get('type') or data.get('adType')
        if not ad_id or not ad_type: return jsonify({"error": "ID do anúncio e tipo são obrigatórios"}), 400
        success = ad_model.record_impression(ad_id, ad_type)
        if success: return jsonify({"success": True})
        else: return jsonify({"error": "Falha ao registrar impressão"}), 500
    except Exception as e:
        logger.error(f"Erro ao registrar impressão: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/click', methods=['POST', 'OPTIONS'])
def record_click():
    if request.method == 'OPTIONS': return '', 200
    if not ad_model: return jsonify({"error": "Modelo de anúncios não inicializado"}), 500
    try:
        data = request.json
        ad_id = data.get('adId')
        ad_type = data.get('type') or data.get('adType')
        if not ad_id or not ad_type: return jsonify({"error": "ID do anúncio e tipo são obrigatórios"}), 400
        success = ad_model.record_click(ad_id, ad_type)
        if success: return jsonify({"success": True})
        else: return jsonify({"error": "Falha ao registrar clique"}), 500
    except Exception as e:
        logger.error(f"Erro ao registrar clique: {str(e)}")
        return jsonify({"error": str(e)}), 500

# --- Rotas do Dashboard ---
@app.route('/')
def dashboard():
    """
    Página principal do dashboard.
    """
    empty_metrics_data = { # Definido uma vez para reutilização
        'banner': {'ads_count': 0, 'total_impressions': 0, 'total_clicks': 0, 'ctr': 0.0, 'ads': []},
        'fullscreen': {'ads_count': 0, 'total_impressions': 0, 'total_clicks': 0, 'ctr': 0.0, 'ads': []}
    }

    if not ad_model:
        logger.warning("DEBUG RENDER: ad_model não inicializado na rota dashboard. Usando empty_metrics.")
        return render_template('dashboard.html', metrics=empty_metrics_data)
    
    try:
        banner_stats_list = []
        fullscreen_stats_list = []

        try:
            banner_stats_list = ad_model.get_banner_stats()
            logger.info(f"DEBUG RENDER: Banner Stats para o dashboard: {banner_stats_list}")
        except Exception as e_bs:
            logger.error(f"Erro ao obter estatísticas de banners para o dashboard: {str(e_bs)}")
            logger.exception("DEBUG RENDER: Exception details in ad_model.get_banner_stats():")
            # banner_stats_list já é [] por padrão se erro

        try:
            fullscreen_stats_list = ad_model.get_fullscreen_stats()
            logger.info(f"DEBUG RENDER: Fullscreen Stats para o dashboard: {fullscreen_stats_list}")
        except Exception as e_fs:
            logger.error(f"Erro ao obter estatísticas de tela cheia para o dashboard: {str(e_fs)}")
            logger.exception("DEBUG RENDER: Exception details in ad_model.get_fullscreen_stats():")
            # fullscreen_stats_list já é [] por padrão se erro
        
        # Garantir que as listas são de fato listas para as próximas operações
        banner_stats = banner_stats_list if isinstance(banner_stats_list, list) else []
        fullscreen_stats = fullscreen_stats_list if isinstance(fullscreen_stats_list, list) else []

        # Verificar e corrigir URLs de imagens
        for banner in banner_stats:
            if isinstance(banner, dict) and 'imageUrl' in banner and \
               ('imgur.com' in banner['imageUrl'] or not str(banner['imageUrl']).startswith('http')):
                banner['imageUrl'] = "https://placehold.co/360x47/orange/white?text=Imagem+Corrigida"
        
        for ad_item in fullscreen_stats: # Renomeado para evitar conflito com 'ad_model'
            if isinstance(ad_item, dict) and 'imageUrl' in ad_item and \
               ('imgur.com' in ad_item['imageUrl'] or not str(ad_item['imageUrl']).startswith('http')):
                ad_item['imageUrl'] = "https://placehold.co/360x640/blue/white?text=Imagem+Corrigida"
        
        # Calcular métricas agregadas para banners
        total_banner_impressions = sum(b.get('impressions', 0) for b in banner_stats if isinstance(b, dict))
        total_banner_clicks = sum(b.get('clicks', 0) for b in banner_stats if isinstance(b, dict))
        banner_ctr = 0.0
        if total_banner_impressions > 0:
            banner_ctr = round((total_banner_clicks / total_banner_impressions) * 100, 2)
        
        # Calcular métricas agregadas para anúncios de tela cheia
        total_fullscreen_impressions = sum(ad_item.get('impressions', 0) for ad_item in fullscreen_stats if isinstance(ad_item, dict))
        total_fullscreen_clicks = sum(ad_item.get('clicks', 0) for ad_item in fullscreen_stats if isinstance(ad_item, dict))
        fullscreen_ctr = 0.0
        if total_fullscreen_impressions > 0:
            fullscreen_ctr = round((total_fullscreen_clicks / total_fullscreen_impressions) * 100, 2)
            
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
        logger.info(f"DEBUG RENDER: Métricas finais enviadas para o template: {metrics}")
        return render_template('dashboard.html', metrics=metrics)

    except Exception as e_dash:
        logger.error(f"Erro GERAL e inesperado ao renderizar dashboard: {str(e_dash)}")
        logger.exception("DEBUG RENDER: Exception details in dashboard route (GENERAL CATCH ALL):")
        return render_template('dashboard.html', metrics=empty_metrics_data) # Fallback para métricas vazias

# --- Rotas para Adicionar Anúncios (mantendo correção de URL) ---
@app.route('/add-banner', methods=['GET', 'POST'])
def add_banner_route(): # Renomeado
    if not ad_model:
        return render_template('error.html', message="Modelo de anúncios não inicializado")
    if request.method == 'POST':
        try:
            title = request.form.get('title')
            image_url = request.form.get('imageUrl')
            target_url = request.form.get('targetUrl')
            if not all([title, image_url, target_url]):
                return render_template('add_banner.html', error="Todos os campos são obrigatórios")
            if 'imgur.com' in image_url or not image_url.startswith('http'):
                image_url = "https://placehold.co/360x47/orange/white?text=Anuncio+Exemplo"
            ad_model.add_banner(title, image_url, target_url)
            return redirect(url_for('dashboard'))
        except Exception as e:
            logger.error(f"Erro ao adicionar banner: {str(e)}")
            return render_template('add_banner.html', error=str(e))
    return render_template('add_banner.html')

@app.route('/add-fullscreen', methods=['GET', 'POST'])
def add_fullscreen_route(): # Renomeado
    if not ad_model:
        return render_template('error.html', message="Modelo de anúncios não inicializado")
    if request.method == 'POST':
        try:
            title = request.form.get('title')
            image_url = request.form.get('imageUrl')
            target_url = request.form.get('targetUrl')
            if not all([title, image_url, target_url]):
                return render_template('add_fullscreen.html', error="Todos os campos são obrigatórios")
            if 'imgur.com' in image_url or not image_url.startswith('http'):
                image_url = "https://placehold.co/360x640/blue/white?text=Anuncio+Tela+Cheia"
            ad_model.add_fullscreen_ad(title, image_url, target_url)
            return redirect(url_for('dashboard'))
        except Exception as e:
            logger.error(f"Erro ao adicionar anúncio de tela cheia: {str(e)}")
            return render_template('add_fullscreen.html', error=str(e))
    return render_template('add_fullscreen.html')

# --- Rotas para Editar Anúncios (mantendo correção de URL e lógica) ---
@app.route('/edit-banner/<ad_id>', methods=['GET', 'POST'])
def edit_banner_route(ad_id): # Renomeado
    if not ad_model:
        return render_template('error.html', message="Modelo de anúncios não inicializado")
    
    banners_list = ad_model.get_banners()
    banner = next((b for b in banners_list if isinstance(b, dict) and b.get('id') == ad_id), None)
    if not banner:
        return render_template('error.html', message=f"Banner com ID {ad_id} não encontrado")
    
    if request.method == 'POST':
        try:
            title = request.form.get('title')
            image_url = request.form.get('imageUrl')
            target_url = request.form.get('targetUrl')
            if not all([title, image_url, target_url]):
                return render_template('edit_banner.html', banner=banner, error="Todos os campos são obrigatórios")
            
            if 'imgur.com' in image_url or not image_url.startswith('http'):
                image_url = "https://placehold.co/360x47/orange/white?text=Imagem+Corrigida"
            
            banner['title'] = title
            banner['imageUrl'] = image_url
            banner['targetUrl'] = target_url
            banner['updatedAt'] = datetime.now().isoformat()
            
            ad_model._save_data(ad_model.banners_file, banners_list) # Salva a lista inteira
            return redirect(url_for('dashboard'))
        except Exception as e:
            logger.error(f"Erro ao editar banner ID {ad_id}: {str(e)}")
            return render_template('edit_banner.html', banner=banner, error=str(e))
            
    return render_template('edit_banner.html', banner=banner)

@app.route('/edit-fullscreen/<ad_id>', methods=['GET', 'POST'])
def edit_fullscreen_route(ad_id): # Renomeado
    if not ad_model:
        return render_template('error.html', message="Modelo de anúncios não inicializado")
        
    ads_list = ad_model.get_fullscreen_ads()
    ad_item = next((a for a in ads_list if isinstance(a, dict) and a.get('id') == ad_id), None) # Renomeado
    if not ad_item:
        return render_template('error.html', message=f"Anúncio com ID {ad_id} não encontrado")
        
    if request.method == 'POST':
        try:
            title = request.form.get('title')
            image_url = request.form.get('imageUrl')
            target_url = request.form.get('targetUrl')
            if not all([title, image_url, target_url]):
                return render_template('edit_fullscreen.html', ad=ad_item, error="Todos os campos são obrigatórios")

            if 'imgur.com' in image_url or not image_url.startswith('http'):
                image_url = "https://placehold.co/360x640/blue/white?text=Imagem+Corrigida"

            ad_item['title'] = title
            ad_item['imageUrl'] = image_url
            ad_item['targetUrl'] = target_url
            ad_item['updatedAt'] = datetime.now().isoformat()
            
            ad_model._save_data(ad_model.fullscreen_file, ads_list) # Salva a lista inteira
            return redirect(url_for('dashboard'))
        except Exception as e:
            logger.error(f"Erro ao editar anúncio de tela cheia ID {ad_id}: {str(e)}")
            return render_template('edit_fullscreen.html', ad=ad_item, error=str(e))
            
    return render_template('edit_fullscreen.html', ad=ad_item)

# --- Rotas para Excluir Anúncios ---
@app.route('/delete-banner/<ad_id>', methods=['POST'])
def delete_banner_route(ad_id): # Renomeado
    if not ad_model:
        return render_template('error.html', message="Modelo de anúncios não inicializado")
    try:
        banners_list = ad_model.get_banners()
        # Filtra para manter apenas os banners que NÃO têm o ad_id
        updated_banners = [b for b in banners_list if not (isinstance(b, dict) and b.get('id') == ad_id)]
        if len(updated_banners) == len(banners_list): # Nada foi filtrado, ID não encontrado
             logger.warning(f"Tentativa de deletar banner com ID {ad_id} não encontrado.")
        ad_model._save_data(ad_model.banners_file, updated_banners)
        return redirect(url_for('dashboard'))
    except Exception as e:
        logger.error(f"Erro ao excluir banner ID {ad_id}: {str(e)}")
        # Passar a mensagem de erro para o template de erro genérico
        return render_template('error.html', message=f"Erro ao excluir banner: {str(e)}")

@app.route('/delete-fullscreen/<ad_id>', methods=['POST'])
def delete_fullscreen_route(ad_id): # Renomeado
    if not ad_model:
        return render_template('error.html', message="Modelo de anúncios não inicializado")
    try:
        ads_list = ad_model.get_fullscreen_ads()
        updated_ads = [a for a in ads_list if not (isinstance(a, dict) and a.get('id') == ad_id)]
        if len(updated_ads) == len(ads_list): # Nada foi filtrado, ID não encontrado
             logger.warning(f"Tentativa de deletar anúncio fullscreen com ID {ad_id} não encontrado.")
        ad_model._save_data(ad_model.fullscreen_file, updated_ads)
        return redirect(url_for('dashboard'))
    except Exception as e:
        logger.error(f"Erro ao excluir anúncio de tela cheia ID {ad_id}: {str(e)}")
        return render_template('error.html', message=f"Erro ao excluir anúncio de tela cheia: {str(e)}")

# Iniciar aplicação
if __name__ == '__main__':
    # Para debug local, pode ser útil habilitar o debug do Flask, mas não para produção no Render
    # host='0.0.0.0' é importante para o Render.com encontrar o serviço
    port = int(os.environ.get("PORT", 10000)) # Render.com define a variável PORT
    app.run(debug=False, host='0.0.0.0', port=port)
