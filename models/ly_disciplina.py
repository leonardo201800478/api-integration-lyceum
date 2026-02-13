#!/usr/bin/env python3
"""
Modelo para tabela LY_DISCIPLINA usando core.database (SQL Server)
SEM chave primária natural – usa IDENTITY.
"""

import logging
from typing import List, Dict, Any, Optional
from core.database import get_db_connection, execute_query, fetch_all, fetch_one

logger = logging.getLogger(__name__)


class LyDisciplinaModel:
    """Modelo para tabela LY_DISCIPLINA (SQL Server) sem chave primária natural."""

    TABLE_NAME = "LY_DISCIPLINA"
    DB_NAME = "lyceum.db"  # nome do banco no SQL Server

    API_FIELDS = [
        'disciplina', 'nome', 'nome_compl', 'nome_fantasia', 'tipo',
        'ativo', 'servico', 'faculdade', 'depto', 'componente',
        'area_conhecimento', 'creditos', 'horas_aula', 'horas_lab',
        'horas_ativ', 'horas_estagio', 'aulas_semanais',
        'aulas_sem_aula', 'aulas_sem_lab', 'aulas_sem_ativ',
        'estagio', 'tipo_estagio', 'multipla', 'categoria_enturmacao',
        'tem_nota', 'tipo_nota', 'tem_freq', 'tem_aval_descritiva',
        'aval_competencia', 'conceito_min1', 'conceito_min2',
        'conceito_min3', 'conceito_min_ex', 'conceito_min_ex2',
        'nota_max', 'nota_max_media', 'n_casas_dec', 'n_casas_dec_media',
        'trunca_media', 'grupo_nota', 'grupo_media', 'pim',
        'formula_mf1', 'formula_mf2', 'formula_mf3', 'formula_ca1',
        'formula_ca2', 'formula_ca3', 'formula_equiv', 'formula_prereq',
        'obs_formula_mf1', 'obs_formula_mf2', 'obs_formula_mf3',
        'perc_presmin', 'falta_diaria', 'prioriza_freq',
        'permite_manter_horario', 'verifica_horario', 'copia_nota_subturma',
        'prazo_divulgacao', 'prazo_revisao', 'campo01',
        'stamp_atualizacao',
        # Campos flag
        'fl_field01', 'fl_field02', 'fl_field03', 'fl_field04', 'fl_field05',
        'fl_field06', 'fl_field07', 'fl_field08', 'fl_field09', 'fl_field10'
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
            [disciplina] NVARCHAR(100) NOT NULL,
            [nome] NVARCHAR(500),
            [nome_compl] NVARCHAR(MAX),
            [nome_fantasia] NVARCHAR(500),
            [tipo] NVARCHAR(50),
            [ativo] CHAR(1),
            [servico] NVARCHAR(50),
            [faculdade] NVARCHAR(50),
            [depto] NVARCHAR(50),
            [componente] NVARCHAR(50),
            [area_conhecimento] NVARCHAR(255),
            [creditos] INT,
            [horas_aula] INT,
            [horas_lab] INT,
            [horas_ativ] INT,
            [horas_estagio] INT,
            [aulas_semanais] INT,
            [aulas_sem_aula] INT,
            [aulas_sem_lab] INT,
            [aulas_sem_ativ] INT,
            [estagio] CHAR(1),
            [tipo_estagio] NVARCHAR(50),
            [multipla] CHAR(1),
            [categoria_enturmacao] NVARCHAR(50),
            [tem_nota] CHAR(1),
            [tipo_nota] NVARCHAR(50),
            [tem_freq] CHAR(1),
            [tem_aval_descritiva] CHAR(1),
            [aval_competencia] CHAR(1),
            [conceito_min1] NVARCHAR(50),
            [conceito_min2] NVARCHAR(50),
            [conceito_min3] NVARCHAR(50),
            [conceito_min_ex] NVARCHAR(50),
            [conceito_min_ex2] NVARCHAR(50),
            [nota_max] DECIMAL(10,2),
            [nota_max_media] DECIMAL(10,2),
            [n_casas_dec] INT,
            [n_casas_dec_media] INT,
            [trunca_media] CHAR(1),
            [grupo_nota] NVARCHAR(50),
            [grupo_media] NVARCHAR(50),
            [pim] CHAR(1),
            [formula_mf1] NVARCHAR(MAX),
            [formula_mf2] NVARCHAR(MAX),
            [formula_mf3] NVARCHAR(MAX),
            [formula_ca1] NVARCHAR(MAX),
            [formula_ca2] NVARCHAR(MAX),
            [formula_ca3] NVARCHAR(MAX),
            [formula_equiv] NVARCHAR(MAX),
            [formula_prereq] NVARCHAR(MAX),
            [obs_formula_mf1] NVARCHAR(MAX),
            [obs_formula_mf2] NVARCHAR(MAX),
            [obs_formula_mf3] NVARCHAR(MAX),
            [perc_presmin] FLOAT,
            [falta_diaria] CHAR(1),
            [prioriza_freq] CHAR(1),
            [permite_manter_horario] CHAR(1),
            [verifica_horario] CHAR(1),
            [copia_nota_subturma] CHAR(1),
            [prazo_divulgacao] INT,
            [prazo_revisao] INT,
            [campo01] NVARCHAR(255),
            [stamp_atualizacao] NVARCHAR(50),
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
                f"CREATE INDEX idx_disciplina_codigo ON [{cls.TABLE_NAME}]([disciplina])",
                f"CREATE INDEX idx_disciplina_nome ON [{cls.TABLE_NAME}]([nome])",
                f"CREATE INDEX idx_disciplina_ativo ON [{cls.TABLE_NAME}]([ativo])",
                f"CREATE INDEX idx_disciplina_faculdade ON [{cls.TABLE_NAME}]([faculdade])",
                f"CREATE INDEX idx_disciplina_depto ON [{cls.TABLE_NAME}]([depto])",
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
        try:
            disciplina_id = cls._normalize_value(data.get('disciplina'))
            if not disciplina_id:
                logger.warning(f"Disciplina sem código: {data}")
                return False

            columns = ['disciplina']
            values = [disciplina_id]
            for field in cls.API_FIELDS:
                if field != 'disciplina':
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
            logger.error(f"Erro ao inserir disciplina {data.get('disciplina')}: {e}")
            return False

    @classmethod
    def batch_insert(cls, data_list: List[Dict]) -> int:
        if not data_list:
            return 0
        success = 0
        errors = 0
        with get_db_connection(db_path=cls.DB_NAME) as conn:
            cursor = conn.cursor()
            for data in data_list:
                try:
                    disciplina_id = cls._normalize_value(data.get('disciplina'))
                    if not disciplina_id:
                        errors += 1
                        continue
                    columns = ['disciplina']
                    values = [disciplina_id]
                    for field in cls.API_FIELDS:
                        if field != 'disciplina':
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
                    logger.error(f"Erro ao inserir disciplina {data.get('disciplina')}: {e}")
                    errors += 1
            conn.commit()
        logger.info(f"Batch insert: {success} sucessos, {errors} erros, total {len(data_list)}")
        return success

    @classmethod
    def get_summary(cls) -> Dict:
        queries = {
            'total_disciplinas': f"SELECT COUNT(*) FROM [{cls.TABLE_NAME}]",
            'disciplinas_distintas': f"SELECT COUNT(DISTINCT [disciplina]) FROM [{cls.TABLE_NAME}]",
            'disciplinas_ativas': f"SELECT COUNT(*) FROM [{cls.TABLE_NAME}] WHERE [ativo] = 'S'",
            'faculdades_distintas': f"SELECT COUNT(DISTINCT [faculdade]) FROM [{cls.TABLE_NAME}] WHERE [faculdade] IS NOT NULL",
            'departamentos_distintos': f"SELECT COUNT(DISTINCT [depto]) FROM [{cls.TABLE_NAME}] WHERE [depto] IS NOT NULL",
            'ultima_atualizacao': f"SELECT MAX([data_atualizacao]) FROM [{cls.TABLE_NAME}]"
        }
        results = {}
        for key, q in queries.items():
            row = fetch_one(q, db_path=cls.DB_NAME)
            results[key] = row[0] if row else 0
        return results

    @classmethod
    def get_all_disciplinas(cls) -> List[Dict]:
        sql = f"SELECT * FROM [{cls.TABLE_NAME}] ORDER BY [disciplina]"
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
    def get_by_disciplina(cls, disciplina_code: str) -> List[Dict]:
        sql = f"SELECT * FROM [{cls.TABLE_NAME}] WHERE [disciplina] = ? ORDER BY [id]"
        rows = fetch_all(sql, (disciplina_code,), db_path=cls.DB_NAME)
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
    def get_disciplinas_ativas(cls) -> List[Dict]:
        sql = f"SELECT * FROM [{cls.TABLE_NAME}] WHERE [ativo] = 'S' ORDER BY [disciplina]"
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