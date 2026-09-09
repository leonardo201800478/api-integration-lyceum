"""V2: consulta de pessoa por ID.

A migração da rotina específica será feita após os testes de contrato da V2.
"""
from sync.sync_ly_pessoa_by_id import buscar_e_salvar_pessoa_por_id

def run(cod_pessoa, buscar_alunos=True):
    return buscar_e_salvar_pessoa_por_id(cod_pessoa, buscar_alunos=buscar_alunos)
