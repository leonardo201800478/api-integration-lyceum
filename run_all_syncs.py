#!/usr/bin/env python3
"""
RUNNER UNIFICADO DE SINCRONIZAÇÕES LYCEUM
- Execução controlada
- Sem subprocess
- Sem execução dupla
- Falha isolada por endpoint
"""

import sys
import os
import time
import json
import logging
import importlib
import traceback

from datetime import datetime
from pathlib import Path

# =============================================================================
# LOGGING
# =============================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("run_all")

# =============================================================================
# CONFIGURAÇÃO DOS SYNCs
# =============================================================================
SYNC_MODULES = [
    ("sync.sync_ly_cursos", "run"),
    ("sync.sync_ly_curriculos", "run"),
    ("sync.sync_ly_disciplinas", "run"),
    ("sync.sync_ly_alunos", "run"),
    ("sync.sync_ly_turmas", "run"),
    ("sync.sync_ly_docentes", "run"),
    ("sync.sync_ly_turma_docentes", "run"),
    ("sync.sync_ly_coordenacoes", "run"),
    ("sync.sync_ly_grades", "run"),
    ("sync.sync_ly_matriculas", "run"),
]

DELAY_SECONDS = 3

# =============================================================================
# AMBIENTE
# =============================================================================
def setup_environment() -> Path:
    root = Path(__file__).resolve().parent

    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    os.chdir(root)
    logger.info(f"Projeto: {root}")
    return root


# =============================================================================
# EXECUÇÃO DE UM SYNC
# =============================================================================
def execute_sync(module_path: str, func_name: str) -> dict:
    start = time.time()

    result = {
        "module": module_path,
        "function": func_name,
        "success": False,
        "error": None,
        "elapsed": 0.0,
    }

    try:
        module = importlib.import_module(module_path)

        if not hasattr(module, func_name):
            raise RuntimeError(f"Função '{func_name}' não encontrada")

        logger.info(f"▶ Executando {module_path}.{func_name}()")
        success = getattr(module, func_name)()

        result["success"] = success is not False

    except Exception as e:
        result["error"] = str(e)
        logger.error(f"Erro em {module_path}: {e}")
        traceback.print_exc()

    result["elapsed"] = time.time() - start
    return result


# =============================================================================
# MAIN
# =============================================================================
def main() -> bool:
    print("\n" + "=" * 70)
    print("🔄 EXECUTOR DE SINCRONIZAÇÕES LYCEUM (PADRONIZADO)")
    print("=" * 70)

    root = setup_environment()

    log_dir = root / "logs" / "execucoes" / datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir.mkdir(parents=True, exist_ok=True)

    results = []

    for idx, (module, func) in enumerate(SYNC_MODULES, 1):
        print(f"[{idx}/{len(SYNC_MODULES)}] {module}")
        res = execute_sync(module, func)
        results.append(res)

        with open(log_dir / f"{module.split('.')[-1]}.json", "w", encoding="utf-8") as f:
            json.dump(res, f, ensure_ascii=False, indent=2)

        if idx < len(SYNC_MODULES):
            time.sleep(DELAY_SECONDS)

    # -------------------------------------------------------------------------
    # RESUMO
    # -------------------------------------------------------------------------
    success = sum(r["success"] for r in results)
    fail = len(results) - success

    report = {
        "timestamp": datetime.now().isoformat(),
        "total": len(results),
        "success": success,
        "failure": fail,
        "results": results,
    }

    report_path = log_dir / "relatorio_final.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("\nRESULTADO FINAL")
    print(f"✅ Sucessos: {success}")
    print(f"❌ Falhas: {fail}")
    print(f"📁 Logs: {log_dir}")
    print(f"📄 Relatório: {report_path}")

    return fail == 0


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
