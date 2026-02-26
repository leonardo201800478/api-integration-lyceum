# core/database.py

import pyodbc
from contextlib import contextmanager
from core.config import config

# Mapeamento de nomes de bancos (caso o projeto use caminhos)
# Aqui consideramos que o parâmetro db_path (antigo caminho do SQLite) será usado como nome do banco no SQL Server
def _resolve_database_name(db_path: str | None) -> str:
    """
    Retorna o nome do banco SQL Server a partir do db_path (ou do padrão configurado).
    Exemplo: se db_path = 'lyceum.db' -> retorna 'lyceum.db'
    """
    if db_path is not None:
        return db_path
    # Se não for especificado, usa o banco padrão do Lyceum (ou você pode definir outro critério)
    return config.SQL_SERVER_DATABASE_LYCEUM

@contextmanager
def get_db_connection(db_path: str | None = None):
    """
    Retorna uma conexão pyodbc com o SQL Server.
    O parâmetro db_path (antigo) agora é interpretado como o nome do banco de dados.
    Exemplo: get_db_connection('lyceum.db') conecta ao banco 'lyceum.db' no servidor.
    """
    database = _resolve_database_name(db_path)

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
        conn.commit()  # commit automático se não houver exceção
    except Exception:
        conn.rollback()  # em caso de erro, desfaz
        raise
    finally:
        conn.close()

def execute_query(query: str, params: tuple = (), db_path: str | None = None):
    """
    Executa uma query (INSERT, UPDATE, DELETE, CREATE, etc.) e retorna o cursor.
    """
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor

def fetch_all(query: str, params: tuple = (), db_path: str | None = None):
    """
    Executa uma query SELECT e retorna todos os resultados.
    """
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()

def fetch_one(query: str, params: tuple = (), db_path: str | None = None):
    """
    Executa uma query SELECT e retorna um único resultado.
    """
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchone()