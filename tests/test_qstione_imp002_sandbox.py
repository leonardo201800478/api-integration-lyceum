"""
Teste controlado da IMP-002 no sandbox Qstione.

Executa SOMENTE a IMP-002 com 1 registro da tabela local.
Não executa outras transações e não altera os dados locais.

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


TRANSACAO = "IMP-002"
TABELA = "imp_002_disciplina"


def descobrir_colunas(tabela: str) -> set[str]:
    with get_db_connection(database_name="qstione") as conn:
        rows = conn.execute(
            """
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'dbo'
              AND TABLE_NAME = ?
            """,
            (tabela,),
        ).fetchall()
    return {str(row[0]) for row in rows}


def ler_primeiro_registro() -> dict:
    campos_api = CAMPOS_API[TRANSACAO]
    colunas = descobrir_colunas(TABELA)
    campos_disponiveis = [campo for campo in campos_api if campo in colunas]
    campos_ausentes = [campo for campo in campos_api if campo not in colunas]

    if campos_ausentes:
        raise RuntimeError(
            "A tabela local não possui campos obrigatórios da IMP-002: "
            + ", ".join(campos_ausentes)
        )

    lista_campos = ", ".join(f"[{campo}]" for campo in campos_disponiveis)
    sql = f"SELECT TOP 1 {lista_campos} FROM dbo.[{TABELA}] ORDER BY [codigoDisciplina]"

    with get_db_connection(database_name="qstione") as conn:
        row = conn.execute(sql).fetchone()

    if row is None:
        raise RuntimeError(f"A tabela {TABELA} não possui registros para o teste.")

    registro = dict(zip(campos_disponiveis, row))
    print(f"   Colunas utilizadas: {', '.join(campos_disponiveis)}")
    return registro


def main() -> int:
    print("=" * 78)
    print(" TESTE CONTROLADO — API QSTIONE SANDBOX")
    print(" Protocolo: 1.2.10 | Dicionário: 1.15.0")
    print(" Escopo: IMP-002, 1 registro")
    print("=" * 78)

    validar_configuracao_qstione()

    print(f"Endpoint: {QSTIONE_BASE_URL}")
    print(f"SSL verify: {QSTIONE_SSL_VERIFY}")
    print(f"Timeout: {QSTIONE_TIMEOUT}s")
    print("Token: configurado (não exibido)")

    registro = ler_primeiro_registro()

    print()
    print("=" * 78)
    print("TESTE IMP-002 — 1 registro")
    print("=" * 78)
    print(f"   Tabela: {TABELA}")
    print("   Payload:")
    print(json.dumps(registro, ensure_ascii=False, indent=2, default=str))

    cliente = ClienteQstione(
        url=QSTIONE_BASE_URL,
        token=QSTIONE_TOKEN or "",
        timeout=QSTIONE_TIMEOUT,
        ssl_verify=QSTIONE_SSL_VERIFY,
    )

    try:
        resultado = cliente.enviar(TRANSACAO, [registro])
    finally:
        cliente.close()

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
        return 1

    if not resultado.sucesso:
        print("\n   ❌ IMP-002 rejeitada pela API.")
        for erro in resultado.erros:
            print(
                "      "
                f"registro={erro.get('numeroRegistro')}; "
                f"excecao={erro.get('nomeExcecao')}; "
                f"detalhes={erro.get('detalhesFalha')}"
            )
        return 1

    print("   ✅ IMP-002 aceita com sucesso.")
    print()
    print("=" * 78)
    print(" TESTE IMP-002 CONCLUÍDO")
    print(" Nenhuma outra transação foi executada.")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
