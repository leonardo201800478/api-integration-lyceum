from core.database import get_db_connection
import logging

logger = logging.getLogger(__name__)


class AlunoModel:
    TABLE = "LY_ALUNO"
    
    # Mapeamento de campos para conversão de tipos
    INTEGER_FIELDS = {
        'ano_ingresso', 'anoconcl2g', 'creditos', 'num_chamada',
        'pessoa', 'sem_ingresso', 'serie', 'dist_aluno_unidade'
    }
    
    BOOLEAN_FIELDS = {'representante_turma'}  # Campos que podem ser 'S'/'N'
    
    @staticmethod
    def create_table():
        """Cria a tabela se não existir, ou atualiza se necessário"""
        with get_db_connection() as conn:
            # Primeiro, verifica se a tabela existe
            cursor = conn.execute(f"""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='{AlunoModel.TABLE}'
            """)
            tabela_existe = cursor.fetchone() is not None
            
            if not tabela_existe:
                # Cria a tabela completa
                conn.execute(f"""
                    CREATE TABLE {AlunoModel.TABLE} (
                        aluno TEXT PRIMARY KEY,
                        ano_ingresso INTEGER,
                        anoconcl2g INTEGER,
                        areacnpq TEXT,
                        candidato TEXT,
                        cidade2g TEXT,
                        classif_aluno TEXT,
                        cod_cartao TEXT,
                        concurso TEXT,
                        cred_educativo TEXT,
                        creditos INTEGER,
                        curriculo TEXT,
                        curso TEXT,
                        curso_ant TEXT,
                        discipoutraserie TEXT,
                        dist_aluno_unidade INTEGER,
                        dt_ingresso TEXT,
                        e_mail_interno TEXT,
                        faculdade_conveniada TEXT,
                        grupo TEXT,
                        instituicao TEXT,
                        nome_abrev TEXT,
                        nome_compl TEXT,
                        nome_conjuge TEXT,
                        nome_social TEXT,
                        num_chamada INTEGER,
                        obs_aluno_finan TEXT,
                        obs_tel_com TEXT,
                        obs_tel_res TEXT,
                        outra_faculdade TEXT,
                        pais2g TEXT,
                        pessoa INTEGER,
                        ref_aluno_ant TEXT,
                        representante_turma TEXT,
                        sem_ingresso INTEGER,
                        serie INTEGER,
                        sit_aluno TEXT,
                        sit_aprov TEXT,
                        stamp_atualizacao TEXT,
                        tipo_aluno TEXT,
                        tipo_escola TEXT,
                        tipo_ingresso TEXT,
                        turma_pref TEXT,
                        turno TEXT,
                        unidade_ensino TEXT,
                        unidade_fisica TEXT,
                        data_sincronizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                logger.info(f"Tabela {AlunoModel.TABLE} criada com sucesso")
            else:
                # Verifica se a coluna data_sincronizacao existe
                cursor = conn.execute(f"""
                    PRAGMA table_info({AlunoModel.TABLE})
                """)
                colunas = [row[1] for row in cursor.fetchall()]
                
                if 'data_sincronizacao' not in colunas:
                    # Adiciona a coluna faltante
                    conn.execute(f"""
                        ALTER TABLE {AlunoModel.TABLE} 
                        ADD COLUMN data_sincronizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    """)
                    logger.info(f"Coluna data_sincronizacao adicionada à tabela {AlunoModel.TABLE}")
                
                logger.info(f"Tabela {AlunoModel.TABLE} verificada/atualizada")
    
    @staticmethod
    def _normalize_value(key: str, value):
        """Normaliza valores antes de inserir no banco"""
        if value is None:
            return None
        
        # Converte campos inteiros
        if key in AlunoModel.INTEGER_FIELDS:
            try:
                return int(value)
            except (ValueError, TypeError):
                return None
        
        # Converte booleanos 'S'/'N'
        if key in AlunoModel.BOOLEAN_FIELDS:
            if isinstance(value, str):
                return 'S' if value.upper() == 'S' else 'N'
        
        # Converte timestamps para string de data
        if key in ['dt_ingresso', 'stamp_atualizacao']:
            if isinstance(value, (int, float)):
                try:
                    from datetime import datetime
                    # Verifica se é timestamp em milissegundos
                    if value > 1000000000000:
                        timestamp = value / 1000
                    else:
                        timestamp = value
                    
                    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                except Exception:
                    return str(value)
        
        # Para strings, remove espaços extras
        if isinstance(value, str):
            return value.strip()
        
        return value
    
    @staticmethod
    def upsert(data: dict):
        """Insere ou atualiza um aluno"""
        if not data.get("aluno"):
            logger.warning(f"Tentativa de upsert sem matrícula: {data}")
            return
        
        aluno_matricula = data.get("aluno")
        
        # Prepara os parâmetros normalizados
        params = {}
        for key in [
            "aluno", "ano_ingresso", "anoconcl2g", "areacnpq", "candidato",
            "cidade2g", "classif_aluno", "cod_cartao", "concurso",
            "cred_educativo", "creditos", "curriculo", "curso", "curso_ant",
            "discipoutraserie", "dist_aluno_unidade", "dt_ingresso",
            "e_mail_interno", "faculdade_conveniada", "grupo", "instituicao",
            "nome_abrev", "nome_compl", "nome_conjuge", "nome_social",
            "num_chamada", "obs_aluno_finan", "obs_tel_com", "obs_tel_res",
            "outra_faculdade", "pais2g", "pessoa", "ref_aluno_ant",
            "representante_turma", "sem_ingresso", "serie", "sit_aluno",
            "sit_aprov", "stamp_atualizacao", "tipo_aluno", "tipo_escola",
            "tipo_ingresso", "turma_pref", "turno", "unidade_ensino",
            "unidade_fisica"
        ]:
            params[key] = AlunoModel._normalize_value(key, data.get(key))
        
        try:
            with get_db_connection() as conn:
                # Prepara a query de UPSERT
                columns = ", ".join(params.keys())
                placeholders = ", ".join([f":{key}" for key in params.keys()])
                update_clause = ", ".join([
                    f"{key}=excluded.{key}" 
                    for key in params.keys() 
                    if key != "aluno"
                ])
                
                # Adiciona data_sincronizacao separadamente
                query = f"""
                    INSERT INTO {AlunoModel.TABLE} ({columns}, data_sincronizacao)
                    VALUES ({placeholders}, CURRENT_TIMESTAMP)
                    ON CONFLICT(aluno) DO UPDATE SET
                        {update_clause},
                        data_sincronizacao = CURRENT_TIMESTAMP
                """
                
                conn.execute(query, params)
                logger.info(f"Aluno {aluno_matricula} upsert realizado com sucesso")
                    
        except Exception as e:
            logger.error(f"Erro no upsert do aluno {aluno_matricula}: {str(e)}")
            # Para debug, mostra a query e parâmetros
            logger.debug(f"Query: {query if 'query' in locals() else 'N/A'}")
            logger.debug(f"Params: {params}")
            raise
    
    @staticmethod
    def get_all_matriculas():
        """Retorna todas as matrículas existentes no banco"""
        with get_db_connection() as conn:
            cursor = conn.execute(f"SELECT aluno FROM {AlunoModel.TABLE}")
            return {row[0] for row in cursor.fetchall()}
    
    @staticmethod
    def delete_obsoletos(matriculas_atualizadas: set):
        """Remove alunos que não estão mais na API"""
        if not matriculas_atualizadas:
            return
        
        with get_db_connection() as conn:
            # Converte o set para lista
            matriculas_lista = list(matriculas_atualizadas)
            placeholders = ','.join(['?'] * len(matriculas_lista))
            
            # Busca os alunos que serão removidos
            cursor = conn.execute(
                f"SELECT aluno FROM {AlunoModel.TABLE} WHERE aluno NOT IN ({placeholders})",
                matriculas_lista
            )
            obsoletos = cursor.fetchall()
            
            if obsoletos:
                conn.execute(
                    f"DELETE FROM {AlunoModel.TABLE} WHERE aluno NOT IN ({placeholders})",
                    matriculas_lista
                )
                logger.info(f"Removidos {len(obsoletos)} alunos obsoletos")
                for aluno in obsoletos[:10]:  # Mostra apenas os primeiros 10
                    logger.info(f"  - Removido: {aluno[0]}")
                if len(obsoletos) > 10:
                    logger.info(f"  ... e mais {len(obsoletos) - 10} alunos")