"""
Teste controlado da cadeia IMP-001 -> IMP-002 -> IMP-005 no sandbox Qstione.

Executa SOMENTE um registro de IMP-005 e suas dependências reais:
    1. curso (IMP-001) referenciado pela disciplina;
    2. disciplina (IMP-002) referenciada pela oferta;
    3. oferta (IMP-005).

A finalidade é validar a cadeia de relacionamentos sem executar a carga completa.
Nenhuma tabela local é alterada.

Uso:
    python tests/test_qstione_imp005_sandbox.py
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


TABELA_CURSO = "imp_001_cursos"
TABELA_DISCIPLINA = "imp_002_disciplina"
TABELA_OFERTA = "imp_005_ofertas"
LOG_FILE = ROOT / "logs" / "test_qstione_imp005_sandbox.log"

LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger("test_qstione_imp005_sandbox")
logger.setLevel(logging.DEBUG)
logger.handlers.clear()
handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
logger.addHandler(handler)
logger.propagate = False


def ler_registro(tabela: str, transacao: str, order_by: str) -> dict:
    campos = CAMPOS_API[transacao]
    sql = (
        "SELECT TOP 1 "
        + ", ".join(f"[{campo}]" for campo in campos)
        + f" FROM dbo.[{tabela}] ORDER BY [{order_by}]"
    )
    with get_db_connection(database_name="qstione") as conn:
        row = conn.execute(sql).fetchone()

    if row is None:
        mensagem = f"Tabela {tabela} sem registros para {transacao}."
        logger.error(mensagem)
        raise RuntimeError(mensagem)

    return dict(zip(campos, row))


def ler_disciplina(codigo_disciplina: str) -> dict:
    campos = CAMPOS_API["IMP-002"]
    sql = (
        "SELECT TOP 1 "
        + ", ".join(f"[{campo}]" for campo in campos)
        + f" FROM dbo.[{TABELA_DISCIPLINA}] "
        "WHERE LTRIM(RTRIM([codigoDisciplina])) = ?"
        " ORDER BY [codigoDisciplina]"
    )
    with get_db_connection(database_name="qstione") as conn:
        row = conn.execute(sql, (codigo_disciplina,)).fetchone()

    if row is None:
        mensagem = (
            "RELACIONAMENTO INCONSISTENTE | IMP-005 -> IMP-002 | "
            f"codigoDisciplina={codigo_disciplina} | "
            f"registro não encontrado em {TABELA_DISCIPLINA}"
        )
        logger.error(mensagem)
        raise RuntimeError(mensagem)

    return dict(zip(campos, row))


def ler_curso(codigo_curso: str) -> dict:
    campos = CAMPOS_API["IMP-001"]
    sql = (
        "SELECT TOP 1 "
        + ", ".join(f"[{campo}]" for campo in campos)
        + f" FROM dbo.[{TABELA_CURSO}] "
        "WHERE LTRIM(RTRIM([codigoCurso])) = ?"
        " ORDER BY [codigoCurso]"
    )
    with get_db_connection(database_name="qstione") as conn:
        row = conn.execute(sql, (codigo_curso,)).fetchone()

    if row is None:
        mensagem = (
            "RELACIONAMENTO INCONSISTENTE | IMP-002 -> IMP-001 | "
            f"codigoCurso={codigo_curso} | "
            f"registro não encontrado em {TABELA_CURSO}"
        )
        logger.error(mensagem)
        raise RuntimeError(mensagem)

    return dict(zip(campos, row))


def validar_consistencia(oferta: dict, disciplina: dict, curso: dict) -> None:
    codigo_disciplina_oferta = str(oferta["codigoDisciplina"]).strip()
    codigo_disciplina = str(disciplina["codigoDisciplina"]).strip()
    codigo_curso = str(disciplina["codigoCurso"]).strip()
    codigo_curso_registro = str(curso["codigoCurso"]).strip()

    logger.info(
        "DEPENDÊNCIA IMP-005 -> IMP-002 | codigoOferta=%s | codigoDisciplina=%s",
        oferta["codigoOferta"],
        codigo_disciplina_oferta,
    )
    logger.info(
        "DEPENDÊNCIA IMP-002 -> IMP-001 | codigoDisciplina=%s | codigoCurso=%s",
        codigo_disciplina,
        codigo_curso,
    )

    if codigo_disciplina_oferta != codigo_disciplina:
        mensagem = (
            "RELACIONAMENTO INCONSISTENTE | IMP-005 -> IMP-002 | "
            f"oferta.codigoDisciplina={codigo_disciplina_oferta} != "
            f"disciplina.codigoDisciplina={codigo_disciplina}"
        )
        logger.error(mensagem)
        raise RuntimeError(mensagem)

    if codigo_curso != codigo_curso_registro:
        mensagem = (
            "RELACIONAMENTO INCONSISTENTE | IMP-002 -> IMP-001 | "
            f"disciplina.codigoCurso={codigo_curso} != "
            f"curso.codigoCurso={codigo_curso_registro}"
        )
        logger.error(mensagem)
        raise RuntimeError(mensagem)

    logger.info("CADEIA DE RELACIONAMENTOS LOCAL: OK")


def enviar_e_exibir(cliente: ClienteQstione, transacao: str, registro: dict) -> bool:
    print()
    print("=" * 78)
    print(f"TESTE {transacao} — 1 registro")
    print("=" * 78)
    print("Payload:")
    print(json.dumps(registro, ensure_ascii=False, indent=2, default=str))

    logger.info(
        "ENVIANDO %s | payload=%s",
        transacao,
        json.dumps(registro, ensure_ascii=False, default=str),
    )

    resultado = cliente.enviar(transacao, [registro])

    print("Retorno:")
    print(f"   HTTP:              {resultado.http_status}")
    print(f"   codigoStatus:      {resultado.codigo_status}")
    print(f"   idRequisicao:      {resultado.id_requisicao}")
    print(f"   modoExecucao:      {resultado.modo_execucao}")
    print(f"   quantidadeErros:   {resultado.quantidade_registros_erro}")

    logger.info(
        "RETORNO %s | HTTP=%s | codigoStatus=%s | idRequisicao=%s | modo=%s | erros=%s",
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
        logger.info(
            "CORPO RESPOSTA %s | %s",
            transacao,
            json.dumps(resultado.corpo_bruto, ensure_ascii=False, default=str),
        )

    if resultado.assincrono:
        mensagem = f"{transacao} retornou modoExecucao=A; teste interrompido."
        logger.error(mensagem)
        print(f"\n❌ {mensagem}")
        return False

    if not resultado.sucesso:
        print(f"\n❌ {transacao} rejeitada pela API.")
        logger.error("%s rejeitada pela API.", transacao)
        for erro in resultado.erros:
            detalhe = (
                "ERRO API | "
                f"transacao={transacao} | "
                f"registro={erro.get('numeroRegistro')} | "
                f"excecao={erro.get('nomeExcecao')} | "
                f"detalhes={erro.get('detalhesFalha')}"
            )
            print(f"   {detalhe}")
            logger.error(detalhe)
        return False

    print(f"✅ {transacao} aceita com sucesso.")
    logger.info("%s aceita com sucesso.", transacao)
    return True


def main() -> int:
    logger.info("=" * 90)
    logger.info("INÍCIO TESTE CONTROLADO IMP-005")

    print("=" * 78)
    print(" TESTE CONTROLADO — CADEIA IMP-001 + IMP-002 + IMP-005")
    print(" Protocolo: 1.2.10 | Dicionário: 1.15.0")
    print(" Escopo: 1 oferta + dependências reais")
    print(" Nenhuma tabela local será alterada.")
    print("=" * 78)

    validar_configuracao_qstione()
    print(f"Endpoint: {QSTIONE_BASE_URL}")
    print(f"SSL verify: {QSTIONE_SSL_VERIFY}")
    print(f"Timeout: {QSTIONE_TIMEOUT}s")
    print("Token: configurado (não exibido)")
    print(f"Log: {LOG_FILE}")

    try:
        oferta = ler_registro(TABELA_OFERTA, "IMP-005", "codigoOferta")
        codigo_disciplina = str(oferta["codigoDisciplina"]).strip()

        print(
            f"\nDependência detectada: IMP-005.codigoDisciplina = {codigo_disciplina}"
        )
        logger.info(
            "OFERTA SELECIONADA | codigoOferta=%s | codigoDisciplina=%s",
            oferta["codigoOferta"],
            codigo_disciplina,
        )

        disciplina = ler_disciplina(codigo_disciplina)
        codigo_curso = str(disciplina["codigoCurso"]).strip()
        curso = ler_curso(codigo_curso)
        validar_consistencia(oferta, disciplina, curso)

    except Exception as exc:
        logger.exception("Falha na resolução da cadeia de dependências.")
        print(f"\n❌ Falha na resolução das dependências: {exc}")
        print(f"Consulte o log: {LOG_FILE}")
        return 1

    print(f"Dependência detectada: IMP-002.codigoCurso = {codigo_curso}")
    print("Ordem de envio: IMP-001 → IMP-002 → IMP-005")

    cliente = ClienteQstione(
        url=QSTIONE_BASE_URL,
        token=QSTIONE_TOKEN or "",
        timeout=QSTIONE_TIMEOUT,
        ssl_verify=QSTIONE_SSL_VERIFY,
    )

    try:
        if not enviar_e_exibir(cliente, "IMP-001", curso):
            return 1
        if not enviar_e_exibir(cliente, "IMP-002", disciplina):
            return 1
        if not enviar_e_exibir(cliente, "IMP-005", oferta):
            return 1
    finally:
        cliente.close()

    logger.info("TESTE CONTROLADO IMP-005 CONCLUÍDO COM SUCESSO")

    print()
    print("=" * 78)
    print(" TESTE CONTROLADO CONCLUÍDO")
    print(" IMP-001: OK")
    print(" IMP-002: OK")
    print(" IMP-005: OK")
    print(" Nenhuma outra transação foi executada.")
    print(f" Log: {LOG_FILE}")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
