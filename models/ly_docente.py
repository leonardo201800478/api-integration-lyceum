#!/usr/bin/env python3
"""
Modelo para tabela LY_DOCENTE usando o core.database existente
SEM chave primária fixa - seguindo o padrão LY_TURMA
"""
import logging
from typing import List, Dict, Any, Optional
from core.database import get_db_connection, execute_query, fetch_all, fetch_one
from core.config import config

logger = logging.getLogger(__name__)


class LyDocenteModel:
    """Modelo para tabela LY_DOCENTE - SEM chave primária fixa"""
    
    TABLE_NAME = "LY_DOCENTE"
    
    # Lista de campos da API para mapeamento
    API_FIELDS = [
        'cpf', 'num_func', 'agencia', 'ano_ingresso', 'ativo', 'atuacao_profis',
        'bairro', 'banco', 'candidato', 'categoria', 'celular', 'cep', 'cgc_emp',
        'cod_lattes', 'concurso', 'conta_banco', 'contrato_trabalho',
        'cprof_dataexp', 'cprof_num', 'cprof_serie', 'cprof_uf', 'curso_contrato',
        'depto', 'dt_admissao', 'dt_demissao', 'dt_habilit_dol', 'dt_nasc',
        'dt_ult_titulo', 'e_mail_com', 'e_mail_emp', 'email', 'end_com_bairro',
        'end_com_cep', 'end_com_compl', 'end_com_municipio', 'end_com_num',
        'end_com_pais', 'end_compl', 'end_num', 'endcom', 'endemp', 'endemp_bairro',
        'endemp_cep', 'endemp_compl', 'endemp_municipio', 'endemp_num', 'endereco',
        'est_civil', 'faculdade', 'fax_com', 'fax_emp', 'fax_res', 'fechar_turma_internet',
        'fl_field01', 'fl_field02', 'fl_field03', 'fl_field04', 'fl_field05',
        'fl_field06', 'fl_field07', 'fl_field08', 'fl_field09', 'fl_field10',
        'fone', 'fone_com', 'fone_emp', 'hab_tac', 'mailbox', 'matricula',
        'municipio', 'nome_abrev', 'nome_compl', 'nome_empresa', 'nome_meio',
        'nome_social', 'obs', 'obs_tel_com', 'obs_tel_res', 'outra_faculdade',
        'pais_res', 'perc_dedic_mens', 'pessoa', 'pispasep', 'primeiro_nome',
        'razao_social', 're', 'regime_trabalho', 'rg_dtexp', 'rg_emissor',
        'rg_num', 'rg_tipo', 'rg_uf', 'senha_alterada', 'senha_dol', 'sexo',
        'sobrenome', 'stamp_atualizacao', 'tempo_exp_ead', 'tempo_exp_edu_basica',
        'tempo_exp_gestao', 'tempo_exp_magisterio', 'tempo_exp_profissional',
        'tipo_ingresso', 'tipo_pessoa', 'titulacao', 'url_particular',
        'url_professional', 'winusuario'
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
        """Cria a tabela LY_DOCENTE se não existir"""
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
            cpf TEXT,
            num_func INTEGER,
            agencia TEXT,
            ano_ingresso INTEGER,
            ativo TEXT,
            atuacao_profis TEXT,
            bairro TEXT,
            banco INTEGER,
            candidato TEXT,
            categoria TEXT,
            celular TEXT,
            cep TEXT,
            cgc_emp TEXT,
            cod_lattes TEXT,
            concurso TEXT,
            conta_banco TEXT,
            contrato_trabalho TEXT,
            cprof_dataexp TEXT,
            cprof_num TEXT,
            cprof_serie TEXT,
            cprof_uf TEXT,
            curso_contrato TEXT,
            depto TEXT,
            dt_admissao TEXT,
            dt_demissao TEXT,
            dt_habilit_dol TEXT,
            dt_nasc TEXT,
            dt_ult_titulo TEXT,
            e_mail_com TEXT,
            e_mail_emp TEXT,
            email TEXT,
            end_com_bairro TEXT,
            end_com_cep TEXT,
            end_com_compl TEXT,
            end_com_municipio TEXT,
            end_com_num TEXT,
            end_com_pais TEXT,
            end_compl TEXT,
            end_num TEXT,
            endcom TEXT,
            endemp TEXT,
            endemp_bairro TEXT,
            endemp_cep TEXT,
            endemp_compl TEXT,
            endemp_municipio TEXT,
            endemp_num TEXT,
            endereco TEXT,
            est_civil TEXT,
            faculdade TEXT,
            fax_com TEXT,
            fax_emp TEXT,
            fax_res TEXT,
            fechar_turma_internet TEXT,
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
            fone TEXT,
            fone_com TEXT,
            fone_emp TEXT,
            hab_tac TEXT,
            mailbox TEXT,
            matricula TEXT,
            municipio TEXT,
            nome_abrev TEXT,
            nome_compl TEXT,
            nome_empresa TEXT,
            nome_meio TEXT,
            nome_social TEXT,
            obs TEXT,
            obs_tel_com TEXT,
            obs_tel_res TEXT,
            outra_faculdade TEXT,
            pais_res TEXT,
            perc_dedic_mens REAL,
            pessoa INTEGER,
            pispasep TEXT,
            primeiro_nome TEXT,
            razao_social TEXT,
            re TEXT,
            regime_trabalho TEXT,
            rg_dtexp TEXT,
            rg_emissor TEXT,
            rg_num TEXT,
            rg_tipo TEXT,
            rg_uf TEXT,
            senha_alterada TEXT,
            senha_dol TEXT,
            sexo TEXT,
            sobrenome TEXT,
            stamp_atualizacao TEXT,
            tempo_exp_ead INTEGER,
            tempo_exp_edu_basica INTEGER,
            tempo_exp_gestao INTEGER,
            tempo_exp_magisterio INTEGER,
            tempo_exp_profissional INTEGER,
            tipo_ingresso TEXT,
            tipo_pessoa TEXT,
            titulacao TEXT,
            url_particular TEXT,
            url_professional TEXT,
            winusuario TEXT,
            -- Metadados
            data_importacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        try:
            execute_query(sql, db_path=config.DB_LYCEUM_PATH)
            
            # Criar índices para melhor performance
            indexes = [
                f"CREATE INDEX idx_docente_cpf ON {cls.TABLE_NAME}(cpf)",
                f"CREATE INDEX idx_docente_num_func ON {cls.TABLE_NAME}(num_func)",
                f"CREATE INDEX idx_docente_nome ON {cls.TABLE_NAME}(nome_compl)",
                f"CREATE INDEX idx_docente_email ON {cls.TABLE_NAME}(email)",
                f"CREATE INDEX idx_docente_depto ON {cls.TABLE_NAME}(depto)",
                f"CREATE INDEX idx_docente_ativo ON {cls.TABLE_NAME}(ativo)",
                f"CREATE INDEX idx_docente_cpf_num_func ON {cls.TABLE_NAME}(cpf, num_func)",
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
        """Insere um novo docente (não verifica duplicatas)"""
        try:
            # Verificar campos que formam a identidade básica
            cpf = cls._normalize_value(data.get('cpf'))
            num_func = cls._normalize_value(data.get('num_func'))
            
            if not all([cpf, num_func]):
                logger.warning(f"Docente sem campos obrigatórios (cpf, num_func): {data}")
                return False
            
            # Preparar colunas e valores
            columns = ['cpf', 'num_func']
            values = [cpf, num_func]
            
            # Adicionar outros campos
            for field in cls.API_FIELDS:
                if field not in ['cpf', 'num_func']:
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
            logger.error(f"Erro ao inserir docente {data.get('cpf')}/{data.get('num_func')}: {e}")
            return False
    
    @classmethod
    def batch_insert(cls, data_list: List[Dict]) -> int:
        """Insere múltiplos docentes em lote (permite duplicatas)"""
        if not data_list:
            return 0
        
        success_count = 0
        error_count = 0
        
        with get_db_connection(db_path=config.DB_LYCEUM_PATH) as conn:
            cursor = conn.cursor()
            
            for data in data_list:
                try:
                    # Verificar campos que formam a identidade básica
                    cpf = cls._normalize_value(data.get('cpf'))
                    num_func = cls._normalize_value(data.get('num_func'))
                    
                    if not all([cpf, num_func]):
                        logger.warning(f"Docente sem campos obrigatórios: {data}")
                        error_count += 1
                        continue
                    
                    # Preparar colunas e valores
                    columns = ['cpf', 'num_func']
                    values = [cpf, num_func]
                    
                    # Adicionar outros campos
                    for field in cls.API_FIELDS:
                        if field not in ['cpf', 'num_func']:
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
                    logger.error(f"Erro ao inserir docente {data.get('cpf')}/{data.get('num_func')}: {e}")
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
                'total_docentes': f"SELECT COUNT(*) FROM {cls.TABLE_NAME}",
                'ativos': f"SELECT COUNT(*) FROM {cls.TABLE_NAME} WHERE ativo = 'S'",
                'inativos': f"SELECT COUNT(*) FROM {cls.TABLE_NAME} WHERE ativo = 'N'",
                'deptos_distintos': f"SELECT COUNT(DISTINCT depto) FROM {cls.TABLE_NAME}",
                'cpfs_distintos': f"SELECT COUNT(DISTINCT cpf) FROM {cls.TABLE_NAME}",
                'num_func_distintos': f"SELECT COUNT(DISTINCT num_func) FROM {cls.TABLE_NAME}",
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
    def get_all_docentes(cls) -> List[Dict]:
        """Retorna todos os docentes da tabela"""
        try:
            sql = f"SELECT * FROM {cls.TABLE_NAME} ORDER BY nome_compl"
            results = fetch_all(sql, db_path=config.DB_LYCEUM_PATH)
            
            # Converter para lista de dicionários
            docentes = []
            for row in results:
                docente = {}
                # Obter nomes das colunas
                with get_db_connection(db_path=config.DB_LYCEUM_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute(f"PRAGMA table_info({cls.TABLE_NAME})")
                    columns = [col[1] for col in cursor.fetchall()]
                
                for i, col in enumerate(columns):
                    if i < len(row):
                        docente[col] = row[i]
                
                docentes.append(docente)
            
            return docentes
            
        except Exception as e:
            logger.error(f"Erro ao buscar docentes: {e}")
            return []
    
    @classmethod
    def get_by_cpf(cls, cpf: str) -> List[Dict]:
        """Retorna docentes por CPF"""
        try:
            sql = f"SELECT * FROM {cls.TABLE_NAME} WHERE cpf = ? ORDER BY num_func"
            results = fetch_all(sql, (cpf,), db_path=config.DB_LYCEUM_PATH)
            
            docentes = []
            for row in results:
                docente = {}
                with get_db_connection(db_path=config.DB_LYCEUM_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute(f"PRAGMA table_info({cls.TABLE_NAME})")
                    columns = [col[1] for col in cursor.fetchall()]
                
                for i, col in enumerate(columns):
                    if i < len(row):
                        docente[col] = row[i]
                
                docentes.append(docente)
            
            return docentes
            
        except Exception as e:
            logger.error(f"Erro ao buscar docente por CPF {cpf}: {e}")
            return []
    
    @classmethod
    def get_by_depto(cls, depto: str) -> List[Dict]:
        """Retorna docentes por departamento"""
        try:
            sql = f"SELECT * FROM {cls.TABLE_NAME} WHERE depto = ? ORDER BY nome_compl"
            results = fetch_all(sql, (depto,), db_path=config.DB_LYCEUM_PATH)
            
            docentes = []
            for row in results:
                docente = {}
                with get_db_connection(db_path=config.DB_LYCEUM_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute(f"PRAGMA table_info({cls.TABLE_NAME})")
                    columns = [col[1] for col in cursor.fetchall()]
                
                for i, col in enumerate(columns):
                    if i < len(row):
                        docente[col] = row[i]
                
                docentes.append(docente)
            
            return docentes
            
        except Exception as e:
            logger.error(f"Erro ao buscar docentes do departamento {depto}: {e}")
            return []