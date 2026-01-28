from core.database import get_db_connection


class TurmaModel:
    TABLE = "LY_TURMA"

    @staticmethod
    def create_table():
        with get_db_connection() as conn:
            conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {TurmaModel.TABLE} (
                    ano TEXT,
                    semestre TEXT,
                    disciplina TEXT,
                    turma TEXT,
                    situacao TEXT,
                    PRIMARY KEY (ano, semestre, disciplina, turma)
                )
            """)

    @staticmethod
    def upsert(data: dict):
        with get_db_connection() as conn:
            conn.execute(f"""
                INSERT INTO {TurmaModel.TABLE}
                (ano, semestre, disciplina, turma, situacao)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(ano, semestre, disciplina, turma) DO UPDATE SET
                    situacao=excluded.situacao
            """, (
                data.get("ano"),
                data.get("semestre"),
                data.get("disciplina"),
                data.get("turma"),
                data.get("situacao")
            ))
