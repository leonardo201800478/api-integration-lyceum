#!/usr/bin/env python3
"""
sync/sync_aceite_contrato.py
ATUALIZA O CAMPO aceite_contrato NA TABELA LY_ALUNO
- Lê alunos da tabela LY_ALUNO (local)
- Para cada aluno, utiliza ano_ingresso e sem_ingresso (como período)
- Consulta endpoint /matricula/codAluno/{aluno}/ano/{ano}/periodo/{periodo}/existeContratoAceito
- Atualiza o campo aceite_contrato na própria LY_ALUNO ('S' ou 'N')
"""

import sys
import time
import logging
import argparse
from pathlib import Path
from typing import Dict, Optional
import requests

# ---------------------------------------------------------------------
# Garantir import do projeto
# ---------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ---------------------------------------------------------------------
# Imports internos
# ---------------------------------------------------------------------
from core.api_client import BaseAPIClient
from core.database import fetch_all, execute_query
from core.config import config

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
# Cliente para a API de contrato aceito (com autenticação)
# ---------------------------------------------------------------------
class ContratoAPIClient(BaseAPIClient):
    """
    Cliente especializado para o endpoint de contrato aceito.
    Herda autenticação e configurações do BaseAPIClient.
    """

    def consultar_contrato(self, cod_aluno: str, ano: int, periodo: int) -> Optional[bool]:
        """
        Consulta se o contrato foi aceito para o aluno/ano/período.
        Retorna True/False ou None em caso de erro (404, 401, timeout, etc).
        """
        endpoint = f"/matricula/codAluno/{cod_aluno}/ano/{ano}/periodo/{periodo}/existeContratoAceito"
        try:
            data = self.get(endpoint, params=None)
            if data is None:
                return None
            if isinstance(data, dict):
                return bool(data.get('existeContratoAceito', False))
            return None
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout ao consultar {cod_aluno}/{ano}/{periodo}")
            return None
        except Exception as e:
            logger.warning(f"Erro ao consultar {cod_aluno}/{ano}/{periodo}: {e}")
            return None


# ---------------------------------------------------------------------
# Função principal
# ---------------------------------------------------------------------
def atualizar_aceite_contrato(
    filtro_ano: Optional[int] = None,
    filtro_periodo: Optional[int] = None,
    api_base_url: Optional[str] = None,
    debug: bool = False
) -> Dict:
    """
    Atualiza o campo aceite_contrato na tabela LY_ALUNO para todos os alunos
    que possuem ano_ingresso e sem_ingresso definidos.
    """
    logger.info("=" * 70)
    logger.info("ATUALIZANDO ACEITE_CONTRATO NA TABELA LY_ALUNO")
    logger.info("=" * 70)

    inicio = time.time()

    # 1. Buscar alunos da tabela LY_ALUNO (apenas com ano_ingresso e sem_ingresso)
    sql = """
        SELECT aluno, ano_ingresso, sem_ingresso
        FROM LY_ALUNO
        WHERE ano_ingresso IS NOT NULL AND sem_ingresso IS NOT NULL
    """
    params = []
    if filtro_ano is not None:
        sql += " AND ano_ingresso = ?"
        params.append(filtro_ano)
    if filtro_periodo is not None:
        sql += " AND sem_ingresso = ?"
        params.append(filtro_periodo)

    rows = fetch_all(sql, tuple(params), database_name="lyceum")
    total_alunos = len(rows)
    logger.info(f"Alunos encontrados na tabela LY_ALUNO: {total_alunos}")

    if total_alunos == 0:
        logger.warning("Nenhum aluno com ano_ingresso e sem_ingresso definidos.")
        return {
            "success": True,
            "total_alunos": 0,
            "atualizados": 0,
            "erros": 0,
            "tempo_total": 0.0,
        }

    # 2. Preparar cliente da API (com autenticação)
    client = ContratoAPIClient()

    # 3. Processar cada aluno
    atualizados = 0
    erros = 0

    for idx, (aluno, ano, sem) in enumerate(rows, start=1):
        try:
            # Converte para inteiros
            ano_int = int(ano)
            periodo = int(sem)

            if debug:
                logger.debug(f"Consultando {aluno}/{ano_int}/{periodo}")

            # Consulta API
            existe = client.consultar_contrato(aluno, ano_int, periodo)
            if existe is None:
                erros += 1
                logger.debug(f"Sem retorno para {aluno}/{ano_int}/{periodo}")
                continue

            # Define o valor a ser atualizado
            aceite = 'S' if existe else 'N'

            # Atualiza o campo na tabela LY_ALUNO
            update_sql = "UPDATE LY_ALUNO SET aceite_contrato = ? WHERE aluno = ?"
            execute_query(update_sql, (aceite, aluno), database_name="lyceum")
            atualizados += 1

            # Log de progresso
            if idx % 100 == 0:
                logger.info(f"Progresso: {idx}/{total_alunos} alunos processados.")

            # Pequeno delay para não sobrecarregar a API
            time.sleep(config.API_DELAY_BETWEEN_REQUESTS)

        except Exception as e:
            erros += 1
            logger.warning(f"Erro ao processar aluno {aluno}: {e}")

    # 4. Resumo final
    tempo_total = time.time() - inicio

    logger.info("=" * 70)
    logger.info("ATUALIZAÇÃO CONCLUÍDA")
    logger.info(f"Alunos processados: {total_alunos}")
    logger.info(f"Atualizados com sucesso: {atualizados}")
    logger.info(f"Erros (consultas sem retorno): {erros}")
    logger.info(f"Tempo total: {tempo_total:.2f}s")
    logger.info("=" * 70)

    return {
        "success": True,
        "total_alunos": total_alunos,
        "atualizados": atualizados,
        "erros": erros,
        "tempo_total": tempo_total,
    }


# ---------------------------------------------------------------------
# Parsing de argumentos
# ---------------------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(
        description="Atualiza o campo aceite_contrato na tabela LY_ALUNO"
    )
    parser.add_argument(
        "--ano",
        type=int,
        help="Filtrar alunos por ano_ingresso específico (ex: 2026)"
    )
    parser.add_argument(
        "--periodo",
        type=int,
        help="Filtrar alunos por sem_ingresso específico (ex: 1, 2, 21, 22, etc.)"
    )
    parser.add_argument(
        "--api-url",
        type=str,
        help="URL base da API (sobrescreve config.LYCEUM_BASE_URL)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Habilita logs de debug para cada requisição"
    )
    return parser.parse_args()


# ---------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------
def main():
    args = parse_args()

    if args.api_url:
        config.LYCEUM_BASE_URL = args.api_url

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info(f"Filtros: ano={args.ano}, periodo={args.periodo} (se fornecido)")

    resultado = atualizar_aceite_contrato(
        filtro_ano=args.ano,
        filtro_periodo=args.periodo,
        api_base_url=args.api_url,
        debug=args.debug
    )

    return 0 if resultado.get("success", False) else 1


if __name__ == "__main__":
    sys.exit(main())