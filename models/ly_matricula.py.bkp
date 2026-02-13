#!/usr/bin/env python3
"""
Modelo para tabela LY_MATRICULA usando o core.database existente
SEM chave primária fixa - similar a LY_TURMA
"""
import logging
from typing import List, Dict, Any, Optional
from core.database import get_db_connection, execute_query, fetch_all, fetch_one
from core.config import config

logger = logging.getLogger(__name__)


class LyMatriculaModel:
    """Modelo para tabela LY_MATRICULA - SEM chave primária fixa"""
    
    TABLE_NAME = "LY_MATRICULA"
    
    # Lista de campos da API para mapeamento (baseado na documentação fornecida)
    API_FIELDS = [
        'aluno', 'ano', 'semestre', 'turma', 'disciplina',
        'cobranca_sep', 'conceito_fim', 'conceito_fim_num',
        'dt_insercao', 'dt_matricula', 'dt_reabertura', 'dt_ultalt',
        'grupo_eletiva', 'lanc_deb', 'num_chamada', 'obs',
        'perc_presfim', 'plano_pagto_pad_esp', 'serie_calculo',
        'sit_detalhe', 'sit_matricula', 'subturma1', 'subturma2',
        'tipo_aprovacao', 'tot_aulas',
        # Campos flag (conforme documentação)
        'fl_field01', 'fl_field02', 'fl_field03', 'fl_field04', 'fl_field05',
        'fl_field06', 'fl_field07', 'fl_field08', 'fl_field09', 'fl_field10'
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
        """Cria a tabela LY_MATRICULA se não existir"""
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
            aluno TEXT,
            ano INTEGER,
            semestre INTEGER,
            turma TEXT,
            disciplina TEXT,
            cobranca_sep TEXT,
            conceito_fim TEXT,
            conceito_fim_num REAL,
            dt_insercao TEXT,
            dt_matricula TEXT,
            dt_reabertura TEXT,
            dt_ultalt TEXT,
            grupo_eletiva TEXT,
            lanc_deb REAL,
            num_chamada INTEGER,
            obs TEXT,
            perc_presfim REAL,
            plano_pagto_pad_esp TEXT,
            serie_calculo INTEGER,
            sit_detalhe TEXT,
            sit_matricula TEXT,
            subturma1 TEXT,
            subturma2 TEXT,
            tipo_aprovacao TEXT,
            tot_aulas INTEGER,
            -- Campos flag
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
            -- Metadados
            data_importacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        try:
            execute_query(sql, db_path=config.DB_LYCEUM_PATH)
            
            # Criar índices para melhor performance (compostos para consultas comuns)
            indexes = [
                f"CREATE INDEX idx_matricula_ano_semestre ON {cls.TABLE_NAME}(ano, semestre)",
                f"CREATE INDEX idx_matricula_aluno ON {cls.TABLE_NAME}(aluno)",
                f"CREATE INDEX idx_matricula_turma ON {cls.TABLE_NAME}(turma)",
                f"CREATE INDEX idx_matricula_disciplina ON {cls.TABLE_NAME}(disciplina)",
                f"CREATE INDEX idx_matricula_sit_matricula ON {cls.TABLE_NAME}(sit_matricula)",
                f"CREATE INDEX idx_matricula_ano_sem_aluno ON {cls.TABLE_NAME}(ano, semestre, aluno)",
                f"CREATE INDEX idx_matricula_ano_sem_turma ON {cls.TABLE_NAME}(ano, semestre, turma)",
                f"CREATE INDEX idx_matricula_turma_disciplina ON {cls.TABLE_NAME}(turma, disciplina)",
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
        """Insere uma nova matrícula (não verifica duplicatas)"""
        try:
            # Verificar campos que formam a identidade básica de uma matrícula
            aluno = cls._normalize_value(data.get('aluno'))
            ano = cls._normalize_value(data.get('ano'))
            semestre = cls._normalize_value(data.get('semestre'))
            turma = cls._normalize_value(data.get('turma'))
            disciplina = cls._normalize_value(data.get('disciplina'))
            
            if not all([aluno, ano, semestre, turma, disciplina]):
                logger.warning(f"Matrícula sem campos obrigatórios (aluno, ano, semestre, turma, disciplina): {data}")
                return False
            
            # Preparar colunas e valores
            columns = ['aluno', 'ano', 'semestre', 'turma', 'disciplina']
            values = [aluno, ano, semestre, turma, disciplina]
            
            # Adicionar outros campos
            for field in cls.API_FIELDS:
                if field not in ['aluno', 'ano', 'semestre', 'turma', 'disciplina']:
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
            logger.error(f"Erro ao inserir matrícula {data.get('aluno')}/{data.get('ano')}/{data.get('semestre')}/{data.get('disciplina')}/{data.get('turma')}: {e}")
            return False
    
    @classmethod
    def batch_insert(cls, data_list: List[Dict]) -> int:
        """Insere múltiplas matrículas em lote (permite duplicatas)"""
        if not data_list:
            return 0
        
        success_count = 0
        error_count = 0
        
        with get_db_connection(db_path=config.DB_LYCEUM_PATH) as conn:
            cursor = conn.cursor()
            
            for data in data_list:
                try:
                    # Verificar campos que formam a identidade básica de uma matrícula
                    aluno = cls._normalize_value(data.get('aluno'))
                    ano = cls._normalize_value(data.get('ano'))
                    semestre = cls._normalize_value(data.get('semestre'))
                    turma = cls._normalize_value(data.get('turma'))
                    disciplina = cls._normalize_value(data.get('disciplina'))
                    
                    if not all([aluno, ano, semestre, turma, disciplina]):
                        logger.warning(f"Matrícula sem campos obrigatórios: {data}")
                        error_count += 1
                        continue
                    
                    # Preparar colunas e valores
                    columns = ['aluno', 'ano', 'semestre', 'turma', 'disciplina']
                    values = [aluno, ano, semestre, turma, disciplina]
                    
                    # Adicionar outros campos
                    for field in cls.API_FIELDS:
                        if field not in ['aluno', 'ano', 'semestre', 'turma', 'disciplina']:
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
                    logger.error(f"Erro ao inserir matrícula {data.get('aluno')}/{data.get('ano')}/{data.get('semestre')}/{data.get('disciplina')}/{data.get('turma')}: {e}")
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
                'total_matriculas': f"SELECT COUNT(*) FROM {cls.TABLE_NAME}",
                'alunos_distintos': f"SELECT COUNT(DISTINCT aluno) FROM {cls.TABLE_NAME}",
                'turmas_distintas': f"SELECT COUNT(DISTINCT turma) FROM {cls.TABLE_NAME}",
                'disciplinas_distintas': f"SELECT COUNT(DISTINCT disciplina) FROM {cls.TABLE_NAME}",
                'anos_distintos': f"SELECT COUNT(DISTINCT ano) FROM {cls.TABLE_NAME}",
                'semestres_distintos': f"SELECT COUNT(DISTINCT semestre) FROM {cls.TABLE_NAME}",
                'matriculas_ativas': f"SELECT COUNT(*) FROM {cls.TABLE_NAME} WHERE sit_matricula = 'A'",
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
    def get_all_matriculas(cls) -> List[Dict]:
        """Retorna todas as matrículas da tabela"""
        try:
            sql = f"SELECT * FROM {cls.TABLE_NAME} ORDER BY ano DESC, semestre DESC, aluno, disciplina"
            results = fetch_all(sql, db_path=config.DB_LYCEUM_PATH)
            
            # Converter para lista de dicionários
            matriculas = []
            for row in results:
                matricula = {}
                # Obter nomes das colunas
                with get_db_connection(db_path=config.DB_LYCEUM_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute(f"PRAGMA table_info({cls.TABLE_NAME})")
                    columns = [col[1] for col in cursor.fetchall()]
                
                for i, col in enumerate(columns):
                    if i < len(row):
                        matricula[col] = row[i]
                
                matriculas.append(matricula)
            
            return matriculas
            
        except Exception as e:
            logger.error(f"Erro ao buscar matrículas: {e}")
            return []
    
    @classmethod
    def get_by_ano_semestre(cls, ano: int, semestre: int) -> List[Dict]:
        """Retorna todas as matrículas de um ano/semestre específico"""
        try:
            sql = f"SELECT * FROM {cls.TABLE_NAME} WHERE ano = ? AND semestre = ? ORDER BY aluno, disciplina"
            results = fetch_all(sql, (ano, semestre), db_path=config.DB_LYCEUM_PATH)
            
            matriculas = []
            for row in results:
                matricula = {}
                with get_db_connection(db_path=config.DB_LYCEUM_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute(f"PRAGMA table_info({cls.TABLE_NAME})")
                    columns = [col[1] for col in cursor.fetchall()]
                
                for i, col in enumerate(columns):
                    if i < len(row):
                        matricula[col] = row[i]
                
                matriculas.append(matricula)
            
            return matriculas
            
        except Exception as e:
            logger.error(f"Erro ao buscar matrículas para {ano}/{semestre}: {e}")
            return []
    
    @classmethod
    def get_by_aluno(cls, aluno_code: str) -> List[Dict]:
        """Retorna todas as matrículas de um aluno específico"""
        try:
            sql = f"SELECT * FROM {cls.TABLE_NAME} WHERE aluno = ? ORDER BY ano DESC, semestre DESC, disciplina"
            results = fetch_all(sql, (aluno_code,), db_path=config.DB_LYCEUM_PATH)
            
            matriculas = []
            for row in results:
                matricula = {}
                with get_db_connection(db_path=config.DB_LYCEUM_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute(f"PRAGMA table_info({cls.TABLE_NAME})")
                    columns = [col[1] for col in cursor.fetchall()]
                
                for i, col in enumerate(columns):
                    if i < len(row):
                        matricula[col] = row[i]
                
                matriculas.append(matricula)
            
            return matriculas
            
        except Exception as e:
            logger.error(f"Erro ao buscar matrículas do aluno {aluno_code}: {e}")
            return []