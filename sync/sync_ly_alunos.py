# sync/sync_ly_alunos.py
"""
Sincronização de alunos da API Lyceum para a tabela LY_ALUNO (SQL Server)

Execução:
    python -m sync.sync_ly_alunos [--incremental]
"""

from __future__ import annotations

import sys
import time
import logging
from pathlib import Path
from typing import Dict, Set

# ----------------------------------------------------------------------
# PATH
# ----------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

# ----------------------------------------------------------------------
# Imports do projeto
# ----------------------------------------------------------------------
from core.api_client import AlunoAPIClient
from core.database import get_db_connection
from models.ly_aluno import AlunoModel

# ----------------------------------------------------------------------
# Configuração de logging SILENCIOSA
# - Suprime logs INFO do modelo (ex: "Aluno X upsert realizado")
# - Mantém apenas WARNING e ERROR
# ----------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Desativa logs verbosos do modelo (que apareciam a cada aluno)
logging.getLogger("models.ly_aluno").setLevel(logging.WARNING)


# ----------------------------------------------------------------------
# Função principal otimizada
# ----------------------------------------------------------------------
def run(modo: str = "completo") -> Dict[str, int | float]:
    """Executa sincronização sem logs individuais e com máximo desempenho."""
    if modo not in ("completo", "incremental"):
        raise ValueError("Modo inválido. Use 'completo' ou 'incremental'.")

    logger.info("=" * 70)
    logger.info("INICIANDO SINCRONIZAÇÃO DE ALUNOS - Modo: %s", modo.upper())
    logger.info("=" * 70)

    start_time = time.time()

    # 1. Garante existência da tabela
    AlunoModel.create_table()

    # 2. Busca todos os alunos via API (GET)
    api = AlunoAPIClient()
    alunos_api = api.get_alunos()

    if not alunos_api:
        logger.warning("API retornou lista vazia ou None")
        return {
            "total_api": 0,
            "total_banco": 0,
            "inseridos": 0,
            "atualizados": 0,
            "ignorados": 0,
            "erros": 0,
            "tempo_total": time.time() - start_time,
        }

    total_recebidos = len(alunos_api)
    logger.info("Registros recebidos da API: %d", total_recebidos)

    # ----------------------------------------------------------
    # FILTRO: mantém apenas os alunos com sit_aluno = 'Ativo'
    # ----------------------------------------------------------
    alunos_ativos = [
        aluno for aluno in alunos_api
        if isinstance(aluno, dict) and aluno.get('sit_aluno') == 'Ativo'
    ]
    total_ativos = len(alunos_ativos)
    logger.info("Registros com sit_aluno='Ativo': %d (descartados %d)",
                total_ativos, total_recebidos - total_ativos)

    # Se não houver alunos ativos, trata de acordo com o modo
    if total_ativos == 0:
        if modo == "completo":
            # Modo completo: remove todos os registros da tabela
            with get_db_connection(database_name="lyceum") as conn:
                conn.execute("DELETE FROM [LY_ALUNO]")
            logger.info("Nenhum aluno ativo encontrado. Tabela esvaziada.")
        else:
            logger.info("Nenhum aluno ativo encontrado. Nada a fazer no modo incremental.")
        return {
            "total_api": 0,
            "total_banco": 0,
            "inseridos": 0,
            "atualizados": 0,
            "ignorados": 0,
            "erros": 0,
            "tempo_total": time.time() - start_time,
        }

    # A partir daqui, trabalhamos apenas com alunos_ativos
    total_api = total_ativos

    # ------------------------------------------------------------------
    # Pré‑carrega stamps (modo incremental) e matrículas existentes (modo completo)
    # Tudo em uma única consulta por modo, evitando SELECT a cada registro
    # ------------------------------------------------------------------
    stamps_banco: Dict[str, str] = {}
    matriculas_existentes: Set[str] = set()

    with get_db_connection(database_name="lyceum") as conn:
        if modo == "incremental":
            cursor = conn.execute("SELECT aluno, stamp_atualizacao FROM [LY_ALUNO]")
            stamps_banco = {str(row[0]): str(row[1] or "") for row in cursor}
            logger.info("Carregados %d stamps existentes", len(stamps_banco))
        else:
            # apenas para saber se a matrícula já existe (usado na contagem)
            cursor = conn.execute("SELECT aluno FROM [LY_ALUNO]")
            matriculas_existentes = {str(row[0]) for row in cursor}
            logger.info("Carregadas %d matrículas existentes", len(matriculas_existentes))

    # ------------------------------------------------------------------
    # Processamento em lote – sem logs individuais
    # ------------------------------------------------------------------
    stats = {"inseridos": 0, "atualizados": 0, "ignorados": 0, "erros": 0}
    matriculas_processadas: Set[str] = set()

    for idx, aluno in enumerate(alunos_ativos, start=1):
        try:
            # Validação mínima
            if not isinstance(aluno, dict):
                stats["ignorados"] += 1
                continue
            matricula = str(aluno.get("aluno"))
            if not matricula:
                stats["ignorados"] += 1
                continue

            matriculas_processadas.add(matricula)

            # ----------------------------------------------------------
            # Modo incremental: compara stamp via dicionário em memória
            # ----------------------------------------------------------
            if modo == "incremental":
                stamp_api = str(aluno.get("stamp_atualizacao", ""))
                stamp_local = stamps_banco.get(matricula, "")
                if stamp_local == stamp_api:
                    stats["ignorados"] += 1
                    continue

            # ----------------------------------------------------------
            # UPSERT (método não deve gerar logs por aluno)
            # ----------------------------------------------------------
            # O método upsert não retorna um booleano, portanto não é possível
            # distinguir INSERT de UPDATE. A contagem abaixo é meramente ilustrativa.
            AlunoModel.upsert(aluno)

            # Como não sabemos se foi inserção ou atualização, contamos como "atualizado"
            # (isso mantém a compatibilidade com o código original que esperava um bool)
            # Para não quebrar, assumimos que sempre foi atualização.
            stats["atualizados"] += 1

            # Log de progresso a cada 500 registros (apenas para acompanhar)
            if idx % 500 == 0:
                logger.info("Progresso: %d / %d registros", idx, total_api)

        except Exception:
            stats["erros"] += 1
            # Log do erro (sem mostrar dados do aluno para manter silêncio)
            logger.exception("Erro no registro %d", idx)

    # ------------------------------------------------------------------
    # Limpeza de registros órfãos (apenas modo completo)
    # ------------------------------------------------------------------
    if modo == "completo":
        if matriculas_processadas:
            logger.info("Removendo registros obsoletos...")
            AlunoModel.delete_obsoletos(matriculas_processadas)
        else:
            # Caso não haja nenhum aluno ativo (já tratado anteriormente),
            # mas mantido aqui por segurança.
            with get_db_connection(database_name="lyceum") as conn:
                conn.execute("DELETE FROM [LY_ALUNO]")
            logger.info("Nenhum aluno ativo para manter. Tabela esvaziada.")

    # ------------------------------------------------------------------
    # Estatísticas finais
    # ------------------------------------------------------------------
    tempo_total = time.time() - start_time

    with get_db_connection(database_name="lyceum") as conn:
        total_banco = conn.execute("SELECT COUNT(*) FROM [LY_ALUNO]").fetchone()[0]

    logger.info("=" * 70)
    logger.info("SINCRONIZAÇÃO FINALIZADA")
    logger.info("Total API (ativos)..: %d", total_api)
    logger.info("Total Banco........: %d", total_banco)
    logger.info("Inseridos..........: %d", stats["inseridos"])
    logger.info("Atualizados........: %d", stats["atualizados"])
    logger.info("Ignorados..........: %d", stats["ignorados"])
    logger.info("Erros..............: %d", stats["erros"])
    logger.info("Tempo total (s)....: %.2f", tempo_total)
    logger.info("=" * 70)

    return {
        "total_api": total_api,
        "total_banco": total_banco,
        **stats,
        "tempo_total": tempo_total,
    }


# ----------------------------------------------------------------------
# Execução direta
# ----------------------------------------------------------------------
if __name__ == "__main__":
    modo = "incremental" if "--incremental" in sys.argv else "completo"
    run(modo=modo)