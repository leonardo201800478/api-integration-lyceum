# reports/queries/relatorio_alunos.py
import pandas as pd
from core.database import get_db_connection
from core.logger import logger

def get_dados_alunos():
    """
    Retorna um DataFrame com dados dos alunos para relatório.
    Realiza joins entre LY_ALUNO, LY_PESSOA e LY_CURSO.
    """
    logger.info("Buscando dados de alunos para relatório...")
    
    query = """
        SELECT 
            A.aluno AS matricula,
            A.nome_compl AS nome,
            P.cpf,
            P.e_mail AS email,
            C.nome AS curso_nome,
            A.sit_aluno AS situacao
        FROM LY_ALUNO A
        LEFT JOIN LY_PESSOA P ON A.pessoa = P.pessoa
        LEFT JOIN LY_CURSO C ON A.curso = C.curso
        ORDER BY C.nome, A.nome_compl
    """
    
    try:
        with get_db_connection(database_name='lyceum.db') as conn:
            df = pd.read_sql_query(query, conn)
        logger.info(f"{len(df)} registros de alunos encontrados.")
        return df
    except Exception as e:
        logger.error(f"Erro ao consultar dados de alunos: {e}")
        # Retorna DataFrame vazio em caso de erro
        return pd.DataFrame()