from core.database import get_db_connection


class TurmaDocenteModel:
    TABLE = "LY_TURMA_DOCENTE"

    @staticmethod
    def create_table():
        with get_db_connection() as conn:
            conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {TurmaDocenteModel.TABLE} (
                    chave TEXT PRIMARY KEY,
                    cpf TEXT,
                    num_func TEXT,
                    ano TEXT,
                    semestre TEXT,
                    disciplina TEXT,
                    turma TEXT
                )
            """)

    @staticmethod
    def upsert(data: dict):
        with get_db_connection() as conn:
            conn.execute(f"""
                INSERT INTO {TurmaDocenteModel.TABLE}
                (chave, cpf, num_func, ano, semestre, disciplina, turma)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(chave) DO UPDATE SET
                    cpf=excluded.cpf,
                    num_func=excluded.num_func,
                    ano=excluded.ano,
                    semestre=excluded.semestre,
                    disciplina=excluded.disciplina,
                    turma=excluded.turma
            """, (
                data.get("chave"),
                data.get("cpf"),
                data.get("numFunc"),
                data.get("ano"),
                data.get("semestre"),
                data.get("disciplina"),
                data.get("turma")
            ))
