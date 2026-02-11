#!/usr/bin/env python3
"""
SCRIPT DE SINCRONIZAÇÃO UNIFICADO - VERSÃO CORRIGIDA
Execução segura via import dinâmico (sem subprocess, sem execução dupla)
"""

import os
import sys
import time
import json
import logging
import importlib.util
import traceback
import io

from datetime import datetime
from pathlib import Path
from contextlib import redirect_stdout, redirect_stderr
from unittest.mock import patch

# -----------------------------------------------------------------------------
# LOGGING
# -----------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("run_all_syncs")

# -----------------------------------------------------------------------------
# CONFIGURAÇÕES
# -----------------------------------------------------------------------------
SCRIPTS = [
    "sync_ly_cursos.py",
    "sync_ly_curriculos.py",
    "sync_ly_disciplinas.py",
    "sync_ly_alunos.py",
    "sync_ly_turmas.py",
    "sync_ly_docentes.py",
    "sync_ly_turma_docentes.py",
    "sync_ly_coordenacoes.py",
    "sync_ly_grades.py",
    "sync_ly_matriculas.py",
]

SCRIPT_FUNCTIONS = {
    "sync_ly_cursos.py": "sincronizar_cursos",
    "sync_ly_curriculos.py": "sincronizar_curriculos",
    "sync_ly_disciplinas.py": "sincronizar_disciplinas",
    "sync_ly_alunos.py": "sync_alunos",
    "sync_ly_turmas.py": "sincronizar_turmas",
    "sync_ly_docentes.py": "sincronizar_docentes",
    "sync_ly_turma_docentes.py": "sincronizar_turma_docentes",
    "sync_ly_coordenacoes.py": "sincronizar_coordenacoes",
    "sync_ly_grades.py": "sincronizar_grades",
    "sync_ly_matriculas.py": "main",
}

DELAY_BETWEEN_SCRIPTS = 3  # segundos

# -----------------------------------------------------------------------------
# AMBIENTE
# -----------------------------------------------------------------------------
def setup_environment() -> Path:
    project_root = Path(__file__).resolve().parent

    if str(project_root) not in sys.path:
        sys.path.append(str(project_root))

    os.chdir(project_root)

    logger.info(f"Projeto: {project_root}")
    return project_root


# -----------------------------------------------------------------------------
# EXECUÇÃO SEGURA DO SCRIPT
# -----------------------------------------------------------------------------
def import_and_execute_script(script_name: str, project_root: Path) -> dict:
    script_path = project_root / "sync" / script_name
    start_time = time.time()

    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()

    result_data = {
        "script": script_name,
        "success": False,
        "returncode": 1,
        "stdout": "",
        "stderr": "",
        "elapsed_time": 0.0,
        "has_stdout": False,
        "has_stderr": False,
    }

    if not script_path.exists():
        result_data["stderr"] = f"Script não encontrado: {script_path}"
        return result_data

    module_name = f"sync.{script_name.replace('.py', '')}"
    spec = importlib.util.spec_from_file_location(module_name, script_path)

    if spec is None or spec.loader is None:
        result_data["stderr"] = "Falha ao criar spec do módulo"
        return result_data

    module = importlib.util.module_from_spec(spec)

    try:
        with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
            spec.loader.exec_module(module)

            function_name = SCRIPT_FUNCTIONS.get(script_name)
            result = None

            if function_name and hasattr(module, function_name):
                if script_name == "sync_ly_matriculas.py":

                    def mock_input(prompt=""):
                        if "Escolha uma opção" in prompt:
                            return "1"
                        return ""

                    with patch("builtins.input", mock_input):
                        result = getattr(module, function_name)()
                else:
                    result = getattr(module, function_name)()

        success = result is not False

    except Exception:
        stderr_buffer.write(traceback.format_exc())
        success = False

    elapsed = time.time() - start_time

    result_data.update(
        {
            "success": success,
            "returncode": 0 if success else 1,
            "stdout": stdout_buffer.getvalue(),
            "stderr": stderr_buffer.getvalue(),
            "elapsed_time": elapsed,
            "has_stdout": bool(stdout_buffer.getvalue().strip()),
            "has_stderr": bool(stderr_buffer.getvalue().strip()),
        }
    )

    status = "SUCESSO" if success else "FALHA"
    logger.info(f"{script_name} - {status} ({elapsed:.2f}s)")

    return result_data


# -----------------------------------------------------------------------------
# LOGS
# -----------------------------------------------------------------------------
def save_individual_log(result: dict, log_dir: Path) -> None:
    name = Path(result["script"]).stem
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"{name}_{ts}.log"

    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)


def generate_summary_report(results: list, log_dir: Path) -> Path:
    report = {
        "timestamp": datetime.now().isoformat(),
        "total": len(results),
        "success": sum(r["success"] for r in results),
        "failure": sum(not r["success"] for r in results),
        "scripts": results,
    }

    path = log_dir / "relatorio_completo.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    return path


# -----------------------------------------------------------------------------
# MAIN
# -----------------------------------------------------------------------------
def main() -> bool:
    print("\n" + "=" * 70)
    print("🔄 EXECUTOR DE SINCRONIZAÇÕES LYCEUM")
    print("=" * 70)

    project_root = setup_environment()

    log_dir = project_root / "logs" / "execucoes" / datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )
    log_dir.mkdir(parents=True, exist_ok=True)

    results = []

    for idx, script in enumerate(SCRIPTS, 1):
        print(f"[{idx}/{len(SCRIPTS)}] Executando {script}")
        res = import_and_execute_script(script, project_root)
        results.append(res)
        save_individual_log(res, log_dir)

        if idx < len(SCRIPTS):
            time.sleep(DELAY_BETWEEN_SCRIPTS)

    report_path = generate_summary_report(results, log_dir)

    ok = sum(r["success"] for r in results)
    fail = len(results) - ok

    print("\nRESULTADO FINAL")
    print(f"✅ Sucessos: {ok}")
    print(f"❌ Falhas: {fail}")
    print(f"📁 Logs: {log_dir}")
    print(f"📄 Relatório: {report_path}")

    return fail == 0


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
