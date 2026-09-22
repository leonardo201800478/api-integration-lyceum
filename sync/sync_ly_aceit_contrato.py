#!/usr/bin/env python3
"""
Sincroniza a informação de aceite de contrato dos alunos.

Fluxo:
    LY_ALUNO
        -> aluno, ano_ingresso, sem_ingresso
        -> API Lyceum /existeContratoAceito
        -> LY_ACEIT_CONTRATO

A tabela LY_ALUNO NÃO é alterada por este sincronizador.
O resultado da API é gravado no campo existeContratoAceito da
tabela dedicada LY_ACEIT_CONTRATO.
"""

import argparse
import logging
import sys
import time
from pathlib import Path
from typing import Any

import requests

# Permite executar o arquivo diretamente a partir da pasta sync/.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.api_client import BaseAPIClient
from core.database import fetch_all
from models.ly_aceit_contrato import LyAceitContratoModel
from qstione import config

logger = logging.getLogger(__name__)


class ContratoAPIClient(BaseAPIClient):
    """Cliente da API para consulta do aceite de contrato."""

    def consultar_contrato(
        self,
        cod_aluno: str,
        ano: int,
        periodo: int,
    ) -> bool | None:
        """
        Consulta se o aluno possui contrato aceito na API.

        Args:
            cod_aluno: Código/matrícula do aluno.
            ano: Ano da matrícula.
            periodo: Período/semestre da matrícula.

        Returns:
            True: contrato aceito.
            False: contrato não aceito.
            None: resposta inválida ou erro de comunicação.
        """
        endpoint = (
            f"/matricula/codAluno/{cod_aluno}"
            f"/ano/{ano}"
            f"/periodo/{periodo}"
            "/existeContratoAceito"
        )

        try:
            data: Any = self.get(endpoint, params=None)

            if isinstance(data, dict):
                valor = data.get("existeContratoAceito")

                if isinstance(valor, bool):
                    return valor

                # Aceita também S/N caso a API devolva o valor nesse formato.
                if isinstance(valor, str):
                    valor_normalizado = valor.strip().upper()

                    if valor_normalizado == "S":
                        return True

                    if valor_normalizado == "N":
                        return False

            logger.warning(
                "Sem retorno válido para %s/%s/%s",
                cod_aluno,
                ano,
                periodo,
            )
            return None

        except requests.exceptions.Timeout:
            logger.warning(
                "Timeout ao consultar contrato %s/%s/%s",
                cod_aluno,
                ano,
                periodo,
            )
            return None

        except requests.exceptions.RequestException as exc:
            logger.warning(
                "Erro HTTP ao consultar contrato %s/%s/%s: %s",
                cod_aluno,
                ano,
                periodo,
                exc,
            )
            return None


def atualizar_aceite_contrato(
    filtro_ano: int | None = None,
    filtro_periodo: int | None = None,
    api_base_url: str | None = None,
    debug: bool = False,
) -> dict[str, Any]:
    """
    Consulta o aceite de contrato para os alunos de LY_ALUNO e grava
    o resultado em LY_ACEIT_CONTRATO.

    Args:
        filtro_ano: Se informado, processa somente esse ano_ingresso.
        filtro_periodo: Se informado, processa somente esse sem_ingresso.
        api_base_url: URL base da API. Quando informado, sobrescreve
            config.LYCEUM_BASE_URL.
        debug: Mantido por compatibilidade com a execução do sincronizador.

    Returns:
        Dicionário com o resultado da execução.
    """
    inicio = time.perf_counter()

    if api_base_url:
        config.LYCEUM_BASE_URL = api_base_url.rstrip("/")

    if debug:
        logger.setLevel(logging.DEBUG)

    logger.info("ATUALIZANDO ACEITE_CONTRATO NA TABELA LY_ACEIT_CONTRATO")

    # Garante que a tabela de destino exista.
    if not LyAceitContratoModel.create_table():
        logger.error(
            "Não foi possível criar/verificar a tabela %s.",
            LyAceitContratoModel.TABLE_NAME,
        )

        return {
            "success": False,
            "total_alunos": 0,
            "atualizados": 0,
            "erros": 1,
            "tempo_total": time.perf_counter() - inicio,
        }

    query = """
        SELECT
            [aluno],
            [ano_ingresso],
            [sem_ingresso]
        FROM [LY_ALUNO]
        WHERE [ano_ingresso] IS NOT NULL
          AND [sem_ingresso] IS NOT NULL
    """

    params: list[int] = []

    if filtro_ano is not None:
        query += "\n          AND [ano_ingresso] = ?"
        params.append(filtro_ano)

    if filtro_periodo is not None:
        query += "\n          AND [sem_ingresso] = ?"
        params.append(filtro_periodo)

    query += "\n        ORDER BY [aluno]"

    try:
        rows = fetch_all(query, tuple(params))
    except Exception:
        logger.exception("Erro ao consultar os alunos em LY_ALUNO.")

        return {
            "success": False,
            "total_alunos": 0,
            "atualizados": 0,
            "erros": 1,
            "tempo_total": time.perf_counter() - inicio,
        }

    total_alunos = len(rows) if rows else 0

    logger.info(
        "Alunos encontrados na tabela LY_ALUNO: %s",
        total_alunos,
    )

    if not rows:
        logger.info(
            "Nenhum aluno com ano_ingresso e sem_ingresso definidos."
        )

        return {
            "success": True,
            "total_alunos": 0,
            "atualizados": 0,
            "erros": 0,
            "tempo_total": 0.0,
        }

    api_client = ContratoAPIClient()

    atualizados = 0
    erros = 0

    for row in rows:
        cod_aluno = row[0]
        ano_ingresso = row[1]
        sem_ingresso = row[2]

        if cod_aluno is None or ano_ingresso is None or sem_ingresso is None:
            erros += 1
            logger.warning(
                "Registro ignorado por dados incompletos: %s",
                row,
            )
            continue

        cod_aluno = str(cod_aluno).strip()

        try:
            ano = int(ano_ingresso)
            periodo = int(sem_ingresso)
        except (TypeError, ValueError):
            erros += 1
            logger.warning(
                "Ano/período inválido para aluno %s: ano=%r período=%r",
                cod_aluno,
                ano_ingresso,
                sem_ingresso,
            )
            continue

        logger.debug(
            "Consultando contrato: %s/%s/%s",
            cod_aluno,
            ano,
            periodo,
        )

        aceito = api_client.consultar_contrato(
            cod_aluno,
            ano,
            periodo,
        )

        if aceito is None:
            erros += 1
            continue

        valor_aceite = "S" if aceito else "N"

        dados = {
            "codAluno": cod_aluno,
            "ano": ano,
            "periodo": periodo,
            "existeContratoAceito": valor_aceite,
        }

        try:
            sucesso = LyAceitContratoModel.upsert(dados)

            if sucesso:
                atualizados += 1
                logger.debug(
                    "Contrato atualizado: %s/%s/%s = %s",
                    cod_aluno,
                    ano,
                    periodo,
                    valor_aceite,
                )
            else:
                erros += 1
                logger.warning(
                    "Falha ao gravar contrato: %s/%s/%s",
                    cod_aluno,
                    ano,
                    periodo,
                )

        except Exception:
            erros += 1
            logger.exception(
                "Erro SQL ao atualizar contrato do aluno %s/%s/%s",
                cod_aluno,
                ano,
                periodo,
            )

        delay = getattr(
            config,
            "API_DELAY_BETWEEN_REQUESTS",
            0,
        )

        if delay > 0:
            time.sleep(delay)

    tempo_total = time.perf_counter() - inicio

    logger.info("=" * 80)
    logger.info("ATUALIZAÇÃO CONCLUÍDA")
    logger.info("Alunos processados: %s", total_alunos)
    logger.info("Atualizados com sucesso: %s", atualizados)
    logger.info(
        "Erros (consultas sem retorno/erro SQL): %s",
        erros,
    )
    logger.info("Tempo total: %.2fs", tempo_total)
    logger.info("=" * 80)

    return {
        "success": erros == 0,
        "total_alunos": total_alunos,
        "atualizados": atualizados,
        "erros": erros,
        "tempo_total": tempo_total,
    }


def parse_args() -> argparse.Namespace:
    """Processa os argumentos da linha de comando."""
    parser = argparse.ArgumentParser(
        description=(
            "Sincroniza o aceite de contrato dos alunos "
            "para a tabela LY_ACEIT_CONTRATO."
        )
    )

    parser.add_argument(
        "--ano",
        type=int,
        help="Filtra pelo ano_ingresso do aluno.",
    )

    parser.add_argument(
        "--periodo",
        type=int,
        help="Filtra pelo sem_ingresso do aluno.",
    )

    parser.add_argument(
        "--api-url",
        help="URL base da API do Lyceum.",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Ativa logs em nível DEBUG.",
    )

    return parser.parse_args()


def main() -> int:
    """Ponto de entrada do sincronizador."""
    args = parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format=(
            "%(asctime)s | %(levelname)s | "
            "%(name)s | %(message)s"
        ),
    )

    resultado = atualizar_aceite_contrato(
        filtro_ano=args.ano,
        filtro_periodo=args.periodo,
        api_base_url=args.api_url,
        debug=args.debug,
    )

    return 0 if resultado["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
