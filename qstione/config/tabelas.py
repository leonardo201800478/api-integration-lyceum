# qstione/config/tabelas.py
"""
Configuração das tabelas do Qstione
Conforme Dicionário de Dados – Versão 1.14.0

Todas as constantes de filtro (ano, período, faculdade, área de conhecimento)
estão centralizadas no topo para facilitar a manutenção a cada virada de período.
"""

# =============================================================================
# CONSTANTES DE FILTRO – CENTRALIZADAS PARA MANUTENÇÃO
# =============================================================================

# ANO e PERÍODO (semestre) vigentes para as cargas
ANO_VIGENTE = 2026
PERIODOS_VIGENTES = ['21', '22', '2']          # semestres letivos
SEMESTRE_OFERTA_FIXO = '2026.2'               # formato AAAAS

# Faculdades / Unidades organizacionais incluídas
FACULDADES_INCLUIDAS = ['001', '002', '004']    # Nível de Curso

# Áreas de conhecimento que devem ser importadas
# Inclui: Obrigatória, Optativa, Disciplinas Obrigatórias, Extensão Curricularizada, NULL e vazio
AREAS_CONHECIMENTO_INCLUIDAS = [
    'Obrigatória',
    'Optativa',
    'Disciplinas Obrigatórias',
    'Extensão Curricularizada',
    None,        # valor nulo
    ''           # string vazia
]

# =============================================================================
# CONFIGURAÇÃO DAS TABELAS DE IMPORTAÇÃO (IMP)
# =============================================================================

TABELAS_CONFIG = {
    # -------------------------------------------------------------------------
    # IMP-001 – Cursos
    # -------------------------------------------------------------------------
    'imp_001_cursos': {
        'nome_planilha': 'IMP-001 - Cursos',
        'tabela_origem': 'LY_CURSO',
        'descricao': 'Importação de cursos',
        'campos': [
            {'nome_qstione': 'codigoCurso', 'tipo': 'CHAR(30)', 'obrigatorio': True,
             'origem': 'curso', 'transformacao': None},
            {'nome_qstione': 'nomeCurso', 'tipo': 'CHAR(64)', 'obrigatorio': True,
             'origem': 'nome', 'transformacao': 'truncar_texto'},
            {'nome_qstione': 'quantPeriodos', 'tipo': 'INTEGER(2)', 'obrigatorio': True,
             'origem': 'prazo_ideal', 'transformacao': 'converter_inteiro'},
            {'nome_qstione': 'codigoUnidadeOrganizacional', 'tipo': 'CHAR(30)', 'obrigatorio': False,
             'origem': None, 'transformacao': 'valor_fixo_4000000001'},
        ],
        'condicoes': f"c.ativo = 'S' AND c.faculdade IN {tuple(FACULDADES_INCLUIDAS)}",
        'agrupamento': 'curso',
        'tipo_carga': 'Incremental',
        'escopo_carga': 'Instituicao'
    },

    # -------------------------------------------------------------------------
    # IMP-002 – Disciplinas
    # -------------------------------------------------------------------------
    'imp_002_disciplina': {
        'nome_planilha': 'IMP-002 - Disciplinas',
        'tabela_origem': 'LY_GRADE',
        'descricao': 'Importação de disciplinas',
        'campos': [
            {'nome_qstione': 'codigoDisciplina', 'tipo': 'CHAR(30)', 'obrigatorio': True,
             'origem': 'disciplina', 'transformacao': 'gerar_codigo_disciplina_curso'},
            {'nome_qstione': 'nomeDisciplina', 'tipo': 'CHAR(100)', 'obrigatorio': True,
             'origem': 'nome_compl', 'transformacao': 'truncar_texto'},
            {'nome_qstione': 'codigoCurso', 'tipo': 'CHAR(30)', 'obrigatorio': True,
             'origem': 'curso', 'transformacao': None},
            {'nome_qstione': 'periodo', 'tipo': 'INTEGER(2)', 'obrigatorio': True,
             'origem': 'serie_ideal', 'transformacao': 'converter_inteiro'},
        ],
        'condicoes': f"c.ativo = 'S' AND c.faculdade IN {tuple(FACULDADES_INCLUIDAS)}",
        'agrupamento': None,
        'tipo_carga': 'Incremental',
        'escopo_carga': 'Instituicao'
    },

    # -------------------------------------------------------------------------
    # IMP-003 – Objetivos de Aprendizagem das Disciplinas
    # -------------------------------------------------------------------------
    'imp_003_objetivos': {
        'nome_planilha': 'IMP-003 - Objetivos de Aprendizagem das Disciplinas',
        'tabela_origem': 'LY_OBJETIVO',
        'descricao': 'Importação de objetivos de aprendizagem',
        'campos': [
            {'nome_qstione': 'codigoDisciplina', 'tipo': 'CHAR(30)', 'obrigatorio': True,
             'origem': 'disciplina', 'transformacao': None},
            {'nome_qstione': 'codigoObjetivo', 'tipo': 'CHAR(32)', 'obrigatorio': True,
             'origem': 'codigo', 'transformacao': None},
            {'nome_qstione': 'descricaoObjetivo', 'tipo': 'CHAR(2100)', 'obrigatorio': True,
             'origem': 'descricao', 'transformacao': None},
            {'nome_qstione': 'tipoObjetivo', 'tipo': 'CHAR(1)', 'obrigatorio': True,
             'origem': 'tipo', 'transformacao': None},
        ],
        'condicoes': '',
        'agrupamento': None,
        'tipo_carga': 'Incremental',
        'escopo_carga': 'Instituicao'
    },

    # -------------------------------------------------------------------------
    # IMP-004 – Referências Bibliográficas das Disciplinas
    # -------------------------------------------------------------------------
    'imp_004_referencias': {
        'nome_planilha': 'IMP-004 - Referências Bibliográficas das Disciplinas',
        'tabela_origem': 'LY_REFERENCIA',
        'descricao': 'Importação de referências bibliográficas',
        'campos': [
            {'nome_qstione': 'codigoDisciplina', 'tipo': 'CHAR(30)', 'obrigatorio': True,
             'origem': 'disciplina', 'transformacao': None},
            {'nome_qstione': 'codigoReferencia', 'tipo': 'CHAR(32)', 'obrigatorio': True,
             'origem': 'codigo', 'transformacao': None},
            {'nome_qstione': 'descricaoReferencia', 'tipo': 'CHAR(2100)', 'obrigatorio': True,
             'origem': 'descricao', 'transformacao': None},
        ],
        'condicoes': '',
        'agrupamento': None,
        'tipo_carga': 'Incremental',
        'escopo_carga': 'Instituicao'
    },

    # -------------------------------------------------------------------------
    # IMP-005 – Ofertas de Disciplinas
    # -------------------------------------------------------------------------
    'imp_005_ofertas': {
        'nome_planilha': 'IMP-005 - Ofertas de Disciplinas',
        'tabela_origem': 'LY_TURMA',
        'descricao': 'Importação de ofertas de disciplinas',
        'campos': [
            {'nome_qstione': 'codigoOferta', 'tipo': 'CHAR(30)', 'obrigatorio': True,
             'origem': None, 'transformacao': 'gerar_codigo_oferta'},
            {'nome_qstione': 'nomeOferta', 'tipo': 'CHAR(100)', 'obrigatorio': True,
             'origem': 'turma', 'transformacao': None},
            {'nome_qstione': 'codigoDisciplina', 'tipo': 'CHAR(30)', 'obrigatorio': True,
             'origem': None, 'transformacao': 'gerar_codigo_disciplina_curso'},
            {'nome_qstione': 'semestreOferta', 'tipo': 'CHAR(6)', 'obrigatorio': True,
             'origem': None, 'transformacao': f'valor_fixo_{SEMESTRE_OFERTA_FIXO}'},
            {'nome_qstione': 'codigoTipoOferta', 'tipo': 'CHAR(3)', 'obrigatorio': True,
             'origem': None, 'transformacao': 'gerar_codigo_tipo_oferta'},
            {'nome_qstione': 'codigoOfertaOrigem', 'tipo': 'CHAR(30)', 'obrigatorio': False,
             'origem': None, 'transformacao': 'gerar_codigo_oferta_origem'},
            {'nome_qstione': 'turno', 'tipo': 'CHAR(1)', 'obrigatorio': False,
             'origem': 'turno', 'transformacao': 'mapear_turno'},
            {'nome_qstione': 'codigoIdentificacaoAVA', 'tipo': 'CHAR(100)', 'obrigatorio': False,
             'origem': None, 'transformacao': 'valor_fixo_vazio'},
        ],
        'condicoes': (
            f"t.ano = {ANO_VIGENTE} "
            f"AND t.semestre IN {tuple(PERIODOS_VIGENTES)} "
            f"AND t.sit_turma = 'aberta' "
            f"AND d.faculdade IN {tuple(FACULDADES_INCLUIDAS)} "
            f"AND (d.area_conhecimento IN {tuple([a for a in AREAS_CONHECIMENTO_INCLUIDAS if a is not None])} "
            f"     OR d.area_conhecimento IS NULL OR d.area_conhecimento = '')"
        ),
        'agrupamento': None,
        'tipo_carga': 'Incremental',
        'escopo_carga': 'Instituicao'
    },

    # -------------------------------------------------------------------------
    # IMP-006 – Usuários
    # -------------------------------------------------------------------------
    'imp_006_usuarios': {
        'nome_planilha': 'IMP-006 - Usuários',
        'tabela_origem': 'LY_DOCENTE',
        'descricao': 'Importação de usuários (docentes)',
        'campos': [
            {'nome_qstione': 'matriculaUsuario', 'tipo': 'CHAR(20)', 'obrigatorio': True,
             'origem': 'matricula', 'transformacao': None},
            {'nome_qstione': 'codigoUsuario', 'tipo': 'CHAR(24)', 'obrigatorio': False,
             'origem': 'email', 'transformacao': 'extrair_usuario_email'},
            {'nome_qstione': 'emailUsuario', 'tipo': 'CHAR(100)', 'obrigatorio': True,
             'origem': 'email', 'transformacao': 'converter_minusculas'},
            {'nome_qstione': 'nomeUsuario', 'tipo': 'CHAR(64)', 'obrigatorio': True,
             'origem': 'nome_compl', 'transformacao': 'truncar_texto'},
        ],
        'condicoes': "ativo = 'S'",
        'agrupamento': 'nomeUsuario',
        'tipo_carga': 'Incremental',
        'escopo_carga': 'Instituicao'
    },

    # -------------------------------------------------------------------------
    # IMP-007 – Usuários dos Cursos
    # -------------------------------------------------------------------------
    'imp_007_usuarios_cursos': {
        'nome_planilha': 'IMP-007 - Usuários Cursos',
        'tabela_origem': 'LY_TURMA_DOCENTE',
        'descricao': 'Associação de usuários aos cursos',
        'campos': [
            {'nome_qstione': 'codigoCurso', 'tipo': 'CHAR(30)', 'obrigatorio': True,
             'origem': 'curso', 'transformacao': None},
            {'nome_qstione': 'emailUsuario', 'tipo': 'CHAR(100)', 'obrigatorio': True,
             'origem': 'email', 'transformacao': 'converter_minusculas'},
            {'nome_qstione': 'papelUsuario', 'tipo': 'CHAR(1)', 'obrigatorio': True,
             'origem': None, 'transformacao': 'determinar_papel_usuario'},
        ],
        'condicoes': f"td.ano = {ANO_VIGENTE} AND td.periodo = '{PERIODOS_VIGENTES[0]}'",
        'agrupamento': None,
        'tipo_carga': 'Incremental',
        'escopo_carga': 'Instituicao'
    },

    # -------------------------------------------------------------------------
    # IMP-008 – Usuários das Disciplinas
    # -------------------------------------------------------------------------
    'imp_008_usuarios_disciplinas': {
        'nome_planilha': 'IMP-008 - Usuários das Disciplinas',
        'tabela_origem': 'LY_TURMA_DOCENTE',
        'descricao': 'Associação de usuários (docentes) às disciplinas',
        'campos': [
            {'nome_qstione': 'codigoDisciplina', 'tipo': 'CHAR(30)', 'obrigatorio': True,
             'origem': None, 'transformacao': 'gerar_codigo_disciplina_curso'},
            {'nome_qstione': 'emailUsuario', 'tipo': 'CHAR(100)', 'obrigatorio': True,
             'origem': 'email', 'transformacao': 'converter_minusculas'},
        ],
        'condicoes': (
            f"td.ano = {ANO_VIGENTE} AND td.periodo = '{PERIODOS_VIGENTES[0]}' "
            f"AND dsc.faculdade IN {tuple(FACULDADES_INCLUIDAS)} "
            f"AND d.ativo = 'S'"
        ),
        'agrupamento': None,
        'tipo_carga': 'Incremental',
        'escopo_carga': 'Instituicao'
    },

    # -------------------------------------------------------------------------
    # IMP-009 – Professores das Ofertas de Disciplinas
    # -------------------------------------------------------------------------
    'imp_009_professores_ofertas': {
        'nome_planilha': 'IMP-009 - Professores das Ofertas de Disciplinas',
        'tabela_origem': 'LY_TURMA_DOCENTE',
        'descricao': 'Associação de professores às ofertas de disciplinas',
        'campos': [
            {'nome_qstione': 'codigoOferta', 'tipo': 'CHAR(30)', 'obrigatorio': True,
             'origem': None, 'transformacao': 'gerar_codigo_oferta'},
            {'nome_qstione': 'emailProfessor', 'tipo': 'CHAR(100)', 'obrigatorio': True,
             'origem': 'email', 'transformacao': 'converter_minusculas'},
        ],
        'condicoes': (
            f"t.ano = {ANO_VIGENTE} "
            f"AND t.semestre IN {tuple(PERIODOS_VIGENTES)} "
            f"AND t.sit_turma = 'aberta' "
            f"AND dsc.faculdade IN {tuple(FACULDADES_INCLUIDAS)} "
            f"AND (dsc.area_conhecimento IN {tuple([a for a in AREAS_CONHECIMENTO_INCLUIDAS if a is not None])} "
            f"     OR dsc.area_conhecimento IS NULL OR dsc.area_conhecimento = '') "
            f"AND d.ativo = 'S'"
        ),
        'agrupamento': None,
        'tipo_carga': 'Incremental',
        'escopo_carga': 'Instituicao'
    },

    # -------------------------------------------------------------------------
    # IMP-010 – Alunos
    # -------------------------------------------------------------------------
    'imp_010_alunos': {
        'nome_planilha': 'IMP-010 - Alunos',
        'tabela_origem': 'LY_ALUNO',
        'descricao': 'Importação de alunos',
        'campos': [
            {'nome_qstione': 'matriculaAluno', 'tipo': 'CHAR(12)', 'obrigatorio': True,
             'origem': 'aluno', 'transformacao': None},
            {'nome_qstione': 'nomeAluno', 'tipo': 'CHAR(140)', 'obrigatorio': True,
             'origem': 'nome_compl', 'transformacao': 'truncar_texto'},
            {'nome_qstione': 'emailAluno', 'tipo': 'CHAR(200)', 'obrigatorio': False,
             'origem': None, 'transformacao': 'gerar_email_aluno'},
            {'nome_qstione': 'codigoCurso', 'tipo': 'CHAR(30)', 'obrigatorio': True,
             'origem': 'curso', 'transformacao': None},
            {'nome_qstione': 'turno', 'tipo': 'CHAR(1)', 'obrigatorio': False,
             'origem': 'turno', 'transformacao': 'mapear_turno'},
            {'nome_qstione': 'codigoIdentificacaoAVA', 'tipo': 'CHAR(100)', 'obrigatorio': False,
             'origem': None, 'transformacao': 'valor_fixo_vazio'},
        ],
        'condicoes': "sit_aluno = 'Ativo'",
        'agrupamento': None,
        'tipo_carga': 'Incremental',
        'escopo_carga': 'Instituicao'
    },

    # -------------------------------------------------------------------------
    # IMP-011 – Alunos das Ofertas de Disciplinas
    # -------------------------------------------------------------------------
    'imp_011_alunos_ofertas': {
        'nome_planilha': 'IMP-011 - Alunos das Ofertas de Disciplinas',
        'tabela_origem': 'LY_MATRICULA',
        'descricao': 'Associação de alunos às ofertas de disciplinas',
        'campos': [
            {'nome_qstione': 'codigoOferta', 'tipo': 'CHAR(30)', 'obrigatorio': True,
             'origem': None, 'transformacao': 'gerar_codigo_oferta'},
            {'nome_qstione': 'matriculaAluno', 'tipo': 'CHAR(12)', 'obrigatorio': True,
             'origem': 'aluno', 'transformacao': None},
            {'nome_qstione': 'codigoCurso', 'tipo': 'CHAR(30)', 'obrigatorio': False,
             'origem': 'curso', 'transformacao': None},
        ],
        'condicoes': f"m.ano = {ANO_VIGENTE} AND m.semestre = '{PERIODOS_VIGENTES[0]}'",
        'agrupamento': None,
        'tipo_carga': 'Incremental',
        'escopo_carga': 'Instituicao'
    },

    # -------------------------------------------------------------------------
    # IMP-012 – Alunos das Ofertas de Disciplinas do Período
    # -------------------------------------------------------------------------
    'imp_012_alunos_periodo': {
        'nome_planilha': 'IMP-012 - Alunos das Ofertas de Disciplinas do Período',
        'tabela_origem': 'LY_MATRICULA',
        'descricao': 'Associação de alunos a todas ofertas de um período',
        'campos': [
            {'nome_qstione': 'numeroPeriodo', 'tipo': 'INTEGER(2)', 'obrigatorio': True,
             'origem': 'periodo', 'transformacao': 'converter_inteiro'},
            {'nome_qstione': 'semestreOferta', 'tipo': 'CHAR(6)', 'obrigatorio': True,
             'origem': None, 'transformacao': f'valor_fixo_{SEMESTRE_OFERTA_FIXO}'},
            {'nome_qstione': 'matriculaAluno', 'tipo': 'CHAR(12)', 'obrigatorio': True,
             'origem': 'aluno', 'transformacao': None},
        ],
        'condicoes': "",
        'agrupamento': None,
        'tipo_carga': 'Incremental',
        'escopo_carga': 'Instituicao'
    },

    # -------------------------------------------------------------------------
    # IMP-013 – Unidades de Avaliação
    # -------------------------------------------------------------------------
    'imp_013_unidades_avaliacao': {
        'nome_planilha': 'IMP-013 - Unidades de Avaliação',
        'tabela_origem': 'LY_UNIDADE_AVALIACAO',
        'descricao': 'Importação de unidades de avaliação',
        'campos': [
            {'nome_qstione': 'codigoUnidade', 'tipo': 'CHAR(32)', 'obrigatorio': True,
             'origem': 'codigo', 'transformacao': None},
            {'nome_qstione': 'nomeUnidade', 'tipo': 'CHAR(64)', 'obrigatorio': True,
             'origem': 'nome', 'transformacao': 'truncar_texto'},
            {'nome_qstione': 'codigoCurso', 'tipo': 'CHAR(30)', 'obrigatorio': False,
             'origem': 'curso', 'transformacao': None},
            {'nome_qstione': 'codigoDisciplina', 'tipo': 'CHAR(30)', 'obrigatorio': False,
             'origem': 'disciplina', 'transformacao': None},
            {'nome_qstione': 'ordemExibicao', 'tipo': 'INTEGER(2)', 'obrigatorio': True,
             'origem': 'ordem', 'transformacao': 'converter_inteiro'},
            {'nome_qstione': 'codigoAgrupamento', 'tipo': 'CHAR(64)', 'obrigatorio': True,
             'origem': 'agrupamento', 'transformacao': None},
        ],
        'condicoes': "",
        'agrupamento': None,
        'tipo_carga': 'Incremental',
        'escopo_carga': 'Instituicao'
    },

    # -------------------------------------------------------------------------
    # IMP-015 – Conteúdos Programáticos
    # -------------------------------------------------------------------------
    'imp_015_conteudos': {
        'nome_planilha': 'IMP-015 - Conteúdos Programáticos',
        'tabela_origem': 'LY_CONTEUDO',
        'descricao': 'Importação de conteúdos programáticos',
        'campos': [
            {'nome_qstione': 'codigoDisciplina', 'tipo': 'CHAR(30)', 'obrigatorio': True,
             'origem': 'disciplina', 'transformacao': None},
            {'nome_qstione': 'codigoConteudo', 'tipo': 'CHAR(32)', 'obrigatorio': True,
             'origem': 'codigo', 'transformacao': None},
            {'nome_qstione': 'conteudoProgramatico', 'tipo': 'CHAR(2100)', 'obrigatorio': True,
             'origem': 'descricao', 'transformacao': None},
        ],
        'condicoes': "",
        'agrupamento': None,
        'tipo_carga': 'Incremental',
        'escopo_carga': 'Instituicao'
    },

    # -------------------------------------------------------------------------
    # IMP-016 – Unidades Organizacionais
    # -------------------------------------------------------------------------
    'imp_016_unidades_organizacionais': {
        'nome_planilha': 'IMP-016 - Unidades Organizacionais',
        'tabela_origem': 'LY_UNIDADE',
        'descricao': 'Importação de unidades organizacionais',
        'campos': [
            {'nome_qstione': 'codigoUnidade', 'tipo': 'CHAR(30)', 'obrigatorio': True,
             'origem': 'codigo', 'transformacao': None},
            {'nome_qstione': 'nomeCurto', 'tipo': 'CHAR(64)', 'obrigatorio': False,
             'origem': 'sigla', 'transformacao': None},
            {'nome_qstione': 'nomeLongo', 'tipo': 'CHAR(150)', 'obrigatorio': True,
             'origem': 'nome', 'transformacao': 'truncar_texto'},
        ],
        'condicoes': "",
        'agrupamento': None,
        'tipo_carga': 'Incremental',
        'escopo_carga': 'Instituicao'
    },
}

# =============================================================================
# CONFIGURAÇÃO DAS CARGAS DE DESATIVAÇÃO (DES)
# =============================================================================

DES_CONFIG = {
    'des_001_cursos': {
        'nome_planilha': 'DES-001 - Cursos',
        'descricao': 'Desativa um curso',
        'campos': [
            {'nome_qstione': 'codigoCurso', 'tipo': 'CHAR(30)', 'obrigatorio': True},
        ]
    },
    'des_002_disciplinas': {
        'nome_planilha': 'DES-002 - Disciplinas',
        'descricao': 'Desativa uma disciplina',
        'campos': [
            {'nome_qstione': 'codigoDisciplina', 'tipo': 'CHAR(30)', 'obrigatorio': True},
        ]
    },
    'des_005_ofertas': {
        'nome_planilha': 'DES-005 - Ofertas de Disciplinas',
        'descricao': 'Desativa uma oferta de disciplina',
        'campos': [
            {'nome_qstione': 'codigoOferta', 'tipo': 'CHAR(30)', 'obrigatorio': True},
        ]
    },
    'des_006_usuarios': {
        'nome_planilha': 'DES-006 - Usuários',
        'descricao': 'Desativa um usuário',
        'campos': [
            {'nome_qstione': 'emailUsuario', 'tipo': 'CHAR(100)', 'obrigatorio': True},
        ]
    },
    'des_007_usuarios_cursos': {
        'nome_planilha': 'DES-007 - Usuários dos Cursos',
        'descricao': 'Desativa o relacionamento entre um usuário e um curso',
        'campos': [
            {'nome_qstione': 'codigoCurso', 'tipo': 'CHAR(30)', 'obrigatorio': True},
            {'nome_qstione': 'emailUsuario', 'tipo': 'CHAR(100)', 'obrigatorio': True},
        ]
    },
    'des_008_usuarios_disciplinas': {
        'nome_planilha': 'DES-008 - Usuários das Disciplinas',
        'descricao': 'Desativa o relacionamento entre um usuário e uma disciplina',
        'campos': [
            {'nome_qstione': 'codigoDisciplina', 'tipo': 'CHAR(30)', 'obrigatorio': True},
            {'nome_qstione': 'emailUsuario', 'tipo': 'CHAR(100)', 'obrigatorio': True},
        ]
    },
    'des_009_professores_ofertas': {
        'nome_planilha': 'DES-009 - Professores das Ofertas de Disciplinas',
        'descricao': 'Desativa o relacionamento entre um professor e uma oferta',
        'campos': [
            {'nome_qstione': 'codigoOferta', 'tipo': 'CHAR(30)', 'obrigatorio': True},
            {'nome_qstione': 'emailProfessor', 'tipo': 'CHAR(100)', 'obrigatorio': True},
        ]
    },
    'des_010_alunos': {
        'nome_planilha': 'DES-010 - Alunos',
        'descricao': 'Desativa um aluno',
        'campos': [
            {'nome_qstione': 'matriculaAluno', 'tipo': 'CHAR(12)', 'obrigatorio': True},
            {'nome_qstione': 'codigoCurso', 'tipo': 'CHAR(30)', 'obrigatorio': False},
        ]
    },
    'des_011_alunos_ofertas': {
        'nome_planilha': 'DES-011 - Alunos das Ofertas de Disciplinas',
        'descricao': 'Desativa o relacionamento entre um aluno e uma oferta',
        'campos': [
            {'nome_qstione': 'codigoOferta', 'tipo': 'CHAR(30)', 'obrigatorio': True},
            {'nome_qstione': 'matriculaAluno', 'tipo': 'CHAR(12)', 'obrigatorio': True},
            {'nome_qstione': 'codigoCurso', 'tipo': 'CHAR(30)', 'obrigatorio': False},
        ]
    },
    'des_012_unidades_organizacionais': {
        'nome_planilha': 'DES-012 - Unidades Organizacionais',
        'descricao': 'Desativa uma unidade organizacional',
        'campos': [
            {'nome_qstione': 'codigoUnidade', 'tipo': 'CHAR(30)', 'obrigatorio': True},
        ]
    },
}

# =============================================================================
# ORDEM DAS COLUNAS NAS PLANILHAS EXCEL
# =============================================================================

ORDEM_COLUNAS_PLANILHA = {
    'imp_001_cursos': ['codigoCurso', 'nomeCurso', 'quantPeriodos', 'codigoUnidadeOrganizacional'],
    'imp_002_disciplina': ['codigoDisciplina', 'nomeDisciplina', 'codigoCurso', 'periodo'],
    'imp_003_objetivos': ['codigoDisciplina', 'codigoObjetivo', 'descricaoObjetivo', 'tipoObjetivo'],
    'imp_004_referencias': ['codigoDisciplina', 'codigoReferencia', 'descricaoReferencia'],
    'imp_005_ofertas': ['codigoOferta', 'nomeOferta', 'codigoDisciplina', 'semestreOferta',
                        'codigoTipoOferta', 'codigoOfertaOrigem', 'turno', 'codigoIdentificacaoAVA'],
    'imp_006_usuarios': ['matriculaUsuario', 'codigoUsuario', 'emailUsuario', 'nomeUsuario'],
    'imp_007_usuarios_cursos': ['codigoCurso', 'emailUsuario', 'papelUsuario'],
    'imp_008_usuarios_disciplinas': ['codigoDisciplina', 'emailUsuario'],
    'imp_009_professores_ofertas': ['codigoOferta', 'emailProfessor'],
    'imp_010_alunos': ['matriculaAluno', 'nomeAluno', 'emailAluno', 'codigoCurso', 'turno', 'codigoIdentificacaoAVA'],
    'imp_011_alunos_ofertas': ['codigoOferta', 'matriculaAluno', 'codigoCurso'],
    'imp_012_alunos_periodo': ['numeroPeriodo', 'semestreOferta', 'matriculaAluno'],
    'imp_013_unidades_avaliacao': ['codigoUnidade', 'nomeUnidade', 'codigoCurso', 'codigoDisciplina', 'ordemExibicao', 'codigoAgrupamento'],
    'imp_015_conteudos': ['codigoDisciplina', 'codigoConteudo', 'conteudoProgramatico'],
    'imp_016_unidades_organizacionais': ['codigoUnidade', 'nomeCurto', 'nomeLongo'],
}