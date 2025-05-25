"""
Modelo de dados para o sistema de anúncios.
Gerencia banners e anúncios de tela cheia.
"""
import os
import json
import logging
from datetime import datetime

class AdModel:
    """
    Modelo para gerenciar anúncios no sistema.
    Suporta banners (360x47px) e anúncios de tela cheia (360x640px).
    """
    
    def __init__(self, data_dir='data', data_file=None):
        """
        Inicializa o modelo com o diretório de dados especificado.
        
        Args:
            data_dir (str): Diretório onde os dados serão armazenados
            data_file (str): Arquivo de dados opcional (para compatibilidade)
        """
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
        """
        Inicializa um arquivo com dados padrão se não existir.
        
        Args:
            file_path (str): Caminho do arquivo
            default_data (any): Dados padrão para inicializar o arquivo
        """
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                json.dump(default_data, f)
    
    def _load_data(self, file_path):
        """
        Carrega dados de um arquivo JSON.
        
        Args:
            file_path (str): Caminho do arquivo
            
        Returns:
            dict: Dados carregados do arquivo
        """
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Erro ao carregar dados de {file_path}: {str(e)}")
            if file_path.endswith('stats.json'):
                return {'impressions': {}, 'clicks': {}}
            return []
    
    def _save_data(self, file_path, data):
        """
        Salva dados em um arquivo JSON.
        
        Args:
            file_path (str): Caminho do arquivo
            data (any): Dados a serem salvos
            
        Returns:
            bool: True se os dados foram salvos com sucesso, False caso contrário
        """
        try:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            logging.error(f"Erro ao salvar dados em {file_path}: {str(e)}")
            return False
    
    def get_banners(self):
        """
        Obtém todos os banners.
        
        Returns:
            list: Lista de banners
        """
        return self._load_data(self.banners_file)
    
    def get_fullscreen_ads(self):
        """
        Obtém todos os anúncios de tela cheia.
        
        Returns:
            list: Lista de anúncios de tela cheia
        """
        return self._load_data(self.fullscreen_file)
    
    def add_banner(self, title, image_url, target_url):
        """
        Adiciona um novo banner.
        
        Args:
            title (str): Título do banner
            image_url (str): URL da imagem do banner
            target_url (str): URL de destino do banner
            
        Returns:
            dict: Banner adicionado
        """
        banners = self.get_banners()
        
        # Gerar ID único
        banner_id = str(len(banners) + 1)
        
        # Criar banner
        banner = {
            'id': banner_id,
            'title': title,
            'imageUrl': image_url,
            'targetUrl': target_url,
            'createdAt': datetime.now().isoformat()
        }
        
        # Adicionar banner à lista
        banners.append(banner)
        
        # Salvar lista atualizada
        self._save_data(self.banners_file, banners)
        
        return banner
    
    def add_fullscreen_ad(self, title, image_url, target_url):
        """
        Adiciona um novo anúncio de tela cheia.
        
        Args:
            title (str): Título do anúncio
            image_url (str): URL da imagem do anúncio
            target_url (str): URL de destino do anúncio
            
        Returns:
            dict: Anúncio adicionado
        """
        ads = self.get_fullscreen_ads()
        
        # Gerar ID único
        ad_id = str(len(ads) + 1)
        
        # Criar anúncio
        ad = {
            'id': ad_id,
            'title': title,
            'imageUrl': image_url,
            'targetUrl': target_url,
            'createdAt': datetime.now().isoformat()
        }
        
        # Adicionar anúncio à lista
        ads.append(ad)
        
        # Salvar lista atualizada
        self._save_data(self.fullscreen_file, ads)
        
        return ad
    
    def record_impression(self, ad_id, ad_type):
        """
        Registra uma impressão de anúncio.
        
        Args:
            ad_id (str): ID do anúncio
            ad_type (str): Tipo do anúncio ('banner' ou 'fullscreen')
            
        Returns:
            bool: True se a impressão foi registrada com sucesso, False caso contrário
        """
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
        return self._save_data(self.stats_file, stats)
    
    def record_click(self, ad_id, ad_type):
        """
        Registra um clique em anúncio.
        
        Args:
            ad_id (str): ID do anúncio
            ad_type (str): Tipo do anúncio ('banner' ou 'fullscreen')
            
        Returns:
            bool: True se o clique foi registrado com sucesso, False caso contrário
        """
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
        return self._save_data(self.stats_file, stats)
    
    def get_stats(self):
        """
        Obtém estatísticas de impressões e cliques.
        
        Returns:
            dict: Estatísticas de impressões e cliques
        """
        return self._load_data(self.stats_file)
    
    def get_banner_stats(self):
        """
        Obtém estatísticas detalhadas de banners.
        
        Returns:
            list: Lista de banners com estatísticas
        """
        banners = self.get_banners()
        stats = self.get_stats()
        
        for banner in banners:
            banner_id = banner['id']
            key = f"banner_{banner_id}"
            
            banner['impressions'] = stats.get('impressions', {}).get(key, 0)
            banner['clicks'] = stats.get('clicks', {}).get(key, 0)
            
            # Calcular taxa de cliques
            if banner['impressions'] > 0:
                banner['ctr'] = round(banner['clicks'] / banner['impressions'] * 100, 2)
            else:
                banner['ctr'] = 0
        
        return banners
    
    def get_fullscreen_stats(self):
        """
        Obtém estatísticas detalhadas de anúncios de tela cheia.
        
        Returns:
            list: Lista de anúncios de tela cheia com estatísticas
        """
        ads = self.get_fullscreen_ads()
        stats = self.get_stats()
        
        for ad in ads:
            ad_id = ad['id']
            key = f"fullscreen_{ad_id}"
            
            ad['impressions'] = stats.get('impressions', {}).get(key, 0)
            ad['clicks'] = stats.get('clicks', {}).get(key, 0)
            
            # Calcular taxa de cliques
            if ad['impressions'] > 0:
                ad['ctr'] = round(ad['clicks'] / ad['impressions'] * 100, 2)
            else:
                ad['ctr'] = 0
        
        return ads
    
    def get_metrics(self):
        """
        Obtém métricas completas para o dashboard.
        
        Returns:
            dict: Métricas formatadas para o dashboard
        """
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
