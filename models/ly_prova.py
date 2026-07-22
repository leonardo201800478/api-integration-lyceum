#!/usr/bin/env python3
"""
models/ly_prova.py
Modelo para tabela LY_PROVA - SQL Server
Chave primária composta: (ano, disciplina, prova, semestre, turma)
"""

import logging
from typing import List, Dict, Any, Optional
from core.database import get_db_connection, execute_query, fetch_all, fetch_one

logger = logging.getLogger(__name__)


class LyProvaModel:
    TABLE_NAME = "LY_PROVA"
    DB_NAME = "lyceum"

    API_FIELDS = [
        'ano', 'classificacao', 'complemento', 'data_divulgacao_aol', 'disciplina',
        'dt_divulgacao', 'dt_inicio', 'dt_limite', 'dt_max_revisao', 'dt_prova',
        'e_oficial', 'e_prova_base_rec', 'e_recuperacao', 'fl_field01', 'fl_field02',
        'fl_field03', 'fl_field04', 'fl_field05', 'fl_field06', 'fl_field07',
        'fl_field08', 'fl_field09', 'fl_field10', 'formula', 'local_trabalho', 'nome',
        'nota_base_rec', 'nota_max', 'num_func', 'on_line', 'ordem',
        'pode_alterar_formula', 'prova', 'prova_base_recuperacao', 'prova_discip_extensiva',
        'read_only', 'result_nulo', 'semestre', 'simulado', 'subdisciplina', 'subperiodo',
        'trabalho', 'turma'
    ]

    PK_FIELDS = ['ano', 'disciplina', 'prova', 'semestre', 'turma']

    @classmethod
    def _normalize_value(cls, value: Any) -> Any:
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
        if cls._table_exists():
            logger.info(f"Tabela {cls.TABLE_NAME} já existe.")
            return True

        sql = f"""
        CREATE TABLE [{cls.TABLE_NAME}] (
            [ano] BIGINT NOT NULL,
            [disciplina] NVARCHAR(100) NOT NULL,
            [prova] NVARCHAR(100) NOT NULL,
            [semestre] BIGINT NOT NULL,
            [turma] NVARCHAR(100) NOT NULL,
            [classificacao] NVARCHAR(100),
            [complemento] NVARCHAR(500),
            [data_divulgacao_aol] NVARCHAR(30),
            [dt_divulgacao] NVARCHAR(30),
            [dt_inicio] NVARCHAR(30),
            [dt_limite] NVARCHAR(30),
            [dt_max_revisao] NVARCHAR(30),
            [dt_prova] NVARCHAR(30),
            [e_oficial] NVARCHAR(10),
            [e_prova_base_rec] NVARCHAR(10),
            [e_recuperacao] NVARCHAR(10),
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
            [formula] NVARCHAR(MAX),
            [local_trabalho] NVARCHAR(100),
            [nome] NVARCHAR(500),
            [nota_base_rec] NVARCHAR(50),
            [nota_max] DECIMAL(10,2),
            [num_func] BIGINT,
            [on_line] NVARCHAR(10),
            [ordem] INT,
            [pode_alterar_formula] NVARCHAR(10),
            [prova_base_recuperacao] NVARCHAR(100),
            [prova_discip_extensiva] NVARCHAR(100),
            [read_only] NVARCHAR(10),
            [result_nulo] NVARCHAR(10),
            [simulado] NVARCHAR(10),
            [subdisciplina] NVARCHAR(100),
            [subperiodo] INT,
            [trabalho] NVARCHAR(10),
            [data_importacao] DATETIME2 DEFAULT GETDATE(),
            [data_atualizacao] DATETIME2 DEFAULT GETDATE(),
            PRIMARY KEY ([ano], [disciplina], [prova], [semestre], [turma])
        )
        """
        try:
            execute_query(sql, database_name=cls.DB_NAME)
            indexes = [
                f"CREATE INDEX idx_prova_prova ON [{cls.TABLE_NAME}]([prova])",
                f"CREATE INDEX idx_prova_disciplina ON [{cls.TABLE_NAME}]([disciplina])",
                f"CREATE INDEX idx_prova_turma ON [{cls.TABLE_NAME}]([turma])",
                f"CREATE INDEX idx_prova_ano_sem ON [{cls.TABLE_NAME}]([ano], [semestre])",
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
    def upsert(cls, data: Dict) -> bool:
        try:
            pk_values = [cls._normalize_value(data.get(field)) for field in cls.PK_FIELDS]
            if None in pk_values:
                logger.warning(f"Registro sem chave completa: {data}")
                return False

            columns = cls.API_FIELDS
            values = [cls._normalize_value(data.get(field)) for field in columns]

            col_list = ', '.join([f"[{col}]" for col in columns])
            param_placeholders = ', '.join(['?' for _ in columns])
            source_cols = ', '.join([f"source.[{col}]" for col in columns])

            update_set = ', '.join([
                f"target.[{col}] = source.[{col}]"
                for col in columns if col not in cls.PK_FIELDS
            ])
            if update_set:
                update_set += ', '
            update_set += "target.[data_atualizacao] = GETDATE()"

            insert_cols = f"{col_list}, [data_importacao], [data_atualizacao]"
            insert_vals = f"{source_cols}, GETDATE(), GETDATE()"

            merge_sql = f"""
                MERGE INTO [{cls.TABLE_NAME}] AS target
                USING (VALUES ({param_placeholders})) AS source ({col_list})
                ON {' AND '.join([f"target.[{pk}] = source.[{pk}]" for pk in cls.PK_FIELDS])}
                WHEN MATCHED THEN
                    UPDATE SET {update_set}
                WHEN NOT MATCHED THEN
                    INSERT ({insert_cols})
                    VALUES ({insert_vals});
            """
            execute_query(merge_sql, tuple(values), database_name=cls.DB_NAME)
            return True
        except Exception as e:
            logger.error(f"Erro ao upsert prova {data.get('prova')}: {e}")
            return False

    @classmethod
    def batch_upsert(cls, data_list: List[Dict]) -> int:
        if not data_list:
            return 0
        success = 0
        errors = 0
        with get_db_connection(database_name=cls.DB_NAME) as conn:
            cursor = conn.cursor()
            for data in data_list:
                try:
                    pk_values = [cls._normalize_value(data.get(field)) for field in cls.PK_FIELDS]
                    if None in pk_values:
                        errors += 1
                        continue
                    columns = cls.API_FIELDS
                    values = [cls._normalize_value(data.get(field)) for field in columns]
                    col_list = ', '.join([f"[{col}]" for col in columns])
                    param_placeholders = ', '.join(['?' for _ in columns])
                    source_cols = ', '.join([f"source.[{col}]" for col in columns])
                    update_set = ', '.join([
                        f"target.[{col}] = source.[{col}]"
                        for col in columns if col not in cls.PK_FIELDS
                    ])
                    if update_set:
                        update_set += ', '
                    update_set += "target.[data_atualizacao] = GETDATE()"
                    insert_cols = f"{col_list}, [data_importacao], [data_atualizacao]"
                    insert_vals = f"{source_cols}, GETDATE(), GETDATE()"
                    merge_sql = f"""
                        MERGE INTO [{cls.TABLE_NAME}] AS target
                        USING (VALUES ({param_placeholders})) AS source ({col_list})
                        ON {' AND '.join([f"target.[{pk}] = source.[{pk}]" for pk in cls.PK_FIELDS])}
                        WHEN MATCHED THEN
                            UPDATE SET {update_set}
                        WHEN NOT MATCHED THEN
                            INSERT ({insert_cols})
                            VALUES ({insert_vals});
                    """
                    cursor.execute(merge_sql, tuple(values))
                    success += 1
                except Exception as e:
                    logger.error(f"Erro ao upsert prova {data.get('prova')}: {e}")
                    errors += 1
            conn.commit()
        logger.info(f"Batch upsert: {success} sucessos, {errors} erros, total {len(data_list)}")
        return success

    @classmethod
    def get_summary(cls) -> Dict:
        try:
            queries = {
                'total_provas': f"SELECT COUNT(*) FROM [{cls.TABLE_NAME}]",
                'ultima_atualizacao': f"SELECT MAX([data_atualizacao]) FROM [{cls.TABLE_NAME}]",
                'disciplinas_distintas': f"SELECT COUNT(DISTINCT [disciplina]) FROM [{cls.TABLE_NAME}]",
                'turmas_distintas': f"SELECT COUNT(DISTINCT [turma]) FROM [{cls.TABLE_NAME}]",
            }
            results = {}
            for key, query in queries.items():
                row = fetch_one(query, database_name=cls.DB_NAME)
                results[key] = row[0] if row else 0
            return results
        except Exception as e:
            logger.error(f"Erro ao obter resumo: {e}")
            return {}