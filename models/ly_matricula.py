#!/usr/bin/env python3
"""
Modelo para tabela LY_MATRICULA usando core.database (SQL Server)
SEM chave primária natural – usa IDENTITY.
"""

import logging
from typing import List, Dict, Any, Optional
from core.database import get_db_connection, execute_query, fetch_all, fetch_one

logger = logging.getLogger(__name__)


class LyMatriculaModel:
    """Modelo para tabela LY_MATRICULA (SQL Server) sem chave primária natural."""

    TABLE_NAME = "LY_MATRICULA"
    DB_NAME = "lyceum.db"  # nome do banco no SQL Server

    API_FIELDS = [
        'aluno', 'ano', 'semestre', 'turma', 'disciplina',
        'cobranca_sep', 'conceito_fim', 'conceito_fim_num',
        'dt_insercao', 'dt_matricula', 'dt_reabertura', 'dt_ultalt',
        'grupo_eletiva', 'lanc_deb', 'num_chamada', 'obs',
        'perc_presfim', 'plano_pagto_pad_esp', 'serie_calculo',
        'sit_detalhe', 'sit_matricula', 'subturma1', 'subturma2',
        'tipo_aprovacao', 'tot_aulas',
        # Campos flag
        'fl_field01', 'fl_field02', 'fl_field03', 'fl_field04', 'fl_field05',
        'fl_field06', 'fl_field07', 'fl_field08', 'fl_field09', 'fl_field10'
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
        result = fetch_one(query, (cls.TABLE_NAME,), db_path=cls.DB_NAME)
        return result is not None

    @classmethod
    def create_table(cls):
        """Cria a tabela LY_MATRICULA se não existir (SQL Server)."""
        if cls._table_exists():
            logger.info(f"Tabela {cls.TABLE_NAME} já existe.")
            return True

        sql = f"""
        CREATE TABLE [{cls.TABLE_NAME}] (
            [id] INT IDENTITY(1,1) PRIMARY KEY,
            [aluno] NVARCHAR(100) NOT NULL,
            [ano] BIGINT NOT NULL,
            [semestre] BIGINT NOT NULL,
            [turma] NVARCHAR(100) NOT NULL,
            [disciplina] NVARCHAR(100) NOT NULL,
            [cobranca_sep] NVARCHAR(50),
            [conceito_fim] NVARCHAR(20),
            [conceito_fim_num] FLOAT,
            [dt_insercao] NVARCHAR(20),
            [dt_matricula] NVARCHAR(20),
            [dt_reabertura] NVARCHAR(20),
            [dt_ultalt] NVARCHAR(20),
            [grupo_eletiva] NVARCHAR(100),
            [lanc_deb] FLOAT,
            [num_chamada] BIGINT,
            [obs] NVARCHAR(MAX),
            [perc_presfim] FLOAT,
            [plano_pagto_pad_esp] NVARCHAR(50),
            [serie_calculo] BIGINT,
            [sit_detalhe] NVARCHAR(50),
            [sit_matricula] NVARCHAR(20),
            [subturma1] NVARCHAR(100),
            [subturma2] NVARCHAR(100),
            [tipo_aprovacao] NVARCHAR(50),
            [tot_aulas] BIGINT,
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
            [data_importacao] DATETIME2 DEFAULT GETDATE(),
            [data_atualizacao] DATETIME2 DEFAULT GETDATE()
        )
        """

        try:
            execute_query(sql, db_path=cls.DB_NAME)

            # Índices
            indexes = [
                f"CREATE INDEX idx_matricula_ano_semestre ON [{cls.TABLE_NAME}]([ano], [semestre])",
                f"CREATE INDEX idx_matricula_aluno ON [{cls.TABLE_NAME}]([aluno])",
                f"CREATE INDEX idx_matricula_turma ON [{cls.TABLE_NAME}]([turma])",
                f"CREATE INDEX idx_matricula_disciplina ON [{cls.TABLE_NAME}]([disciplina])",
                f"CREATE INDEX idx_matricula_sit_matricula ON [{cls.TABLE_NAME}]([sit_matricula])",
                f"CREATE INDEX idx_matricula_ano_sem_aluno ON [{cls.TABLE_NAME}]([ano], [semestre], [aluno])",
                f"CREATE INDEX idx_matricula_ano_sem_turma ON [{cls.TABLE_NAME}]([ano], [semestre], [turma])",
                f"CREATE INDEX idx_matricula_turma_disciplina ON [{cls.TABLE_NAME}]([turma], [disciplina])",
            ]
            for idx_sql in indexes:
                try:
                    execute_query(idx_sql, db_path=cls.DB_NAME)
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
            execute_query(sql, db_path=cls.DB_NAME)
            logger.info(f"Tabela {cls.TABLE_NAME} limpa.")
            return True
        except Exception as e:
            logger.error(f"Erro ao limpar tabela {cls.TABLE_NAME}: {e}")
            return False

    @classmethod
    def insert(cls, data: Dict) -> bool:
        """Insere uma nova matrícula (não verifica duplicatas)."""
        try:
            aluno = cls._normalize_value(data.get('aluno'))
            ano = cls._normalize_value(data.get('ano'))
            semestre = cls._normalize_value(data.get('semestre'))
            turma = cls._normalize_value(data.get('turma'))
            disciplina = cls._normalize_value(data.get('disciplina'))

            if not all([aluno, ano, semestre, turma, disciplina]):
                logger.warning(f"Matrícula sem campos obrigatórios: {data}")
                return False

            columns = ['aluno', 'ano', 'semestre', 'turma', 'disciplina']
            values = [aluno, ano, semestre, turma, disciplina]

            for field in cls.API_FIELDS:
                if field not in ['aluno', 'ano', 'semestre', 'turma', 'disciplina']:
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
            execute_query(sql, tuple(values), db_path=cls.DB_NAME)
            return True
        except Exception as e:
            logger.error(f"Erro ao inserir matrícula {data.get('aluno')}/{data.get('ano')}/{data.get('semestre')}/{data.get('disciplina')}/{data.get('turma')}: {e}")
            return False

    @classmethod
    def batch_insert(cls, data_list: List[Dict]) -> int:
        """Insere múltiplas matrículas em lote (permite duplicatas)."""
        if not data_list:
            return 0

        success = 0
        errors = 0

        with get_db_connection(db_path=cls.DB_NAME) as conn:
            cursor = conn.cursor()
            for data in data_list:
                try:
                    aluno = cls._normalize_value(data.get('aluno'))
                    ano = cls._normalize_value(data.get('ano'))
                    semestre = cls._normalize_value(data.get('semestre'))
                    turma = cls._normalize_value(data.get('turma'))
                    disciplina = cls._normalize_value(data.get('disciplina'))

                    if not all([aluno, ano, semestre, turma, disciplina]):
                        logger.warning(f"Matrícula sem campos obrigatórios: {data}")
                        errors += 1
                        continue

                    columns = ['aluno', 'ano', 'semestre', 'turma', 'disciplina']
                    values = [aluno, ano, semestre, turma, disciplina]

                    for field in cls.API_FIELDS:
                        if field not in ['aluno', 'ano', 'semestre', 'turma', 'disciplina']:
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
                    logger.error(f"Erro ao inserir matrícula {data.get('aluno')}/{data.get('ano')}/{data.get('semestre')}/{data.get('disciplina')}/{data.get('turma')}: {e}")
                    errors += 1
            conn.commit()

        logger.info(f"Batch insert: {success} sucessos, {errors} erros, total {len(data_list)}")
        return success

    @classmethod
    def get_summary(cls) -> Dict:
        """Retorna estatísticas da tabela."""
        queries = {
            'total_matriculas': f"SELECT COUNT(*) FROM [{cls.TABLE_NAME}]",
            'alunos_distintos': f"SELECT COUNT(DISTINCT [aluno]) FROM [{cls.TABLE_NAME}]",
            'turmas_distintas': f"SELECT COUNT(DISTINCT [turma]) FROM [{cls.TABLE_NAME}]",
            'disciplinas_distintas': f"SELECT COUNT(DISTINCT [disciplina]) FROM [{cls.TABLE_NAME}]",
            'anos_distintos': f"SELECT COUNT(DISTINCT [ano]) FROM [{cls.TABLE_NAME}]",
            'semestres_distintos': f"SELECT COUNT(DISTINCT [semestre]) FROM [{cls.TABLE_NAME}]",
            'matriculas_ativas': f"SELECT COUNT(*) FROM [{cls.TABLE_NAME}] WHERE [sit_matricula] = 'A'",
            'ultima_atualizacao': f"SELECT MAX([data_atualizacao]) FROM [{cls.TABLE_NAME}]"
        }
        results = {}
        for key, q in queries.items():
            row = fetch_one(q, db_path=cls.DB_NAME)
            results[key] = row[0] if row else 0
        return results

    @classmethod
    def get_all_matriculas(cls) -> List[Dict]:
        """Retorna todas as matrículas da tabela."""
        sql = f"SELECT * FROM [{cls.TABLE_NAME}] ORDER BY [ano] DESC, [semestre] DESC, [aluno], [disciplina]"
        rows = fetch_all(sql, db_path=cls.DB_NAME)
        if not rows:
            return []
        col_query = """
            SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = ? ORDER BY ORDINAL_POSITION
        """
        col_rows = fetch_all(col_query, (cls.TABLE_NAME,), db_path=cls.DB_NAME)
        columns = [r[0] for r in col_rows]
        return [dict(zip(columns, row)) for row in rows]

    @classmethod
    def get_by_ano_semestre(cls, ano: int, semestre: int) -> List[Dict]:
        """Retorna todas as matrículas de um ano/semestre específico."""
        sql = f"SELECT * FROM [{cls.TABLE_NAME}] WHERE [ano] = ? AND [semestre] = ? ORDER BY [aluno], [disciplina]"
        rows = fetch_all(sql, (ano, semestre), db_path=cls.DB_NAME)
        if not rows:
            return []
        col_query = """
            SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = ? ORDER BY ORDINAL_POSITION
        """
        col_rows = fetch_all(col_query, (cls.TABLE_NAME,), db_path=cls.DB_NAME)
        columns = [r[0] for r in col_rows]
        return [dict(zip(columns, row)) for row in rows]

    @classmethod
    def get_by_aluno(cls, aluno_code: str) -> List[Dict]:
        """Retorna todas as matrículas de um aluno específico."""
        sql = f"SELECT * FROM [{cls.TABLE_NAME}] WHERE [aluno] = ? ORDER BY [ano] DESC, [semestre] DESC, [disciplina]"
        rows = fetch_all(sql, (aluno_code,), db_path=cls.DB_NAME)
        if not rows:
            return []
        col_query = """
            SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = ? ORDER BY ORDINAL_POSITION
        """
        col_rows = fetch_all(col_query, (cls.TABLE_NAME,), db_path=cls.DB_NAME)
        columns = [r[0] for r in col_rows]
        return [dict(zip(columns, row)) for row in rows]