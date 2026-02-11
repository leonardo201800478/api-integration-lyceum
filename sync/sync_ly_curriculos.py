#!/usr/bin/env python3
"""
SINCRONIZAÇÃO LY_CURRICULO
- Execução direta
- Sem menu
- Sem filtros
- Somente GET na API Lyceum
- SEM chave primária (permite duplicatas)
- Sincronização completa (truncate + insert)
"""

import sys
import os
import time
import logging

# ---------------------------------------------------------------------
# Garantir import do projeto
# ---------------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ---------------------------------------------------------------------
# Imports internos
# ---------------------------------------------------------------------
from core.config import config
from core.api_client import CurriculoAPIClient
from models.ly_curriculo import LyCurriculoModel

# ---------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------
# Função principal de sincronização
# ---------------------------------------------------------------------
def sincronizar_curriculos():
    """
    Sincroniza TODOS os currículos:
    - Busca completa via API (GET)
    - Limpa tabela local
    - Insere novamente
    - Permite duplicatas (sem PK)
    """
    logger.info("=" * 70)
    logger.info("INICIANDO SINCRONIZAÇÃO DE CURRÍCULOS")
    logger.info("Modo: COMPLETO (SEM FILTROS / SEM CHAVE PRIMÁRIA)")
    logger.info("=" * 70)

    inicio = time.time()

    # 1. Criar/verificar tabela
    LyCurriculoModel.create_table()

    resumo_inicial = LyCurriculoModel.get_summary()
    total_inicial = resumo_inicial.get("total_curriculos", 0)
    logger.info(f"Total inicial no banco: {total_inicial}")

    # 2. Buscar dados da API
    logger.info("Buscando currículos na API Lyceum...")
    logger.info(f"Base URL: {config.LYCEUM_BASE_URL}")

    client = CurriculoAPIClient()
    curriculos = client.get_curriculos()  # ✅ somente GET

    if not curriculos:
        logger.warning("API retornou zero registros")
        return {
            "success": True,
            "total_api": 0,
            "inseridas": 0,
            "tempo_total": 0,
        }

    logger.info(f"Total retornado pela API: {len(curriculos)}")

    # 3. Filtrar e normalizar registros
    registros_validos = []
    registros_invalidos = 0

    for idx, registro in enumerate(curriculos):
        if not isinstance(registro, dict):
            registros_invalidos += 1
            continue

        # Regras mínimas de validade
        if not registro.get("curriculo") or not registro.get("curso"):
            registros_invalidos += 1
            continue

        registro_limpo = {}
        for campo, valor in registro.items():
            if valor is None:
                continue
            if not isinstance(valor, (str, int, float, bool)):
                valor = str(valor)
            registro_limpo[campo] = valor

        registros_validos.append(registro_limpo)

    logger.info(f"Registros válidos: {len(registros_validos)}")
    if registros_invalidos:
        logger.warning(f"Registros inválidos ignorados: {registros_invalidos}")

    if not registros_validos:
        logger.warning("Nenhum registro válido para inserção")
        return {
            "success": True,
            "total_api": len(curriculos),
            "inseridas": 0,
            "tempo_total": 0,
        }

    # 4. Análise simples de duplicatas (API)
    pares_unicos = {
        f"{r.get('curriculo')}-{r.get('curso')}"
        for r in registros_validos
    }

    logger.info("Análise de duplicatas (dados da API):")
    logger.info(f"  Registros totais: {len(registros_validos)}")
    logger.info(f"  Pares únicos curriculo-curso: {len(pares_unicos)}")
    logger.info(f"  Duplicatas: {len(registros_validos) - len(pares_unicos)}")

    # 5. Limpar tabela local
    logger.info("Limpando tabela LY_CURRICULO...")
    LyCurriculoModel.clear_table()

    # 6. Inserir no banco
    logger.info("Inserindo registros no banco local...")
    inseridas = LyCurriculoModel.batch_insert(registros_validos)

    # 7. Resumo final
    tempo_total = time.time() - inicio
    resumo_final = LyCurriculoModel.get_summary()
    total_final = resumo_final.get("total_curriculos", 0)

    logger.info("=" * 70)
    logger.info("RESUMO DA SINCRONIZAÇÃO")
    logger.info(f"API retornou: {len(curriculos)}")
    logger.info(f"Válidos: {len(registros_validos)}")
    logger.info(f"Inseridos: {inseridas}")
    logger.info(f"Banco antes: {total_inicial}")
    logger.info(f"Banco depois: {total_final}")
    logger.info(f"Cursos distintos: {resumo_final.get('cursos_distintos', 0)}")
    logger.info(f"Currículos distintos: {resumo_final.get('curriculos_distintos', 0)}")
    if resumo_final.get("ultima_atualizacao"):
        logger.info(f"Última atualização: {resumo_final['ultima_atualizacao']}")
    logger.info(f"Tempo total: {tempo_total:.2f}s")
    logger.info("=" * 70)

    return {
        "success": True,
        "total_api": len(curriculos),
        "validas": len(registros_validos),
        "inseridas": inseridas,
        "tempo_total": tempo_total,
    }


# ---------------------------------------------------------------------
# Entry point padrão
# ---------------------------------------------------------------------
def run():
    return sincronizar_curriculos()


if __name__ == "__main__":
    sucesso = run()
    sys.exit(0 if sucesso else 1)
