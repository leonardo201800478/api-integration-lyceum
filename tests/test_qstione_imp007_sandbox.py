"""Teste controlado do IMP-007 no Sandbox Qstione.

Valida a cadeia real de dependencias:
    IMP-001 (curso) -> IMP-006 (usuario) -> IMP-007 (usuario x curso)

O teste seleciona exatamente um vinculo existente em imp_007_usuarios_cursos,
localiza as dependencias correspondentes nas tabelas locais e envia somente
esses tres registros, nesta ordem. Nenhuma tabela local e alterada.

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
from qstione.api.cliente import ClienteQstione, CAMPOS_API
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
    """Seleciona um vinculo real e suas dependencias locais."""
    with get_db_connection(database_name="qstione") as conn:
        vinculo_row = conn.execute(
            """
            SELECT TOP 1 codigoCurso, emailUsuario, papelUsuario
            FROM dbo.imp_007_usuarios_cursos
            ORDER BY codigoCurso, emailUsuario
            """
        ).fetchone()

        if vinculo_row is None:
            raise RuntimeError("A tabela imp_007_usuarios_cursos nao possui registros.")

        codigo_curso, email_usuario, papel_usuario = vinculo_row

        curso_row = conn.execute(
            """
            SELECT TOP 1 codigoCurso, nomeCurso, quantPeriodos, codigoUnidadeOrganizacional
            FROM dbo.imp_001_cursos
            WHERE codigoCurso = ?
            """,
            (codigo_curso,),
        ).fetchone()

        if curso_row is None:
            raise RuntimeError(
                f"Dependencia IMP-001 nao encontrada para codigoCurso={codigo_curso!r}."
            )

        usuario_row = conn.execute(
            """
            SELECT TOP 1 matriculaUsuario, codigoUsuario, emailUsuario, nomeUsuario
            FROM dbo.imp_006_usuarios
            WHERE emailUsuario = ?
            """,
            (email_usuario,),
        ).fetchone()

        if usuario_row is None:
            raise RuntimeError(
                f"Dependencia IMP-006 nao encontrada para emailUsuario={email_usuario!r}."
            )

    curso = dict(zip(CAMPOS_API["IMP-001"], curso_row))
    usuario = dict(zip(CAMPOS_API["IMP-006"], usuario_row))
    vinculo = dict(zip(CAMPOS_API["IMP-007"], vinculo_row))

    logger.info("DEPENDENCIA IMP-001 | %s", curso)
    logger.info("DEPENDENCIA IMP-006 | %s", usuario)
    logger.info("REGISTRO IMP-007 | %s", vinculo)

    return curso, usuario, vinculo


def validar(curso: dict, usuario: dict, vinculo: dict) -> None:
    if str(curso["codigoCurso"]).strip() != str(vinculo["codigoCurso"]).strip():
        raise RuntimeError("Inconsistencia: IMP-007.codigoCurso difere do IMP-001.")

    if str(usuario["emailUsuario"]).strip().lower() != str(vinculo["emailUsuario"]).strip().lower():
        raise RuntimeError("Inconsistencia: IMP-007.emailUsuario difere do IMP-006.")

    if not str(vinculo["papelUsuario"]).strip():
        raise RuntimeError("IMP-007.papelUsuario esta vazio.")

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
