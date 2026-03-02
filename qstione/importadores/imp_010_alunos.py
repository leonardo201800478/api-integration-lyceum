"""
qstione/importadores/imp_010_alunos.py
Importador para tabela imp_010_alunos
Adaptado para SQL Server usando core.database

Exporta dados de alunos ativos do Lyceum para o Qstione.
Filtro: LY_ALUNO.sit_aluno = 'Ativo'

Campos:
    - matriculaAluno:       NVARCHAR(20)  – aluno (ly_aluno.aluno)
    - nomeAluno:            NVARCHAR(140) – nome_compl (ly_aluno.nome_compl)
    - emailAluno:           NVARCHAR(100) – concatenado: aluno + '@dominio' onde dominio é 'etecfoa.com.br' se unidade_ensino = '007', senão 'unifoa.edu.br'
    - codigoCurso:          NVARCHAR(30)  – curso (ly_aluno.curso)
    - turno:                NVARCHAR(1)   – mapeado via mapear_turno(ly_aluno.turno)
    - codigoIdentificacaoAVA: NVARCHAR(100) – sempre vazio
"""

from core.database import get_db_connection
from qstione.core.transformacoes import (
    truncar_texto,
    converter_minusculas,
    mapear_turno
)
from qstione.core.validacoes import validar_matricula, validar_nome, validar_codigo_curso


class ImportadorAlunos:

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
        if self._tabela_existe('imp_010_alunos'):
            # Verifica se as colunas obrigatórias existem
            try:
                with get_db_connection(db_path='qstione.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
                        WHERE TABLE_NAME = 'imp_010_alunos'
                          AND COLUMN_NAME IN ('data_criacao', 'data_atualizacao')
                    """)
                    colunas = [row[0] for row in cursor.fetchall()]
                    if 'data_criacao' in colunas and 'data_atualizacao' in colunas:
                        print("✅ Tabela imp_010_alunos já existe com estrutura correta.")
                        return
                    else:
                        print("⚠️  Colunas ausentes. Recriando tabela...")
                        cursor.execute("DROP TABLE imp_010_alunos")
                        conn.commit()
            except Exception as e:
                print(f"⚠️  Erro ao verificar colunas: {e}. Recriando tabela...")
                with get_db_connection(db_path='qstione.db') as conn:
                    conn.execute("DROP TABLE IF EXISTS imp_010_alunos")
                    conn.commit()

        print("🆕 Criando tabela imp_010_alunos...")
        create_sql = """
            CREATE TABLE imp_010_alunos (
                matriculaAluno NVARCHAR(20) NOT NULL,
                nomeAluno NVARCHAR(140) NOT NULL,
                emailAluno NVARCHAR(100) NULL,
                codigoCurso NVARCHAR(30) NOT NULL,
                turno NVARCHAR(1) NULL,
                codigoIdentificacaoAVA NVARCHAR(100) NULL,
                data_criacao DATETIME2 DEFAULT GETDATE(),
                data_atualizacao DATETIME2 DEFAULT GETDATE(),
                PRIMARY KEY (matriculaAluno)
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

        # Índice para curso (opcional)
        if not self._indice_existe('idx_alunos_curso'):
            try:
                with get_db_connection(db_path='qstione.db') as conn:
                    conn.execute("CREATE INDEX idx_alunos_curso ON imp_010_alunos(codigoCurso)")
                    conn.commit()
                print("✅ Índice idx_alunos_curso criado.")
            except Exception as e:
                print(f"⚠️ Índice idx_alunos_curso não pôde ser criado: {e}")

    # -------------------------------------------------------------------------
    # Obter dados do Lyceum (apenas alunos ativos)
    # -------------------------------------------------------------------------
    def obter_dados_lyceum(self):
        """
        Obtém todos os alunos ativos da tabela LY_ALUNO (sit_aluno = 'Ativo').
        Retorna lista de tuplas (aluno, nome_compl, unidade_ensino, curso, turno)
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT
                    aluno,
                    nome_compl,
                    unidade_ensino,
                    curso,
                    turno
                FROM LY_ALUNO
                WHERE sit_aluno = 'Ativo'
                ORDER BY aluno
            """
            cursor.execute(query)
            return cursor.fetchall()

    # -------------------------------------------------------------------------
    # Transformar dados (com lógica de e-mail por unidade_ensino)
    # -------------------------------------------------------------------------
    def transformar_dados(self, dados_lyceum):
        dados_transformados = []

        for registro in dados_lyceum:
            aluno, nome_compl, unidade_ensino, curso, turno = registro

            # Validações básicas
            if not validar_matricula(aluno):
                print(f"  ⚠️  Matrícula inválida: {aluno}")
                continue

            if not validar_nome(nome_compl):
                print(f"  ⚠️  Nome inválido para aluno {aluno}: {nome_compl}")
                continue

            if not validar_codigo_curso(curso):
                print(f"  ⚠️  Código de curso inválido: {curso} para aluno {aluno}")
                continue

            # Nome do aluno (truncar)
            nome_aluno = truncar_texto(nome_compl, 140)

            # Gerar e-mail conforme unidade_ensino
            if unidade_ensino == '007':
                dominio = '@etecfoa.com.br'
            else:
                dominio = '@unifoa.edu.br'
            email_aluno = converter_minusculas(f"{aluno}{dominio}")
            email_aluno = truncar_texto(email_aluno, 100)

            # Mapear turno
            turno_mapeado = mapear_turno(turno)  # retorna M,T,N,I,O ou None

            # Código identificação AVA (vazio)
            codigo_ava = ''

            dados_transformados.append({
                'matriculaAluno': str(aluno)[:20],
                'nomeAluno': nome_aluno,
                'emailAluno': email_aluno,
                'codigoCurso': str(curso)[:30],
                'turno': turno_mapeado,
                'codigoIdentificacaoAVA': codigo_ava
            })

        return dados_transformados

    # -------------------------------------------------------------------------
    # Importar para Qstione (MERGE)
    # -------------------------------------------------------------------------
    def importar_para_qstione(self, dados_transformados):
        self._criar_tabela()

        merge_sql = """
            MERGE INTO imp_010_alunos AS target
            USING (VALUES (?, ?, ?, ?, ?, ?)) AS source (matriculaAluno, nomeAluno, emailAluno, codigoCurso, turno, codigoIdentificacaoAVA)
            ON target.matriculaAluno = source.matriculaAluno
            WHEN MATCHED THEN
                UPDATE SET
                    nomeAluno = source.nomeAluno,
                    emailAluno = source.emailAluno,
                    codigoCurso = source.codigoCurso,
                    turno = source.turno,
                    codigoIdentificacaoAVA = source.codigoIdentificacaoAVA,
                    data_atualizacao = GETDATE()
            WHEN NOT MATCHED THEN
                INSERT (matriculaAluno, nomeAluno, emailAluno, codigoCurso, turno, codigoIdentificacaoAVA, data_criacao, data_atualizacao)
                VALUES (source.matriculaAluno, source.nomeAluno, source.emailAluno, source.codigoCurso, source.turno, source.codigoIdentificacaoAVA, GETDATE(), GETDATE());
        """

        total_inseridos = 0
        total_atualizados = 0
        total_erros = 0

        with get_db_connection(db_path='qstione.db') as conn:
            cursor = conn.cursor()
            for reg in dados_transformados:
                try:
                    cursor.execute("SELECT 1 FROM imp_010_alunos WHERE matriculaAluno = ?", (reg['matriculaAluno'],))
                    existe = cursor.fetchone()

                    cursor.execute(merge_sql, (
                        reg['matriculaAluno'],
                        reg['nomeAluno'],
                        reg['emailAluno'],
                        reg['codigoCurso'],
                        reg['turno'],
                        reg['codigoIdentificacaoAVA']
                    ))

                    if existe:
                        total_atualizados += 1
                    else:
                        total_inseridos += 1
                except Exception as e:
                    total_erros += 1
                    print(f"  ✗  Erro ao importar {reg['matriculaAluno']}: {e}")

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
        print("IMPORTAÇÃO: imp_010_alunos")
        print("=" * 70)

        # 1. Obter dados do Lyceum (apenas ativos)
        dados_lyceum = self.obter_dados_lyceum()
        print(f"📊 Registros encontrados no Lyceum: {len(dados_lyceum)}")

        # 2. Transformar dados
        print("🔄 Transformando dados...")
        dados_transformados = self.transformar_dados(dados_lyceum)
        print(f"✅ Registros válidos para importação: {len(dados_transformados)}")

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
    importador = ImportadorAlunos()
    importador.executar_importacao()