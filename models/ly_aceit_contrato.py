#!/usr/bin/env python3
"""
models/ly_aceit_contrato.py
Modelo para tabela LY_ACEIT_CONTRATO usando core.database (SQL Server)
COM chave primária composta (codAluno, ano, periodo)
"""

import logging
from typing import List, Dict, Any, Optional
from core.database import get_db_connection, execute_query, fetch_all, fetch_one

logger = logging.getLogger(__name__)


class LyAceitContratoModel:
    """
    Modelo para tabela LY_ACEIT_CONTRATO com chave primária composta.
    Armazena se um aluno aceitou o contrato em um determinado ano/período.
    """

    TABLE_NAME = "LY_ACEIT_CONTRATO"
    DB_NAME = "lyceum"  # nome do banco no SQL Server

    # Campos da fonte de dados (exclui metadados)
    API_FIELDS = ['codAluno', 'ano', 'periodo', 'existeContratoAceito']

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
        result = fetch_one(query, (cls.TABLE_NAME,), database_name=cls.DB_NAME)
        return result is not None

    @classmethod
    def create_table(cls):
        """Cria a tabela LY_ACEIT_CONTRATO se não existir (SQL Server)."""
        if cls._table_exists():
            logger.info(f"Tabela {cls.TABLE_NAME} já existe.")
            return True

        # SQL para criar a tabela com chave primária composta
        sql = f"""
        CREATE TABLE [{cls.TABLE_NAME}] (
            [codAluno] NVARCHAR(50) NOT NULL,
            [ano] INT NOT NULL,
            [periodo] INT NOT NULL,
            [existeContratoAceito] CHAR(1) NULL,  -- 'S' ou 'N'
            [data_importacao] DATETIME2 DEFAULT GETDATE(),
            [data_atualizacao] DATETIME2 DEFAULT GETDATE(),
            CONSTRAINT PK_{cls.TABLE_NAME} PRIMARY KEY ([codAluno], [ano], [periodo])
        )
        """

        try:
            execute_query(sql, database_name=cls.DB_NAME)

            # Criar índices adicionais para consultas comuns
            indexes = [
                f"CREATE INDEX idx_{cls.TABLE_NAME}_ano_periodo ON [{cls.TABLE_NAME}]([ano], [periodo])",
                f"CREATE INDEX idx_{cls.TABLE_NAME}_existe ON [{cls.TABLE_NAME}]([existeContratoAceito])"
            ]
            for idx_sql in indexes:
                try:
                    execute_query(idx_sql, database_name=cls.DB_NAME)
                except Exception as e:
                    logger.warning(f"Erro ao criar índice: {e}")

            logger.info(f"Tabela {cls.TABLE_NAME} criada com sucesso (chave primária composta).")
            return True

        except Exception as e:
            logger.error(f"Erro ao criar tabela {cls.TABLE_NAME}: {e}")
            return False

    @classmethod
    def upsert(cls, data: Dict) -> bool:
        """
        Insere ou atualiza um único registro usando MERGE.
        Espera um dicionário com as chaves: codAluno, ano, periodo, existeContratoAceito.
        """
        try:
            cod_aluno = cls._normalize_value(data.get('codAluno'))
            ano = cls._normalize_value(data.get('ano'))
            periodo = cls._normalize_value(data.get('periodo'))

            if not cod_aluno or ano is None or periodo is None:
                logger.warning(f"Dados incompletos: {data}")
                return False

            # Lista de colunas (API_FIELDS) na ordem
            columns = cls.API_FIELDS
            values = [cls._normalize_value(data.get(col)) for col in columns]

            col_list = ', '.join([f"[{col}]" for col in columns])
            param_placeholders = ', '.join(['?' for _ in columns])
            source_cols = ', '.join([f"source.[{col}]" for col in columns])

            # Condição de match: chave composta
            match_condition = "target.[codAluno] = source.[codAluno] AND target.[ano] = source.[ano] AND target.[periodo] = source.[periodo]"

            # UPDATE SET: todas as colunas exceto as chaves
            update_set = ', '.join([
                f"target.[{col}] = source.[{col}]"
                for col in columns if col not in ['codAluno', 'ano', 'periodo']
            ])
            if update_set:
                update_set += ', '
            update_set += "target.[data_atualizacao] = GETDATE()"

            # INSERT: colunas da fonte + metadados
            insert_cols = f"{col_list}, [data_importacao], [data_atualizacao]"
            insert_vals = f"{source_cols}, GETDATE(), GETDATE()"

            merge_sql = f"""
                MERGE INTO [{cls.TABLE_NAME}] AS target
                USING (VALUES ({param_placeholders})) AS source ({col_list})
                ON {match_condition}
                WHEN MATCHED THEN
                    UPDATE SET {update_set}
                WHEN NOT MATCHED THEN
                    INSERT ({insert_cols})
                    VALUES ({insert_vals});
            """

            execute_query(merge_sql, tuple(values), database_name=cls.DB_NAME)
            logger.debug(f"Registro {cod_aluno}/{ano}/{periodo} upsert realizado com sucesso")
            return True

        except Exception as e:
            logger.error(f"Erro ao upsert registro {data.get('codAluno')}/{data.get('ano')}/{data.get('periodo')}: {e}")
            return False

    @classmethod
    def batch_upsert(cls, data_list: List[Dict]) -> int:
        """Insere ou atualiza múltiplos registros em lote."""
        if not data_list:
            return 0

        success_count = 0
        error_count = 0

        with get_db_connection(database_name=cls.DB_NAME) as conn:
            cursor = conn.cursor()
            columns = cls.API_FIELDS
            col_list = ', '.join([f"[{col}]" for col in columns])
            param_placeholders = ', '.join(['?' for _ in columns])
            source_cols = ', '.join([f"source.[{col}]" for col in columns])

            match_condition = "target.[codAluno] = source.[codAluno] AND target.[ano] = source.[ano] AND target.[periodo] = source.[periodo]"

            update_set = ', '.join([
                f"target.[{col}] = source.[{col}]"
                for col in columns if col not in ['codAluno', 'ano', 'periodo']
            ])
            if update_set:
                update_set += ', '
            update_set += "target.[data_atualizacao] = GETDATE()"

            insert_cols = f"{col_list}, [data_importacao], [data_atualizacao]"
            insert_vals = f"{source_cols}, GETDATE(), GETDATE()"

            merge_sql = f"""
                MERGE INTO [{cls.TABLE_NAME}] AS target
                USING (VALUES ({param_placeholders})) AS source ({col_list})
                ON {match_condition}
                WHEN MATCHED THEN
                    UPDATE SET {update_set}
                WHEN NOT MATCHED THEN
                    INSERT ({insert_cols})
                    VALUES ({insert_vals});
            """

            for data in data_list:
                try:
                    cod_aluno = cls._normalize_value(data.get('codAluno'))
                    ano = cls._normalize_value(data.get('ano'))
                    periodo = cls._normalize_value(data.get('periodo'))
                    if not cod_aluno or ano is None or periodo is None:
                        logger.warning(f"Dados incompletos: {data}")
                        error_count += 1
                        continue

                    values = [cls._normalize_value(data.get(col)) for col in columns]
                    cursor.execute(merge_sql, tuple(values))
                    success_count += 1

                except Exception as e:
                    logger.error(f"Erro ao processar registro {data.get('codAluno')}/{data.get('ano')}/{data.get('periodo')}: {e}")
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
                'total_registros': f"SELECT COUNT(*) FROM [{cls.TABLE_NAME}]",
                'total_aceitos': f"SELECT COUNT(*) FROM [{cls.TABLE_NAME}] WHERE [existeContratoAceito] = 'S'",
                'total_nao_aceitos': f"SELECT COUNT(*) FROM [{cls.TABLE_NAME}] WHERE [existeContratoAceito] = 'N'",
                'anos_distintos': f"SELECT COUNT(DISTINCT [ano]) FROM [{cls.TABLE_NAME}]",
                'ultima_atualizacao': f"SELECT MAX([data_atualizacao]) FROM [{cls.TABLE_NAME}]"
            }

            results = {}
            for key, query in queries.items():
                row = fetch_one(query, database_name=cls.DB_NAME)
                results[key] = row[0] if row else 0

            return results

        except Exception as e:
            logger.error(f"Erro ao obter resumo: {e}")
            return {}

    @classmethod
    def get_by_aluno(cls, codAluno: str) -> List[Dict]:
        """Retorna todos os registros de um determinado aluno."""
        try:
            sql = f"SELECT * FROM [{cls.TABLE_NAME}] WHERE [codAluno] = ? ORDER BY [ano] DESC, [periodo] DESC"
            rows = fetch_all(sql, (codAluno,), database_name=cls.DB_NAME)
            if not rows:
                return []

            col_query = """
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = ?
                ORDER BY ORDINAL_POSITION
            """
            col_rows = fetch_all(col_query, (cls.TABLE_NAME,), database_name=cls.DB_NAME)
            columns = [col[0] for col in col_rows] if col_rows else []

            result = []
            for row in rows:
                item = {}
                for i, col in enumerate(columns):
                    if i < len(row):
                        item[col] = row[i]
                result.append(item)
            return result

        except Exception as e:
            logger.error(f"Erro ao buscar registros do aluno {codAluno}: {e}")
            return []

    @classmethod
    def get_by_ano_periodo(cls, ano: int, periodo: int) -> List[Dict]:
        """Retorna todos os registros de um determinado ano/período."""
        try:
            sql = f"SELECT * FROM [{cls.TABLE_NAME}] WHERE [ano] = ? AND [periodo] = ? ORDER BY [codAluno]"
            rows = fetch_all(sql, (ano, periodo), database_name=cls.DB_NAME)
            if not rows:
                return []

            col_query = """
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = ?
                ORDER BY ORDINAL_POSITION
            """
            col_rows = fetch_all(col_query, (cls.TABLE_NAME,), database_name=cls.DB_NAME)
            columns = [col[0] for col in col_rows] if col_rows else []

            result = []
            for row in rows:
                item = {}
                for i, col in enumerate(columns):
                    if i < len(row):
                        item[col] = row[i]
                result.append(item)
            return result

        except Exception as e:
            logger.error(f"Erro ao buscar registros para ano/período {ano}/{periodo}: {e}")
            return []