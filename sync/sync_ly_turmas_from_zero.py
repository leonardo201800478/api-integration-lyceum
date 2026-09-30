#!/usr/bin/env python3
"""
sync/sync_ly_turmas_from_zero.py

Sincronização da LY_TURMA iniciando SEMPRE pela página 0 da API.

Características
---------------
- Não utiliza o checkpoint existente.
- Não altera nem reseta a tabela de checkpoint.
- Não limpa a LY_TURMA.
- Busca os dados diretamente do endpoint da API Lyceum.
- A paginação começa sempre em 0 a cada execução.
- Os contadores estatísticos começam sempre em zero.
- Registros já existentes são tratados pelo batch_insert() do model.
- O processo termina quando o endpoint retornar uma página vazia.
- O filtro de ano permanece em 2026, conforme o sync atual.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import time

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

from core.api_client import TurmaAPIClient
from core.config import config
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

logger = logging.getLogger("sync.ly_turmas_from_zero")

# ============================================================================
# CONFIGURAÇÕES
# ============================================================================

ANO = 2026
PAGE_SIZE = config.API_PAGE_SIZE
DEFAULT_DELAY = config.API_DELAY_BETWEEN_REQUESTS


# ============================================================================
# API
# ============================================================================

def get_turmas_page(
    client: TurmaAPIClient,
    page: int,
) -> list:
    """
    Busca uma página de turmas diretamente no endpoint da API Lyceum.

    Parameters
    ----------
    client:
        Instância do cliente da API Lyceum.

    page:
        Número da página que será requisitada.

    Returns
    -------
    list
        Registros retornados pelo endpoint.
    """
    return client.get_turmas_from_page(
        page,
        PAGE_SIZE,
        ano=ANO,
    )


# ============================================================================
# SINCRONIZAÇÃO
# ============================================================================

def run(
    max_pages: int | None = None,
    delay: float = DEFAULT_DELAY,
) -> bool:
    """
    Executa a sincronização começando sempre pela página 0.

    O checkpoint existente é deliberadamente ignorado. Dessa forma, uma
    nova execução sempre consulta novamente o endpoint desde o início.

    Parameters
    ----------
    max_pages:
        Limita a quantidade de páginas processadas nesta execução.
        None significa processar até o endpoint retornar uma página vazia.

    delay:
        Intervalo, em segundos, entre requisições consecutivas.

    Returns
    -------
    bool
        True quando a execução termina normalmente.
        False quando ocorre erro durante a sincronização.
    """
    start_time = time.time()

    # ------------------------------------------------------------------------
    # CONTADORES
    # ------------------------------------------------------------------------
    # Todos começam em zero em cada execução.
    total_api = 0
    total_2026 = 0
    total_inseridos = 0
    total_duplicados = 0
    total_invalidos = 0

    pages_processed = 0
    pages_with_2026 = 0
    pages_without_2026 = 0
    pages_only_duplicates = 0

    # ------------------------------------------------------------------------
    # PAGINAÇÃO
    # ------------------------------------------------------------------------
    # IMPORTANTE:
    # Diferentemente do sync incremental, aqui a página inicial é FIXA.
    # Não consultamos o checkpoint.
    page = 0

    logger.info("=" * 90)
    logger.info("INICIANDO SINCRONIZAÇÃO DA LY_TURMA")
    logger.info("Modo: REPROCESSAMENTO DESDE A PÁGINA 0")
    logger.info("Endpoint: API Lyceum")
    logger.info("Filtro: ano = %d", ANO)
    logger.info("Página inicial: %d", page)
    logger.info("Checkpoint: IGNORADO")
    logger.info("LY_TURMA será limpa? NÃO")
    logger.info("=" * 90)

    try:
        # --------------------------------------------------------------------
        # TABELA
        # --------------------------------------------------------------------
        if not LyTurmaModel.create_table():
            logger.error("Falha ao preparar LY_TURMA.")
            return False

        # --------------------------------------------------------------------
        # CLIENTE DA API
        # --------------------------------------------------------------------
        client = TurmaAPIClient()

        while True:
            # ----------------------------------------------------------------
            # LIMITE OPCIONAL
            # ----------------------------------------------------------------
            if max_pages is not None and pages_processed >= max_pages:
                logger.info(
                    "Limite de %d páginas atingido.",
                    max_pages,
                )
                break

            # ----------------------------------------------------------------
            # LEITURA DO ENDPOINT
            # ----------------------------------------------------------------
            logger.info(
                "Consultando endpoint | página=%d | page_size=%d",
                page,
                PAGE_SIZE,
            )

            items = get_turmas_page(
                client,
                page,
            )

            # ----------------------------------------------------------------
            # FIM DA API
            # ----------------------------------------------------------------
            if not items:
                logger.info(
                    "Endpoint retornou página %d vazia. "
                    "Sincronização finalizada.",
                    page,
                )
                break

            total_api += len(items)

            # ----------------------------------------------------------------
            # FILTRO DO ANO
            # ----------------------------------------------------------------
            valid_items = []

            for item in items:
                ano = item.get("ano")

                try:
                    item_ano = int(ano) if ano is not None else None
                except (TypeError, ValueError):
                    item_ano = None

                if item_ano == ANO:
                    valid_items.append(item)
                else:
                    total_invalidos += 1

            total_2026 += len(valid_items)

            # ----------------------------------------------------------------
            # ESTATÍSTICAS DA PÁGINA
            # ----------------------------------------------------------------
            if valid_items:
                pages_with_2026 += 1
            else:
                pages_without_2026 += 1

            logger.info(
                "Página %d | API=%d | ano=%d=%d",
                page,
                len(items),
                ANO,
                len(valid_items),
            )

            # ----------------------------------------------------------------
            # PERSISTÊNCIA
            # ----------------------------------------------------------------
            result = LyTurmaModel.batch_insert(
                valid_items
            )

            inseridos = result.get("inseridos", 0)
            duplicados = result.get("duplicados", 0)
            invalidos_batch = result.get("invalidos", 0)

            total_inseridos += inseridos
            total_duplicados += duplicados
            total_invalidos += invalidos_batch

            if (
                valid_items
                and inseridos == 0
                and duplicados == len(valid_items)
            ):
                pages_only_duplicates += 1

            logger.info(
                "Página %d processada | "
                "INSERT=%d | DUPLICADOS=%d | INVÁLIDOS=%d",
                page,
                inseridos,
                duplicados,
                invalidos_batch,
            )

            pages_processed += 1

            # ----------------------------------------------------------------
            # PRÓXIMA PÁGINA
            # ----------------------------------------------------------------
            page += 1

            if delay > 0:
                time.sleep(delay)

        # ====================================================================
        # RESUMO
        # ====================================================================

        elapsed = time.time() - start_time

        try:
            summary = LyTurmaModel.get_summary()
        except (AttributeError, TypeError, KeyError):
            summary = {}

        logger.info("=" * 90)
        logger.info("SINCRONIZAÇÃO FINALIZADA")
        logger.info("=" * 90)

        logger.info("Páginas processadas: %d", pages_processed)
        logger.info(
            "Páginas com registros de %d: %d",
            ANO,
            pages_with_2026,
        )
        logger.info(
            "Páginas sem registros de %d: %d",
            ANO,
            pages_without_2026,
        )
        logger.info(
            "Páginas somente com duplicados: %d",
            pages_only_duplicates,
        )
        logger.info("Registros retornados pela API: %d", total_api)
        logger.info(
            "Registros de %d: %d",
            ANO,
            total_2026,
        )
        logger.info("INSERTs reais: %d", total_inseridos)
        logger.info("Duplicados ignorados: %d", total_duplicados)
        logger.info("Registros inválidos: %d", total_invalidos)

        logger.info(
            "Total LY_TURMA: %d",
            summary.get("total_turmas", 0),
        )

        logger.info(
            "Próxima execução começará novamente na página: 0"
        )
        logger.info(
            "Checkpoint utilizado: NÃO"
        )
        logger.info(
            "Tempo total: %.2f s",
            elapsed,
        )
        logger.info("=" * 90)

        return True

    except Exception:
        logger.exception(
            "Erro durante sincronização da LY_TURMA."
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
            "Sincroniza LY_TURMA consultando a API desde a página 0."
        )
    )

    parser.add_argument(
        "--pages",
        type=int,
        default=None,
        help=(
            "Quantidade máxima de páginas desta execução. "
            "Sem informar, processa até o endpoint retornar vazio."
        ),
    )

    parser.add_argument(
        "--delay",
        type=float,
        default=DEFAULT_DELAY,
        help=(
            "Intervalo em segundos entre requisições. "
            "Padrão: valor definido em config."
        ),
    )

    args = parser.parse_args()

    # ------------------------------------------------------------------------
    # VALIDAÇÕES
    # ------------------------------------------------------------------------

    if args.pages is not None and args.pages <= 0:
        logger.error("--pages deve ser maior que zero.")
        return 1

    if args.delay < 0:
        logger.error("--delay não pode ser negativo.")
        return 1

    if not all(
        [
            config.LYCEUM_BASE_URL,
            config.LYCEUM_USERNAME,
            config.LYCEUM_PASSWORD,
        ]
    ):
        logger.error(
            "Configuração da API Lyceum incompleta."
        )
        return 1

    # ------------------------------------------------------------------------
    # EXECUÇÃO
    # ------------------------------------------------------------------------

    return (
        0
        if run(
            max_pages=args.pages,
            delay=args.delay,
        )
        else 1
    )


if __name__ == "__main__":
    sys.exit(main())
