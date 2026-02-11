"""
Sincronização de alunos da API Lyceum para a tabela LY_ALUNO

Execução recomendada:
    python -m sync.sync_ly_alunos
"""

from __future__ import annotations

import sys
import time
import logging
from pathlib import Path
from typing import Dict, Set

# ============================================================================
# Ajuste de PATH para permitir execução direta
# ============================================================================
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

# ============================================================================
# Imports do projeto
# ============================================================================
from core.api_client import AlunoAPIClient
from core.database import get_db_connection
from models.ly_aluno import AlunoModel

# ============================================================================
# Logging
# ============================================================================
logger = logging.getLogger(__name__)

# ============================================================================
# Função principal
# ============================================================================
def run(modo: str = "completo") -> Dict[str, int | float]:
    """
    Executa a sincronização de alunos.

    Args:
        modo: 'completo' ou 'incremental'

    Returns:
        dict com estatísticas da execução
    """
    if modo not in ("completo", "incremental"):
        raise ValueError("Modo inválido. Use 'completo' ou 'incremental'.")

    logger.info("=" * 70)
    logger.info("INICIANDO SINCRONIZAÇÃO DE ALUNOS")
    logger.info("Modo: %s", modo.upper())
    logger.info("=" * 70)

    start_time = time.time()

    # ----------------------------------------------------------------------
    # Garante tabela
    # ----------------------------------------------------------------------
    AlunoModel.create_table()

    # ----------------------------------------------------------------------
    # Busca dados da API (GET)
    # ----------------------------------------------------------------------
    api = AlunoAPIClient()
    alunos_api = api.get_alunos()

    if not alunos_api:
        logger.warning("API retornou lista vazia ou None")
        return {}

    logger.info("Registros recebidos da API: %s", len(alunos_api))

    # ----------------------------------------------------------------------
    # Controle
    # ----------------------------------------------------------------------
    matriculas_processadas: Set[str] = set()
    stats = {
        "inseridos": 0,
        "atualizados": 0,
        "ignorados": 0,
        "erros": 0,
    }

    # ----------------------------------------------------------------------
    # Processamento
    # ----------------------------------------------------------------------
    for idx, aluno in enumerate(alunos_api, start=1):
        try:
            if not isinstance(aluno, dict):
                stats["ignorados"] += 1
                continue

            matricula = aluno.get("aluno")
            if not matricula:
                stats["ignorados"] += 1
                continue

            matricula = str(matricula)
            matriculas_processadas.add(matricula)

            # --------------------------------------------------------------
            # Modo incremental
            # --------------------------------------------------------------
            if modo == "incremental":
                with get_db_connection() as conn:
                    row = conn.execute(
                        "SELECT stamp_atualizacao FROM LY_ALUNO WHERE aluno = ?",
                        (matricula,),
                    ).fetchone()

                if row:
                    stamp_local = str(row[0])
                    stamp_api = str(aluno.get("stamp_atualizacao", ""))

                    if stamp_local == stamp_api:
                        stats["ignorados"] += 1
                        continue

            # --------------------------------------------------------------
            # Verifica existência
            # --------------------------------------------------------------
            with get_db_connection() as conn:
                existe = conn.execute(
                    "SELECT 1 FROM LY_ALUNO WHERE aluno = ?",
                    (matricula,),
                ).fetchone()

            # --------------------------------------------------------------
            # UPSERT
            # --------------------------------------------------------------
            AlunoModel.upsert(aluno)

            if existe:
                stats["atualizados"] += 1
            else:
                stats["inseridos"] += 1

            if idx % 500 == 0:
                logger.info("Processados %s / %s", idx, len(alunos_api))

        except Exception as exc:
            stats["erros"] += 1
            logger.exception("Erro processando aluno %s", aluno.get("aluno"))

    # ----------------------------------------------------------------------
    # Limpeza de obsoletos
    # ----------------------------------------------------------------------
    if modo == "completo":
        logger.info("Removendo registros obsoletos...")
        AlunoModel.delete_obsoletos(matriculas_processadas)

    # ----------------------------------------------------------------------
    # Estatísticas finais
    # ----------------------------------------------------------------------
    tempo_total = time.time() - start_time

    with get_db_connection() as conn:
        total_banco = conn.execute(
            "SELECT COUNT(*) FROM LY_ALUNO"
        ).fetchone()[0]

    logger.info("=" * 70)
    logger.info("SINCRONIZAÇÃO FINALIZADA")
    logger.info("Total API........: %s", len(alunos_api))
    logger.info("Total Banco......: %s", total_banco)
    logger.info("Inseridos........: %s", stats["inseridos"])
    logger.info("Atualizados......: %s", stats["atualizados"])
    logger.info("Ignorados........: %s", stats["ignorados"])
    logger.info("Erros............: %s", stats["erros"])
    logger.info("Tempo total (s)..: %.2f", tempo_total)
    logger.info("=" * 70)

    return {
        "total_api": len(alunos_api),
        "total_banco": total_banco,
        **stats,
        "tempo_total": tempo_total,
    }


# ============================================================================
# Execução direta
# ============================================================================
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    modo_execucao = "incremental" if "--incremental" in sys.argv else "completo"
    run(modo=modo_execucao)
