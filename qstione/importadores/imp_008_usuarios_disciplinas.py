"""
qstione/importadores/imp_008_usuarios_disciplinas.py
Importador para tabela imp_008_usuarios_disciplinas
Adaptado para SQL Server usando core.database e alinhado ao imp_002

MODIFICAÇÃO: agora inclui, para cada disciplina, os e-mails dos coordenadores
e membros do NDE dos cursos associados à disciplina via LY_GRADE,
além dos docentes já existentes.
- Somente registros com status = 'S' nas tabelas imp_nde_* são considerados.
- Tabela imp_008_usuarios_disciplinas agora possui coluna STATUS ('S'/'N') para controle de ativos.
"""

from core.database import get_db_connection
from qstione.core.transformacoes import (
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
        if self._tabela_existe('imp_008_usuarios_disciplinas'):
            # Verifica se coluna status existe, senão adiciona
            with get_db_connection(database_name='qstione') as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_NAME = 'imp_008_usuarios_disciplinas'
                      AND COLUMN_NAME = 'status'
                """)
                if not cursor.fetchone():
                    print("   ↳ Adicionando coluna status à imp_008_usuarios_disciplinas...")
                    conn.execute("ALTER TABLE imp_008_usuarios_disciplinas ADD status CHAR(1) NOT NULL DEFAULT 'S'")
                    conn.commit()
                # Verifica se colunas data_criacao e data_atualizacao existem
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
        # Se não existe ou foi recriada, cria nova com status
        print("🆕 Criando tabela imp_008_usuarios_disciplinas...")
        create_sql = """
            CREATE TABLE imp_008_usuarios_disciplinas (
                codigoDisciplina NVARCHAR(30) NOT NULL,
                emailUsuario NVARCHAR(100) NOT NULL,
                status CHAR(1) NOT NULL DEFAULT 'S',
                data_criacao DATETIME2 DEFAULT GETDATE(),
                data_atualizacao DATETIME2 DEFAULT GETDATE(),
                PRIMARY KEY (codigoDisciplina, emailUsuario)
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
            ('idx_usuarios_disciplinas_email', "CREATE INDEX idx_usuarios_disciplinas_email ON imp_008_usuarios_disciplinas(emailUsuario)"),
            ('idx_usuarios_disciplinas_codigo', "CREATE INDEX idx_usuarios_disciplinas_codigo ON imp_008_usuarios_disciplinas(codigoDisciplina)")
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
    # Obter mapeamento disciplina original -> código padronizado (da tabela imp_002)
    # -------------------------------------------------------------------------
    def _obter_codigos_disciplina(self):
        """
        Consulta a tabela imp_002_disciplina no banco Qstione e retorna um dicionário
        com a disciplina original (extraída da parte antes do '-') -> codigoDisciplina completo.
        """
        codigos = {}
        try:
            with get_db_connection(database_name='qstione') as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT codigoDisciplina FROM imp_002_disciplina
                """)
                for row in cursor.fetchall():
                    codigo_completo = row[0]
                    if '-' in codigo_completo:
                        original = codigo_completo.split('-')[0]
                        codigos[original] = codigo_completo
                    else:
                        codigos[codigo_completo] = codigo_completo
        except Exception as e:
            print(f"  ⚠️  Erro ao consultar imp_002_disciplina: {e}")
        return codigos

    # -------------------------------------------------------------------------
    # Buscar e-mails dos coordenadores e membros do NDE por curso (tabelas Qstione)
    # Agora com filtro de STATUS = 'S' (apenas ativos)
    # -------------------------------------------------------------------------
    def _obter_emails_nde_por_curso(self):
        """
        Retorna um dicionário: codigoCurso -> lista de e-mails (coordenador + membros)
        a partir das tabelas imp_nde_cursos e imp_nde_membros, considerando apenas
        registros com status = 'S' (ativos).
        """
        emails_por_curso = {}
        try:
            with get_db_connection(database_name='qstione') as conn:
                cursor = conn.cursor()
                # Coordenadores ativos (status = 'S')
                cursor.execute("""
                    SELECT codigoCurso, emailCoordenador
                    FROM imp_nde_cursos
                    WHERE emailCoordenador IS NOT NULL AND emailCoordenador != ''
                      AND status = 'S'
                """)
                for row in cursor.fetchall():
                    curso = row[0]
                    email = row[1]
                    if curso not in emails_por_curso:
                        emails_por_curso[curso] = []
                    emails_por_curso[curso].append(email)

                # Membros ativos (status = 'S')
                cursor.execute("""
                    SELECT codigoCurso, emailMembro
                    FROM imp_nde_membros
                    WHERE emailMembro IS NOT NULL AND emailMembro != ''
                      AND status = 'S'
                """)
                for row in cursor.fetchall():
                    curso = row[0]
                    email = row[1]
                    if curso not in emails_por_curso:
                        emails_por_curso[curso] = []
                    emails_por_curso[curso].append(email)

        except Exception as e:
            print(f"  ⚠️  Erro ao buscar e-mails do NDE: {e}")
        return emails_por_curso

    # -------------------------------------------------------------------------
    # Obter dados do Lyceum (docentes + NDE)
    # -------------------------------------------------------------------------
    def obter_dados_lyceum(self):
        """
        Obtém do banco Lyceum os pares (disciplina, email) únicos,
        respeitando os filtros de ano, período, faculdade.

        Fontes:
        1. Docentes ativos (LY_TURMA_DOCENTE + LY_DOCENTE) – sempre incluídos.
        2. Coordenadores e membros do NDE (apenas status = 'S'), via LY_GRADE
           para obter o curso de cada disciplina, e depois buscas nas tabelas imp_nde_*.
        """
        periodo_principal = PERIODOS_VIGENTES[0]
        faculdades_placeholder = ','.join(['?'] * len(FACULDADES_INCLUIDAS))

        # ------------------------------------------------------------
        # 1. Docentes (consulta original)
        # ------------------------------------------------------------
        with get_db_connection() as conn:
            cursor = conn.cursor()
            query_docentes = f"""
                SELECT DISTINCT
                    td.disciplina,
                    d.email
                FROM LY_TURMA_DOCENTE td
                INNER JOIN LY_DISCIPLINA dsc
                    ON dsc.disciplina = td.disciplina
                INNER JOIN LY_DOCENTE d
                    ON d.num_func = td.num_func
                WHERE td.ano = ?
                  AND td.periodo = ?
                  AND dsc.faculdade IN ({faculdades_placeholder})
                  AND d.ativo = 'S'
            """
            params = [ANO_VIGENTE, periodo_principal] + FACULDADES_INCLUIDAS
            cursor.execute(query_docentes, params)
            docentes = cursor.fetchall()  # lista de (disciplina, email)

        # ------------------------------------------------------------
        # 2. Disciplinas e seus cursos via LY_GRADE (para NDE)
        # ------------------------------------------------------------
        with get_db_connection() as conn:
            cursor = conn.cursor()
            query_grade = f"""
                SELECT DISTINCT
                    td.disciplina,
                    g.curso
                FROM LY_TURMA_DOCENTE td
                INNER JOIN LY_DISCIPLINA dsc
                    ON dsc.disciplina = td.disciplina
                INNER JOIN LY_GRADE g
                    ON g.disciplina = td.disciplina
                WHERE td.ano = ?
                  AND td.periodo = ?
                  AND dsc.faculdade IN ({faculdades_placeholder})
            """
            cursor.execute(query_grade, params)
            pares_disciplina_curso = cursor.fetchall()  # lista de (disciplina, curso)

        # ------------------------------------------------------------
        # 3. Emails NDE por curso (apenas ativos) – tabelas Qstione
        # ------------------------------------------------------------
        emails_nde_por_curso = self._obter_emails_nde_por_curso()

        # ------------------------------------------------------------
        # 4. Construir lista final de pares (disciplina, email)
        # ------------------------------------------------------------
        resultados = set()  # para evitar duplicatas

        # Adiciona docentes (sempre)
        for disciplina, email in docentes:
            if disciplina and email:
                resultados.add((disciplina, email))

        # Adiciona NDE (apenas ativos, já filtrados em _obter_emails_nde_por_curso)
        for disciplina, curso in pares_disciplina_curso:
            if disciplina and curso:
                emails_do_curso = emails_nde_por_curso.get(curso, [])
                for email in emails_do_curso:
                    if email:
                        resultados.add((disciplina, email))

        # Retorna como lista de tuplas
        return list(resultados)

    # -------------------------------------------------------------------------
    # Transformar dados (usando mapeamento de disciplinas do imp_002)
    # -------------------------------------------------------------------------
    def transformar_dados(self, dados_lyceum):
        mapa_codigos = self._obter_codigos_disciplina()
        if not mapa_codigos:
            print("  ⚠️  Nenhum código de disciplina encontrado no imp_002. Os códigos serão gerados dinamicamente, mas podem divergir.")

        dados_transformados = []

        for disciplina, email in dados_lyceum:
            # Validação do e-mail
            if not validar_email(email):
                print(f"  ⚠️  E-mail inválido para disciplina {disciplina}: {email}")
                continue

            # Obter código padronizado
            if disciplina in mapa_codigos:
                codigo_disciplina_final = mapa_codigos[disciplina]
            else:
                # Fallback: gerar um código genérico (sem curso) – apenas o código original truncado
                print(f"  ⚠️  Disciplina {disciplina} não encontrada no imp_002. Usando código original.")
                codigo_disciplina_final = truncar_texto(disciplina, 30)

            # E-mail em minúsculas e truncado
            email_final = converter_minusculas(email)
            email_final = truncar_texto(email_final, 100)

            dados_transformados.append({
                'codigoDisciplina': codigo_disciplina_final,
                'emailUsuario': email_final
            })

        return dados_transformados

    # -------------------------------------------------------------------------
    # Importar para Qstione (MERGE) com status
    # -------------------------------------------------------------------------
    def importar_para_qstione(self, dados_transformados):
        self._criar_tabela()

        # Primeiro, marcar todos os registros existentes como inativos ('N')
        with get_db_connection(database_name='qstione') as conn:
            conn.execute("UPDATE imp_008_usuarios_disciplinas SET status = 'N', data_atualizacao = GETDATE()")
            conn.commit()

        merge_sql = """
            MERGE INTO imp_008_usuarios_disciplinas AS target
            USING (VALUES (?, ?)) AS source (codigoDisciplina, emailUsuario)
            ON target.codigoDisciplina = source.codigoDisciplina
               AND target.emailUsuario = source.emailUsuario
            WHEN MATCHED THEN
                UPDATE SET
                    status = 'S',
                    data_atualizacao = GETDATE()
            WHEN NOT MATCHED THEN
                INSERT (codigoDisciplina, emailUsuario, status, data_criacao, data_atualizacao)
                VALUES (source.codigoDisciplina, source.emailUsuario, 'S', GETDATE(), GETDATE());
        """

        total_inseridos = 0
        total_atualizados = 0
        total_erros = 0

        with get_db_connection(database_name='qstione') as conn:
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

        dados_lyceum = self.obter_dados_lyceum()
        print(f"📊 Registros encontrados no Lyceum (após DISTINCT e união com NDE): {len(dados_lyceum)}")

        print("🔄 Transformando dados...")
        dados_transformados = self.transformar_dados(dados_lyceum)
        print(f"✅ Registros válidos para importação: {len(dados_transformados)}")

        print("💾 Importando para banco Qstione...")
        resultado = self.importar_para_qstione(dados_transformados)

        print(f"\n📈 RESULTADO DA IMPORTAÇÃO:")
        print(f"  ✓ Inseridos: {resultado['total_inseridos']}")
        print(f"  ↻ Atualizados: {resultado['total_atualizados']}")
        print(f"  ✗ Erros: {resultado['total_erros']}")
        print(f"  📋 Total processados: {resultado['total_processados']}")
        print("\n✅ Registros presentes no Lyceum foram marcados como 'S' (ativo).")
        print("   Registros ausentes foram marcados como 'N' (inativo).")

        return dados_transformados


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    importador = ImportadorUsuariosDisciplinas()
    importador.executar_importacao()