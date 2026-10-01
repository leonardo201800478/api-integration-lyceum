#!/usr/bin/env python3
"""
RUNNER DE SINCRONIZAÇÕES DE ALUNOS

Executa, em ordem, as sincronizações relacionadas ao fluxo de alunos:

1. sync_ly_alunos
2. sync_ly_matriculas
3. sync_ly_pessoa_by_id
4. sync_ly_aceit_contrato

O runner segue a mesma estrutura do run_all:
- execução isolada de cada módulo;
- captura de logs WARNING/ERROR;
- log consolidado em arquivo;
- relatório JSON individual por sincronização;
- relatório final consolidado;
- retorno de código de saída adequado para automação.

IMPORTANTE:
O sync_ly_pessoa_by_id é executado somente depois de
sync_ly_alunos. Dessa forma, ele pode localizar as pessoas vinculadas
aos alunos que acabaram de ser sincronizados, sem necessidade de
recarregar toda a tabela de pessoas.
"""

import importlib
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# =============================================================================
# CONFIGURAÇÃO DOS SYNCS
# =============================================================================

SYNC_MODULES = [
    ("sync.sync_ly_alunos", "run"),
    ("sync.sync_ly_matriculas", "run"),
    ("sync.sync_ly_pessoa_by_id", "run"),
    ("sync.sync_ly_aceit_contrato", "run"),
]

DELAY_SECONDS = 3


# =============================================================================
# LOGGER DE CAPTURA DE AVISOS/ERROS
# =============================================================================

class LogCaptureHandler(logging.Handler):
    """
    Captura mensagens de log WARNING e ERROR emitidas pelos syncs.

    As mensagens são armazenadas em uma lista de dicionários para que
    possam ser incorporadas ao relatório JSON consolidado.
    """

    def __init__(self, level: int = logging.WARNING) -> None:
        super().__init__(level)
        self.records: list[dict[str, Any]] = []

    def emit(self, record: logging.LogRecord) -> None:
        """Armazena uma ocorrência de log no formato utilizado pelo relatório."""
        self.records.append(
            {
                "timestamp": datetime.fromtimestamp(
                    record.created,
                    tz=timezone.utc,
                ).isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
            }
        )

    def clear(self) -> None:
        """Limpa os registros capturados pelo handler."""
        self.records.clear()


# =============================================================================
# AMBIENTE DE EXECUÇÃO
# =============================================================================

def setup_environment() -> Path:
    """
    Configura o diretório raiz do projeto.

    O comportamento é equivalente ao run_all: o diretório do próprio
    runner é colocado no sys.path e definido como diretório de trabalho.
    """
    root = Path(__file__).resolve().parent

    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    os.chdir(root)

    return root


# =============================================================================
# EXECUÇÃO DE UM SYNC
# =============================================================================

def execute_sync(module_path: str, func_name: str) -> dict[str, Any]:
    """
    Importa dinamicamente um módulo e executa sua função.

    Parameters
    ----------
    module_path:
        Caminho Python completo do módulo, por exemplo
        ``sync.sync_ly_alunos``.

    func_name:
        Nome da função de entrada do módulo, normalmente ``run``.

    Returns
    -------
    dict[str, Any]
        Resultado padronizado contendo:
        - módulo;
        - função;
        - sucesso;
        - erro;
        - tempo de execução;
        - logs WARNING/ERROR capturados.
    """
    start = time.time()

    result: dict[str, Any] = {
        "module": module_path,
        "function": func_name,
        "success": False,
        "error": None,
        "elapsed": 0.0,
        "logs": [],
    }

    capture_handler = LogCaptureHandler(logging.WARNING)
    root_logger = logging.getLogger()
    root_logger.addHandler(capture_handler)

    try:
        logger.info("▶ Executando %s.%s()", module_path, func_name)

        module = importlib.import_module(module_path)

        if not hasattr(module, func_name):
            raise RuntimeError(
                f"Função '{func_name}' não encontrada no módulo {module_path}"
            )

        sync_function = getattr(module, func_name)
        success = sync_function()

        # Mantém a mesma semântica do run_all:
        # qualquer retorno diferente de False é considerado sucesso.
        result["success"] = success is not False

    except Exception as exc:  # noqa: BLE001
        result["error"] = str(exc)

        logger.error(
            "❌ Erro em %s: %s",
            module_path,
            exc,
            exc_info=True,
        )

    finally:
        root_logger.removeHandler(capture_handler)
        result["logs"] = capture_handler.records
        result["elapsed"] = time.time() - start

    return result


# =============================================================================
# LOGGING CONSOLIDADO
# =============================================================================

def setup_logging(log_dir: Path) -> logging.Logger:
    """
    Configura logging para console e arquivo.

    Parameters
    ----------
    log_dir:
        Diretório onde será criado o arquivo ``execucao.log``.

    Returns
    -------
    logging.Logger
        Logger utilizado pelo runner.
    """
    log_format = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    root_logger = logging.getLogger()

    # Remove handlers anteriores para evitar logs duplicados.
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    root_logger.setLevel(logging.INFO)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(
        logging.Formatter(log_format, date_format)
    )
    root_logger.addHandler(console_handler)

    log_file = log_dir / "execucao.log"

    file_handler = logging.FileHandler(
        log_file,
        encoding="utf-8",
    )
    file_handler.setFormatter(
        logging.Formatter(log_format, date_format)
    )
    root_logger.addHandler(file_handler)

    runner_logger = logging.getLogger("run_aluno")
    runner_logger.info("📁 Log consolidado: %s", log_file)

    return runner_logger


# =============================================================================
# RELATÓRIO FINAL
# =============================================================================

def build_report(
    results: list[dict[str, Any]],
    execution_id: str,
) -> dict[str, Any]:
    """
    Monta o relatório consolidado da execução.

    Parameters
    ----------
    results:
        Resultados individuais produzidos por execute_sync().

    execution_id:
        Identificador temporal da execução.

    Returns
    -------
    dict[str, Any]
        Estrutura serializável em JSON com resumo e logs de validação.
    """
    success_count = sum(1 for result in results if result["success"])
    fail_count = len(results) - success_count

    all_validation_logs: list[dict[str, Any]] = []

    for result in results:
        for log_entry in result.get("logs", []):
            entry = dict(log_entry)
            entry["module"] = result["module"]
            all_validation_logs.append(entry)

    validation_stats: dict[str, Any] = {
        "total_warnings": sum(
            1
            for log in all_validation_logs
            if log["level"] == "WARNING"
        ),
        "total_errors": sum(
            1
            for log in all_validation_logs
            if log["level"] == "ERROR"
        ),
        "by_module": {},
    }

    for log in all_validation_logs:
        module = log["module"]

        if module not in validation_stats["by_module"]:
            validation_stats["by_module"][module] = {
                "WARNING": 0,
                "ERROR": 0,
            }

        level = log["level"]

        if level in validation_stats["by_module"][module]:
            validation_stats["by_module"][module][level] += 1

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "execucao": execution_id,
        "total_modulos": len(results),
        "sucessos": success_count,
        "falhas": fail_count,
        "validacao": {
            "total_warnings": validation_stats["total_warnings"],
            "total_errors": validation_stats["total_errors"],
            "por_modulo": validation_stats["by_module"],
            "logs": all_validation_logs,
        },
        "resultados": results,
    }


# =============================================================================
# FUNÇÃO PRINCIPAL
# =============================================================================

def main() -> bool:
    """
    Executa o fluxo completo de sincronização de alunos.

    A ordem é deliberada:

        alunos
            ↓
        matrículas
            ↓
        pessoas dos alunos novos
            ↓
        aceite de contrato

    Returns
    -------
    bool
        True quando todos os syncs terminam sem falha; False caso
        qualquer etapa apresente erro ou retorne False.
    """
    print("\n" + "=" * 70)
    print("🎓 RUNNER DE SINCRONIZAÇÕES DE ALUNOS")
    print("=" * 70)

    root = setup_environment()

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    log_dir = root / "logs" / "execucoes" / f"aluno_{timestamp}"
    log_dir.mkdir(parents=True, exist_ok=True)

    global logger
    logger = setup_logging(log_dir)

    results: list[dict[str, Any]] = []
    total_steps = len(SYNC_MODULES)

    for index, (module_path, func_name) in enumerate(SYNC_MODULES, 1):
        logger.info(
            "[%02d/%02d] %s",
            index,
            total_steps,
            module_path,
        )

        # Destaque explícito da etapa que resolve as pessoas dos novos alunos.
        if module_path == "sync.sync_ly_pessoa_by_id":
            logger.info(
                "👤 Etapa de pessoas: executada após sync_ly_alunos "
                "para processar as pessoas referenciadas pelos alunos "
                "recém-sincronizados."
            )

        if module_path == "sync.sync_ly_aceit_contrato":
            logger.info(
                "📄 Etapa de aceite de contrato: iniciada após "
                "alunos, matrículas e pessoas."
            )

        result = execute_sync(module_path, func_name)
        results.append(result)

        module_name = module_path.split(".")[-1]
        result_path = log_dir / f"{module_name}.json"

        with result_path.open("w", encoding="utf-8") as file:
            json.dump(
                result,
                file,
                ensure_ascii=False,
                indent=2,
            )

        if index < total_steps:
            time.sleep(DELAY_SECONDS)

    report = build_report(results, timestamp)

    report_path = log_dir / "relatorio_final.json"

    with report_path.open("w", encoding="utf-8") as file:
        json.dump(
            report,
            file,
            ensure_ascii=False,
            indent=2,
        )

    success_count = report["sucessos"]
    fail_count = report["falhas"]
    validation = report["validacao"]

    print("\n" + "=" * 70)
    print("📊 RESUMO DA EXECUÇÃO")
    print("=" * 70)
    print(
        f"✅ Sincronias com sucesso: "
        f"{success_count}/{len(results)}"
    )
    print(
        f"❌ Sincronias com falha:   "
        f"{fail_count}/{len(results)}"
    )
    print(
        f"⚠️  Total de avisos: "
        f"{validation['total_warnings']}"
    )
    print(
        f"🔴 Total de erros:  "
        f"{validation['total_errors']}"
    )
    print(f"📁 Diretório de logs: {log_dir}")
    print(f"📄 Relatório consolidado: {report_path}")
    print("=" * 70)

    if validation["logs"]:
        logger.info("🔍 Detalhamento de avisos/erros por sincronia:")

        for module, counts in validation["por_modulo"].items():
            if counts["WARNING"] or counts["ERROR"]:
                logger.info(
                    "   - %s: %d avisos, %d erros",
                    module,
                    counts["WARNING"],
                    counts["ERROR"],
                )

    return fail_count == 0


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    sys.exit(0 if main() else 1)
