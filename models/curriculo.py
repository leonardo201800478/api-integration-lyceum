from core.database import get_db_connection


class CurriculoModel:
    TABLE = "LY_CURRICULO"

    @staticmethod
    def create_table():
        with get_db_connection() as conn:
            conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {CurriculoModel.TABLE} (
                    codigo TEXT PRIMARY KEY,
                    curso TEXT,
                    nome TEXT,
                    versao TEXT,
                    situacao TEXT
                )
            """)

    @staticmethod
    def upsert(data: dict):
        with get_db_connection() as conn:
            conn.execute(f"""
                INSERT INTO {CurriculoModel.TABLE}
                (codigo, curso, nome, versao, situacao)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(codigo) DO UPDATE SET
                    curso=excluded.curso,
                    nome=excluded.nome,
                    versao=excluded.versao,
                    situacao=excluded.situacao
            """, (
                data.get("curriculo"),
                data.get("curso"),
                data.get("nome"),
                data.get("versao"),
                data.get("situacao")
            ))
