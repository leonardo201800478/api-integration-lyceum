#!/usr/bin/env python3
"""
Sincronização da tabela LY_GRADE

- Sincronização COMPLETA (full refresh)
- API Lyceum: SOMENTE GET
- Banco local: clear + batch insert
- Sem chave primária fixa (padrão LY_TURMA / LY_CURRICULO)
"""

import sys
import os
import time
import logging
from datetime import datetime
from collections import Counter
from typing import List, Dict


# -----------------------------------------------------------------------------
# Path do projeto
# -----------------------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)


# -----------------------------------------------------------------------------
# Importações internas
# -----------------------------------------------------------------------------
from core.config import config
from core.api_client import get_grade_client
from models.ly_grade import LyGradeModel


# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("sync_ly_grade")


# -----------------------------------------------------------------------------
# Funções auxiliares
# -----------------------------------------------------------------------------
def validar_grades(grades: List[Dict]) -> tuple[list[Dict], int]:
    """
    Filtra registros válidos de grade.

    Campos obrigatórios:
    - curriculo
    - curso
    - disciplina
    """
    validas = []
    invalidas = 0

    for g in grades:
        if g.get("curriculo") and g.get("curso") and g.get("disciplina"):
            validas.append(g)
        else:
            invalidas += 1

    return validas, invalidas


def log_estatisticas(grades: List[Dict]) -> None:
    """Gera estatísticas descritivas para auditoria."""
    obrigatorias = sum(1 for g in grades if g.get("obrigatoria") == "S")
    optativas = len(grades) - obrigatorias

    logger.info("Estatísticas gerais:")
    logger.info(" - Total: %s", len(grades))
    logger.info(" - Obrigatórias: %s", obrigatorias)
    logger.info(" - Optativas: %s", optativas)

    curriculos = Counter(g.get("curriculo", "Não informado") for g in grades)
    logger.info("Top 5 currículos:")
    for cur, qtd in curriculos.most_common(5):
        logger.info(" - %s: %s", cur, qtd)

    cursos = Counter(g.get("curso", "Não informado") for g in grades)
    logger.info("Top 5 cursos:")
    for curso, qtd in cursos.most_common(5):
        logger.info(" - %s: %s", curso, qtd)

    series = Counter(g.get("serie_ideal", "Não informado") for g in grades)
    logger.info("Distribuição por série ideal:")
    for serie, qtd in sorted(series.items()):
        logger.info(" - Série %s: %s", serie, qtd)

    chaves = [
        f"{g.get('curriculo')}-{g.get('curso')}-{g.get('disciplina')}"
        for g in grades
    ]
    unicos = set(chaves)

    logger.info("Combinações curriculo-curso-disciplina:")
    logger.info(" - Registros: %s", len(chaves))
    logger.info(" - Únicos: %s", len(unicos))
    logger.info(" - Duplicados: %s", len(chaves) - len(unicos))


# -----------------------------------------------------------------------------
# Sincronização principal
# -----------------------------------------------------------------------------
def sincronizar_grades() -> bool:
    """
    Executa a sincronização completa da tabela LY_GRADE.

    Fluxo:
    1. Cria/verifica tabela
    2. Busca dados via GET na API Lyceum
    3. Valida registros
    4. Limpa tabela local
    5. Insere dados válidos
    """
    logger.info("=" * 70)
    logger.info("INICIANDO SINCRONIZAÇÃO DA TABELA LY_GRADE")
    logger.info("Início: %s", datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
    logger.info("=" * 70)

    inicio = time.time()

    # 1. Banco
    LyGradeModel.create_table()
    resumo_inicial = LyGradeModel.get_summary()
    logger.info("Resumo inicial: %s", resumo_inicial)

    # 2. API (GET)
    client = get_grade_client()
    grades_api = client.get_grades()

    if not grades_api:
        logger.warning("Nenhuma grade retornada pela API")
        return True

    logger.info("Total retornado pela API: %s", len(grades_api))

    # 3. Validação
    grades_validas, grades_invalidas = validar_grades(grades_api)

    logger.info("Grades válidas: %s", len(grades_validas))
    if grades_invalidas:
        logger.warning("Grades inválidas descartadas: %s", grades_invalidas)

    if not grades_validas:
        logger.warning("Nenhuma grade válida para inserção")
        return True

    # Amostra
    amostra = grades_validas[0]
    logger.info(
        "Amostra | Curriculo=%s | Curso=%s | Disciplina=%s",
        amostra.get("curriculo"),
        amostra.get("curso"),
        amostra.get("disciplina"),
    )

    log_estatisticas(grades_validas)

    # 4. Banco local
    logger.info("Limpando tabela LY_GRADE")
    LyGradeModel.clear_table()

    logger.info("Inserindo %s grades", len(grades_validas))
    inseridas = LyGradeModel.batch_insert(grades_validas)

    # 5. Resumo final
    tempo_total = time.time() - inicio
    resumo_final = LyGradeModel.get_summary()

    logger.info("=" * 70)
    logger.info("RESUMO FINAL")
    logger.info("Inseridas: %s", inseridas)
    logger.info("Resumo final: %s", resumo_final)
    logger.info("Tempo total: %.2f s", tempo_total)
    logger.info("Taxa: %.2f grades/s", inseridas / tempo_total)
    logger.info("=" * 70)

    return inseridas == len(grades_validas)


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
        sucesso = sincronizar_grades()
        return 0 if sucesso else 1

    except KeyboardInterrupt:
        logger.warning("Processo interrompido pelo usuário")
        return 1

    except Exception:
        logger.exception("Erro inesperado na sincronização")
        return 1


if __name__ == "__main__":
    sys.exit(main())
