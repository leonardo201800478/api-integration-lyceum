# qstione/importadores/imp_002_disciplina.py
"""
Importador para tabela imp_002_disciplina
Origem: LY_DISCIPLINA + LY_GRADE + LY_CURSO
Filtros: FACULDADES_INCLUIDAS (curso) e AREAS_CONHECIMENTO_INCLUIDAS (disciplina)
Período extraído de LY_GRADE.serie_ideal (não fixo)
"""

from core.database import get_db_connection
from qstione.core.transformacoes import (
    converter_inteiro,
    gerar_codigo_disciplina_curso,
    truncar_texto
)
from qstione.core.validacoes import (
    validar_codigo_disciplina,
    validar_nome_disciplina,
    validar_codigo_curso
)
from qstione.config.filtros import (
    FACULDADES_INCLUIDAS,
    AREAS_CONHECIMENTO_INCLUIDAS
)


class ImportadorDisciplinas:

    def __init__(self):
        pass

    # -------------------------------------------------------------------------
    # Funções auxiliares para tabela destino
    # -------------------------------------------------------------------------
    def _tabela_existe(self, nome_tabela: str) -> bool:
        try:
            with get_db_connection(database_name='qstione') as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 1 FROM INFORMATION_SCHEMA.TABLES
                    WHERE TABLE_NAME = ? AND TABLE_TYPE = 'BASE TABLE'
                """, (nome_tabela,))
                return cursor.fetchone() is not None
        except Exception as e:
            print(f"  ⚠️  Erro ao verificar existência da tabela: {e}")
            return False

    def _indice_existe(self, nome_indice: str) -> bool:
        try:
            with get_db_connection(database_name='qstione') as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM sys.indexes WHERE name = ?", (nome_indice,))
                return cursor.fetchone() is not None
        except Exception as e:
            print(f"  ⚠️  Erro ao verificar índice: {e}")
            return False

    def _criar_tabela(self):
        if self._tabela_existe('imp_002_disciplina'):
            try:
                with get_db_connection(database_name='qstione') as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
                        WHERE TABLE_NAME = 'imp_002_disciplina'
                          AND COLUMN_NAME IN ('data_criacao', 'data_atualizacao')
                    """)
                    colunas = [row[0] for row in cursor.fetchall()]
                    if 'data_criacao' in colunas and 'data_atualizacao' in colunas:
                        print("✅ Tabela imp_002_disciplina já existe com estrutura correta.")
                        return
                    else:
                        print("⚠️  Colunas ausentes. Recriando tabela...")
                        cursor.execute("DROP TABLE imp_002_disciplina")
                        conn.commit()
            except Exception as e:
                print(f"⚠️  Erro ao verificar colunas: {e}. Recriando tabela...")
                with get_db_connection(database_name='qstione') as conn:
                    conn.execute("DROP TABLE IF EXISTS imp_002_disciplina")
                    conn.commit()

        print("🆕 Criando tabela imp_002_disciplina...")
        create_sql = """
            CREATE TABLE imp_002_disciplina (
                codigoDisciplina NVARCHAR(30) NOT NULL,
                nomeDisciplina NVARCHAR(100) NOT NULL,
                codigoCurso NVARCHAR(30) NOT NULL,
                periodo INTEGER NOT NULL,
                data_criacao DATETIME2 DEFAULT GETDATE(),
                data_atualizacao DATETIME2 DEFAULT GETDATE(),
                PRIMARY KEY (codigoDisciplina, codigoCurso, periodo)
            )
        """
        try:
            with get_db_connection(database_name='qstione') as conn:
                conn.execute(create_sql)
                conn.commit()
            print("✅ Tabela criada.")
        except Exception as e:
            print(f"❌ Erro ao criar tabela: {e}")
            return

        indices = [
            ('idx_disciplinas_curso', "CREATE INDEX idx_disciplinas_curso ON imp_002_disciplina(codigoCurso)"),
            ('idx_disciplinas_nome', "CREATE INDEX idx_disciplinas_nome ON imp_002_disciplina(nomeDisciplina)")
        ]
        for nome_idx, sql_idx in indices:
            if not self._indice_existe(nome_idx):
                try:
                    with get_db_connection(database_name='qstione') as conn:
                        conn.execute(sql_idx)
                        conn.commit()
                    print(f"✅ Índice {nome_idx} criado.")
                except Exception as e:
                    print(f"⚠️ Índice {nome_idx} não pôde ser criado: {e}")
            else:
                print(f"✅ Índice {nome_idx} já existe.")

    # -------------------------------------------------------------------------
    # Obter dados do Lyceum (disciplina + cursos + períodos) com filtros
    # -------------------------------------------------------------------------
    def obter_dados_lyceum(self):
        """Retorna todas as combinações disciplina/curso que atendem aos filtros."""
        faculdades_placeholders = ','.join(['?'] * len(FACULDADES_INCLUIDAS))
        areas_placeholders = ','.join(['?'] * len(AREAS_CONHECIMENTO_INCLUIDAS))

        query = f"""
            SELECT DISTINCT
                d.disciplina,
                d.nome_compl,
                g.curso,
                c.nome as nome_curso,
                g.serie_ideal
            FROM LY_GRADE g
            INNER JOIN LY_DISCIPLINA d ON d.disciplina = g.disciplina
            INNER JOIN LY_CURSO c ON c.curso = g.curso
            WHERE c.ativo = 'S'
              AND c.faculdade IN ({faculdades_placeholders})
              AND (d.area_conhecimento IN ({areas_placeholders})
                   OR d.area_conhecimento IS NULL
                   OR d.area_conhecimento = '')
            ORDER BY d.disciplina, g.curso
        """
        params = (*FACULDADES_INCLUIDAS, *AREAS_CONHECIMENTO_INCLUIDAS)
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()

    # -------------------------------------------------------------------------
    # Transformar dados (agregando por disciplina)
    # -------------------------------------------------------------------------
    def transformar_dados(self, dados_lyceum):
        """
        Estrutura: {disciplina: {"nome_compl": nome, "cursos": {curso: {"nome_curso": nome, "periodos": set()}}}
        """
        disciplinas = {}
        for disciplina, nome_compl, curso, nome_curso, serie_ideal in dados_lyceum:
            if disciplina not in disciplinas:
                disciplinas[disciplina] = {
                    "nome_compl": nome_compl,
                    "cursos": {}
                }
            if curso not in disciplinas[disciplina]["cursos"]:
                disciplinas[disciplina]["cursos"][curso] = {
                    "nome_curso": nome_curso,
                    "periodos": set()
                }
            disciplinas[disciplina]["cursos"][curso]["periodos"].add(serie_ideal)

        dados_transformados = []
        cont_periodo_zero = 0

        for disciplina, info in disciplinas.items():
            nome_compl = info["nome_compl"]
            cursos = info["cursos"]

            # Validar código da disciplina
            if not validar_codigo_disciplina(disciplina):
                print(f"  ⚠️  Código da disciplina inválido: {disciplina}")
                continue

            # Validar/normalizar nome da disciplina
            nome_disciplina = validar_nome_disciplina(nome_compl)
            if nome_disciplina is None:
                nome_disciplina = truncar_texto(nome_compl, 100)
                if not nome_disciplina:
                    print(f"  ⚠️  Nome da disciplina inválido após truncagem: {nome_compl}")
                    continue
                print(f"  ⚠️  Nome da disciplina truncado para 100 caracteres: {nome_disciplina}")

            # Determinar se é compartilhada (mais de um curso)
            if len(cursos) > 1:
                codigo_curso = '999'
                nome_curso = 'TURMAS COMPARTILHADAS'
                # Período = menor valor entre todos os períodos de todos os cursos
                todos_periodos = set()
                for c in cursos.values():
                    todos_periodos.update(c["periodos"])
                periodos_int = [converter_inteiro(p) for p in todos_periodos if p is not None]
                if not periodos_int:
                    print(f"  ⚠️  Nenhum período válido para disciplina {disciplina}")
                    continue
                periodo = min(periodos_int)
            else:
                codigo_curso, curso_info = next(iter(cursos.items()))
                nome_curso = curso_info["nome_curso"]
                periodo_raw = next(iter(curso_info["periodos"]))
                periodo = converter_inteiro(periodo_raw)

            # Converter período 0 -> 1
            if periodo == 0:
                periodo = 1
                cont_periodo_zero += 1
                print(f"  ⚠️  Período 0 convertido para 1 na disciplina {disciplina} (curso {codigo_curso})")

            if periodo is None or periodo < 1:
                print(f"  ⚠️  Período inválido para disciplina {disciplina}: {periodo}")
                continue

            if not validar_codigo_curso(codigo_curso):
                print(f"  ⚠️  Código do curso inválido: {codigo_curso} para disciplina {disciplina}")
                continue

            codigo_disciplina_final = gerar_codigo_disciplina_curso(
                disciplina,
                nome_curso,
                codigo_curso
            )

            dados_transformados.append({
                'codigoDisciplina': codigo_disciplina_final,
                'nomeDisciplina': nome_disciplina,
                'codigoCurso': str(codigo_curso)[:30],
                'periodo': periodo
            })

        if cont_periodo_zero > 0:
            print(f"  ⚠️  Total de disciplinas com período 0 convertidas para 1: {cont_periodo_zero}")
        return dados_transformados

    # -------------------------------------------------------------------------
    # Importar para Qstione (MERGE)
    # -------------------------------------------------------------------------
    def importar_para_qstione(self, dados_transformados):
        self._criar_tabela()

        merge_sql = """
            MERGE INTO imp_002_disciplina AS target
            USING (VALUES (?, ?, ?, ?)) AS source (codigoDisciplina, nomeDisciplina, codigoCurso, periodo)
            ON target.codigoDisciplina = source.codigoDisciplina
               AND target.codigoCurso = source.codigoCurso
               AND target.periodo = source.periodo
            WHEN MATCHED THEN
                UPDATE SET
                    nomeDisciplina = source.nomeDisciplina,
                    data_atualizacao = GETDATE()
            WHEN NOT MATCHED THEN
                INSERT (codigoDisciplina, nomeDisciplina, codigoCurso, periodo, data_criacao, data_atualizacao)
                VALUES (source.codigoDisciplina, source.nomeDisciplina, source.codigoCurso, source.periodo, GETDATE(), GETDATE());
        """

        total_inseridos = 0
        total_atualizados = 0
        total_erros = 0

        with get_db_connection(database_name='qstione') as conn:
            cursor = conn.cursor()
            for reg in dados_transformados:
                try:
                    cursor.execute("""
                        SELECT 1 FROM imp_002_disciplina
                        WHERE codigoDisciplina = ? AND codigoCurso = ? AND periodo = ?
                    """, (reg['codigoDisciplina'], reg['codigoCurso'], reg['periodo']))
                    existe = cursor.fetchone()

                    cursor.execute(merge_sql, (
                        reg['codigoDisciplina'],
                        reg['nomeDisciplina'],
                        reg['codigoCurso'],
                        reg['periodo']
                    ))

                    if existe:
                        total_atualizados += 1
                    else:
                        total_inseridos += 1

                except Exception as e:
                    total_erros += 1
                    print(f"  ✗  Erro ao importar {reg['codigoDisciplina']} - {reg['codigoCurso']} - {reg['periodo']}: {e}")

            conn.commit()

        return {
            'total_inseridos': total_inseridos,
            'total_atualizados': total_atualizados,
            'total_erros': total_erros,
            'total_processados': len(dados_transformados)
        }

    # -------------------------------------------------------------------------
    # Execução principal
    # -------------------------------------------------------------------------
    def executar_importacao(self):
        print("=" * 70)
        print("IMPORTAÇÃO: imp_002_disciplina (com filtros e período variável)")
        print("=" * 70)
        print(f"FACULDADES_INCLUIDAS: {FACULDADES_INCLUIDAS}")
        print(f"AREAS_CONHECIMENTO_INCLUIDAS: {AREAS_CONHECIMENTO_INCLUIDAS}")

        # 1. Obter dados do Lyceum
        dados_lyceum = self.obter_dados_lyceum()
        print(f"📊 Combinações disciplina/curso encontradas: {len(dados_lyceum)}")

        # 2. Transformar dados
        print("🔄 Transformando dados...")
        dados_transformados = self.transformar_dados(dados_lyceum)
        print(f"✅ Registros únicos para importação: {len(dados_transformados)}")

        # 3. Importar para Qstione
        print("💾 Importando para banco Qstione...")
        resultado = self.importar_para_qstione(dados_transformados)

        print(f"\n📈 RESULTADO DA IMPORTAÇÃO:")
        print(f"  ✓ Inseridos: {resultado['total_inseridos']}")
        print(f"  ↻ Atualizados: {resultado['total_atualizados']}")
        print(f"  ✗ Erros: {resultado['total_erros']}")
        print(f"  📋 Total processados: {resultado['total_processados']}")

        return dados_transformados


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    importador = ImportadorDisciplinas()
    importador.executar_importacao()