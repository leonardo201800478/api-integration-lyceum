from core.database import execute_query, fetch_all, fetch_one, get_db_connection
from datetime import datetime

class AlunoModel:
    """Modelo para tabela IMP-010 - Alunos"""
    
    TABLE_NAME = "imp_010_alunos"
    
    @classmethod
    def create_table(cls, db_name="dados_unifoa.db"):
        """Cria a tabela IMP-010"""
        query = f'''
        CREATE TABLE IF NOT EXISTS {cls.TABLE_NAME} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            matriculaAluno TEXT(12) NOT NULL UNIQUE,
            nomeAluno TEXT(140) NOT NULL,
            emailAluno TEXT(200),
            codigoCurso TEXT(30) NOT NULL,
            turno TEXT(1),
            codigoIdentificacaoAVA TEXT(100),
            sit_aluno TEXT(20),
            data_importacao DATETIME DEFAULT CURRENT_TIMESTAMP,
            data_atualizacao DATETIME DEFAULT CURRENT_TIMESTAMP,
            ativo BOOLEAN DEFAULT 1
        )
        '''
        
        execute_query(query, db_name=db_name)
        
        # Criar índices
        indexes = [
            f"CREATE INDEX IF NOT EXISTS idx_{cls.TABLE_NAME}_matricula ON {cls.TABLE_NAME}(matriculaAluno)",
            f"CREATE INDEX IF NOT EXISTS idx_{cls.TABLE_NAME}_curso ON {cls.TABLE_NAME}(codigoCurso)",
            f"CREATE INDEX IF NOT EXISTS idx_{cls.TABLE_NAME}_ativo ON {cls.TABLE_NAME}(ativo)",
            f"CREATE INDEX IF NOT EXISTS idx_{cls.TABLE_NAME}_situacao ON {cls.TABLE_NAME}(sit_aluno)"
        ]
        
        for index_query in indexes:
            execute_query(index_query, db_name=db_name)
        
        print(f"✅ Tabela {cls.TABLE_NAME} criada/verificada")
    
    @classmethod
    def get_existing_matriculas(cls, db_name="dados_unifoa.db"):
        """Retorna conjunto de matrículas existentes"""
        query = f"SELECT matriculaAluno FROM {cls.TABLE_NAME}"
        results = fetch_all(query, db_name=db_name)
        return {str(row[0]) for row in results}
    
    @classmethod
    def insert_aluno(cls, aluno_data: dict, db_name="dados_unifoa.db"):
        """Insere um novo aluno"""
        query = f'''
        INSERT INTO {cls.TABLE_NAME} 
        (matriculaAluno, nomeAluno, emailAluno, codigoCurso, turno, 
         codigoIdentificacaoAVA, sit_aluno, ativo)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        '''
        
        params = (
            aluno_data.get('matriculaAluno'),
            aluno_data.get('nomeAluno'),
            aluno_data.get('emailAluno'),
            aluno_data.get('codigoCurso'),
            aluno_data.get('turno'),
            aluno_data.get('codigoIdentificacaoAVA'),
            aluno_data.get('sit_aluno'),
            aluno_data.get('ativo', True)
        )
        
        execute_query(query, params, db_name=db_name)
    
    @classmethod
    def update_aluno(cls, matricula: str, aluno_data: dict, db_name="dados_unifoa.db"):
        """Atualiza um aluno existente"""
        query = f'''
        UPDATE {cls.TABLE_NAME} 
        SET nomeAluno = ?, emailAluno = ?, codigoCurso = ?, turno = ?,
            sit_aluno = ?, data_atualizacao = CURRENT_TIMESTAMP, ativo = ?
        WHERE matriculaAluno = ?
        '''
        
        params = (
            aluno_data.get('nomeAluno'),
            aluno_data.get('emailAluno'),
            aluno_data.get('codigoCurso'),
            aluno_data.get('turno'),
            aluno_data.get('sit_aluno'),
            aluno_data.get('ativo', True),
            matricula
        )
        
        execute_query(query, params, db_name=db_name)
    
    @classmethod
    def set_inactive(cls, matriculas_to_keep: set, db_name="dados_unifoa.db"):
        """Marca alunos como inativos exceto os na lista"""
        if not matriculas_to_keep:
            return 0
        
        placeholders = ','.join(['?'] * len(matriculas_to_keep))
        query = f'''
        UPDATE {cls.TABLE_NAME} 
        SET ativo = 0, data_atualizacao = CURRENT_TIMESTAMP
        WHERE matriculaAluno NOT IN ({placeholders})
        '''
        
        cursor = execute_query(query, list(matriculas_to_keep), db_name=db_name)
        return cursor.rowcount
    
    @classmethod
    def get_summary(cls, db_name="dados_unifoa.db"):
        """Obtém resumo dos dados"""
        with get_db_connection(db_name) as conn:
            cursor = conn.cursor()
            
            cursor.execute(f"SELECT COUNT(*) FROM {cls.TABLE_NAME}")
            total = cursor.fetchone()[0]
            
            cursor.execute(f"SELECT COUNT(*) FROM {cls.TABLE_NAME} WHERE ativo = 1")
            ativos = cursor.fetchone()[0]
            
            cursor.execute(f"SELECT COUNT(DISTINCT codigoCurso) FROM {cls.TABLE_NAME} WHERE ativo = 1")
            cursos = cursor.fetchone()[0]
            
            return {
                "total_alunos": total,
                "alunos_ativos": ativos,
                "alunos_inativos": total - ativos,
                "cursos_distintos": cursos
            }
    
    @classmethod
    def get_recent_alunos(cls, limit=5, db_name="dados_unifoa.db"):
        """Retorna alunos mais recentes"""
        query = f'''
        SELECT matriculaAluno, nomeAluno, emailAluno, codigoCurso, turno
        FROM {cls.TABLE_NAME} 
        WHERE ativo = 1
        ORDER BY data_importacao DESC 
        LIMIT ?
        '''
        
        return fetch_all(query, (limit,), db_name=db_name)