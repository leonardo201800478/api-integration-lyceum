#!/usr/bin/env python3
"""
Sincronização FULL REFRESH da tabela LY_GRADE.

Utiliza o cliente GradeAPIClient via factory (get_grade_client) para obter todas as grades
via paginação automática com parâmetros 'page' e 'size' (configurados em core.config).

REGRAS DE NEGÓCIO:
1. Campos obrigatórios: curriculo, curso, disciplina (não vazios).
2. Registros com campos obrigatórios ausentes são descartados (log em DEBUG).
3. Estatísticas de auditoria: obrigatórias/optativas, top currículos, top cursos, distribuição por série.
4. FULL REFRESH: limpa a tabela e insere todos os dados válidos.
"""

import sys
import os
import time
import logging
from datetime import datetime
from collections import Counter
from pathlib import Path
from typing import List, Dict, Any, Tuple

# -----------------------------------------------------------------------------
# AJUSTE DE PATH PARA IMPORTAÇÃO DOS MÓDULOS INTERNOS
# -----------------------------------------------------------------------------
RAIZ_PROJETO = Path(__file__).resolve().parent.parent
if str(RAIZ_PROJETO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROJETO))
    os.chdir(RAIZ_PROJETO)

# -----------------------------------------------------------------------------
# IMPORTAÇÕES INTERNAS
# -----------------------------------------------------------------------------
from core.config import config
from core.api_client import get_grade_client
from models.ly_grade import LyGradeModel

# -----------------------------------------------------------------------------
# Logger – herda configuração do executor central (sem basicConfig)
# -----------------------------------------------------------------------------
logger = logging.getLogger("sync_ly_grade")

# -----------------------------------------------------------------------------
# CONSTANTES
# -----------------------------------------------------------------------------
REQUIRED_FIELDS = ["curriculo", "curso", "disciplina"]  # Campos obrigatórios
TOP_N = 5  # Quantidade de itens nos rankings

# -----------------------------------------------------------------------------
# FUNÇÕES AUXILIARES
# -----------------------------------------------------------------------------
def validar_grades(grades: List[Dict[str, Any]]) -> Tuple[List[Dict], int]:
    """
    Filtra grades com campos obrigatórios presentes e não vazios.
    Retorna (lista_de_grades_válidas, quantidade_descartadas).
    """
    validas = []
    descartadas = 0

    for g in grades:
        if all(g.get(campo) for campo in REQUIRED_FIELDS):
            validas.append(g)
        else:
            descartadas += 1
            logger.debug("Grade descartada (campos obrigatórios ausentes): %s",
                         {c: g.get(c) for c in REQUIRED_FIELDS})

    return validas, descartadas


def gerar_estatisticas(grades: List[Dict]) -> None:
    """Registra estatísticas detalhadas para auditoria."""
    if not grades:
        logger.info("Nenhuma grade válida para análise.")
        return

    obrigatorias = sum(1 for g in grades if g.get("obrigatoria") == "S")
    optativas = len(grades) - obrigatorias

    logger.info("📊 Estatísticas das grades válidas:")
    logger.info("   - Total: %s", len(grades))
    logger.info("   - Obrigatórias: %s", obrigatorias)
    logger.info("   - Optativas: %s", optativas)

    # Top N currículos
    curriculos = Counter(g.get("curriculo", "Não informado") for g in grades)
    logger.info("   - Top %d currículos:", TOP_N)
    for cur, qtd in curriculos.most_common(TOP_N):
        logger.info("       • %s: %s", cur, qtd)

    # Top N cursos
    cursos = Counter(g.get("curso", "Não informado") for g in grades)
    logger.info("   - Top %d cursos:", TOP_N)
    for curso, qtd in cursos.most_common(TOP_N):
        logger.info("       • %s: %s", curso, qtd)

    # Distribuição por série ideal
    series = Counter(g.get("serie_ideal", "Não informado") for g in grades)
    logger.info("   - Distribuição por série ideal:")
    for serie, qtd in sorted(series.items()):
        logger.info("       • Série %s: %s", serie, qtd)

    # Chaves compostas (curriculo+curso+disciplina) – duplicatas
    chaves = [
        f"{g.get('curriculo')}-{g.get('curso')}-{g.get('disciplina')}"
        for g in grades
    ]
    total_chaves = len(chaves)
    unicas = len(set(chaves))
    logger.info("   - Chaves (curriculo-curso-disciplina): %s únicas de %s", unicas, total_chaves)
    if total_chaves > unicas:
        logger.warning("   ⚠️  %s duplicatas de chave encontradas!", total_chaves - unicas)


# -----------------------------------------------------------------------------
# FUNÇÃO PRINCIPAL – CHAMADA PELO RUN_ALL_SYNC
# -----------------------------------------------------------------------------
def run() -> bool:
    """
    Executa o fluxo completo de sincronização da tabela LY_GRADE.
    Retorna True em caso de sucesso (ou ausência de dados), False em falha crítica.
    """
    logger.info("=" * 70)
    logger.info("🔄 INÍCIO DA SINCRONIA: LY_GRADE")
    logger.info("⏱️  %s", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    logger.info("=" * 70)

    tempo_inicio = time.time()

    try:
        # ---------------------------------------------------------------------
        # 1. Garantir existência da tabela
        # ---------------------------------------------------------------------
        LyGradeModel.create_table()
        resumo_inicial = LyGradeModel.get_summary()
        logger.info("📋 Resumo inicial da tabela: %s", resumo_inicial)

        # ---------------------------------------------------------------------
        # 2. Consumir API Lyceum – GradeAPIClient.get_grades()
        #    A paginação já está implementada no cliente (page, size).
        # ---------------------------------------------------------------------
        logger.info("📡 Conectando à API Lyceum (endpoint: grades)...")
        cliente = get_grade_client()
        grades_brutas = cliente.get_grades()

        if grades_brutas is None:
            logger.error("❌ Cliente retornou None – falha na requisição.")
            return False

        if not grades_brutas:
            logger.warning("⚠️  Nenhuma grade retornada pela API. Nada a sincronizar.")
            LyGradeModel.clear_table()
            logger.info("✅ Tabela esvaziada (sem dados na API).")
            return True

        logger.info("📦 Total bruto recebido da API: %s registros", len(grades_brutas))

        # ---------------------------------------------------------------------
        # 3. Validação dos dados
        # ---------------------------------------------------------------------
        grades_validas, qtd_descartadas = validar_grades(grades_brutas)

        logger.info("✅ Grades válidas: %s", len(grades_validas))
        if qtd_descartadas:
            logger.warning("⚠️  Grades descartadas (campos obrigatórios ausentes): %s", qtd_descartadas)

        if not grades_validas:
            logger.warning("🚫 Nenhuma grade válida para inserção. Tabela será esvaziada.")
            LyGradeModel.clear_table()
            return True

        # ---------------------------------------------------------------------
        # 4. Amostra e estatísticas
        # ---------------------------------------------------------------------
        amostra = grades_validas[0]
        logger.info("🔍 Amostra (primeiro registro válido):")
        logger.info("   - Currículo: %s", amostra.get("curriculo"))
        logger.info("   - Curso: %s", amostra.get("curso"))
        logger.info("   - Disciplina: %s", amostra.get("disciplina"))
        logger.info("   - Obrigatória: %s", amostra.get("obrigatoria", "---"))
        logger.info("   - Série ideal: %s", amostra.get("serie_ideal", "---"))

        gerar_estatisticas(grades_validas)

        # ---------------------------------------------------------------------
        # 5. Operação no banco local (FULL REFRESH)
        # ---------------------------------------------------------------------
        logger.info("🧹 Limpando tabela LY_GRADE...")
        linhas_removidas = LyGradeModel.clear_table()
        logger.info("   - Registros removidos: %s", linhas_removidas)

        logger.info("💾 Inserindo %s grades no banco...", len(grades_validas))
        inseridas = LyGradeModel.batch_insert(grades_validas)

        if inseridas != len(grades_validas):
            logger.error("❌ Inserção incompleta: %s de %s registros inseridos.",
                         inseridas, len(grades_validas))
            return False

        # ---------------------------------------------------------------------
        # 6. Finalização e resumo
        # ---------------------------------------------------------------------
        tempo_total = time.time() - tempo_inicio
        taxa = inseridas / tempo_total if tempo_total > 0 else 0
        resumo_final = LyGradeModel.get_summary()

        logger.info("=" * 70)
        logger.info("✅ SINCRONIA CONCLUÍDA COM SUCESSO")
        logger.info("📈 Resumo final da tabela: %s", resumo_final)
        logger.info("⏱️  Tempo total: %.2f s", tempo_total)
        logger.info("⚡ Taxa de inserção: %.2f registros/s", taxa)
        logger.info("=" * 70)

        return True

    except Exception:
        logger.exception("❌ Falha crítica durante a sincronia de grades")
        return False


# -----------------------------------------------------------------------------
# EXECUÇÃO ISOLADA (para testes manuais)
# -----------------------------------------------------------------------------
def main() -> int:
    """Ponto de entrada para execução direta do script."""
    # Verifica credenciais (o cliente já faz isso, mas é uma cortesia)
    if not all([config.LYCEUM_BASE_URL, config.LYCEUM_USERNAME, config.LYCEUM_PASSWORD]):
        logger.error("Configurações da API Lyceum incompletas. Verifique o arquivo .env.")
        return 1

    sucesso = run()
    return 0 if sucesso else 1


if __name__ == "__main__":
    sys.exit(main())