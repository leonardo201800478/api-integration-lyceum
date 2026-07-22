SELECT * from VW_ALUNO where pering = '2026/2' 
and DS_SITUACAO = 'Ativo' 
and Situação_Matricula = 'Matriculado'
order by curso;


SELECT 
    curso,
    crr_cd_curso,
    COUNT(*) AS total_por_curso,
    (SELECT COUNT(*) FROM VW_ALUNO 
     WHERE pering IN ('2026/23', '2026/2') 
         AND DS_SITUACAO = 'Ativo' 
         AND Situação_Matricula = 'Matriculado') AS total_geral
FROM VW_ALUNO 
WHERE pering IN ('2026/23', '2026/2') 
    AND DS_SITUACAO = 'Ativo' 
    AND Situação_Matricula = 'Matriculado'
GROUP BY curso, crr_cd_curso
ORDER BY curso;