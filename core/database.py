import sqlite3
from datetime import datetime
from contextlib import contextmanager

@contextmanager
def get_db_connection(db_name="dados_unifoa.db"):
    """Context manager para conexão com SQLite"""
    conn = sqlite3.connect(db_name)
    conn.row_factory = sqlite3.Row  # Para retornar dicionários
    try:
        yield conn
    finally:
        conn.close()

def execute_query(query, params=None, db_name="dados_unifoa.db"):
    """Executa uma query e retorna resultados"""
    with get_db_connection(db_name) as conn:
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        conn.commit()
        return cursor

def execute_many(query, params_list, db_name="dados_unifoa.db"):
    """Executa query com múltiplos parâmetros"""
    with get_db_connection(db_name) as conn:
        cursor = conn.cursor()
        cursor.executemany(query, params_list)
        conn.commit()
        return cursor

def fetch_all(query, params=None, db_name="dados_unifoa.db"):
    """Busca todos os resultados"""
    with get_db_connection(db_name) as conn:
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return cursor.fetchall()

def fetch_one(query, params=None, db_name="dados_unifoa.db"):
    """Busca um único resultado"""
    with get_db_connection(db_name) as conn:
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return cursor.fetchone()