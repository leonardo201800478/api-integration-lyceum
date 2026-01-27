import requests
from requests.auth import HTTPBasicAuth
import time
import warnings
from typing import Dict, List, Optional, Generator
from .config import config

warnings.filterwarnings('ignore', message='Unverified HTTPS request')

class BaseAPIClient:
    """Cliente base para API Lyceum"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(config.API_USERNAME, config.API_PASSWORD)
        self.session.verify = False
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'LyceumSync/1.0'
        })
    
    def get_paginated_data(self, endpoint: str, page: int = 1, size: int = None, 
                          filters: Dict = None) -> List[Dict]:
        """Busca dados paginados da API"""
        if size is None:
            size = config.PAGE_SIZE
        
        params = {
            "page": page,
            "size": size,
            **(filters or {})
        }
        
        try:
            response = self.session.get(
                f"{config.API_BASE_URL}{endpoint}",
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict) and 'data' in data:
                    return data['data']
                return data if isinstance(data, list) else []
            elif response.status_code == 404:
                return []
            else:
                print(f"⚠️  Status {response.status_code} para {endpoint} página {page}")
                return []
                
        except Exception as e:
            print(f"❌ Erro ao buscar {endpoint} página {page}: {e}")
            return []
    
    def get_all_data(self, endpoint: str, filters: Dict = None) -> Generator[List[Dict], None, None]:
        """Busca todos os dados paginadamente"""
        page = 1
        
        while page <= config.MAX_PAGES:
            data = self.get_paginated_data(endpoint, page, filters=filters)
            
            if not data:
                break
            
            yield data
            
            # Se veio menos dados que o solicitado, é a última página
            if len(data) < config.PAGE_SIZE:
                break
            
            page += 1
            time.sleep(0.5)  # Delay entre páginas

class CursoAPIClient(BaseAPIClient):
    """Cliente específico para dados de cursos"""
    
    def get_cursos(self) -> List[Dict]:
        """Busca todos os cursos da API"""
        all_cursos = []
        endpoint = "/v2/tabela/cursos"
        
        print("🔍 Buscando cursos da API...")
        
        for page_data in self.get_all_data(endpoint):
            all_cursos.extend(page_data)
            print(f"📄 Página com {len(page_data)} cursos")
        
        print(f"✅ Total de cursos encontrados: {len(all_cursos)}")
        return all_cursos


class CurriculoAPIClient(BaseAPIClient):
    """Cliente específico para dados de currículos"""
    
    def get_curriculos(self) -> List[Dict]:
        """Busca todos os currículos da API"""
        all_curriculos = []
        endpoint = "/v2/tabela/curriculos"
        
        print("🔍 Buscando currículos da API...")
        
        for page_data in self.get_all_data(endpoint):
            all_curriculos.extend(page_data)
            print(f"📄 Página com {len(page_data)} currículos")
        
        print(f"✅ Total de currículos encontrados: {len(all_curriculos)}")
        return all_curriculos