import sqlite3
from contextlib import contextmanager
from core.config import config


@contextmanager
def get_db_connection(db_path: str | None = None):
    """
    Retorna conexão SQLite com commit automático
    """
    path = db_path or config.DB_LYCEUM_PATH
    conn = sqlite3.connect(path)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()
