#!/usr/bin/env python3
"""
SINCRONIZAÇÃO LY_DISCIPLINA
- Execução direta
- Sem menu
- Somente GET na API Lyceum
- SEM chave primária fixa (permite duplicatas)
- Sincronização completa (clear + insert)
"""

import sys
import os
import time
import logging
from collections import Counter

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
from core.api_client import DisciplinaAPIClient
from models.ly_disciplina import LyDisciplinaModel

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
def sincronizar_disciplinas():
    """
    Sincroniza disciplinas da API Lyceum:
    - Busca completa (GET)
    - Validação mínima
    - Limpa e reinsere todos os dados
    """
    logger.info("=" * 70)
    logger.info("INICIANDO SINCRONIZAÇÃO DE DISCIPLINAS")
    logger.info("Modo: COMPLETO (SEM CHAVE PRIMÁRIA)")
    logger.info("=" * 70)

    inicio = time.time()

    # 1. Criar/verificar tabela
    LyDisciplinaModel.create_table()

    resumo_inicial = LyDisciplinaModel.get_summary()
    total_inicial = resumo_inicial.get("total_disciplinas", 0)
    logger.info(f"Total inicial no banco: {total_inicial}")

    # 2. Buscar dados da API
    logger.info("Buscando disciplinas na API Lyceum...")
    logger.info(f"Base URL: {config.LYCEUM_BASE_URL}")

    client = DisciplinaAPIClient()
    disciplinas = client.get_disciplinas()  # ✅ somente GET

    if not disciplinas:
        logger.warning("API retornou zero registros")
        return {
            "success": True,
            "total_api": 0,
            "processados": 0,
            "tempo_total": 0,
        }

    logger.info(f"Total retornado pela API: {len(disciplinas)}")

    # 3. Filtrar e normalizar registros
    disciplinas_validas = []
    disciplinas_invalidas = 0

    for registro in disciplinas:
        if not isinstance(registro, dict):
            disciplinas_invalidas += 1
            continue

        if not registro.get("disciplina"):
            disciplinas_invalidas += 1
            continue

        registro_limpo = {}
        for campo, valor in registro.items():
            if valor is None:
                continue
            if not isinstance(valor, (str, int, float, bool)):
                valor = str(valor)
            registro_limpo[campo] = valor

        disciplinas_validas.append(registro_limpo)

    logger.info(f"Disciplinas válidas: {len(disciplinas_validas)}")
    if disciplinas_invalidas:
        logger.warning(f"Disciplinas inválidas ignoradas: {disciplinas_invalidas}")

    if not disciplinas_validas:
        logger.warning("Nenhuma disciplina válida para processamento")
        return {
            "success": True,
            "total_api": len(disciplinas),
            "processados": 0,
            "tempo_total": 0,
        }

    # 4. Estatísticas básicas
    ativas = sum(1 for d in disciplinas_validas if d.get("ativo") == "S")
    inativas = len(disciplinas_validas) - ativas

    logger.info("Estatísticas dos dados:")
    logger.info(f"  Ativas: {ativas}")
    logger.info(f"  Inativas: {inativas}")

    faculdades = Counter(d.get("faculdade", "Não informado") for d in disciplinas_validas)
    departamentos = Counter(d.get("depto", "Não informado") for d in disciplinas_validas)

    logger.info("Distribuição por faculdade (top 5):")
    for faculdade, qtd in faculdades.most_common(5):
        logger.info(f"  {faculdade}: {qtd}")

    logger.info("Distribuição por departamento (top 5):")
    for depto, qtd in departamentos.most_common(5):
        logger.info(f"  {depto}: {qtd}")

    # Análise de duplicatas
    codigos = [d.get("disciplina") for d in disciplinas_validas if d.get("disciplina")]
    duplicatas = len(codigos) - len(set(codigos))
    logger.info(f"Códigos distintos de disciplina: {len(set(codigos))}")
    logger.info(f"Duplicatas detectadas: {duplicatas}")

    # 5. Limpar tabela
    logger.info("Limpando tabela LY_DISCIPLINA...")
    LyDisciplinaModel.clear_table()

    # 6. Inserir no banco
    logger.info("Inserindo disciplinas no banco local...")
    processadas = LyDisciplinaModel.batch_insert(disciplinas_validas)

    # 7. Resumo final
    tempo_total = time.time() - inicio
    resumo_final = LyDisciplinaModel.get_summary()
    total_final = resumo_final.get("total_disciplinas", 0)

    logger.info("=" * 70)
    logger.info("RESUMO DA SINCRONIZAÇÃO")
    logger.info(f"API retornou: {len(disciplinas)}")
    logger.info(f"Válidas: {len(disciplinas_validas)}")
    logger.info(f"Processadas: {processadas}")
    logger.info(f"Banco antes: {total_inicial}")
    logger.info(f"Banco depois: {total_final}")
    logger.info(f"Disciplinas ativas: {resumo_final.get('disciplinas_ativas', 0)}")
    logger.info(f"Faculdades distintas: {resumo_final.get('faculdades_distintas', 0)}")
    logger.info(f"Departamentos distintos: {resumo_final.get('departamentos_distintos', 0)}")
    if resumo_final.get("ultima_atualizacao"):
        logger.info(f"Última atualização: {resumo_final['ultima_atualizacao']}")
    logger.info(f"Tempo total: {tempo_total:.2f}s")
    logger.info("=" * 70)

    return {
        "success": True,
        "total_api": len(disciplinas),
        "validos": len(disciplinas_validas),
        "processados": processadas,
        "tempo_total": tempo_total,
    }


# ---------------------------------------------------------------------
# Entry point padrão
# ---------------------------------------------------------------------
def run():
    return sincronizar_disciplinas()


if __name__ == "__main__":
    resultado = run()
    sys.exit(0 if resultado else 1)
