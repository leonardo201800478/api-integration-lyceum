#!/usr/bin/env python3
"""
RUNNER UNIFICADO DE SINCRONIZAÇÕES LYCEUM
- Execução controlada e isolada por módulo
- Captura automática de logs de validação (e-mails inválidos, CPFs, etc.)
- Geração de log consolidado e relatório JSON detalhado
- Compatível com todos os syncs que expõem função run() → bool
"""

import sys
import os
import time
import json
import logging
import importlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

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
    # NOVOS MÓDULOS DE PROVAS
    ("sync.sync_ly_provas_disciplinas", "run"),
    ("sync.sync_ly_provas", "run"),
]

DELAY_SECONDS = 3  # Aguardo entre sincronias (bom comportamento)

# =============================================================================
# HANDLER PERSONALIZADO PARA CAPTURAR LOGS DOS MÓDULOS
# =============================================================================
class LogCaptureHandler(logging.Handler):
    """
    Handler que coleta mensagens de log em uma lista de dicionários.
    Útil para inspecionar warnings/errors emitidos durante a execução de um sync.
    """
    def __init__(self, level=logging.WARNING):
        super().__init__(level)
        self.records = []

    def emit(self, record):
        self.records.append({
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        })

    def clear(self):
        self.records.clear()

# =============================================================================
# AMBIENTE DE EXECUÇÃO
# =============================================================================
def setup_environment() -> Path:
    """Configura o path do projeto e retorna o diretório raiz."""
    root = Path(__file__).resolve().parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    os.chdir(root)
    return root

# =============================================================================
# EXECUÇÃO DE UM MÓDULO DE SINCRONIA COM CAPTURA DE LOGS
# =============================================================================
def execute_sync(module_path: str, func_name: str) -> Dict[str, Any]:
    """
    Importa dinamicamente um módulo e executa sua função 'run'.
    Captura todos os logs de nível WARNING ou superior emitidos durante a execução.
    Retorna um dicionário com status, erro, tempo e logs capturados.
    """
    start = time.time()
    result = {
        "module": module_path,
        "function": func_name,
        "success": False,
        "error": None,
        "elapsed": 0.0,
        "logs": [],  # Logs de validação (WARNING+)
    }

    # Handler temporário para capturar logs de aviso/erro
    capture_handler = LogCaptureHandler(logging.WARNING)
    root_logger = logging.getLogger()
    root_logger.addHandler(capture_handler)

    try:
        logger.info(f"▶ Executando {module_path}.{func_name}()")
        module = importlib.import_module(module_path)

        if not hasattr(module, func_name):
            raise RuntimeError(f"Função '{func_name}' não encontrada no módulo {module_path}")

        success = getattr(module, func_name)()
        result["success"] = success is not False

    except Exception as e:
        result["error"] = str(e)
        logger.error(f"❌ Erro em {module_path}: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Remove o handler e guarda os logs capturados
        root_logger.removeHandler(capture_handler)
        result["logs"] = capture_handler.records
        result["elapsed"] = time.time() - start

    return result

# =============================================================================
# CONFIGURAÇÃO DE LOGGING CONSOLIDADO (ARQUIVO + CONSOLE)
# =============================================================================
def setup_logging(log_dir: Path) -> logging.Logger:
    """
    Configura o logger raiz com:
    - Console (stdout) com formato simples
    - Arquivo de log completo dentro de log_dir/execucao.log
    Retorna o logger 'run_all' para uso no script.
    """
    log_format = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # Remove handlers existentes para evitar duplicidade
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    root_logger.setLevel(logging.INFO)

    # Handler para console (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(log_format, date_format))
    root_logger.addHandler(console_handler)

    # Handler para arquivo consolidado
    log_file = log_dir / "execucao.log"
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter(log_format, date_format))
    root_logger.addHandler(file_handler)

    logger = logging.getLogger("run_all")
    logger.info(f"📁 Log consolidado: {log_file}")
    return logger

# =============================================================================
# FUNÇÃO PRINCIPAL
# =============================================================================
def main() -> bool:
    print("\n" + "=" * 70)
    print("🔄 EXECUTOR DE SINCRONIZAÇÕES LYCEUM (PADRONIZADO COM CAPTURA DE LOGS)")
    print("=" * 70)

    root = setup_environment()

    # Cria diretório de logs para esta execução
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = root / "logs" / "execucoes" / timestamp
    log_dir.mkdir(parents=True, exist_ok=True)

    # Configura logging (console + arquivo)
    global logger
    logger = setup_logging(log_dir)

    results = []

    # Executa cada sincronia
    for idx, (module, func) in enumerate(SYNC_MODULES, 1):
        logger.info(f"[{idx:02d}/{len(SYNC_MODULES):02d}] {module}")
        res = execute_sync(module, func)
        results.append(res)

        # Salva resultado individual em JSON
        module_name = module.split('.')[-1]
        result_path = log_dir / f"{module_name}.json"
        with open(result_path, "w", encoding="utf-8") as f:
            json.dump(res, f, ensure_ascii=False, indent=2)

        # Aguarda entre execuções (menos sobrecarga na API)
        if idx < len(SYNC_MODULES):
            time.sleep(DELAY_SECONDS)

    # =========================================================================
    # RELATÓRIO FINAL CONSOLIDADO
    # =========================================================================
    success_count = sum(1 for r in results if r["success"])
    fail_count = len(results) - success_count

    # Agrega todos os logs de validação capturados
    all_validation_logs = []
    for r in results:
        for log_entry in r.get("logs", []):
            log_entry["module"] = r["module"]
            all_validation_logs.append(log_entry)

    # Estatísticas dos logs de validação
    validation_stats = {
        "total_warnings": len([l for l in all_validation_logs if l["level"] == "WARNING"]),
        "total_errors": len([l for l in all_validation_logs if l["level"] == "ERROR"]),
        "by_module": {}
    }
    for log in all_validation_logs:
        mod = log["module"]
        if mod not in validation_stats["by_module"]:
            validation_stats["by_module"][mod] = {"WARNING": 0, "ERROR": 0}
        validation_stats["by_module"][mod][log["level"]] += 1

    # Relatório completo
    report = {
        "timestamp": datetime.now().isoformat(),
        "execucao": timestamp,
        "total_modulos": len(results),
        "sucessos": success_count,
        "falhas": fail_count,
        "validacao": {
            "total_warnings": validation_stats["total_warnings"],
            "total_errors": validation_stats["total_errors"],
            "por_modulo": validation_stats["by_module"],
            "logs": all_validation_logs  # lista completa para análise detalhada
        },
        "resultados": results
    }

    report_path = log_dir / "relatorio_final.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # Exibe resumo no console
    print("\n" + "=" * 70)
    print("📊 RESUMO DA EXECUÇÃO")
    print("=" * 70)
    print(f"✅ Sincronias com sucesso: {success_count}/{len(results)}")
    print(f"❌ Sincronias com falha:    {fail_count}/{len(results)}")
    print(f"⚠️  Total de avisos (validação): {validation_stats['total_warnings']}")
    print(f"🔴 Total de erros (validação):   {validation_stats['total_errors']}")
    print(f"📁 Diretório de logs: {log_dir}")
    print(f"📄 Relatório consolidado: {report_path}")
    print("=" * 70)

    # Loga resumo de avisos por módulo
    if all_validation_logs:
        logger.info("🔍 Detalhamento de avisos/erros por sincronia:")
        for mod, counts in validation_stats["by_module"].items():
            if counts["WARNING"] > 0 or counts["ERROR"] > 0:
                logger.info(f"   - {mod}: {counts['WARNING']} avisos, {counts['ERROR']} erros")

    return fail_count == 0


if __name__ == "__main__":
    sys.exit(0 if main() else 1)