import requests
import time
from typing import List, Optional, Any, Dict
from core.config import config


class BaseAPIClient:
    """
    Cliente base da API Lyceum
    - Autenticação: Basic Auth
    - Método: GET somente
    - Paginação automática (page 0 → última página válida)
    - size fixo conforme configuração
    """

    def __init__(self, session: Optional[requests.Session] = None):
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
        # Usar sessão fornecida ou criar uma nova
        self.session = session or requests.Session()

    def get(self, endpoint: str, params: Optional[dict] = None) -> Any:
        """
        Executa uma requisição GET simples.
        Retorna JSON ou None em caso de erro HTTP.
        """
        url = f"{self.base_url}{endpoint}"

        try:
            response = self.session.get(
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

    def get_paginated(self, endpoint: str, params: Optional[Dict] = None) -> List[dict]:
        """
        Percorre todas as páginas disponíveis da API.
        A API retorna {'data': [...]} em vez de lista direta.
        
        Args:
            endpoint: Endpoint da API
            params: Parâmetros adicionais para a requisição (opcional)
        """
        results: List[dict] = []
        page = config.API_PAGE_START
        
        print(f"  🔄 Iniciando paginação no endpoint: {endpoint}")
        if params:
            print(f"  📋 Parâmetros: {params}")
        
        while True:
            # Base parameters - página e tamanho
            request_params = {
                "page": page,
                "size": config.API_PAGE_SIZE
            }
            
            # Adicionar parâmetros extras se fornecidos
            if params:
                request_params.update(params)
            
            print(f"    📄 Página {page} (size={config.API_PAGE_SIZE})...")
            
            data = self.get(endpoint, params=request_params)
            
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
    
    def close(self):
        """Fecha a sessão HTTP"""
        if hasattr(self, 'session'):
            self.session.close()


# ==================================================
# FÁBRICA DE CLIENTES - Garante que cada consulta use uma sessão separada
# ==================================================

class APIClientFactory:
    """Fábrica para criar clientes de API com sessões isoladas"""
    
    @staticmethod
    def create_curso_client() -> 'CursoAPIClient':
        """Cria cliente de cursos com sessão isolada"""
        return CursoAPIClient()
    
    @staticmethod
    def create_curriculo_client() -> 'CurriculoAPIClient':
        """Cria cliente de currículos com sessão isolada"""
        return CurriculoAPIClient()
    
    @staticmethod
    def create_aluno_client() -> 'AlunoAPIClient':
        """Cria cliente de alunos com sessão isolada"""
        return AlunoAPIClient()
    
    @staticmethod
    def create_docente_client() -> 'DocenteAPIClient':
        """Cria cliente de docentes com sessão isolada"""
        return DocenteAPIClient()
    
    @staticmethod
    def create_disciplina_client() -> 'DisciplinaAPIClient':
        """Cria cliente de disciplinas com sessão isolada"""
        return DisciplinaAPIClient()
    
    @staticmethod
    def create_turma_client() -> 'TurmaAPIClient':
        """Cria cliente de turmas com sessão isolada"""
        return TurmaAPIClient()
    
    @staticmethod
    def create_turma_docente_client() -> 'TurmaDocenteAPIClient':
        """Cria cliente de turma-docente com sessão isolada"""
        return TurmaDocenteAPIClient()
    
    @staticmethod
    def create_matricula_client() -> 'MatriculaAPIClient':
        """Cria cliente de matrículas com sessão isolada"""
        return MatriculaAPIClient()
    
    @staticmethod
    def create_grade_client() -> 'GradeAPIClient':
        """Cria cliente de grades com sessão isolada"""
        return GradeAPIClient()
    
    @staticmethod
    def create_coordenacao_client() -> 'CoordenacaoAPIClient':
        """Cria cliente de coordenações com sessão isolada"""
        return CoordenacaoAPIClient()
    
    @staticmethod
    def create_pessoa_client() -> 'PessoaAPIClient':
        """Cria cliente de pessoas com sessão isolada"""
        return PessoaAPIClient()


# ==================================================
# CLIENTES ESPECÍFICOS POR ENTIDADE
# ==================================================

class CursoAPIClient(BaseAPIClient):
    def get_cursos(self) -> List[dict]:
        return self.get_paginated("/v2/tabela/cursos")


class CurriculoAPIClient(BaseAPIClient):
    def get_curriculos(self) -> List[dict]:
        """Obtém todos os currículos"""
        return self.get_paginated("/v2/tabela/curriculos")
    
    def get_curriculo(self, curriculo_code: str) -> Optional[dict]:
        """Obtém um currículo específico por código"""
        endpoint = f"/v2/tabela/curriculos"
        params = {"pk[curriculo]": curriculo_code}
        data = self.get(endpoint, params=params)
        if data and isinstance(data, dict) and 'data' in data:
            items = data['data']
            if isinstance(items, list) and len(items) > 0:
                return items[0]
        return None


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
    
    def get_turmas_filtradas(self, ano: Optional[int] = None, semestre: Optional[int] = None) -> List[dict]:
        """Obtém turmas com filtros opcionais de ano e semestre"""
        params = {}
        if ano is not None:
            params["ano"] = ano
        if semestre is not None:
            params["semestre"] = semestre
        return self.get_paginated("/v2/tabela/turmas", params=params)


class TurmaDocenteAPIClient(BaseAPIClient):
    def get_turmas_docentes(self) -> List[dict]:
        return self.get_paginated("/v2/tabela/turma-docente")
    
    def get_turmas_docentes_filtradas(self, ano: Optional[int] = None, semestre: Optional[int] = None) -> List[dict]:
        """Obtém turma-docente com filtros opcionais de ano e semestre"""
        params = {}
        if ano is not None:
            params["ano"] = ano
        if semestre is not None:
            params["semestre"] = semestre
        return self.get_paginated("/v2/tabela/turma-docente", params=params)


class MatriculaAPIClient(BaseAPIClient):
    def get_matriculas(self) -> List[dict]:
        """Obtém todas as matrículas (sem filtros)"""
        return self.get_paginated("/v2/tabela/matriculas")
    
    def get_matriculas_filtradas(self, ano: Optional[int] = None, semestre: Optional[int] = None) -> List[dict]:
        """
        Obtém matrículas com filtros opcionais de ano e semestre
        
        Args:
            ano: Ano para filtrar (opcional)
            semestre: Semestre para filtrar (opcional)
            
        Returns:
            Lista de matrículas filtradas
        """
        params = {}
        if ano is not None:
            params["ano"] = ano
        if semestre is not None:
            params["semestre"] = semestre
        
        print(f"🔍 Buscando matrículas com filtros: ano={ano}, semestre={semestre}")
        return self.get_paginated("/v2/tabela/matriculas", params=params)
    
    def get_matriculas_by_aluno(self, aluno_code: str) -> List[dict]:
        """Obtém matrículas de um aluno específico"""
        params = {"pk[aluno]": aluno_code}
        return self.get_paginated("/v2/tabela/matriculas", params=params)
    
    def get_matriculas_by_turma(self, turma_code: str) -> List[dict]:
        """Obtém matrículas de uma turma específica"""
        params = {"pk[turma]": turma_code}
        return self.get_paginated("/v2/tabela/matriculas", params=params)
    
class GradeAPIClient(BaseAPIClient):
    def get_grades(self) -> List[dict]:
        """Obtém todas as grades"""
        return self.get_paginated("/v2/tabela/grades")
    
class PessoaAPIClient(BaseAPIClient):
    def get_pessoas(self) -> List[dict]:
        """Obtém todas as pessoas"""
        return self.get_paginated("/v2/tabela/pessoas")


class CoordenacaoAPIClient(BaseAPIClient):
    def get_coordenacoes(self) -> List[dict]:
        """
        Obtém todas as coordenações via paginação
        Começa da página 0 com tamanho config.API_PAGE_SIZE (padrão: 100)
        Continua até a última página com dados presentes
        """
        return self.get_paginated("/v2/tabela/coordenacao")
    
    def get_coordenacoes_filtradas(self, ano: Optional[int] = None, semestre: Optional[int] = None) -> List[dict]:
        """
        Obtém coordenações com filtros opcionais de ano e semestre
        Segue o mesmo padrão dos outros clientes (TurmaAPIClient, TurmaDocenteAPIClient, etc.)
        """
        params = {}
        if ano is not None:
            params["ano"] = ano
        if semestre is not None:
            params["semestre"] = semestre
        return self.get_paginated("/v2/tabela/coordenacao", params=params)


# ==================================================
# MÉTODOS DE CONVENIÊNCIA - Mantém compatibilidade
# ==================================================

def get_curriculo_client() -> CurriculoAPIClient:
    """Retorna um cliente de currículo com sessão isolada"""
    return APIClientFactory.create_curriculo_client()

def get_aluno_client() -> AlunoAPIClient:
    """Retorna um cliente de alunos com sessão isolada"""
    return APIClientFactory.create_aluno_client()

def get_curso_client() -> CursoAPIClient:
    """Retorna um cliente de cursos com sessão isolada"""
    return APIClientFactory.create_curso_client()

def get_docente_client() -> DocenteAPIClient:
    """Retorna um cliente de docentes com sessão isolada"""
    return APIClientFactory.create_docente_client()

def get_disciplina_client() -> DisciplinaAPIClient:
    """Retorna um cliente de disciplinas com sessão isolada"""
    return APIClientFactory.create_disciplina_client()

def get_turma_client() -> TurmaAPIClient:
    """Retorna um cliente de turmas com sessão isolada"""
    return APIClientFactory.create_turma_client()

def get_turma_docente_client() -> TurmaDocenteAPIClient:
    """Retorna um cliente de turma-docente com sessão isolada"""
    return APIClientFactory.create_turma_docente_client()

def get_matricula_client() -> MatriculaAPIClient:
    """Retorna um cliente de matrículas com sessão isolada"""
    return APIClientFactory.create_matricula_client()

def get_grade_client() -> GradeAPIClient:
    """Retorna um cliente de grades com sessão isolada"""
    return APIClientFactory.create_grade_client()

def get_coordenacao_client() -> CoordenacaoAPIClient:
    """Retorna um cliente de coordenações com sessão isolada"""
    return APIClientFactory.create_coordenacao_client()

def get_pessoa_client() -> PessoaAPIClient:
    """Retorna um cliente de pessoas com sessão isolada"""
    return APIClientFactory.create_pessoa_client()