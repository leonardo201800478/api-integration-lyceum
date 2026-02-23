from core.database import get_db_connection

try:
    with get_db_connection(db_path='qstione.db') as conn:
        print("✅ Conexão com SQL Server (qstione.db) OK")
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        print("✅ Consulta executada")
except Exception as e:
    print(f"❌ Erro: {e}")