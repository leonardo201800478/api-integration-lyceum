# lxp/exportadores/exp_001_cursos.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import os
import pandas as pd
from core.logger import logger
from core.database import execute_query, fetch_one

logger.info("=== INÍCIO DO SCRIPT ===")

def criar_tabela_course():
    logger.info("Verificando existência da tabela lxp_course...")
    try:
        query_check = """
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = 'lxp_course'
        """
        logger.debug(f"Executando query: {query_check}")
        result = fetch_one(query_check, database_name='lxp')
        logger.debug(f"Resultado da query: {result}")
        if result is None:
            logger.error("fetch_one retornou None. Verifique conexão com banco lxp.")
            return False
        exists = result[0] > 0
        logger.info(f"Tabela existe? {exists}")
        if not exists:
            logger.info("Tabela não existe. Criando...")
            create_sql = """
            CREATE TABLE lxp_course (
                id INT IDENTITY(1,1) PRIMARY KEY,
                name NVARCHAR(150) NOT NULL,
                externalId NVARCHAR(50) NOT NULL UNIQUE,
                isActive BIT NOT NULL,
                externalTeachingModalityId NVARCHAR(50) NOT NULL,
                externalEducationLevelId NVARCHAR(50) NOT NULL,
                courseTypeId NVARCHAR(15) NULL,
                created_at DATETIME DEFAULT GETDATE(),
                updated_at DATETIME DEFAULT GETDATE()
            );
            """
            logger.info("Executando CREATE TABLE...")
            execute_query(create_sql, database_name='lxp')
            logger.info("Tabela criada com sucesso.")
        else:
            logger.info("Tabela já existe.")
        return True
    except Exception as e:
        logger.exception(f"EXCEÇÃO em criar_tabela_course: {e}")
        return False

def upsert_course(curso_data):
    logger.info(f"Iniciando upsert para externalId={curso_data['externalId']}")
    try:
        merge_sql = """
        MERGE lxp_course AS target
        USING (SELECT ? AS externalId) AS source
        ON target.externalId = source.externalId
        WHEN MATCHED THEN
            UPDATE SET
                name = ?,
                isActive = ?,
                externalTeachingModalityId = ?,
                externalEducationLevelId = ?,
                courseTypeId = ?,
                updated_at = GETDATE()
        WHEN NOT MATCHED THEN
            INSERT (name, externalId, isActive, externalTeachingModalityId,
                    externalEducationLevelId, courseTypeId)
            VALUES (?, ?, ?, ?, ?, ?);
        """
        params = (
            curso_data['externalId'],
            curso_data['name'],
            curso_data['isActive'],
            curso_data['externalTeachingModalityId'],
            curso_data['externalEducationLevelId'],
            curso_data['courseTypeId'],
            curso_data['name'],
            curso_data['externalId'],
            curso_data['isActive'],
            curso_data['externalTeachingModalityId'],
            curso_data['externalEducationLevelId'],
            curso_data['courseTypeId']
        )
        logger.debug("Executando MERGE...")
        execute_query(merge_sql, params, database_name='lxp')
        logger.info("Upsert concluído.")
        return True
    except Exception as e:
        logger.exception(f"EXCEÇÃO em upsert_course: {e}")
        return False

def run():
    logger.info(">>> Executando run()")
    try:
        logger.info("Criando diretório de saída...")
        os.makedirs('exportacoes/lxp', exist_ok=True)
        logger.info("Diretório OK.")

        curso_fixo = {
            'name': 'AMBIENTAÇÃO E SOFT SKILLS (EAD)',
            'externalId': '998',
            'isActive': True,
            'externalTeachingModalityId': '8566e942-e4b2-439b-a89a-72447e361c50',
            'externalEducationLevelId': 'c5395622-e684-4921-aaad-c2b98e7263d2',
            'courseTypeId': 'bachelor'
        }
        logger.info(f"Dados fixos: {curso_fixo}")

        if not criar_tabela_course():
            logger.error("Falha na criação/verificação da tabela. Abortando.")
            return False

        if not upsert_course(curso_fixo):
            logger.error("Falha no upsert. Abortando.")
            return False

        logger.info("Gerando CSV...")
        dados_csv = [{
            'name': curso_fixo['name'],
            'externalId': curso_fixo['externalId'],
            'isActive': 'true' if curso_fixo['isActive'] else 'false',
            'externalTeachingModalityId': curso_fixo['externalTeachingModalityId'],
            'externalEducationLevelId': curso_fixo['externalEducationLevelId'],
            'courseTypeId': curso_fixo['courseTypeId']
        }]
        df = pd.DataFrame(dados_csv)
        colunas = ['name', 'externalId', 'isActive', 
                   'externalTeachingModalityId', 'externalEducationLevelId', 
                   'courseTypeId']
        df = df[colunas]
        logger.info(f"DataFrame criado: {df}")

        caminho = 'exportacoes/lxp/course.unifoa2.csv'
        df.to_csv(caminho, sep=';', index=False, encoding='utf-8-sig')
        logger.info(f"CSV salvo em: {caminho}")

        logger.info("Fim da execução com sucesso.")
        return True
    except Exception as e:
        logger.exception(f"EXCEÇÃO GERAL NO RUN: {e}")
        return False

if __name__ == "__main__":
    sucesso = run()
    logger.info(f"Resultado final: {sucesso}")
    sys.exit(0 if sucesso else 1)