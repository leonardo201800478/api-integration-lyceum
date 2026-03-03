# lxp/exportadores/exp_004_desenturmar_alunos_cursos_livres_ead.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import os
import pandas as pd
from core.logger import logger
from core.database import get_db_connection

# Constantes com valores fixos (UUIDs e IDs) – mesmos utilizados no arquivo de enturmação
EXTERNAL_CLASS_SUBJECT_ID = 'd575b0e5-9193-4737-bdc2-567f5bf246f7'
EXTERNAL_CURRICULUM_ID = '998202621'
EXTERNAL_PERIOD_ID = 'ed45c7d0-6e6e-466b-b9d1-43fcd6cbd9d4'
EXTERNAL_ENROLLMENT_STATUS_ID = 'eccd4f88-229c-4458-8177-cacc85cbdbb8'

def run() -> bool:
    """
    Gera arquivo CSV para desenturmar alunos inativos (sit_aluno <> 'Ativo' e unidade_ensino <> '002').
    O arquivo gerado segue o formato enrollment-class-subject.unifoa2.delete.csv,
    com os mesmos campos do arquivo de enturmação, utilizando valores fixos para os demais campos.
    """
    logger.info("=== INÍCIO DA GERAÇÃO DE ARQUIVO DE DESENTURMAÇÃO (DELETE) ===")
    try:
        # Garantir diretório de saída
        os.makedirs('exportacoes/lxp', exist_ok=True)

        # --- Consulta no banco Lyceum (tabela LY_ALUNO) ---
        logger.info("Conectando ao banco Lyceum para buscar alunos inativos...")
        query_lyceum = f"""
            SELECT 
                A.aluno AS externalEnrollmentId,
                '{EXTERNAL_CLASS_SUBJECT_ID}' AS externalClassSubjectId,
                '{EXTERNAL_CURRICULUM_ID}' AS externalCurriculumId,
                '{EXTERNAL_PERIOD_ID}' AS externalPeriodId,
                '' AS startDate,
                '' AS endDate,
                '{EXTERNAL_ENROLLMENT_STATUS_ID}' AS externalEnrollmentClassSubjectStatusId,
                '' AS externalEnrollmentTypeId,
                '' AS "ext.info.tags"
            FROM LY_ALUNO A
            WHERE A.sit_aluno <> 'Ativo'
            AND A.unidade_ensino = '002'
            ORDER BY externalEnrollmentId
        """
        # Usa conexão com o banco 'lyceum.tbl'
        with get_db_connection('lyceum.tbl') as conn:
            df = pd.read_sql_query(query_lyceum, conn)
        logger.info(f"{len(df)} registros obtidos da tabela LY_ALUNO (alunos inativos).")

        if df.empty:
            logger.warning("Nenhum aluno inativo encontrado. Nenhum arquivo de delete será gerado.")
            # Ainda assim, podemos criar um arquivo vazio? Normalmente não é necessário.
            return True

        # --- Geração do CSV ---
        logger.info("Gerando CSV de delete...")
        colunas = ['externalEnrollmentId', 'externalClassSubjectId', 'externalCurriculumId',
                   'externalPeriodId', 'startDate', 'endDate', 
                   'externalEnrollmentClassSubjectStatusId', 'externalEnrollmentTypeId',
                   'ext.info.tags']
        df_csv = df[colunas].copy()
        df_csv = df_csv.fillna('')  # Garantir que campos vazios fiquem como string vazia
        caminho = 'exportacoes/lxp/enrollment-class-subject.unifoa2.delete.csv'
        df_csv.to_csv(caminho, sep=';', index=False, encoding='utf-8-sig')
        logger.info(f"Arquivo CSV salvo em: {caminho}")

        logger.info("Geração concluída com sucesso.")
        return True

    except Exception as e:
        logger.exception(f"Exceção não tratada no run(): {e}")
        return False

if __name__ == "__main__":
    sys.exit(0 if run() else 1)