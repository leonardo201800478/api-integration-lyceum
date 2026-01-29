from sqlalchemy import Column, String, Integer, DateTime, Text
import sys
import os

# Adiciona o diretório raiz ao path para importar core.database
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import Base

class LY_TURMA_DOCENTE(Base):
    """
    Modelo SQLAlchemy para a tabela LY_TURMA_DOCENTE.
    Representa a relação entre docentes e turmas no sistema Lyceum.
    """
    __tablename__ = 'LY_TURMA_DOCENTE'
    
    # Chave primária
    chave = Column(Integer, primary_key=True, nullable=False)
    
    # Dados da turma
    turma = Column(String(20))
    disciplina = Column(String(20))
    ano = Column(Integer)
    periodo = Column(Integer)
    
    # Dados do docente
    num_func = Column(Integer, nullable=False)
    
    # Datas
    dt_inicio = Column(DateTime)
    dt_fim = Column(DateTime)
    dt_ultalt = Column(DateTime)
    
    # Informações da relação
    funcao = Column(String(50))
    carga_hor = Column(Integer)
    observacao = Column(Text)
    usuario = Column(String(50))
    
    # Campos flexíveis (field01 a field20)
    fl_field01 = Column(String(100))
    fl_field02 = Column(String(100))
    fl_field03 = Column(String(100))
    fl_field04 = Column(String(100))
    fl_field05 = Column(String(100))
    fl_field06 = Column(String(100))
    fl_field07 = Column(String(100))
    fl_field08 = Column(String(100))
    fl_field09 = Column(String(100))
    fl_field10 = Column(String(100))
    fl_field11 = Column(String(100))
    fl_field12 = Column(String(100))
    fl_field13 = Column(String(100))
    fl_field14 = Column(String(100))
    fl_field15 = Column(String(100))
    fl_field16 = Column(String(100))
    fl_field17 = Column(String(100))
    fl_field18 = Column(String(100))
    fl_field19 = Column(String(100))
    fl_field20 = Column(String(100))
    
    def __repr__(self):
        return f"<LY_TURMA_DOCENTE(chave={self.chave}, turma={self.turma}, num_func={self.num_func})>"