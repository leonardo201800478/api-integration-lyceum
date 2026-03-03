# reports/sync_pessoas.py

import sys
from pathlib import Path

# Garante que o diretório raiz seja encontrado
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database import get_db_connection
from core.logger import logger
import subprocess

def verificar_e_sincronizar_pessoas():
    """Verifica pessoas em LY_ALUNO não existentes em LY_PESSOA e sincroniza."""
    logger.info("Verificando pessoas faltantes na tabela LY_PESSOA...")
    
    query_faltantes = """
        SELECT DISTINCT A.pessoa
        FROM LY_ALUNO A
        LEFT JOIN LY_PESSOA P ON A.pessoa = P.pessoa
        WHERE P.pessoa IS NULL AND A.pessoa IS NOT NULL
    """
    
    with get_db_connection(database_name='lyceum.db') as conn:
        cursor = conn.cursor()
        cursor.execute(query_faltantes)
        faltantes = [row[0] for row in cursor.fetchall()]
    
    if not faltantes:
        logger.info("Nenhuma pessoa faltante encontrada.")
        return
    
    logger.info(f"Encontradas {len(faltantes)} pessoas faltantes. Iniciando sincronização...")
    
    sync_script = Path(__file__).parent.parent / "sync" / "sync_ly_pessoa_by_id.py"
    
    if not sync_script.exists():
        logger.error(f"Script de sync não encontrado: {sync_script}")
        return
    
    for pessoa_id in faltantes:
        logger.info(f"Sincronizando pessoa ID: {pessoa_id}")
        try:
            subprocess.run([sys.executable, str(sync_script), str(pessoa_id)], check=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Erro ao sincronizar pessoa {pessoa_id}: {e}")

if __name__ == "__main__":
    verificar_e_sincronizar_pessoas()