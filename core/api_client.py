import logging
import random
import time
from typing import Any, cast

import requests
import urllib3
from requests.adapters import HTTPAdapter

from core.config import config

logger = logging.getLogger("lyceum_sync.api")

# ============================================================================
# RETENTATIVA DA API
# ============================================================================

# Execução unattended: falhas transitórias não devem derrubar o processo.
RETRY_INITIAL_DELAY = 5.0
RETRY_MAX_DELAY = 300.0
RETRY_BACKOFF_FACTOR = 2.0
RETRY_JITTER = 3.0

# Respostas que normalmente indicam indisponibilidade transitória.
RETRYABLE_STATUS_CODES = frozenset({
    408, 429,
    500, 502, 503, 504, 520, 521, 522, 523, 524,
})

HTTP_POOL_CONNECTIONS = 4
HTTP_POOL_MAXSIZE = 4


def _retry_delay(attempt: int) -> float:
    """
    Calcula o intervalo de espera entre tentativas.

    O backoff cresce de forma exponencial até o limite de 5 minutos,
    com pequeno jitter para evitar reconexões rígidas.

    Parameters
    ----------
    attempt:
        Número da tentativa que falhou.

    Returns
    -------
    float
        Intervalo em segundos.
    """
    delay = min(
        RETRY_MAX_DELAY,
        RETRY_INITIAL_DELAY
        * (RETRY_BACKOFF_FACTOR ** max(0, attempt - 1)),
    )

    return min(
        RETRY_MAX_DELAY,
        delay + random.uniform(0, RETRY_JITTER),
    )


class BaseAPIClient:
    """
    Cliente base resiliente da API Lyceum.

    Responsabilidades:
        - autenticação Basic Auth;
        - requisições GET;
        - retry indefinido em falhas transitórias;
        - recriação da sessão após falha de transporte;
        - paginação automática;
        - paginação individual;
        - fechamento seguro da sessão.

    A chamada get() não retorna None para uma falha transitória. Ela
    permanece tentando a mesma requisição até obter uma resposta válida
    ou até o operador interromper o processo.
    """

    def __init__(
        self,
        session: requests.Session | None = None,
    ):
        """
        Inicializa o cliente da API.

        Parameters
        ----------
        session:
            Sessão requests opcional.
        """
        missing = []

        if not config.LYCEUM_BASE_URL:
            missing.append("LYCEUM_BASE_URL")

        if not config.LYCEUM_USERNAME:
            missing.append("LYCEUM_USERNAME")

        if not config.LYCEUM_PASSWORD:
            missing.append("LYCEUM_PASSWORD")

        if missing:
            raise RuntimeError(
                "Credenciais da API Lyceum incompletas. "
                "Variáveis faltando no .env: "
                + ", ".join(missing)
            )

        base_url = cast(str, config.LYCEUM_BASE_URL)
        username = cast(str, config.LYCEUM_USERNAME)
        password = cast(str, config.LYCEUM_PASSWORD)

        self.base_url = base_url.rstrip("/")
        self.auth: tuple[str, str] = (username, password)
        self.headers = {
            "Accept": "application/json",
        }

        self.session = session or self._create_session()

        if config.LYCEUM_SSL_VERIFY is False:
            urllib3.disable_warnings(
                urllib3.exceptions.InsecureRequestWarning
            )

    def _create_session(self) -> requests.Session:
        """
        Cria uma nova sessão HTTP com pool de conexões.

        O adapter não executa retries finitos. A política de retry infinito
        fica centralizada em get(), permitindo também recriar a Session
        quando a conexão persistente fica em estado inválido.
        """
        session = requests.Session()

        adapter = HTTPAdapter(
            pool_connections=HTTP_POOL_CONNECTIONS,
            pool_maxsize=HTTP_POOL_MAXSIZE,
            max_retries=0,
        )

        session.mount("http://", adapter)
        session.mount("https://", adapter)

        session.auth = self.auth
        session.headers.update(self.headers)

        return session

    def _close_session(self) -> None:
        """Fecha a sessão HTTP atual sem propagar erro de fechamento."""
        session = getattr(self, "session", None)

        if session is None:
            return

        try:
            session.close()
        except Exception:
            logger.debug(
                "Falha ao fechar sessão HTTP.",
                exc_info=True,
            )

    def _recreate_session(self) -> None:
        """Descarta a sessão atual e cria uma nova sessão HTTP."""
        self._close_session()
        self.session = self._create_session()

    def _sleep_before_retry(
        self,
        attempt: int,
        reason: str,
        endpoint: str,
    ) -> None:
        """
        Aguarda antes da próxima tentativa e registra o motivo.
        """
        delay = _retry_delay(attempt)

        logger.warning(
            "API indisponível | endpoint=%s | tentativa=%d | "
            "nova tentativa em %.1fs | motivo=%s",
            endpoint,
            attempt,
            delay,
            reason,
        )

        time.sleep(delay)

    @staticmethod
    def _is_retryable_status(status_code: int) -> bool:
        """Retorna True quando o status HTTP representa falha transitória."""
        return status_code in RETRYABLE_STATUS_CODES

    # ------------------------------------------------------------------------
    # GET
    # ------------------------------------------------------------------------

    def get(
        self,
        endpoint: str,
        params: dict | None = None,
    ) -> Any:
        """
        Executa uma requisição GET com recuperação indefinida.

        São repetidos indefinidamente:
            - erro de conexão;
            - timeout;
            - reset da conexão;
            - erro de transporte;
            - HTTP 408/429;
            - HTTP 5xx transitório;
            - resposta 200 cujo JSON esteja inválido.

        Erros HTTP não transitórios, como 401, 403 e 404, são propagados
        para não mascarar problemas permanentes de configuração ou endpoint.

        Parameters
        ----------
        endpoint:
            Endpoint relativo.

        params:
            Parâmetros da query string.

        Returns
        -------
        Any
            JSON retornado pela API.

        Raises
        ------
        requests.HTTPError
            Para respostas HTTP não transitórias.
        KeyboardInterrupt
            Para interrupção manual do operador.
        """
        url = f"{self.base_url}{endpoint}"
        attempt = 0

        while True:
            try:
                response = self.session.get(
                    url,
                    auth=self.auth,
                    headers=self.headers,
                    params=params,
                    timeout=config.API_TIMEOUT,
                    verify=config.LYCEUM_SSL_VERIFY,
                )

                status = response.status_code

                if status == 200:
                    try:
                        return response.json()
                    except ValueError as exc:
                        attempt += 1

                        logger.warning(
                            "JSON inválido | endpoint=%s | tentativa=%d | "
                            "erro=%s",
                            endpoint,
                            attempt,
                            exc,
                        )

                        self._recreate_session()
                        self._sleep_before_retry(
                            attempt,
                            f"JSON inválido: {exc}",
                            endpoint,
                        )
                        continue

                if self._is_retryable_status(status):
                    attempt += 1

                    reason = (
                        f"HTTP {status} "
                        f"({response.reason or 'sem descrição'})"
                    )

                    logger.warning(
                        "Resposta transitória do servidor | endpoint=%s | "
                        "HTTP=%d | tentativa=%d",
                        endpoint,
                        status,
                        attempt,
                    )

                    self._recreate_session()
                    self._sleep_before_retry(
                        attempt,
                        reason,
                        endpoint,
                    )
                    continue

                # Não tratar 401/403/404 etc. como página vazia.
                response.raise_for_status()

                raise requests.HTTPError(
                    f"HTTP inesperado {status} para {url}",
                    response=response,
                )

            except KeyboardInterrupt:
                raise

            except requests.HTTPError:
                # Erro HTTP não transitório: propaga para o importador.
                # Isso evita transformar credenciais inválidas, endpoint
                # inexistente etc. em um retry infinito.
                raise

            except requests.RequestException as exc:
                attempt += 1

                logger.warning(
                    "Falha de comunicação com a API | endpoint=%s | "
                    "tentativa=%d | erro=%s",
                    endpoint,
                    attempt,
                    exc,
                    exc_info=True,
                )

                self._recreate_session()
                self._sleep_before_retry(
                    attempt,
                    str(exc),
                    endpoint,
                )

    # ------------------------------------------------------------------------
    # PAGINAÇÃO AUTOMÁTICA
    # ------------------------------------------------------------------------

    def get_paginated(
        self,
        endpoint: str,
        params: dict | None = None,
    ) -> list[dict]:
        """
        Percorre todas as páginas disponíveis.

        Uma falha transitória não encerra a paginação porque get() somente
        retorna após obter uma resposta válida.

        A API pode retornar {"data": [...]} ou diretamente [...].
        """
        results: list[dict] = []
        page = config.API_PAGE_START

        logger.info(
            "Iniciando paginação | endpoint=%s",
            endpoint,
        )

        if params:
            logger.info(
                "Parâmetros da paginação | %s",
                params,
            )

        while True:
            request_params = {
                "page": page,
                "size": config.API_PAGE_SIZE,
            }

            if params:
                request_params.update(params)

            logger.info(
                "Consultando página | endpoint=%s | page=%d | size=%d",
                endpoint,
                page,
                config.API_PAGE_SIZE,
            )

            data = self.get(
                endpoint,
                params=request_params,
            )

            # Nunca interpretar None como fim da API.
            if data is None:
                raise RuntimeError(
                    f"API retornou None inesperadamente para "
                    f"{endpoint}, página {page}."
                )

            if isinstance(data, dict) and "data" in data:
                items = data["data"]

                if not isinstance(items, list):
                    raise RuntimeError(
                        "Campo 'data' não é uma lista: "
                        f"{type(items).__name__}"
                    )

                if not items:
                    logger.info(
                        "Paginação finalizada | página=%d vazia.",
                        page,
                    )
                    break

                results.extend(items)

                logger.info(
                    "Página=%d | registros=%d | acumulado=%d",
                    page,
                    len(items),
                    len(results),
                )

            elif isinstance(data, list):
                if not data:
                    logger.info(
                        "Paginação finalizada | página=%d vazia.",
                        page,
                    )
                    break

                results.extend(data)

                logger.info(
                    "Página=%d | registros=%d | acumulado=%d",
                    page,
                    len(data),
                    len(results),
                )

            else:
                raise RuntimeError(
                    "Formato inesperado retornado pela API: "
                    f"{type(data).__name__}"
                )

            page += 1

            if config.API_DELAY_BETWEEN_REQUESTS > 0:
                time.sleep(
                    config.API_DELAY_BETWEEN_REQUESTS
                )

        logger.info(
            "Paginação completa | endpoint=%s | registros=%d",
            endpoint,
            len(results),
        )

        return results

    # ------------------------------------------------------------------------
    # FECHAMENTO
    # ------------------------------------------------------------------------

    def close(self):
        """Fecha a sessão HTTP atual de forma segura."""
        self._close_session()



# ============================================================================
# FÁBRICA
# ============================================================================

class APIClientFactory:
    """
    Fábrica de clientes com sessões independentes.
    """

    @staticmethod
    def create_curso_client():
        return CursoAPIClient()

    @staticmethod
    def create_curriculo_client():
        return CurriculoAPIClient()

    @staticmethod
    def create_aluno_client():
        return AlunoAPIClient()

    @staticmethod
    def create_docente_client():
        return DocenteAPIClient()

    @staticmethod
    def create_disciplina_client():
        return DisciplinaAPIClient()

    @staticmethod
    def create_turma_client():
        return TurmaAPIClient()

    @staticmethod
    def create_turma_docente_client():
        return TurmaDocenteAPIClient()

    @staticmethod
    def create_matricula_client():
        return MatriculaAPIClient()

    @staticmethod
    def create_grade_client():
        return GradeAPIClient()

    @staticmethod
    def create_coordenacao_client():
        return CoordenacaoAPIClient()

    @staticmethod
    def create_pessoa_client():
        return PessoaAPIClient()

    @staticmethod
    def create_prova_disciplina_client():
        return ProvaDisciplinaAPIClient()

    @staticmethod
    def create_prova_client():
        return ProvaAPIClient()


# ============================================================================
# CURSOS
# ============================================================================

class CursoAPIClient(BaseAPIClient):

    def get_cursos(self) -> list[dict]:
        return self.get_paginated(
            "/v2/tabela/cursos"
        )


# ============================================================================
# CURRÍCULOS
# ============================================================================

class CurriculoAPIClient(BaseAPIClient):

    def get_curriculos(self) -> list[dict]:
        return self.get_paginated(
            "/v2/tabela/curriculos"
        )

    def get_curriculo(
        self,
        curriculo_code: str
    ) -> dict | None:

        data = self.get(
            "/v2/tabela/curriculos",
            params={
                "pk[curriculo]": curriculo_code
            }
        )

        if (
            isinstance(data, dict)
            and "data" in data
        ):

            items = data["data"]

            if (
                isinstance(items, list)
                and items
            ):

                return items[0]

        return None


# ============================================================================
# ALUNOS
# ============================================================================

class AlunoAPIClient(BaseAPIClient):

    def get_alunos(self) -> list[dict]:
        return self.get_paginated(
            "/v2/tabela/alunos"
        )

    def get_aluno(
        self,
        matricula: str
    ) -> dict | None:

        data = self.get(
            "/v2/tabela/alunos",
            params={
                "pk[aluno]": matricula
            }
        )

        if (
            isinstance(data, dict)
            and "data" in data
        ):

            items = data["data"]

            if (
                isinstance(items, list)
                and items
            ):

                return items[0]

        return None


# ============================================================================
# DOCENTES
# ============================================================================

class DocenteAPIClient(BaseAPIClient):

    def get_docentes(self) -> list[dict]:
        return self.get_paginated(
            "/v2/tabela/docente"
        )


# ============================================================================
# DISCIPLINAS
# ============================================================================

class DisciplinaAPIClient(BaseAPIClient):

    def get_disciplinas(self) -> list[dict]:
        return self.get_paginated(
            "/v2/tabela/disciplinas"
        )


# ============================================================================
# TURMAS
# ============================================================================

class TurmaAPIClient(BaseAPIClient):

    def get_turmas(self) -> list[dict]:

        return self.get_paginated(
            "/v2/tabela/turmas"
        )

    def get_turmas_filtradas(
        self,
        ano: int | None = None,
        semestre: int | None = None
    ) -> list[dict]:
        """
        Obtém todas as turmas usando filtros da API.
        """

        params = {}

        if ano is not None:
            params["ano"] = ano

        if semestre is not None:
            params["semestre"] = semestre

        return self.get_paginated(
            "/v2/tabela/turmas",
            params=params
        )

    def get_turmas_from_page(
        self,
        page: int,
        page_size: int | None = None,
        ano: int | None = None,
        semestre: int | None = None
    ) -> list[dict]:
        """
        Obtém somente uma página de turmas.

        Este método é utilizado pelas sincronizações
        incrementais para que o processo não precise
        carregar toda a API em memória.

        Parameters
        ----------
        page:
            Página desejada.

        page_size:
            Quantidade de registros da página.

        ano:
            Filtro opcional de ano.

        semestre:
            Filtro opcional de semestre.
        """

        if page_size is None:

            page_size = config.API_PAGE_SIZE

        params = {
            "page": page,
            "size": page_size
        }

        if ano is not None:
            params["ano"] = ano

        if semestre is not None:
            params["semestre"] = semestre

        data = self.get(
            "/v2/tabela/turmas",
            params=params
        )

        if not data:
            return []

        if (
            isinstance(data, dict)
            and "data" in data
        ):

            items = data["data"]

            if isinstance(items, list):

                return items

            return []

        if isinstance(data, list):

            return data

        return []


# ============================================================================
# TURMA DOCENTE
# ============================================================================

class TurmaDocenteAPIClient(BaseAPIClient):

    def get_turmas_docentes(self) -> list[dict]:

        return self.get_paginated(
            "/v2/tabela/turma-docente"
        )

    def get_turmas_docentes_filtradas(
        self,
        ano: int | None = None,
        semestre: int | None = None
    ) -> list[dict]:

        params = {}

        if ano is not None:
            params["ano"] = ano

        if semestre is not None:
            params["semestre"] = semestre

        return self.get_paginated(
            "/v2/tabela/turma-docente",
            params=params
        )

    def get_turmas_docentes_from_page(
        self,
        start_page: int,
        page_size: int | None = None,
        ano: int | None = None,
        semestre: int | None = None
    ) -> list[dict]:
        """
        Obtém somente uma página de turma-docente.

        Inclui filtros opcionais de ano e semestre.
        """

        if page_size is None:

            page_size = config.API_PAGE_SIZE

        params = {
            "page": start_page,
            "size": page_size
        }

        if ano is not None:
            params["ano"] = ano

        if semestre is not None:
            params["semestre"] = semestre

        data = self.get(
            "/v2/tabela/turma-docente",
            params=params
        )

        if not data:
            return []

        if (
            isinstance(data, dict)
            and "data" in data
        ):

            items = data["data"]

            if isinstance(items, list):

                return items

            return []

        if isinstance(data, list):

            return data

        return []


# ============================================================================
# MATRÍCULAS
# ============================================================================

class MatriculaAPIClient(BaseAPIClient):

    def get_matriculas(self) -> list[dict]:

        return self.get_paginated(
            "/v2/tabela/matriculas"
        )

    def get_matriculas_filtradas(
        self,
        ano: int | None = None,
        semestre: int | None = None
    ) -> list[dict]:

        params = {}

        if ano is not None:
            params["ano"] = ano

        if semestre is not None:
            params["semestre"] = semestre

        return self.get_paginated(
            "/v2/tabela/matriculas",
            params=params
        )

    def get_matriculas_by_aluno(
        self,
        aluno_code: str
    ) -> list[dict]:

        return self.get_paginated(
            "/v2/tabela/matriculas",
            params={
                "pk[aluno]": aluno_code
            }
        )

    def get_matriculas_by_turma(
        self,
        turma_code: str
    ) -> list[dict]:

        return self.get_paginated(
            "/v2/tabela/matriculas",
            params={
                "pk[turma]": turma_code
            }
        )


# ============================================================================
# GRADE
# ============================================================================

class GradeAPIClient(BaseAPIClient):

    def get_grades(self) -> list[dict]:

        return self.get_paginated(
            "/v2/tabela/grades"
        )


# ============================================================================
# PESSOA
# ============================================================================

class PessoaAPIClient(BaseAPIClient):

    def get_pessoas(self) -> list[dict]:

        return self.get_paginated(
            "/v2/tabela/pessoas"
        )

    def get_pessoa_by_id(
        self,
        cod_pessoa: int
    ) -> dict | None:

        data = self.get(
            "/v2/tabela/pessoas",
            params={
                "pk[pessoa]": cod_pessoa
            }
        )

        if (
            isinstance(data, dict)
            and "data" in data
        ):

            items = data["data"]

            if (
                isinstance(items, list)
                and items
            ):

                return items[0]

        elif (
            isinstance(data, dict)
            and "pessoa" in data
        ):

            return data

        elif (
            isinstance(data, list)
            and data
        ):

            return data[0]

        return None

    def get_pessoa_detalhada(
        self,
        id_pessoa: int
    ) -> dict | None:

        data = self.get(
            f"/v2/pessoas/idPessoa/"
            f"{id_pessoa}/obterPessoa"
        )

        if (
            isinstance(data, dict)
            and "data" in data
        ):

            return data["data"]

        if isinstance(data, dict):

            return data

        return None


# ============================================================================
# COORDENAÇÃO
# ============================================================================

class CoordenacaoAPIClient(BaseAPIClient):

    def get_coordenacoes(self) -> list[dict]:

        return self.get_paginated(
            "/v2/tabela/coordenacao"
        )

    def get_coordenacoes_filtradas(
        self,
        ano: int | None = None,
        semestre: int | None = None
    ) -> list[dict]:

        params = {}

        if ano is not None:
            params["ano"] = ano

        if semestre is not None:
            params["semestre"] = semestre

        return self.get_paginated(
            "/v2/tabela/coordenacao",
            params=params
        )


# ============================================================================
# PROVAS-DISCIPLINAS
# ============================================================================

class ProvaDisciplinaAPIClient(BaseAPIClient):

    def get_provas_disciplinas(self) -> list[dict]:

        return self.get_paginated(
            "/v2/tabela/provas-disciplinas"
        )

    def get_provas_disciplinas_filtradas(
        self,
        **kwargs
    ) -> list[dict]:

        return self.get_paginated(
            "/v2/tabela/provas-disciplinas",
            params=kwargs
        )


# ============================================================================
# PROVAS
# ============================================================================

class ProvaAPIClient(BaseAPIClient):

    def get_prova(
        self,
        ano: int,
        disciplina: str,
        prova: str,
        semestre: int,
        turma: str
    ) -> dict | None:

        params = {
            "pk[ano]": ano,
            "pk[disciplina]": disciplina,
            "pk[prova]": prova,
            "pk[semestre]": semestre,
            "pk[turma]": turma
        }

        data = self.get(
            "/v2/tabela/provas",
            params=params
        )

        if isinstance(data, dict):

            if "data" in data:

                items = data["data"]

                if (
                    isinstance(items, list)
                    and items
                ):

                    return items[0]

            else:

                return data

        return None


# ============================================================================
# FUNÇÕES DE CONVENIÊNCIA
# ============================================================================

def get_curriculo_client():
    return APIClientFactory.create_curriculo_client()


def get_aluno_client():
    return APIClientFactory.create_aluno_client()


def get_curso_client():
    return APIClientFactory.create_curso_client()


def get_docente_client():
    return APIClientFactory.create_docente_client()


def get_disciplina_client():
    return APIClientFactory.create_disciplina_client()


def get_turma_client():
    return APIClientFactory.create_turma_client()


def get_turma_docente_client():
    return APIClientFactory.create_turma_docente_client()


def get_matricula_client():
    return APIClientFactory.create_matricula_client()


def get_grade_client():
    return APIClientFactory.create_grade_client()


def get_coordenacao_client():
    return APIClientFactory.create_coordenacao_client()


def get_pessoa_client():
    return APIClientFactory.create_pessoa_client()


def get_prova_disciplina_client():
    return APIClientFactory.create_prova_disciplina_client()


def get_prova_client():
    return APIClientFactory.create_prova_client()