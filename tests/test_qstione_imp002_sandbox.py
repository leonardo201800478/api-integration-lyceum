"""
Teste controlado da cadeia IMP-001 -> IMP-002 no sandbox Qstione.

Executa SOMENTE:
    1. IMP-001 para o curso associado ao primeiro registro da IMP-002;
    2. IMP-002 para esse mesmo registro.

A finalidade é validar a dependência obrigatória entre curso e disciplina.
Não altera os dados locais.

Uso:
    python tests/test_qstione_imp002_sandbox.py
"""

from __future__ import annotations

import json
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


def ler_registro_disciplina() -> dict:
    campos = CAMPOS_API["IMP-002"]
    sql = (
        "SELECT TOP 1 "
        + ", ".join(f"[{campo}]" for campo in campos)
        + f" FROM dbo.[{TABELA_DISCIPLINA}] ORDER BY [codigoDisciplina]"
    )
    with get_db_connection(database_name="qstione") as conn:
        row = conn.execute(sql).fetchone()
    if row is None:
        raise RuntimeError(f"A tabela {TABELA_DISCIPLINA} não possui registros.")
    return dict(zip(campos, row))


def ler_curso(codigo_curso: str) -> dict:
    campos = CAMPOS_API["IMP-001"]
    sql = (
        "SELECT TOP 1 "
        + ", ".join(f"[{campo}]" for campo in campos)
        + f" FROM dbo.[{TABELA_CURSO}] WHERE LTRIM(RTRIM([codigoCurso])) = ?"
    )
    with get_db_connection(database_name="qstione") as conn:
        row = conn.execute(sql, (codigo_curso,)).fetchone()
    if row is None:
        raise RuntimeError(
            f"Não foi encontrado na tabela {TABELA_CURSO} o curso "
            f"associado à disciplina: {codigo_curso}."
        )
    return dict(zip(campos, row))


def enviar_e_exibir(cliente: ClienteQstione, transacao: str, registro: dict) -> bool:
    print()
    print("=" * 78)
    print(f"TESTE {transacao} — 1 registro")
    print("=" * 78)
    print("   Payload:")
    print(json.dumps(registro, ensure_ascii=False, indent=2, default=str))

    resultado = cliente.enviar(transacao, [registro])

    print("   Retorno:")
    print(f"      HTTP:              {resultado.http_status}")
    print(f"      codigoStatus:      {resultado.codigo_status}")
    print(f"      idRequisicao:      {resultado.id_requisicao}")
    print(f"      modoExecucao:      {resultado.modo_execucao}")
    print(f"      quantidadeErros:   {resultado.quantidade_registros_erro}")

    if resultado.corpo_bruto not in (None, [], {}):
        print("      corpoResposta:")
        print(json.dumps(resultado.corpo_bruto, ensure_ascii=False, indent=2, default=str))

    if resultado.assincrono:
        print("\n   ❌ A API aceitou a operação como assíncrona.")
        return False

    if not resultado.sucesso:
        print(f"\n   ❌ {transacao} rejeitada pela API.")
        for erro in resultado.erros:
            print(
                "      "
                f"registro={erro.get('numeroRegistro')}; "
                f"excecao={erro.get('nomeExcecao')}; "
                f"detalhes={erro.get('detalhesFalha')}"
            )
        return False

    print(f"   ✅ {transacao} aceita com sucesso.")
    return True


def main() -> int:
    print("=" * 78)
    print(" TESTE CONTROLADO — CADEIA IMP-001 + IMP-002")
    print(" Protocolo: 1.2.10 | Dicionário: 1.15.0")
    print(" Escopo: curso da primeira disciplina + 1 disciplina")
    print("=" * 78)

    validar_configuracao_qstione()
    print(f"Endpoint: {QSTIONE_BASE_URL}")
    print(f"SSL verify: {QSTIONE_SSL_VERIFY}")
    print(f"Timeout: {QSTIONE_TIMEOUT}s")
    print("Token: configurado (não exibido)")

    disciplina = ler_registro_disciplina()
    codigo_curso = str(disciplina["codigoCurso"]).strip()
    curso = ler_curso(codigo_curso)

    print(f"\n   Dependência detectada: IMP-002.codigoCurso = {codigo_curso}")
    print("   O teste enviará primeiro esse curso à API e somente depois a disciplina.")

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
    finally:
        cliente.close()

    print()
    print("=" * 78)
    print(" TESTE CONTROLADO CONCLUÍDO")
    print(" IMP-001: OK")
    print(" IMP-002: OK")
    print(" Nenhuma outra transação foi executada.")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
