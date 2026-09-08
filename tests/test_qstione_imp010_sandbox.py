"""Teste controlado do IMP-010 no Sandbox Qstione.

Cadeia validada:
    IMP-001 -> IMP-010

Seleciona um aluno real com curso correspondente. Nenhuma tabela local e alterada.
"""

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
from qstione.config.qstione_config import (
    QSTIONE_BASE_URL,
    QSTIONE_SSL_VERIFY,
    QSTIONE_TIMEOUT,
    QSTIONE_TOKEN,
    validar_configuracao_qstione,
)

LOG_PATH = ROOT / "logs" / "test_qstione_imp010_sandbox.log"


def configurar_log() -> logging.Logger:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("test_qstione_imp010_sandbox")
    logger.handlers.clear()
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
    logger.addHandler(handler)
    logger.propagate = False
    return logger


def ler_registros() -> tuple[dict, dict]:
    """Seleciona um aluno e o curso correspondente em uma unica consulta."""
    sql = """
        SELECT TOP 1
            a.[matriculaAluno],
            a.[nomeAluno],
            a.[emailAluno],
            a.[codigoCurso],
            a.[turno],
            a.[codigoIdentificacaoAVA],
            c.[codigoCurso],
            c.[nomeCurso],
            c.[quantPeriodos],
            c.[codigoUnidadeOrganizacional]
        FROM dbo.[imp_010_alunos] a
        INNER JOIN dbo.[imp_001_cursos] c
            ON LTRIM(RTRIM(CAST(c.[codigoCurso] AS NVARCHAR(100)))) =
               LTRIM(RTRIM(CAST(a.[codigoCurso] AS NVARCHAR(100))))
        WHERE NULLIF(LTRIM(RTRIM(CAST(a.[matriculaAluno] AS NVARCHAR(100)))), '') IS NOT NULL
          AND NULLIF(LTRIM(RTRIM(a.[nomeAluno])), '') IS NOT NULL
          AND NULLIF(LTRIM(RTRIM(a.[emailAluno])), '') IS NOT NULL
          AND NULLIF(LTRIM(RTRIM(CAST(a.[codigoCurso] AS NVARCHAR(100)))), '') IS NOT NULL
        ORDER BY a.[codigoCurso], a.[matriculaAluno]
    """

    with get_db_connection(database_name="qstione") as conn:
        row = conn.execute(sql).fetchone()

    if row is None:
        raise RuntimeError(
            "Nao existe aluno valido em IMP-010 com curso correspondente em IMP-001."
        )

    aluno = {
        campo: row[indice]
        for indice, campo in enumerate(CAMPOS_API["IMP-010"])
    }
    curso = {
        "codigoCurso": row[6],
        "nomeCurso": row[7],
        "quantPeriodos": row[8],
        "codigoUnidadeOrganizacional": row[9],
    }

    if str(aluno["codigoCurso"]).strip() != str(curso["codigoCurso"]).strip():
        raise RuntimeError("Inconsistencia entre IMP-010.codigoCurso e IMP-001.codigoCurso.")

    return curso, aluno


def enviar(cliente: ClienteQstione, transacao: str, registro: dict) -> bool:
    print(f"\n{transacao} payload:")
    print(json.dumps(registro, ensure_ascii=False, indent=2, default=str))

    resultado = cliente.enviar(transacao, [registro])

    print(f"HTTP: {resultado.http_status}")
    print(f"codigoStatus: {resultado.codigo_status}")
    print(f"idRequisicao: {resultado.id_requisicao}")
    print(f"modoExecucao: {resultado.modo_execucao}")
    print(f"quantidadeErros: {resultado.quantidade_registros_erro}")

    if resultado.corpo_bruto not in (None, [], {}):
        print("corpoResposta:")
        print(json.dumps(resultado.corpo_bruto, ensure_ascii=False, indent=2, default=str))

    if resultado.assincrono:
        print(f"❌ {transacao} retornou modoExecucao=A; teste interrompido.")
        return False

    if not resultado.sucesso:
        print(f"❌ {transacao} rejeitada pela API.")
        for erro in resultado.erros:
            print(
                "   ERRO API | registro=%s | excecao=%s | detalhes=%s"
                % (
                    erro.get("numeroRegistro"),
                    erro.get("nomeExcecao"),
                    erro.get("detalhesFalha"),
                )
            )
        return False

    print(f"✅ {transacao} aceita com sucesso.")
    return True


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
        print(f"Endpoint: {QSTIONE_BASE_URL}")
        print(f"SSL verify: {QSTIONE_SSL_VERIFY}")
        print(f"Timeout: {QSTIONE_TIMEOUT}s")
        print("Token: configurado (nao exibido)")
        print(f"Log: {LOG_PATH}")

        curso, aluno = ler_registros()

        print(f"\nDependencia detectada: IMP-010.codigoCurso = {aluno['codigoCurso']}")
        print(f"Dependencia detectada: IMP-010.matriculaAluno = {aluno['matriculaAluno']}")
        print("Ordem de envio: IMP-001 → IMP-010")

    except Exception as exc:
        logger.exception("Falha na preparacao do teste IMP-010: %s", exc)
        print(f"\n❌ FALHA: {exc}")
        print(f"Log: {LOG_PATH}")
        return 1

    cliente = ClienteQstione(
        url=QSTIONE_BASE_URL,
        token=QSTIONE_TOKEN or "",
        timeout=QSTIONE_TIMEOUT,
        ssl_verify=QSTIONE_SSL_VERIFY,
    )

    try:
        if not enviar(cliente, "IMP-001", curso):
            return 1
        if not enviar(cliente, "IMP-010", aluno):
            return 1
    finally:
        cliente.close()

    logger.info("IMP-001 OK | codigoCurso=%s", curso["codigoCurso"])
    logger.info("IMP-010 OK | matriculaAluno=%s | codigoCurso=%s", aluno["matriculaAluno"], aluno["codigoCurso"])

    print("\n" + "=" * 78)
    print(" TESTE CONTROLADO CONCLUIDO")
    print(" IMP-001: OK")
    print(" IMP-010: OK")
    print(" Nenhuma tabela local foi alterada.")
    print(f" Log: {LOG_PATH}")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
