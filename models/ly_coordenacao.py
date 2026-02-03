"""
Modelo para tabela LY_COORDENACAO usando o core.database existente
SEM constraints NOT NULL - traz todos os dados da API
"""
import logging
from typing import List, Dict, Any, Optional
from core.database import get_db_connection, execute_query, fetch_all, fetch_one
from core.config import config

logger = logging.getLogger(__name__)


class LyCoordenacaoModel:
    """Modelo para tabela LY_COORDENACAO - Sem constraints NOT NULL"""
    
    TABLE_NAME = "LY_COORDENACAO"
    
    # Lista de campos da API para mapeamento
    API_FIELDS = [
        'chave', 'classificacao', 'curriculo', 'curso', 'dt_fim', 'dt_ini',
        'num_func', 'participacao_porcent', 'tipo_coord', 'turno', 'unid_fisica'
    ]
    
    @classmethod
    def _normalize_value(cls, value: Any) -> Any:
        """Normaliza valores para inserção no banco"""
        if value is None:
            return None
        
        # Converte strings removendo espaços extras
        if isinstance(value, str):
            value = value.strip()
            if value == '':
                return None
        
        # Converte números
        if isinstance(value, (int, float)):
            return value
        
        # Para outros tipos, converte para string
        return str(value)
    
    @classmethod
    def drop_and_recreate_table(cls):
        """Remove a tabela se existir e cria uma nova - SEM constraints NOT NULL"""
        try:
            # Remove a tabela se existir
            drop_sql = f"DROP TABLE IF EXISTS {cls.TABLE_NAME}"
            execute_query(drop_sql, db_path=config.DB_LYCEUM_PATH)
            logger.info(f"Tabela {cls.TABLE_NAME} removida")
            
            # SQL para criar a tabela SEM constraints NOT NULL
            sql = f"""
            CREATE TABLE {cls.TABLE_NAME} (
                chave TEXT,
                classificacao TEXT,
                curriculo TEXT,
                curso TEXT,
                dt_fim TEXT,
                dt_ini TEXT,
                num_func TEXT,
                participacao_porcent REAL,
                tipo_coord TEXT,
                turno TEXT,
                unid_fisica TEXT,
                -- Metadados
                data_importacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            
            execute_query(sql, db_path=config.DB_LYCEUM_PATH)
            
            # Criar índices para melhor performance
            indexes = [
                f"CREATE INDEX idx_coordenacao_chave ON {cls.TABLE_NAME}(chave)",
                f"CREATE INDEX idx_coordenacao_curso ON {cls.TABLE_NAME}(curso)",
                f"CREATE INDEX idx_coordenacao_num_func ON {cls.TABLE_NAME}(num_func)",
                f"CREATE INDEX idx_coordenacao_tipo_coord ON {cls.TABLE_NAME}(tipo_coord)",
                f"CREATE INDEX idx_coordenacao_dt_ini ON {cls.TABLE_NAME}(dt_ini)"
            ]
            
            for index_sql in indexes:
                try:
                    execute_query(index_sql, db_path=config.DB_LYCEUM_PATH)
                except Exception as e:
                    logger.warning(f"Erro ao criar índice: {e}")
            
            logger.info(f"Tabela {cls.TABLE_NAME} criada com sucesso (sem constraints NOT NULL)")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao recriar tabela {cls.TABLE_NAME}: {e}")
            return False
    
    @classmethod
    def create_table(cls):
        """Verifica se a tabela existe e a recria se necessário"""
        try:
            # Verificar se a tabela já existe
            table_exists_query = """
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name=?
            """
            
            result = fetch_one(table_exists_query, (cls.TABLE_NAME,), db_path=config.DB_LYCEUM_PATH)
            
            if not result:
                # Cria nova tabela
                return cls.drop_and_recreate_table()
            else:
                # Tabela já existe
                logger.info(f"Tabela {cls.TABLE_NAME} já existe")
                
                # Verificar estrutura da tabela
                check_structure_sql = f"PRAGMA table_info({cls.TABLE_NAME})"
                columns_info = fetch_all(check_structure_sql, db_path=config.DB_LYCEUM_PATH)
                
                # Lista de colunas que devem existir
                expected_columns = cls.API_FIELDS + ['data_importacao', 'data_atualizacao']
                existing_columns = [col[1] for col in columns_info]
                
                # Verifica se todas as colunas esperadas existem
                missing_columns = [col for col in expected_columns if col not in existing_columns]
                
                if missing_columns:
                    logger.warning(f"Tabela {cls.TABLE_NAME} faltando colunas: {missing_columns}")
                    return cls.drop_and_recreate_table()
                
                return True
                
        except Exception as e:
            logger.error(f"Erro ao verificar tabela {cls.TABLE_NAME}: {e}")
            return cls.drop_and_recreate_table()
    
    @classmethod
    def batch_insert(cls, data_list: List[Dict]) -> int:
        """Insere múltiplos registros em lote - aceita qualquer campo"""
        if not data_list:
            return 0
        
        success_count = 0
        error_count = 0
        
        with get_db_connection(db_path=config.DB_LYCEUM_PATH) as conn:
            cursor = conn.cursor()
            
            for i, data in enumerate(data_list, 1):
                try:
                    if not isinstance(data, dict):
                        logger.warning(f"Registro {i} não é um dicionário: {type(data)}")
                        error_count += 1
                        continue
                    
                    # Prepara todos os campos disponíveis nos dados
                    columns = []
                    values = []
                    placeholders = []
                    
                    # Adiciona todos os campos que existem nos dados
                    for field, value in data.items():
                        normalized_value = cls._normalize_value(value)
                        if normalized_value is not None:
                            columns.append(field)
                            values.append(normalized_value)
                            placeholders.append('?')
                    
                    # Se não há campos, insere um registro vazio?
                    if not columns:
                        # Insere registro vazio com apenas metadados
                        columns = ['data_atualizacao']
                        values = ['CURRENT_TIMESTAMP']
                        placeholders = ['CURRENT_TIMESTAMP']
                    
                    # Adiciona campos de metadados se não existirem
                    if 'data_atualizacao' not in columns:
                        columns.append('data_atualizacao')
                        values.append('CURRENT_TIMESTAMP')
                        placeholders.append('CURRENT_TIMESTAMP')
                    
                    if 'data_importacao' not in columns:
                        columns.append('data_importacao')
                        values.append('CURRENT_TIMESTAMP')
                        placeholders.append('CURRENT_TIMESTAMP')
                    
                    # Construir query INSERT
                    columns_str = ', '.join(columns)
                    placeholders_str = ', '.join(placeholders)
                    
                    sql = f"""
                    INSERT INTO {cls.TABLE_NAME} ({columns_str})
                    VALUES ({placeholders_str})
                    """
                    
                    # Valores para executar (exclui CURRENT_TIMESTAMP)
                    execute_values = []
                    for col, val in zip(columns, values):
                        if val != 'CURRENT_TIMESTAMP':
                            execute_values.append(val)
                    
                    cursor.execute(sql, tuple(execute_values))
                    success_count += 1
                    
                    # Log a cada 10 registros
                    if i % 10 == 0:
                        logger.debug(f"Processados {i}/{len(data_list)} registros")
                    
                except Exception as e:
                    logger.error(f"Erro ao processar registro {i}: {e}")
                    logger.debug(f"Dados do registro {i}: {data}")
                    error_count += 1
                    continue
            
            conn.commit()
        
        logger.info(f"Batch insert: {success_count} sucessos, {error_count} erros, total {len(data_list)}")
        return success_count
    
    @classmethod
    def clear_table(cls):
        """Limpa todos os registros da tabela"""
        try:
            sql = f"DELETE FROM {cls.TABLE_NAME}"
            execute_query(sql, db_path=config.DB_LYCEUM_PATH)
            logger.info(f"Tabela {cls.TABLE_NAME} limpa com sucesso")
            return True
        except Exception as e:
            logger.error(f"Erro ao limpar tabela {cls.TABLE_NAME}: {e}")
            return False
    
    @classmethod
    def get_summary(cls) -> Dict:
        """Retorna estatísticas da tabela"""
        try:
            queries = {
                'total_coordenacoes': f"SELECT COUNT(*) FROM {cls.TABLE_NAME}",
                'cursos_distintos': f"SELECT COUNT(DISTINCT curso) FROM {cls.TABLE_NAME}",
                'funcionarios_distintos': f"SELECT COUNT(DISTINCT num_func) FROM {cls.TABLE_NAME}",
                'tipos_coordenacao': f"SELECT COUNT(DISTINCT tipo_coord) FROM {cls.TABLE_NAME}",
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