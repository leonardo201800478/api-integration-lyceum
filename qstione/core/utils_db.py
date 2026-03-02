# qstione/core/utils_db.py

def tabela_existe(conn, nome_tabela):
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = ? AND TABLE_TYPE = 'BASE TABLE'", (nome_tabela,))
    return cursor.fetchone() is not None

def criar_tabela_se_nao_existe(conn, create_sql, nome_tabela):
    if not tabela_existe(conn, nome_tabela):
        conn.execute(create_sql)
        conn.commit()

def indice_existe(conn, nome_indice):
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM sys.indexes WHERE name = ?", (nome_indice,))
    return cursor.fetchone() is not None