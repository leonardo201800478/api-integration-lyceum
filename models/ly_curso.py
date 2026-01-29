#!/usr/bin/env python3
"""
Modelo para tabela LY_CURSO usando o core.database existente
COM chave primária no campo 'curso' - único por curso
"""
import logging
from typing import List, Dict, Any, Optional
from core.database import get_db_connection, execute_query, fetch_all, fetch_one
from core.config import config

logger = logging.getLogger(__name__)


class LyCursoModel:
    """Modelo para tabela LY_CURSO com chave primária"""
    
    TABLE_NAME = "LY_CURSO"
    
    # Lista de campos da API para mapeamento
    API_FIELDS = [
        'curso', 'nome', 'ativo', 'modalidade', 'tipo', 'nivel',
        'depto', 'faculdade', 'grupo_curso', 'habilitacao',
        'titulo', 'mnemonico', 'evento', 'formatura', 'kit',
        'cobran_disc', 'valor_cred_assoc_disc', 'processo_doc_ingresso',
        'tem_reclassificacao', 'usa_serie_ideal', 'vagas',
        'duracao_aula', 'curso_associado', 'faculdade_associada',
        'decreto', 'dt_dou', 'nome_diretor', 'portaria_diretor',
        'rg_num_diretor', 'nome_secretaria', 'portaria_secretaria',
        'rg_num_secretaria', 'num_func', 'stamp_atualizacao',
        # Campos INEP
        'inep_curso', 'inep_nivel', 'inep_grau', 'inep_area_de_conhecimento',
        'inep_ocde', 'inep_regime', 'inep_turno', 'inep_turnooferta',
        'inep_presencial', 'inep_diplomas', 'inep_diploma_rec',
        'inep_tipocursoextensao', 'inep_tipocursopos',
        'inep_dtinicio', 'inep_dtdespacho_criacao', 'inep_numdespacho_criacao',
        'inep_tipodoc_criacao', 'inep_dtdespacho_rec', 'inep_numdespacho_rec',
        'inep_tipodoc_rec', 'inep_dtfinal_rec', 'inep_dtpubl_rec',
        'inep_numdoc_rec', 'inep_validade_rec', 'inep_dtdespacho_renov',
        'inep_numdespacho_renov', 'inep_tipodoc_renov', 'inep_dtpubl_renov',
        'inep_numdoc_renov', 'inep_validade_renov',
        # Campos INEP extensão
        'inep_ext_cargahoraria', 'inep_ext_alunosmatriculados',
        'inep_ext_alunosconcluintes', 'inep_ext_alunosgraduacao',
        'inep_ext_alunosposgraduacao', 'inep_ext_alunosprofedbasica',
        'inep_ext_alunosprofliberais', 'inep_ext_alunosexecutivos',
        'inep_ext_alunosoutrasies', 'inep_ext_docentessies',
        'inep_ext_docentesoutrasies', 'inep_extservidoresies',
        'inep_ext_pessoascomunidade', 'inep_ext_pessoasoutrasies',
        # Campos INEP questionário
        'inep_q01', 'inep_q02', 'inep_q03',
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
        """Cria a tabela LY_CURSO se não existir"""
        # Verificar se a tabela já existe
        table_exists_query = """
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name=?
        """
        
        result = fetch_one(table_exists_query, (cls.TABLE_NAME,), db_path=config.DB_LYCEUM_PATH)
        
        if result:
            logger.info(f"Tabela {cls.TABLE_NAME} já existe")
            return True
        
        # SQL para criar a tabela COM chave primária no campo 'curso'
        sql = f"""
        CREATE TABLE {cls.TABLE_NAME} (
            curso TEXT PRIMARY KEY,
            nome TEXT,
            ativo TEXT,
            modalidade TEXT,
            tipo TEXT,
            nivel TEXT,
            depto TEXT,
            faculdade TEXT,
            grupo_curso TEXT,
            habilitacao TEXT,
            titulo TEXT,
            mnemonico TEXT,
            evento TEXT,
            formatura TEXT,
            kit TEXT,
            cobran_disc TEXT,
            valor_cred_assoc_disc TEXT,
            processo_doc_ingresso TEXT,
            tem_reclassificacao TEXT,
            usa_serie_ideal TEXT,
            vagas INTEGER,
            duracao_aula INTEGER,
            curso_associado TEXT,
            faculdade_associada TEXT,
            decreto TEXT,
            dt_dou TEXT,
            nome_diretor TEXT,
            portaria_diretor TEXT,
            rg_num_diretor TEXT,
            nome_secretaria TEXT,
            portaria_secretaria TEXT,
            rg_num_secretaria TEXT,
            num_func INTEGER,
            stamp_atualizacao TEXT,
            -- Campos INEP
            inep_curso TEXT,
            inep_nivel TEXT,
            inep_grau TEXT,
            inep_area_de_conhecimento TEXT,
            inep_ocde TEXT,
            inep_regime TEXT,
            inep_turno TEXT,
            inep_turnooferta TEXT,
            inep_presencial TEXT,
            inep_diplomas TEXT,
            inep_diploma_rec TEXT,
            inep_tipocursoextensao TEXT,
            inep_tipocursopos TEXT,
            inep_dtinicio TEXT,
            inep_dtdespacho_criacao TEXT,
            inep_numdespacho_criacao TEXT,
            inep_tipodoc_criacao TEXT,
            inep_dtdespacho_rec TEXT,
            inep_numdespacho_rec TEXT,
            inep_tipodoc_rec TEXT,
            inep_dtfinal_rec TEXT,
            inep_dtpubl_rec TEXT,
            inep_numdoc_rec TEXT,
            inep_validade_rec TEXT,
            inep_dtdespacho_renov TEXT,
            inep_numdespacho_renov TEXT,
            inep_tipodoc_renov TEXT,
            inep_dtpubl_renov TEXT,
            inep_numdoc_renov TEXT,
            inep_validade_renov TEXT,
            -- Campos INEP extensão
            inep_ext_cargahoraria INTEGER,
            inep_ext_alunosmatriculados INTEGER,
            inep_ext_alunosconcluintes INTEGER,
            inep_ext_alunosgraduacao INTEGER,
            inep_ext_alunosposgraduacao INTEGER,
            inep_ext_alunosprofedbasica INTEGER,
            inep_ext_alunosprofliberais INTEGER,
            inep_ext_alunosexecutivos INTEGER,
            inep_ext_alunosoutrasies INTEGER,
            inep_ext_docentessies INTEGER,
            inep_ext_docentesoutrasies INTEGER,
            inep_extservidoresies INTEGER,
            inep_ext_pessoascomunidade INTEGER,
            inep_ext_pessoasoutrasies INTEGER,
            -- Campos INEP questionário
            inep_q01 TEXT,
            inep_q02 TEXT,
            inep_q03 TEXT,
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
                f"CREATE INDEX idx_curso_nome ON {cls.TABLE_NAME}(nome)",
                f"CREATE INDEX idx_curso_modalidade ON {cls.TABLE_NAME}(modalidade)",
                f"CREATE INDEX idx_curso_nivel ON {cls.TABLE_NAME}(nivel)",
                f"CREATE INDEX idx_curso_ativo ON {cls.TABLE_NAME}(ativo)",
            ]
            
            for index_sql in indexes:
                try:
                    execute_query(index_sql, db_path=config.DB_LYCEUM_PATH)
                except Exception as e:
                    logger.warning(f"Erro ao criar índice: {e}")
            
            logger.info(f"Tabela {cls.TABLE_NAME} criada com sucesso (chave primária: curso)")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao criar tabela {cls.TABLE_NAME}: {e}")
            return False
    
    @classmethod
    def upsert(cls, data: Dict) -> bool:
        """Insere ou atualiza um único curso (curso é chave primária)"""
        try:
            # Verificar campo obrigatório
            curso_id = cls._normalize_value(data.get('curso'))
            
            if not curso_id:
                logger.warning(f"Curso sem código: {data}")
                return False
            
            # Preparar colunas e valores
            columns = ['curso']
            values = [curso_id]
            placeholders = ['?']
            
            # Adicionar outros campos
            for field in cls.API_FIELDS:
                if field != 'curso':
                    value = cls._normalize_value(data.get(field))
                    if value is not None:
                        columns.append(field)
                        values.append(value)
                        placeholders.append('?')
            
            # Adicionar campos de metadados
            columns.append('data_atualizacao')
            values.append('CURRENT_TIMESTAMP')
            placeholders.append('CURRENT_TIMESTAMP')
            
            # Construir query de upsert com chave primária 'curso'
            columns_str = ', '.join(columns)
            placeholders_str = ', '.join(placeholders)
            
            # Para o UPDATE, precisamos de uma lista de assignments
            update_assignments = []
            for col in columns:
                if col not in ['curso', 'data_atualizacao']:
                    update_assignments.append(f"{col} = excluded.{col}")
            
            update_assignments.append("data_atualizacao = CURRENT_TIMESTAMP")
            update_str = ', '.join(update_assignments)
            
            sql = f"""
            INSERT INTO {cls.TABLE_NAME} ({columns_str})
            VALUES ({placeholders_str})
            ON CONFLICT(curso) DO UPDATE SET
                {update_str}
            """
            
            execute_query(sql, tuple(values[:len(values)-1]), db_path=config.DB_LYCEUM_PATH)
            logger.debug(f"Curso {curso_id} upsert realizado com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao upsert curso {data.get('curso')}: {e}")
            return False
    
    @classmethod
    def batch_upsert(cls, data_list: List[Dict]) -> int:
        """Insere ou atualiza múltiplos cursos em lote"""
        if not data_list:
            return 0
        
        success_count = 0
        error_count = 0
        
        with get_db_connection(db_path=config.DB_LYCEUM_PATH) as conn:
            cursor = conn.cursor()
            
            for data in data_list:
                try:
                    # Verificar campo obrigatório
                    curso_id = cls._normalize_value(data.get('curso'))
                    
                    if not curso_id:
                        logger.warning(f"Curso sem código: {data}")
                        error_count += 1
                        continue
                    
                    # Preparar colunas e valores
                    columns = ['curso']
                    values = [curso_id]
                    placeholders = ['?']
                    
                    # Adicionar outros campos
                    for field in cls.API_FIELDS:
                        if field != 'curso':
                            value = cls._normalize_value(data.get(field))
                            if value is not None:
                                columns.append(field)
                                values.append(value)
                                placeholders.append('?')
                    
                    # Adicionar campos de metadados
                    columns.append('data_atualizacao')
                    values.append('CURRENT_TIMESTAMP')
                    placeholders.append('CURRENT_TIMESTAMP')
                    
                    # Construir query de upsert
                    columns_str = ', '.join(columns)
                    placeholders_str = ', '.join(placeholders)
                    
                    # Para o UPDATE, precisamos de uma lista de assignments
                    update_assignments = []
                    for col in columns:
                        if col not in ['curso', 'data_atualizacao']:
                            update_assignments.append(f"{col} = excluded.{col}")
                    
                    update_assignments.append("data_atualizacao = CURRENT_TIMESTAMP")
                    update_str = ', '.join(update_assignments)
                    
                    sql = f"""
                    INSERT INTO {cls.TABLE_NAME} ({columns_str})
                    VALUES ({placeholders_str})
                    ON CONFLICT(curso) DO UPDATE SET
                        {update_str}
                    """
                    
                    cursor.execute(sql, tuple(values[:len(values)-1]))
                    success_count += 1
                    
                except Exception as e:
                    logger.error(f"Erro ao processar curso {data.get('curso')}: {e}")
                    error_count += 1
                    continue
            
            conn.commit()
        
        logger.info(f"Batch upsert: {success_count} sucessos, {error_count} erros, total {len(data_list)}")
        return success_count
    
    @classmethod
    def get_summary(cls) -> Dict:
        """Retorna estatísticas da tabela"""
        try:
            queries = {
                'total_cursos': f"SELECT COUNT(*) FROM {cls.TABLE_NAME}",
                'cursos_ativos': f"SELECT COUNT(*) FROM {cls.TABLE_NAME} WHERE ativo = 'S'",
                'modalidades_distintas': f"SELECT COUNT(DISTINCT modalidade) FROM {cls.TABLE_NAME}",
                'niveis_distintos': f"SELECT COUNT(DISTINCT nivel) FROM {cls.TABLE_NAME}",
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
    def get_all_cursos(cls) -> List[Dict]:
        """Retorna todos os cursos da tabela"""
        try:
            sql = f"SELECT * FROM {cls.TABLE_NAME} ORDER BY curso"
            results = fetch_all(sql, db_path=config.DB_LYCEUM_PATH)
            
            # Converter para lista de dicionários
            cursos = []
            for row in results:
                curso = {}
                # Obter nomes das colunas
                with get_db_connection(db_path=config.DB_LYCEUM_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute(f"PRAGMA table_info({cls.TABLE_NAME})")
                    columns = [col[1] for col in cursor.fetchall()]
                
                for i, col in enumerate(columns):
                    if i < len(row):
                        curso[col] = row[i]
                
                cursos.append(curso)
            
            return cursos
            
        except Exception as e:
            logger.error(f"Erro ao buscar cursos: {e}")
            return []
    
    @classmethod
    def get_by_curso(cls, curso_code: str) -> Optional[Dict]:
        """Retorna um curso específico pelo código"""
        try:
            sql = f"SELECT * FROM {cls.TABLE_NAME} WHERE curso = ?"
            result = fetch_one(sql, (curso_code,), db_path=config.DB_LYCEUM_PATH)
            
            if not result:
                return None
            
            curso = {}
            with get_db_connection(db_path=config.DB_LYCEUM_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute(f"PRAGMA table_info({cls.TABLE_NAME})")
                columns = [col[1] for col in cursor.fetchall()]
            
            for i, col in enumerate(columns):
                if i < len(result):
                    curso[col] = result[i]
            
            return curso
            
        except Exception as e:
            logger.error(f"Erro ao buscar curso {curso_code}: {e}")
            return None
    
    @classmethod
    def get_cursos_ativos(cls) -> List[Dict]:
        """Retorna todos os cursos ativos"""
        try:
            sql = f"SELECT * FROM {cls.TABLE_NAME} WHERE ativo = 'S' ORDER BY curso"
            results = fetch_all(sql, db_path=config.DB_LYCEUM_PATH)
            
            cursos = []
            for row in results:
                curso = {}
                with get_db_connection(db_path=config.DB_LYCEUM_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute(f"PRAGMA table_info({cls.TABLE_NAME})")
                    columns = [col[1] for col in cursor.fetchall()]
                
                for i, col in enumerate(columns):
                    if i < len(row):
                        curso[col] = row[i]
                
                cursos.append(curso)
            
            return cursos
            
        except Exception as e:
            logger.error(f"Erro ao buscar cursos ativos: {e}")
            return []