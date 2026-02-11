#!/usr/bin/env python3
"""
Sincronização da tabela LY_DOCENTE

- Sincronização COMPLETA (full refresh)
- API Lyceum: SOMENTE GET
- Banco local: clear + batch insert
- Sem chave primária fixa (padrão LY_TURMA)
"""

import sys
import os
import time
import logging
from datetime import datetime
from collections import Counter
from typing import List, Dict

# Garante import do projeto
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from core.config import config
from core.api_client import DocenteAPIClient
from models.ly_docente import LyDocenteModel


# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("sync_ly_docente")


# -----------------------------------------------------------------------------
# Funções auxiliares
# -----------------------------------------------------------------------------
def validar_docentes(docentes: List[Dict]) -> tuple[list[Dict], int]:
    """
    Filtra docentes válidos.

    Regras:
    - cpf obrigatório
    - num_func obrigatório
    """
    validos = []
    invalidos = 0

    for d in docentes:
        if d.get("cpf") and d.get("num_func"):
            validos.append(d)
        else:
            invalidos += 1

    return validos, invalidos


def log_estatisticas(docentes: List[Dict]) -> None:
    """Gera estatísticas descritivas para auditoria."""
    ativos = sum(1 for d in docentes if d.get("ativo") == "S")
    inativos = len(docentes) - ativos

    logger.info("Estatísticas gerais:")
    logger.info(" - Total: %s", len(docentes))
    logger.info(" - Ativos: %s", ativos)
    logger.info(" - Inativos: %s", inativos)

    deptos = Counter(d.get("depto", "Não informado") for d in docentes)
    logger.info("Top 10 departamentos:")
    for depto, qtd in deptos.most_common(10):
        logger.info(" - %s: %s", depto, qtd)

    titulacoes = Counter(d.get("titulacao", "Não informado") for d in docentes)
    logger.info("Top 5 titulações:")
    for tit, qtd in titulacoes.most_common(5):
        logger.info(" - %s: %s", tit, qtd)

    chaves = [f"{d.get('cpf')}-{d.get('num_func')}" for d in docentes]
    unicos = set(chaves)

    logger.info("Combinações cpf-num_func:")
    logger.info(" - Registros: %s", len(chaves))
    logger.info(" - Únicos: %s", len(unicos))
    logger.info(" - Duplicados: %s", len(chaves) - len(unicos))


# -----------------------------------------------------------------------------
# Sincronização principal
# -----------------------------------------------------------------------------
def sincronizar_docentes() -> bool:
    """
    Executa a sincronização completa da tabela LY_DOCENTE.

    Fluxo:
    1. Cria/verifica tabela
    2. Busca dados via GET na API Lyceum
    3. Valida registros
    4. Limpa tabela local
    5. Insere dados válidos
    """
    logger.info("=" * 70)
    logger.info("INICIANDO SINCRONIZAÇÃO DA TABELA LY_DOCENTE")
    logger.info("Início: %s", datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
    logger.info("=" * 70)

    inicio = time.time()

    # 1. Tabela
    LyDocenteModel.create_table()
    resumo_inicial = LyDocenteModel.get_summary()

    logger.info("Resumo inicial: %s", resumo_inicial)

    # 2. API (GET)
    client = DocenteAPIClient()
    docentes_api = client.get_docentes()

    if not docentes_api:
        logger.warning("Nenhum docente retornado pela API")
        return False

    logger.info("Total retornado pela API: %s", len(docentes_api))

    # 3. Validação
    docentes_validos, docentes_invalidos = validar_docentes(docentes_api)

    logger.info("Docentes válidos: %s", len(docentes_validos))
    if docentes_invalidos:
        logger.warning("Docentes inválidos descartados: %s", docentes_invalidos)

    if not docentes_validos:
        logger.warning("Nenhum docente válido para inserção")
        return True

    # Amostra
    amostra = docentes_validos[0]
    logger.info(
        "Amostra | CPF=%s | NUM_FUNC=%s | NOME=%s",
        amostra.get("cpf"),
        amostra.get("num_func"),
        amostra.get("nome_compl"),
    )

    log_estatisticas(docentes_validos)

    # 4. Banco local
    logger.info("Limpando tabela LY_DOCENTE")
    LyDocenteModel.clear_table()

    logger.info("Inserindo %s docentes", len(docentes_validos))
    inseridos = LyDocenteModel.batch_insert(docentes_validos)

    # 5. Resumo final
    tempo_total = time.time() - inicio
    resumo_final = LyDocenteModel.get_summary()

    logger.info("=" * 70)
    logger.info("RESUMO FINAL")
    logger.info("Inseridos: %s", inseridos)
    logger.info("Resumo final: %s", resumo_final)
    logger.info("Tempo total: %.2f s", tempo_total)
    logger.info("Taxa: %.2f docentes/s", inseridos / tempo_total)
    logger.info("=" * 70)

    return inseridos == len(docentes_validos)


# -----------------------------------------------------------------------------
# Entry point
# -----------------------------------------------------------------------------
def main() -> int:
    """Ponto de entrada do script."""
    if not all(
        [config.LYCEUM_BASE_URL, config.LYCEUM_USERNAME, config.LYCEUM_PASSWORD]
    ):
        logger.error("Configurações da API Lyceum incompletas (.env)")
        return 1

    try:
        sucesso = sincronizar_docentes()
        return 0 if sucesso else 1

    except KeyboardInterrupt:
        logger.warning("Processo interrompido pelo usuário")
        return 1

    except Exception:
        logger.exception("Erro inesperado na sincronização")
        return 1


if __name__ == "__main__":
    sys.exit(main())
