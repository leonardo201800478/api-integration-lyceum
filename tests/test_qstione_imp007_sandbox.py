"""Teste controlado do IMP-007 no Sandbox Qstione.

Cadeia validada:
    IMP-001 -> IMP-006 -> IMP-007

Seleciona uma relacao real de imp_007_usuarios_cursos somente quando as
respectivas dependencias locais tambem existem. Nenhuma tabela local e alterada.

Uso:
    python tests/test_qstione_imp007_sandbox.py
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

LOG_FILE = ROOT / "logs" / "test_qstione_imp007_sandbox.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger("test_qstione_imp007_sandbox")
logger.setLevel(logging.DEBUG)
logger.handlers.clear()
handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
logger.addHandler(handler)
logger.propagate = False


def buscar_registros() -> tuple[dict, dict, dict]:
    """Seleciona uma relacao com curso e usuario existentes localmente."""
    sql = """
        SELECT TOP 1
            v.[codigoCurso],
            v.[emailUsuario],
            v.[papelUsuario],
            c.[nomeCurso],
            c.[quantPeriodos],
            c.[codigoUnidadeOrganizacional],
            u.[matriculaUsuario],
            u.[codigoUsuario],
            u.[emailUsuario],
            u.[nomeUsuario]
        FROM dbo.[imp_007_usuarios_cursos] v
        INNER JOIN dbo.[imp_001_cursos] c
            ON LTRIM(RTRIM(CAST(c.[codigoCurso] AS NVARCHAR(100)))) =
               LTRIM(RTRIM(CAST(v.[codigoCurso] AS NVARCHAR(100))))
        INNER JOIN dbo.[imp_006_usuarios] u
            ON LOWER(LTRIM(RTRIM(u.[emailUsuario]))) =
               LOWER(LTRIM(RTRIM(v.[emailUsuario])))
        WHERE v.[codigoCurso] IS NOT NULL
          AND LTRIM(RTRIM(CAST(v.[codigoCurso] AS NVARCHAR(100)))) <> ''
          AND v.[emailUsuario] IS NOT NULL
          AND LTRIM(RTRIM(v.[emailUsuario])) <> ''
          AND v.[papelUsuario] IS NOT NULL
          AND LTRIM(RTRIM(v.[papelUsuario])) <> ''
        ORDER BY v.[codigoCurso], v.[emailUsuario]
    """

    with get_db_connection(database_name="qstione") as conn:
        row = conn.execute(sql).fetchone()

    if row is None:
        raise RuntimeError(
            "Nao existe registro IMP-007 com dependencias locais completas "
            "em IMP-001 e IMP-006."
        )

    vinculo = {
        "codigoCurso": row[0],
        "emailUsuario": row[1],
        "papelUsuario": row[2],
    }
    curso = {
        "codigoCurso": row[0],
        "nomeCurso": row[3],
        "quantPeriodos": row[4],
        "codigoUnidadeOrganizacional": row[5],
    }
    usuario = {
        "matriculaUsuario": row[6],
        "codigoUsuario": row[7],
        "emailUsuario": row[8],
        "nomeUsuario": row[9],
    }

    logger.info("DEPENDENCIA IMP-001 | %s", curso)
    logger.info("DEPENDENCIA IMP-006 | %s", usuario)
    logger.info("REGISTRO IMP-007 | %s", vinculo)

    return curso, usuario, vinculo


def validar(curso: dict, usuario: dict, vinculo: dict) -> None:
    if str(curso["codigoCurso"]).strip() != str(vinculo["codigoCurso"]).strip():
        raise RuntimeError("Inconsistencia: IMP-007.codigoCurso difere do IMP-001.")

    if str(usuario["emailUsuario"]).strip().lower() != str(vinculo["emailUsuario"]).strip().lower():
        raise RuntimeError("Inconsistencia: IMP-007.emailUsuario difere do IMP-006.")

    if not str(vinculo["codigoCurso"]).strip():
        raise RuntimeError("IMP-007.codigoCurso esta vazio.")
    if not str(vinculo["emailUsuario"]).strip() or "@" not in str(vinculo["emailUsuario"]):
        raise RuntimeError("IMP-007.emailUsuario invalido.")
    if str(vinculo["papelUsuario"]).strip() not in {"G", "C", "A", "P"}:
        raise RuntimeError(
            f"IMP-007.papelUsuario invalido: {vinculo['papelUsuario']!r}."
        )


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
        logger.error("%s retornou modoExecucao=A.", transacao)
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
        logger.error("%s rejeitada | erros=%s", transacao, resultado.erros)
        return False

    print(f"✅ {transacao} aceita com sucesso.")
    return True


def main() -> int:
    print("=" * 78)
    print(" TESTE CONTROLADO — CADEIA IMP-001 + IMP-006 + IMP-007")
    print(" Protocolo: 1.2.10 | Dicionario: 1.15.0")
    print(" Escopo: 1 curso + 1 usuario + 1 vinculo usuario/curso")
    print(" Nenhuma tabela local sera alterada.")
    print("=" * 78)

    try:
        validar_configuracao_qstione()
        print(f"Endpoint: {QSTIONE_BASE_URL}")
        print(f"SSL verify: {QSTIONE_SSL_VERIFY}")
        print(f"Timeout: {QSTIONE_TIMEOUT}s")
        print("Token: configurado (nao exibido)")
        print(f"Log: {LOG_FILE}")

        curso, usuario, vinculo = buscar_registros()
        validar(curso, usuario, vinculo)

        print(f"\nDependencia detectada: IMP-007.codigoCurso = {vinculo['codigoCurso']}")
        print(f"Dependencia detectada: IMP-007.emailUsuario = {vinculo['emailUsuario']}")
        print(f"Papel: {vinculo['papelUsuario']}")
        print("Ordem de envio: IMP-001 → IMP-006 → IMP-007")

    except Exception as exc:
        logger.exception("Falha na preparacao do teste IMP-007.")
        print(f"\n❌ Falha na validacao local: {exc}")
        print(f"Consulte o log: {LOG_FILE}")
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
        if not enviar(cliente, "IMP-006", usuario):
            return 1
        if not enviar(cliente, "IMP-007", vinculo):
            return 1
    finally:
        cliente.close()

    print("\n" + "=" * 78)
    print(" TESTE CONTROLADO CONCLUIDO")
    print(" IMP-001: OK")
    print(" IMP-006: OK")
    print(" IMP-007: OK")
    print(" Nenhuma tabela local foi alterada.")
    print(f" Log: {LOG_FILE}")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
