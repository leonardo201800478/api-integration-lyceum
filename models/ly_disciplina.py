#!/usr/bin/env python3
"""
Modelo para tabela LY_DISCIPLINA usando o core.database existente
SEM chave primária fixa - similar a LY_CURRICULO
"""
import logging
from typing import List, Dict, Any, Optional
from core.database import get_db_connection, execute_query, fetch_all, fetch_one
from core.config import config

logger = logging.getLogger(__name__)


class LyDisciplinaModel:
    """Modelo para tabela LY_DISCIPLINA - SEM chave primária fixa"""
    
    TABLE_NAME = "LY_DISCIPLINA"
    
    # Lista de campos da API para mapeamento
    API_FIELDS = [
        'disciplina', 'nome', 'nome_compl', 'nome_fantasia', 'tipo',
        'ativo', 'servico', 'faculdade', 'depto', 'componente',
        'area_conhecimento', 'creditos', 'horas_aula', 'horas_lab',
        'horas_ativ', 'horas_estagio', 'aulas_semanais',
        'aulas_sem_aula', 'aulas_sem_lab', 'aulas_sem_ativ',
        'estagio', 'tipo_estagio', 'multipla', 'categoria_enturmacao',
        'tem_nota', 'tipo_nota', 'tem_freq', 'tem_aval_descritiva',
        'aval_competencia', 'conceito_min1', 'conceito_min2',
        'conceito_min3', 'conceito_min_ex', 'conceito_min_ex2',
        'nota_max', 'nota_max_media', 'n_casas_dec', 'n_casas_dec_media',
        'trunca_media', 'grupo_nota', 'grupo_media', 'pim',
        'formula_mf1', 'formula_mf2', 'formula_mf3', 'formula_ca1',
        'formula_ca2', 'formula_ca3', 'formula_equiv', 'formula_prereq',
        'obs_formula_mf1', 'obs_formula_mf2', 'obs_formula_mf3',
        'perc_presmin', 'falta_diaria', 'prioriza_freq',
        'permite_manter_horario', 'verifica_horario', 'copia_nota_subturma',
        'prazo_divulgacao', 'prazo_revisao', 'campo01',
        'stamp_atualizacao',
        # Campos flag
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
        """Cria a tabela LY_DISCIPLINA se não existir"""
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
            disciplina TEXT NOT NULL,
            nome TEXT,
            nome_compl TEXT,
            nome_fantasia TEXT,
            tipo TEXT,
            ativo TEXT,
            servico TEXT,
            faculdade TEXT,
            depto TEXT,
            componente TEXT,
            area_conhecimento TEXT,
            creditos INTEGER,
            horas_aula INTEGER,
            horas_lab INTEGER,
            horas_ativ INTEGER,
            horas_estagio INTEGER,
            aulas_semanais INTEGER,
            aulas_sem_aula INTEGER,
            aulas_sem_lab INTEGER,
            aulas_sem_ativ INTEGER,
            estagio TEXT,
            tipo_estagio TEXT,
            multipla TEXT,
            categoria_enturmacao TEXT,
            tem_nota TEXT,
            tipo_nota TEXT,
            tem_freq TEXT,
            tem_aval_descritiva TEXT,
            aval_competencia TEXT,
            conceito_min1 TEXT,
            conceito_min2 TEXT,
            conceito_min3 TEXT,
            conceito_min_ex TEXT,
            conceito_min_ex2 TEXT,
            nota_max TEXT,
            nota_max_media TEXT,
            n_casas_dec INTEGER,
            n_casas_dec_media INTEGER,
            trunca_media TEXT,
            grupo_nota TEXT,
            grupo_media TEXT,
            pim TEXT,
            formula_mf1 TEXT,
            formula_mf2 TEXT,
            formula_mf3 TEXT,
            formula_ca1 TEXT,
            formula_ca2 TEXT,
            formula_ca3 TEXT,
            formula_equiv TEXT,
            formula_prereq TEXT,
            obs_formula_mf1 TEXT,
            obs_formula_mf2 TEXT,
            obs_formula_mf3 TEXT,
            perc_presmin REAL,
            falta_diaria TEXT,
            prioriza_freq TEXT,
            permite_manter_horario TEXT,
            verifica_horario TEXT,
            copia_nota_subturma TEXT,
            prazo_divulgacao INTEGER,
            prazo_revisao INTEGER,
            campo01 TEXT,
            stamp_atualizacao TEXT,
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
            
            # Criar índices para melhor performance
            indexes = [
                f"CREATE INDEX idx_disciplina_codigo ON {cls.TABLE_NAME}(disciplina)",
                f"CREATE INDEX idx_disciplina_nome ON {cls.TABLE_NAME}(nome)",
                f"CREATE INDEX idx_disciplina_ativo ON {cls.TABLE_NAME}(ativo)",
                f"CREATE INDEX idx_disciplina_faculdade ON {cls.TABLE_NAME}(faculdade)",
                f"CREATE INDEX idx_disciplina_depto ON {cls.TABLE_NAME}(depto)",
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
        """Insere uma nova disciplina (não verifica duplicatas)"""
        try:
            # Verificar campo obrigatório
            disciplina_id = cls._normalize_value(data.get('disciplina'))
            
            if not disciplina_id:
                logger.warning(f"Disciplina sem código: {data}")
                return False
            
            # Preparar colunas e valores
            columns = ['disciplina']
            values = [disciplina_id]
            
            # Adicionar outros campos
            for field in cls.API_FIELDS:
                if field != 'disciplina':
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
            logger.error(f"Erro ao inserir disciplina {data.get('disciplina')}: {e}")
            return False
    
    @classmethod
    def batch_insert(cls, data_list: List[Dict]) -> int:
        """Insere múltiplas disciplinas em lote (permite duplicatas)"""
        if not data_list:
            return 0
        
        success_count = 0
        error_count = 0
        
        with get_db_connection(db_path=config.DB_LYCEUM_PATH) as conn:
            cursor = conn.cursor()
            
            for data in data_list:
                try:
                    # Verificar campo obrigatório
                    disciplina_id = cls._normalize_value(data.get('disciplina'))
                    
                    if not disciplina_id:
                        logger.warning(f"Disciplina sem código: {data}")
                        error_count += 1
                        continue
                    
                    # Preparar colunas e valores
                    columns = ['disciplina']
                    values = [disciplina_id]
                    
                    # Adicionar outros campos
                    for field in cls.API_FIELDS:
                        if field != 'disciplina':
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
                    logger.error(f"Erro ao inserir disciplina {data.get('disciplina')}: {e}")
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
                'total_disciplinas': f"SELECT COUNT(*) FROM {cls.TABLE_NAME}",
                'disciplinas_distintas': f"SELECT COUNT(DISTINCT disciplina) FROM {cls.TABLE_NAME}",
                'disciplinas_ativas': f"SELECT COUNT(*) FROM {cls.TABLE_NAME} WHERE ativo = 'S'",
                'faculdades_distintas': f"SELECT COUNT(DISTINCT faculdade) FROM {cls.TABLE_NAME} WHERE faculdade IS NOT NULL",
                'departamentos_distintos': f"SELECT COUNT(DISTINCT depto) FROM {cls.TABLE_NAME} WHERE depto IS NOT NULL",
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
    def get_all_disciplinas(cls) -> List[Dict]:
        """Retorna todas as disciplinas da tabela"""
        try:
            sql = f"SELECT * FROM {cls.TABLE_NAME} ORDER BY disciplina"
            results = fetch_all(sql, db_path=config.DB_LYCEUM_PATH)
            
            # Converter para lista de dicionários
            disciplinas = []
            for row in results:
                disciplina = {}
                # Obter nomes das colunas
                with get_db_connection(db_path=config.DB_LYCEUM_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute(f"PRAGMA table_info({cls.TABLE_NAME})")
                    columns = [col[1] for col in cursor.fetchall()]
                
                for i, col in enumerate(columns):
                    if i < len(row):
                        disciplina[col] = row[i]
                
                disciplinas.append(disciplina)
            
            return disciplinas
            
        except Exception as e:
            logger.error(f"Erro ao buscar disciplinas: {e}")
            return []
    
    @classmethod
    def get_by_disciplina(cls, disciplina_code: str) -> List[Dict]:
        """Retorna todas as ocorrências de uma disciplina específica"""
        try:
            sql = f"SELECT * FROM {cls.TABLE_NAME} WHERE disciplina = ? ORDER BY id"
            results = fetch_all(sql, (disciplina_code,), db_path=config.DB_LYCEUM_PATH)
            
            disciplinas = []
            for row in results:
                disciplina = {}
                with get_db_connection(db_path=config.DB_LYCEUM_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute(f"PRAGMA table_info({cls.TABLE_NAME})")
                    columns = [col[1] for col in cursor.fetchall()]
                
                for i, col in enumerate(columns):
                    if i < len(row):
                        disciplina[col] = row[i]
                
                disciplinas.append(disciplina)
            
            return disciplinas
            
        except Exception as e:
            logger.error(f"Erro ao buscar disciplina {disciplina_code}: {e}")
            return []
    
    @classmethod
    def get_disciplinas_ativas(cls) -> List[Dict]:
        """Retorna todas as disciplinas ativas"""
        try:
            sql = f"SELECT * FROM {cls.TABLE_NAME} WHERE ativo = 'S' ORDER BY disciplina"
            results = fetch_all(sql, db_path=config.DB_LYCEUM_PATH)
            
            disciplinas = []
            for row in results:
                disciplina = {}
                with get_db_connection(db_path=config.DB_LYCEUM_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute(f"PRAGMA table_info({cls.TABLE_NAME})")
                    columns = [col[1] for col in cursor.fetchall()]
                
                for i, col in enumerate(columns):
                    if i < len(row):
                        disciplina[col] = row[i]
                
                disciplinas.append(disciplina)
            
            return disciplinas
            
        except Exception as e:
            logger.error(f"Erro ao buscar disciplinas ativas: {e}")
            return []