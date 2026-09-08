"""Teste controlado do IMP-008 no Sandbox Qstione.

Cadeia validada:
    IMP-001 -> IMP-002 -> IMP-006 -> IMP-008

O teste seleciona exatamente um registro real da tabela
imp_008_usuarios_disciplinas e resolve as dependencias reais antes do envio.
Nenhuma tabela local e alterada.

Uso:
    python tests/test_qstione_imp008_sandbox.py
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

LOG_FILE = ROOT / "logs" / "test_qstione_imp008_sandbox.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger("test_qstione_imp008_sandbox")
logger.setLevel(logging.DEBUG)
logger.handlers.clear()
handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
logger.addHandler(handler)
logger.propagate = False


def selecionar_registro() -> dict:
    sql = """
        SELECT TOP 1
            [codigoDisciplina],
            [emailUsuario]
        FROM dbo.[imp_008_usuarios_disciplinas]
        ORDER BY [codigoDisciplina], [emailUsuario]
    """
    with get_db_connection(database_name="qstione") as conn:
        row = conn.execute(sql).fetchone()
    if row is None:
        raise RuntimeError("A tabela imp_008_usuarios_disciplinas nao possui registros.")
    registro = {"codigoDisciplina": row[0], "emailUsuario": row[1]}
    logger.info("REGISTRO IMP-008 SELECIONADO | %s", registro)
    return registro


def buscar_disciplina(codigo_disciplina: str) -> dict:
    sql = """
        SELECT TOP 1
            [codigoDisciplina],
            [nomeDisciplina],
            [codigoCurso],
            [periodo]
        FROM dbo.[imp_002_disciplinas]
        WHERE [codigoDisciplina] = ?
    """
    with get_db_connection(database_name="qstione") as conn:
        row = conn.execute(sql, (codigo_disciplina,)).fetchone()
    if row is None:
        raise RuntimeError(
            f"Dependencia IMP-002 nao encontrada para codigoDisciplina={codigo_disciplina}."
        )
    return {
        "codigoDisciplina": row[0],
        "nomeDisciplina": row[1],
        "codigoCurso": row[2],
        "periodo": row[3],
    }


def buscar_curso(codigo_curso: str) -> dict:
    sql = """
        SELECT TOP 1
            [codigoCurso],
            [nomeCurso],
            [quantPeriodos],
            [codigoUnidadeOrganizacional]
        FROM dbo.[imp_001_cursos]
        WHERE [codigoCurso] = ?
    """
    with get_db_connection(database_name="qstione") as conn:
        row = conn.execute(sql, (codigo_curso,)).fetchone()
    if row is None:
        raise RuntimeError(
            f"Dependencia IMP-001 nao encontrada para codigoCurso={codigo_curso}."
        )
    return {
        "codigoCurso": row[0],
        "nomeCurso": row[1],
        "quantPeriodos": row[2],
        "codigoUnidadeOrganizacional": row[3],
    }


def buscar_usuario(email: str) -> dict:
    sql = """
        SELECT TOP 1
            [matriculaUsuario],
            [codigoUsuario],
            [emailUsuario],
            [nomeUsuario]
        FROM dbo.[imp_006_usuarios]
        WHERE LOWER(LTRIM(RTRIM([emailUsuario]))) = LOWER(LTRIM(RTRIM(?)))
    """
    with get_db_connection(database_name="qstione") as conn:
        row = conn.execute(sql, (email,)).fetchone()
    if row is None:
        raise RuntimeError(
            f"Dependencia IMP-006 nao encontrada para emailUsuario={email}."
        )
    return {
        "matriculaUsuario": row[0],
        "codigoUsuario": row[1],
        "emailUsuario": row[2],
        "nomeUsuario": row[3],
    }


def validar_dependencias(registro: dict, disciplina: dict, curso: dict, usuario: dict) -> None:
    if str(registro["codigoDisciplina"]).strip() != str(disciplina["codigoDisciplina"]).strip():
        raise RuntimeError("Inconsistencia entre IMP-008 e IMP-002: codigoDisciplina.")

    if str(disciplina["codigoCurso"]).strip() != str(curso["codigoCurso"]).strip():
        raise RuntimeError("Inconsistencia entre IMP-002 e IMP-001: codigoCurso.")

    if str(registro["emailUsuario"]).strip().lower() != str(usuario["emailUsuario"]).strip().lower():
        raise RuntimeError("Inconsistencia entre IMP-008 e IMP-006: emailUsuario.")

    if not str(registro["codigoDisciplina"]).strip():
        raise RuntimeError("IMP-008 possui codigoDisciplina vazio.")
    if not str(registro["emailUsuario"]).strip() or "@" not in str(registro["emailUsuario"]):
        raise RuntimeError("IMP-008 possui emailUsuario invalido.")

    logger.info(
        "DEPENDENCIAS OK | disciplina=%s | curso=%s | usuario=%s",
        registro["codigoDisciplina"],
        curso["codigoCurso"],
        usuario["emailUsuario"],
    )


def enviar(cliente: ClienteQstione, transacao: str, registro: dict) -> bool:
    print()
    print(f"{transacao} payload:")
    print(json.dumps(registro, ensure_ascii=False, indent=2, default=str))

    resultado = cliente.enviar(transacao, [registro])

    print("HTTP:", resultado.http_status)
    print("codigoStatus:", resultado.codigo_status)
    print("idRequisicao:", resultado.id_requisicao)
    print("modoExecucao:", resultado.modo_execucao)
    print("quantidadeErros:", resultado.quantidade_registros_erro)

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
        logger.error("%s retornou modoExecucao=A; teste interrompido.", transacao)
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
            logger.error("ERRO API %s | %s", transacao, erro)
        return False

    print(f"✅ {transacao} aceita com sucesso.")
    return True


def main() -> int:
    print("=" * 78)
    print(" TESTE CONTROLADO — CADEIA IMP-001 + IMP-002 + IMP-006 + IMP-008")
    print(" Protocolo: 1.2.10 | Dicionario: 1.15.0")
    print(" Escopo: 1 disciplina + dependencias reais")
    print(" Nenhuma tabela local sera alterada.")
    print("=" * 78)

    try:
        validar_configuracao_qstione()
        print(f"Endpoint: {QSTIONE_BASE_URL}")
        print(f"SSL verify: {QSTIONE_SSL_VERIFY}")
        print(f"Timeout: {QSTIONE_TIMEOUT}s")
        print("Token: configurado (nao exibido)")
        print(f"Log: {LOG_FILE}")

        registro = selecionar_registro()
        disciplina = buscar_disciplina(str(registro["codigoDisciplina"]).strip())
        curso = buscar_curso(str(disciplina["codigoCurso"]).strip())
        usuario = buscar_usuario(str(registro["emailUsuario"]).strip())
        validar_dependencias(registro, disciplina, curso, usuario)

        print(f"\nDependencia detectada: IMP-008.codigoDisciplina = {registro['codigoDisciplina']}")
        print(f"Dependencia detectada: IMP-002.codigoCurso = {disciplina['codigoCurso']}")
        print(f"Dependencia detectada: IMP-008.emailUsuario = {registro['emailUsuario']}")
        print("Ordem de envio: IMP-001 → IMP-002 → IMP-006 → IMP-008")

    except Exception as exc:
        logger.exception("Falha na preparacao do teste IMP-008.")
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
        if not enviar(cliente, "IMP-002", disciplina):
            return 1
        if not enviar(cliente, "IMP-006", usuario):
            return 1
        if not enviar(cliente, "IMP-008", registro):
            return 1
    finally:
        cliente.close()

    print()
    print("=" * 78)
    print(" TESTE CONTROLADO CONCLUIDO")
    print(" IMP-001: OK")
    print(" IMP-002: OK")
    print(" IMP-006: OK")
    print(" IMP-008: OK")
    print(" Nenhuma tabela local foi alterada.")
    print(f" Log: {LOG_FILE}")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
