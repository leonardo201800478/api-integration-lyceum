"""
qstione/diagnosticos/validar_integridade_carga.py

Diagnóstico pós-carga do conjunto de importadores Qstione.

Objetivo
--------
Validar a integridade referencial do staging local depois da execução da
carga completa, com atenção especial ao curso técnico 999 / Turma Compartilhada.

O diagnóstico NÃO altera dados.
Pode ser executado diretamente pelo botão Play do VS Code.
"""

import os
import sys


ROOT = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.database import get_db_connection
from qstione.config.filtros import (
    ANO_VIGENTE,
    PERIODOS_VIGENTES,
    SITUACAO_TURMA_VALIDA,
)


DB = "qstione"


QUERIES = {
    "imp_001_cursos": """
        SELECT COUNT(*)
        FROM [qstione].[dbo].[imp_001_cursos]
    """,
    "curso_999": """
        SELECT COUNT(*)
        FROM [qstione].[dbo].[imp_001_cursos]
        WHERE codigoCurso = '999'
    """,
    "imp_002_disciplinas": """
        SELECT COUNT(*)
        FROM [qstione].[dbo].[imp_002_disciplinas]
    """,
    "imp_005_ofertas": """
        SELECT COUNT(*)
        FROM [qstione].[dbo].[imp_005_ofertas]
    """,
    "imp_006_usuarios": """
        SELECT COUNT(*)
        FROM [qstione].[dbo].[imp_006_usuarios]
    """,
    "imp_007_usuarios_cursos": """
        SELECT COUNT(*)
        FROM [qstione].[dbo].[imp_007_usuarios_cursos]
    """,
    "imp_008_usuarios_disciplinas": """
        SELECT COUNT(*)
        FROM [qstione].[dbo].[imp_008_usuarios_disciplinas]
    """,
    "imp_009_professores_ofertas": """
        SELECT COUNT(*)
        FROM [qstione].[dbo].[imp_009_professores_ofertas]
    """,
    "imp_010_alunos": """
        SELECT COUNT(*)
        FROM [qstione].[dbo].[imp_010_alunos]
    """,
    "imp_011_alunos_ofertas": """
        SELECT COUNT(*)
        FROM [qstione].[dbo].[imp_011_alunos_ofertas]
    """,
    "imp_013_unidades_avaliacao": """
        SELECT COUNT(*)
        FROM [qstione].[dbo].[imp_013_unidades_avaliacao]
    """,
}


REFERENTIAL_CHECKS = [
    (
        "IMP-010 com curso inexistente",
        """
        SELECT COUNT(*)
        FROM [qstione].[dbo].[imp_010_alunos] a
        LEFT JOIN [qstione].[dbo].[imp_001_cursos] c
          ON c.codigoCurso = a.codigoCurso
        WHERE c.codigoCurso IS NULL
        """,
    ),
    (
        "IMP-011 com curso inexistente",
        """
        SELECT COUNT(*)
        FROM [qstione].[dbo].[imp_011_alunos_ofertas] a
        LEFT JOIN [qstione].[dbo].[imp_001_cursos] c
          ON c.codigoCurso = a.codigoCurso
        WHERE c.codigoCurso IS NULL
        """,
    ),
    (
        "IMP-011 com oferta inexistente",
        """
        SELECT COUNT(*)
        FROM [qstione].[dbo].[imp_011_alunos_ofertas] a
        LEFT JOIN [qstione].[dbo].[imp_005_ofertas] o
          ON o.codigoOferta = a.codigoOferta
        WHERE o.codigoOferta IS NULL
        """,
    ),
    (
        "IMP-009 com oferta inexistente",
        """
        SELECT COUNT(*)
        FROM [qstione].[dbo].[imp_009_professores_ofertas] p
        LEFT JOIN [qstione].[dbo].[imp_005_ofertas] o
          ON o.codigoOferta = p.codigoOferta
        WHERE o.codigoOferta IS NULL
        """,
    ),
    (
        "IMP-007 com curso inexistente",
        """
        SELECT COUNT(*)
        FROM [qstione].[dbo].[imp_007_usuarios_cursos] u
        LEFT JOIN [qstione].[dbo].[imp_001_cursos] c
          ON c.codigoCurso = u.codigoCurso
        WHERE c.codigoCurso IS NULL
        """,
    ),
]


def scalar(conn, sql, params=()):
    return conn.execute(sql, params).fetchone()[0]


def main():
    print("=" * 80)
    print("DIAGNÓSTICO DE INTEGRIDADE — CARGA QSTIONE")
    print("=" * 80)
    print(f"ANO_VIGENTE={ANO_VIGENTE}")
    print(f"PERIODOS_VIGENTES={PERIODOS_VIGENTES}")
    print(f"SITUACAO_TURMA_VALIDA={SITUACAO_TURMA_VALIDA}")
    print()

    with get_db_connection(database_name=DB) as conn:
        print("CONTAGENS")
        print("-" * 80)

        for nome, sql in QUERIES.items():
            try:
                total = scalar(conn, sql)
                print(f"{nome:35} {total:>8}")
            except Exception as exc:
                print(f"{nome:35} ERRO: {exc}")

        print()
        print("CURSO SINTÉTICO 999")
        print("-" * 80)

        row = conn.execute(
            """
            SELECT
                [codigoCurso],
                [nomeCurso],
                [quantPeriodos],
                [codigoUnidadeOrganizacional]
            FROM [qstione].[dbo].[imp_001_cursos]
            WHERE [codigoCurso] = '999'
            """
        ).fetchone()

        if row:
            print(
                f"999 | nome={row[1]} | quantPeriodos={row[2]} "
                f"| unidade={row[3]}"
            )
        else:
            print("ERRO: curso 999 não está cadastrado no staging Qstione.")

        print()
        print("INTEGRIDADE REFERENCIAL")
        print("-" * 80)

        falhas = 0
        for nome, sql in REFERENTIAL_CHECKS:
            total = scalar(conn, sql)
            status = "OK" if total == 0 else "FALHA"
            if total:
                falhas += 1
            print(f"[{status:6}] {nome}: {total}")

        print()
        print("TURMAS COMPARTILHADAS NO LYCEUM")
        print("-" * 80)

        periodos = ",".join("?" for _ in PERIODOS_VIGENTES)
        total_compartilhadas = scalar(
            conn,
            f"""
            SELECT COUNT(*)
            FROM [LY_TURMA] t
            WHERE t.ano = ?
              AND t.semestre IN ({periodos})
              AND t.sit_turma = ?
              AND t.disciplina IS NOT NULL
              AND LTRIM(RTRIM(CAST(t.disciplina AS NVARCHAR(100)))) <> ''
              AND (
                    t.curso IS NULL
                    OR LTRIM(RTRIM(CAST(t.curso AS NVARCHAR(30)))) = ''
                    OR LTRIM(RTRIM(CAST(t.curso AS NVARCHAR(30)))) = '999'
                  )
            """,
            [ANO_VIGENTE, *PERIODOS_VIGENTES, SITUACAO_TURMA_VALIDA],
        )

        print(f"Turmas compartilhadas válidas: {total_compartilhadas}")

        if total_compartilhadas > 0 and row is None:
            falhas += 1
            print("[FALHA] Existem turmas compartilhadas, mas o curso 999 não existe.")
        elif total_compartilhadas == 0 and row is not None:
            print("[INFO] 999 existe embora não haja turma compartilhada no período atual.")

        print()
        if falhas:
            print(f"RESULTADO: FALHA — {falhas} verificação(ões) precisam de atenção.")
            return 1

        print("RESULTADO: OK — integridade básica da carga confirmada.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
