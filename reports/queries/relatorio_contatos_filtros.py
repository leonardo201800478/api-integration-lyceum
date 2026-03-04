# reports/queries/relatorio_contatos_filtros.py

import pandas as pd
from core.database import get_db_connection
from core.logger import logger

def get_dados_contatos_filtros(anos, semestres, unidade_responsavel, curso=None):
    """
    Retorna DataFrame com dados de contatos aplicando filtros.
    Obtém o curso priorizando LY_ALUNO.curso e depois LY_TURMA.curso,
    e garante apenas um registro por aluno (matrícula mais recente).
    """
    logger.info(f"Buscando contatos com filtros: anos={anos}, semestres={semestres}, unidade={unidade_responsavel}, curso={curso}")
    
    placeholders_ano = ','.join(['?'] * len(anos))
    placeholders_sem = ','.join(['?'] * len(semestres))
    
    query = f"""
        WITH dados AS (
            SELECT
                M.aluno AS cod_aluno,
                COALESCE(A.nome_social, A.nome_compl, '') AS nome_aluno,
                A.sit_aluno,
                A.pessoa AS cod_pessoa,
                COALESCE(A.curso, T.curso) AS cod_curso,
                C.nome AS nome_curso,
                P.fone,
                P.e_mail,
                P.e_mail_com,
                P.e_mail_interno,
                P.ddd_fone_celular,
                P.ddd_fone,
                P.celular,
                M.sit_matricula,
                ROW_NUMBER() OVER (PARTITION BY M.aluno ORDER BY M.ano DESC, M.semestre DESC) AS rn
            FROM LY_MATRICULA M
            INNER JOIN LY_TURMA T 
                ON M.ano = T.ano 
                AND M.semestre = T.semestre 
                AND M.turma = T.turma 
                AND M.disciplina = T.disciplina
            INNER JOIN LY_ALUNO A 
                ON M.aluno = A.aluno
            LEFT JOIN LY_PESSOA P 
                ON A.pessoa = P.pessoa
            LEFT JOIN LY_CURSO C
                ON C.curso = COALESCE(A.curso, T.curso)
            WHERE T.ano IN ({placeholders_ano})
              AND T.semestre IN ({placeholders_sem})
              AND T.unidade_responsavel = ?
    """
    
    params = anos + semestres + [unidade_responsavel]
    
    if curso:
        query += " AND COALESCE(A.curso, T.curso) = ?"
        params.append(curso)
    
    query += """
        )
        SELECT
            cod_aluno,
            nome_aluno,
            sit_aluno,
            cod_pessoa,
            cod_curso,
            nome_curso,
            fone,
            e_mail,
            e_mail_com,
            e_mail_interno,
            ddd_fone_celular,
            ddd_fone,
            celular,
            sit_matricula
        FROM dados
        WHERE rn = 1
        ORDER BY nome_curso, nome_aluno
    """
    
    try:
        with get_db_connection(database_name='lyceum') as conn:
            df = pd.read_sql_query(query, conn, params=params)
        
        # Substituir NaN por string vazia
        df = df.fillna('')
        
        logger.info(f"{len(df)} registros encontrados.")
        return df
    except Exception as e:
        logger.error(f"Erro ao executar consulta de contatos: {e}")
        return pd.DataFrame()