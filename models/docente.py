from core.database import get_db_connection


class DocenteModel:
    TABLE = "LY_DOCENTE"

    @staticmethod
    def create_table():
        with get_db_connection() as conn:
            conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {DocenteModel.TABLE} (
                    cpf TEXT,
                    num_func TEXT,
                    nome TEXT,
                    email TEXT,
                    situacao TEXT,
                    PRIMARY KEY (cpf, num_func)
                )
            """)

    @staticmethod
    def upsert(data: dict):
        with get_db_connection() as conn:
            conn.execute(f"""
                INSERT INTO {DocenteModel.TABLE}
                (cpf, num_func, nome, email, situacao)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(cpf, num_func) DO UPDATE SET
                    nome=excluded.nome,
                    email=excluded.email,
                    situacao=excluded.situacao
            """, (
                data.get("cpf"),
                data.get("numFunc"),
                data.get("nome"),
                data.get("email"),
                data.get("situacao")
            ))
