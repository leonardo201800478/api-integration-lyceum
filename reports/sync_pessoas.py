# reports/sync_pessoas.py
"""
Ponto de entrada standalone para sincronização manual de pessoas pendentes.

A lógica de consulta e sincronização foi centralizada em:
    sync.sync_ly_pessoa_by_id._buscar_pessoas_pendentes()
    sync.sync_ly_pessoa_by_id.buscar_e_salvar_pessoa_por_id()

Este módulo importa essas funções diretamente, eliminando o uso de
subprocess e garantindo que logs, conexões e tratamento de erros
sejam unificados com o restante do projeto.

Uso:
    python reports/sync_pessoas.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.logger import logger
from sync.sync_ly_pessoa_by_id import (
    _buscar_pessoas_pendentes,
    buscar_e_salvar_pessoa_por_id,
)


def verificar_e_sincronizar_pessoas() -> None:
    """Verifica pessoas em LY_ALUNO não existentes em LY_PESSOA e sincroniza."""
    logger.info("Verificando pessoas faltantes na tabela LY_PESSOA...")

    try:
        faltantes = _buscar_pessoas_pendentes()
    except Exception as e:
        logger.error(f"Erro ao consultar pessoas pendentes: {e}")
        return

    if not faltantes:
        logger.info("Nenhuma pessoa faltante encontrada.")
        return

    total = len(faltantes)
    logger.info(f"Encontradas {total} pessoas faltantes. Iniciando sincronização...")

    sucessos, falhas = 0, 0
    for pessoa_id in faltantes:
        logger.info(f"Sincronizando pessoa ID: {pessoa_id}")
        resultado = buscar_e_salvar_pessoa_por_id(pessoa_id, buscar_alunos=False)
        if resultado:
            sucessos += 1
        else:
            falhas += 1
            logger.error(f"Falha ao sincronizar pessoa {pessoa_id}")

    logger.info(f"Sincronização concluída: {sucessos}/{total} com sucesso | {falhas} falhas.")


if __name__ == "__main__":
    verificar_e_sincronizar_pessoas()