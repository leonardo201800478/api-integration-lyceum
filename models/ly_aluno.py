# models/ly_aluno.py

from core.database import execute_query, fetch_all, fetch_one
import logging

logger = logging.getLogger(__name__)

class AlunoModel:
    TABLE = "LY_ALUNO"  # Nome da tabela no SQL Server

    # Mapeamento de campos para conversão de tipos (mesmo)
    INTEGER_FIELDS = {
        'ano_ingresso', 'anoconcl2g', 'creditos', 'num_chamada',
        'pessoa', 'sem_ingresso', 'serie', 'dist_aluno_unidade'
    }
    BOOLEAN_FIELDS = {'representante_turma'}  # Campos que podem ser 'S'/'N'

    @staticmethod
    def _normalize_value(key: str, value):
        """Normaliza valores antes de inserir no banco (igual ao original)"""
        if value is None:
            return None

        if key in AlunoModel.INTEGER_FIELDS:
            try:
                # Converte para int (Python int é ilimitado, será enviado como BIGINT)
                return int(value)
            except (ValueError, TypeError):
                return None

        if key in AlunoModel.BOOLEAN_FIELDS:
            if isinstance(value, str):
                return 'S' if value.upper() == 'S' else 'N'

        if key in ['dt_ingresso', 'stamp_atualizacao']:
            if isinstance(value, (int, float)):
                try:
                    from datetime import datetime
                    # Converte timestamp (segundos ou milissegundos) para string ISO
                    if value > 1000000000000:
                        timestamp = value / 1000
                    else:
                        timestamp = value
                    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                except Exception:
                    return str(value)

        if isinstance(value, str):
            return value.strip()

        return value

    @staticmethod
    def create_table():
        """
        Verifica se a tabela existe no SQL Server e a cria se necessário.
        Usa tipos BIGINT para campos numéricos grandes e NVARCHAR com tamanhos adequados.
        """
        # Verifica se a tabela existe usando INFORMATION_SCHEMA
        query = """
            SELECT 1 FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = ? AND TABLE_TYPE = 'BASE TABLE'
        """
        exists = fetch_one(query, (AlunoModel.TABLE,))

        if not exists:
            # Cria a tabela completa com tipos ajustados
            create_sql = f"""
                CREATE TABLE [{AlunoModel.TABLE}] (
                    [aluno] NVARCHAR(100) PRIMARY KEY,
                    [ano_ingresso] BIGINT,
                    [anoconcl2g] BIGINT,
                    [areacnpq] NVARCHAR(255),
                    [candidato] NVARCHAR(100),
                    [cidade2g] NVARCHAR(255),
                    [classif_aluno] NVARCHAR(100),
                    [cod_cartao] NVARCHAR(100),
                    [concurso] NVARCHAR(100),
                    [cred_educativo] NVARCHAR(50),
                    [creditos] BIGINT,
                    [curriculo] NVARCHAR(50),
                    [curso] NVARCHAR(100),
                    [curso_ant] NVARCHAR(255),      -- Aumentado para evitar truncamento
                    [discipoutraserie] NVARCHAR(20),
                    [dist_aluno_unidade] BIGINT,
                    [dt_ingresso] NVARCHAR(30),     -- Armazenar como string no formato YYYY-MM-DD HH:MM:SS
                    [e_mail_interno] NVARCHAR(255),
                    [faculdade_conveniada] NVARCHAR(50),
                    [grupo] NVARCHAR(50),
                    [instituicao] NVARCHAR(200),
                    [nome_abrev] NVARCHAR(200),
                    [nome_compl] NVARCHAR(500),
                    [nome_conjuge] NVARCHAR(500),
                    [nome_social] NVARCHAR(500),
                    [num_chamada] BIGINT,
                    [obs_aluno_finan] NVARCHAR(MAX),
                    [obs_tel_com] NVARCHAR(MAX),
                    [obs_tel_res] NVARCHAR(MAX),
                    [outra_faculdade] NVARCHAR(100),
                    [pais2g] NVARCHAR(255),
                    [pessoa] BIGINT,
                    [ref_aluno_ant] NVARCHAR(100),
                    [representante_turma] CHAR(1),
                    [sem_ingresso] BIGINT,
                    [serie] BIGINT,
                    [sit_aluno] NVARCHAR(50),
                    [sit_aprov] NVARCHAR(50),
                    [stamp_atualizacao] NVARCHAR(30),  -- String no mesmo formato
                    [tipo_aluno] NVARCHAR(50),
                    [tipo_escola] NVARCHAR(50),
                    [tipo_ingresso] NVARCHAR(50),
                    [turma_pref] NVARCHAR(50),
                    [turno] NVARCHAR(20),
                    [unidade_ensino] NVARCHAR(100),
                    [unidade_fisica] NVARCHAR(100),
                    [data_sincronizacao] DATETIME2 DEFAULT GETDATE()
                )
            """
            execute_query(create_sql)
            logger.info(f"Tabela {AlunoModel.TABLE} criada com sucesso (tipos ajustados)")
        else:
            # Verifica se a coluna data_sincronizacao existe
            col_query = """
                SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = ? AND COLUMN_NAME = 'data_sincronizacao'
            """
            col_exists = fetch_one(col_query, (AlunoModel.TABLE,))
            if not col_exists:
                alter_sql = f"""
                    ALTER TABLE [{AlunoModel.TABLE}] 
                    ADD [data_sincronizacao] DATETIME2 DEFAULT GETDATE()
                """
                execute_query(alter_sql)
                logger.info(f"Coluna data_sincronizacao adicionada à tabela {AlunoModel.TABLE}")
            logger.info(f"Tabela {AlunoModel.TABLE} verificada/atualizada")

    @staticmethod
    def upsert(data: dict):
        """Insere ou atualiza um aluno usando MERGE (SQL Server)"""
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

        # Colunas na ordem (exceto data_sincronizacao, que será tratada separadamente)
        columns = list(params.keys())
        update_columns = [c for c in columns if c != "aluno"]

        # Constrói o UPDATE SET
        update_set = ", ".join([f"target.[{col}] = source.[{col}]" for col in update_columns])

        # Colunas para INSERT (incluindo data_sincronizacao)
        insert_cols = [f"[{col}]" for col in columns] + ["[data_sincronizacao]"]
        insert_vals = ", ".join([f"source.[{col}]" for col in columns]) + ", GETDATE()"

        # Monta o MERGE
        merge_sql = f"""
            MERGE INTO [{AlunoModel.TABLE}] AS target
            USING (VALUES ({','.join(['?' for _ in columns])})) AS source ({','.join([f"[{col}]" for col in columns])})
            ON target.[aluno] = source.[aluno]
            WHEN MATCHED THEN
                UPDATE SET
                    {update_set},
                    target.[data_sincronizacao] = GETDATE()
            WHEN NOT MATCHED THEN
                INSERT ({', '.join(insert_cols)})
                VALUES ({insert_vals});
        """

        param_values = [params[col] for col in columns]

        try:
            execute_query(merge_sql, param_values)
            logger.info(f"Aluno {aluno_matricula} upsert realizado com sucesso")
        except Exception as e:
            logger.error(f"Erro no upsert do aluno {aluno_matricula}: {str(e)}")
            logger.debug(f"Params: {params}")
            raise

    @staticmethod
    def get_all_matriculas():
        """Retorna todas as matrículas existentes no banco"""
        rows = fetch_all(f"SELECT [aluno] FROM [{AlunoModel.TABLE}]")
        return {row[0] for row in rows} if rows else set()

    @staticmethod
    def delete_obsoletos(matriculas_atualizadas: set):
        """Remove alunos que não estão mais na API"""
        if not matriculas_atualizadas:
            return

        matriculas_lista = list(matriculas_atualizadas)
        placeholders = ','.join(['?' for _ in matriculas_lista])

        # Opcional: log dos obsoletos
        select_obs_sql = f"""
            SELECT [aluno] FROM [{AlunoModel.TABLE}] 
            WHERE [aluno] NOT IN ({placeholders})
        """
        obsoletos = fetch_all(select_obs_sql, matriculas_lista)

        if obsoletos:
            delete_sql = f"""
                DELETE FROM [{AlunoModel.TABLE}] 
                WHERE [aluno] NOT IN ({placeholders})
            """
            execute_query(delete_sql, matriculas_lista)
            logger.info(f"Removidos {len(obsoletos)} alunos obsoletos")
            for aluno in obsoletos[:10]:
                logger.info(f"  - Removido: {aluno[0]}")
            if len(obsoletos) > 10:
                logger.info(f"  ... e mais {len(obsoletos) - 10} alunos")