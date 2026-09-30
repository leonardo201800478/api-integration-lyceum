#!/usr/bin/env python3
"""
sync/sync_ly_turmas_by_pk.py

Sincronização da LY_TURMA utilizando o novo endpoint GET por chave primária.

Fluxo
-----
1. Consulta no SQL Server:
       SELECT DISTINCT
           ano,
           periodo,
           turma,
           disciplina
       FROM [lyceum].[dbo].[LY_TURMA_DOCENTE]

2. Cada combinação encontrada é tratada como uma PK de LY_TURMA:
       ano        -> pk[ano]
       periodo    -> pk[semestre]
       turma      -> pk[turma]
       disciplina -> pk[disciplina]

3. Para cada PK é executado:
       GET /v2/tabela/turmas

   com os quatro parâmetros obrigatórios.

4. O retorno da API é persistido na LY_TURMA através de
   LyTurmaModel.batch_insert().

Importante
----------
O novo endpoint não utiliza paginação e não há filtro adicional por ano,
semestre, faculdade ou curso. O conjunto de registros a consultar é definido
exclusivamente pelas quatro PKs distintas existentes em LY_TURMA_DOCENTE.

A diferença de nomenclatura entre as tabelas é tratada explicitamente:
    LY_TURMA_DOCENTE.periodo -> API pk[semestre]

A LY_TURMA não é limpa e nenhum checkpoint de paginação é utilizado.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from typing import Any

import requests

# ============================================================================
# PATH
# ============================================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# ============================================================================
# IMPORTS DO PROJETO
# ============================================================================

from core.config import config
from core.database import get_db_connection
from models.ly_turma import LyTurmaModel

# ============================================================================
# LOGGING
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s | %(levelname)s | "
        "%(name)s | %(message)s"
    ),
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger("sync.ly_turma_by_pk")

# ============================================================================
# CONFIGURAÇÕES
# ============================================================================

DEFAULT_TIMEOUT = 30.0
DEFAULT_DELAY = getattr(
    config,
    "API_DELAY_BETWEEN_REQUESTS",
    0.0,
)

PK_QUERY = """
SELECT DISTINCT
    ano,
    periodo,
    turma,
    disciplina
FROM [lyceum].[dbo].[LY_TURMA_DOCENTE]
WHERE ano IS NOT NULL
  AND periodo IS NOT NULL
  AND turma IS NOT NULL
  AND disciplina IS NOT NULL
ORDER BY
    ano,
    periodo,
    turma,
    disciplina
"""


# ============================================================================
# TIPOS
# ============================================================================

PK = tuple[Any, Any, Any, Any]


# ============================================================================
# BANCO DE DADOS
# ============================================================================

LYCEUM_DB_NAME = "lyceum"


def get_turma_pks() -> list[PK]:
    """
    Obtém todas as PKs distintas de LY_TURMA_DOCENTE.

    A conexão é aberta pelo mecanismo central do projeto
    ``core.database.get_db_connection()``, utilizando o banco Lyceum.
    Não é criada uma connection string própria nem uma variável de ambiente
    adicional para este sync.

    O campo ``periodo`` de LY_TURMA_DOCENTE é mantido como origem do valor
    que será enviado para ``pk[semestre]`` no endpoint de LY_TURMA.

    Returns
    -------
    list[PK]
        Tuplas no formato ``(ano, periodo, turma, disciplina)``.
    """
    with get_db_connection(database_name=LYCEUM_DB_NAME) as connection:
        cursor = connection.cursor()
        cursor.execute(PK_QUERY)

        rows = cursor.fetchall()

        return [
            (
                row.ano,
                row.periodo,
                row.turma,
                row.disciplina,
            )
            for row in rows
        ]


# ============================================================================
# API
# ============================================================================

def build_turma_url() -> str:
    """
    Monta a URL do endpoint de carga de dados de turmas.

    Returns
    -------
    str
        URL completa de /v2/tabela/turmas.
    """
    base_url = config.LYCEUM_BASE_URL.rstrip("/")

    return f"{base_url}/v2/tabela/turmas"


def get_turma_by_pk(
    session: requests.Session,
    pk: PK,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict[str, Any] | None:
    """
    Consulta uma turma utilizando as quatro PKs obrigatórias da API.

    Parameters
    ----------
    session:
        Sessão HTTP autenticada.

    pk:
        Tupla:
            (ano, periodo, turma, disciplina)

        O segundo elemento, periodo, é enviado como pk[semestre].

    timeout:
        Tempo máximo da requisição HTTP em segundos.

    Returns
    -------
    dict | None
        Registro retornado pela API.
        None quando a API responde 404.

    Raises
    ------
    requests.HTTPError
        Para respostas HTTP diferentes de 200 e 404.
    requests.RequestException
        Para erros de comunicação.
    """
    ano, periodo, turma, disciplina = pk

    params = {
        "pk[ano]": str(ano),
        "pk[disciplina]": str(disciplina),
        "pk[semestre]": str(periodo),
        "pk[turma]": str(turma),
    }

    response = session.get(
        build_turma_url(),
        params=params,
        timeout=timeout,
    )

    if response.status_code == 404:
        return None

    response.raise_for_status()

    payload = response.json()

    if not isinstance(payload, dict):
        raise ValueError(
            "Resposta inesperada do endpoint de turmas: "
            f"{type(payload).__name__}."
        )

    return payload


def create_api_session() -> requests.Session:
    """
    Cria uma sessão HTTP com autenticação básica do Lyceum.

    Returns
    -------
    requests.Session
        Sessão configurada para as chamadas GET.
    """
    if not all(
        [
            config.LYCEUM_BASE_URL,
            config.LYCEUM_USERNAME,
            config.LYCEUM_PASSWORD,
        ]
    ):
        raise RuntimeError(
            "Configuração da API Lyceum incompleta."
        )

    session = requests.Session()

    session.auth = (
        config.LYCEUM_USERNAME,
        config.LYCEUM_PASSWORD,
    )

    session.headers.update(
        {
            "Accept": "*/*",
        }
    )

    return session


# ============================================================================
# NORMALIZAÇÃO
# ============================================================================

def normalize_api_record(
    item: dict[str, Any],
    pk: PK,
) -> dict[str, Any]:
    """
    Garante que as quatro PKs retornadas pela API correspondam às PKs
    solicitadas.

    A API normalmente retorna ano, semestre, disciplina e turma. Caso algum
    desses campos esteja ausente ou nulo, o valor solicitado é utilizado.

    Parameters
    ----------
    item:
        Registro retornado pelo endpoint.

    pk:
        PK solicitada:
        (ano, periodo, turma, disciplina).

    Returns
    -------
    dict
        Registro pronto para o model LY_TURMA.
    """
    ano, periodo, turma, disciplina = pk

    normalized = dict(item)

    if normalized.get("ano") is None:
        normalized["ano"] = ano

    if normalized.get("semestre") is None:
        normalized["semestre"] = periodo

    if normalized.get("turma") is None:
        normalized["turma"] = turma

    if normalized.get("disciplina") is None:
        normalized["disciplina"] = disciplina

    return normalized


# ============================================================================
# PERSISTÊNCIA
# ============================================================================

def persist_record(
    record: dict[str, Any],
) -> dict[str, int]:
    """
    Persiste um registro da API na LY_TURMA.

    Parameters
    ----------
    record:
        Registro retornado pelo endpoint.

    Returns
    -------
    dict
        Resultado produzido por LyTurmaModel.batch_insert().
    """
    return LyTurmaModel.batch_insert([record])


# ============================================================================
# SINCRONIZAÇÃO
# ============================================================================

def run(
    limit: int | None = None,
    delay: float = DEFAULT_DELAY,
    timeout: float = DEFAULT_TIMEOUT,
) -> bool:
    """
    Executa a sincronização da LY_TURMA por PK.

    A cada execução os contadores começam do zero. O conjunto de chamadas
    HTTP é obtido novamente de LY_TURMA_DOCENTE.

    Parameters
    ----------
    limit:
        Limita a quantidade de PKs processadas.
        None significa todas.

    delay:
        Intervalo entre chamadas HTTP.

    timeout:
        Timeout individual de cada chamada HTTP.

    Returns
    -------
    bool
        True quando termina sem erro.
        False quando ocorre erro fatal.
    """
    start_time = time.time()

    total_pks = 0
    total_processadas = 0
    total_sucesso = 0
    total_404 = 0
    total_inseridos = 0
    total_duplicados = 0
    total_invalidos = 0
    total_erros = 0

    logger.info("=" * 100)
    logger.info("INICIANDO SINCRONIZAÇÃO - LY_TURMA POR PK")
    logger.info("Endpoint: GET /v2/tabela/turmas")
    logger.info("Paginação: NÃO")
    logger.info("Fonte das PKs: LY_TURMA_DOCENTE")
    logger.info("Mapeamento: periodo -> pk[semestre]")
    logger.info("Tabela destino será limpa? NÃO")
    logger.info("=" * 100)

    try:
        # --------------------------------------------------------------------
        # PREPARA TABELA
        # --------------------------------------------------------------------
        if not LyTurmaModel.create_table():
            logger.error(
                "Falha ao preparar LY_TURMA."
            )
            return False

        # --------------------------------------------------------------------
        # PKS
        # --------------------------------------------------------------------
        pks = get_turma_pks()

        if limit is not None:
            pks = pks[:limit]

        total_pks = len(pks)

        logger.info(
            "PKs encontradas em LY_TURMA_DOCENTE: %d",
            total_pks,
        )

        if not pks:
            logger.warning(
                "Nenhuma PK encontrada em LY_TURMA_DOCENTE."
            )
            return True

        # --------------------------------------------------------------------
        # SESSÃO HTTP
        # --------------------------------------------------------------------
        session = create_api_session()

        with session:
            for index, pk in enumerate(pks, start=1):
                ano, periodo, turma, disciplina = pk

                total_processadas += 1

                logger.info(
                    "[%d/%d] GET turma | "
                    "ano=%s | periodo=%s -> semestre=%s | "
                    "turma=%s | disciplina=%s",
                    index,
                    total_pks,
                    ano,
                    periodo,
                    periodo,
                    turma,
                    disciplina,
                )

                try:
                    item = get_turma_by_pk(
                        session,
                        pk,
                        timeout=timeout,
                    )

                    # --------------------------------------------------------
                    # 404
                    # --------------------------------------------------------
                    if item is None:
                        total_404 += 1

                        logger.warning(
                            "[%d/%d] 404 | "
                            "ano=%s | semestre=%s | turma=%s | disciplina=%s",
                            index,
                            total_pks,
                            ano,
                            periodo,
                            turma,
                            disciplina,
                        )

                        continue

                    # --------------------------------------------------------
                    # NORMALIZA
                    # --------------------------------------------------------
                    record = normalize_api_record(
                        item,
                        pk,
                    )

                    total_sucesso += 1

                    # --------------------------------------------------------
                    # PERSISTE
                    # --------------------------------------------------------
                    result = persist_record(record)

                    inseridos = int(
                        result.get("inseridos", 0)
                    )
                    duplicados = int(
                        result.get("duplicados", 0)
                    )
                    invalidos = int(
                        result.get("invalidos", 0)
                    )

                    total_inseridos += inseridos
                    total_duplicados += duplicados
                    total_invalidos += invalidos

                    logger.info(
                        "[%d/%d] OK | "
                        "INSERT=%d | DUPLICADOS=%d | INVÁLIDOS=%d",
                        index,
                        total_pks,
                        inseridos,
                        duplicados,
                        invalidos,
                    )

                except requests.HTTPError as exc:
                    total_erros += 1

                    status = (
                        exc.response.status_code
                        if exc.response is not None
                        else "?"
                    )

                    logger.error(
                        "[%d/%d] HTTP %s | "
                        "ano=%s | semestre=%s | turma=%s | disciplina=%s | %s",
                        index,
                        total_pks,
                        status,
                        ano,
                        periodo,
                        turma,
                        disciplina,
                        exc,
                    )

                except (requests.RequestException, ValueError) as exc:
                    total_erros += 1

                    logger.error(
                        "[%d/%d] ERRO API | "
                        "ano=%s | semestre=%s | turma=%s | disciplina=%s | %s",
                        index,
                        total_pks,
                        ano,
                        periodo,
                        turma,
                        disciplina,
                        exc,
                    )

                except Exception:
                    total_erros += 1

                    logger.exception(
                        "[%d/%d] ERRO AO PROCESSAR PK | "
                        "ano=%s | periodo=%s | turma=%s | disciplina=%s",
                        index,
                        total_pks,
                        ano,
                        periodo,
                        turma,
                        disciplina,
                    )

                if delay > 0 and index < total_pks:
                    time.sleep(delay)

        elapsed = time.time() - start_time

        # --------------------------------------------------------------------
        # RESUMO
        # --------------------------------------------------------------------
        try:
            summary = LyTurmaModel.get_summary()
        except (AttributeError, TypeError, KeyError):
            summary = {}

        logger.info("=" * 100)
        logger.info("RESUMO - LY_TURMA POR PK")
        logger.info("=" * 100)
        logger.info(
            "PKs encontradas: %d",
            total_pks,
        )
        logger.info(
            "PKs processadas: %d",
            total_processadas,
        )
        logger.info(
            "Respostas 200: %d",
            total_sucesso,
        )
        logger.info(
            "Respostas 404: %d",
            total_404,
        )
        logger.info(
            "Erros: %d",
            total_erros,
        )
        logger.info(
            "INSERTs reais: %d",
            total_inseridos,
        )
        logger.info(
            "Duplicados: %d",
            total_duplicados,
        )
        logger.info(
            "Inválidos: %d",
            total_invalidos,
        )
        logger.info(
            "Total LY_TURMA: %d",
            summary.get("total_turmas", 0),
        )
        logger.info(
            "Tempo total: %.2f s",
            elapsed,
        )
        logger.info("=" * 100)

        # Erros individuais não interrompem as demais PKs.
        # A execução só é considerada fatal quando houve erro estrutural
        # antes ou fora do processamento normal das PKs.
        return total_erros == 0

    except Exception:
        logger.exception(
            "Erro fatal durante sincronização LY_TURMA por PK."
        )
        return False


# ============================================================================
# MAIN
# ============================================================================

def main() -> int:
    """
    Ponto de entrada da sincronização.

    Returns
    -------
    int
        0 para sucesso.
        1 para erro.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Sincroniza LY_TURMA usando as PKs distintas de "
            "LY_TURMA_DOCENTE e o novo endpoint GET por PK."
        )
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help=(
            "Quantidade máxima de PKs processadas. "
            "Sem informar, processa todas."
        ),
    )

    parser.add_argument(
        "--delay",
        type=float,
        default=DEFAULT_DELAY,
        help=(
            "Intervalo em segundos entre chamadas à API."
        ),
    )

    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT,
        help=(
            "Timeout de cada chamada à API em segundos."
        ),
    )

    args = parser.parse_args()

    if args.limit is not None and args.limit <= 0:
        logger.error(
            "--limit deve ser maior que zero."
        )
        return 1

    if args.delay < 0:
        logger.error(
            "--delay não pode ser negativo."
        )
        return 1

    if args.timeout <= 0:
        logger.error(
            "--timeout deve ser maior que zero."
        )
        return 1

    return (
        0
        if run(
            limit=args.limit,
            delay=args.delay,
            timeout=args.timeout,
        )
        else 1
    )


if __name__ == "__main__":
    sys.exit(main())
