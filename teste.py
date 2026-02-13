import os
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path para importar os módulos do projeto
sys.path.insert(0, str(Path(__file__).parent))

from core.database import get_db_connection
from qstione.config.tabelas import TABELAS_CONFIG

def mapear_tipo_sqlserver(tipo_original: str) -> str:
    """Converte o tipo definido no dicionário para SQL Server."""
    tipo_upper = tipo_original.upper()
    if tipo_upper.startswith('INTEGER'):
        return 'INT'
    # Caso contrário, mantém como está (CHAR, etc.)
    return tipo_original

def gerar_create_table(nome_tabela: str, config: dict) -> str:
    """Gera o comando CREATE TABLE para SQL Server."""
    campos = config['campos']
    colunas = []
    for campo in campos:
        nome = campo['nome_qstione']
        tipo = mapear_tipo_sqlserver(campo['tipo'])
        nullable = "" if campo.get('obrigatorio', False) else "NULL"
        # Se for obrigatório, adiciona NOT NULL
        not_null = "NOT NULL" if campo.get('obrigatorio', False) else ""
        # Monta a definição da coluna
        coluna_def = f"    [{nome}] {tipo} {not_null}".strip()
        colunas.append(coluna_def)

    # Cria a string CREATE TABLE
    create_stmt = f"CREATE TABLE [{nome_tabela}] (\n"
    create_stmt += ",\n".join(colunas)
    create_stmt += "\n);"
    return create_stmt

def criar_tabelas_no_banco():
    """Conecta ao banco qstione.db e executa os CREATE TABLE."""
    # Usa a conexão com o banco 'qstione.db'
    with get_db_connection('qstione.db') as conn:
        cursor = conn.cursor()
        for nome_tabela, config in TABELAS_CONFIG.items():
            print(f"Criando tabela {nome_tabela}...")
            create_sql = gerar_create_table(nome_tabela, config)
            try:
                cursor.execute(create_sql)
                conn.commit()
                print(f"  -> OK")
            except Exception as e:
                print(f"  -> Erro: {e}")
                # Se quiser parar ao primeiro erro, descomente a linha abaixo
                # raise

if __name__ == "__main__":
    criar_tabelas_no_banco()