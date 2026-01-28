from core.database import get_db_connection


class DisciplinaModel:
    TABLE = "LY_DISCIPLINA"

    @staticmethod
    def create_table():
        with get_db_connection() as conn:
            conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {DisciplinaModel.TABLE} (
                    codigo TEXT PRIMARY KEY,
                    nome TEXT,
                    carga_horaria INTEGER,
                    situacao TEXT
                )
            """)

    @staticmethod
    def upsert(data: dict):
        with get_db_connection() as conn:
            conn.execute(f"""
                INSERT INTO {DisciplinaModel.TABLE}
                (codigo, nome, carga_horaria, situacao)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(codigo) DO UPDATE SET
                    nome=excluded.nome,
                    carga_horaria=excluded.carga_horaria,
                    situacao=excluded.situacao
            """, (
                data.get("disciplina"),
                data.get("nome"),
                data.get("cargaHoraria"),
                data.get("situacao")
            ))
