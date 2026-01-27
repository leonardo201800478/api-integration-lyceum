from typing import Dict, List, Optional
from datetime import datetime

class AlunoProcessor:
    """Processador de dados para alunos IMP-010"""
    
    @staticmethod
    def generate_email(matricula: str, unidade_ensino: str) -> str:
        """Gera email conforme regra"""
        if unidade_ensino == "007":
            return f"{matricula}@etecfoa.com.br"
        else:
            return f"{matricula}@unifoa.edu.br"
    
    @staticmethod
    def normalize_turno(turno: str) -> str:
        """Normaliza turno para M,T,N,I,O"""
        if not turno:
            return ""
        
        turno = str(turno)[0].upper()
        valid_turnos = ["M", "T", "N", "I", "O"]
        
        return turno if turno in valid_turnos else "O"
    
    @staticmethod
    def process_aluno(aluno_data: Dict) -> Optional[Dict]:
        """Processa dados de um aluno para formato IMP-010"""
        try:
            # Campos obrigatórios
            matricula = aluno_data.get("aluno", "")
            nome_completo = aluno_data.get("nome_compl", "")
            curso = aluno_data.get("curso", "")
            
            # Verificar campos obrigatórios
            if not all([matricula, nome_completo, curso]):
                return None
            
            # Gerar email
            unidade_ensino = aluno_data.get("unidade_ensino", "")
            email = AlunoProcessor.generate_email(matricula, unidade_ensino)
            
            # Normalizar turno
            turno = AlunoProcessor.normalize_turno(aluno_data.get("turno", ""))
            
            return {
                "matriculaAluno": str(matricula)[:12],      # Máximo 12 caracteres
                "nomeAluno": str(nome_completo)[:140],      # Máximo 140 caracteres
                "emailAluno": str(email)[:200],             # Máximo 200 caracteres
                "codigoCurso": str(curso)[:30],             # Máximo 30 caracteres
                "turno": turno,
                "codigoIdentificacaoAVA": None,             # Em branco
                "sit_aluno": aluno_data.get("sit_aluno", ""),
                "ativo": True
            }
        except Exception as e:
            print(f"❌ Erro ao processar aluno {aluno_data.get('aluno', 'N/A')}: {e}")
            return None
    
    @staticmethod
    def process_batch(alunos_data: List[Dict]) -> List[Dict]:
        """Processa um lote de alunos"""
        processed = []
        
        for aluno in alunos_data:
            processed_aluno = AlunoProcessor.process_aluno(aluno)
            if processed_aluno:
                processed.append(processed_aluno)
        
        print(f"📦 Alunos processados: {len(processed)}/{len(alunos_data)}")
        return processed

class ImportResult:
    """Resultado da importação"""
    
    def __init__(self):
        self.inserted = 0
        self.updated = 0
        self.errors = 0
        self.inactivated = 0
    
    def add_inserted(self):
        self.inserted += 1
    
    def add_updated(self):
        self.updated += 1
    
    def add_error(self):
        self.errors += 1
    
    def add_inactivated(self, count):
        self.inactivated = count
    
    def summary(self):
        return {
            "inserted": self.inserted,
            "updated": self.updated,
            "errors": self.errors,
            "inactivated": self.inactivated
        }