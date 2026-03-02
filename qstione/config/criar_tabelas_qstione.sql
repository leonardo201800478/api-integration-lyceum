-- =============================================================================
-- qstione/config/criar_tabelas_qstione.sql
-- Criação das tabelas de importação e desativação do Qstione
-- Conforme Dicionário de Dados – Versão 1.14.0
-- =============================================================================

-- IMP-001 – Cursos
CREATE TABLE IF NOT EXISTS imp_001_cursos (
    codigoCurso TEXT NOT NULL,                     -- CHAR(30)
    nomeCurso TEXT NOT NULL,                      -- CHAR(64)
    quantPeriodos INTEGER NOT NULL,               -- INTEGER(2)
    codigoUnidadeOrganizacional TEXT,             -- CHAR(30) – opcional
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (codigoCurso)
);

-- IMP-002 – Disciplinas
CREATE TABLE IF NOT EXISTS imp_002_disciplina (
    codigoDisciplina TEXT NOT NULL,               -- CHAR(30)
    nomeDisciplina TEXT NOT NULL,                -- CHAR(100)
    codigoCurso TEXT NOT NULL,                   -- CHAR(30)
    periodo INTEGER NOT NULL,                    -- INTEGER(2)
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (codigoDisciplina, codigoCurso, periodo)
);

-- IMP-003 – Objetivos de Aprendizagem das Disciplinas
CREATE TABLE IF NOT EXISTS imp_003_objetivos (
    codigoDisciplina TEXT NOT NULL,               -- CHAR(30)
    codigoObjetivo TEXT NOT NULL,                -- CHAR(32)
    descricaoObjetivo TEXT NOT NULL,             -- CHAR(2100)
    tipoObjetivo TEXT NOT NULL,                  -- CHAR(1) – A, C, H
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (codigoDisciplina, codigoObjetivo)
);

-- IMP-004 – Referências Bibliográficas das Disciplinas
CREATE TABLE IF NOT EXISTS imp_004_referencias (
    codigoDisciplina TEXT NOT NULL,               -- CHAR(30)
    codigoReferencia TEXT NOT NULL,              -- CHAR(32)
    descricaoReferencia TEXT NOT NULL,           -- CHAR(2100)
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (codigoDisciplina, codigoReferencia)
);

-- IMP-005 – Ofertas de Disciplinas
CREATE TABLE IF NOT EXISTS imp_005_ofertas (
    codigoOferta TEXT NOT NULL,                  -- CHAR(30)
    nomeOferta TEXT NOT NULL,                    -- CHAR(100)
    codigoDisciplina TEXT NOT NULL,              -- CHAR(30)
    semestreOferta TEXT NOT NULL,                -- CHAR(6)  – AAAASS
    codigoTipoOferta TEXT NOT NULL,              -- CHAR(3)  – REG, REP, REC
    codigoOfertaOrigem TEXT,                     -- CHAR(30) – opcional
    turno TEXT,                                  -- CHAR(1)  – M,T,N,I,O
    codigoIdentificacaoAVA TEXT,                 -- CHAR(100) – opcional
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (codigoOferta)
);

-- IMP-006 – Usuários
CREATE TABLE IF NOT EXISTS imp_006_usuarios (
    matriculaUsuario TEXT NOT NULL,              -- CHAR(20)
    codigoUsuario TEXT,                          -- CHAR(24) – opcional
    emailUsuario TEXT NOT NULL,                  -- CHAR(100)
    nomeUsuario TEXT NOT NULL,                   -- CHAR(64)
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (matriculaUsuario),
    UNIQUE (emailUsuario)
);

-- IMP-007 – Usuários dos Cursos
CREATE TABLE IF NOT EXISTS imp_007_usuarios_cursos (
    codigoCurso TEXT NOT NULL,                   -- CHAR(30)
    emailUsuario TEXT NOT NULL,                  -- CHAR(100)
    papelUsuario TEXT NOT NULL,                  -- CHAR(1) – P, C, A, G, O
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (codigoCurso, emailUsuario)
);

-- IMP-008 – Usuários das Disciplinas
CREATE TABLE IF NOT EXISTS imp_008_usuarios_disciplinas (
    codigoDisciplina TEXT NOT NULL,              -- CHAR(30)
    emailUsuario TEXT NOT NULL,                  -- CHAR(100)
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (codigoDisciplina, emailUsuario)
);

-- IMP-009 – Professores das Ofertas de Disciplinas
CREATE TABLE IF NOT EXISTS imp_009_professores_ofertas (
    codigoOferta TEXT NOT NULL,                  -- CHAR(30)
    emailProfessor TEXT NOT NULL,                -- CHAR(100)
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (codigoOferta, emailProfessor)
);

-- IMP-010 – Alunos
CREATE TABLE IF NOT EXISTS imp_010_alunos (
    matriculaAluno TEXT NOT NULL,                -- CHAR(12) – apenas números
    nomeAluno TEXT NOT NULL,                     -- CHAR(140)
    emailAluno TEXT,                             -- CHAR(200) – opcional
    codigoCurso TEXT NOT NULL,                   -- CHAR(30)
    turno TEXT,                                  -- CHAR(1)  – M,T,N,I,O
    codigoIdentificacaoAVA TEXT,                 -- CHAR(100) – opcional
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (matriculaAluno, codigoCurso)
);

-- IMP-011 – Alunos das Ofertas de Disciplinas
CREATE TABLE IF NOT EXISTS imp_011_alunos_ofertas (
    codigoOferta TEXT NOT NULL,                  -- CHAR(30)
    matriculaAluno TEXT NOT NULL,                -- CHAR(12)
    codigoCurso TEXT,                            -- CHAR(30) – opcional
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (codigoOferta, matriculaAluno, codigoCurso)
);

-- IMP-012 – Alunos das Ofertas de Disciplinas do Período
CREATE TABLE IF NOT EXISTS imp_012_alunos_periodo (
    numeroPeriodo INTEGER NOT NULL,              -- INTEGER(2)
    semestreOferta TEXT NOT NULL,                -- CHAR(6)
    matriculaAluno TEXT NOT NULL,                -- CHAR(12)
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (numeroPeriodo, semestreOferta, matriculaAluno)
);

-- IMP-013 – Unidades de Avaliação
CREATE TABLE IF NOT EXISTS imp_013_unidades_avaliacao (
    codigoUnidade TEXT NOT NULL,                 -- CHAR(32)
    nomeUnidade TEXT NOT NULL,                   -- CHAR(64)
    codigoCurso TEXT,                            -- CHAR(30) – opcional
    codigoDisciplina TEXT,                       -- CHAR(30) – opcional
    ordemExibicao INTEGER NOT NULL,              -- INTEGER(2)
    codigoAgrupamento TEXT NOT NULL,             -- CHAR(64)
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (codigoUnidade)
);

-- IMP-015 – Conteúdos Programáticos
CREATE TABLE IF NOT EXISTS imp_015_conteudos (
    codigoDisciplina TEXT NOT NULL,              -- CHAR(30)
    codigoConteudo TEXT NOT NULL,                -- CHAR(32)
    conteudoProgramatico TEXT NOT NULL,          -- CHAR(2100)
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (codigoDisciplina, codigoConteudo)
);

-- IMP-016 – Unidades Organizacionais
CREATE TABLE IF NOT EXISTS imp_016_unidades_organizacionais (
    codigoUnidade TEXT NOT NULL,                 -- CHAR(30)
    nomeCurto TEXT,                              -- CHAR(64) – opcional
    nomeLongo TEXT NOT NULL,                     -- CHAR(150)
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (codigoUnidade)
);

-- =============================================================================
-- TABELAS DE DESATIVAÇÃO (DES)
-- =============================================================================

-- DES-001 – Cursos
CREATE TABLE IF NOT EXISTS des_001_cursos (
    codigoCurso TEXT NOT NULL PRIMARY KEY,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- DES-002 – Disciplinas
CREATE TABLE IF NOT EXISTS des_002_disciplinas (
    codigoDisciplina TEXT NOT NULL PRIMARY KEY,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- DES-005 – Ofertas de Disciplinas
CREATE TABLE IF NOT EXISTS des_005_ofertas (
    codigoOferta TEXT NOT NULL PRIMARY KEY,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- DES-006 – Usuários
CREATE TABLE IF NOT EXISTS des_006_usuarios (
    emailUsuario TEXT NOT NULL PRIMARY KEY,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- DES-007 – Usuários dos Cursos
CREATE TABLE IF NOT EXISTS des_007_usuarios_cursos (
    codigoCurso TEXT NOT NULL,
    emailUsuario TEXT NOT NULL,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (codigoCurso, emailUsuario)
);

-- DES-008 – Usuários das Disciplinas
CREATE TABLE IF NOT EXISTS des_008_usuarios_disciplinas (
    codigoDisciplina TEXT NOT NULL,
    emailUsuario TEXT NOT NULL,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (codigoDisciplina, emailUsuario)
);

-- DES-009 – Professores das Ofertas de Disciplinas
CREATE TABLE IF NOT EXISTS des_009_professores_ofertas (
    codigoOferta TEXT NOT NULL,
    emailProfessor TEXT NOT NULL,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (codigoOferta, emailProfessor)
);

-- DES-010 – Alunos
CREATE TABLE IF NOT EXISTS des_010_alunos (
    matriculaAluno TEXT NOT NULL,
    codigoCurso TEXT,  -- opcional
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (matriculaAluno, COALESCE(codigoCurso, ''))
);

-- DES-011 – Alunos das Ofertas de Disciplinas
CREATE TABLE IF NOT EXISTS des_011_alunos_ofertas (
    codigoOferta TEXT NOT NULL,
    matriculaAluno TEXT NOT NULL,
    codigoCurso TEXT,  -- opcional
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (codigoOferta, matriculaAluno, COALESCE(codigoCurso, ''))
);

-- DES-012 – Unidades Organizacionais
CREATE TABLE IF NOT EXISTS des_012_unidades_organizacionais (
    codigoUnidade TEXT NOT NULL PRIMARY KEY,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);