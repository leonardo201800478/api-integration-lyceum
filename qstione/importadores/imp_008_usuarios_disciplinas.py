"""
Importador para tabela imp_008_usuarios_disciplinas
Adaptado para SQL Server usando core.database

Exporta a relação entre disciplinas e docentes (email) para o Qstione.
Gera o código da disciplina concatenado com as iniciais do curso,
seguindo a mesma regra do importador imp_002_disciplina.

Campos:
    - codigoDisciplina: CHAR(30)  – código da disciplina + '-' + iniciais do curso
    - emailUsuario:      CHAR(100) – e-mail do docente (minúsculas)

Filtros aplicados (centralizados em qstione.config.filtros):
    - LY_TURMA_DOCENTE: ano = ANO_VIGENTE, periodo = primeiro de PERIODOS_VIGENTES
    - LY_DISCIPLINA:    faculdade IN (FACULDADES_INCLUIDAS)
    - LY_DOCENTE:       ativo = 'S'
    - Apenas docentes com e‑mail válido (validar_email)
"""

from core.database import get_db_connection
from qstione.core.transformacoes import (
    gerar_codigo_disciplina_curso,
    converter_minusculas,
    truncar_texto
)
from qstione.core.validacoes import validar_email
from qstione.config.filtros import ANO_VIGENTE, PERIODOS_VIGENTES, FACULDADES_INCLUIDAS


class ImportadorUsuariosDisciplinas:

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
        if self._tabela_existe('imp_008_usuarios_disciplinas'):
            # Verifica se as colunas obrigatórias existem
            try:
                with get_db_connection(db_path='qstione.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
                        WHERE TABLE_NAME = 'imp_008_usuarios_disciplinas'
                          AND COLUMN_NAME IN ('data_criacao', 'data_atualizacao')
                    """)
                    colunas = [row[0] for row in cursor.fetchall()]
                    if 'data_criacao' in colunas and 'data_atualizacao' in colunas:
                        print("✅ Tabela imp_008_usuarios_disciplinas já existe com estrutura correta.")
                        return
                    else:
                        print("⚠️  Colunas ausentes. Recriando tabela...")
                        cursor.execute("DROP TABLE imp_008_usuarios_disciplinas")
                        conn.commit()
            except Exception as e:
                print(f"⚠️  Erro ao verificar colunas: {e}. Recriando tabela...")
                with get_db_connection(db_path='qstione.db') as conn:
                    conn.execute("DROP TABLE IF EXISTS imp_008_usuarios_disciplinas")
                    conn.commit()

        print("🆕 Criando tabela imp_008_usuarios_disciplinas...")
        create_sql = """
            CREATE TABLE imp_008_usuarios_disciplinas (
                codigoDisciplina NVARCHAR(30) NOT NULL,
                emailUsuario NVARCHAR(100) NOT NULL,
                data_criacao DATETIME2 DEFAULT GETDATE(),
                data_atualizacao DATETIME2 DEFAULT GETDATE(),
                PRIMARY KEY (codigoDisciplina, emailUsuario)
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
            ('idx_usuarios_disciplinas_email', "CREATE INDEX idx_usuarios_disciplinas_email ON imp_008_usuarios_disciplinas(emailUsuario)"),
            ('idx_usuarios_disciplinas_codigo', "CREATE INDEX idx_usuarios_disciplinas_codigo ON imp_008_usuarios_disciplinas(codigoDisciplina)")
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
        Obtém do banco Lyceum os pares (disciplina, email) únicos,
        respeitando os filtros de ano, período, faculdade e docente ativo.
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Usa o primeiro período da lista como período principal
            periodo_principal = PERIODOS_VIGENTES[0]
            faculdades_placeholder = ','.join(['?'] * len(FACULDADES_INCLUIDAS))

            query = f"""
                SELECT DISTINCT
                    td.disciplina,
                    d.email,
                    g.curso AS codigo_curso,
                    c.nome   AS nome_curso
                FROM LY_TURMA_DOCENTE td
                INNER JOIN LY_DISCIPLINA dsc
                    ON dsc.disciplina = td.disciplina
                INNER JOIN LY_DOCENTE d
                    ON d.num_func = td.num_func
                INNER JOIN LY_GRADE g
                    ON g.disciplina = td.disciplina
                INNER JOIN LY_CURSO c
                    ON c.curso = g.curso
                WHERE td.ano = ?
                  AND td.periodo = ?
                  AND dsc.faculdade IN ({faculdades_placeholder})
                  AND d.ativo = 'S'
                ORDER BY td.disciplina, d.email
            """

            params = [ANO_VIGENTE, periodo_principal] + FACULDADES_INCLUIDAS
            cursor.execute(query, params)
            return cursor.fetchall()

    # -------------------------------------------------------------------------
    # Transformar dados
    # -------------------------------------------------------------------------
    def transformar_dados(self, dados_lyceum):
        """
        Transforma cada registro bruto do Lyceum no formato esperado pelo Qstione.
        - Gera codigoDisciplina com a função gerar_codigo_disciplina_curso
        - Converte e‑mail para minúsculas
        - Valida o e‑mail; registros inválidos são ignorados com aviso
        """
        dados_transformados = []

        for disciplina, email, codigo_curso, nome_curso in dados_lyceum:
            # Validação do e-mail (campo obrigatório)
            if not validar_email(email):
                print(f"  ⚠️  E-mail inválido para disciplina {disciplina}: {email}")
                continue

            # Geração do código da disciplina (igual ao imp_002)
            codigo_disciplina_final = gerar_codigo_disciplina_curso(
                disciplina,
                nome_curso,
                codigo_curso
            )

            # E-mail em minúsculas e truncado
            email_final = converter_minusculas(email)
            email_final = truncar_texto(email_final, 100)

            # Truncar código da disciplina para 30 caracteres
            codigo_disciplina_final = truncar_texto(codigo_disciplina_final, 30)

            dados_transformados.append({
                'codigoDisciplina': codigo_disciplina_final,
                'emailUsuario': email_final
            })

        return dados_transformados

    # -------------------------------------------------------------------------
    # Importar para Qstione (MERGE)
    # -------------------------------------------------------------------------
    def importar_para_qstione(self, dados_transformados):
        self._criar_tabela()

        merge_sql = """
            MERGE INTO imp_008_usuarios_disciplinas AS target
            USING (VALUES (?, ?)) AS source (codigoDisciplina, emailUsuario)
            ON target.codigoDisciplina = source.codigoDisciplina
               AND target.emailUsuario = source.emailUsuario
            WHEN MATCHED THEN
                UPDATE SET
                    data_atualizacao = GETDATE()
            WHEN NOT MATCHED THEN
                INSERT (codigoDisciplina, emailUsuario, data_criacao, data_atualizacao)
                VALUES (source.codigoDisciplina, source.emailUsuario, GETDATE(), GETDATE());
        """

        total_inseridos = 0
        total_atualizados = 0
        total_erros = 0

        with get_db_connection(db_path='qstione.db') as conn:
            cursor = conn.cursor()
            for reg in dados_transformados:
                try:
                    cursor.execute("""
                        SELECT 1 FROM imp_008_usuarios_disciplinas
                        WHERE codigoDisciplina = ? AND emailUsuario = ?
                    """, (reg['codigoDisciplina'], reg['emailUsuario']))
                    existe = cursor.fetchone()

                    cursor.execute(merge_sql, (
                        reg['codigoDisciplina'],
                        reg['emailUsuario']
                    ))

                    if existe:
                        total_atualizados += 1
                    else:
                        total_inseridos += 1
                except Exception as e:
                    total_erros += 1
                    print(f"  ✗ Erro ao importar {reg['codigoDisciplina']} - {reg['emailUsuario']}: {e}")

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
        print("IMPORTAÇÃO: imp_008_usuarios_disciplinas")
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
    importador = ImportadorUsuariosDisciplinas()
    importador.executar_importacao()