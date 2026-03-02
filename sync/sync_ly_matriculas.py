#!/usr/bin/env python3
"""
sync/sync_ly_matriculas.py
SINCRONIZAÇÃO LY_MATRICULA
- Sem menu
- Sem filtros
- Paginação delegada ao APIClient
- Apenas método GET na API
"""

import sys
import os
import time
import logging
from datetime import datetime

# Garantir import do projeto
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.config import config
from core.api_client import APIClientFactory
from models.ly_matricula import LyMatriculaModel

# ---------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------
# Função principal de sincronização
# ---------------------------------------------------------------------
def sincronizar_matriculas():
    """
    Sincroniza TODAS as matrículas:
    - Busca completa via API (GET)
    - Limpa tabela local
    - Insere novamente
    """
    logger.info("=" * 70)
    logger.info("INICIANDO SINCRONIZAÇÃO DE MATRÍCULAS")
    logger.info("Modo: COMPLETO (SEM FILTROS)")
    logger.info("=" * 70)

    inicio = time.time()

    # 1. Criar/verificar tabela
    LyMatriculaModel.create_table()

    resumo_inicial = LyMatriculaModel.get_summary()
    total_inicial = resumo_inicial.get("total_matriculas", 0)
    logger.info(f"Total inicial no banco: {total_inicial}")

    # 2. Buscar dados da API (GET)
    logger.info("Buscando matrículas na API Lyceum...")
    client = APIClientFactory.create_matricula_client()
    matriculas = client.get_matriculas()  # ✅ paginação interna

    if not matriculas:
        logger.warning("API retornou zero matrículas")
        return {
            "success": True,
            "total_api": 0,
            "inseridas": 0,
            "tempo_total": 0
        }

    logger.info(f"Total retornado pela API: {len(matriculas)}")

    # 3. Limpar tabela local (usando o modelo)
    logger.info("Limpando tabela LY_MATRICULA...")
    LyMatriculaModel.clear_table()

    # 4. Inserir no banco
    logger.info("Inserindo matrículas no banco local...")
    inseridas = LyMatriculaModel.batch_insert(matriculas)

    # 5. Resumo final
    tempo_total = time.time() - inicio
    resumo_final = LyMatriculaModel.get_summary()
    total_final = resumo_final.get("total_matriculas", 0)

    logger.info("=" * 70)
    logger.info("RESUMO DA SINCRONIZAÇÃO")
    logger.info(f"API retornou: {len(matriculas)}")
    logger.info(f"Inseridas: {inseridas}")
    logger.info(f"Banco antes: {total_inicial}")
    logger.info(f"Banco depois: {total_final}")
    logger.info(f"Tempo total: {tempo_total:.2f}s")
    logger.info("=" * 70)

    return {
        "success": True,
        "total_api": len(matriculas),
        "inseridas": inseridas,
        "tempo_total": tempo_total
    }


# ---------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------
def run():
    return sincronizar_matriculas()


if __name__ == "__main__":
    sucesso = run()
    sys.exit(0 if sucesso else 1)