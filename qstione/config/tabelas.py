"""
Configuração das tabelas do Qstione
"""

TABELAS_CONFIG = {
    'imp_001_cursos': {
        'nome_planilha': 'IMP-001 - Cursos',
        'tabela_origem': 'LY_CURSO',
        'descricao': 'Importação de cursos',
        'campos': [
            {
                'nome_qstione': 'codigoCurso',
                'tipo': 'CHAR(30)',
                'obrigatorio': True,
                'origem': 'curso',
                'transformacao': None
            },
            {
                'nome_qstione': 'nomeCurso',
                'tipo': 'CHAR(64)',
                'obrigatorio': True,
                'origem': 'nome',
                'transformacao': None
            },
            {
                'nome_qstione': 'quantPeriodos',
                'tipo': 'INTEGER(2)',
                'obrigatorio': True,
                'origem': 'prazo_ideal',
                'transformacao': 'converter_inteiro'
            },
            {
                'nome_qstione': 'codigoUnidadeOrganizacional',
                'tipo': 'CHAR(30)',
                'obrigatorio': True,
                'origem': None,
                'transformacao': 'valor_fixo_4000000001'
            }
        ],
        'condicoes': "c.ativo = 'S' AND c.faculdade IN ('001', '002', '004')",
        'agrupamento': 'curso',
        'tipo_carga': 'Incremental',
        'escopo_carga': 'Instituicao'
    },
    'imp_002_disciplina': {
        'nome_planilha': 'IMP-002 - Disciplinas',
        'tabela_origem': 'LY_GRADE',
        'descricao': 'Importação de disciplinas',
        'campos': [
            {
                'nome_qstione': 'codigoDisciplina',
                'tipo': 'CHAR(30)',
                'obrigatorio': True,
                'origem': 'disciplina',
                'transformacao': None
            },
            {
                'nome_qstione': 'nomeDisciplina',
                'tipo': 'CHAR(100)',
                'obrigatorio': True,
                'origem': 'nome_compl',
                'transformacao': None
            },
            {
                'nome_qstione': 'codigoCurso',
                'tipo': 'CHAR(30)',
                'obrigatorio': True,
                'origem': 'curso',
                'transformacao': None
            },
            {
                'nome_qstione': 'periodo',
                'tipo': 'INTEGER(2)',
                'obrigatorio': True,
                'origem': 'serie_ideal',
                'transformacao': 'converter_inteiro'
            }
        ],
        'condicoes': "c.ativo = 'S' AND c.faculdade IN ('001', '002', '004')",
        'agrupamento': None,
        'tipo_carga': 'Incremental',
        'escopo_carga': 'Instituicao'
    },
    'imp_006_usuarios': {
        'nome_planilha': 'IMP-006 - Usuários',
        'tabela_origem': 'LY_DOCENTE',
        'descricao': 'Importação de usuários (docentes)',
        'campos': [
            {
                'nome_qstione': 'matriculaUsuario',
                'tipo': 'CHAR(20)',
                'obrigatorio': True,
                'origem': 'matricula',
                'transformacao': None
            },
            {
                'nome_qstione': 'codigoUsuario',
                'tipo': 'CHAR(24)',
                'obrigatorio': False,
                'origem': 'email',
                'transformacao': 'extrair_usuario_email'
            },
            {
                'nome_qstione': 'emailUsuario',
                'tipo': 'CHAR(100)',
                'obrigatorio': True,
                'origem': 'email',
                'transformacao': 'converter_minusculas'
            },
            {
                'nome_qstione': 'nomeUsuario',
                'tipo': 'CHAR(64)',
                'obrigatorio': True,
                'origem': 'nome_compl',
                'transformacao': None
            }
        ],
        'condicoes': "ativo = 'S'",
        'agrupamento': 'cpf',
        'tipo_carga': 'Incremental',
        'escopo_carga': 'Instituicao'
    }
    # Adicionar novas tabelas aqui...
}

# Ordem das colunas na planilha Excel
ORDEM_COLUNAS_PLANILHA = {
    'imp_001_cursos': ['codigoCurso', 'nomeCurso', 'quantPeriodos', 'codigoUnidadeOrganizacional'],
    'imp_002_disciplina': ['codigoDisciplina', 'nomeDisciplina', 'codigoCurso', 'periodo'],
    'imp_006_usuarios': ['matriculaUsuario', 'codigoUsuario', 'emailUsuario', 'nomeUsuario']
}