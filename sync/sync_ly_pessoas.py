#!/usr/bin/env python3
"""
sync/sync_ly_pessoas.py
SINCRONIZAÇÃO LY_PESSOA
- Execução direta
- Somente GET na API Lyceum
- Upsert por chave primária (pessoa)
"""

import sys
import os
import time
import logging

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.config import config
from core.api_client import PessoaAPIClient  # Supondo que exista um cliente para pessoas
from models.ly_pessoa import LyPessoaModel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def sincronizar_pessoas():
    logger.info("=" * 70)
    logger.info("INICIANDO SINCRONIZAÇÃO DE PESSOAS")
    logger.info("Modo: UPSERT (CHAVE = pessoa)")
    logger.info("=" * 70)

    inicio = time.time()

    # Criar/verificar tabela
    LyPessoaModel.create_table()

    resumo_inicial = LyPessoaModel.get_summary()
    total_inicial = resumo_inicial.get('total_pessoas', 0)
    logger.info(f"Total inicial no banco: {total_inicial}")

    # Buscar dados da API
    logger.info("Buscando pessoas na API Lyceum...")
    client = PessoaAPIClient()
    pessoas = client.get_pessoas()  # método que deve implementar paginação e retornar lista

    if not pessoas:
        logger.warning("API retornou zero registros")
        return {"success": True, "total_api": 0, "processados": 0, "tempo_total": 0}

    logger.info(f"Total retornado pela API: {len(pessoas)}")

    # Filtrar registros válidos (apenas dicionários)
    validos = [p for p in pessoas if isinstance(p, dict) and p.get('pessoa') is not None]
    invalidos = len(pessoas) - len(validos)
    if invalidos:
        logger.warning(f"Registros inválidos ignorados: {invalidos}")

    if not validos:
        logger.warning("Nenhum registro válido para processamento")
        return {"success": True, "total_api": len(pessoas), "processados": 0, "tempo_total": 0}

    # Upsert em lote
    logger.info("Gravando pessoas no banco (UPSERT)...")
    processados = LyPessoaModel.batch_upsert(validos)

    tempo_total = time.time() - inicio
    resumo_final = LyPessoaModel.get_summary()
    total_final = resumo_final.get('total_pessoas', 0)

    logger.info("=" * 70)
    logger.info("RESUMO DA SINCRONIZAÇÃO")
    logger.info(f"API retornou: {len(pessoas)}")
    logger.info(f"Válidos: {len(validos)}")
    logger.info(f"Processados: {processados}")
    logger.info(f"Banco antes: {total_inicial}")
    logger.info(f"Banco depois: {total_final}")
    if resumo_final.get('ultima_atualizacao'):
        logger.info(f"Última atualização: {resumo_final['ultima_atualizacao']}")
    logger.info(f"Tempo total: {tempo_total:.2f}s")
    logger.info("=" * 70)

    return {
        "success": True,
        "total_api": len(pessoas),
        "validos": len(validos),
        "processados": processados,
        "tempo_total": tempo_total,
    }


def run():
    return sincronizar_pessoas()


if __name__ == "__main__":
    resultado = run()
    sys.exit(0 if resultado else 1)