"""
models/ly_coordenacao.py
Modelo para tabela LY_COORDENACAO usando core.database (SQL Server)
Sem constraints NOT NULL - aceita todos os dados da API.
"""

import logging
from typing import List, Dict, Any, Optional

from core.database import get_db_connection, execute_query, fetch_all, fetch_one

logger = logging.getLogger(__name__)


class LyCoordenacaoModel:
    """Modelo para tabela LY_COORDENACAO - SQL Server"""

    TABLE_NAME = "LY_COORDENACAO"
    DB_NAME = "lyceum.db"  # nome do banco no SQL Server

    # Campos esperados da API (excluindo metadados)
    API_FIELDS = [
        'chave', 'classificacao', 'curriculo', 'curso', 'dt_fim', 'dt_ini',
        'num_func', 'participacao_porcent', 'tipo_coord', 'turno', 'unid_fisica'
    ]

    @classmethod
    def _normalize_value(cls, value: Any) -> Any:
        """Normaliza valores para inserção no SQL Server."""
        if value is None:
            return None

        if isinstance(value, str):
            value = value.strip()
            if value == '':
                return None

        if isinstance(value, (int, float)):
            return value

        # Para outros tipos (bool, etc.) converte para string
        return str(value)

    @classmethod
    def _table_exists(cls) -> bool:
        """Verifica se a tabela já existe no banco."""
        query = """
            SELECT 1 FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_NAME = ?
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
    def drop_and_recreate_table(cls):
        """Remove a tabela (se existir) e a recria com a estrutura correta."""
        try:
            # Remove tabela
            drop_sql = f"DROP TABLE IF EXISTS [{cls.TABLE_NAME}]"
            execute_query(drop_sql, db_path=cls.DB_NAME)
            logger.info(f"Tabela {cls.TABLE_NAME} removida (se existia).")

            # Cria nova tabela com tipos adequados para SQL Server
            create_sql = f"""
            CREATE TABLE [{cls.TABLE_NAME}] (
                [chave]                       NVARCHAR(255),
                [classificacao]                NVARCHAR(255),
                [curriculo]                    NVARCHAR(255),
                [curso]                        NVARCHAR(255),
                [dt_fim]                       NVARCHAR(20),
                [dt_ini]                       NVARCHAR(20),
                [num_func]                     NVARCHAR(50),
                [participacao_porcent]          FLOAT,
                [tipo_coord]                    NVARCHAR(50),
                [turno]                         NVARCHAR(20),
                [unid_fisica]                   NVARCHAR(50),
                [data_importacao]               DATETIME2 DEFAULT GETDATE(),
                [data_atualizacao]               DATETIME2 DEFAULT GETDATE()
            )
            """
            execute_query(create_sql, db_path=cls.DB_NAME)

            # Índices
            indexes = [
                f"CREATE INDEX idx_coordenacao_chave ON [{cls.TABLE_NAME}]([chave])",
                f"CREATE INDEX idx_coordenacao_curso ON [{cls.TABLE_NAME}]([curso])",
                f"CREATE INDEX idx_coordenacao_num_func ON [{cls.TABLE_NAME}]([num_func])",
                f"CREATE INDEX idx_coordenacao_tipo_coord ON [{cls.TABLE_NAME}]([tipo_coord])",
                f"CREATE INDEX idx_coordenacao_dt_ini ON [{cls.TABLE_NAME}]([dt_ini])"
            ]
            for idx_sql in indexes:
                try:
                    execute_query(idx_sql, db_path=cls.DB_NAME)
                except Exception as e:
                    logger.warning(f"Erro ao criar índice: {e}")

            logger.info(f"Tabela {cls.TABLE_NAME} recriada com sucesso.")
            return True

        except Exception as e:
            logger.error(f"Erro ao recriar tabela {cls.TABLE_NAME}: {e}")
            return False

    @classmethod
    def create_table(cls):
        """Verifica se a tabela existe e a recria se necessário."""
        try:
            if not cls._table_exists():
                return cls.drop_and_recreate_table()

            # Tabela existe: verifica colunas
            existing = set(cls._get_existing_columns())
            expected = set(cls.API_FIELDS + ['data_importacao', 'data_atualizacao'])

            if not expected.issubset(existing):
                missing = expected - existing
                logger.warning(f"Tabela {cls.TABLE_NAME} faltando colunas: {missing}. Recriando...")
                return cls.drop_and_recreate_table()

            logger.info(f"Tabela {cls.TABLE_NAME} já existe com estrutura adequada.")
            return True

        except Exception as e:
            logger.error(f"Erro ao verificar tabela {cls.TABLE_NAME}: {e}")
            return cls.drop_and_recreate_table()

    @classmethod
    def batch_insert(cls, data_list: List[Dict]) -> int:
        """
        Insere múltiplos registros em lote.
        Utiliza apenas os campos definidos em API_FIELDS.
        """
        if not data_list:
            return 0

        # Campos da tabela (sem os metadados, que têm default)
        table_columns = cls.API_FIELDS

        # Preparar lista de tuplas com valores na ordem das colunas
        values_to_insert = []
        valid_records = 0

        for idx, data in enumerate(data_list, 1):
            if not isinstance(data, dict):
                logger.warning(f"Registro {idx} ignorado (não é dict).")
                continue

            row = []
            valid = True
            for col in table_columns:
                raw_val = data.get(col)
                norm_val = cls._normalize_value(raw_val)
                # Se o valor for None, insere NULL no banco (aceito)
                row.append(norm_val)

            # Só adiciona se pelo menos um campo não for None? Não, pode ser tudo None, mas ainda assim insere.
            values_to_insert.append(tuple(row))
            valid_records += 1

        if not values_to_insert:
            logger.warning("Nenhum registro válido para inserir.")
            return 0

        # Construir INSERT com placeholders
        columns_str = ', '.join(f"[{col}]" for col in table_columns)
        placeholders = ', '.join(['?'] * len(table_columns))

        insert_sql = f"""
            INSERT INTO [{cls.TABLE_NAME}] ({columns_str})
            VALUES ({placeholders})
        """

        # Executa em lote (pode-se usar executemany, mas execute_query atual não suporta)
        # Como não temos executemany, faremos um loop com transação manual
        success = 0
        error = 0
        with get_db_connection(db_path=cls.DB_NAME) as conn:
            cursor = conn.cursor()
            for row in values_to_insert:
                try:
                    cursor.execute(insert_sql, row)
                    success += 1
                except Exception as e:
                    logger.error(f"Erro ao inserir registro: {e}")
                    logger.debug(f"Dados: {row}")
                    error += 1
            conn.commit()

        logger.info(f"Batch insert: {success} inseridos, {error} erros, total {len(data_list)}")
        return success

    @classmethod
    def clear_table(cls):
        """Remove todos os registros da tabela."""
        try:
            sql = f"DELETE FROM [{cls.TABLE_NAME}]"
            execute_query(sql, db_path=cls.DB_NAME)
            logger.info(f"Tabela {cls.TABLE_NAME} limpa com sucesso.")
            return True
        except Exception as e:
            logger.error(f"Erro ao limpar tabela {cls.TABLE_NAME}: {e}")
            return False

    @classmethod
    def get_summary(cls) -> Dict:
        """Retorna estatísticas da tabela."""
        try:
            queries = {
                'total_coordenacoes': f"SELECT COUNT(*) FROM [{cls.TABLE_NAME}]",
                'cursos_distintos': f"SELECT COUNT(DISTINCT [curso]) FROM [{cls.TABLE_NAME}]",
                'funcionarios_distintos': f"SELECT COUNT(DISTINCT [num_func]) FROM [{cls.TABLE_NAME}]",
                'tipos_coordenacao': f"SELECT COUNT(DISTINCT [tipo_coord]) FROM [{cls.TABLE_NAME}]",
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