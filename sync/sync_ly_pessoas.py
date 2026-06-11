#!/usr/bin/env python3
"""
sync/sync_ly_pessoas.py

SINCRONIZAÇÃO LY_PESSOA

Características:
- Busca dados da API Lyceum
- Valida registros recebidos
- UPSERT por chave primária (pessoa)
- Processamento em lotes de 1000 registros
- Logs detalhados de progresso
- Resumo final da execução
"""

import os
import sys
import time
import logging

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.api_client import PessoaAPIClient
from models.ly_pessoa import LyPessoaModel


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)

BATCH_SIZE = 1000


def sincronizar_pessoas():

    logger.info("=" * 80)
    logger.info("INICIANDO SINCRONIZAÇÃO LY_PESSOA")
    logger.info(f"Tamanho do lote: {BATCH_SIZE}")
    logger.info("=" * 80)

    inicio_execucao = time.time()

    try:

        # ------------------------------------------------------------------
        # Garantir existência da tabela
        # ------------------------------------------------------------------

        logger.info("Verificando estrutura da tabela...")

        LyPessoaModel.create_table()

        resumo_inicial = LyPessoaModel.get_summary()

        total_inicial = resumo_inicial.get(
            "total_pessoas",
            0
        )

        logger.info(
            f"Total atual na tabela: {total_inicial:,}"
        )

        # ------------------------------------------------------------------
        # Buscar API
        # ------------------------------------------------------------------

        logger.info(
            "Consultando API de pessoas do Lyceum..."
        )

        api_inicio = time.time()

        client = PessoaAPIClient()

        pessoas = client.get_pessoas()

        api_tempo = time.time() - api_inicio

        if not pessoas:

            logger.warning(
                "A API retornou zero registros."
            )

            return {
                "success": True,
                "total_api": 0,
                "validos": 0,
                "processados": 0,
                "tempo_total": 0
            }

        logger.info(
            f"API retornou {len(pessoas):,} registros "
            f"em {api_tempo:.2f}s"
        )

        # ------------------------------------------------------------------
        # Validar registros
        # ------------------------------------------------------------------

        logger.info(
            "Validando registros recebidos..."
        )

        validos = []
        invalidos = 0

        for pessoa in pessoas:

            if not isinstance(pessoa, dict):
                invalidos += 1
                continue

            if pessoa.get("pessoa") is None:
                invalidos += 1
                continue

            validos.append(pessoa)

        logger.info(
            f"Registros válidos: {len(validos):,}"
        )

        if invalidos:
            logger.warning(
                f"Registros inválidos ignorados: "
                f"{invalidos:,}"
            )

        if not validos:

            logger.warning(
                "Nenhum registro válido encontrado."
            )

            return {
                "success": True,
                "total_api": len(pessoas),
                "validos": 0,
                "processados": 0,
                "tempo_total": 0
            }

        # ------------------------------------------------------------------
        # UPSERT
        # ------------------------------------------------------------------

        logger.info(
            f"Iniciando UPSERT de "
            f"{len(validos):,} registros..."
        )

        inicio_upsert = time.time()

        processados = LyPessoaModel.batch_upsert(
            validos,
            batch_size=BATCH_SIZE
        )

        tempo_upsert = time.time() - inicio_upsert

        # ------------------------------------------------------------------
        # Resumo final
        # ------------------------------------------------------------------

        resumo_final = LyPessoaModel.get_summary()

        total_final = resumo_final.get(
            "total_pessoas",
            0
        )

        tempo_total = time.time() - inicio_execucao

        logger.info("=" * 80)
        logger.info("RESUMO DA SINCRONIZAÇÃO")
        logger.info("=" * 80)

        logger.info(
            f"Total recebido da API: "
            f"{len(pessoas):,}"
        )

        logger.info(
            f"Registros válidos: "
            f"{len(validos):,}"
        )

        logger.info(
            f"Registros processados: "
            f"{processados:,}"
        )

        logger.info(
            f"Total antes: "
            f"{total_inicial:,}"
        )

        logger.info(
            f"Total depois: "
            f"{total_final:,}"
        )

        logger.info(
            f"Tempo API: "
            f"{api_tempo:.2f}s"
        )

        logger.info(
            f"Tempo UPSERT: "
            f"{tempo_upsert:.2f}s"
        )

        logger.info(
            f"Tempo total: "
            f"{tempo_total:.2f}s"
        )

        ultima_atualizacao = resumo_final.get(
            "ultima_atualizacao"
        )

        if ultima_atualizacao:

            logger.info(
                f"Última atualização: "
                f"{ultima_atualizacao}"
            )

        logger.info("=" * 80)

        return {
            "success": True,
            "total_api": len(pessoas),
            "validos": len(validos),
            "processados": processados,
            "tempo_api": api_tempo,
            "tempo_upsert": tempo_upsert,
            "tempo_total": tempo_total
        }

    except Exception as e:

        logger.exception(
            f"Erro durante sincronização: {e}"
        )

        return {
            "success": False,
            "erro": str(e)
        }


def run():
    return sincronizar_pessoas()


if __name__ == "__main__":

    resultado = run()

    if resultado.get("success"):
        sys.exit(0)

    sys.exit(1)