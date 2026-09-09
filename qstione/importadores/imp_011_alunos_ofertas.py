"""
qstione/importadores/imp_011_alunos_ofertas.py

Importador independente para alunos vinculados às ofertas/turmas.

REGRAS PRINCIPAIS
-----------------

1. A fonte da matrícula é LY_MATRICULA.
2. A oferta é identificada por disciplina, turma, ano e semestre.
3. O codigoOferta é gerado pela mesma função utilizada pelo IMP-005.
4. O curso da oferta é obtido de LY_TURMA.curso.
5. Se LY_TURMA.curso for NULL, vazio ou 999, codigoCurso = 999.
6. Cursos definidos são normalizados pelo mesmo MAPEAMENTO_CURSOS usado
   pelo IMP-002 e IMP-010.
7. Somente matrículas de alunos com sit_aluno = 'Ativo' são importadas.
8. A turma deve atender aos filtros de ano, período, situação e faculdade.
9. A existência da matrícula não depende de docente.
10. A tabela destino é totalmente reconstruída em cada execução.
11. O arquivo pode ser executado diretamente pelo botão Play do VS Code.
12. executar_importacao() é mantido como ponto de entrada compatível com
    qstione.processos.carga_completa.
"""

import os
import sys

ROOT = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
)

if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.database import get_db_connection

from qstione.core.transformacoes import gerar_codigo_oferta, truncar_texto
from qstione.core.validacoes import validar_matricula, validar_codigo_curso
from qstione.config.filtros import (
    ANO_VIGENTE,
    PERIODOS_VIGENTES,
    FACULDADES_INCLUIDAS,
    SITUACAO_TURMA_VALIDA,
)
from qstione.importadores.imp_002_disciplina import MAPEAMENTO_CURSOS


class ImportadorAlunosOfertas:
    """Importa os alunos ativos matriculados nas ofertas vigentes."""

    @staticmethod
    def _curso_unificado(curso) -> str:
        if curso is None:
            return "999"

        curso = str(curso).strip()

        if not curso or curso == "999":
            return "999"

        if curso in MAPEAMENTO_CURSOS:
            return str(MAPEAMENTO_CURSOS[curso][0]).strip()

        return curso

    def _tabela_existe(self, nome_tabela):
        try:
            with get_db_connection(database_name="qstione") as conn:
                return (
                    conn.execute(
                        """
                        SELECT 1
                        FROM INFORMATION_SCHEMA.TABLES
                        WHERE TABLE_NAME = ?
                          AND TABLE_TYPE = 'BASE TABLE'
                        """,
                        (nome_tabela,),
                    ).fetchone()
                    is not None
                )
        except Exception as e:
            print(f"⚠️ Erro ao verificar tabela: {e}")
            return False

    def _indice_existe(self, nome_indice):
        try:
            with get_db_connection(database_name="qstione") as conn:
                return (
                    conn.execute(
                        """
                        SELECT 1
                        FROM sys.indexes
                        WHERE name = ?
                        """,
                        (nome_indice,),
                    ).fetchone()
                    is not None
                )
        except Exception:
            return False

    def _criar_tabela(self):
        if self._tabela_existe("imp_011_alunos_ofertas"):
            self._criar_indices()
            return True

        print("🆕 Criando tabela imp_011_alunos_ofertas...")

        try:
            with get_db_connection(database_name="qstione") as conn:
                conn.execute(
                    """
                    CREATE TABLE imp_011_alunos_ofertas (
                        codigoOferta NVARCHAR(30) NOT NULL,
                        matriculaAluno NVARCHAR(20) NOT NULL,
                        codigoCurso NVARCHAR(30) NOT NULL,
                        data_criacao DATETIME2 DEFAULT GETDATE(),
                        data_atualizacao DATETIME2 DEFAULT GETDATE(),
                        PRIMARY KEY (codigoOferta, matriculaAluno)
                    )
                    """
                )
                conn.commit()

            print("✅ Tabela criada.")
            self._criar_indices()
            return True

        except Exception as e:
            print(f"❌ Erro ao criar tabela: {e}")
            return False

    def _criar_indices(self):
        indices = [
            (
                "idx_alunos_ofertas_matricula",
                """
                CREATE INDEX idx_alunos_ofertas_matricula
                ON imp_011_alunos_ofertas(matriculaAluno)
                """,
            ),
            (
                "idx_alunos_ofertas_curso",
                """
                CREATE INDEX idx_alunos_ofertas_curso
                ON imp_011_alunos_ofertas(codigoCurso)
                """,
            ),
            (
                "idx_alunos_ofertas_oferta",
                """
                CREATE INDEX idx_alunos_ofertas_oferta
                ON imp_011_alunos_ofertas(codigoOferta)
                """,
            ),
        ]

        for nome_indice, sql in indices:
            if self._indice_existe(nome_indice):
                continue

            try:
                with get_db_connection(database_name="qstione") as conn:
                    conn.execute(sql)
                    conn.commit()
            except Exception as e:
                print(f"⚠️ Índice {nome_indice} não pôde ser criado: {e}")

    def obter_dados_lyceum(self):
        """Obtém somente matrículas de alunos com sit_aluno = 'Ativo'."""

        periodos = ",".join("?" for _ in PERIODOS_VIGENTES)
        faculdades = ",".join("?" for _ in FACULDADES_INCLUIDAS)

        query = f"""
            SELECT DISTINCT
                m.aluno,
                m.ano,
                m.semestre,
                m.turma,
                m.disciplina,
                t.curso

            FROM LY_MATRICULA m

            INNER JOIN LY_TURMA t
                ON t.ano = m.ano
               AND t.semestre = m.semestre
               AND t.turma = m.turma
               AND t.disciplina = m.disciplina

            INNER JOIN LY_ALUNO a
                ON a.aluno = m.aluno

            LEFT JOIN LY_CURSO c
                ON c.curso = t.curso

            WHERE a.sit_aluno = 'Ativo'
              AND m.ano = ?
              AND m.semestre IN ({periodos})
              AND t.sit_turma = ?
              AND (
                    t.curso IS NULL
                    OR LTRIM(RTRIM(t.curso)) = ''
                    OR LTRIM(RTRIM(t.curso)) = '999'
                    OR c.faculdade IN ({faculdades})
                  )

            ORDER BY
                m.aluno,
                m.ano,
                m.semestre,
                m.turma,
                m.disciplina
        """

        params = [
            ANO_VIGENTE,
            *PERIODOS_VIGENTES,
            SITUACAO_TURMA_VALIDA,
            *FACULDADES_INCLUIDAS,
        ]

        with get_db_connection() as conn:
            return conn.execute(query, params).fetchall()

    def transformar_dados(self, dados_lyceum):
        unicos = {}
        total_999 = 0
        total_mapeados = 0
        total_invalidos = 0

        for (
            aluno,
            ano,
            semestre,
            turma,
            disciplina,
            curso_turma,
        ) in dados_lyceum:

            if not validar_matricula(aluno):
                total_invalidos += 1
                print(f"⚠️ Matrícula inválida: {aluno}")
                continue

            curso_original = (
                str(curso_turma).strip()
                if curso_turma is not None
                else ""
            )

            curso_unificado = self._curso_unificado(curso_turma)

            if curso_unificado == "999":
                total_999 += 1
            elif curso_original in MAPEAMENTO_CURSOS:
                total_mapeados += 1

            if not validar_codigo_curso(curso_unificado):
                total_invalidos += 1
                print(
                    f"⚠️ Código de curso inválido: {curso_original} → "
                    f"{curso_unificado} | aluno={aluno} | turma={turma} | "
                    f"disciplina={disciplina}"
                )
                continue

            codigo_oferta = truncar_texto(
                gerar_codigo_oferta(
                    disciplina,
                    turma,
                    ano,
                    semestre,
                ),
                30,
            )

            matricula = truncar_texto(str(aluno), 20)
            chave = (codigo_oferta, matricula)

            unicos[chave] = {
                "codigoOferta": codigo_oferta,
                "matriculaAluno": matricula,
                "codigoCurso": truncar_texto(curso_unificado, 30),
            }

        print(f"🔗 Turmas compartilhadas / curso 999: {total_999}")
        print(f"🔄 Cursos normalizados pelo MAPEAMENTO_CURSOS: {total_mapeados}")
        if total_invalidos:
            print(f"⚠️ Registros inválidos ignorados: {total_invalidos}")

        return list(unicos.values())

    def importar_para_qstione(self, dados_transformados):
        if not self._criar_tabela():
            return {
                "total_inseridos": 0,
                "total_atualizados": 0,
                "total_erros": len(dados_transformados),
                "total_processados": len(dados_transformados),
            }

        inseridos = 0
        erros = 0

        try:
            with get_db_connection(database_name="qstione") as conn:
                conn.execute("DELETE FROM imp_011_alunos_ofertas")
                cursor = conn.cursor()

                for reg in dados_transformados:
                    try:
                        cursor.execute(
                            """
                            INSERT INTO imp_011_alunos_ofertas
                            (
                                codigoOferta,
                                matriculaAluno,
                                codigoCurso,
                                data_criacao,
                                data_atualizacao
                            )
                            VALUES (?, ?, ?, GETDATE(), GETDATE())
                            """,
                            (
                                reg["codigoOferta"],
                                reg["matriculaAluno"],
                                reg["codigoCurso"],
                            ),
                        )
                        inseridos += 1
                    except Exception as e:
                        erros += 1
                        print(f"❌ Erro ao inserir aluno/oferta {reg}: {e}")

                conn.commit()

        except Exception as e:
            print(f"❌ Erro na importação: {e}")
            return {
                "total_inseridos": inseridos,
                "total_atualizados": 0,
                "total_erros": erros + 1,
                "total_processados": len(dados_transformados),
            }

        print(f"📈 Inseridos: {inseridos} | Erros: {erros}")

        return {
            "total_inseridos": inseridos,
            "total_atualizados": 0,
            "total_erros": erros,
            "total_processados": len(dados_transformados),
        }

    def executar(self):
        print("=" * 70)
        print("IMPORTAÇÃO: imp_011_alunos_ofertas")
        print("=" * 70)
        print(f"📅 Ano: {ANO_VIGENTE}")
        print(f"📅 Períodos: {PERIODOS_VIGENTES}")
        print(f"🏫 Faculdades: {FACULDADES_INCLUIDAS}")
        print(f"📚 Situação: {SITUACAO_TURMA_VALIDA}")
        print("👤 Alunos elegíveis: LY_ALUNO.sit_aluno = 'Ativo'")
        print("🔗 Curso da oferta: LY_TURMA.curso")

        dados = self.obter_dados_lyceum()
        print(f"📊 Registros encontrados: {len(dados)}")

        transformados = self.transformar_dados(dados)
        print(f"✅ Registros únicos: {len(transformados)}")

        return self.importar_para_qstione(transformados)

    def executar_importacao(self):
        """
        Ponto de entrada utilizado pela carga completa.

        Mantém compatibilidade com qstione.processos.carga_completa,
        que executa os importadores através deste método.
        """
        return self.executar()


if __name__ == "__main__":
    resultado = ImportadorAlunosOfertas().executar_importacao()
    print("=" * 70)
    print("RESULTADO FINAL")
    print("=" * 70)
    for chave, valor in resultado.items():
        print(f"{chave}: {valor}")
