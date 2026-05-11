#!/usr/bin/env python3
"""
sync/sync_ly_provas.py
Sincronizador da tabela LY_PROVA
Este sincronizador depende dos dados de LY_PROVA_DISCIP.
Para cada registro em LY_PROVA_DISCIP, tenta obter os detalhes da prova via API
(requer os parâmetros: ano, disciplina, prova, semestre, turma).

ATENÇÃO: a API de provas exige chave composta. Este sincronizador percorre
as provas-disciplinas já sincronizadas e, se encontrar os campos necessários,
faz a chamada individual.
"""

import logging
from core.api_client import get_prova_client
from models.ly_prova import LyProvaModel
from models.ly_prova_discip import LyProvaDiscipModel

logger = logging.getLogger("sync_ly_prova")

# Delay entre chamadas para não sobrecarregar a API
API_DELAY = 0.5


def run() -> bool:
    """
    Executa a sincronia de provas detalhadas.
    1. Obtém todas as provas-disciplinas do banco local.
    2. Para cada uma, extrai os campos que compõem a chave (ano, disciplina, prova, semestre, turma).
       Nota: a tabela LY_PROVA_DISCIP pode não ter ano/semestre/turma. Será necessário
       obter essas informações de outras tabelas (turmas, etc.). Se não houver, a prova não pode ser buscada.
    """
    logger.info("=" * 50)
    logger.info("Iniciando sincronização de LY_PROVA...")

    try:
        # Cria a tabela se não existir
        LyProvaModel.create_table()

        # Obtém todas as provas-disciplinas do banco
        provas_discip = LyProvaDiscipModel.get_all_provas_disciplinas()
        if not provas_discip:
            logger.warning("Nenhuma prova-disciplina encontrada no banco. Execute sync_ly_provas_disciplinas primeiro.")
            return True

        logger.info(f"Total de provas-disciplinas a processar: {len(provas_discip)}")

        client = get_prova_client()
        sucessos = 0
        falhas = 0

        for pd in provas_discip:
            # Tenta extrair os campos da chave. Precisamos de ano, disciplina, prova, semestre, turma.
            # A tabela LY_PROVA_DISCIP contém 'prova' e 'disciplina', mas não ano/semestre/turma.
            # Uma abordagem real exigiria relacionar com turmas ou outra fonte.
            # Aqui, vamos supor que esses campos venham de outro lugar (ex: parâmetros de entrada).
            # Como não temos, vamos pular este registro com aviso.
            prova_cod = pd.get('prova')
            disciplina_cod = pd.get('disciplina')

            # Exemplo: se houvesse uma tabela de turmas, poderíamos buscar as turmas que usam essa disciplina...
            # Por simplicidade, este sincronizador não fará nada e retornará False indicando que precisa de implementação adicional.
            logger.warning(f"Registro ignorado (faltam dados de turma/período): prova={prova_cod}, disciplina={disciplina_cod}")
            falhas += 1

        # Implementação real exigiria uma lógica de negócio para determinar as combinações válidas.
        # Possível fonte: tabela LY_TURMA (ano, semestre, turma, disciplina). Poderíamos fazer um JOIN.
        # Exemplo de consulta:
        # SELECT T.ano, T.semestre, T.turma, PD.prova, PD.disciplina
        # FROM LY_PROVA_DISCIP PD
        # INNER JOIN LY_TURMA T ON PD.disciplina = T.disciplina
        # WHERE T.ano IN (...) etc.
        # Mas isso depende do contexto.

        # Para não deixar o sincronizador quebrado, retornamos False indicando que precisa ser revisado.
        logger.error("Sincronizador de provas precisa ser adaptado com a lógica de negócio para obter ano/semestre/turma.")
        return False

    except Exception as e:
        logger.error(f"Erro durante sincronização: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()