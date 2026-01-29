"""
Configuração das tabelas do Qstione
"""

TABELAS_CONFIG = {
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
    'imp_006_usuarios': ['matriculaUsuario', 'codigoUsuario', 'emailUsuario', 'nomeUsuario']
}