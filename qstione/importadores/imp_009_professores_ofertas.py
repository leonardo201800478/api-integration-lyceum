"""
Importador para tabela imp_009_professores_ofertas
Adaptado para SQL Server usando core.database

Exporta a relação entre ofertas de disciplinas (turmas) e professores (e-mail).
Gera o código da oferta da mesma forma que o importador imp_005_ofertas.

Campos:
    - codigoOferta:   CHAR(30) – código da oferta (disciplina_turma_anoSemestre)
    - emailProfessor: CHAR(100) – e-mail do docente (minúsculas)

Filtros aplicados (centralizados em qstione.config.filtros):
    - LY_TURMA: ano = ANO_VIGENTE, semestre IN (PERIODOS_VIGENTES), sit_turma = 'aberta'
    - LY_DISCIPLINA: faculdade IN (FACULDADES_INCLUIDAS)
    - Áreas de conhecimento: as definidas em AREAS_CONHECIMENTO_INCLUIDAS (inclui NULL e vazio)
    - LY_DOCENTE: ativo = 'S' e e-mail válido
"""

from core.database import get_db_connection
from qstione.core.transformacoes import (
    gerar_codigo_oferta,
    converter_minusculas,
    truncar_texto
)
from qstione.core.validacoes import validar_email
from qstione.config.filtros import (
    ANO_VIGENTE,
    PERIODOS_VIGENTES,
    FACULDADES_INCLUIDAS,
    AREAS_CONHECIMENTO_INCLUIDAS
)


class ImportadorProfessoresOfertas:

    def __init__(self):
        pass

    # -------------------------------------------------------------------------
    # Funções auxiliares para verificação de existência de tabelas/índices
    # -------------------------------------------------------------------------
    def _tabela_existe(self, nome_tabela: str) -> bool:
        try:
            with get_db_connection(db_path='qstione.db') as conn:
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
            with get_db_connection(db_path='qstione.db') as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM sys.indexes WHERE name = ?", (nome_indice,))
                return cursor.fetchone() is not None
        except Exception as e:
            print(f"  ⚠️  Erro ao verificar índice: {e}")
            return False

    def _criar_tabela(self):
        if self._tabela_existe('imp_009_professores_ofertas'):
            # Verifica se as colunas obrigatórias existem
            try:
                with get_db_connection(db_path='qstione.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
                        WHERE TABLE_NAME = 'imp_009_professores_ofertas'
                          AND COLUMN_NAME IN ('data_criacao', 'data_atualizacao')
                    """)
                    colunas = [row[0] for row in cursor.fetchall()]
                    if 'data_criacao' in colunas and 'data_atualizacao' in colunas:
                        print("✅ Tabela imp_009_professores_ofertas já existe com estrutura correta.")
                        return
                    else:
                        print("⚠️  Colunas ausentes. Recriando tabela...")
                        cursor.execute("DROP TABLE imp_009_professores_ofertas")
                        conn.commit()
            except Exception as e:
                print(f"⚠️  Erro ao verificar colunas: {e}. Recriando tabela...")
                with get_db_connection(db_path='qstione.db') as conn:
                    conn.execute("DROP TABLE IF EXISTS imp_009_professores_ofertas")
                    conn.commit()

        print("🆕 Criando tabela imp_009_professores_ofertas...")
        create_sql = """
            CREATE TABLE imp_009_professores_ofertas (
                codigoOferta NVARCHAR(30) NOT NULL,
                emailProfessor NVARCHAR(100) NOT NULL,
                data_criacao DATETIME2 DEFAULT GETDATE(),
                data_atualizacao DATETIME2 DEFAULT GETDATE(),
                PRIMARY KEY (codigoOferta, emailProfessor)
            )
        """
        try:
            with get_db_connection(db_path='qstione.db') as conn:
                conn.execute(create_sql)
                conn.commit()
            print("✅ Tabela criada.")
        except Exception as e:
            print(f"❌ Erro ao criar tabela: {e}")
            return

        # Índices
        indices = [
            ('idx_professores_ofertas_email', "CREATE INDEX idx_professores_ofertas_email ON imp_009_professores_ofertas(emailProfessor)"),
            ('idx_professores_ofertas_codigo', "CREATE INDEX idx_professores_ofertas_codigo ON imp_009_professores_ofertas(codigoOferta)")
        ]
        for nome_idx, sql_idx in indices:
            if not self._indice_existe(nome_idx):
                try:
                    with get_db_connection(db_path='qstione.db') as conn:
                        conn.execute(sql_idx)
                        conn.commit()
                    print(f"✅ Índice {nome_idx} criado.")
                except Exception as e:
                    print(f"⚠️ Índice {nome_idx} não pôde ser criado: {e}")
            else:
                print(f"✅ Índice {nome_idx} já existe.")

    # -------------------------------------------------------------------------
    # Obter dados do Lyceum
    # -------------------------------------------------------------------------
    def obter_dados_lyceum(self):
        """
        Obtém do banco Lyceum os pares (disciplina, turma, ano, semestre, email)
        respeitando os filtros e garantindo DISTINCT para evitar duplicatas.
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Construir placeholders para períodos e faculdades
            periodos_placeholders = ','.join(['?'] * len(PERIODOS_VIGENTES))
            faculdades_placeholders = ','.join(['?'] * len(FACULDADES_INCLUIDAS))

            # Áreas de conhecimento: extrair apenas as não nulas para usar na cláusula IN
            areas_nao_nulas = [a for a in AREAS_CONHECIMENTO_INCLUIDAS if a is not None and a != '']
            areas_placeholders = ','.join(['?'] * len(areas_nao_nulas))

            query = f"""
                SELECT DISTINCT
                    t.disciplina,
                    t.turma,
                    t.ano,
                    t.semestre,
                    d.email
                FROM LY_TURMA t
                INNER JOIN LY_DISCIPLINA dsc
                    ON dsc.disciplina = t.disciplina
                INNER JOIN LY_TURMA_DOCENTE td
                    ON td.disciplina = t.disciplina
                    AND td.turma = t.turma
                    AND td.ano = t.ano
                    AND td.periodo = t.semestre
                INNER JOIN LY_DOCENTE d
                    ON d.num_func = td.num_func
                WHERE t.ano = ?
                  AND t.semestre IN ({periodos_placeholders})
                  AND t.sit_turma = 'aberta'
                  AND dsc.faculdade IN ({faculdades_placeholders})
                  AND (dsc.area_conhecimento IN ({areas_placeholders})
                       OR dsc.area_conhecimento IS NULL
                       OR dsc.area_conhecimento = '')
                  AND d.ativo = 'S'
                  AND d.email IS NOT NULL
                  AND d.email != ''
                ORDER BY t.disciplina, t.turma, d.email
            """

            params = [ANO_VIGENTE] + PERIODOS_VIGENTES + FACULDADES_INCLUIDAS + areas_nao_nulas
            cursor.execute(query, params)
            return cursor.fetchall()

    # -------------------------------------------------------------------------
    # Transformar dados
    # -------------------------------------------------------------------------
    def transformar_dados(self, dados_lyceum):
        dados_transformados = []

        for disciplina, turma, ano, semestre, email in dados_lyceum:
            # Validação do e-mail
            if not validar_email(email):
                print(f"  ⚠️  E-mail inválido para oferta {disciplina}_{turma}_{ano}{semestre}: {email}")
                continue

            # Geração do código da oferta (igual ao imp_005)
            codigo_oferta = gerar_codigo_oferta(disciplina, turma, ano, semestre)
            codigo_oferta = truncar_texto(codigo_oferta, 30)

            # E-mail normalizado
            email_final = converter_minusculas(email)
            email_final = truncar_texto(email_final, 100)

            dados_transformados.append({
                'codigoOferta': codigo_oferta,
                'emailProfessor': email_final
            })

        return dados_transformados

    # -------------------------------------------------------------------------
    # Importar para Qstione (MERGE)
    # -------------------------------------------------------------------------
    def importar_para_qstione(self, dados_transformados):
        self._criar_tabela()

        merge_sql = """
            MERGE INTO imp_009_professores_ofertas AS target
            USING (VALUES (?, ?)) AS source (codigoOferta, emailProfessor)
            ON target.codigoOferta = source.codigoOferta
               AND target.emailProfessor = source.emailProfessor
            WHEN MATCHED THEN
                UPDATE SET
                    data_atualizacao = GETDATE()
            WHEN NOT MATCHED THEN
                INSERT (codigoOferta, emailProfessor, data_criacao, data_atualizacao)
                VALUES (source.codigoOferta, source.emailProfessor, GETDATE(), GETDATE());
        """

        total_inseridos = 0
        total_atualizados = 0
        total_erros = 0

        with get_db_connection(db_path='qstione.db') as conn:
            cursor = conn.cursor()
            for reg in dados_transformados:
                try:
                    cursor.execute("""
                        SELECT 1 FROM imp_009_professores_ofertas
                        WHERE codigoOferta = ? AND emailProfessor = ?
                    """, (reg['codigoOferta'], reg['emailProfessor']))
                    existe = cursor.fetchone()

                    cursor.execute(merge_sql, (
                        reg['codigoOferta'],
                        reg['emailProfessor']
                    ))

                    if existe:
                        total_atualizados += 1
                    else:
                        total_inseridos += 1
                except Exception as e:
                    total_erros += 1
                    print(f"  ✗ Erro ao importar {reg['codigoOferta']} - {reg['emailProfessor']}: {e}")

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
        print("IMPORTAÇÃO: imp_009_professores_ofertas")
        print("=" * 70)

        # 1. Obtém dados brutos do Lyceum
        dados_lyceum = self.obter_dados_lyceum()
        print(f"📊 Registros encontrados no Lyceum (após DISTINCT): {len(dados_lyceum)}")

        # 2. Transforma e valida os dados
        print("🔄 Transformando dados...")
        dados_transformados = self.transformar_dados(dados_lyceum)
        print(f"✅ Registros válidos para importação: {len(dados_transformados)}")

        # 3. Importa para o banco Qstione
        print("💾 Importando para banco Qstione...")
        resultado = self.importar_para_qstione(dados_transformados)

        # 4. Exibe relatório final
        print(f"\n📈 RESULTADO DA IMPORTAÇÃO:")
        print(f"  ✓ Inseridos: {resultado['total_inseridos']}")
        print(f"  ↻ Atualizados: {resultado['total_atualizados']}")
        print(f"  ✗ Erros: {resultado['total_erros']}")
        print(f"  📋 Total processados: {resultado['total_processados']}")

        return dados_transformados


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    importador = ImportadorProfessoresOfertas()
    importador.executar_importacao()