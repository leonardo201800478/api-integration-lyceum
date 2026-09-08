from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.database import get_db_connection
from qstione.api.cliente import CAMPOS_API, ClienteQstione
from qstione.config.qstione_config import validar_configuracao_qstione

LOG_PATH = ROOT / "logs" / "test_qstione_imp010_sandbox.log"


def configurar_log() -> logging.Logger:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("test_qstione_imp010_sandbox")
    logger.handlers.clear()
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
    logger.addHandler(handler)
    return logger


def ler_registro_imp010() -> dict:
    campos = CAMPOS_API["IMP-010"]
    sql = f"""
        SELECT TOP 1
            {', '.join(f'dbo.imp_010_alunos.[{campo}]' for campo in campos)}
        FROM dbo.imp_010_alunos
        INNER JOIN dbo.imp_001_cursos c
            ON c.codigoCurso = dbo.imp_010_alunos.codigoCurso
        WHERE NULLIF(LTRIM(RTRIM(dbo.imp_010_alunos.matriculaAluno)), '') IS NOT NULL
          AND NULLIF(LTRIM(RTRIM(dbo.imp_010_alunos.nomeAluno)), '') IS NOT NULL
          AND NULLIF(LTRIM(RTRIM(dbo.imp_010_alunos.emailAluno)), '') IS NOT NULL
          AND NULLIF(LTRIM(RTRIM(dbo.imp_010_alunos.codigoCurso)), '') IS NOT NULL
        ORDER BY dbo.imp_010_alunos.codigoCurso,
                 dbo.imp_010_alunos.matriculaAluno
    """
    with get_db_connection("qstione") as conn:
        cursor = conn.cursor()
        cursor.execute(sql)
        row = cursor.fetchone()
        if not row:
            raise RuntimeError("Nenhum registro valido encontrado em dbo.imp_010_alunos com curso correspondente em IMP-001.")
        return dict(zip(campos, row))


def main() -> int:
    logger = configurar_log()
    print("=" * 78)
    print(" TESTE CONTROLADO — CADEIA IMP-001 + IMP-010")
    print(" Protocolo: 1.2.10 | Dicionario: 1.15.0")
    print(" Escopo: 1 curso + 1 aluno")
    print(" Nenhuma tabela local sera alterada.")
    print("=" * 78)

    try:
        validar_configuracao_qstione()
        from qstione.config.qstione_config import QSTIONE_BASE_URL, QSTIONE_SSL_VERIFY, QSTIONE_TIMEOUT
        print(f"Endpoint: {QSTIONE_BASE_URL}")
        print(f"SSL verify: {QSTIONE_SSL_VERIFY}")
        print(f"Timeout: {QSTIONE_TIMEOUT}s")
        print("Token: configurado (nao exibido)")
        print(f"Log: {LOG_PATH}")

        aluno = ler_registro_imp010()
        codigo_curso = aluno["codigoCurso"]
        print(f"\nDependencia detectada: IMP-010.codigoCurso = {codigo_curso}")
        print(f"Dependencia detectada: IMP-010.matriculaAluno = {aluno['matriculaAluno']}")
        print(f"Ordem de envio: IMP-001 → IMP-010")

        with get_db_connection("qstione") as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT TOP 1 codigoCurso, nomeCurso, quantPeriodos, codigoUnidadeOrganizacional
                FROM dbo.imp_001_cursos
                WHERE codigoCurso = ?
                ORDER BY codigoCurso
            """, codigo_curso)
            curso_row = cursor.fetchone()

        if not curso_row:
            raise RuntimeError(f"Curso {codigo_curso} nao encontrado em dbo.imp_001_cursos.")

        curso = {
            "codigoCurso": curso_row[0],
            "nomeCurso": curso_row[1],
            "quantPeriodos": curso_row[2],
            "codigoUnidadeOrganizacional": curso_row[3],
        }

        cliente = ClienteQstione()
        resultados = {}

        print("\nIMP-001 payload:")
        print(json.dumps(curso, ensure_ascii=False, indent=2))
        resultado = cliente.enviar("IMP-001", [curso])
        resultados["IMP-001"] = resultado
        print(f"HTTP: {resultado.http_status}")
        print(f"codigoStatus: {resultado.codigo_status}")
        print(f"idRequisicao: {resultado.id_requisicao}")
        print(f"modoExecucao: {resultado.modo_execucao}")
        print(f"quantidadeErros: {len(resultado.erros)}")
        if not resultado.sucesso:
            print("❌ IMP-001 rejeitado. Teste interrompido.")
            return 1
        print("✅ IMP-001 aceita com sucesso.")

        print("\nIMP-010 payload:")
        print(json.dumps(aluno, ensure_ascii=False, indent=2))
        resultado = cliente.enviar("IMP-010", [aluno])
        resultados["IMP-010"] = resultado
        print(f"HTTP: {resultado.http_status}")
        print(f"codigoStatus: {resultado.codigo_status}")
        print(f"idRequisicao: {resultado.id_requisicao}")
        print(f"modoExecucao: {resultado.modo_execucao}")
        print(f"quantidadeErros: {len(resultado.erros)}")
        if not resultado.sucesso:
            print("❌ IMP-010 rejeitado.")
            if resultado.corpo_resposta:
                print("corpoResposta:")
                print(resultado.corpo_resposta)
            return 1
        print("✅ IMP-010 aceita com sucesso.")

        logger.info("IMP-001 OK | codigoCurso=%s", codigo_curso)
        logger.info("IMP-010 OK | matriculaAluno=%s | codigoCurso=%s", aluno["matriculaAluno"], codigo_curso)

        print("\n" + "=" * 78)
        print(" TESTE CONTROLADO CONCLUIDO")
        print(" IMP-001: OK")
        print(" IMP-010: OK")
        print(" Nenhuma tabela local foi alterada.")
        print(f" Log: {LOG_PATH}")
        print("=" * 78)
        return 0

    except Exception as exc:
        logger.exception("Falha no teste: %s", exc)
        print(f"\n❌ FALHA: {exc}")
        print(f"Log: {LOG_PATH}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
