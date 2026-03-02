"""
qstione/importadores/imp_011_alunos_ofertas.py
Importador para tabela imp_011_alunos_ofertas (Alunos das Ofertas de Disciplinas)
Adaptado para SQL Server – corrigido: PK sem coluna anulável.
"""

from core.database import get_db_connection
from qstione.core.transformacoes import gerar_codigo_oferta, truncar_texto
from qstione.core.validacoes import validar_matricula, validar_codigo_curso
from qstione.config.filtros import ANO_VIGENTE, PERIODOS_VIGENTES, SITUACAO_TURMA_VALIDA


class ImportadorAlunosOfertas:

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

    def _criar_tabela(self) -> bool:
        if self._tabela_existe('imp_011_alunos_ofertas'):
            print("✅ Tabela imp_011_alunos_ofertas já existe.")
            return True

        print("🆕 Criando tabela imp_011_alunos_ofertas...")
        create_sql = """
            CREATE TABLE imp_011_alunos_ofertas (
                codigoOferta NVARCHAR(30) NOT NULL,
                matriculaAluno NVARCHAR(20) NOT NULL,
                codigoCurso NVARCHAR(30) NULL,
                data_criacao DATETIME2 DEFAULT GETDATE(),
                data_atualizacao DATETIME2 DEFAULT GETDATE(),
                PRIMARY KEY (codigoOferta, matriculaAluno)
            )
        """
        try:
            with get_db_connection(db_path='qstione.db') as conn:
                conn.execute(create_sql)
                conn.commit()
            print("✅ Tabela criada com sucesso.")
        except Exception as e:
            print(f"❌ Erro ao criar tabela: {e}")
            return False

        # Índices opcionais
        indices = [
            ('idx_alunos_ofertas_matricula', "CREATE INDEX idx_alunos_ofertas_matricula ON imp_011_alunos_ofertas(matriculaAluno)"),
            ('idx_alunos_ofertas_curso', "CREATE INDEX idx_alunos_ofertas_curso ON imp_011_alunos_ofertas(codigoCurso) WHERE codigoCurso IS NOT NULL"),
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
        return True

    # -------------------------------------------------------------------------
    # Obter dados do Lyceum
    # -------------------------------------------------------------------------
    def obter_dados_lyceum(self):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            periodos_placeholders = ','.join(['?'] * len(PERIODOS_VIGENTES))
            situacao = SITUACAO_TURMA_VALIDA if 'SITUACAO_TURMA_VALIDA' in locals() else 'aberta'

            query = f"""
                SELECT
                    m.aluno,
                    m.ano,
                    m.semestre,
                    m.turma,
                    m.disciplina,
                    a.curso
                FROM LY_MATRICULA m
                INNER JOIN LY_TURMA t
                    ON m.ano = t.ano
                    AND m.semestre = t.semestre
                    AND m.turma = t.turma
                    AND m.disciplina = t.disciplina
                INNER JOIN LY_ALUNO a
                    ON m.aluno = a.aluno
                WHERE m.ano = ?
                  AND m.semestre IN ({periodos_placeholders})
                  AND t.sit_turma = ?
                ORDER BY m.aluno, m.ano, m.semestre, m.turma, m.disciplina
            """
            params = [ANO_VIGENTE] + PERIODOS_VIGENTES + [situacao]
            cursor.execute(query, params)
            return cursor.fetchall()

    # -------------------------------------------------------------------------
    # Transformar dados
    # -------------------------------------------------------------------------
    def transformar_dados(self, dados_lyceum):
        dados_transformados = []
        for row in dados_lyceum:
            aluno, ano, semestre, turma, disciplina, curso = row

            if not validar_matricula(aluno):
                print(f"  ⚠️  Matrícula inválida: {aluno}")
                continue
            if curso and not validar_codigo_curso(curso):
                print(f"  ⚠️  Código de curso inválido: {curso} para aluno {aluno}")
                continue

            codigo_oferta = gerar_codigo_oferta(disciplina, turma, ano, semestre)
            codigo_oferta = truncar_texto(codigo_oferta, 30)
            matricula_aluno = truncar_texto(aluno, 20)

            dados_transformados.append({
                'codigoOferta': codigo_oferta,
                'matriculaAluno': matricula_aluno,
                'codigoCurso': truncar_texto(curso, 30) if curso else None
            })

        return dados_transformados

    # -------------------------------------------------------------------------
    # Importar para Qstione (MERGE)
    # -------------------------------------------------------------------------
    def importar_para_qstione(self, dados_transformados):
        if not self._criar_tabela():
            print("❌ Não foi possível criar/verificar a tabela. Abortando importação.")
            return {
                'total_inseridos': 0,
                'total_atualizados': 0,
                'total_erros': len(dados_transformados),
                'total_processados': len(dados_transformados)
            }

        merge_sql = """
            MERGE INTO imp_011_alunos_ofertas AS target
            USING (VALUES (?, ?, ?)) AS source (codigoOferta, matriculaAluno, codigoCurso)
            ON target.codigoOferta = source.codigoOferta
               AND target.matriculaAluno = source.matriculaAluno
            WHEN MATCHED THEN
                UPDATE SET
                    codigoCurso = source.codigoCurso,
                    data_atualizacao = GETDATE()
            WHEN NOT MATCHED THEN
                INSERT (codigoOferta, matriculaAluno, codigoCurso, data_criacao, data_atualizacao)
                VALUES (source.codigoOferta, source.matriculaAluno, source.codigoCurso, GETDATE(), GETDATE());
        """

        total_inseridos = 0
        total_atualizados = 0
        total_erros = 0

        with get_db_connection(db_path='qstione.db') as conn:
            cursor = conn.cursor()
            for reg in dados_transformados:
                try:
                    cursor.execute("""
                        SELECT 1 FROM imp_011_alunos_ofertas
                        WHERE codigoOferta = ? AND matriculaAluno = ?
                    """, (reg['codigoOferta'], reg['matriculaAluno']))
                    existe = cursor.fetchone()

                    cursor.execute(merge_sql, (
                        reg['codigoOferta'],
                        reg['matriculaAluno'],
                        reg['codigoCurso']
                    ))

                    if existe:
                        total_atualizados += 1
                    else:
                        total_inseridos += 1
                except Exception as e:
                    total_erros += 1
                    print(f"  ✗ Erro ao importar {reg['codigoOferta']} - {reg['matriculaAluno']}: {e}")

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
        print("IMPORTAÇÃO: imp_011_alunos_ofertas")
        print("=" * 70)

        dados_lyceum = self.obter_dados_lyceum()
        print(f"📊 Registros encontrados no Lyceum: {len(dados_lyceum)}")

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

        return dados_transformados


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    importador = ImportadorAlunosOfertas()
    importador.executar_importacao()