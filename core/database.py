# core/database.py

import pyodbc
from contextlib import contextmanager
from core.config import config

def _resolve_database_name(database_name: str | None) -> str:
    """Retorna o nome do banco SQL Server a partir do nome informado."""
    if database_name is not None:
        return database_name
    return config.SQL_SERVER_DATABASE_LYCEUM

@contextmanager
def get_db_connection(database_name: str | None = None):
    """
    Retorna uma conexão pyodbc com o SQL Server.
    :param database_name: Nome do banco de dados (ex: 'lyceum.tbl', 'qstione.tbl').
    """
    database = _resolve_database_name(database_name)

    connection_string = (
        f"DRIVER={config.SQL_SERVER_DRIVER};"
        f"SERVER={config.SQL_SERVER_HOST},{config.SQL_SERVER_PORT};"
        f"DATABASE={database};"
        f"UID={config.SQL_SERVER_USER};"
        f"PWD={config.SQL_SERVER_PASSWORD};"
        "TrustServerCertificate=yes;"
    )

    conn = pyodbc.connect(connection_string)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def execute_query(query: str, params: tuple = (), database_name: str | None = None):
    with get_db_connection(database_name) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor

def fetch_all(query: str, params: tuple = (), database_name: str | None = None):
    with get_db_connection(database_name) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()

def fetch_one(query: str, params: tuple = (), database_name: str | None = None):
    with get_db_connection(database_name) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchone()