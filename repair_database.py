#!/usr/bin/env python3
"""
Script para reparar o banco de dados
"""
import sqlite3
from core.config import config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def repair_aluno_table():
    """Repara a tabela LY_ALUNO"""
    print("Reparando tabela LY_ALUNO...")
    
    conn = sqlite3.connect(config.DB_LYCEUM_PATH)
    cursor = conn.cursor()
    
    try:
        # 1. Verifica se a tabela existe
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='LY_ALUNO'
        """)
        
        if cursor.fetchone() is None:
            print("Tabela LY_ALUNO não existe. Criando...")
            # Aqui você pode copiar o SQL de criação da tabela do aluno.py
            from models.ly_aluno import AlunoModel
            AlunoModel.create_table()
            print("Tabela criada com sucesso!")
            return
        
        # 2. Verifica colunas existentes
        cursor.execute("PRAGMA table_info(LY_ALUNO)")
        colunas = {row[1]: row for row in cursor.fetchall()}
        
        print(f"Colunas existentes: {len(colunas)}")
        for nome in sorted(colunas.keys()):
            print(f"  - {nome}")
        
        # 3. Verifica coluna data_sincronizacao
        if 'data_sincronizacao' not in colunas:
            print("Adicionando coluna data_sincronizacao...")
            cursor.execute("""
                ALTER TABLE LY_ALUNO 
                ADD COLUMN data_sincronizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            """)
            conn.commit()
            print("Coluna adicionada com sucesso!")
        else:
            print("Coluna data_sincronizacao já existe.")
        
        # 4. Verifica se há dados na tabela
        cursor.execute("SELECT COUNT(*) FROM LY_ALUNO")
        total = cursor.fetchone()[0]
        print(f"Total de registros na tabela: {total}")
        
        if total > 0:
            # Mostra alguns exemplos
            cursor.execute("SELECT aluno, nome_compl, curso FROM LY_ALUNO LIMIT 5")
            print("\nPrimeiros 5 registros:")
            for row in cursor.fetchall():
                print(f"  {row[0]}: {row[1]} - Curso: {row[2]}")
        
    except Exception as e:
        print(f"Erro ao reparar tabela: {e}")
        conn.rollback()
    finally:
        conn.close()

def backup_database():
    """Faz backup do banco de dados"""
    import shutil
    from datetime import datetime
    
    backup_file = f"{config.DB_LYCEUM_PATH}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        shutil.copy2(config.DB_LYCEUM_PATH, backup_file)
        print(f"Backup criado: {backup_file}")
    except Exception as e:
        print(f"Erro ao criar backup: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("REPARADOR DE BANCO DE DADOS")
    print("=" * 60)
    
    # Faz backup primeiro
    backup_database()
    
    # Repara a tabela
    repair_aluno_table()
    
    print("\n" + "=" * 60)
    print("REPARO CONCLUIDO!")
    print("=" * 60)