"""
Importador para tabela imp_007_usuarios_cursos
Adaptado para SQL Server com garantia de unicidade por (curso, email)
"""

from core.database import get_db_connection
from qstione.core.transformacoes import (
    converter_minusculas,
    determinar_papel_usuario
)
from qstione.core.validacoes import (
    validar_codigo_curso,
    validar_email,
    validar_papel_usuario
)
from qstione.config.filtros import ANO_VIGENTE, PERIODOS_VIGENTES


class ImportadorUsuariosCursos:

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
        if self._tabela_existe('imp_007_usuarios_cursos'):
            # Verifica se as colunas obrigatórias existem
            try:
                with get_db_connection(db_path='qstione.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
                        WHERE TABLE_NAME = 'imp_007_usuarios_cursos'
                          AND COLUMN_NAME IN ('data_criacao', 'data_atualizacao')
                    """)
                    colunas = [row[0] for row in cursor.fetchall()]
                    if 'data_criacao' in colunas and 'data_atualizacao' in colunas:
                        print("✅ Tabela imp_007_usuarios_cursos já existe com estrutura correta.")
                        return
                    else:
                        print("⚠️  Colunas ausentes. Recriando tabela...")
                        cursor.execute("DROP TABLE imp_007_usuarios_cursos")
                        conn.commit()
            except Exception as e:
                print(f"⚠️  Erro ao verificar colunas: {e}. Recriando tabela...")
                with get_db_connection(db_path='qstione.db') as conn:
                    conn.execute("DROP TABLE IF EXISTS imp_007_usuarios_cursos")
                    conn.commit()

        print("🆕 Criando tabela imp_007_usuarios_cursos...")
        create_sql = """
            CREATE TABLE imp_007_usuarios_cursos (
                codigoCurso NVARCHAR(30) NOT NULL,
                emailUsuario NVARCHAR(100) NOT NULL,
                papelUsuario NVARCHAR(1) NOT NULL,
                data_criacao DATETIME2 DEFAULT GETDATE(),
                data_atualizacao DATETIME2 DEFAULT GETDATE(),
                PRIMARY KEY (codigoCurso, emailUsuario)
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
            ('idx_usuarios_cursos_email', "CREATE INDEX idx_usuarios_cursos_email ON imp_007_usuarios_cursos(emailUsuario)"),
            ('idx_usuarios_cursos_curso', "CREATE INDEX idx_usuarios_cursos_curso ON imp_007_usuarios_cursos(codigoCurso)"),
            ('idx_usuarios_cursos_papel', "CREATE INDEX idx_usuarios_cursos_papel ON imp_007_usuarios_cursos(papelUsuario)")
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
    # Obter coordenadores da tabela LY_COORDENACAO
    # -------------------------------------------------------------------------
    def obter_coordenadores(self):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT DISTINCT num_func, curso
                FROM LY_COORDENACAO
            """
            cursor.execute(query)
            coordenadores = {}
            for row in cursor.fetchall():
                num_func, curso = row
                chave = (str(num_func), str(curso))
                coordenadores[chave] = True
            print(f"📋 Coordenadores encontrados: {len(coordenadores)}")
            return coordenadores

    # -------------------------------------------------------------------------
    # Obter dados principais do Lyceum (garantindo unicidade por curso e email)
    # -------------------------------------------------------------------------
    def obter_dados_lyceum(self):
        # Primeiro obtém coordenadores
        coordenadores = self.obter_coordenadores()

        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Usamos uma subconsulta para trazer uma única linha por (num_func, curso)
            # com a informação de se o docente é coordenador (através de LEFT JOIN com coordenadores).
            # Depois, no Python, determinamos o papel.
            periodo_principal = PERIODOS_VIGENTES[0]
            query = """
                SELECT DISTINCT
                    td.num_func,
                    d.email,
                    g.curso
                FROM LY_TURMA_DOCENTE td
                INNER JOIN LY_GRADE g
                    ON g.disciplina = td.disciplina
                INNER JOIN LY_DOCENTE d
                    ON d.num_func = td.num_func
                WHERE td.ano = ?
                  AND td.periodo = ?
                  AND d.ativo = 'S'
                ORDER BY td.num_func, g.curso
            """
            cursor.execute(query, (ANO_VIGENTE, periodo_principal))
            dados = cursor.fetchall()

        return dados, coordenadores

    # -------------------------------------------------------------------------
    # Transformar dados (com deduplicação final por (email, curso))
    # -------------------------------------------------------------------------
    def transformar_dados(self, dados_lyceum, coordenadores):
        # Usamos um dicionário para garantir unicidade por (email, curso)
        # e dar prioridade ao papel 'C' (coordenador) caso haja conflito
        registros_unicos = {}

        for registro in dados_lyceum:
            num_func, email, curso = registro

            # Validações
            if not validar_codigo_curso(curso):
                print(f"  ⚠️  Código do curso inválido: {curso} para docente {num_func}")
                continue

            if not validar_email(email):
                print(f"  ⚠️  Email inválido: {email} para docente {num_func}")
                continue

            # Transformações
            email_final = converter_minusculas(email)
            chave = (str(curso)[:30], email_final[:100])

            # Determinar papel do usuário (C ou P)
            papel = determinar_papel_usuario(num_func, curso, coordenadores)

            if not validar_papel_usuario(papel):
                print(f"  ⚠️  Papel do usuário inválido: {papel} para docente {num_func}")
                continue

            # Se já existe um registro para a mesma chave, mantém o que tem maior prioridade
            # Prioridade: C > P
            if chave in registros_unicos:
                papel_existente = registros_unicos[chave]['papelUsuario']
                # Se o papel atual é C e o existente é P, substitui
                if papel == 'C' and papel_existente == 'P':
                    registros_unicos[chave]['papelUsuario'] = papel
                # Se ambos são iguais, não faz nada (mantém)
                # Se o atual é P e o existente é C, mantém o C (já está)
            else:
                registros_unicos[chave] = {
                    'codigoCurso': str(curso)[:30],
                    'emailUsuario': email_final[:100],
                    'papelUsuario': papel
                }

        return list(registros_unicos.values())

    # -------------------------------------------------------------------------
    # Importar para Qstione (MERGE)
    # -------------------------------------------------------------------------
    def importar_para_qstione(self, dados_transformados):
        self._criar_tabela()

        merge_sql = """
            MERGE INTO imp_007_usuarios_cursos AS target
            USING (VALUES (?, ?, ?)) AS source (codigoCurso, emailUsuario, papelUsuario)
            ON target.codigoCurso = source.codigoCurso
               AND target.emailUsuario = source.emailUsuario
            WHEN MATCHED THEN
                UPDATE SET
                    papelUsuario = source.papelUsuario,
                    data_atualizacao = GETDATE()
            WHEN NOT MATCHED THEN
                INSERT (codigoCurso, emailUsuario, papelUsuario, data_criacao, data_atualizacao)
                VALUES (source.codigoCurso, source.emailUsuario, source.papelUsuario, GETDATE(), GETDATE());
        """

        total_inseridos = 0
        total_atualizados = 0
        total_erros = 0

        with get_db_connection(db_path='qstione.db') as conn:
            cursor = conn.cursor()
            for reg in dados_transformados:
                try:
                    cursor.execute("""
                        SELECT 1 FROM imp_007_usuarios_cursos
                        WHERE codigoCurso = ? AND emailUsuario = ?
                    """, (reg['codigoCurso'], reg['emailUsuario']))
                    existe = cursor.fetchone()

                    cursor.execute(merge_sql, (
                        reg['codigoCurso'],
                        reg['emailUsuario'],
                        reg['papelUsuario']
                    ))

                    if existe:
                        total_atualizados += 1
                    else:
                        total_inseridos += 1
                except Exception as e:
                    total_erros += 1
                    print(f"  ✗  Erro ao importar {reg['codigoCurso']} - {reg['emailUsuario']}: {e}")

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
        print("IMPORTAÇÃO: imp_007_usuarios_cursos")
        print("=" * 70)

        # 1. Obter dados do Lyceum (inclui coordenadores)
        print("📋 Obtendo dados do Lyceum...")
        dados_lyceum, coordenadores = self.obter_dados_lyceum()
        print(f"📊 Registros encontrados no Lyceum (após DISTINCT): {len(dados_lyceum)}")

        # 2. Transformar dados (deduplicação por curso+email)
        print("🔄 Transformando dados...")
        dados_transformados = self.transformar_dados(dados_lyceum, coordenadores)
        print(f"✅ Registros únicos para importação: {len(dados_transformados)}")

        # 3. Importar para Qstione
        print("💾 Importando para banco Qstione...")
        resultado = self.importar_para_qstione(dados_transformados)

        print(f"\n📈 RESULTADO DA IMPORTAÇÃO:")
        print(f"  ✓ Inseridos: {resultado['total_inseridos']}")
        print(f"  ↻ Atualizados: {resultado['total_atualizados']}")
        print(f"  ✗ Erros: {resultado['total_erros']}")
        print(f"  📋 Total processados: {resultado['total_processados']}")

        # Estatísticas de papéis
        coordenadores_count = sum(1 for reg in dados_transformados if reg['papelUsuario'] == 'C')
        professores_count = sum(1 for reg in dados_transformados if reg['papelUsuario'] == 'P')

        print(f"\n👥 DISTRIBUIÇÃO DE PAPÉIS:")
        print(f"  👑 Coordenadores (C): {coordenadores_count}")
        print(f"  👨‍🏫 Professores (P): {professores_count}")

        return dados_transformados


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    importador = ImportadorUsuariosCursos()
    importador.executar_importacao()