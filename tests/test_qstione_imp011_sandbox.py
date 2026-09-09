"""Teste controlado do IMP-011 no Sandbox Qstione.

Cadeia validada:
    IMP-001 -> IMP-002 -> IMP-005 -> IMP-006 -> IMP-010 -> IMP-011

Seleciona uma relacao real aluno/oferta somente quando todas as dependencias
locais necessarias existem. Nenhuma tabela local e alterada.
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
from qstione.api.cliente import ClienteQstione
from qstione.config.qstione_config import (
    QSTIONE_BASE_URL,
    QSTIONE_SSL_VERIFY,
    QSTIONE_TIMEOUT,
    QSTIONE_TOKEN,
    validar_configuracao_qstione,
)

LOG_FILE = ROOT / "logs" / "test_qstione_imp011_sandbox.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger("test_qstione_imp011_sandbox")
logger.handlers.clear()
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
logger.addHandler(handler)
logger.propagate = False


def buscar_cadeia() -> tuple[dict, dict, dict, dict, dict]:
    """Seleciona um vinculo IMP-011 com todas as dependencias locais completas."""
    sql = """
        SELECT TOP 1
            ao.[codigoOferta],
            ao.[matriculaAluno],
            ao.[codigoCurso],

            o.[codigoOferta],
            o.[nomeOferta],
            o.[codigoDisciplina],
            o.[semestreOferta],
            o.[codigoTipoOferta],
            o.[codigoOfertaOrigem],
            o.[turno],
            o.[codigoIdentificacaoAVA],

            d.[codigoDisciplina],
            d.[nomeDisciplina],
            d.[codigoCurso],
            d.[periodo],

            c.[codigoCurso],
            c.[nomeCurso],
            c.[quantPeriodos],
            c.[codigoUnidadeOrganizacional],

            a.[matriculaAluno],
            a.[nomeAluno],
            a.[emailAluno],
            a.[codigoCurso],
            a.[turno],
            a.[codigoIdentificacaoAVA]
        FROM dbo.[imp_011_alunos_ofertas] ao
        INNER JOIN dbo.[imp_005_ofertas] o
            ON LTRIM(RTRIM(CAST(o.[codigoOferta] AS NVARCHAR(200)))) =
               LTRIM(RTRIM(CAST(ao.[codigoOferta] AS NVARCHAR(200))))
        INNER JOIN dbo.[imp_002_disciplina] d
            ON LTRIM(RTRIM(CAST(d.[codigoDisciplina] AS NVARCHAR(100)))) =
               LTRIM(RTRIM(CAST(o.[codigoDisciplina] AS NVARCHAR(100))))
        INNER JOIN dbo.[imp_001_cursos] c
            ON LTRIM(RTRIM(CAST(c.[codigoCurso] AS NVARCHAR(100)))) =
               LTRIM(RTRIM(CAST(d.[codigoCurso] AS NVARCHAR(100))))
        INNER JOIN dbo.[imp_010_alunos] a
            ON LTRIM(RTRIM(CAST(a.[matriculaAluno] AS NVARCHAR(100)))) =
               LTRIM(RTRIM(CAST(ao.[matriculaAluno] AS NVARCHAR(100))))
           AND LTRIM(RTRIM(CAST(a.[codigoCurso] AS NVARCHAR(100)))) =
               LTRIM(RTRIM(CAST(ao.[codigoCurso] AS NVARCHAR(100))))
        WHERE ao.[codigoOferta] IS NOT NULL
          AND LTRIM(RTRIM(CAST(ao.[codigoOferta] AS NVARCHAR(200)))) <> ''
          AND ao.[matriculaAluno] IS NOT NULL
          AND LTRIM(RTRIM(CAST(ao.[matriculaAluno] AS NVARCHAR(100)))) <> ''
          AND ao.[codigoCurso] IS NOT NULL
          AND LTRIM(RTRIM(CAST(ao.[codigoCurso] AS NVARCHAR(100)))) <> ''
        ORDER BY ao.[codigoOferta], ao.[matriculaAluno]
    """

    with get_db_connection(database_name="qstione") as conn:
        row = conn.execute(sql).fetchone()

    if row is None:
        raise RuntimeError(
            "Nao existe registro IMP-011 com dependencias completas em "
            "IMP-005, IMP-002, IMP-001 e IMP-010."
        )

    vinculo = {
        "codigoOferta": row[0],
        "matriculaAluno": row[1],
        "codigoCurso": row[2],
    }
    oferta = {
        "codigoOferta": row[3],
        "nomeOferta": row[4],
        "codigoDisciplina": row[5],
        "semestreOferta": row[6],
        "codigoTipoOferta": row[7],
        "codigoOfertaOrigem": row[8],
        "turno": row[9],
        "codigoIdentificacaoAVA": row[10],
    }
    disciplina = {
        "codigoDisciplina": row[11],
        "nomeDisciplina": row[12],
        "codigoCurso": row[13],
        "periodo": row[14],
    }
    curso = {
        "codigoCurso": row[15],
        "nomeCurso": row[16],
        "quantPeriodos": row[17],
        "codigoUnidadeOrganizacional": row[18],
    }
    aluno = {
        "matriculaAluno": row[19],
        "nomeAluno": row[20],
        "emailAluno": row[21],
        "codigoCurso": row[22],
        "turno": row[23],
        "codigoIdentificacaoAVA": row[24],
    }

    validar_consistencia(curso, disciplina, oferta, aluno, vinculo)
    return curso, disciplina, oferta, aluno, vinculo


def validar_consistencia(
    curso: dict,
    disciplina: dict,
    oferta: dict,
    aluno: dict,
    vinculo: dict,
) -> None:
    def igual(a: object, b: object) -> bool:
        return str(a).strip().lower() == str(b).strip().lower()

    if not igual(disciplina["codigoCurso"], curso["codigoCurso"]):
        raise RuntimeError("Inconsistencia: IMP-002.codigoCurso difere do IMP-001.")
    if not igual(oferta["codigoDisciplina"], disciplina["codigoDisciplina"]):
        raise RuntimeError("Inconsistencia: IMP-005.codigoDisciplina difere do IMP-002.")
    if not igual(vinculo["codigoOferta"], oferta["codigoOferta"]):
        raise RuntimeError("Inconsistencia: IMP-011.codigoOferta difere do IMP-005.")
    if not igual(aluno["codigoCurso"], curso["codigoCurso"]):
        raise RuntimeError("Inconsistencia: IMP-010.codigoCurso difere do IMP-001.")
    if not igual(vinculo["matriculaAluno"], aluno["matriculaAluno"]):
        raise RuntimeError("Inconsistencia: IMP-011.matriculaAluno difere do IMP-010.")
    if not igual(vinculo["codigoCurso"], curso["codigoCurso"]):
        raise RuntimeError("Inconsistencia: IMP-011.codigoCurso difere do IMP-001.")


def enviar(cliente: ClienteQstione, transacao: str, registro: dict) -> bool:
    print(f"\n{transacao} payload:")
    print(json.dumps(registro, ensure_ascii=False, indent=2, default=str))
    logger.info("ENVIANDO %s | %s", transacao, registro)

    resultado = cliente.enviar(transacao, [registro])

    print(f"HTTP: {resultado.http_status}")
    print(f"codigoStatus: {resultado.codigo_status}")
    print(f"idRequisicao: {resultado.id_requisicao}")
    print(f"modoExecucao: {resultado.modo_execucao}")
    print(f"quantidadeErros: {resultado.quantidade_registros_erro}")

    logger.info(
        "RETORNO %s | HTTP=%s | status=%s | id=%s | modo=%s | erros=%s",
        transacao,
        resultado.http_status,
        resultado.codigo_status,
        resultado.id_requisicao,
        resultado.modo_execucao,
        resultado.quantidade_registros_erro,
    )

    if resultado.corpo_bruto not in (None, [], {}):
        print("corpoResposta:")
        print(json.dumps(resultado.corpo_bruto, ensure_ascii=False, indent=2, default=str))
        logger.info("CORPO RESPOSTA %s | %s", transacao, resultado.corpo_bruto)

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
    print("=" * 78)
    print(" TESTE CONTROLADO — CADEIA IMP-001 + IMP-002 + IMP-005 + IMP-010 + IMP-011")
    print(" Protocolo: 1.2.10 | Dicionario: 1.15.0")
    print(" Escopo: 1 curso + 1 disciplina + 1 oferta + 1 aluno + 1 vinculo")
    print(" Nenhuma tabela local sera alterada.")
    print("=" * 78)

    try:
        validar_configuracao_qstione()
        print(f"Endpoint: {QSTIONE_BASE_URL}")
        print(f"SSL verify: {QSTIONE_SSL_VERIFY}")
        print(f"Timeout: {QSTIONE_TIMEOUT}s")
        print("Token: configurado (nao exibido)")
        print(f"Log: {LOG_FILE}")

        curso, disciplina, oferta, aluno, vinculo = buscar_cadeia()

        print(f"\nDependencia detectada: IMP-011.codigoOferta = {vinculo['codigoOferta']}")
        print(f"Dependencia detectada: IMP-011.matriculaAluno = {vinculo['matriculaAluno']}")
        print(f"Dependencia detectada: IMP-011.codigoCurso = {vinculo['codigoCurso']}")
        print("Ordem de envio: IMP-001 → IMP-002 → IMP-005 → IMP-010 → IMP-011")

    except Exception as exc:
        logger.exception("Falha na preparacao do teste IMP-011: %s", exc)
        print(f"\n❌ FALHA: {exc}")
        print(f"Log: {LOG_FILE}")
        return 1

    cliente = ClienteQstione(
        url=QSTIONE_BASE_URL,
        token=QSTIONE_TOKEN or "",
        timeout=QSTIONE_TIMEOUT,
        ssl_verify=QSTIONE_SSL_VERIFY,
    )

    try:
        for transacao, registro in (
            ("IMP-001", curso),
            ("IMP-002", disciplina),
            ("IMP-005", oferta),
            ("IMP-010", aluno),
            ("IMP-011", vinculo),
        ):
            if not enviar(cliente, transacao, registro):
                return 1
    finally:
        cliente.close()

    logger.info("TESTE CONCLUIDO | IMP-001=OK | IMP-002=OK | IMP-005=OK | IMP-010=OK | IMP-011=OK")

    print("\n" + "=" * 78)
    print(" TESTE CONTROLADO CONCLUIDO")
    print(" IMP-001: OK")
    print(" IMP-002: OK")
    print(" IMP-005: OK")
    print(" IMP-010: OK")
    print(" IMP-011: OK")
    print(" Nenhuma tabela local foi alterada.")
    print(f" Log: {LOG_FILE}")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
