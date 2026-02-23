#!/usr/bin/env python3
"""
Sincronizador da tabela LY_PROVA_DISCIP
Utiliza o cliente ProvaDisciplinaAPIClient para obter dados paginados.
"""

import logging
from core.api_client import get_prova_disciplina_client
from models.ly_prova_discip import LyProvaDiscipModel

logger = logging.getLogger("sync_ly_prova_discip")


def run() -> bool:
    """
    Executa a sincronia completa de provas-disciplinas.
    - Obtém todos os registros da API (paginação automática)
    - Insere/atualiza em lote no banco
    """
    logger.info("=" * 50)
    logger.info("Iniciando sincronização de LY_PROVA_DISCIP...")

    try:
        # Cria a tabela se não existir
        LyProvaDiscipModel.create_table()

        # Obtém dados da API
        client = get_prova_disciplina_client()
        logger.info("Buscando dados da API...")
        dados_api = client.get_provas_disciplinas()

        if not dados_api:
            logger.warning("Nenhum dado retornado pela API.")
            return True

        logger.info(f"Total de registros obtidos da API: {len(dados_api)}")

        # Insere em lote
        inseridos = LyProvaDiscipModel.batch_insert(dados_api)

        logger.info(f"Registros inseridos/atualizados: {inseridos}")
        logger.info("Sincronização de LY_PROVA_DISCIP concluída com sucesso.")
        return True

    except Exception as e:
        logger.error(f"Erro durante sincronização: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    # Para execução direta (teste)
    logging.basicConfig(level=logging.INFO)
    run()