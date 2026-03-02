#!/usr/bin/env python3
"""
models/ly_curso.py
Modelo para tabela LY_CURSO usando core.database (SQL Server)
COM chave primária no campo 'curso' - único por curso
"""

import logging
from typing import List, Dict, Any, Optional
from core.database import get_db_connection, execute_query, fetch_all, fetch_one

logger = logging.getLogger(__name__)


class LyCursoModel:
    """Modelo para tabela LY_CURSO com chave primária (SQL Server)."""

    TABLE_NAME = "LY_CURSO"
    DB_NAME = "lyceum.db"  # nome do banco no SQL Server

    # Lista de campos da API para mapeamento (exclui metadados)
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

    # Colunas de metadados (não inclusas no MERGE como fonte)
    META_FIELDS = ['data_importacao', 'data_atualizacao']

    @classmethod
    def _normalize_value(cls, value: Any) -> Any:
        """Normaliza valores para inserção no banco."""
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
    def _table_exists(cls) -> bool:
        """Verifica se a tabela já existe no banco."""
        query = """
            SELECT 1 FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_NAME = ? AND TABLE_TYPE = 'BASE TABLE'
        """
        result = fetch_one(query, (cls.TABLE_NAME,), db_path=cls.DB_NAME)
        return result is not None

    @classmethod
    def _get_existing_columns(cls) -> List[str]:
        """Retorna lista de colunas existentes na tabela."""
        query = """
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = ?
        """
        rows = fetch_all(query, (cls.TABLE_NAME,), db_path=cls.DB_NAME)
        return [row[0] for row in rows] if rows else []

    @classmethod
    def create_table(cls):
        """Cria a tabela LY_CURSO se não existir (SQL Server)."""
        if cls._table_exists():
            logger.info(f"Tabela {cls.TABLE_NAME} já existe.")
            return True

        # SQL para criar a tabela com chave primária 'curso'
        sql = f"""
        CREATE TABLE [{cls.TABLE_NAME}] (
            [curso] NVARCHAR(100) PRIMARY KEY,
            [nome] NVARCHAR(255),
            [ativo] CHAR(1),
            [modalidade] NVARCHAR(50),
            [tipo] NVARCHAR(50),
            [nivel] NVARCHAR(50),
            [depto] NVARCHAR(50),
            [faculdade] NVARCHAR(50),
            [grupo_curso] NVARCHAR(50),
            [habilitacao] NVARCHAR(500),
            [titulo] NVARCHAR(50),
            [mnemonico] NVARCHAR(20),
            [evento] NVARCHAR(50),
            [formatura] NVARCHAR(50),
            [kit] NVARCHAR(50),
            [cobran_disc] NVARCHAR(10),
            [valor_cred_assoc_disc] NVARCHAR(50),
            [processo_doc_ingresso] NVARCHAR(50),
            [tem_reclassificacao] CHAR(1),
            [usa_serie_ideal] CHAR(1),
            [vagas] INT,
            [duracao_aula] INT,
            [curso_associado] NVARCHAR(100),
            [faculdade_associada] NVARCHAR(50),
            [decreto] NVARCHAR(1000),
            [dt_dou] NVARCHAR(20),
            [nome_diretor] NVARCHAR(255),
            [portaria_diretor] NVARCHAR(100),
            [rg_num_diretor] NVARCHAR(50),
            [nome_secretaria] NVARCHAR(255),
            [portaria_secretaria] NVARCHAR(100),
            [rg_num_secretaria] NVARCHAR(50),
            [num_func] INT,
            [stamp_atualizacao] NVARCHAR(50),
            -- Campos INEP
            [inep_curso] NVARCHAR(100),
            [inep_nivel] NVARCHAR(50),
            [inep_grau] NVARCHAR(50),
            [inep_area_de_conhecimento] NVARCHAR(100),
            [inep_ocde] NVARCHAR(50),
            [inep_regime] NVARCHAR(50),
            [inep_turno] NVARCHAR(50),
            [inep_turnooferta] NVARCHAR(50),
            [inep_presencial] CHAR(1),
            [inep_diplomas] NVARCHAR(50),
            [inep_diploma_rec] NVARCHAR(50),
            [inep_tipocursoextensao] NVARCHAR(50),
            [inep_tipocursopos] NVARCHAR(50),
            [inep_dtinicio] NVARCHAR(20),
            [inep_dtdespacho_criacao] NVARCHAR(20),
            [inep_numdespacho_criacao] NVARCHAR(50),
            [inep_tipodoc_criacao] NVARCHAR(50),
            [inep_dtdespacho_rec] NVARCHAR(20),
            [inep_numdespacho_rec] NVARCHAR(50),
            [inep_tipodoc_rec] NVARCHAR(50),
            [inep_dtfinal_rec] NVARCHAR(20),
            [inep_dtpubl_rec] NVARCHAR(20),
            [inep_numdoc_rec] NVARCHAR(50),
            [inep_validade_rec] NVARCHAR(20),
            [inep_dtdespacho_renov] NVARCHAR(20),
            [inep_numdespacho_renov] NVARCHAR(50),
            [inep_tipodoc_renov] NVARCHAR(50),
            [inep_dtpubl_renov] NVARCHAR(20),
            [inep_numdoc_renov] NVARCHAR(50),
            [inep_validade_renov] NVARCHAR(20),
            -- Campos INEP extensão
            [inep_ext_cargahoraria] INT,
            [inep_ext_alunosmatriculados] INT,
            [inep_ext_alunosconcluintes] INT,
            [inep_ext_alunosgraduacao] INT,
            [inep_ext_alunosposgraduacao] INT,
            [inep_ext_alunosprofedbasica] INT,
            [inep_ext_alunosprofliberais] INT,
            [inep_ext_alunosexecutivos] INT,
            [inep_ext_alunosoutrasies] INT,
            [inep_ext_docentessies] INT,
            [inep_ext_docentesoutrasies] INT,
            [inep_extservidoresies] INT,
            [inep_ext_pessoascomunidade] INT,
            [inep_ext_pessoasoutrasies] INT,
            -- Campos INEP questionário
            [inep_q01] NVARCHAR(255),
            [inep_q02] NVARCHAR(255),
            [inep_q03] NVARCHAR(255),
            -- Campos flag
            [fl_field01] NVARCHAR(255),
            [fl_field02] NVARCHAR(255),
            [fl_field03] NVARCHAR(255),
            [fl_field04] NVARCHAR(255),
            [fl_field05] NVARCHAR(255),
            [fl_field06] NVARCHAR(255),
            [fl_field07] NVARCHAR(255),
            [fl_field08] NVARCHAR(255),
            [fl_field09] NVARCHAR(255),
            [fl_field10] NVARCHAR(255),
            -- Metadados
            [data_importacao] DATETIME2 DEFAULT GETDATE(),
            [data_atualizacao] DATETIME2 DEFAULT GETDATE()
        )
        """

        try:
            execute_query(sql, db_path=cls.DB_NAME)

            # Criar índices
            indexes = [
                f"CREATE INDEX idx_curso_nome ON [{cls.TABLE_NAME}]([nome])",
                f"CREATE INDEX idx_curso_modalidade ON [{cls.TABLE_NAME}]([modalidade])",
                f"CREATE INDEX idx_curso_nivel ON [{cls.TABLE_NAME}]([nivel])",
                f"CREATE INDEX idx_curso_ativo ON [{cls.TABLE_NAME}]([ativo])",
            ]
            for idx_sql in indexes:
                try:
                    execute_query(idx_sql, db_path=cls.DB_NAME)
                except Exception as e:
                    logger.warning(f"Erro ao criar índice: {e}")

            logger.info(f"Tabela {cls.TABLE_NAME} criada com sucesso (chave primária: curso).")
            return True

        except Exception as e:
            logger.error(f"Erro ao criar tabela {cls.TABLE_NAME}: {e}")
            return False

    @classmethod
    def upsert(cls, data: Dict) -> bool:
        """Insere ou atualiza um único curso usando MERGE."""
        try:
            curso_id = cls._normalize_value(data.get('curso'))
            if not curso_id:
                logger.warning(f"Curso sem código: {data}")
                return False

            # Lista de colunas (todas as API_FIELDS, na ordem)
            columns = cls.API_FIELDS
            # Valores na mesma ordem
            values = [cls._normalize_value(data.get(col)) for col in columns]

            # Geração dinâmica do MERGE
            col_list = ', '.join([f"[{col}]" for col in columns])
            param_placeholders = ', '.join(['?' for _ in columns])
            source_cols = ', '.join([f"source.[{col}]" for col in columns])

            # UPDATE SET: todas exceto a chave 'curso'
            update_set = ', '.join([
                f"target.[{col}] = source.[{col}]"
                for col in columns if col != 'curso'
            ])
            # Adiciona atualização da data
            if update_set:
                update_set += ', '
            update_set += "target.[data_atualizacao] = GETDATE()"

            # INSERT: colunas da fonte + metadados
            insert_cols = f"{col_list}, [data_importacao], [data_atualizacao]"
            insert_vals = f"{source_cols}, GETDATE(), GETDATE()"

            merge_sql = f"""
                MERGE INTO [{cls.TABLE_NAME}] AS target
                USING (VALUES ({param_placeholders})) AS source ({col_list})
                ON target.[curso] = source.[curso]
                WHEN MATCHED THEN
                    UPDATE SET {update_set}
                WHEN NOT MATCHED THEN
                    INSERT ({insert_cols})
                    VALUES ({insert_vals});
            """

            execute_query(merge_sql, tuple(values), db_path=cls.DB_NAME)
            logger.debug(f"Curso {curso_id} upsert realizado com sucesso")
            return True

        except Exception as e:
            logger.error(f"Erro ao upsert curso {data.get('curso')}: {e}")
            return False

    @classmethod
    def batch_upsert(cls, data_list: List[Dict]) -> int:
        """Insere ou atualiza múltiplos cursos em lote."""
        if not data_list:
            return 0

        success_count = 0
        error_count = 0

        with get_db_connection(db_path=cls.DB_NAME) as conn:
            cursor = conn.cursor()
            columns = cls.API_FIELDS
            col_list = ', '.join([f"[{col}]" for col in columns])
            param_placeholders = ', '.join(['?' for _ in columns])
            source_cols = ', '.join([f"source.[{col}]" for col in columns])
            update_set = ', '.join([
                f"target.[{col}] = source.[{col}]"
                for col in columns if col != 'curso'
            ])
            if update_set:
                update_set += ', '
            update_set += "target.[data_atualizacao] = GETDATE()"
            insert_cols = f"{col_list}, [data_importacao], [data_atualizacao]"
            insert_vals = f"{source_cols}, GETDATE(), GETDATE()"

            merge_sql = f"""
                MERGE INTO [{cls.TABLE_NAME}] AS target
                USING (VALUES ({param_placeholders})) AS source ({col_list})
                ON target.[curso] = source.[curso]
                WHEN MATCHED THEN
                    UPDATE SET {update_set}
                WHEN NOT MATCHED THEN
                    INSERT ({insert_cols})
                    VALUES ({insert_vals});
            """

            for data in data_list:
                try:
                    curso_id = cls._normalize_value(data.get('curso'))
                    if not curso_id:
                        logger.warning(f"Curso sem código: {data}")
                        error_count += 1
                        continue

                    values = [cls._normalize_value(data.get(col)) for col in columns]
                    cursor.execute(merge_sql, tuple(values))
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
        """Retorna estatísticas da tabela."""
        try:
            queries = {
                'total_cursos': f"SELECT COUNT(*) FROM [{cls.TABLE_NAME}]",
                'cursos_ativos': f"SELECT COUNT(*) FROM [{cls.TABLE_NAME}] WHERE [ativo] = 'S'",
                'modalidades_distintas': f"SELECT COUNT(DISTINCT [modalidade]) FROM [{cls.TABLE_NAME}]",
                'niveis_distintos': f"SELECT COUNT(DISTINCT [nivel]) FROM [{cls.TABLE_NAME}]",
                'ultima_atualizacao': f"SELECT MAX([data_atualizacao]) FROM [{cls.TABLE_NAME}]"
            }

            results = {}
            for key, query in queries.items():
                row = fetch_one(query, db_path=cls.DB_NAME)
                results[key] = row[0] if row else 0

            return results

        except Exception as e:
            logger.error(f"Erro ao obter resumo: {e}")
            return {}

    @classmethod
    def get_all_cursos(cls) -> List[Dict]:
        """Retorna todos os cursos da tabela."""
        try:
            sql = f"SELECT * FROM [{cls.TABLE_NAME}] ORDER BY [curso]"
            rows = fetch_all(sql, db_path=cls.DB_NAME)
            if not rows:
                return []

            # Obter nomes das colunas
            col_query = """
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = ?
                ORDER BY ORDINAL_POSITION
            """
            col_rows = fetch_all(col_query, (cls.TABLE_NAME,), db_path=cls.DB_NAME)
            columns = [row[0] for row in col_rows] if col_rows else []

            cursos = []
            for row in rows:
                curso = {}
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
        """Retorna um curso específico pelo código."""
        try:
            sql = f"SELECT * FROM [{cls.TABLE_NAME}] WHERE [curso] = ?"
            row = fetch_one(sql, (curso_code,), db_path=cls.DB_NAME)
            if not row:
                return None

            # Obter nomes das colunas
            col_query = """
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = ?
                ORDER BY ORDINAL_POSITION
            """
            col_rows = fetch_all(col_query, (cls.TABLE_NAME,), db_path=cls.DB_NAME)
            columns = [col[0] for col in col_rows] if col_rows else []

            curso = {}
            for i, col in enumerate(columns):
                if i < len(row):
                    curso[col] = row[i]
            return curso

        except Exception as e:
            logger.error(f"Erro ao buscar curso {curso_code}: {e}")
            return None

    @classmethod
    def get_cursos_ativos(cls) -> List[Dict]:
        """Retorna todos os cursos ativos."""
        try:
            sql = f"SELECT * FROM [{cls.TABLE_NAME}] WHERE [ativo] = 'S' ORDER BY [curso]"
            rows = fetch_all(sql, db_path=cls.DB_NAME)
            if not rows:
                return []

            col_query = """
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = ?
                ORDER BY ORDINAL_POSITION
            """
            col_rows = fetch_all(col_query, (cls.TABLE_NAME,), db_path=cls.DB_NAME)
            columns = [col[0] for col in col_rows] if col_rows else []

            cursos = []
            for row in rows:
                curso = {}
                for i, col in enumerate(columns):
                    if i < len(row):
                        curso[col] = row[i]
                cursos.append(curso)

            return cursos

        except Exception as e:
            logger.error(f"Erro ao buscar cursos ativos: {e}")
            return []