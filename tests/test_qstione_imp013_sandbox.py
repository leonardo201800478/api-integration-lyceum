"""Teste controlado do IMP-013 no Sandbox Qstione.

Cadeia validada:
    IMP-001 -> IMP-002 -> IMP-005 -> IMP-013

Seleciona uma unidade de avaliacao real somente quando curso e disciplina
correspondentes existem localmente. Nenhuma tabela local e alterada.
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

LOG_FILE = ROOT / "logs" / "test_qstione_imp013_sandbox.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger("test_qstione_imp013_sandbox")
logger.handlers.clear()
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
logger.addHandler(handler)
logger.propagate = False


def buscar_cadeia() -> tuple[dict, dict, dict, dict]:
    """Seleciona um IMP-013 com curso e disciplina correspondentes."""
    sql = """
        SELECT TOP 1
            ua.[codigoUnidade],
            ua.[nomeUnidade],
            ua.[codigoCurso],
            ua.[codigoDisciplina],
            ua.[ordemExibicao],
            ua.[codigoAgrupamento],

            d.[codigoDisciplina],
            d.[nomeDisciplina],
            d.[codigoCurso],
            d.[periodo],

            c.[codigoCurso],
            c.[nomeCurso],
            c.[quantPeriodos],
            c.[codigoUnidadeOrganizacional],

            o.[codigoOferta],
            o.[nomeOferta],
            o.[semestreOferta],
            o.[codigoTipoOferta],
            o.[codigoOfertaOrigem],
            o.[turno],
            o.[codigoIdentificacaoAVA]
        FROM dbo.[imp_013_unidades_avaliacao] ua
        INNER JOIN dbo.[imp_002_disciplina] d
            ON LTRIM(RTRIM(CAST(d.[codigoDisciplina] AS NVARCHAR(100)))) =
               LTRIM(RTRIM(CAST(ua.[codigoDisciplina] AS NVARCHAR(100))))
           AND LTRIM(RTRIM(CAST(d.[codigoCurso] AS NVARCHAR(100)))) =
               LTRIM(RTRIM(CAST(ua.[codigoCurso] AS NVARCHAR(100))))
        INNER JOIN dbo.[imp_001_cursos] c
            ON LTRIM(RTRIM(CAST(c.[codigoCurso] AS NVARCHAR(100)))) =
               LTRIM(RTRIM(CAST(ua.[codigoCurso] AS NVARCHAR(100))))
        LEFT JOIN dbo.[imp_005_ofertas] o
            ON LTRIM(RTRIM(CAST(o.[codigoDisciplina] AS NVARCHAR(100)))) =
               LTRIM(RTRIM(CAST(ua.[codigoDisciplina] AS NVARCHAR(100))))
           AND LTRIM(RTRIM(CAST(o.[semestreOferta] AS NVARCHAR(50)))) = '2026.2'
        WHERE ua.[codigoUnidade] IS NOT NULL
          AND LTRIM(RTRIM(CAST(ua.[codigoUnidade] AS NVARCHAR(200)))) <> ''
          AND ua.[nomeUnidade] IS NOT NULL
          AND LTRIM(RTRIM(ua.[nomeUnidade])) <> ''
          AND ua.[codigoCurso] IS NOT NULL
          AND LTRIM(RTRIM(CAST(ua.[codigoCurso] AS NVARCHAR(100)))) <> ''
          AND ua.[codigoDisciplina] IS NOT NULL
          AND LTRIM(RTRIM(CAST(ua.[codigoDisciplina] AS NVARCHAR(100)))) <> ''
        ORDER BY ua.[codigoCurso], ua.[codigoDisciplina], ua.[codigoUnidade]
    """

    with get_db_connection(database_name="qstione") as conn:
        row = conn.execute(sql).fetchone()

    if row is None:
        raise RuntimeError(
            "Nao existe registro IMP-013 com dependencias completas em "
            "IMP-001 e IMP-002."
        )

    unidade = {
        "codigoUnidade": row[0],
        "nomeUnidade": row[1],
        "codigoCurso": row[2],
        "codigoDisciplina": row[3],
        "ordemExibicao": row[4],
        "codigoAgrupamento": row[5],
    }
    disciplina = {
        "codigoDisciplina": row[6],
        "nomeDisciplina": row[7],
        "codigoCurso": row[8],
        "periodo": row[9],
    }
    curso = {
        "codigoCurso": row[10],
        "nomeCurso": row[11],
        "quantPeriodos": row[12],
        "codigoUnidadeOrganizacional": row[13],
    }

    oferta = None
    if row[14] is not None:
        oferta = {
            "codigoOferta": row[14],
            "nomeOferta": row[15],
            "codigoDisciplina": unidade["codigoDisciplina"],
            "semestreOferta": row[16],
            "codigoTipoOferta": row[17],
            "codigoOfertaOrigem": row[18],
            "turno": row[19],
            "codigoIdentificacaoAVA": row[20],
        }

    validar_consistencia(curso, disciplina, unidade)
    return curso, disciplina, oferta, unidade


def validar_consistencia(curso: dict, disciplina: dict, unidade: dict) -> None:
    def igual(a: object, b: object) -> bool:
        return str(a).strip().lower() == str(b).strip().lower()

    if not igual(unidade["codigoCurso"], curso["codigoCurso"]):
        raise RuntimeError("Inconsistencia: IMP-013.codigoCurso difere do IMP-001.")
    if not igual(unidade["codigoDisciplina"], disciplina["codigoDisciplina"]):
        raise RuntimeError("Inconsistencia: IMP-013.codigoDisciplina difere do IMP-002.")
    if not str(unidade["codigoUnidade"]).strip():
        raise RuntimeError("IMP-013.codigoUnidade esta vazio.")
    if not str(unidade["nomeUnidade"]).strip():
        raise RuntimeError("IMP-013.nomeUnidade esta vazio.")


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
                % (erro.get("numeroRegistro"), erro.get("nomeExcecao"), erro.get("detalhesFalha"))
            )
        return False

    print(f"✅ {transacao} aceita com sucesso.")
    return True


def main() -> int:
    print("=" * 78)
    print(" TESTE CONTROLADO — CADEIA IMP-001 + IMP-002 + IMP-005 + IMP-013")
    print(" Protocolo: 1.2.10 | Dicionario: 1.15.0")
    print(" Escopo: 1 curso + 1 disciplina + 1 oferta + 1 unidade de avaliacao")
    print(" Nenhuma tabela local sera alterada.")
    print("=" * 78)

    try:
        validar_configuracao_qstione()
        print(f"Endpoint: {QSTIONE_BASE_URL}")
        print(f"SSL verify: {QSTIONE_SSL_VERIFY}")
        print(f"Timeout: {QSTIONE_TIMEOUT}s")
        print("Token: configurado (nao exibido)")
        print(f"Log: {LOG_FILE}")

        curso, disciplina, oferta, unidade = buscar_cadeia()
        print(f"\nDependencia detectada: IMP-013.codigoCurso = {unidade['codigoCurso']}")
        print(f"Dependencia detectada: IMP-013.codigoDisciplina = {unidade['codigoDisciplina']}")
        print(f"Dependencia detectada: IMP-013.codigoUnidade = {unidade['codigoUnidade']}")
        print("Ordem de envio: IMP-001 → IMP-002 → IMP-005 → IMP-013")

    except Exception as exc:
        logger.exception("Falha na preparacao do teste IMP-013: %s", exc)
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
        ):
            if not enviar(cliente, transacao, registro):
                return 1

        # IMP-005 e uma dependencia importante da unidade de avaliacao quando
        # houver oferta correspondente no banco local. Caso nao exista, o
        # teste ainda pode validar IMP-013 diretamente apos IMP-001/002.
        if oferta is not None:
            if not enviar(cliente, "IMP-005", oferta):
                return 1
        else:
            print("\nIMP-005: nenhuma oferta 2026.2 correspondente encontrada localmente;")
            print("         prosseguindo com IMP-013, pois IMP-013 depende de curso/disciplina.")

        if not enviar(cliente, "IMP-013", unidade):
            return 1
    finally:
        cliente.close()

    logger.info("TESTE CONCLUIDO | IMP-001=OK | IMP-002=OK | IMP-005=%s | IMP-013=OK", "OK" if oferta else "NAO TESTADO")

    print("\n" + "=" * 78)
    print(" TESTE CONTROLADO CONCLUIDO")
    print(" IMP-001: OK")
    print(" IMP-002: OK")
    print(f" IMP-005: {'OK' if oferta else 'NAO TESTADO'}")
    print(" IMP-013: OK")
    print(" Nenhuma tabela local foi alterada.")
    print(f" Log: {LOG_FILE}")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
