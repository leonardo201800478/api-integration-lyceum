# lxp/exportadores/exp_002_curriculum.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import os
import pandas as pd
from core.logger import logger
from core.database import execute_query, fetch_one

def criar_tabela_curriculum():
    """Cria a tabela lxp_curriculum no banco lxp se ela não existir."""
    logger.info("Verificando existência da tabela lxp_curriculum...")
    try:
        query_check = """
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = 'lxp_curriculum'
        """
        result = fetch_one(query_check, db_path='lxp')
        if result is None:
            logger.error("fetch_one retornou None. Possível erro de conexão.")
            return False
        exists = result[0] > 0
        if not exists:
            logger.info("Tabela lxp_curriculum não encontrada. Criando...")
            create_sql = """
            CREATE TABLE lxp_curriculum (
                id INT IDENTITY(1,1) PRIMARY KEY,
                externalCourseId NVARCHAR(50) NOT NULL,
                name NVARCHAR(150) NOT NULL,
                externalId NVARCHAR(50) NOT NULL UNIQUE,
                workload INT NOT NULL,
                startDate DATE NULL,
                endDate DATE NULL,
                isActive BIT NOT NULL,
                created_at DATETIME DEFAULT GETDATE(),
                updated_at DATETIME DEFAULT GETDATE()
            );
            """
            execute_query(create_sql, db_path='lxp')
            logger.info("Tabela lxp_curriculum criada com sucesso.")
        else:
            logger.info("Tabela lxp_curriculum já existe.")
        return True
    except Exception as e:
        logger.exception(f"Erro ao verificar/criar tabela: {e}")
        return False

def upsert_curriculum(curriculum_data):
    """
    Insere ou atualiza um currículo na tabela lxp_curriculum.
    curriculum_data: dicionário com chaves: externalCourseId, name, externalId,
                     workload, startDate, endDate, isActive.
    startDate/endDate podem ser None (NULL no banco).
    isActive deve ser booleano.
    """
    logger.info(f"Iniciando upsert para externalId={curriculum_data['externalId']}")
    try:
        merge_sql = """
        MERGE lxp_curriculum AS target
        USING (SELECT ? AS externalId) AS source
        ON target.externalId = source.externalId
        WHEN MATCHED THEN
            UPDATE SET
                externalCourseId = ?,
                name = ?,
                workload = ?,
                startDate = ?,
                endDate = ?,
                isActive = ?,
                updated_at = GETDATE()
        WHEN NOT MATCHED THEN
            INSERT (externalCourseId, name, externalId, workload, startDate, endDate, isActive)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """
        params = (
            curriculum_data['externalId'],  # source ON
            curriculum_data['externalCourseId'],
            curriculum_data['name'],
            curriculum_data['workload'],
            curriculum_data['startDate'],
            curriculum_data['endDate'],
            curriculum_data['isActive'],
            curriculum_data['externalCourseId'],  # INSERT
            curriculum_data['name'],
            curriculum_data['externalId'],
            curriculum_data['workload'],
            curriculum_data['startDate'],
            curriculum_data['endDate'],
            curriculum_data['isActive']
        )
        execute_query(merge_sql, params, db_path='lxp')
        logger.info("Upsert concluído com sucesso.")
        return True
    except Exception as e:
        logger.exception(f"Erro no upsert: {e}")
        return False

def run() -> bool:
    """
    Exporta dados de currículos para o arquivo curriculum.unifoa2.csv e
    sincroniza a tabela lxp_curriculum no SQL Server com o registro fixo.
    """
    logger.info("=== INÍCIO DA EXPORTAÇÃO DE CURRÍCULOS ===")
    try:
        # Garantir diretório de saída
        os.makedirs('exportacoes/lxp', exist_ok=True)
        logger.info("Diretório de saída garantido.")

        # Dados fixos (provisório)
        curriculum_fixo = {
            'externalCourseId': '998',
            'name': 'Curriculo_Padrao',
            'externalId': '998202621',
            'workload': 200,
            'startDate': None,          # NULL no banco, vazio no CSV
            'endDate': None,             # NULL no banco, vazio no CSV
            'isActive': True
        }
        logger.info(f"Dados fixos: {curriculum_fixo}")

        # Sincronização com banco
        if not criar_tabela_curriculum():
            logger.error("Falha na criação/verificação da tabela. Abortando.")
            return False

        if not upsert_curriculum(curriculum_fixo):
            logger.error("Falha no upsert. Abortando.")
            return False

        # Geração do CSV
        logger.info("Gerando DataFrame para CSV...")
        dados_csv = [{
            'externalCourseId': curriculum_fixo['externalCourseId'],
            'name': curriculum_fixo['name'],
            'externalId': curriculum_fixo['externalId'],
            'workload': curriculum_fixo['workload'],
            'startDate': '',  # vazio conforme especificação
            'endDate': '',
            'isActive': 'true' if curriculum_fixo['isActive'] else 'false'
        }]
        df = pd.DataFrame(dados_csv)
        colunas = ['externalCourseId', 'name', 'externalId', 'workload',
                   'startDate', 'endDate', 'isActive']
        df = df[colunas]
        logger.info(f"DataFrame criado com {len(df)} linhas.")

        caminho = 'exportacoes/lxp/curriculum.unifoa2.csv'
        df.to_csv(caminho, sep=';', index=False, encoding='utf-8-sig')
        logger.info(f"Arquivo CSV salvo em: {caminho}")

        logger.info("Exportação concluída com sucesso.")
        return True

    except Exception as e:
        logger.exception(f"Exceção não tratada no run(): {e}")
        return False

if __name__ == "__main__":
    sys.exit(0 if run() else 1)