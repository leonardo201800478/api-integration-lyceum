SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
ALTER VIEW [dbo].[VW_ALUNO] AS
WITH MatriculaUnica AS (
    SELECT 
        aluno,
        ano,
        semestre,
        turma,
        -- Escolhe uma disciplina (a primeira) para representar a matrícula na turma
        disciplina,
        sit_matricula,
        ROW_NUMBER() OVER (
            PARTITION BY aluno, ano, semestre, turma 
            ORDER BY disciplina
        ) AS rn
    FROM LY_MATRICULA
)
SELECT 
    ROW_NUMBER() OVER (ORDER BY A.aluno, MU.ano DESC, MU.semestre DESC, MU.turma) AS [ID],
    P.cpf AS [pes_nu_cpf_cgc],
    C.decreto AS [HAB_MEC],
    A.pessoa AS [pes_id_pessoa],
    P.nome_compl AS [pes_nm_pessoa],
    P.nome_social AS [pes_nm_registro],
    A.aluno AS [alu_nu_matricula],
    C.nome AS [curso],
    C.titulo AS [crr_nm_titulo],
    A.curriculo AS [id_curriculo_atual_aluno],
    A.serie AS [rcr_nu_periodo_aluno],
    -- Ano/semestre da turma (matrícula)
    CAST(MU.ano AS VARCHAR) + '/' + CAST(MU.semestre AS VARCHAR) AS [semestre oca],
    A.sit_aluno AS [DS_SITUACAO],
    MU.sit_matricula AS [Situação_Matricula],
    A.dt_ingresso AS [his_dt_ingresso],
    NULL AS [his_dt_saida],
    NULL AS [rcr_dt_colacao_grau],
    A.unidade_ensino AS [tpc_ds_tp_curso],
    A.turno AS [Turno],
    -- Ano/semestre de ingresso do aluno
    CAST(A.ano_ingresso AS VARCHAR) + '/' + CAST(A.sem_ingresso AS VARCHAR) AS [pering],
    CR.regime AS [DS_PERIODICIDADE],
    C.tipo AS [MODALIDADE_ENSINO],
    A.unidade_fisica AS [INSTITUICAO_ENSINO],
    A.tipo_ingresso AS [TIPO_INGRESSO]
FROM LY_ALUNO A
LEFT JOIN LY_PESSOA P ON A.pessoa = P.pessoa
LEFT JOIN LY_CURSO C ON A.curso = C.curso
LEFT JOIN LY_CURRICULO CR ON A.curriculo = CR.curriculo AND A.curso = CR.curso
LEFT JOIN MatriculaUnica MU ON A.aluno = MU.aluno AND MU.rn = 1;  -- apenas uma linha por (aluno, ano, semestre, turma)
GO
