#!/usr/bin/env python3
"""
models/ly_turma.py
Modelo para tabela LY_TURMA usando core.database (SQL Server)
SEM chave primária natural – usa IDENTITY.
"""

import logging
from typing import List, Dict, Any, Optional
from core.database import get_db_connection, execute_query, fetch_all, fetch_one

logger = logging.getLogger(__name__)


class LyTurmaModel:
    TABLE_NAME = "LY_TURMA"
    DB_NAME = "lyceum"

    API_FIELDS = [
        'ano', 'semestre', 'turma', 'disciplina', 'curso', 'curriculo',
        'sit_turma', 'dt_inicio', 'dt_fim', 'dt_criacao', 'dt_ultalt',
        'dt_limite_enturma', 'dt_confirma_dol', 'stamp_atualizacao',
        'num_alunos', 'vagas_calouros', 'vagas_veteranos', 'aulas_previstas',
        'aulas_dadas', 'min_aulas', 'duracao_aula', 'serie', 'nivel',
        'turno', 'horario', 'tem_horario', 'faculdade', 'unidade_responsavel',
        'centro_de_custo', 'disciplina_multipla', 'dependencia', 'especial',
        'turma_integracao', 'em_elaboracao', 'lancamento_historico',
        'permite_choque_horario', 'permite_desfaz_fecham', 'utiliza_indice',
        'utiliza_proc_seletivo', 'exibe_somente_lista_sel', 'interf_ens_dist',
        'nivel_presenca', 'idioma', 'classificacao', 'num_func', 'ult_num_chamada',
        'formula_mf1', 'formula_mf2', 'formula_mf3', 'formula_ca1', 'formula_ca2',
        'formula_ca3', 'obs_formula_mf1', 'obs_formula_mf2', 'obs_formula_mf3',
        'conceito_min1', 'conceito_min2', 'conceito_min3', 'conceito_min_ex',
        'conceito_min_ex2',
        'fl_field01', 'fl_field02', 'fl_field03', 'fl_field04', 'fl_field05',
        'fl_field06', 'fl_field07', 'fl_field08', 'fl_field09', 'fl_field10',
        'fl_field11', 'fl_field12', 'fl_field13', 'fl_field14', 'fl_field15',
        'fl_field16', 'fl_field17', 'fl_field18', 'fl_field19', 'fl_field20'
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
        result = fetch_one(query, (cls.TABLE_NAME,), database_name=cls.DB_NAME)
        return result is not None

    @classmethod
    def create_table(cls):
        if cls._table_exists():
            logger.info(f"Tabela {cls.TABLE_NAME} já existe.")
            return True

        sql = f"""
        CREATE TABLE [{cls.TABLE_NAME}] (
            [id] INT IDENTITY(1,1) PRIMARY KEY,
            [ano] BIGINT NOT NULL,
            [semestre] BIGINT NOT NULL,
            [turma] NVARCHAR(100) NOT NULL,
            [disciplina] NVARCHAR(100) NOT NULL,
            [curso] NVARCHAR(100),
            [curriculo] NVARCHAR(100),
            [sit_turma] NVARCHAR(20),
            [dt_inicio] NVARCHAR(30),
            [dt_fim] NVARCHAR(30),
            [dt_criacao] NVARCHAR(30),
            [dt_ultalt] NVARCHAR(30),
            [dt_limite_enturma] NVARCHAR(30),
            [dt_confirma_dol] NVARCHAR(30),
            [stamp_atualizacao] NVARCHAR(50),
            [num_alunos] BIGINT,
            [vagas_calouros] BIGINT,
            [vagas_veteranos] BIGINT,
            [aulas_previstas] BIGINT,
            [aulas_dadas] BIGINT,
            [min_aulas] BIGINT,
            [duracao_aula] BIGINT,
            [serie] BIGINT,
            [nivel] NVARCHAR(50),
            [turno] NVARCHAR(20),
            [horario] NVARCHAR(255),
            [tem_horario] NVARCHAR(2),
            [faculdade] NVARCHAR(50),
            [unidade_responsavel] NVARCHAR(100),
            [centro_de_custo] NVARCHAR(50),
            [disciplina_multipla] NVARCHAR(2),
            [dependencia] NVARCHAR(20),
            [especial] NVARCHAR(20),
            [turma_integracao] NVARCHAR(20),
            [em_elaboracao] NVARCHAR(20),
            [lancamento_historico] NVARCHAR(20),
            [permite_choque_horario] NVARCHAR(20),
            [permite_desfaz_fecham] NVARCHAR(20),
            [utiliza_indice] NVARCHAR(20),
            [utiliza_proc_seletivo] NVARCHAR(20),
            [exibe_somente_lista_sel] NVARCHAR(20),
            [interf_ens_dist] NVARCHAR(20),
            [nivel_presenca] NVARCHAR(50),
            [idioma] NVARCHAR(50),
            [classificacao] NVARCHAR(50),
            [num_func] BIGINT,
            [ult_num_chamada] BIGINT,
            [formula_mf1] NVARCHAR(MAX),
            [formula_mf2] NVARCHAR(MAX),
            [formula_mf3] NVARCHAR(MAX),
            [formula_ca1] NVARCHAR(MAX),
            [formula_ca2] NVARCHAR(MAX),
            [formula_ca3] NVARCHAR(MAX),
            [obs_formula_mf1] NVARCHAR(MAX),
            [obs_formula_mf2] NVARCHAR(MAX),
            [obs_formula_mf3] NVARCHAR(MAX),
            [conceito_min1] NVARCHAR(50),
            [conceito_min2] NVARCHAR(50),
            [conceito_min3] NVARCHAR(50),
            [conceito_min_ex] NVARCHAR(50),
            [conceito_min_ex2] NVARCHAR(50),
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
            [fl_field11] NVARCHAR(255),
            [fl_field12] NVARCHAR(255),
            [fl_field13] NVARCHAR(255),
            [fl_field14] NVARCHAR(255),
            [fl_field15] NVARCHAR(255),
            [fl_field16] NVARCHAR(255),
            [fl_field17] NVARCHAR(255),
            [fl_field18] NVARCHAR(255),
            [fl_field19] NVARCHAR(255),
            [fl_field20] NVARCHAR(255),
            [data_importacao] DATETIME2 DEFAULT GETDATE(),
            [data_atualizacao] DATETIME2 DEFAULT GETDATE()
        )
        """

        try:
            execute_query(sql, database_name=cls.DB_NAME)

            # Índices
            indexes = [
                f"CREATE INDEX idx_turma_ano_semestre ON [{cls.TABLE_NAME}]([ano], [semestre])",
                f"CREATE INDEX idx_turma_disciplina ON [{cls.TABLE_NAME}]([disciplina])",
                f"CREATE INDEX idx_turma_curso ON [{cls.TABLE_NAME}]([curso])",
                f"CREATE INDEX idx_turma_sit_turma ON [{cls.TABLE_NAME}]([sit_turma])",
                f"CREATE INDEX idx_turma_faculdade ON [{cls.TABLE_NAME}]([faculdade])",
                f"CREATE INDEX idx_turma_ano_sem_dis_tur ON [{cls.TABLE_NAME}]([ano], [semestre], [disciplina], [turma])",
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
        try:
            ano = cls._normalize_value(data.get('ano'))
            semestre = cls._normalize_value(data.get('semestre'))
            turma = cls._normalize_value(data.get('turma'))
            disciplina = cls._normalize_value(data.get('disciplina'))

            if not all([ano, semestre, turma, disciplina]):
                logger.warning(f"Turma sem campos obrigatórios: {data}")
                return False

            columns = ['ano', 'semestre', 'turma', 'disciplina']
            values = [ano, semestre, turma, disciplina]

            for field in cls.API_FIELDS:
                if field not in ['ano', 'semestre', 'turma', 'disciplina']:
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
            logger.error(f"Erro ao inserir turma {data.get('ano')}/{data.get('semestre')}/{data.get('disciplina')}/{data.get('turma')}: {e}")
            return False

    @classmethod
    def batch_insert(cls, data_list: List[Dict]) -> int:
        if not data_list:
            return 0

        success = 0
        errors = 0

        with get_db_connection(database_name=cls.DB_NAME) as conn:
            cursor = conn.cursor()
            for data in data_list:
                try:
                    ano = cls._normalize_value(data.get('ano'))
                    semestre = cls._normalize_value(data.get('semestre'))
                    turma = cls._normalize_value(data.get('turma'))
                    disciplina = cls._normalize_value(data.get('disciplina'))

                    if not all([ano, semestre, turma, disciplina]):
                        logger.warning(f"Turma sem campos obrigatórios: {data}")
                        errors += 1
                        continue

                    columns = ['ano', 'semestre', 'turma', 'disciplina']
                    values = [ano, semestre, turma, disciplina]

                    for field in cls.API_FIELDS:
                        if field not in ['ano', 'semestre', 'turma', 'disciplina']:
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
                    logger.error(f"Erro ao inserir turma {data.get('ano')}/{data.get('semestre')}/{data.get('disciplina')}/{data.get('turma')}: {e}")
                    errors += 1
            conn.commit()

        logger.info(f"Batch insert: {success} sucessos, {errors} erros, total {len(data_list)}")
        return success

    @classmethod
    def get_summary(cls) -> Dict:
        queries = {
            'total_turmas': f"SELECT COUNT(*) FROM [{cls.TABLE_NAME}]",
            'anos_distintos': f"SELECT COUNT(DISTINCT [ano]) FROM [{cls.TABLE_NAME}]",
            'semestres_distintos': f"SELECT COUNT(DISTINCT [semestre]) FROM [{cls.TABLE_NAME}]",
            'disciplinas_distintas': f"SELECT COUNT(DISTINCT [disciplina]) FROM [{cls.TABLE_NAME}]",
            'turmas_distintas': f"SELECT COUNT(DISTINCT [turma]) FROM [{cls.TABLE_NAME}]",
            'turmas_ativas': f"SELECT COUNT(*) FROM [{cls.TABLE_NAME}] WHERE [sit_turma] = 'A'",
            'ultima_atualizacao': f"SELECT MAX([data_atualizacao]) FROM [{cls.TABLE_NAME}]"
        }
        results = {}
        for key, q in queries.items():
            row = fetch_one(q, database_name=cls.DB_NAME)
            results[key] = row[0] if row else 0
        return results

    @classmethod
    def get_all_turmas(cls) -> List[Dict]:
        sql = f"SELECT * FROM [{cls.TABLE_NAME}] ORDER BY [ano] DESC, [semestre] DESC, [disciplina], [turma]"
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
    def get_by_ano_semestre(cls, ano: int, semestre: int) -> List[Dict]:
        sql = f"SELECT * FROM [{cls.TABLE_NAME}] WHERE [ano] = ? AND [semestre] = ? ORDER BY [disciplina], [turma]"
        rows = fetch_all(sql, (ano, semestre), database_name=cls.DB_NAME)
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
    def get_by_disciplina(cls, disciplina_code: str) -> List[Dict]:
        sql = f"SELECT * FROM [{cls.TABLE_NAME}] WHERE [disciplina] = ? ORDER BY [ano] DESC, [semestre] DESC, [turma]"
        rows = fetch_all(sql, (disciplina_code,), database_name=cls.DB_NAME)
        if not rows:
            return []
        col_query = """
            SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = ? ORDER BY ORDINAL_POSITION
        """
        col_rows = fetch_all(col_query, (cls.TABLE_NAME,), database_name=cls.DB_NAME)
        columns = [r[0] for r in col_rows]
        return [dict(zip(columns, row)) for row in rows]