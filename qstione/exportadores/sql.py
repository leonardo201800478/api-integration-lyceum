"""
Exportação para arquivos SQL
"""

import sqlite3
from datetime import datetime
import os

class ExportadorSQL:
    def __init__(self):
        pass
    
    def exportar_banco_completo(self, caminho_banco, pasta_saida='backups'):
        """
        Exporta backup completo do banco Qstione
        """
        os.makedirs(pasta_saida, exist_ok=True)
        
        data_hora = datetime.now().strftime('%Y%m%d_%H%M%S')
        nome_arquivo = f"qstione_backup_{data_hora}.sql"
        caminho_arquivo = os.path.join(pasta_saida, nome_arquivo)
        
        try:
            conn = sqlite3.connect(caminho_banco)
            cursor = conn.cursor()
            
            with open(caminho_arquivo, 'w', encoding='utf-8') as f:
                # Cabeçalho
                f.write(f"-- Backup do banco Qstione\n")
                f.write(f"-- Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"-- Banco original: {os.path.basename(caminho_banco)}\n")
                f.write(f"\n")
                
                # Obter todas as tabelas
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tabelas = cursor.fetchall()
                
                for tabela_info in tabelas:
                    tabela = tabela_info[0]
                    
                    # Obter estrutura da tabela
                    cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{tabela}'")
                    create_sql = cursor.fetchone()[0]
                    
                    f.write(f"\n-- Tabela: {tabela}\n")
                    f.write(f"{create_sql};\n\n")
                    
                    # Obter dados da tabela
                    cursor.execute(f"SELECT * FROM {tabela}")
                    registros = cursor.fetchall()
                    
                    if registros:
                        f.write(f"-- Dados da tabela {tabela} ({len(registros)} registros)\n")
                        
                        # Obter nomes das colunas
                        cursor.execute(f"PRAGMA table_info({tabela})")
                        colunas_info = cursor.fetchall()
                        colunas = [col[1] for col in colunas_info]
                        
                        for registro in registros:
                            valores_formatados = []
                            for valor in registro:
                                if valor is None:
                                    valores_formatados.append("NULL")
                                elif isinstance(valor, str):
                                    # Escapar aspas simples
                                    valor_escapado = valor.replace("'", "''")
                                    valores_formatados.append(f"'{valor_escapado}'")
                                elif isinstance(valor, (int, float)):
                                    valores_formatados.append(str(valor))
                                else:
                                    valores_formatados.append(f"'{str(valor)}'")
                            
                            colunas_sql = ', '.join(colunas)
                            valores_sql = ', '.join(valores_formatados)
                            
                            f.write(f"INSERT INTO {tabela} ({colunas_sql}) VALUES ({valores_sql});\n")
                    
                    f.write(f"\n")
                
                f.write(f"\n-- Fim do backup\n")
            
            cursor.close()
            conn.close()
            
            print(f"✓ Backup SQL gerado: {caminho_arquivo}")
            return caminho_arquivo
            
        except Exception as e:
            print(f"✗ Erro ao gerar backup SQL: {e}")
            return None