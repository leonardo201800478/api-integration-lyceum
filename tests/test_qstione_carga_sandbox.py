"""
Teste controlado da API Qstione no sandbox.

Executa SOMENTE duas transações, com 1 registro de cada:

    IMP-016 -> registro institucional fixo já existente na tabela
    IMP-001 -> primeiro curso da tabela

Não executa a carga completa e não altera os dados locais.

IMPORTANTE:
- codigoUnidadeGestora é opcional na IMP-016 segundo o dicionário 1.15.0.
- A tabela local de IMP-016 pode não possuir essa coluna; nesse caso o campo
  simplesmente não é enviado para a API.

Uso:
    python tests/test_qstione_carga_sandbox.py

O token nunca é exibido no console.
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


def obter_colunas_tabela(tabela: str) -> set[str]:
    """Retorna as colunas existentes na tabela Qstione."""
    sql = """
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'dbo'
          AND TABLE_NAME = ?
    """

    with get_db_connection(database_name="qstione") as conn:
        rows = conn.execute(sql, tabela).fetchall()

    return {str(row[0]) for row in rows}


def ler_primeiro_registro(tabela: str, campos: tuple[str, ...]) -> dict:
    """
    Lê exatamente um registro da tabela Qstione.

    Campos opcionais da API que não existem na tabela local são omitidos.
    Campos obrigatórios da transação continuam sendo exigidos.
    """
    colunas_existentes = obter_colunas_tabela(tabela)
    campos_presentes = tuple(campo for campo in campos if campo in colunas_existentes)

    if not campos_presentes:
        raise RuntimeError(
            f"A tabela {tabela} não possui nenhuma das colunas esperadas: {campos}."
        )

    # Para IMP-016, codigoUnidadeGestora é opcional no dicionário Qstione.
    if tabela == "imp_016_unidades_organizacionais":
        campos_obrigatorios = {"codigoUnidade", "nomeLongo"}
        ausentes = campos_obrigatorios - set(campos_presentes)
        if ausentes:
            raise RuntimeError(
                f"A tabela {tabela} não possui campos obrigatórios da IMP-016: "
                f"{sorted(ausentes)}."
            )

    lista_campos = ", ".join(f"[{campo}]" for campo in campos_presentes)
    sql = f"SELECT TOP 1 {lista_campos} FROM dbo.[{tabela}]"

    with get_db_connection(database_name="qstione") as conn:
        row = conn.execute(sql).fetchone()

    if row is None:
        raise RuntimeError(
            f"A tabela {tabela} não possui registros para o teste."
        )

    registro = dict(zip(campos_presentes, row))

    print(f"   Colunas utilizadas: {', '.join(campos_presentes)}")
    campos_omitidos = tuple(campo for campo in campos if campo not in colunas_existentes)
    if campos_omitidos:
        print(
            "   Campos opcionais ausentes na tabela local e omitidos do payload: "
            + ", ".join(campos_omitidos)
        )

    return registro


def exibir_registro(registro: dict) -> None:
    """Exibe o registro sem dados sensíveis de autenticação."""
    print("   Payload:")
    print(json.dumps(registro, ensure_ascii=False, indent=2, default=str))


def executar_transacao(
    cliente: ClienteQstione,
    transacao: str,
    tabela: str,
) -> bool:
    """Envia um único registro e valida o retorno da API."""
    campos = CAMPOS_API[transacao]
    registro = ler_primeiro_registro(tabela, campos)

    print()
    print("=" * 78)
    print(f"TESTE {transacao} — 1 registro")
    print("=" * 78)
    print(f"   Tabela: {tabela}")
    exibir_registro(registro)

    resultado = cliente.enviar(transacao, [registro])

    print("   Retorno:")
    print(f"      HTTP:              {resultado.http_status}")
    print(f"      codigoStatus:      {resultado.codigo_status}")
    print(f"      idRequisicao:      {resultado.id_requisicao}")
    print(f"      modoExecucao:      {resultado.modo_execucao}")
    print(f"      quantidadeErros:   {resultado.quantidade_registros_erro}")

    if resultado.corpo_bruto not in (None, [], {}):
        print("      corpoResposta:")
        print(
            json.dumps(
                resultado.corpo_bruto,
                ensure_ascii=False,
                indent=2,
                default=str,
            )
        )

    if resultado.assincrono:
        print()
        print(
            "   ❌ A API aceitou a operação como assíncrona. "
            "Este teste não considera a etapa concluída sem a confirmação "
            "posterior prevista pelo protocolo."
        )
        return False

    if not resultado.sucesso:
        print()
        print("   ❌ Transação rejeitada pela API.")
        for erro in resultado.erros:
            print(
                "      "
                f"registro={erro.get('numeroRegistro')}; "
                f"excecao={erro.get('nomeExcecao')}; "
                f"detalhes={erro.get('detalhesFalha')}"
            )
        return False

    print("   ✅ Transação aceita com sucesso.")
    return True


def main() -> int:
    print("=" * 78)
    print(" TESTE CONTROLADO — API QSTIONE SANDBOX")
    print(" Protocolo: 1.2.10 | Dicionário: 1.15.0")
    print(" Escopo: IMP-016 + IMP-001, 1 registro cada")
    print("=" * 78)

    validar_configuracao_qstione()

    print(f"Endpoint: {QSTIONE_BASE_URL}")
    print(f"SSL verify: {QSTIONE_SSL_VERIFY}")
    print(f"Timeout: {QSTIONE_TIMEOUT}s")
    print("Token: configurado (não exibido)")

    cliente = ClienteQstione(
        url=QSTIONE_BASE_URL,
        token=QSTIONE_TOKEN or "",
        timeout=QSTIONE_TIMEOUT,
        ssl_verify=QSTIONE_SSL_VERIFY,
    )

    try:
        # IMP-016 é exclusivamente o registro fixo já existente na tabela.
        if not executar_transacao(
            cliente,
            "IMP-016",
            "imp_016_unidades_organizacionais",
        ):
            return 1

        # Só executa IMP-001 depois da confirmação síncrona do IMP-016.
        if not executar_transacao(
            cliente,
            "IMP-001",
            "imp_001_cursos",
        ):
            return 1

    finally:
        cliente.close()

    print()
    print("=" * 78)
    print(" TESTE CONTROLADO CONCLUÍDO")
    print(" IMP-016: OK")
    print(" IMP-001: OK")
    print(" Nenhuma outra transação foi executada.")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
