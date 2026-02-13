#!/usr/bin/env python3
"""
Modelo para tabela LY_GRADE usando o core.database existente
SEM chave primária fixa - similar a LY_TURMA
"""
import logging
from typing import List, Dict, Any, Optional
from core.database import get_db_connection, execute_query, fetch_all, fetch_one
from core.config import config

logger = logging.getLogger(__name__)


class LyGradeModel:
    """Modelo para tabela LY_GRADE - SEM chave primária fixa"""
    
    TABLE_NAME = "LY_GRADE"
    
    # Lista de campos da API para mapeamento
    API_FIELDS = [
        'atividade', 'aulas_sem_ativ', 'aulas_sem_aulas', 'aulas_sem_lab',
        'aulas_semanais', 'complemento', 'curriculo', 'curso', 'disciplina',
        'disciplina_extensiva', 'especial', 'fl_field01', 'fl_field02',
        'fl_field03', 'fl_field04', 'fl_field05', 'fl_field06', 'fl_field07',
        'fl_field08', 'fl_field09', 'fl_field10', 'formula_equiv',
        'formula_prereq', 'max_matr_aprov', 'max_reprov', 'nome_exibicao',
        'obrigatoria', 'permite_glp', 'retem_serie', 'serie_ideal',
        'serie_prereq', 'stamp_atualizacao', 'tese_dissertacao', 'turno'
    ]
    
    @classmethod
    def _normalize_value(cls, value: Any) -> Any:
        """Normaliza valores para inserção no banco"""
        if value is None:
            return None
        
        if isinstance(value, bool):
            return 'S' if value else 'N'
        
        if isinstance(value, (int, float)):
            return value
        
        if isinstance(value, str):
            value = value.strip()
            if value.lower() in ['null', 'none', '']:
                return None
            return value
        
        # Para outros tipos, converte para string
        return str(value)
    
    @classmethod
    def create_table(cls):
        """Cria a tabela LY_GRADE se não existir"""
        # Verificar se a tabela já existe
        table_exists_query = """
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name=?
        """
        
        result = fetch_one(table_exists_query, (cls.TABLE_NAME,), db_path=config.DB_LYCEUM_PATH)
        
        if result:
            logger.info(f"Tabela {cls.TABLE_NAME} já existe")
            return True
        
        # SQL para criar a tabela SEM chave primária fixa
        sql = f"""
        CREATE TABLE {cls.TABLE_NAME} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            atividade TEXT,
            aulas_sem_ativ INTEGER,
            aulas_sem_aulas INTEGER,
            aulas_sem_lab INTEGER,
            aulas_semanais INTEGER,
            complemento TEXT,
            curriculo TEXT,
            curso TEXT,
            disciplina TEXT,
            disciplina_extensiva TEXT,
            especial TEXT,
            fl_field01 TEXT,
            fl_field02 TEXT,
            fl_field03 TEXT,
            fl_field04 TEXT,
            fl_field05 TEXT,
            fl_field06 TEXT,
            fl_field07 TEXT,
            fl_field08 TEXT,
            fl_field09 TEXT,
            fl_field10 TEXT,
            formula_equiv TEXT,
            formula_prereq TEXT,
            max_matr_aprov INTEGER,
            max_reprov INTEGER,
            nome_exibicao TEXT,
            obrigatoria TEXT,
            permite_glp TEXT,
            retem_serie TEXT,
            serie_ideal INTEGER,
            serie_prereq INTEGER,
            stamp_atualizacao TEXT,
            tese_dissertacao TEXT,
            turno TEXT,
            -- Metadados
            data_importacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        try:
            execute_query(sql, db_path=config.DB_LYCEUM_PATH)
            
            # Criar índices para melhor performance
            indexes = [
                f"CREATE INDEX idx_grade_curriculo_curso ON {cls.TABLE_NAME}(curriculo, curso)",
                f"CREATE INDEX idx_grade_disciplina ON {cls.TABLE_NAME}(disciplina)",
                f"CREATE INDEX idx_grade_curso ON {cls.TABLE_NAME}(curso)",
                f"CREATE INDEX idx_grade_obrigatoria ON {cls.TABLE_NAME}(obrigatoria)",
                f"CREATE INDEX idx_grade_serie_ideal ON {cls.TABLE_NAME}(serie_ideal)",
            ]
            
            for index_sql in indexes:
                try:
                    execute_query(index_sql, db_path=config.DB_LYCEUM_PATH)
                except Exception as e:
                    logger.warning(f"Erro ao criar índice: {e}")
            
            logger.info(f"Tabela {cls.TABLE_NAME} criada com sucesso (sem chave primária fixa)")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao criar tabela {cls.TABLE_NAME}: {e}")
            return False
    
    @classmethod
    def clear_table(cls):
        """Limpa a tabela completamente (para sincronizações completas)"""
        try:
            sql = f"DELETE FROM {cls.TABLE_NAME}"
            execute_query(sql, db_path=config.DB_LYCEUM_PATH)
            logger.info(f"Tabela {cls.TABLE_NAME} limpa")
            return True
        except Exception as e:
            logger.error(f"Erro ao limpar tabela {cls.TABLE_NAME}: {e}")
            return False
    
    @classmethod
    def insert(cls, data: Dict) -> bool:
        """Insere uma nova grade (não verifica duplicatas)"""
        try:
            # Verificar campos que formam a identidade básica
            curriculo = cls._normalize_value(data.get('curriculo'))
            curso = cls._normalize_value(data.get('curso'))
            disciplina = cls._normalize_value(data.get('disciplina'))
            
            if not all([curriculo, curso, disciplina]):
                logger.warning(f"Grade sem campos obrigatórios (curriculo, curso, disciplina): {data}")
                return False
            
            # Preparar colunas e valores
            columns = ['curriculo', 'curso', 'disciplina']
            values = [curriculo, curso, disciplina]
            
            # Adicionar outros campos
            for field in cls.API_FIELDS:
                if field not in ['curriculo', 'curso', 'disciplina']:
                    value = cls._normalize_value(data.get(field))
                    if value is not None:
                        columns.append(field)
                        values.append(value)
            
            # Construir query de INSERT simples
            columns_str = ', '.join(columns)
            placeholders = ', '.join(['?' for _ in values])
            
            sql = f"""
            INSERT INTO {cls.TABLE_NAME} ({columns_str}, data_atualizacao)
            VALUES ({placeholders}, CURRENT_TIMESTAMP)
            """
            
            execute_query(sql, tuple(values), db_path=config.DB_LYCEUM_PATH)
            return True
            
        except Exception as e:
            logger.error(f"Erro ao inserir grade {data.get('curriculo')}/{data.get('curso')}/{data.get('disciplina')}: {e}")
            return False
    
    @classmethod
    def batch_insert(cls, data_list: List[Dict]) -> int:
        """Insere múltiplas grades em lote (permite duplicatas)"""
        if not data_list:
            return 0
        
        success_count = 0
        error_count = 0
        
        with get_db_connection(db_path=config.DB_LYCEUM_PATH) as conn:
            cursor = conn.cursor()
            
            for data in data_list:
                try:
                    # Verificar campos que formam a identidade básica
                    curriculo = cls._normalize_value(data.get('curriculo'))
                    curso = cls._normalize_value(data.get('curso'))
                    disciplina = cls._normalize_value(data.get('disciplina'))
                    
                    if not all([curriculo, curso, disciplina]):
                        logger.warning(f"Grade sem campos obrigatórios: {data}")
                        error_count += 1
                        continue
                    
                    # Preparar colunas e valores
                    columns = ['curriculo', 'curso', 'disciplina']
                    values = [curriculo, curso, disciplina]
                    
                    # Adicionar outros campos
                    for field in cls.API_FIELDS:
                        if field not in ['curriculo', 'curso', 'disciplina']:
                            value = cls._normalize_value(data.get(field))
                            if value is not None:
                                columns.append(field)
                                values.append(value)
                    
                    # Construir query de INSERT simples
                    columns_str = ', '.join(columns)
                    placeholders = ', '.join(['?' for _ in values])
                    
                    sql = f"""
                    INSERT INTO {cls.TABLE_NAME} ({columns_str}, data_atualizacao)
                    VALUES ({placeholders}, CURRENT_TIMESTAMP)
                    """
                    
                    cursor.execute(sql, tuple(values))
                    success_count += 1
                    
                except Exception as e:
                    logger.error(f"Erro ao inserir grade {data.get('curriculo')}/{data.get('curso')}/{data.get('disciplina')}: {e}")
                    error_count += 1
                    continue
            
            conn.commit()
        
        logger.info(f"Batch insert: {success_count} sucessos, {error_count} erros, total {len(data_list)}")
        return success_count
    
    @classmethod
    def get_summary(cls) -> Dict:
        """Retorna estatísticas da tabela"""
        try:
            queries = {
                'total_grades': f"SELECT COUNT(*) FROM {cls.TABLE_NAME}",
                'curriculos_distintos': f"SELECT COUNT(DISTINCT curriculo) FROM {cls.TABLE_NAME}",
                'cursos_distintos': f"SELECT COUNT(DISTINCT curso) FROM {cls.TABLE_NAME}",
                'disciplinas_distintas': f"SELECT COUNT(DISTINCT disciplina) FROM {cls.TABLE_NAME}",
                'obrigatorias': f"SELECT COUNT(*) FROM {cls.TABLE_NAME} WHERE obrigatoria = 'S'",
                'optativas': f"SELECT COUNT(*) FROM {cls.TABLE_NAME} WHERE obrigatoria = 'N'",
                'ultima_atualizacao': f"SELECT MAX(data_atualizacao) FROM {cls.TABLE_NAME}"
            }
            
            results = {}
            for key, query in queries.items():
                result = fetch_one(query, db_path=config.DB_LYCEUM_PATH)
                if result:
                    results[key] = result[0]
                else:
                    results[key] = 0
            
            return results
            
        except Exception as e:
            logger.error(f"Erro ao obter resumo: {e}")
            return {}
    
    @classmethod
    def get_all_grades(cls) -> List[Dict]:
        """Retorna todas as grades da tabela"""
        try:
            sql = f"SELECT * FROM {cls.TABLE_NAME} ORDER BY curriculo, curso, serie_ideal, disciplina"
            results = fetch_all(sql, db_path=config.DB_LYCEUM_PATH)
            
            # Converter para lista de dicionários
            grades = []
            for row in results:
                grade = {}
                # Obter nomes das colunas
                with get_db_connection(db_path=config.DB_LYCEUM_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute(f"PRAGMA table_info({cls.TABLE_NAME})")
                    columns = [col[1] for col in cursor.fetchall()]
                
                for i, col in enumerate(columns):
                    if i < len(row):
                        grade[col] = row[i]
                
                grades.append(grade)
            
            return grades
            
        except Exception as e:
            logger.error(f"Erro ao buscar grades: {e}")
            return []
    
    @classmethod
    def get_by_curriculo_curso(cls, curriculo: str, curso: str) -> List[Dict]:
        """Retorna todas as grades de um currículo e curso específicos"""
        try:
            sql = f"SELECT * FROM {cls.TABLE_NAME} WHERE curriculo = ? AND curso = ? ORDER BY serie_ideal, disciplina"
            results = fetch_all(sql, (curriculo, curso), db_path=config.DB_LYCEUM_PATH)
            
            grades = []
            for row in results:
                grade = {}
                with get_db_connection(db_path=config.DB_LYCEUM_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute(f"PRAGMA table_info({cls.TABLE_NAME})")
                    columns = [col[1] for col in cursor.fetchall()]
                
                for i, col in enumerate(columns):
                    if i < len(row):
                        grade[col] = row[i]
                
                grades.append(grade)
            
            return grades
            
        except Exception as e:
            logger.error(f"Erro ao buscar grades para curriculo={curriculo}, curso={curso}: {e}")
            return []
    
    @classmethod
    def get_by_curso(cls, curso: str) -> List[Dict]:
        """Retorna todas as grades de um curso específico"""
        try:
            sql = f"SELECT * FROM {cls.TABLE_NAME} WHERE curso = ? ORDER BY curriculo, serie_ideal, disciplina"
            results = fetch_all(sql, (curso,), db_path=config.DB_LYCEUM_PATH)
            
            grades = []
            for row in results:
                grade = {}
                with get_db_connection(db_path=config.DB_LYCEUM_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute(f"PRAGMA table_info({cls.TABLE_NAME})")
                    columns = [col[1] for col in cursor.fetchall()]
                
                for i, col in enumerate(columns):
                    if i < len(row):
                        grade[col] = row[i]
                
                grades.append(grade)
            
            return grades
            
        except Exception as e:
            logger.error(f"Erro ao buscar grades do curso {curso}: {e}")
            return []
    
    @classmethod
    def get_by_disciplina(cls, disciplina: str) -> List[Dict]:
        """Retorna todas as grades de uma disciplina específica"""
        try:
            sql = f"SELECT * FROM {cls.TABLE_NAME} WHERE disciplina = ? ORDER BY curriculo, curso, serie_ideal"
            results = fetch_all(sql, (disciplina,), db_path=config.DB_LYCEUM_PATH)
            
            grades = []
            for row in results:
                grade = {}
                with get_db_connection(db_path=config.DB_LYCEUM_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute(f"PRAGMA table_info({cls.TABLE_NAME})")
                    columns = [col[1] for col in cursor.fetchall()]
                
                for i, col in enumerate(columns):
                    if i < len(row):
                        grade[col] = row[i]
                
                grades.append(grade)
            
            return grades
            
        except Exception as e:
            logger.error(f"Erro ao buscar grades da disciplina {disciplina}: {e}")
            return []