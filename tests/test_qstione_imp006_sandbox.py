"""Teste controlado do IMP-006 no Sandbox Qstione.

O IMP-006 cadastra usuarios/docentes e nao possui dependencia de outra
transacao Qstione anterior. A populacao, entretanto, vem da cadeia real
LY_TURMA_DOCENTE -> LY_TURMA -> LY_DOCENTE definida pelo importador.

Este teste le SOMENTE a tabela local imp_006_usuarios, valida os campos
obrigatorios e envia exatamente um registro ao Sandbox. Nenhuma tabela
local e alterada.

Uso:
    python tests/test_qstione_imp006_sandbox.py
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

TABELA = "imp_006_usuarios"
TRANSACAO = "IMP-006"
LOG_FILE = ROOT / "logs" / "test_qstione_imp006_sandbox.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger("test_qstione_imp006_sandbox")
logger.setLevel(logging.DEBUG)
logger.handlers.clear()
handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
logger.addHandler(handler)
logger.propagate = False


def ler_registro() -> dict:
    campos = CAMPOS_API[TRANSACAO]
    sql = (
        "SELECT TOP 1 "
        + ", ".join(f"[{campo}]" for campo in campos)
        + f" FROM dbo.[{TABELA}] ORDER BY [matriculaUsuario]"
    )
    with get_db_connection(database_name="qstione") as conn:
        row = conn.execute(sql).fetchone()
    if row is None:
        mensagem = f"A tabela {TABELA} nao possui registros."
        logger.error(mensagem)
        raise RuntimeError(mensagem)
    registro = dict(zip(campos, row))
    logger.info("REGISTRO SELECIONADO | %s", registro)
    return registro


def validar_registro(registro: dict) -> None:
    obrigatorios = ("matriculaUsuario", "emailUsuario", "nomeUsuario")
    for campo in obrigatorios:
        valor = registro.get(campo)
        if valor is None or not str(valor).strip():
            mensagem = (
                f"DADO INVALIDO | IMP-006 | matriculaUsuario="
                f"{registro.get('matriculaUsuario')} | campo={campo} | valor={valor!r}"
            )
            logger.error(mensagem)
            raise RuntimeError(mensagem)

    email = str(registro["emailUsuario"]).strip()
    if "@" not in email:
        mensagem = (
            f"DADO INVALIDO | IMP-006 | matriculaUsuario={registro['matriculaUsuario']} | "
            f"emailUsuario={email!r} | formato invalido"
        )
        logger.error(mensagem)
        raise RuntimeError(mensagem)

    codigo = registro.get("codigoUsuario")
    if codigo is not None and not str(codigo).strip():
        mensagem = (
            f"DADO INCONSISTENTE | IMP-006 | matriculaUsuario={registro['matriculaUsuario']} | "
            "codigoUsuario vazio"
        )
        logger.error(mensagem)
        raise RuntimeError(mensagem)

    logger.info(
        "VALIDACAO LOCAL OK | matriculaUsuario=%s | codigoUsuario=%s | emailUsuario=%s",
        registro["matriculaUsuario"],
        registro.get("codigoUsuario"),
        registro["emailUsuario"],
    )


def enviar(cliente: ClienteQstione, registro: dict) -> bool:
    print()
    print("=" * 78)
    print("TESTE IMP-006 — 1 registro")
    print("=" * 78)
    print("Payload:")
    print(json.dumps(registro, ensure_ascii=False, indent=2, default=str))

    logger.info(
        "ENVIANDO IMP-006 | payload=%s",
        json.dumps(registro, ensure_ascii=False, default=str),
    )

    resultado = cliente.enviar(TRANSACAO, [registro])

    print("Retorno:")
    print(f"   HTTP:              {resultado.http_status}")
    print(f"   codigoStatus:      {resultado.codigo_status}")
    print(f"   idRequisicao:      {resultado.id_requisicao}")
    print(f"   modoExecucao:      {resultado.modo_execucao}")
    print(f"   quantidadeErros:   {resultado.quantidade_registros_erro}")

    logger.info(
        "RETORNO IMP-006 | HTTP=%s | status=%s | id=%s | modo=%s | erros=%s",
        resultado.http_status,
        resultado.codigo_status,
        resultado.id_requisicao,
        resultado.modo_execucao,
        resultado.quantidade_registros_erro,
    )

    if resultado.corpo_bruto not in (None, [], {}):
        print("corpoResposta:")
        print(json.dumps(resultado.corpo_bruto, ensure_ascii=False, indent=2, default=str))
        logger.info("CORPO RESPOSTA IMP-006 | %s", resultado.corpo_bruto)

    if resultado.assincrono:
        logger.error("IMP-006 retornou modoExecucao=A; teste interrompido.")
        print("\n❌ IMP-006 retornou modoExecucao=A; teste interrompido.")
        return False

    if not resultado.sucesso:
        print("\n❌ IMP-006 rejeitada pela API.")
        for erro in resultado.erros:
            detalhe = (
                "ERRO API | transacao=IMP-006 | "
                f"registro={erro.get('numeroRegistro')} | "
                f"excecao={erro.get('nomeExcecao')} | "
                f"detalhes={erro.get('detalhesFalha')}"
            )
            print(f"   {detalhe}")
            logger.error(detalhe)
        return False

    print("✅ IMP-006 aceita com sucesso.")
    logger.info("IMP-006 aceita com sucesso.")
    return True


def main() -> int:
    print("=" * 78)
    print(" TESTE CONTROLADO — IMP-006")
    print(" Protocolo: 1.2.10 | Dicionario: 1.15.0")
    print(" Escopo: 1 usuario real da tabela imp_006_usuarios")
    print(" Nenhuma tabela local sera alterada.")
    print("=" * 78)

    try:
        validar_configuracao_qstione()
        print(f"Endpoint: {QSTIONE_BASE_URL}")
        print(f"SSL verify: {QSTIONE_SSL_VERIFY}")
        print(f"Timeout: {QSTIONE_TIMEOUT}s")
        print("Token: configurado (nao exibido)")
        print(f"Log: {LOG_FILE}")

        registro = ler_registro()
        validar_registro(registro)
    except Exception as exc:
        logger.exception("Falha antes do envio do IMP-006.")
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
        if not enviar(cliente, registro):
            return 1
    finally:
        cliente.close()

    print()
    print("=" * 78)
    print(" TESTE CONTROLADO CONCLUIDO")
    print(" IMP-006: OK")
    print(" Nenhuma outra transacao foi executada.")
    print(f" Log: {LOG_FILE}")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
