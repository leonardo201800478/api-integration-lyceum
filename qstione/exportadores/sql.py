# qstione/exportadores/sql.py

from core.database import get_db_connection
from datetime import datetime
import os

class ExportadorSQL:
    def exportar_banco_completo(self, pasta_saida='backups'):
        os.makedirs(pasta_saida, exist_ok=True)
        data_hora = datetime.now().strftime('%Y%m%d_%H%M%S')
        nome_arquivo = f"qstione_backup_{data_hora}.sql"
        caminho_arquivo = os.path.join(pasta_saida, nome_arquivo)

        try:
            with get_db_connection(database_name='qstione.db') as conn:
                cursor = conn.cursor()
                with open(caminho_arquivo, 'w', encoding='utf-8') as f:
                    f.write(f"-- Backup do banco Qstione (SQL Server)\n")
                    f.write(f"-- Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

                    # Listar tabelas
                    cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")
                    tabelas = [row[0] for row in cursor.fetchall()]

                    for tabela in tabelas:
                        # Obter colunas
                        cursor.execute("""
                            SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
                            WHERE TABLE_NAME = ?
                            ORDER BY ORDINAL_POSITION
                        """, (tabela,))
                        colunas = [row[0] for row in cursor.fetchall()]
                        if not colunas:
                            continue

                        # Obter dados
                        cursor.execute(f"SELECT * FROM {tabela}")
                        registros = cursor.fetchall()
                        f.write(f"\n-- Tabela: {tabela} ({len(registros)} registros)\n")

                        for registro in registros:
                            valores = []
                            for valor in registro:
                                if valor is None:
                                    valores.append("NULL")
                                elif isinstance(valor, str):
                                    # Escapar aspas simples
                                    valor_escapado = valor.replace("'", "''")
                                    valores.append(f"'{valor_escapado}'")
                                elif isinstance(valor, (int, float)):
                                    valores.append(str(valor))
                                elif isinstance(valor, datetime):
                                    valores.append(f"'{valor.isoformat()}'")
                                else:
                                    valores.append(f"'{str(valor)}'")
                            colunas_sql = ', '.join(colunas)
                            valores_sql = ', '.join(valores)
                            f.write(f"INSERT INTO {tabela} ({colunas_sql}) VALUES ({valores_sql});\n")

                    f.write("\n-- Fim do backup\n")
            print(f"✓ Backup SQL gerado: {caminho_arquivo}")
            return caminho_arquivo
        except Exception as e:
            print(f"✗ Erro ao gerar backup SQL: {e}")
            return None