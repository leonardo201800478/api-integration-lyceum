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

class AlunoAPIClient(BaseAPIClient):
    """Cliente específico para dados de alunos"""
    
    def get_alunos_ativos(self) -> List[Dict]:
        """Busca todos os alunos ativos"""
        all_alunos = []
        endpoint = "/v2/tabela/alunos"
        filters = {"sit_aluno": "Ativo"}
        
        print("🔍 Buscando alunos ativos da API...")
        
        for page_data in self.get_all_data(endpoint, filters):
            all_alunos.extend(page_data)
            print(f"📄 Página com {len(page_data)} alunos ativos")
        
        print(f"✅ Total de alunos ativos encontrados: {len(all_alunos)}")
        return all_alunos
    
    def get_aluno_by_matricula(self, matricula: str) -> Optional[Dict]:
        """Busca aluno específico por matrícula"""
        endpoint = "/v2/tabela/alunos"
        data = self.get_paginated_data(endpoint, 1, 1, {"pk[aluno]": matricula})
        return data[0] if data else None