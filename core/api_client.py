import requests
import time
from typing import List, Optional, Any
from core.config import config


class BaseAPIClient:
    """
    Cliente base da API Lyceum
    - Autenticação: Basic Auth
    - Método: GET somente
    - Paginação automática (page 0 → última página válida)
    - size fixo conforme configuração
    """

    def __init__(self):
        if not all([
            config.LYCEUM_BASE_URL,
            config.LYCEUM_USERNAME,
            config.LYCEUM_PASSWORD
        ]):
            raise RuntimeError("Credenciais da API Lyceum não carregadas corretamente")

        self.base_url = config.LYCEUM_BASE_URL.rstrip("/")
        self.auth = (config.LYCEUM_USERNAME, config.LYCEUM_PASSWORD)
        self.headers = {
            "Accept": "application/json"
        }

    def get(self, endpoint: str, params: Optional[dict] = None) -> Any:
        """
        Executa uma requisição GET simples.
        Retorna JSON ou None em caso de erro HTTP.
        """
        url = f"{self.base_url}{endpoint}"

        try:
            response = requests.get(
                url,
                auth=self.auth,
                headers=self.headers,
                params=params,
                timeout=config.API_TIMEOUT
            )

            if response.status_code != 200:
                print(f"⚠️ HTTP {response.status_code} → {url}")
                return None

            return response.json()
        except Exception as e:
            print(f"⚠️ Erro na requisição → {url}: {e}")
            return None

    def get_paginated(self, endpoint: str) -> List[dict]:
        """
        Percorre todas as páginas disponíveis da API.
        A API retorna {'data': [...]} em vez de lista direta.
        """
        results: List[dict] = []
        page = config.API_PAGE_START
        
        print(f"  🔄 Iniciando paginação no endpoint: {endpoint}")
        
        while True:
            params = {
                "page": page,
                "size": config.API_PAGE_SIZE
            }
            
            print(f"    📄 Página {page} (size={config.API_PAGE_SIZE})...")
            
            data = self.get(endpoint, params=params)
            
            # Fim da paginação
            if not data:
                print(f"    ⏹️  Página {page} retornou None")
                break
            
            # Verifica se é um dicionário com chave 'data'
            if isinstance(data, dict) and 'data' in data:
                items = data['data']
                if not isinstance(items, list):
                    print(f"    ⚠️  'data' não é uma lista: {type(items)}")
                    break
                    
                if len(items) == 0:
                    print(f"    ✅ Página {page} vazia - fim da paginação")
                    break
                    
                results.extend(items)
                print(f"    📊 Página {page}: {len(items)} registros (total: {len(results)})")
                
                # Verifica se há mais páginas (pela resposta total)
                total_count = data.get('X-Total-Count')  # Vem no header, não no body
                # Na verdade, o total count vem no header, não no JSON
                # Vamos confiar na página vazia para determinar o fim
                
            elif isinstance(data, list):
                # Formato alternativo: lista direta
                if len(data) == 0:
                    print(f"    ✅ Página {page} vazia - fim da paginação")
                    break
                    
                results.extend(data)
                print(f"    📊 Página {page}: {len(data)} registros (total: {len(results)})")
            else:
                print(f"    ⚠️  Formato de resposta inesperado: {type(data)}")
                print(f"    Conteúdo: {str(data)[:200]}...")
                break
            
            page += 1

            # Evita sobrecarga na API
            time.sleep(config.API_DELAY_BETWEEN_REQUESTS)
        
        print(f"  ✅ Paginação completa: {len(results)} registros no total")
        return results


# ==================================================
# CLIENTES ESPECÍFICOS POR ENTIDADE
# ==================================================

class CursoAPIClient(BaseAPIClient):
    def get_cursos(self) -> List[dict]:
        return self.get_paginated("/v2/tabela/cursos")


class CurriculoAPIClient(BaseAPIClient):
    def get_curriculos(self) -> List[dict]:
        return self.get_paginated("/v2/tabela/curriculos")


class AlunoAPIClient(BaseAPIClient):
    def get_alunos(self) -> List[dict]:
        return self.get_paginated("/v2/tabela/alunos")
    
    def get_aluno(self, matricula: str) -> Optional[dict]:
        """Obtém um aluno específico por matrícula"""
        endpoint = f"/v2/tabela/alunos"
        params = {"pk[aluno]": matricula}
        data = self.get(endpoint, params=params)
        if data and isinstance(data, dict) and 'data' in data:
            items = data['data']
            if isinstance(items, list) and len(items) > 0:
                return items[0]
        return None


class DocenteAPIClient(BaseAPIClient):
    def get_docentes(self) -> List[dict]:
        return self.get_paginated("/v2/tabela/docente")


class DisciplinaAPIClient(BaseAPIClient):
    def get_disciplinas(self) -> List[dict]:
        return self.get_paginated("/v2/tabela/disciplinas")


class TurmaAPIClient(BaseAPIClient):
    def get_turmas(self) -> List[dict]:
        return self.get_paginated("/v2/tabela/turmas")


class TurmaDocenteAPIClient(BaseAPIClient):
    def get_turmas_docentes(self) -> List[dict]:
        return self.get_paginated("/v2/tabela/turma-docente")