"""
qstione/diagnosticos/validar_integridade_qstione.py

Diagnóstico pós-carga das tabelas de staging do Qstione.

Não altera dados. Executa somente consultas no banco [qstione].[dbo].
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


CHECKS = [
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

COUNTS = [
    "imp_001_cursos",
    "imp_002_disciplinas",
    "imp_005_ofertas",
    "imp_006_usuarios",
    "imp_007_usuarios_cursos",
    "imp_008_usuarios_disciplinas",
    "imp_009_professores_ofertas",
    "imp_010_alunos",
    "imp_011_alunos_ofertas",
    "imp_013_unidades_avaliacao",
]


def scalar(conn, sql):
    return conn.execute(sql).fetchone()[0]


def main():
    print("=" * 80)
    print("DIAGNÓSTICO DE INTEGRIDADE — STAGING QSTIONE")
    print("=" * 80)

    falhas = 0

    with get_db_connection(database_name="qstione") as conn:
        print("CONTAGENS")
        print("-" * 80)

        for tabela in COUNTS:
            try:
                total = scalar(
                    conn,
                    f"""
                    SELECT COUNT(*)
                    FROM [qstione].[dbo].[{tabela}]
                    """,
                )
                print(f"{tabela:35} {total:>8}")
            except Exception as exc:
                falhas += 1
                print(f"{tabela:35} ERRO: {exc}")

        print()
        print("CURSO 999")
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
                f"codigoCurso={row[0]} | nomeCurso={row[1]} | "
                f"quantPeriodos={row[2]} | "
                f"codigoUnidadeOrganizacional={row[3]}"
            )
        else:
            print("999 não encontrado no staging.")

        print()
        print("INTEGRIDADE REFERENCIAL")
        print("-" * 80)

        for nome, sql in CHECKS:
            total = scalar(conn, sql)
            status = "OK" if total == 0 else "FALHA"
            if total:
                falhas += 1
            print(f"[{status:6}] {nome}: {total}")

    print()
    if falhas:
        print(f"RESULTADO: FALHA — {falhas} verificação(ões).")
        return 1

    print("RESULTADO: OK — staging Qstione sem inconsistências básicas.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
