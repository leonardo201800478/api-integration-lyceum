#!/usr/bin/env python3
"""
Modelo para tabela LY_PROVA_DISCIP (Provas Disciplinas) - SQL Server
Chave primária composta: (prova, disciplina) ? Ou usar IDENTITY?
A API retorna uma lista paginada, sem chave natural óbvia. Vamos usar IDENTITY.
"""

import logging
from typing import List, Dict, Any, Optional
from core.database import get_db_connection, execute_query, fetch_all, fetch_one

logger = logging.getLogger(__name__)


class LyProvaDiscipModel:
    TABLE_NAME = "LY_PROVA_DISCIP"
    DB_NAME = "lyceum.db"  # nome do banco no SQL Server

    # Lista de campos da API (conforme documentação)
    API_FIELDS = [
        'classificacao', 'descricao', 'disciplina', 'e_oficial', 'e_prova_base_rec',
        'e_recuperacao', 'fl_field01', 'fl_field02', 'fl_field03', 'fl_field04',
        'fl_field05', 'fl_field06', 'fl_field07', 'fl_field08', 'fl_field09',
        'fl_field10', 'formula', 'local_trabalho', 'nota_base_rec', 'nota_max',
        'on_line', 'ordem', 'pode_alterar_formula', 'prova', 'prova_base_recuperacao',
        'result_nulo', 'subdisciplina', 'subperiodo', 'trabalho'
    ]

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
        result = fetch_one(query, (cls.TABLE_NAME,), db_path=cls.DB_NAME)
        return result is not None

    @classmethod
    def create_table(cls):
        if cls._table_exists():
            logger.info(f"Tabela {cls.TABLE_NAME} já existe.")
            return True

        sql = f"""
        CREATE TABLE [{cls.TABLE_NAME}] (
            [id] INT IDENTITY(1,1) PRIMARY KEY,
            [classificacao] NVARCHAR(100),
            [descricao] NVARCHAR(500),
            [disciplina] NVARCHAR(100) NOT NULL,
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
            [nota_base_rec] NVARCHAR(50),
            [nota_max] DECIMAL(10,2),
            [on_line] NVARCHAR(10),
            [ordem] INT,
            [pode_alterar_formula] NVARCHAR(10),
            [prova] NVARCHAR(100) NOT NULL,
            [prova_base_recuperacao] NVARCHAR(100),
            [result_nulo] NVARCHAR(10),
            [subdisciplina] NVARCHAR(100),
            [subperiodo] INT,
            [trabalho] NVARCHAR(10),
            [data_importacao] DATETIME2 DEFAULT GETDATE(),
            [data_atualizacao] DATETIME2 DEFAULT GETDATE()
        )
        """
        try:
            execute_query(sql, db_path=cls.DB_NAME)

            # Índices
            indexes = [
                f"CREATE INDEX idx_prova_discip_prova ON [{cls.TABLE_NAME}]([prova])",
                f"CREATE INDEX idx_prova_discip_disciplina ON [{cls.TABLE_NAME}]([disciplina])",
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
    def batch_insert(cls, data_list: List[Dict]) -> int:
        """Insere múltiplos registros em lote (ignora duplicatas baseado em prova+disciplina)."""
        if not data_list:
            return 0

        success = 0
        errors = 0

        with get_db_connection(db_path=cls.DB_NAME) as conn:
            cursor = conn.cursor()
            for data in data_list:
                try:
                    # Campos obrigatórios (prova e disciplina)
                    prova = cls._normalize_value(data.get('prova'))
                    disciplina = cls._normalize_value(data.get('disciplina'))
                    if not prova or not disciplina:
                        logger.warning(f"Registro sem prova ou disciplina: {data}")
                        errors += 1
                        continue

                    columns = ['prova', 'disciplina']
                    values = [prova, disciplina]

                    for field in cls.API_FIELDS:
                        if field not in ['prova', 'disciplina']:
                            val = cls._normalize_value(data.get(field))
                            if val is not None:
                                columns.append(field)
                                values.append(val)

                    cols_str = ', '.join([f"[{c}]" for c in columns])
                    placeholders = ', '.join(['?' for _ in values])

                    # Usar MERGE para evitar duplicatas (chave: prova+disciplina)
                    merge_sql = f"""
                        MERGE INTO [{cls.TABLE_NAME}] AS target
                        USING (VALUES ({placeholders})) AS source ({cols_str})
                        ON target.[prova] = source.[prova] AND target.[disciplina] = source.[disciplina]
                        WHEN MATCHED THEN
                            UPDATE SET {', '.join([f"target.[{c}] = source.[{c}]" for c in columns if c not in ['prova', 'disciplina']])},
                                      target.[data_atualizacao] = GETDATE()
                        WHEN NOT MATCHED THEN
                            INSERT ({cols_str}, [data_importacao], [data_atualizacao])
                            VALUES ({placeholders}, GETDATE(), GETDATE());
                    """
                    cursor.execute(merge_sql, tuple(values * 2))  # valores duas vezes (uma para source, uma para insert)
                    success += 1
                except Exception as e:
                    logger.error(f"Erro ao inserir prova_discip {data.get('prova')}/{data.get('disciplina')}: {e}")
                    errors += 1
            conn.commit()

        logger.info(f"Batch insert: {success} sucessos, {errors} erros, total {len(data_list)}")
        return success

    @classmethod
    def clear_table(cls):
        try:
            sql = f"DELETE FROM [{cls.TABLE_NAME}]"
            execute_query(sql, db_path=cls.DB_NAME)
            logger.info(f"Tabela {cls.TABLE_NAME} limpa.")
            return True
        except Exception as e:
            logger.error(f"Erro ao limpar tabela {cls.TABLE_NAME}: {e}")
            return False

    @classmethod
    def get_all_provas_disciplinas(cls) -> List[Dict]:
        """Retorna todos os registros para serem usados na busca de provas detalhadas."""
        sql = f"SELECT * FROM [{cls.TABLE_NAME}] ORDER BY [prova], [disciplina]"
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