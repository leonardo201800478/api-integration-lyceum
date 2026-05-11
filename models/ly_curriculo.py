"""
models/ly_curriculo.py
Modelo para tabela LY_CURRICULO usando core.database (SQL Server)
ID gerado de forma determinística via concatenação: curso + curriculo

MIGRAÇÃO AUTOMÁTICA:
  Se a tabela existir com [id] INT/IDENTITY, o método _migrate_id_column()
  remove a constraint de PK antiga, dropa a coluna id, recria como
  NVARCHAR(512) NOT NULL e adiciona nova PK — tudo sem recriar a tabela.
"""

import logging
from typing import List, Dict, Any, Optional
from core.database import get_db_connection, execute_query, fetch_all, fetch_one

logger = logging.getLogger(__name__)


class LyCurriculoModel:
    """Modelo para tabela LY_CURRICULO (SQL Server) com ID composto curso+curriculo."""

    TABLE_NAME = "LY_CURRICULO"
    DB_NAME = "lyceum"

    API_FIELDS = [
        'curriculo', 'curso', 'turno', 'prazo_ideal', 'prazo_max',
        'ano_ini', 'sem_ini', 'regime', 'aulas_previstas', 'creditos',
        'situacao', 'stamp_atualizacao', 'dt_homolog', 'dt_extincao',
        'modalidade', 'servico', 'valor', 'codigo_secundario', 'nome_secundario',
        'classificacao', 'habilinep', 'pesquisa', 'tese_dissertacao',
        'tipo_prazo_concl', 'tipo_prazo_orien', 'prazo_conc_prev',
        'prazo_desig_orien', 'prazo_max_adap', 'unid_prazo_max_adap',
        'retem_serie', 'serie_max_orient', 'ativ_compl_ch', 'ativ_compl_creditos',
        'perc_ch_pres', 'perc_ch_semi_pres', 'perc_ch_nao_pres',
        'ver_ch_integracao', 'ver_cred_integracao', 'max_alunos', 'min_alunos',
        'num_disc_atras_prog', 'tranc_max', 'tranc_cons_max', 'tranc_max_discip',
        'canc_max_discip', 'atlz_max_discip', 'n_max_dias_tranc',
        'tranc_interv_data', 'tranca_primeiro_periodo', 'excecao_trancamento',
        'permite_cancelamento', 'credmin_matr', 'credmin_foragrade',
        'credmax_foragrade', 'ratear_mens', 'ratear_desc',
        'matr_obrig_todas_discip_serie', 'restringe_unid_fis', 'obs',
        'emp_cnpj', 'emp_endereco', 'emp_end_num', 'emp_end_compl',
        'emp_bairro', 'emp_cep', 'emp_municipio', 'emp_fone', 'emp_contato',
        'indice', 'colecao_livros', 'fl_field01', 'fl_field02', 'fl_field03',
        'fl_field04', 'fl_field05', 'fl_field06', 'fl_field07', 'fl_field08',
        'fl_field09', 'fl_field10'
    ]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @classmethod
    def _generate_id(cls, curso: Any, curriculo: Any) -> str:
        """Gera ID determinístico: '<curso>_<curriculo>'  ex: '006_20262'"""
        return f"{str(curso).strip()}_{str(curriculo).strip()}"

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

    # ------------------------------------------------------------------
    # Verificações de estrutura
    # ------------------------------------------------------------------

    @classmethod
    def _table_exists(cls) -> bool:
        query = """
            SELECT 1 FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_NAME = ? AND TABLE_TYPE = 'BASE TABLE'
        """
        result = fetch_one(query, (cls.TABLE_NAME,), database_name=cls.DB_NAME)
        return result is not None

    @classmethod
    def _get_id_column_type(cls) -> Optional[str]:
        """Retorna o DATA_TYPE atual da coluna [id], ou None se não existir."""
        query = """
            SELECT DATA_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = ? AND COLUMN_NAME = 'id'
        """
        row = fetch_one(query, (cls.TABLE_NAME,), database_name=cls.DB_NAME)
        return row[0].lower() if row else None

    @classmethod
    def _get_pk_constraint_name(cls) -> Optional[str]:
        """Retorna o nome da constraint de PK da tabela, se existir."""
        query = """
            SELECT kc.name
            FROM sys.key_constraints kc
            JOIN sys.tables t ON t.object_id = kc.parent_object_id
            WHERE kc.type = 'PK' AND t.name = ?
        """
        row = fetch_one(query, (cls.TABLE_NAME,), database_name=cls.DB_NAME)
        return row[0] if row else None

    # ------------------------------------------------------------------
    # Migração automática  INT → NVARCHAR
    # ------------------------------------------------------------------

    @classmethod
    def _migrate_id_column(cls):
        """
        Migra [id] de INT IDENTITY para NVARCHAR(512) NOT NULL.

        Passos:
          1. Remove PK existente
          2. Dropa coluna [id] antiga
          3. Adiciona nova coluna [id] NVARCHAR(512) NOT NULL (com default '' temporário)
          4. Remove o default temporário via DECLARE dinâmico
          5. Recria a PK
        """
        logger.info(f"Iniciando migração da coluna [id] em {cls.TABLE_NAME} ...")

        pk_name = cls._get_pk_constraint_name()

        steps = []

        # 1. Drop PK
        if pk_name:
            steps.append(f"ALTER TABLE [{cls.TABLE_NAME}] DROP CONSTRAINT [{pk_name}]")

        # 2. Drop coluna id antiga (IDENTITY não pode ser alterada, precisa dropar)
        steps.append(f"ALTER TABLE [{cls.TABLE_NAME}] DROP COLUMN [id]")

        # 3. Nova coluna com default temporário (exigido pelo NOT NULL em tabela existente)
        steps.append(
            f"ALTER TABLE [{cls.TABLE_NAME}] ADD [id] NVARCHAR(512) NOT NULL DEFAULT ''"
        )

        # 4. Remove o default temporário (nome gerado automaticamente pelo SQL Server)
        steps.append(f"""
            DECLARE @df NVARCHAR(256);
            SELECT @df = d.name
            FROM sys.default_constraints d
            JOIN sys.columns c ON c.default_object_id = d.object_id
            JOIN sys.tables  t ON t.object_id = c.object_id
            WHERE t.name = '{cls.TABLE_NAME}' AND c.name = 'id';
            IF @df IS NOT NULL
                EXEC('ALTER TABLE [{cls.TABLE_NAME}] DROP CONSTRAINT [' + @df + ']');
        """)

        # 5. Recria PK
        steps.append(
            f"ALTER TABLE [{cls.TABLE_NAME}] "
            f"ADD CONSTRAINT [PK_LY_CURRICULO] PRIMARY KEY ([id])"
        )

        try:
            for sql in steps:
                execute_query(sql.strip(), database_name=cls.DB_NAME)
            logger.info("Migração da coluna [id] concluída com sucesso.")
        except Exception as e:
            logger.error(f"Erro durante migração da coluna [id]: {e}")
            raise

    # ------------------------------------------------------------------
    # DDL
    # ------------------------------------------------------------------

    @classmethod
    def create_table(cls):
        """
        Cria a tabela se não existir.
        Se já existir com [id] INT (legado IDENTITY), executa migração automática.
        """
        if cls._table_exists():
            id_type = cls._get_id_column_type()
            if id_type == 'int':
                logger.warning(
                    f"Tabela {cls.TABLE_NAME} existe com [id] INT — executando migração automática."
                )
                cls._migrate_id_column()
            else:
                logger.info(f"Tabela {cls.TABLE_NAME} já existe com estrutura correta.")
            return True

        sql = f"""
        CREATE TABLE [{cls.TABLE_NAME}] (
            [id] NVARCHAR(512) NOT NULL,
            [curriculo] NVARCHAR(255) NOT NULL,
            [curso] NVARCHAR(255) NOT NULL,
            [turno] NVARCHAR(50),
            [prazo_ideal] INT,
            [prazo_max] INT,
            [ano_ini] INT,
            [sem_ini] INT,
            [regime] NVARCHAR(50),
            [aulas_previstas] INT,
            [creditos] INT,
            [situacao] NVARCHAR(50),
            [stamp_atualizacao] NVARCHAR(50),
            [dt_homolog] NVARCHAR(20),
            [dt_extincao] NVARCHAR(20),
            [modalidade] NVARCHAR(255),
            [servico] NVARCHAR(50),
            [valor] NVARCHAR(50),
            [codigo_secundario] NVARCHAR(100),
            [nome_secundario] NVARCHAR(255),
            [classificacao] NVARCHAR(50),
            [habilinep] NVARCHAR(50),
            [pesquisa] NVARCHAR(50),
            [tese_dissertacao] NVARCHAR(50),
            [tipo_prazo_concl] NVARCHAR(50),
            [tipo_prazo_orien] NVARCHAR(50),
            [prazo_conc_prev] INT,
            [prazo_desig_orien] INT,
            [prazo_max_adap] INT,
            [unid_prazo_max_adap] NVARCHAR(50),
            [retem_serie] INT,
            [serie_max_orient] INT,
            [ativ_compl_ch] INT,
            [ativ_compl_creditos] INT,
            [perc_ch_pres] FLOAT,
            [perc_ch_semi_pres] FLOAT,
            [perc_ch_nao_pres] FLOAT,
            [ver_ch_integracao] NVARCHAR(50),
            [ver_cred_integracao] NVARCHAR(50),
            [max_alunos] INT,
            [min_alunos] INT,
            [num_disc_atras_prog] INT,
            [tranc_max] INT,
            [tranc_cons_max] INT,
            [tranc_max_discip] INT,
            [canc_max_discip] INT,
            [atlz_max_discip] INT,
            [n_max_dias_tranc] INT,
            [tranc_interv_data] NVARCHAR(20),
            [tranca_primeiro_periodo] NVARCHAR(10),
            [excecao_trancamento] NVARCHAR(10),
            [permite_cancelamento] NVARCHAR(10),
            [credmin_matr] INT,
            [credmin_foragrade] INT,
            [credmax_foragrade] INT,
            [ratear_mens] NVARCHAR(10),
            [ratear_desc] NVARCHAR(10),
            [matr_obrig_todas_discip_serie] NVARCHAR(10),
            [restringe_unid_fis] NVARCHAR(10),
            [obs] NVARCHAR(MAX),
            [emp_cnpj] NVARCHAR(20),
            [emp_endereco] NVARCHAR(255),
            [emp_end_num] NVARCHAR(20),
            [emp_end_compl] NVARCHAR(100),
            [emp_bairro] NVARCHAR(100),
            [emp_cep] NVARCHAR(10),
            [emp_municipio] NVARCHAR(100),
            [emp_fone] NVARCHAR(50),
            [emp_contato] NVARCHAR(100),
            [indice] NVARCHAR(50),
            [colecao_livros] NVARCHAR(255),
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
            [data_atualizacao] DATETIME2 DEFAULT GETDATE(),
            CONSTRAINT [PK_LY_CURRICULO] PRIMARY KEY ([id])
        )
        """

        try:
            execute_query(sql, database_name=cls.DB_NAME)

            indexes = [
                f"CREATE INDEX idx_curriculo_curso ON [{cls.TABLE_NAME}]([curriculo], [curso])",
                f"CREATE INDEX idx_curriculo_situacao ON [{cls.TABLE_NAME}]([situacao])",
                f"CREATE INDEX idx_curriculo_turno ON [{cls.TABLE_NAME}]([turno])",
                f"CREATE INDEX idx_curriculo_ano_ini ON [{cls.TABLE_NAME}]([ano_ini])",
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
            execute_query(f"DELETE FROM [{cls.TABLE_NAME}]", database_name=cls.DB_NAME)
            logger.info(f"Tabela {cls.TABLE_NAME} limpa.")
            return True
        except Exception as e:
            logger.error(f"Erro ao limpar tabela {cls.TABLE_NAME}: {e}")
            return False

    # ------------------------------------------------------------------
    # DML
    # ------------------------------------------------------------------

    @classmethod
    def _build_columns_and_values(cls, data: Dict):
        """
        Monta listas de colunas e valores a partir de um dict de dados da API.
        Retorna (generated_id, columns, values) ou (None, None, None) se inválido.
        """
        curriculo_id = cls._normalize_value(data.get('curriculo'))
        curso_id = cls._normalize_value(data.get('curso'))

        if not curriculo_id or not curso_id:
            return None, None, None

        generated_id = cls._generate_id(curso_id, curriculo_id)

        columns = ['id', 'curriculo', 'curso']
        values = [generated_id, curriculo_id, curso_id]

        for field in cls.API_FIELDS:
            if field not in ('curriculo', 'curso'):
                value = cls._normalize_value(data.get(field))
                if value is not None:
                    columns.append(field)
                    values.append(value)

        return generated_id, columns, values

    @classmethod
    def insert(cls, data: Dict) -> bool:
        """Insere um currículo. Ignora silenciosamente se o id já existir."""
        try:
            generated_id, columns, values = cls._build_columns_and_values(data)

            if generated_id is None:
                logger.warning(f"Currículo sem código ou curso: {data}")
                return False

            columns_str = ', '.join([f"[{c}]" for c in columns])
            placeholders = ', '.join(['?' for _ in values])

            sql = f"""
                IF NOT EXISTS (SELECT 1 FROM [{cls.TABLE_NAME}] WHERE [id] = ?)
                INSERT INTO [{cls.TABLE_NAME}] ({columns_str}, [data_atualizacao])
                VALUES ({placeholders}, GETDATE())
            """

            execute_query(sql, (generated_id, *values), database_name=cls.DB_NAME)
            return True

        except Exception as e:
            logger.error(f"Erro ao inserir currículo {data.get('curriculo')}: {e}")
            return False

    @classmethod
    def batch_insert(cls, data_list: List[Dict]) -> int:
        """Insere múltiplos currículos em lote. Ignora ids já existentes."""
        if not data_list:
            return 0

        success_count = 0
        error_count = 0

        with get_db_connection(database_name=cls.DB_NAME) as conn:
            cursor = conn.cursor()

            for data in data_list:
                try:
                    generated_id, columns, values = cls._build_columns_and_values(data)

                    if generated_id is None:
                        logger.warning(f"Currículo sem código ou curso: {data}")
                        error_count += 1
                        continue

                    columns_str = ', '.join([f"[{c}]" for c in columns])
                    placeholders = ', '.join(['?' for _ in values])

                    sql = f"""
                        IF NOT EXISTS (SELECT 1 FROM [{cls.TABLE_NAME}] WHERE [id] = ?)
                        INSERT INTO [{cls.TABLE_NAME}] ({columns_str}, [data_atualizacao])
                        VALUES ({placeholders}, GETDATE())
                    """

                    cursor.execute(sql, (generated_id, *values))
                    success_count += 1

                except Exception as e:
                    logger.error(f"Erro ao inserir currículo {data.get('curriculo')}: {e}")
                    error_count += 1
                    continue

            conn.commit()

        logger.info(
            f"Batch insert: {success_count} sucessos, {error_count} erros, total {len(data_list)}"
        )
        return success_count

    # ------------------------------------------------------------------
    # Consultas
    # ------------------------------------------------------------------

    @classmethod
    def get_summary(cls) -> Dict:
        """Retorna estatísticas da tabela."""
        try:
            queries = {
                'total_curriculos':     f"SELECT COUNT(*) FROM [{cls.TABLE_NAME}]",
                'cursos_distintos':     f"SELECT COUNT(DISTINCT [curso]) FROM [{cls.TABLE_NAME}]",
                'curriculos_distintos': f"SELECT COUNT(DISTINCT [curriculo]) FROM [{cls.TABLE_NAME}]",
                'situacoes_distintas':  f"SELECT COUNT(DISTINCT [situacao]) FROM [{cls.TABLE_NAME}] WHERE [situacao] IS NOT NULL",
                'ultima_atualizacao':   f"SELECT MAX([data_atualizacao]) FROM [{cls.TABLE_NAME}]",
            }

            results = {}
            for key, query in queries.items():
                row = fetch_one(query, database_name=cls.DB_NAME)
                results[key] = row[0] if row else 0

            return results

        except Exception as e:
            logger.error(f"Erro ao obter resumo: {e}")
            return {}