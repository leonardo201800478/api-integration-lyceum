# qstione/desativadores/des_001_cursos.py
from .desativador_base import DesativadorBase

class DesativadorCursos(DesativadorBase):
    def __init__(self, conexao_qstione):
        super().__init__(conexao_qstione, 'des_001_cursos')