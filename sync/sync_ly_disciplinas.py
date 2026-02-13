#!/usr/bin/env python3
"""
SINCRONIZAÇÃO LY_DISCIPLINA
- Execução direta
- Sem menu
- Somente GET na API Lyceum
- SEM chave primária fixa (permite duplicatas)
- Sincronização completa (clear + insert)
"""

import sys
import os
import time
import logging
from collections import Counter

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.config import config
from core.api_client import DisciplinaAPIClient
from models.ly_disciplina import LyDisciplinaModel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def sincronizar_disciplinas():
    logger.info("=" * 70)
    logger.info("INICIANDO SINCRONIZAÇÃO DE DISCIPLINAS")
    logger.info("Modo: COMPLETO (SEM CHAVE PRIMÁRIA)")
    logger.info("=" * 70)

    inicio = time.time()

    LyDisciplinaModel.create_table()
    resumo_inicial = LyDisciplinaModel.get_summary()
    total_inicial = resumo_inicial.get("total_disciplinas", 0)
    logger.info(f"Total inicial no banco: {total_inicial}")

    logger.info("Buscando disciplinas na API Lyceum...")
    client = DisciplinaAPIClient()
    disciplinas = client.get_disciplinas()

    if not disciplinas:
        logger.warning("API retornou zero registros")
        return {"success": True, "total_api": 0, "processados": 0, "tempo_total": 0}

    logger.info(f"Total retornado pela API: {len(disciplinas)}")

    disciplinas_validas = []
    disciplinas_invalidas = 0
    for registro in disciplinas:
        if not isinstance(registro, dict):
            disciplinas_invalidas += 1
            continue
        if not registro.get("disciplina"):
            disciplinas_invalidas += 1
            continue
        # Não precisa limpar, o modelo normaliza
        disciplinas_validas.append(registro)

    logger.info(f"Disciplinas válidas: {len(disciplinas_validas)}")
    if disciplinas_invalidas:
        logger.warning(f"Disciplinas inválidas ignoradas: {disciplinas_invalidas}")

    if not disciplinas_validas:
        return {"success": True, "total_api": len(disciplinas), "processados": 0, "tempo_total": 0}

    ativas = sum(1 for d in disciplinas_validas if d.get("ativo") == "S")
    logger.info(f"Ativas: {ativas}, Inativas: {len(disciplinas_validas)-ativas}")

    codigos = [d.get("disciplina") for d in disciplinas_validas if d.get("disciplina")]
    logger.info(f"Códigos distintos: {len(set(codigos))}, duplicatas: {len(codigos)-len(set(codigos))}")

    logger.info("Limpando tabela LY_DISCIPLINA...")
    LyDisciplinaModel.clear_table()

    logger.info("Inserindo disciplinas no banco...")
    processadas = LyDisciplinaModel.batch_insert(disciplinas_validas)

    tempo_total = time.time() - inicio
    resumo_final = LyDisciplinaModel.get_summary()
    total_final = resumo_final.get("total_disciplinas", 0)

    logger.info("=" * 70)
    logger.info("RESUMO DA SINCRONIZAÇÃO")
    logger.info(f"API retornou: {len(disciplinas)}")
    logger.info(f"Válidas: {len(disciplinas_validas)}")
    logger.info(f"Processadas: {processadas}")
    logger.info(f"Banco antes: {total_inicial}")
    logger.info(f"Banco depois: {total_final}")
    logger.info(f"Disciplinas ativas: {resumo_final.get('disciplinas_ativas', 0)}")
    logger.info(f"Última atualização: {resumo_final.get('ultima_atualizacao', 'N/A')}")
    logger.info(f"Tempo total: {tempo_total:.2f}s")
    logger.info("=" * 70)

    return {
        "success": True,
        "total_api": len(disciplinas),
        "validos": len(disciplinas_validas),
        "processados": processadas,
        "tempo_total": tempo_total,
    }


def run():
    return sincronizar_disciplinas()


if __name__ == "__main__":
    resultado = run()
    sys.exit(0 if resultado else 1)