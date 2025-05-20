"""
Modelo de dados para o sistema de anúncios
"""
import json
import time
from datetime import datetime

class AdModel:
    """Classe para gerenciar os anúncios no Firebase"""
    
    def __init__(self, firebase_ref):
        """
        Inicializa o modelo com a referência do Firebase
        
        Args:
            firebase_ref: Referência para o nó 'ads' no Firebase
        """
        self.ref = firebase_ref
        
    def get_banner_ads(self):
        """
        Obtém todos os anúncios de banner
        
        Returns:
            list: Lista de anúncios de banner
        """
        try:
            banner_ref = self.ref.child('bannerAds')
            ads = banner_ref.get() or {}
            return [{'id': key, **value} for key, value in ads.items()]
        except Exception as e:
            print(f"Erro ao obter banners: {str(e)}")
            return []
    
    def get_fullscreen_ads(self):
        """
        Obtém todos os anúncios de tela cheia
        
        Returns:
            list: Lista de anúncios de tela cheia
        """
        try:
            fullscreen_ref = self.ref.child('fullscreenAds')
            ads = fullscreen_ref.get() or {}
            return [{'id': key, **value} for key, value in ads.items()]
        except Exception as e:
            print(f"Erro ao obter anúncios de tela cheia: {str(e)}")
            return []
    
    def get_banner_ad(self, ad_id):
        """
        Obtém um anúncio de banner específico pelo ID
        
        Args:
            ad_id (str): ID do anúncio
            
        Returns:
            dict: Dados do anúncio ou None se não encontrado
        """
        try:
            banner_ref = self.ref.child(f'bannerAds/{ad_id}')
            ad_data = banner_ref.get()
            if ad_data:
                return {'id': ad_id, **ad_data}
            return None
        except Exception as e:
            print(f"Erro ao obter banner: {str(e)}")
            return None
    
    def get_fullscreen_ad(self, ad_id):
        """
        Obtém um anúncio de tela cheia específico pelo ID
        
        Args:
            ad_id (str): ID do anúncio
            
        Returns:
            dict: Dados do anúncio ou None se não encontrado
        """
        try:
            fullscreen_ref = self.ref.child(f'fullscreenAds/{ad_id}')
            ad_data = fullscreen_ref.get()
            if ad_data:
                return {'id': ad_id, **ad_data}
            return None
        except Exception as e:
            print(f"Erro ao obter anúncio de tela cheia: {str(e)}")
            return None
    
    def add_banner_ad(self, image_url, link_url):
        """
        Adiciona um novo anúncio de banner
        
        Args:
            image_url (str): URL da imagem no Imgur
            link_url (str): URL de destino do anúncio
            
        Returns:
            str: ID do anúncio criado
        """
        try:
            banner_ref = self.ref.child('bannerAds')
            new_ad = {
                'imageUrl': image_url,
                'linkUrl': link_url,
                'impressions': 0,
                'clicks': 0,
                'createdAt': datetime.now().isoformat(),
                'lastShown': None
            }
            ad_ref = banner_ref.push(new_ad)
            return ad_ref.key
        except Exception as e:
            print(f"Erro ao adicionar banner: {str(e)}")
            return None
    
    def add_fullscreen_ad(self, image_url, link_url):
        """
        Adiciona um novo anúncio de tela cheia
        
        Args:
            image_url (str): URL da imagem no Imgur
            link_url (str): URL de destino do anúncio
            
        Returns:
            str: ID do anúncio criado
        """
        try:
            fullscreen_ref = self.ref.child('fullscreenAds')
            new_ad = {
                'imageUrl': image_url,
                'linkUrl': link_url,
                'impressions': 0,
                'clicks': 0,
                'createdAt': datetime.now().isoformat(),
                'lastShown': None
            }
            ad_ref = fullscreen_ref.push(new_ad)
            return ad_ref.key
        except Exception as e:
            print(f"Erro ao adicionar anúncio de tela cheia: {str(e)}")
            return None
    
    def update_banner_ad(self, ad_id, image_url, link_url):
        """
        Atualiza um anúncio de banner existente
        
        Args:
            ad_id (str): ID do anúncio
            image_url (str): Nova URL da imagem
            link_url (str): Nova URL de destino
            
        Returns:
            bool: True se bem-sucedido, False caso contrário
        """
        try:
            banner_ref = self.ref.child(f'bannerAds/{ad_id}')
            
            # Verificar se o anúncio existe
            ad_data = banner_ref.get()
            if not ad_data:
                return False
            
            # Atualizar apenas os campos necessários
            updates = {
                'imageUrl': image_url,
                'linkUrl': link_url,
                'updatedAt': datetime.now().isoformat()
            }
            
            banner_ref.update(updates)
            return True
        except Exception as e:
            print(f"Erro ao atualizar banner: {str(e)}")
            return False
    
    def update_fullscreen_ad(self, ad_id, image_url, link_url):
        """
        Atualiza um anúncio de tela cheia existente
        
        Args:
            ad_id (str): ID do anúncio
            image_url (str): Nova URL da imagem
            link_url (str): Nova URL de destino
            
        Returns:
            bool: True se bem-sucedido, False caso contrário
        """
        try:
            fullscreen_ref = self.ref.child(f'fullscreenAds/{ad_id}')
            
            # Verificar se o anúncio existe
            ad_data = fullscreen_ref.get()
            if not ad_data:
                return False
            
            # Atualizar apenas os campos necessários
            updates = {
                'imageUrl': image_url,
                'linkUrl': link_url,
                'updatedAt': datetime.now().isoformat()
            }
            
            fullscreen_ref.update(updates)
            return True
        except Exception as e:
            print(f"Erro ao atualizar anúncio de tela cheia: {str(e)}")
            return False
    
    def delete_banner_ad(self, ad_id):
        """
        Exclui um anúncio de banner
        
        Args:
            ad_id (str): ID do anúncio
            
        Returns:
            bool: True se bem-sucedido, False caso contrário
        """
        try:
            banner_ref = self.ref.child(f'bannerAds/{ad_id}')
            
            # Verificar se o anúncio existe
            ad_data = banner_ref.get()
            if not ad_data:
                return False
            
            # Excluir o anúncio
            banner_ref.delete()
            return True
        except Exception as e:
            print(f"Erro ao excluir banner: {str(e)}")
            return False
    
    def delete_fullscreen_ad(self, ad_id):
        """
        Exclui um anúncio de tela cheia
        
        Args:
            ad_id (str): ID do anúncio
            
        Returns:
            bool: True se bem-sucedido, False caso contrário
        """
        try:
            fullscreen_ref = self.ref.child(f'fullscreenAds/{ad_id}')
            
            # Verificar se o anúncio existe
            ad_data = fullscreen_ref.get()
            if not ad_data:
                return False
            
            # Excluir o anúncio
            fullscreen_ref.delete()
            return True
        except Exception as e:
            print(f"Erro ao excluir anúncio de tela cheia: {str(e)}")
            return False
    
    def record_impression(self, ad_id, ad_type):
        """
        Registra uma impressão de anúncio
        
        Args:
            ad_id (str): ID do anúncio
            ad_type (str): Tipo do anúncio ('banner' ou 'fullscreen')
            
        Returns:
            bool: True se bem-sucedido, False caso contrário
        """
        try:
            type_path = 'bannerAds' if ad_type == 'banner' else 'fullscreenAds'
            ad_ref = self.ref.child(f"{type_path}/{ad_id}")
            
            # Obter contagem atual
            ad_data = ad_ref.get() or {}
            current_count = ad_data.get('impressions', 0)
            
            # Atualizar contagem e timestamp
            updates = {
                'impressions': current_count + 1,
                'lastShown': datetime.now().isoformat()
            }
            
            ad_ref.update(updates)
            return True
        except Exception as e:
            print(f"Erro ao registrar impressão: {str(e)}")
            return False
    
    def record_click(self, ad_id, ad_type):
        """
        Registra um clique em anúncio
        
        Args:
            ad_id (str): ID do anúncio
            ad_type (str): Tipo do anúncio ('banner' ou 'fullscreen')
            
        Returns:
            bool: True se bem-sucedido, False caso contrário
        """
        try:
            type_path = 'bannerAds' if ad_type == 'banner' else 'fullscreenAds'
            ad_ref = self.ref.child(f"{type_path}/{ad_id}")
            
            # Obter contagem atual
            ad_data = ad_ref.get() or {}
            current_count = ad_data.get('clicks', 0)
            
            # Atualizar contagem
            ad_ref.update({'clicks': current_count + 1})
            return True
        except Exception as e:
            print(f"Erro ao registrar clique: {str(e)}")
            return False
    
    def get_metrics(self):
        """
        Obtém métricas de todos os anúncios
        
        Returns:
            dict: Métricas de anúncios
        """
        try:
            banner_ads = self.get_banner_ads()
            fullscreen_ads = self.get_fullscreen_ads()
            
            total_banner_impressions = sum(ad.get('impressions', 0) for ad in banner_ads)
            total_banner_clicks = sum(ad.get('clicks', 0) for ad in banner_ads)
            
            total_fullscreen_impressions = sum(ad.get('impressions', 0) for ad in fullscreen_ads)
            total_fullscreen_clicks = sum(ad.get('clicks', 0) for ad in fullscreen_ads)
            
            banner_ctr = (total_banner_clicks / total_banner_impressions * 100) if total_banner_impressions > 0 else 0
            fullscreen_ctr = (total_fullscreen_clicks / total_fullscreen_impressions * 100) if total_fullscreen_impressions > 0 else 0
            
            return {
                'banner': {
                    'ads_count': len(banner_ads),
                    'total_impressions': total_banner_impressions,
                    'total_clicks': total_banner_clicks,
                    'ctr': round(banner_ctr, 2),
                    'ads': banner_ads
                },
                'fullscreen': {
                    'ads_count': len(fullscreen_ads),
                    'total_impressions': total_fullscreen_impressions,
                    'total_clicks': total_fullscreen_clicks,
                    'ctr': round(fullscreen_ctr, 2),
                    'ads': fullscreen_ads
                }
            }
        except Exception as e:
            print(f"Erro ao obter métricas: {str(e)}")
            return {
                'banner': {'ads_count': 0, 'total_impressions': 0, 'total_clicks': 0, 'ctr': 0, 'ads': []},
                'fullscreen': {'ads_count': 0, 'total_impressions': 0, 'total_clicks': 0, 'ctr': 0, 'ads': []}
            }
