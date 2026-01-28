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

def execute_query(query: str, params: tuple = (), db_path: str | None = None):
    """
    Executa uma query (INSERT, UPDATE, DELETE, CREATE, etc.)
    """
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor

def fetch_all(query: str, params: tuple = (), db_path: str | None = None):
    """
    Executa uma query SELECT e retorna todos os resultados
    """
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()

def fetch_one(query: str, params: tuple = (), db_path: str | None = None):
    """
    Executa uma query SELECT e retorna um único resultado
    """
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchone()