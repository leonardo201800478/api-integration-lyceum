#!/usr/bin/env python3
"""
SINCRONIZAÇÃO LY_CURSO
- Execução direta
- Sem menu
- Somente GET na API Lyceum
- COM chave primária no campo 'curso'
- Upsert (insert/update)
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
from core.api_client import CursoAPIClient
from models.ly_curso import LyCursoModel

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
def sincronizar_cursos():
    """
    Sincroniza cursos da API Lyceum:
    - Busca completa (GET)
    - Validação mínima
    - Upsert por chave primária (curso)
    """
    logger.info("=" * 70)
    logger.info("INICIANDO SINCRONIZAÇÃO DE CURSOS")
    logger.info("Modo: UPSERT (CHAVE PRIMÁRIA = curso)")
    logger.info("=" * 70)

    inicio = time.time()

    # 1. Criar/verificar tabela
    LyCursoModel.create_table()

    resumo_inicial = LyCursoModel.get_summary()
    total_inicial = resumo_inicial.get("total_cursos", 0)
    logger.info(f"Total inicial no banco: {total_inicial}")

    # 2. Buscar dados da API
    logger.info("Buscando cursos na API Lyceum...")
    logger.info(f"Base URL: {config.LYCEUM_BASE_URL}")

    client = CursoAPIClient()
    cursos = client.get_cursos()  # ✅ somente GET

    if not cursos:
        logger.warning("API retornou zero registros")
        return {
            "success": True,
            "total_api": 0,
            "processados": 0,
            "tempo_total": 0,
        }

    logger.info(f"Total retornado pela API: {len(cursos)}")

    # 3. Filtrar e normalizar registros
    cursos_validos = []
    cursos_invalidos = 0

    for registro in cursos:
        if not isinstance(registro, dict):
            cursos_invalidos += 1
            continue

        # Curso é chave obrigatória
        if not registro.get("curso"):
            cursos_invalidos += 1
            continue

        registro_limpo = {}
        for campo, valor in registro.items():
            if valor is None:
                continue
            if not isinstance(valor, (str, int, float, bool)):
                valor = str(valor)
            registro_limpo[campo] = valor

        cursos_validos.append(registro_limpo)

    logger.info(f"Cursos válidos: {len(cursos_validos)}")
    if cursos_invalidos:
        logger.warning(f"Cursos inválidos ignorados: {cursos_invalidos}")

    if not cursos_validos:
        logger.warning("Nenhum curso válido para processamento")
        return {
            "success": True,
            "total_api": len(cursos),
            "processados": 0,
            "tempo_total": 0,
        }

    # 4. Estatísticas básicas
    ativos = sum(1 for c in cursos_validos if c.get("ativo") == "S")
    inativos = len(cursos_validos) - ativos

    logger.info("Estatísticas dos dados:")
    logger.info(f"  Ativos: {ativos}")
    logger.info(f"  Inativos: {inativos}")

    # Modalidades
    modalidades = {}
    for c in cursos_validos:
        modalidade = c.get("modalidade", "Não informado")
        modalidades[modalidade] = modalidades.get(modalidade, 0) + 1

    logger.info("Distribuição por modalidade (top 5):")
    for modalidade, qtd in sorted(modalidades.items(), key=lambda x: x[1], reverse=True)[:5]:
        logger.info(f"  {modalidade}: {qtd}")

    # Níveis
    niveis = {}
    for c in cursos_validos:
        nivel = c.get("nivel", "Não informado")
        niveis[nivel] = niveis.get(nivel, 0) + 1

    logger.info("Distribuição por nível (top 5):")
    for nivel, qtd in sorted(niveis.items(), key=lambda x: x[1], reverse=True)[:5]:
        logger.info(f"  {nivel}: {qtd}")

    # 5. Upsert no banco
    logger.info("Gravando cursos no banco local (UPSERT)...")
    processados = LyCursoModel.batch_upsert(cursos_validos)

    # 6. Resumo final
    tempo_total = time.time() - inicio
    resumo_final = LyCursoModel.get_summary()
    total_final = resumo_final.get("total_cursos", 0)

    logger.info("=" * 70)
    logger.info("RESUMO DA SINCRONIZAÇÃO")
    logger.info(f"API retornou: {len(cursos)}")
    logger.info(f"Válidos: {len(cursos_validos)}")
    logger.info(f"Processados: {processados}")
    logger.info(f"Banco antes: {total_inicial}")
    logger.info(f"Banco depois: {total_final}")
    logger.info(f"Cursos ativos: {resumo_final.get('cursos_ativos', 0)}")
    logger.info(f"Modalidades distintas: {resumo_final.get('modalidades_distintas', 0)}")
    logger.info(f"Níveis distintos: {resumo_final.get('niveis_distintos', 0)}")
    if resumo_final.get("ultima_atualizacao"):
        logger.info(f"Última atualização: {resumo_final['ultima_atualizacao']}")
    logger.info(f"Tempo total: {tempo_total:.2f}s")
    logger.info("=" * 70)

    return {
        "success": True,
        "total_api": len(cursos),
        "validos": len(cursos_validos),
        "processados": processados,
        "tempo_total": tempo_total,
    }


# ---------------------------------------------------------------------
# Entry point padrão
# ---------------------------------------------------------------------
def run():
    return sincronizar_cursos()


if __name__ == "__main__":
    resultado = run()
    sys.exit(0 if resultado else 1)
