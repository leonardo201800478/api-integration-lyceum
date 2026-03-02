#!/usr/bin/env python3
"""
sync/sync_ly_docentes.py
Sincronização FULL REFRESH da tabela LY_DOCENTE.

Utiliza o cliente DocenteAPICliente (já implementado) para obter todos os docentes
via paginação automática com parâmetros 'page' e 'size' (configurados em core.config).

REGRAS DE NEGÓCIO:
1. Campos obrigatórios: cpf e num_func (não vazios).
2. CPF deve ser normalizado (apenas 11 dígitos).
3. E-mail de docente deve ter domínio @foa.org.br (se presente, apenas loga inválidos).
4. DOCENTE PADRÃO (matrícula "1") é automaticamente descartado – não é real.
5. Docentes com e-mail inválido são registrados em log, mas NÃO são excluídos (apenas o padrão é excluído).
"""

import sys
import os
import time
import logging
import re
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
from core.api_client import DocenteAPIClient
from models.ly_docente import LyDocenteModel

# -----------------------------------------------------------------------------
# Logger
# -----------------------------------------------------------------------------
logger = logging.getLogger("sync_ly_docente")

# -----------------------------------------------------------------------------
# CONSTANTES
# -----------------------------------------------------------------------------
REQUIRED_FIELDS = ["cpf", "num_func"]       # Campos obrigatórios
DOMINIO_DOCENTE = "foa.org.br"              # Domínio exclusivo para docentes
DOCENTE_PADRAO_MATRICULA = "1"             # Matrícula do docente fictício (deve ser excluído)
DEPTOS_TOP_N = 5
TITULOS_TOP_N = 5

# -----------------------------------------------------------------------------
# FUNÇÕES AUXILIARES
# -----------------------------------------------------------------------------
def normalizar_cpf(cpf: Any) -> str:
    """Remove caracteres não numéricos e retorna apenas dígitos."""
    if not cpf:
        return ""
    return re.sub(r"\D", "", str(cpf))


def validar_email_docente(email: Any) -> Tuple[bool, str]:
    """
    Valida e-mail de docente: deve terminar com @foa.org.br.
    Retorna (True, email_normalizado) se válido;
    (False, email_original) se inválido; (False, "") se vazio/nulo.
    """
    if not email or not isinstance(email, str):
        return False, ""
    email = email.strip().lower()
    if email.endswith(f"@{DOMINIO_DOCENTE}"):
        return True, email
    return False, email


def validar_docentes(docentes: List[Dict[str, Any]]) -> Tuple[List[Dict], int, int, List[Dict]]:
    """
    Aplica todas as validações e transformações nos docentes.

    Args:
        docentes: Lista bruta da API.

    Returns:
        - docentes_validos: lista de dicionários prontos para inserção.
        - total_descartados: soma de todos os descartes (campos obrigatórios, CPF inválido, docente padrão).
        - emails_invalidos: lista de docentes (não descartados) com e-mail inválido.
    """
    validos = []
    descartados = 0
    emails_invalidos = []

    for doc in docentes:
        # ---------------------------------------------------------------------
        # 1. Descarte do docente padrão (matrícula "1")
        # ---------------------------------------------------------------------
        if str(doc.get("num_func")) == DOCENTE_PADRAO_MATRICULA:
            logger.debug("Docente padrão descartado (matrícula %s)", DOCENTE_PADRAO_MATRICULA)
            descartados += 1
            continue

        # ---------------------------------------------------------------------
        # 2. Validação de campos obrigatórios
        # ---------------------------------------------------------------------
        if not all(doc.get(campo) for campo in REQUIRED_FIELDS):
            logger.debug("Docente descartado (campos obrigatórios ausentes): %s",
                         {c: doc.get(c) for c in REQUIRED_FIELDS})
            descartados += 1
            continue

        # ---------------------------------------------------------------------
        # 3. Normalização e validação do CPF
        # ---------------------------------------------------------------------
        cpf_normalizado = normalizar_cpf(doc.get("cpf"))
        if len(cpf_normalizado) != 11:
            logger.debug("Docente descartado (CPF inválido após normalização): %s", doc.get("num_func"))
            descartados += 1
            continue
        doc["cpf"] = cpf_normalizado   # substitui pelo valor limpo

        # ---------------------------------------------------------------------
        # 4. Validação de e-mail (não descarta, apenas loga)
        # ---------------------------------------------------------------------
        email_valido, email_limpo = validar_email_docente(doc.get("email"))
        if not email_valido and doc.get("email"):   # só registra se existir e for inválido
            emails_invalidos.append({
                "num_func": doc.get("num_func"),
                "cpf": doc.get("cpf"),
                "email": doc.get("email")
            })
        doc["email"] = email_limpo if email_valido else doc.get("email")

        # Se chegou até aqui, docente é válido
        validos.append(doc)

    return validos, descartados, emails_invalidos


def gerar_estatisticas(docentes: List[Dict]) -> None:
    """Registra estatísticas detalhadas para auditoria."""
    if not docentes:
        return

    ativos = sum(1 for d in docentes if d.get("ativo") == "S")
    inativos = len(docentes) - ativos

    logger.info("📊 Estatísticas dos docentes válidos:")
    logger.info("   - Total: %s", len(docentes))
    logger.info("   - Ativos: %s", ativos)
    logger.info("   - Inativos: %s", inativos)

    # Top N departamentos
    deptos = Counter(d.get("depto", "Não informado") for d in docentes)
    logger.info("   - Top %d departamentos:", DEPTOS_TOP_N)
    for depto, qtd in deptos.most_common(DEPTOS_TOP_N):
        logger.info("       • %s: %s", depto, qtd)

    # Top N titulações
    titulos = Counter(d.get("titulacao", "Não informado") for d in docentes)
    logger.info("   - Top %d titulações:", TITULOS_TOP_N)
    for tit, qtd in titulos.most_common(TITULOS_TOP_N):
        logger.info("       • %s: %s", tit, qtd)

    # Chaves compostas (cpf + num_func) – duplicatas
    chaves = [f"{d['cpf']}-{d['num_func']}" for d in docentes if d.get("cpf") and d.get("num_func")]
    total_chaves = len(chaves)
    unicas = len(set(chaves))
    logger.info("   - Chaves (cpf+num_func): %s únicas de %s", unicas, total_chaves)
    if total_chaves > unicas:
        logger.warning("   ⚠️  %s duplicatas de chave encontradas!", total_chaves - unicas)


def log_emails_invalidos(docentes_com_email_invalido: List[Dict]) -> None:
    """Registra em log a matrícula e CPF de cada docente com e-mail inválido."""
    if not docentes_com_email_invalido:
        return

    logger.warning("📧 Docentes com e-mail inválido (domínio diferente de @%s):", DOMINIO_DOCENTE)
    for doc in docentes_com_email_invalido:
        logger.warning("   - Matrícula: %s | CPF: %s | E-mail fornecido: %s",
                       doc.get("num_func"), doc.get("cpf"), doc.get("email"))


# -----------------------------------------------------------------------------
# FUNÇÃO PRINCIPAL (chamada pelo run_all_syncs.py)
# -----------------------------------------------------------------------------
def run() -> bool:
    logger.info("=" * 70)
    logger.info("🔄 INÍCIO DA SINCRONIA: LY_DOCENTE")
    logger.info("⏱️  %s", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    logger.info("=" * 70)

    tempo_inicio = time.time()

    try:
        # 1. Tabela
        LyDocenteModel.create_table()
        resumo_inicial = LyDocenteModel.get_summary()
        logger.info("📋 Resumo inicial da tabela: %s", resumo_inicial)

        # 2. API
        logger.info("📡 Conectando à API Lyceum (endpoint: docente)...")
        cliente = DocenteAPIClient()
        docentes_brutos = cliente.get_docentes()

        if docentes_brutos is None:
            logger.error("❌ Cliente retornou None – falha na requisição.")
            return False

        if not docentes_brutos:
            logger.warning("⚠️  Nenhum docente retornado pela API. Nada a sincronizar.")
            LyDocenteModel.clear_table()
            logger.info("✅ Tabela esvaziada (sem dados na API).")
            return True

        logger.info("📦 Total bruto recebido da API: %s registros", len(docentes_brutos))

        # 3. Validação completa
        docentes_validos, total_descartados, emails_invalidos = validar_docentes(docentes_brutos)

        logger.info("✅ Docentes válidos: %s", len(docentes_validos))
        if total_descartados > 0:
            logger.warning("⚠️  Docentes descartados: %s (campos obrigatórios, CPF inválido ou docente padrão)",
                           total_descartados)

        # Log de e-mails inválidos (apenas entre os válidos)
        log_emails_invalidos(emails_invalidos)

        if not docentes_validos:
            logger.warning("🚫 Nenhum docente válido para inserção. Tabela será esvaziada.")
            LyDocenteModel.clear_table()
            return True

        # 4. Amostra e estatísticas
        amostra = docentes_validos[0]
        logger.info("🔍 Amostra (primeiro registro válido):")
        logger.info("   - CPF: %s", amostra.get("cpf"))
        logger.info("   - NUM_FUNC: %s", amostra.get("num_func"))
        logger.info("   - NOME: %s", amostra.get("nome_compl", "---"))
        logger.info("   - E-MAIL: %s", amostra.get("email", "---"))
        logger.info("   - ATIVO: %s", amostra.get("ativo", "---"))

        gerar_estatisticas(docentes_validos)

        # 5. Banco de dados
        logger.info("🧹 Limpando tabela LY_DOCENTE...")
        linhas_removidas = LyDocenteModel.clear_table()
        logger.info("   - Registros removidos: %s", linhas_removidas)

        logger.info("💾 Inserindo %s docentes no banco...", len(docentes_validos))
        inseridos = LyDocenteModel.batch_insert(docentes_validos)

        if inseridos != len(docentes_validos):
            logger.error("❌ Inserção incompleta: %s de %s registros inseridos.",
                         inseridos, len(docentes_validos))
            return False

        # 6. Finalização
        tempo_total = time.time() - tempo_inicio
        taxa = inseridos / tempo_total if tempo_total > 0 else 0
        resumo_final = LyDocenteModel.get_summary()

        logger.info("=" * 70)
        logger.info("✅ SINCRONIA CONCLUÍDA COM SUCESSO")
        logger.info("📈 Resumo final da tabela: %s", resumo_final)
        logger.info("⏱️  Tempo total: %.2f s", tempo_total)
        logger.info("⚡ Taxa de inserção: %.2f registros/s", taxa)
        logger.info("=" * 70)

        return True

    except Exception as e:
        logger.exception("❌ Falha crítica durante a sincronia de docentes")
        return False


# -----------------------------------------------------------------------------
# EXECUÇÃO ISOLADA
# -----------------------------------------------------------------------------
def main() -> int:
    if not all([config.LYCEUM_BASE_URL, config.LYCEUM_USERNAME, config.LYCEUM_PASSWORD]):
        logger.error("Configurações da API Lyceum incompletas. Verifique o arquivo .env.")
        return 1

    sucesso = run()
    return 0 if sucesso else 1


if __name__ == "__main__":
    sys.exit(main())