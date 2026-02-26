# lxp/exportadores/exp_001_cursos.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import os
import pandas as pd
from core.logger import logger
from core.database import execute_query, fetch_one

print("=== INÍCIO DO SCRIPT ===")

def criar_tabela_course():
    print("Verificando existência da tabela lxp_course...")
    try:
        query_check = """
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = 'lxp_course'
        """
        print(f"Executando query: {query_check}")
        result = fetch_one(query_check, db_path='lxp')
        print(f"Resultado da query: {result}")
        if result is None:
            print("ERRO: fetch_one retornou None. Verifique conexão com banco lxp.")
            return False
        exists = result[0] > 0
        print(f"Tabela existe? {exists}")
        if not exists:
            print("Tabela não existe. Criando...")
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
            print("Executando CREATE TABLE...")
            execute_query(create_sql, db_path='lxp')
            print("Tabela criada com sucesso.")
        else:
            print("Tabela já existe.")
        return True
    except Exception as e:
        print(f"EXCEÇÃO em criar_tabela_course: {e}")
        import traceback
        traceback.print_exc()
        return False

def upsert_course(curso_data):
    print(f"Iniciando upsert para externalId={curso_data['externalId']}")
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
        print("Executando MERGE...")
        execute_query(merge_sql, params, db_path='lxp')
        print("Upsert concluído.")
        return True
    except Exception as e:
        print(f"EXCEÇÃO em upsert_course: {e}")
        import traceback
        traceback.print_exc()
        return False

def run():
    print(">>> Executando run()")
    try:
        print("Criando diretório de saída...")
        os.makedirs('exportacoes/lxp', exist_ok=True)
        print("Diretório OK.")

        curso_fixo = {
            'name': 'AMBIENTAÇÃO E SOFT SKILLS (EAD)',
            'externalId': '998',
            'isActive': True,
            'externalTeachingModalityId': '8566e942-e4b2-439b-a89a-72447e361c50',
            'externalEducationLevelId': 'c5395622-e684-4921-aaad-c2b98e7263d2',
            'courseTypeId': 'bachelor'
        }
        print(f"Dados fixos: {curso_fixo}")

        if not criar_tabela_course():
            print("Falha na criação/verificação da tabela. Abortando.")
            return False

        if not upsert_course(curso_fixo):
            print("Falha no upsert. Abortando.")
            return False

        print("Gerando CSV...")
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
        print(f"DataFrame criado: {df}")

        caminho = 'exportacoes/lxp/course.unifoa2.csv'
        df.to_csv(caminho, sep=';', index=False, encoding='utf-8-sig')
        print(f"CSV salvo em: {caminho}")

        print("Fim da execução com sucesso.")
        return True
    except Exception as e:
        print(f"EXCEÇÃO GERAL NO RUN: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    sucesso = run()
    print(f"Resultado final: {sucesso}")
    sys.exit(0 if sucesso else 1)