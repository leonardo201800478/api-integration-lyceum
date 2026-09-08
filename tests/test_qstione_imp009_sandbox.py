"""Teste controlado do IMP-009 no Sandbox Qstione.

Cadeia validada:
    IMP-001 -> IMP-002 -> IMP-005 -> IMP-006 -> IMP-009

Seleciona um vinculo real de imp_009_professores_ofertas e resolve toda a
cadeia local. Isso evita testar uma oferta cuja disciplina ainda nao exista
na plataforma. Nenhuma tabela local e alterada.
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

LOG_FILE = ROOT / "logs" / "test_qstione_imp009_sandbox.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
logger = logging.getLogger("test_qstione_imp009_sandbox")
logger.setLevel(logging.DEBUG)
logger.handlers.clear()
handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
logger.addHandler(handler)
logger.propagate = False


def buscar_registros() -> tuple[dict, dict, dict, dict, dict]:
    """Seleciona uma cadeia IMP-009 com todas as dependencias locais."""
    with get_db_connection(database_name="qstione") as conn:
        row = conn.execute("""
            SELECT TOP 1
                po.codigoOferta,
                po.emailProfessor,
                o.codigoOferta,
                o.nomeOferta,
                o.codigoDisciplina,
                o.semestreOferta,
                o.codigoTipoOferta,
                o.codigoOfertaOrigem,
                o.turno,
                o.codigoIdentificacaoAVA,
                d.codigoDisciplina,
                d.nomeDisciplina,
                d.codigoCurso,
                d.periodo,
                c.codigoCurso,
                c.nomeCurso,
                c.quantPeriodos,
                c.codigoUnidadeOrganizacional,
                u.matriculaUsuario,
                u.codigoUsuario,
                u.emailUsuario,
                u.nomeUsuario
            FROM dbo.imp_009_professores_ofertas po
            INNER JOIN dbo.imp_005_ofertas o
                ON o.codigoOferta = po.codigoOferta
            INNER JOIN dbo.imp_002_disciplina d
                ON d.codigoDisciplina = o.codigoDisciplina
            INNER JOIN dbo.imp_001_cursos c
                ON c.codigoCurso = d.codigoCurso
            INNER JOIN dbo.imp_006_usuarios u
                ON LOWER(LTRIM(RTRIM(u.emailUsuario))) =
                   LOWER(LTRIM(RTRIM(po.emailProfessor)))
            ORDER BY po.codigoOferta, po.emailProfessor
        """).fetchone()

    if row is None:
        raise RuntimeError(
            "Nao existe cadeia IMP-009 com dependencias locais completas "
            "em IMP-001, IMP-002, IMP-005 e IMP-006."
        )

    oferta = dict(zip(CAMPOS_API["IMP-005"], row[2:10]))
    disciplina = dict(zip(CAMPOS_API["IMP-002"], row[10:14]))
    curso = dict(zip(CAMPOS_API["IMP-001"], row[14:18]))
    usuario = dict(zip(CAMPOS_API["IMP-006"], row[18:22]))
    vinculo = {
        "codigoOferta": row[0],
        "emailProfessor": row[1],
    }
    return curso, disciplina, oferta, usuario, vinculo


def validar(curso: dict, disciplina: dict, oferta: dict, usuario: dict, vinculo: dict) -> None:
    if str(disciplina["codigoCurso"]).strip() != str(curso["codigoCurso"]).strip():
        raise RuntimeError("Inconsistencia: IMP-002.codigoCurso difere do IMP-001.")
    if str(oferta["codigoDisciplina"]).strip() != str(disciplina["codigoDisciplina"]).strip():
        raise RuntimeError("Inconsistencia: IMP-005.codigoDisciplina difere do IMP-002.")
    if str(oferta["codigoOferta"]).strip() != str(vinculo["codigoOferta"]).strip():
        raise RuntimeError("Inconsistencia: IMP-009.codigoOferta difere do IMP-005.")
    if str(usuario["emailUsuario"]).strip().lower() != str(vinculo["emailProfessor"]).strip().lower():
        raise RuntimeError("Inconsistencia: IMP-009.emailProfessor difere do IMP-006.emailUsuario.")
    if not str(vinculo["codigoOferta"]).strip():
        raise RuntimeError("IMP-009.codigoOferta esta vazio.")
    if not str(vinculo["emailProfessor"]).strip() or "@" not in str(vinculo["emailProfessor"]):
        raise RuntimeError("IMP-009.emailProfessor invalido.")


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
            print("   ERRO API | registro=%s | excecao=%s | detalhes=%s" % (
                erro.get("numeroRegistro"), erro.get("nomeExcecao"), erro.get("detalhesFalha")))
        return False
    print(f"✅ {transacao} aceita com sucesso.")
    return True


def main() -> int:
    print("=" * 78)
    print(" TESTE CONTROLADO — CADEIA IMP-001 + IMP-002 + IMP-005 + IMP-006 + IMP-009")
    print(" Protocolo: 1.2.10 | Dicionario: 1.15.0")
    print(" Escopo: 1 curso + 1 disciplina + 1 oferta + 1 professor + 1 vinculo")
    print(" Nenhuma tabela local sera alterada.")
    print("=" * 78)
    try:
        validar_configuracao_qstione()
        print(f"Endpoint: {QSTIONE_BASE_URL}")
        print(f"SSL verify: {QSTIONE_SSL_VERIFY}")
        print(f"Timeout: {QSTIONE_TIMEOUT}s")
        print("Token: configurado (nao exibido)")
        print(f"Log: {LOG_FILE}")
        curso, disciplina, oferta, usuario, vinculo = buscar_registros()
        validar(curso, disciplina, oferta, usuario, vinculo)
        print(f"\nDependencia detectada: IMP-009.codigoOferta = {vinculo['codigoOferta']}")
        print(f"Dependencia detectada: IMP-005.codigoDisciplina = {oferta['codigoDisciplina']}")
        print(f"Dependencia detectada: IMP-002.codigoCurso = {disciplina['codigoCurso']}")
        print(f"Dependencia detectada: IMP-009.emailProfessor = {vinculo['emailProfessor']}")
        print("Ordem de envio: IMP-001 → IMP-002 → IMP-005 → IMP-006 → IMP-009")
    except Exception as exc:
        logger.exception("Falha na preparacao do teste IMP-009.")
        print(f"\n❌ Falha na validacao local: {exc}")
        print(f"Consulte o log: {LOG_FILE}")
        return 1

    cliente = ClienteQstione(url=QSTIONE_BASE_URL, token=QSTIONE_TOKEN or "",
                             timeout=QSTIONE_TIMEOUT, ssl_verify=QSTIONE_SSL_VERIFY)
    try:
        if not enviar(cliente, "IMP-001", curso): return 1
        if not enviar(cliente, "IMP-002", disciplina): return 1
        if not enviar(cliente, "IMP-005", oferta): return 1
        if not enviar(cliente, "IMP-006", usuario): return 1
        if not enviar(cliente, "IMP-009", vinculo): return 1
    finally:
        cliente.close()

    print("\n" + "=" * 78)
    print(" TESTE CONTROLADO CONCLUIDO")
    print(" IMP-001: OK")
    print(" IMP-002: OK")
    print(" IMP-005: OK")
    print(" IMP-006: OK")
    print(" IMP-009: OK")
    print(" Nenhuma tabela local foi alterada.")
    print(f" Log: {LOG_FILE}")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
