#!/usr/bin/env python3
"""
Modelo para tabela LY_TURMA_DOCENTE usando o core.database existente
"""
import logging
from typing import List, Dict, Any
from core.database import get_db_connection, execute_query, fetch_all, fetch_one
from core.config import config

logger = logging.getLogger(__name__)


class LyTurmaDocenteModel:
    """Modelo para tabela LY_TURMA_DOCENTE"""
    
    TABLE_NAME = "LY_TURMA_DOCENTE"
    
    # Lista de campos da API para mapeamento (baseado na documentação fornecida)
    API_FIELDS = [
        'chave', 'ano', 'periodo', 'turma', 'disciplina', 'num_func',
        'funcao', 'carga_hor', 'dt_inicio', 'dt_fim', 'dt_ultalt',
        'observacao', 'usuario',
        # Campos flag
        'fl_field01', 'fl_field02', 'fl_field03', 'fl_field04', 'fl_field05',
        'fl_field06', 'fl_field07', 'fl_field08', 'fl_field09', 'fl_field10',
        'fl_field11', 'fl_field12', 'fl_field13', 'fl_field14', 'fl_field15',
        'fl_field16', 'fl_field17', 'fl_field18', 'fl_field19', 'fl_field20'
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
        """Cria a tabela LY_TURMA_DOCENTE se não existir"""
        # Verificar se a tabela já existe
        table_exists_query = """
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name=?
        """
        
        result = fetch_one(table_exists_query, (cls.TABLE_NAME,), db_path=config.DB_LYCEUM_PATH)
        
        if result:
            logger.info(f"Tabela {cls.TABLE_NAME} já existe")
            return True
        
        # SQL para criar a tabela
        sql = f"""
        CREATE TABLE {cls.TABLE_NAME} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chave INTEGER,
            ano INTEGER,
            periodo INTEGER,
            turma TEXT,
            disciplina TEXT,
            num_func INTEGER,
            funcao TEXT,
            carga_hor INTEGER,
            dt_inicio TEXT,
            dt_fim TEXT,
            dt_ultalt TEXT,
            observacao TEXT,
            usuario TEXT,
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
            fl_field11 TEXT,
            fl_field12 TEXT,
            fl_field13 TEXT,
            fl_field14 TEXT,
            fl_field15 TEXT,
            fl_field16 TEXT,
            fl_field17 TEXT,
            fl_field18 TEXT,
            fl_field19 TEXT,
            fl_field20 TEXT,
            -- Metadados
            data_importacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        try:
            execute_query(sql, db_path=config.DB_LYCEUM_PATH)
            
            # Criar índices para melhor performance
            indexes = [
                f"CREATE INDEX idx_turma_docente_chave ON {cls.TABLE_NAME}(chave)",
                f"CREATE INDEX idx_turma_docente_ano_periodo ON {cls.TABLE_NAME}(ano, periodo)",
                f"CREATE INDEX idx_turma_docente_turma ON {cls.TABLE_NAME}(turma)",
                f"CREATE INDEX idx_turma_docente_disciplina ON {cls.TABLE_NAME}(disciplina)",
                f"CREATE INDEX idx_turma_docente_num_func ON {cls.TABLE_NAME}(num_func)",
            ]
            
            for index_sql in indexes:
                try:
                    execute_query(index_sql, db_path=config.DB_LYCEUM_PATH)
                except Exception as e:
                    logger.warning(f"Erro ao criar índice: {e}")
            
            logger.info(f"Tabela {cls.TABLE_NAME} criada com sucesso")
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
    def batch_insert(cls, data_list: List[Dict]) -> int:
        """Insere múltiplos registros em lote"""
        if not data_list:
            return 0
        
        success_count = 0
        error_count = 0
        
        with get_db_connection(db_path=config.DB_LYCEUM_PATH) as conn:
            cursor = conn.cursor()
            
            for data in data_list:
                try:
                    # Verificar campos obrigatórios
                    chave = cls._normalize_value(data.get('chave'))
                    
                    if not chave:
                        logger.warning(f"Registro sem chave: {data}")
                        error_count += 1
                        continue
                    
                    # Preparar colunas e valores
                    columns = ['chave']
                    values = [chave]
                    
                    # Adicionar outros campos
                    for field in cls.API_FIELDS:
                        if field != 'chave':
                            value = cls._normalize_value(data.get(field))
                            if value is not None:
                                columns.append(field)
                                values.append(value)
                    
                    # Construir query de INSERT
                    columns_str = ', '.join(columns)
                    placeholders = ', '.join(['?' for _ in values])
                    
                    sql = f"""
                    INSERT INTO {cls.TABLE_NAME} ({columns_str}, data_atualizacao)
                    VALUES ({placeholders}, CURRENT_TIMESTAMP)
                    """
                    
                    cursor.execute(sql, tuple(values))
                    success_count += 1
                    
                except Exception as e:
                    logger.error(f"Erro ao inserir turma_docente chave={data.get('chave')}: {e}")
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
                'total_registros': f"SELECT COUNT(*) FROM {cls.TABLE_NAME}",
                'turmas_distintas': f"SELECT COUNT(DISTINCT turma) FROM {cls.TABLE_NAME}",
                'disciplinas_distintas': f"SELECT COUNT(DISTINCT disciplina) FROM {cls.TABLE_NAME}",
                'docentes_distintos': f"SELECT COUNT(DISTINCT num_func) FROM {cls.TABLE_NAME}",
                'anos_distintos': f"SELECT COUNT(DISTINCT ano) FROM {cls.TABLE_NAME}",
                'periodos_distintos': f"SELECT COUNT(DISTINCT periodo) FROM {cls.TABLE_NAME}",
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