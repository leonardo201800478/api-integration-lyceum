from core.database import execute_query, fetch_all, fetch_one, get_db_connection

class CursoModel:
    """Modelo para tabela IMP-001 - Cursos"""
    
    TABLE_NAME = "imp_001_cursos"
    
    @classmethod
    def create_table(cls, db_name="dados_unifoa.db"):
        """Cria a tabela IMP-001"""
        query = f'''
        CREATE TABLE IF NOT EXISTS {cls.TABLE_NAME} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigoCurso TEXT(30) NOT NULL UNIQUE,
            nomeCurso TEXT(64) NOT NULL,
            codigoUnidadeOrganizacional TEXT(30) NOT NULL,
            quantPeriodos INTEGER,
            data_importacao DATETIME DEFAULT CURRENT_TIMESTAMP,
            data_atualizacao DATETIME DEFAULT CURRENT_TIMESTAMP,
            ativo BOOLEAN DEFAULT 1
        )
        '''
        
        execute_query(query, db_name=db_name)
        
        # Criar índices
        indexes = [
            f"CREATE INDEX IF NOT EXISTS idx_{cls.TABLE_NAME}_codigo ON {cls.TABLE_NAME}(codigoCurso)",
            f"CREATE INDEX IF NOT EXISTS idx_{cls.TABLE_NAME}_unidade ON {cls.TABLE_NAME}(codigoUnidadeOrganizacional)",
            f"CREATE INDEX IF NOT EXISTS idx_{cls.TABLE_NAME}_ativo ON {cls.TABLE_NAME}(ativo)"
        ]
        
        for index_query in indexes:
            execute_query(index_query, db_name=db_name)
        
        print(f"✅ Tabela {cls.TABLE_NAME} criada/verificada")
    
    @classmethod
    def get_existing_codigos(cls, db_name="dados_unifoa.db"):
        """Retorna conjunto de códigos de curso existentes"""
        query = f"SELECT codigoCurso FROM {cls.TABLE_NAME}"
        results = fetch_all(query, db_name=db_name)
        return {str(row[0]) for row in results}
    
    @classmethod
    def insert_curso(cls, curso_data: dict, db_name="dados_unifoa.db"):
        """Insere um novo curso"""
        query = f'''
        INSERT INTO {cls.TABLE_NAME} 
        (codigoCurso, nomeCurso, codigoUnidadeOrganizacional, quantPeriodos, ativo)
        VALUES (?, ?, ?, ?, ?)
        '''
        
        params = (
            curso_data.get('codigoCurso'),
            curso_data.get('nomeCurso'),
            curso_data.get('codigoUnidadeOrganizacional'),
            curso_data.get('quantPeriodos'),
            curso_data.get('ativo', True)
        )
        
        execute_query(query, params, db_name=db_name)
    
    @classmethod
    def update_curso(cls, codigo_curso: str, curso_data: dict, db_name="dados_unifoa.db"):
        """Atualiza um curso existente"""
        query = f'''
        UPDATE {cls.TABLE_NAME} 
        SET nomeCurso = ?, codigoUnidadeOrganizacional = ?, quantPeriodos = ?,
            data_atualizacao = CURRENT_TIMESTAMP, ativo = ?
        WHERE codigoCurso = ?
        '''
        
        params = (
            curso_data.get('nomeCurso'),
            curso_data.get('codigoUnidadeOrganizacional'),
            curso_data.get('quantPeriodos'),
            curso_data.get('ativo', True),
            codigo_curso
        )
        
        execute_query(query, params, db_name=db_name)
    
    @classmethod
    def set_inactive(cls, codigos_to_keep: set, db_name="dados_unifoa.db"):
        """Marca cursos como inativos exceto os na lista"""
        if not codigos_to_keep:
            return 0
        
        placeholders = ','.join(['?'] * len(codigos_to_keep))
        query = f'''
        UPDATE {cls.TABLE_NAME} 
        SET ativo = 0, data_atualizacao = CURRENT_TIMESTAMP
        WHERE codigoCurso NOT IN ({placeholders})
        '''
        
        cursor = execute_query(query, list(codigos_to_keep), db_name=db_name)
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
            
            cursor.execute(f"SELECT COUNT(DISTINCT codigoUnidadeOrganizacional) FROM {cls.TABLE_NAME} WHERE ativo = 1")
            unidades = cursor.fetchone()[0]
            
            return {
                "total_cursos": total,
                "cursos_ativos": ativos,
                "cursos_inativos": total - ativos,
                "unidades_distintas": unidades
            }
    
    @classmethod
    def get_recent_cursos(cls, limit=5, db_name="dados_unifoa.db"):
        """Retorna cursos mais recentes"""
        query = f'''
        SELECT codigoCurso, nomeCurso, codigoUnidadeOrganizacional, quantPeriodos
        FROM {cls.TABLE_NAME} 
        WHERE ativo = 1
        ORDER BY data_importacao DESC 
        LIMIT ?
        '''
        
        return fetch_all(query, (limit,), db_name=db_name)