# reports/queries/relatorio_alunos.py
import pandas as pd
from core.database import get_db_connection
from core.logger import logger

def get_dados_alunos():
    """
    Retorna um DataFrame com dados dos alunos para relatório.
    Utiliza a conexão do core com SQL Server.
    """
    logger.info("Buscando dados de alunos para relatório...")
    query = """
        SELECT 
            matricula,
            nome,
            cpf,
            email,
            curso_nome,
            situacao
        FROM dbo.ly_aluno  -- Ajuste o schema conforme sua base (ex: dbo, lyceum)
        ORDER BY nome
    """
    with get_db_connection() as conn:
        df = pd.read_sql_query(query, conn)
    logger.info(f"{len(df)} registros de alunos encontrados.")
    return df