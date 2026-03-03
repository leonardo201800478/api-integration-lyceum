#!/usr/bin/env python3
"""
models/ly_grade.py
Modelo para tabela LY_GRADE usando core.database (SQL Server)
SEM chave primária natural – usa IDENTITY.
"""

import logging
from typing import List, Dict, Any, Optional
from core.database import get_db_connection, execute_query, fetch_all, fetch_one

logger = logging.getLogger(__name__)


class LyGradeModel:
    """Modelo para tabela LY_GRADE (SQL Server) sem chave primária natural."""

    TABLE_NAME = "LY_GRADE"
    DB_NAME = "lyceum.db"  # nome do banco no SQL Server

    API_FIELDS = [
        'atividade', 'aulas_sem_ativ', 'aulas_sem_aulas', 'aulas_sem_lab',
        'aulas_semanais', 'complemento', 'curriculo', 'curso', 'disciplina',
        'disciplina_extensiva', 'especial', 'fl_field01', 'fl_field02',
        'fl_field03', 'fl_field04', 'fl_field05', 'fl_field06', 'fl_field07',
        'fl_field08', 'fl_field09', 'fl_field10', 'formula_equiv',
        'formula_prereq', 'max_matr_aprov', 'max_reprov', 'nome_exibicao',
        'obrigatoria', 'permite_glp', 'retem_serie', 'serie_ideal',
        'serie_prereq', 'stamp_atualizacao', 'tese_dissertacao', 'turno'
    ]

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
        return str(value)

    @classmethod
    def _table_exists(cls) -> bool:
        query = """
            SELECT 1 FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_NAME = ? AND TABLE_TYPE = 'BASE TABLE'
        """
        result = fetch_one(query, (cls.TABLE_NAME,), database_name=cls.DB_NAME)
        return result is not None

    @classmethod
    def create_table(cls):
        """Cria a tabela LY_GRADE se não existir (SQL Server)."""
        if cls._table_exists():
            logger.info(f"Tabela {cls.TABLE_NAME} já existe.")
            return True

        sql = f"""
        CREATE TABLE [{cls.TABLE_NAME}] (
            [id] INT IDENTITY(1,1) PRIMARY KEY,
            [atividade] NVARCHAR(50),
            [aulas_sem_ativ] BIGINT,
            [aulas_sem_aulas] BIGINT,
            [aulas_sem_lab] BIGINT,
            [aulas_semanais] BIGINT,
            [complemento] NVARCHAR(255),
            [curriculo] NVARCHAR(100) NOT NULL,
            [curso] NVARCHAR(100) NOT NULL,
            [disciplina] NVARCHAR(100) NOT NULL,
            [disciplina_extensiva] NVARCHAR(255),
            [especial] CHAR(1),
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
            [formula_equiv] NVARCHAR(MAX),
            [formula_prereq] NVARCHAR(MAX),
            [max_matr_aprov] BIGINT,
            [max_reprov] BIGINT,
            [nome_exibicao] NVARCHAR(255),
            [obrigatoria] CHAR(1),
            [permite_glp] CHAR(1),
            [retem_serie] CHAR(1),
            [serie_ideal] BIGINT,
            [serie_prereq] BIGINT,
            [stamp_atualizacao] NVARCHAR(50),
            [tese_dissertacao] CHAR(1),
            [turno] NVARCHAR(20),
            [data_importacao] DATETIME2 DEFAULT GETDATE(),
            [data_atualizacao] DATETIME2 DEFAULT GETDATE()
        )
        """

        try:
            execute_query(sql, database_name=cls.DB_NAME)

            # Índices
            indexes = [
                f"CREATE INDEX idx_grade_curriculo_curso ON [{cls.TABLE_NAME}]([curriculo], [curso])",
                f"CREATE INDEX idx_grade_disciplina ON [{cls.TABLE_NAME}]([disciplina])",
                f"CREATE INDEX idx_grade_curso ON [{cls.TABLE_NAME}]([curso])",
                f"CREATE INDEX idx_grade_obrigatoria ON [{cls.TABLE_NAME}]([obrigatoria])",
                f"CREATE INDEX idx_grade_serie_ideal ON [{cls.TABLE_NAME}]([serie_ideal])",
            ]
            for idx_sql in indexes:
                try:
                    execute_query(idx_sql, database_name=cls.DB_NAME)
                except Exception as e:
                    logger.warning(f"Erro ao criar índice: {e}")

            logger.info(f"Tabela {cls.TABLE_NAME} criada com sucesso.")
            return True
        except Exception as e:
            logger.error(f"Erro ao criar tabela {cls.TABLE_NAME}: {e}")
            return False

    @classmethod
    def clear_table(cls):
        """Remove todos os registros da tabela."""
        try:
            sql = f"DELETE FROM [{cls.TABLE_NAME}]"
            execute_query(sql, database_name=cls.DB_NAME)
            logger.info(f"Tabela {cls.TABLE_NAME} limpa.")
            return True
        except Exception as e:
            logger.error(f"Erro ao limpar tabela {cls.TABLE_NAME}: {e}")
            return False

    @classmethod
    def insert(cls, data: Dict) -> bool:
        """Insere uma nova grade (não verifica duplicatas)."""
        try:
            curriculo = cls._normalize_value(data.get('curriculo'))
            curso = cls._normalize_value(data.get('curso'))
            disciplina = cls._normalize_value(data.get('disciplina'))

            if not all([curriculo, curso, disciplina]):
                logger.warning(f"Grade sem campos obrigatórios: {data}")
                return False

            columns = ['curriculo', 'curso', 'disciplina']
            values = [curriculo, curso, disciplina]

            for field in cls.API_FIELDS:
                if field not in ['curriculo', 'curso', 'disciplina']:
                    val = cls._normalize_value(data.get(field))
                    if val is not None:
                        columns.append(field)
                        values.append(val)

            cols_str = ', '.join([f"[{c}]" for c in columns])
            placeholders = ', '.join(['?' for _ in values])
            sql = f"""
                INSERT INTO [{cls.TABLE_NAME}] ({cols_str}, [data_atualizacao])
                VALUES ({placeholders}, GETDATE())
            """
            execute_query(sql, tuple(values), database_name=cls.DB_NAME)
            return True
        except Exception as e:
            logger.error(f"Erro ao inserir grade {data.get('curriculo')}/{data.get('curso')}/{data.get('disciplina')}: {e}")
            return False

    @classmethod
    def batch_insert(cls, data_list: List[Dict]) -> int:
        """Insere múltiplas grades em lote (permite duplicatas)."""
        if not data_list:
            return 0

        success = 0
        errors = 0

        with get_db_connection(database_name=cls.DB_NAME) as conn:
            cursor = conn.cursor()
            for data in data_list:
                try:
                    curriculo = cls._normalize_value(data.get('curriculo'))
                    curso = cls._normalize_value(data.get('curso'))
                    disciplina = cls._normalize_value(data.get('disciplina'))

                    if not all([curriculo, curso, disciplina]):
                        logger.warning(f"Grade sem campos obrigatórios: {data}")
                        errors += 1
                        continue

                    columns = ['curriculo', 'curso', 'disciplina']
                    values = [curriculo, curso, disciplina]

                    for field in cls.API_FIELDS:
                        if field not in ['curriculo', 'curso', 'disciplina']:
                            val = cls._normalize_value(data.get(field))
                            if val is not None:
                                columns.append(field)
                                values.append(val)

                    cols_str = ', '.join([f"[{c}]" for c in columns])
                    placeholders = ', '.join(['?' for _ in values])
                    sql = f"""
                        INSERT INTO [{cls.TABLE_NAME}] ({cols_str}, [data_atualizacao])
                        VALUES ({placeholders}, GETDATE())
                    """
                    cursor.execute(sql, tuple(values))
                    success += 1
                except Exception as e:
                    logger.error(f"Erro ao inserir grade {data.get('curriculo')}/{data.get('curso')}/{data.get('disciplina')}: {e}")
                    errors += 1
            conn.commit()

        logger.info(f"Batch insert: {success} sucessos, {errors} erros, total {len(data_list)}")
        return success

    @classmethod
    def get_summary(cls) -> Dict:
        """Retorna estatísticas da tabela."""
        queries = {
            'total_grades': f"SELECT COUNT(*) FROM [{cls.TABLE_NAME}]",
            'curriculos_distintos': f"SELECT COUNT(DISTINCT [curriculo]) FROM [{cls.TABLE_NAME}]",
            'cursos_distintos': f"SELECT COUNT(DISTINCT [curso]) FROM [{cls.TABLE_NAME}]",
            'disciplinas_distintas': f"SELECT COUNT(DISTINCT [disciplina]) FROM [{cls.TABLE_NAME}]",
            'obrigatorias': f"SELECT COUNT(*) FROM [{cls.TABLE_NAME}] WHERE [obrigatoria] = 'S'",
            'optativas': f"SELECT COUNT(*) FROM [{cls.TABLE_NAME}] WHERE [obrigatoria] = 'N'",
            'ultima_atualizacao': f"SELECT MAX([data_atualizacao]) FROM [{cls.TABLE_NAME}]"
        }
        results = {}
        for key, q in queries.items():
            row = fetch_one(q, database_name=cls.DB_NAME)
            results[key] = row[0] if row else 0
        return results

    @classmethod
    def get_all_grades(cls) -> List[Dict]:
        """Retorna todas as grades da tabela."""
        sql = f"SELECT * FROM [{cls.TABLE_NAME}] ORDER BY [curriculo], [curso], [serie_ideal], [disciplina]"
        rows = fetch_all(sql, database_name=cls.DB_NAME)
        if not rows:
            return []
        col_query = """
            SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = ? ORDER BY ORDINAL_POSITION
        """
        col_rows = fetch_all(col_query, (cls.TABLE_NAME,), database_name=cls.DB_NAME)
        columns = [r[0] for r in col_rows]
        return [dict(zip(columns, row)) for row in rows]

    @classmethod
    def get_by_curriculo_curso(cls, curriculo: str, curso: str) -> List[Dict]:
        """Retorna todas as grades de um currículo e curso específicos."""
        sql = f"SELECT * FROM [{cls.TABLE_NAME}] WHERE [curriculo] = ? AND [curso] = ? ORDER BY [serie_ideal], [disciplina]"
        rows = fetch_all(sql, (curriculo, curso), database_name=cls.DB_NAME)
        if not rows:
            return []
        col_query = """
            SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = ? ORDER BY ORDINAL_POSITION
        """
        col_rows = fetch_all(col_query, (cls.TABLE_NAME,), database_name=cls.DB_NAME)
        columns = [r[0] for r in col_rows]
        return [dict(zip(columns, row)) for row in rows]

    @classmethod
    def get_by_curso(cls, curso: str) -> List[Dict]:
        """Retorna todas as grades de um curso específico."""
        sql = f"SELECT * FROM [{cls.TABLE_NAME}] WHERE [curso] = ? ORDER BY [curriculo], [serie_ideal], [disciplina]"
        rows = fetch_all(sql, (curso,), database_name=cls.DB_NAME)
        if not rows:
            return []
        col_query = """
            SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = ? ORDER BY ORDINAL_POSITION
        """
        col_rows = fetch_all(col_query, (cls.TABLE_NAME,), database_name=cls.DB_NAME)
        columns = [r[0] for r in col_rows]
        return [dict(zip(columns, row)) for row in rows]

    @classmethod
    def get_by_disciplina(cls, disciplina: str) -> List[Dict]:
        """Retorna todas as grades de uma disciplina específica."""
        sql = f"SELECT * FROM [{cls.TABLE_NAME}] WHERE [disciplina] = ? ORDER BY [curriculo], [curso], [serie_ideal]"
        rows = fetch_all(sql, (disciplina,), database_name=cls.DB_NAME)
        if not rows:
            return []
        col_query = """
            SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = ? ORDER BY ORDINAL_POSITION
        """
        col_rows = fetch_all(col_query, (cls.TABLE_NAME,), database_name=cls.DB_NAME)
        columns = [r[0] for r in col_rows]
        return [dict(zip(columns, row)) for row in rows]