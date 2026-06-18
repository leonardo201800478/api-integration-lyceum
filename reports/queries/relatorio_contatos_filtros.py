import pandas as pd
from core.database import get_db_connection
from core.logger import logger

def get_dados_contatos_filtros(anos, semestres, unidade_responsavel, curso=None,
                               ano_ingresso=None, sem_ingresso=None):
    """
    Retorna DataFrame com dados de contatos aplicando filtros.
    Obtém o curso priorizando LY_ALUNO.curso e depois LY_TURMA.curso,
    e garante apenas um registro por aluno (matrícula mais recente).

    Parâmetros:
        anos (list): Lista de anos de oferta.
        semestres (list): Lista de semestres de oferta.
        unidade_responsavel (str): Código da unidade.
        curso (str ou None): Código do curso (opcional).
        ano_ingresso (list ou None): Lista de anos de ingresso (opcional).
        sem_ingresso (list ou None): Lista de semestres de ingresso (opcional).
    """
    logger.info(f"Buscando contatos com filtros: anos={anos}, semestres={semestres}, "
                f"unidade={unidade_responsavel}, curso={curso}, "
                f"ano_ingresso={ano_ingresso}, sem_ingresso={sem_ingresso}")

    placeholders_ano = ','.join(['?'] * len(anos))
    placeholders_sem = ','.join(['?'] * len(semestres))

    # Montagem dinâmica da query
    query = f"""
        WITH dados AS (
            SELECT
                M.aluno AS cod_aluno,
                COALESCE(A.nome_social, A.nome_compl, '') AS nome_aluno,
                A.sit_aluno,
                A.pessoa AS cod_pessoa,
                A.ano_ingresso,
                A.sem_ingresso,
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

    # NOVOS FILTROS DE INGRESSO
    if ano_ingresso:
        if isinstance(ano_ingresso, list):
            placeholders_ai = ','.join(['?'] * len(ano_ingresso))
            query += f" AND A.ano_ingresso IN ({placeholders_ai})"
            params.extend(ano_ingresso)
        else:
            query += " AND A.ano_ingresso = ?"
            params.append(ano_ingresso)

    if sem_ingresso:
        if isinstance(sem_ingresso, list):
            placeholders_si = ','.join(['?'] * len(sem_ingresso))
            query += f" AND A.sem_ingresso IN ({placeholders_si})"
            params.extend(sem_ingresso)
        else:
            query += " AND A.sem_ingresso = ?"
            params.append(sem_ingresso)

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

        df = df.fillna('')
        logger.info(f"{len(df)} registros encontrados.")
        return df
    except Exception as e:
        logger.error(f"Erro ao executar consulta de contatos: {e}")
        return pd.DataFrame()