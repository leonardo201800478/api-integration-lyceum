"""
Configuração centralizada de filtros para importações do Qstione.
Ajuste estas constantes a cada novo período letivo.
"""

# =============================================================================
# CONSTANTES DE FILTRO – CENTRALIZADAS PARA MANUTENÇÃO
# =============================================================================

# ANO e PERÍODO (semestre) vigentes para as cargas
ANO_VIGENTE = 2026
PERIODOS_VIGENTES = ['21', '22', '2']          # semestres letivos
SEMESTRE_OFERTA_FIXO = '2026.2'                # formato AAAAS

# Faculdades / Unidades organizacionais incluídas
FACULDADES_INCLUIDAS = ['001', '002', '004']   # Nível de Curso

# Áreas de conhecimento que devem ser importadas
# Inclui: Obrigatória, Optativa, Disciplinas Obrigatórias, Extensão Curricularizada, NULL e vazio
AREAS_CONHECIMENTO_INCLUIDAS = [
    'Obrigatória',
    'Optativa',
    'Disciplinas Obrigatórias',
    'Extensão Curricularizada',
    'Pesquisa Curricularizada',
    None,        # valor nulo
    ''           # string vazia
]

# Status de turma considerado
SITUACAO_TURMA_VALIDA = 'aberta'