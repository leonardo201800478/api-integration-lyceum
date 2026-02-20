import pandas as pd
from core.database import get_db_connection
from core.logger import logger

def get_dados_contatos_filtros(anos, semestres, unidade_responsavel, curso=None):
    """
    Retorna DataFrame com dados de contatos aplicando filtros.
    Agora obtém o curso via COALESCE entre LY_TURMA.curso e LY_ALUNO.curso.
    """
    logger.info(f"Buscando contatos com filtros: anos={anos}, semestres={semestres}, unidade={unidade_responsavel}, curso={curso}")
    
    placeholders_ano = ','.join(['?'] * len(anos))
    placeholders_sem = ','.join(['?'] * len(semestres))
    
    query = f"""
        SELECT DISTINCT
            M.aluno AS cod_aluno,
            COALESCE(A.nome_social, A.nome_compl, '') AS nome_aluno,
            A.sit_aluno,
            A.pessoa AS cod_pessoa,
            COALESCE(T.curso, A.curso) AS cod_curso,  -- Curso vindo da turma ou do aluno
            C.nome AS nome_curso,
            P.fone,
            P.e_mail,
            P.e_mail_com,
            P.e_mail_interno,
            P.ddd_fone_celular,
            P.ddd_fone,
            P.celular,
            M.sit_matricula
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
            ON C.curso = COALESCE(T.curso, A.curso)  -- Join com o código do curso unificado
        WHERE T.ano IN ({placeholders_ano})
          AND T.semestre IN ({placeholders_sem})
          AND T.unidade_responsavel = ?
    """
    
    params = anos + semestres + [unidade_responsavel]
    
    if curso:
        query += " AND COALESCE(T.curso, A.curso) = ?"
        params.append(curso)
    
    query += " ORDER BY nome_curso, nome_aluno"
    
    with get_db_connection() as conn:
        df = pd.read_sql_query(query, conn, params=params)
    
    # Substituir NaN por string vazia
    df = df.fillna('')
    
    logger.info(f"{len(df)} registros encontrados.")
    return df