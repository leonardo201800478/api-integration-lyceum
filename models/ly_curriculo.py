#!/usr/bin/env python3
"""
Modelo para tabela LY_CURRICULO usando o core.database existente
SEM CHAVE PRIMÁRIA - para permitir múltiplos registros com o mesmo currículo/curso
"""
import logging
from typing import List, Dict, Any, Optional
from core.database import get_db_connection, execute_query, fetch_all, fetch_one
from core.config import config

logger = logging.getLogger(__name__)


class LyCurriculoModel:
    """Modelo para tabela LY_CURRICULO SEM chave primária"""
    
    TABLE_NAME = "LY_CURRICULO"
    
    # Lista de campos da API para mapeamento
    API_FIELDS = [
        'curriculo', 'curso', 'turno', 'prazo_ideal', 'prazo_max',
        'ano_ini', 'sem_ini', 'regime', 'aulas_previstas', 'creditos',
        'situacao', 'stamp_atualizacao', 'dt_homolog', 'dt_extincao',
        'modalidade', 'servico', 'valor', 'codigo_secundario', 'nome_secundario',
        'classificacao', 'habilinep', 'pesquisa', 'tese_dissertacao',
        'tipo_prazo_concl', 'tipo_prazo_orien', 'prazo_conc_prev',
        'prazo_desig_orien', 'prazo_max_adap', 'unid_prazo_max_adap',
        'retem_serie', 'serie_max_orient', 'ativ_compl_ch', 'ativ_compl_creditos',
        'perc_ch_pres', 'perc_ch_semi_pres', 'perc_ch_nao_pres',
        'ver_ch_integracao', 'ver_cred_integracao', 'max_alunos', 'min_alunos',
        'num_disc_atras_prog', 'tranc_max', 'tranc_cons_max', 'tranc_max_discip',
        'canc_max_discip', 'atlz_max_discip', 'n_max_dias_tranc',
        'tranc_interv_data', 'tranca_primeiro_periodo', 'excecao_trancamento',
        'permite_cancelamento', 'credmin_matr', 'credmin_foragrade',
        'credmax_foragrade', 'ratear_mens', 'ratear_desc',
        'matr_obrig_todas_discip_serie', 'restringe_unid_fis', 'obs',
        'emp_cnpj', 'emp_endereco', 'emp_end_num', 'emp_end_compl',
        'emp_bairro', 'emp_cep', 'emp_municipio', 'emp_fone', 'emp_contato',
        'indice', 'colecao_livros', 'fl_field01', 'fl_field02', 'fl_field03',
        'fl_field04', 'fl_field05', 'fl_field06', 'fl_field07', 'fl_field08',
        'fl_field09', 'fl_field10'
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
        """Cria a tabela LY_CURRICULO sem chave primária"""
        # Verificar se a tabela já existe
        table_exists_query = """
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name=?
        """
        
        result = fetch_one(table_exists_query, (cls.TABLE_NAME,), db_path=config.DB_LYCEUM_PATH)
        
        if result:
            logger.info(f"Tabela {cls.TABLE_NAME} já existe")
            return True
        
        # SQL para criar a tabela SEM chave primária
        sql = f"""
        CREATE TABLE {cls.TABLE_NAME} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            curriculo TEXT NOT NULL,
            curso TEXT NOT NULL,
            turno TEXT,
            prazo_ideal INTEGER,
            prazo_max INTEGER,
            ano_ini INTEGER,
            sem_ini INTEGER,
            regime TEXT,
            aulas_previstas INTEGER,
            creditos INTEGER,
            situacao TEXT,
            stamp_atualizacao TEXT,
            dt_homolog TEXT,
            dt_extincao TEXT,
            modalidade TEXT,
            servico TEXT,
            valor TEXT,
            codigo_secundario TEXT,
            nome_secundario TEXT,
            classificacao TEXT,
            habilinep TEXT,
            pesquisa TEXT,
            tese_dissertacao TEXT,
            tipo_prazo_concl TEXT,
            tipo_prazo_orien TEXT,
            prazo_conc_prev INTEGER,
            prazo_desig_orien INTEGER,
            prazo_max_adap INTEGER,
            unid_prazo_max_adap TEXT,
            retem_serie INTEGER,
            serie_max_orient INTEGER,
            ativ_compl_ch INTEGER,
            ativ_compl_creditos INTEGER,
            perc_ch_pres REAL,
            perc_ch_semi_pres REAL,
            perc_ch_nao_pres REAL,
            ver_ch_integracao TEXT,
            ver_cred_integracao TEXT,
            max_alunos INTEGER,
            min_alunos INTEGER,
            num_disc_atras_prog INTEGER,
            tranc_max INTEGER,
            tranc_cons_max INTEGER,
            tranc_max_discip INTEGER,
            canc_max_discip INTEGER,
            atlz_max_discip INTEGER,
            n_max_dias_tranc INTEGER,
            tranc_interv_data TEXT,
            tranca_primeiro_periodo TEXT,
            excecao_trancamento TEXT,
            permite_cancelamento TEXT,
            credmin_matr INTEGER,
            credmin_foragrade INTEGER,
            credmax_foragrade INTEGER,
            ratear_mens TEXT,
            ratear_desc TEXT,
            matr_obrig_todas_discip_serie TEXT,
            restringe_unid_fis TEXT,
            obs TEXT,
            emp_cnpj TEXT,
            emp_endereco TEXT,
            emp_end_num TEXT,
            emp_end_compl TEXT,
            emp_bairro TEXT,
            emp_cep TEXT,
            emp_municipio TEXT,
            emp_fone TEXT,
            emp_contato TEXT,
            indice TEXT,
            colecao_livros TEXT,
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
            data_importacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        try:
            execute_query(sql, db_path=config.DB_LYCEUM_PATH)
            
            # Criar índices para melhor performance (mas não únicos)
            indexes = [
                f"CREATE INDEX idx_curriculo_curso ON {cls.TABLE_NAME}(curriculo, curso)",
                f"CREATE INDEX idx_curriculo_situacao ON {cls.TABLE_NAME}(situacao)",
                f"CREATE INDEX idx_curriculo_turno ON {cls.TABLE_NAME}(turno)",
                f"CREATE INDEX idx_curriculo_ano_ini ON {cls.TABLE_NAME}(ano_ini)",
            ]
            
            for index_sql in indexes:
                try:
                    execute_query(index_sql, db_path=config.DB_LYCEUM_PATH)
                except Exception as e:
                    logger.warning(f"Erro ao criar índice: {e}")
            
            logger.info(f"Tabela {cls.TABLE_NAME} criada com sucesso (sem chave primária)")
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
        """Insere um novo currículo (não verifica duplicatas)"""
        try:
            # Verificar campos obrigatórios
            curriculo_id = cls._normalize_value(data.get('curriculo'))
            curso_id = cls._normalize_value(data.get('curso'))
            
            if not curriculo_id or not curso_id:
                logger.warning(f"Currículo sem código ou curso: {data}")
                return False
            
            # Preparar colunas e valores
            columns = ['curriculo', 'curso']
            values = [curriculo_id, curso_id]
            
            # Adicionar outros campos
            for field in cls.API_FIELDS:
                if field not in ['curriculo', 'curso']:
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
            logger.error(f"Erro ao inserir currículo {data.get('curriculo')}: {e}")
            return False
    
    @classmethod
    def batch_insert(cls, data_list: List[Dict]) -> int:
        """Insere múltiplos currículos em lote (permite duplicatas)"""
        if not data_list:
            return 0
        
        success_count = 0
        error_count = 0
        
        with get_db_connection(db_path=config.DB_LYCEUM_PATH) as conn:
            cursor = conn.cursor()
            
            for data in data_list:
                try:
                    # Verificar campos obrigatórios
                    curriculo_id = cls._normalize_value(data.get('curriculo'))
                    curso_id = cls._normalize_value(data.get('curso'))
                    
                    if not curriculo_id or not curso_id:
                        logger.warning(f"Currículo sem código ou curso: {data}")
                        error_count += 1
                        continue
                    
                    # Preparar colunas e valores
                    columns = ['curriculo', 'curso']
                    values = [curriculo_id, curso_id]
                    
                    # Adicionar outros campos
                    for field in cls.API_FIELDS:
                        if field not in ['curriculo', 'curso']:
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
                    logger.error(f"Erro ao inserir currículo {data.get('curriculo')}: {e}")
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
                'total_curriculos': f"SELECT COUNT(*) FROM {cls.TABLE_NAME}",
                'cursos_distintos': f"SELECT COUNT(DISTINCT curso) FROM {cls.TABLE_NAME}",
                'curriculos_distintos': f"SELECT COUNT(DISTINCT curriculo) FROM {cls.TABLE_NAME}",
                'situacoes_distintas': f"SELECT COUNT(DISTINCT situacao) FROM {cls.TABLE_NAME} WHERE situacao IS NOT NULL",
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