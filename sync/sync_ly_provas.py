#!/usr/bin/env python3
"""
sync/sync_ly_provas.py
Sincroniza LY_PROVA a partir das turmas abertas (consulta direta ao banco) e lista de provas.
Para cada turma (ano, disciplina, semestre, turma) e para cada prova da lista,
chama a API e insere/atualiza.
"""

import sys
import os
import time
import logging
from typing import List, Dict, Any

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.config import config
from core.api_client import get_prova_client
from models.sql_turma import SQLTurmaModel
from models.ly_prova import LyProvaModel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ============================================================
# CONFIGURAÇÃO
# ============================================================
# Lista de códigos de prova a serem consultados
PROVAS_OPCOES = ['AV', 'AVF', 'AVS', 'AVSB']   # Pode ser expandido

# Unidades permitidas (None para todas)
UNIDADES = ['001', '002']   # ou None para todas

# Paginação artificial (lotes de chamadas)
PAGE_SIZE = 50          # Número de combinações (turma x prova) por lote
API_DELAY = 0.5          # Delay entre chamadas


def gerar_combinacoes(turmas: List[Dict], provas: List[str]) -> List[Dict[str, Any]]:
    """
    Gera todas as combinações de turma + prova.
    Cada combinação é um dicionário com: ano, disciplina, prova, semestre, turma.
    """
    combinacoes = []
    for turma in turmas:
        for prova in provas:
            combinacoes.append({
                'ano': turma['ano'],
                'disciplina': turma['disciplina'],
                'prova': prova,
                'semestre': turma['semestre'],
                'turma': turma['turma'],
                # campos extras para log
                'curso': turma.get('curso'),
                'unidade': turma.get('unidade_responsavel'),
            })
    return combinacoes


def sincronizar_provas():
    logger.info("=" * 70)
    logger.info("INICIANDO SINCRONIZAÇÃO DE PROVAS (turmas abertas + lista de provas)")
    if UNIDADES:
        logger.info(f"Unidades: {UNIDADES}")
    else:
        logger.info("Unidades: todas")
    logger.info(f"Tipos de prova: {PROVAS_OPCOES}")
    logger.info("=" * 70)

    inicio = time.time()

    # 1. Criar/verificar tabela LY_PROVA
    LyProvaModel.create_table()
    total_inicial = LyProvaModel.get_summary().get("total_provas", 0)
    logger.info(f"Total inicial no banco: {total_inicial}")

    # 2. Buscar turmas abertas diretamente da tabela SQL
    turmas = SQLTurmaModel.get_turmas_abertas(unidades=UNIDADES)
    if not turmas:
        logger.warning("Nenhuma turma aberta encontrada para as unidades especificadas.")
        return {"success": True, "total_combinacoes": 0, "processados": 0}

    logger.info(f"Encontradas {len(turmas)} turmas abertas.")

    # 3. Gerar combinações
    combinacoes = gerar_combinacoes(turmas, PROVAS_OPCOES)
    total_combinacoes = len(combinacoes)
    logger.info(f"Total de combinações (turma x prova): {total_combinacoes}")

    if not combinacoes:
        logger.warning("Nenhuma combinação gerada.")
        return {"success": True, "total_combinacoes": 0, "processados": 0}

    # 4. Inicializar cliente da API
    client = get_prova_client()
    logger.info(f"Base URL: {config.LYCEUM_BASE_URL}")

    # 5. Processar combinações em lotes
    sucessos = 0
    falhas = 0
    page = 0
    dados_para_upsert = []

    while page * PAGE_SIZE < total_combinacoes:
        start = page * PAGE_SIZE
        end = min(start + PAGE_SIZE, total_combinacoes)
        batch = combinacoes[start:end]
        logger.info(f"Processando lote {page} (registros {start+1} a {end})")

        for comb in batch:
            ano = comb['ano']
            disciplina = comb['disciplina']
            prova = comb['prova']
            semestre = comb['semestre']
            turma = comb['turma']

            try:
                data = client.get_prova(
                    ano=ano,
                    disciplina=disciplina,
                    prova=prova,
                    semestre=semestre,
                    turma=turma
                )
                if data:
                    dados_para_upsert.append(data)
                    sucessos += 1
                else:
                    falhas += 1
                    logger.warning(f"Nenhum dado para combinação: {comb}")
            except Exception as e:
                falhas += 1
                logger.error(f"Erro na combinação {comb}: {e}")

            time.sleep(API_DELAY)

        # Upsert do lote acumulado
        if dados_para_upsert:
            logger.info(f"Gravando lote de {len(dados_para_upsert)} provas no banco...")
            LyProvaModel.batch_upsert(dados_para_upsert)
            dados_para_upsert = []

        page += 1

    # Upsert final (caso sobre dados)
    if dados_para_upsert:
        LyProvaModel.batch_upsert(dados_para_upsert)

    # 6. Resumo final
    tempo_total = time.time() - inicio
    total_final = LyProvaModel.get_summary().get("total_provas", 0)

    logger.info("=" * 70)
    logger.info("RESUMO DA SINCRONIZAÇÃO")
    logger.info(f"Total de combinações processadas: {total_combinacoes}")
    logger.info(f"Sucessos: {sucessos}")
    logger.info(f"Falhas: {falhas}")
    logger.info(f"Banco antes: {total_inicial}")
    logger.info(f"Banco depois: {total_final}")
    logger.info(f"Tempo total: {tempo_total:.2f}s")
    logger.info("=" * 70)

    return {
        "success": falhas == 0,
        "total_combinacoes": total_combinacoes,
        "sucessos": sucessos,
        "falhas": falhas,
    }


def run():
    return sincronizar_provas()


if __name__ == "__main__":
    resultado = run()
    sys.exit(0 if resultado.get("success", False) else 1)