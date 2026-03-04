# lxp/exportadores/exp_003_enrollment.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import os
import pandas as pd
from core.logger import logger
from core.database import get_db_connection, execute_query, fetch_one

# Constantes com valores fixos (UUIDs e IDs)
EXTERNAL_CLASS_SUBJECT_ID = 'd575b0e5-9193-4737-bdc2-567f5bf246f7'
EXTERNAL_CURRICULUM_ID = '998202621'
EXTERNAL_PERIOD_ID = 'ed45c7d0-6e6e-466b-b9d1-43fcd6cbd9d4'
EXTERNAL_ENROLLMENT_STATUS_ID = 'eccd4f88-229c-4458-8177-cacc85cbdbb8'

def criar_tabela_enrollment():
    """Cria a tabela lxp_enrollment_class_subject no banco lxp se ela não existir."""
    logger.info("Verificando existência da tabela lxp_enrollment_class_subject...")
    try:
        query_check = """
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = 'lxp_enrollment_class_subject'
        """
        result = fetch_one(query_check, db_path='lxp')
        if result is None:
            logger.error("fetch_one retornou None. Possível erro de conexão.")
            return False
        exists = result[0] > 0
        if not exists:
            logger.info("Tabela não encontrada. Criando...")
            create_sql = """
            CREATE TABLE lxp_enrollment_class_subject (
                externalEnrollmentId NVARCHAR(50) PRIMARY KEY,
                externalClassSubjectId NVARCHAR(50) NOT NULL,
                externalCurriculumId NVARCHAR(50) NOT NULL,
                externalPeriodId NVARCHAR(50) NULL,
                startDate DATE NULL,
                endDate DATE NULL,
                externalEnrollmentClassSubjectStatusId NVARCHAR(50) NOT NULL,
                externalEnrollmentTypeId NVARCHAR(50) NULL,
                ext_info_tags NVARCHAR(50) NULL,
                created_at DATETIME DEFAULT GETDATE(),
                updated_at DATETIME DEFAULT GETDATE()
            );
            """
            execute_query(create_sql, db_path='lxp')
            logger.info("Tabela lxp_enrollment_class_subject criada com sucesso.")
        else:
            logger.info("Tabela já existe.")
        return True
    except Exception as e:
        logger.exception(f"Erro ao verificar/criar tabela: {e}")
        return False

def upsert_enrollment_batch(df):
    """
    Insere ou atualiza um lote de enturmações na tabela lxp_enrollment_class_subject.
    Utiliza MERGE para cada linha.
    """
    logger.info(f"Iniciando upsert de {len(df)} registros...")
    success_count = 0
    for _, row in df.iterrows():
        try:
            merge_sql = """
            MERGE lxp_enrollment_class_subject AS target
            USING (SELECT ? AS externalEnrollmentId) AS source
            ON target.externalEnrollmentId = source.externalEnrollmentId
            WHEN MATCHED THEN
                UPDATE SET
                    externalClassSubjectId = ?,
                    externalCurriculumId = ?,
                    externalPeriodId = ?,
                    startDate = ?,
                    endDate = ?,
                    externalEnrollmentClassSubjectStatusId = ?,
                    externalEnrollmentTypeId = ?,
                    ext_info_tags = ?,
                    updated_at = GETDATE()
            WHEN NOT MATCHED THEN
                INSERT (externalEnrollmentId, externalClassSubjectId, externalCurriculumId,
                        externalPeriodId, startDate, endDate,
                        externalEnrollmentClassSubjectStatusId, externalEnrollmentTypeId,
                        ext_info_tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """
            params = (
                row['externalEnrollmentId'],  # source ON
                row['externalClassSubjectId'],
                row['externalCurriculumId'],
                row['externalPeriodId'],
                row['startDate'] if pd.notna(row['startDate']) else None,
                row['endDate'] if pd.notna(row['endDate']) else None,
                row['externalEnrollmentClassSubjectStatusId'],
                row['externalEnrollmentTypeId'] if pd.notna(row['externalEnrollmentTypeId']) else None,
                row['ext.info.tags'] if pd.notna(row['ext.info.tags']) else None,
                row['externalEnrollmentId'],  # INSERT
                row['externalClassSubjectId'],
                row['externalCurriculumId'],
                row['externalPeriodId'],
                row['startDate'] if pd.notna(row['startDate']) else None,
                row['endDate'] if pd.notna(row['endDate']) else None,
                row['externalEnrollmentClassSubjectStatusId'],
                row['externalEnrollmentTypeId'] if pd.notna(row['externalEnrollmentTypeId']) else None,
                row['ext.info.tags'] if pd.notna(row['ext.info.tags']) else None
            )
            execute_query(merge_sql, params, db_path='lxp')
            success_count += 1
        except Exception as e:
            logger.error(f"Erro no upsert para externalEnrollmentId={row['externalEnrollmentId']}: {e}")
    logger.info(f"Upsert concluído: {success_count}/{len(df)} registros processados.")
    return success_count == len(df)

def run() -> bool:
    """
    Exporta dados de enturmações para o arquivo enrollment-class-subject.unifoa2.csv
    e sincroniza a tabela lxp_enrollment_class_subject no banco lxp.
    """
    logger.info("=== INÍCIO DA EXPORTAÇÃO DE ENTURMAÇÕES ===")
    try:
        # Garantir diretório de saída
        os.makedirs('exportacoes/lxp', exist_ok=True)

        # --- Consulta no banco Lyceum (tabela LY_ALUNO) ---
        logger.info("Conectando ao banco Lyceum para buscar alunos ativos...")
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
            WHERE A.sit_aluno = 'Ativo'
            AND a.unidade_ensino = '002'
            ORDER BY externalEnrollmentId
        """
        # Usa conexão com o banco 'lyceum'
        with get_db_connection('lyceum') as conn:
            df = pd.read_sql_query(query_lyceum, conn)
        logger.info(f"{len(df)} registros obtidos da tabela LY_ALUNO.")

        if df.empty:
            logger.warning("Nenhum aluno ativo encontrado. Nada a exportar.")
            # Ainda assim, criar a tabela se não existir
            criar_tabela_enrollment()
            return True

        # --- Sincronização com a tabela lxp_enrollment_class_subject ---
        if not criar_tabela_enrollment():
            logger.error("Falha na criação/verificação da tabela. Abortando.")
            return False

        if not upsert_enrollment_batch(df):
            logger.error("Falha no upsert em lote. Abortando.")
            return False

        # --- Geração do CSV ---
        logger.info("Gerando CSV...")
        colunas = ['externalEnrollmentId', 'externalClassSubjectId', 'externalCurriculumId',
                   'externalPeriodId', 'startDate', 'endDate', 
                   'externalEnrollmentClassSubjectStatusId', 'externalEnrollmentTypeId',
                   'ext.info.tags']
        df_csv = df[colunas].copy()
        df_csv = df_csv.fillna('')  # Garantir que campos vazios fiquem como string vazia
        caminho = 'exportacoes/lxp/enrollment-class-subject.unifoa2.csv'
        df_csv.to_csv(caminho, sep=';', index=False, encoding='utf-8-sig')
        logger.info(f"Arquivo CSV salvo em: {caminho}")

        logger.info("Exportação concluída com sucesso.")
        return True

    except Exception as e:
        logger.exception(f"Exceção não tratada no run(): {e}")
        return False

if __name__ == "__main__":
    sys.exit(0 if run() else 1)