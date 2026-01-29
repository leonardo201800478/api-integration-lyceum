#!/usr/bin/env python3
"""
Modelo para tabela LY_TURMA usando o core.database existente
SEM chave primária fixa - similar a LY_CURRICULO e LY_DISCIPLINA
"""
import logging
from typing import List, Dict, Any, Optional
from core.database import get_db_connection, execute_query, fetch_all, fetch_one
from core.config import config

logger = logging.getLogger(__name__)


class LyTurmaModel:
    """Modelo para tabela LY_TURMA - SEM chave primária fixa"""
    
    TABLE_NAME = "LY_TURMA"
    
    # Lista de campos da API para mapeamento
    API_FIELDS = [
        'ano', 'semestre', 'turma', 'disciplina', 'curso', 'curriculo',
        'sit_turma', 'dt_inicio', 'dt_fim', 'dt_criacao', 'dt_ultalt',
        'dt_limite_enturma', 'dt_confirma_dol', 'stamp_atualizacao',
        'num_alunos', 'vagas_calouros', 'vagas_veteranos', 'aulas_previstas',
        'aulas_dadas', 'min_aulas', 'duracao_aula', 'serie', 'nivel',
        'turno', 'horario', 'tem_horario', 'faculdade', 'unidade_responsavel',
        'centro_de_custo', 'disciplina_multipla', 'dependencia', 'especial',
        'turma_integracao', 'em_elaboracao', 'lancamento_historico',
        'permite_choque_horario', 'permite_desfaz_fecham', 'utiliza_indice',
        'utiliza_proc_seletivo', 'exibe_somente_lista_sel', 'interf_ens_dist',
        'nivel_presenca', 'idioma', 'classificacao', 'num_func', 'ult_num_chamada',
        'formula_mf1', 'formula_mf2', 'formula_mf3', 'formula_ca1', 'formula_ca2',
        'formula_ca3', 'obs_formula_mf1', 'obs_formula_mf2', 'obs_formula_mf3',
        'conceito_min1', 'conceito_min2', 'conceito_min3', 'conceito_min_ex',
        'conceito_min_ex2',
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
        """Cria a tabela LY_TURMA se não existir"""
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
            ano INTEGER,
            semestre INTEGER,
            turma TEXT,
            disciplina TEXT,
            curso TEXT,
            curriculo TEXT,
            sit_turma TEXT,
            dt_inicio TEXT,
            dt_fim TEXT,
            dt_criacao TEXT,
            dt_ultalt TEXT,
            dt_limite_enturma TEXT,
            dt_confirma_dol TEXT,
            stamp_atualizacao TEXT,
            num_alunos INTEGER,
            vagas_calouros INTEGER,
            vagas_veteranos INTEGER,
            aulas_previstas INTEGER,
            aulas_dadas INTEGER,
            min_aulas INTEGER,
            duracao_aula INTEGER,
            serie INTEGER,
            nivel TEXT,
            turno TEXT,
            horario TEXT,
            tem_horario TEXT,
            faculdade TEXT,
            unidade_responsavel TEXT,
            centro_de_custo TEXT,
            disciplina_multipla TEXT,
            dependencia TEXT,
            especial TEXT,
            turma_integracao TEXT,
            em_elaboracao TEXT,
            lancamento_historico TEXT,
            permite_choque_horario TEXT,
            permite_desfaz_fecham TEXT,
            utiliza_indice TEXT,
            utiliza_proc_seletivo TEXT,
            exibe_somente_lista_sel TEXT,
            interf_ens_dist TEXT,
            nivel_presenca TEXT,
            idioma TEXT,
            classificacao TEXT,
            num_func INTEGER,
            ult_num_chamada INTEGER,
            formula_mf1 TEXT,
            formula_mf2 TEXT,
            formula_mf3 TEXT,
            formula_ca1 TEXT,
            formula_ca2 TEXT,
            formula_ca3 TEXT,
            obs_formula_mf1 TEXT,
            obs_formula_mf2 TEXT,
            obs_formula_mf3 TEXT,
            conceito_min1 TEXT,
            conceito_min2 TEXT,
            conceito_min3 TEXT,
            conceito_min_ex TEXT,
            conceito_min_ex2 TEXT,
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
            
            # Criar índices para melhor performance (compostos para consultas comuns)
            indexes = [
                f"CREATE INDEX idx_turma_ano_semestre ON {cls.TABLE_NAME}(ano, semestre)",
                f"CREATE INDEX idx_turma_disciplina ON {cls.TABLE_NAME}(disciplina)",
                f"CREATE INDEX idx_turma_curso ON {cls.TABLE_NAME}(curso)",
                f"CREATE INDEX idx_turma_sit_turma ON {cls.TABLE_NAME}(sit_turma)",
                f"CREATE INDEX idx_turma_faculdade ON {cls.TABLE_NAME}(faculdade)",
                f"CREATE INDEX idx_turma_ano_sem_dis_tur ON {cls.TABLE_NAME}(ano, semestre, disciplina, turma)",
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
        """Insere uma nova turma (não verifica duplicatas)"""
        try:
            # Verificar campos que formam a identidade básica de uma turma
            ano = cls._normalize_value(data.get('ano'))
            semestre = cls._normalize_value(data.get('semestre'))
            turma = cls._normalize_value(data.get('turma'))
            disciplina = cls._normalize_value(data.get('disciplina'))
            
            if not all([ano, semestre, turma, disciplina]):
                logger.warning(f"Turma sem campos obrigatórios (ano, semestre, turma, disciplina): {data}")
                return False
            
            # Preparar colunas e valores
            columns = ['ano', 'semestre', 'turma', 'disciplina']
            values = [ano, semestre, turma, disciplina]
            
            # Adicionar outros campos
            for field in cls.API_FIELDS:
                if field not in ['ano', 'semestre', 'turma', 'disciplina']:
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
            logger.error(f"Erro ao inserir turma {data.get('ano')}/{data.get('semestre')}/{data.get('disciplina')}/{data.get('turma')}: {e}")
            return False
    
    @classmethod
    def batch_insert(cls, data_list: List[Dict]) -> int:
        """Insere múltiplas turmas em lote (permite duplicatas)"""
        if not data_list:
            return 0
        
        success_count = 0
        error_count = 0
        
        with get_db_connection(db_path=config.DB_LYCEUM_PATH) as conn:
            cursor = conn.cursor()
            
            for data in data_list:
                try:
                    # Verificar campos que formam a identidade básica de uma turma
                    ano = cls._normalize_value(data.get('ano'))
                    semestre = cls._normalize_value(data.get('semestre'))
                    turma = cls._normalize_value(data.get('turma'))
                    disciplina = cls._normalize_value(data.get('disciplina'))
                    
                    if not all([ano, semestre, turma, disciplina]):
                        logger.warning(f"Turma sem campos obrigatórios: {data}")
                        error_count += 1
                        continue
                    
                    # Preparar colunas e valores
                    columns = ['ano', 'semestre', 'turma', 'disciplina']
                    values = [ano, semestre, turma, disciplina]
                    
                    # Adicionar outros campos
                    for field in cls.API_FIELDS:
                        if field not in ['ano', 'semestre', 'turma', 'disciplina']:
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
                    logger.error(f"Erro ao inserir turma {data.get('ano')}/{data.get('semestre')}/{data.get('disciplina')}/{data.get('turma')}: {e}")
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
                'total_turmas': f"SELECT COUNT(*) FROM {cls.TABLE_NAME}",
                'anos_distintos': f"SELECT COUNT(DISTINCT ano) FROM {cls.TABLE_NAME}",
                'semestres_distintos': f"SELECT COUNT(DISTINCT semestre) FROM {cls.TABLE_NAME}",
                'disciplinas_distintas': f"SELECT COUNT(DISTINCT disciplina) FROM {cls.TABLE_NAME}",
                'turmas_distintas': f"SELECT COUNT(DISTINCT turma) FROM {cls.TABLE_NAME}",
                'turmas_ativas': f"SELECT COUNT(*) FROM {cls.TABLE_NAME} WHERE sit_turma = 'A'",
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
    def get_all_turmas(cls) -> List[Dict]:
        """Retorna todas as turmas da tabela"""
        try:
            sql = f"SELECT * FROM {cls.TABLE_NAME} ORDER BY ano DESC, semestre DESC, disciplina, turma"
            results = fetch_all(sql, db_path=config.DB_LYCEUM_PATH)
            
            # Converter para lista de dicionários
            turmas = []
            for row in results:
                turma = {}
                # Obter nomes das colunas
                with get_db_connection(db_path=config.DB_LYCEUM_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute(f"PRAGMA table_info({cls.TABLE_NAME})")
                    columns = [col[1] for col in cursor.fetchall()]
                
                for i, col in enumerate(columns):
                    if i < len(row):
                        turma[col] = row[i]
                
                turmas.append(turma)
            
            return turmas
            
        except Exception as e:
            logger.error(f"Erro ao buscar turmas: {e}")
            return []
    
    @classmethod
    def get_by_ano_semestre(cls, ano: int, semestre: int) -> List[Dict]:
        """Retorna todas as turmas de um ano/semestre específico"""
        try:
            sql = f"SELECT * FROM {cls.TABLE_NAME} WHERE ano = ? AND semestre = ? ORDER BY disciplina, turma"
            results = fetch_all(sql, (ano, semestre), db_path=config.DB_LYCEUM_PATH)
            
            turmas = []
            for row in results:
                turma = {}
                with get_db_connection(db_path=config.DB_LYCEUM_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute(f"PRAGMA table_info({cls.TABLE_NAME})")
                    columns = [col[1] for col in cursor.fetchall()]
                
                for i, col in enumerate(columns):
                    if i < len(row):
                        turma[col] = row[i]
                
                turmas.append(turma)
            
            return turmas
            
        except Exception as e:
            logger.error(f"Erro ao buscar turmas para {ano}/{semestre}: {e}")
            return []
    
    @classmethod
    def get_by_disciplina(cls, disciplina_code: str) -> List[Dict]:
        """Retorna todas as turmas de uma disciplina específica"""
        try:
            sql = f"SELECT * FROM {cls.TABLE_NAME} WHERE disciplina = ? ORDER BY ano DESC, semestre DESC, turma"
            results = fetch_all(sql, (disciplina_code,), db_path=config.DB_LYCEUM_PATH)
            
            turmas = []
            for row in results:
                turma = {}
                with get_db_connection(db_path=config.DB_LYCEUM_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute(f"PRAGMA table_info({cls.TABLE_NAME})")
                    columns = [col[1] for col in cursor.fetchall()]
                
                for i, col in enumerate(columns):
                    if i < len(row):
                        turma[col] = row[i]
                
                turmas.append(turma)
            
            return turmas
            
        except Exception as e:
            logger.error(f"Erro ao buscar turmas da disciplina {disciplina_code}: {e}")
            return []