from core.database import get_db_connection
from core.logger import logger
import subprocess
import sys
from pathlib import Path

def verificar_e_sincronizar_pessoas():
    """
    Verifica se existem pessoas em LY_ALUNO que não estão em LY_PESSOA.
    Se houver, executa sync_ly_pessoa_by_id.py para cada ID faltante.
    """
    logger.info("Verificando pessoas faltantes na tabela LY_PESSOA...")
    
    query_faltantes = """
        SELECT DISTINCT A.pessoa
        FROM LY_ALUNO A
        LEFT JOIN LY_PESSOA P ON A.pessoa = P.pessoa
        WHERE P.pessoa IS NULL AND A.pessoa IS NOT NULL
    """
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query_faltantes)
        faltantes = [row[0] for row in cursor.fetchall()]
    
    if not faltantes:
        logger.info("Nenhuma pessoa faltante encontrada.")
        return
    
    logger.info(f"Encontradas {len(faltantes)} pessoas faltantes. Iniciando sincronização...")
    
    # Caminho para o script de sync (ajuste se necessário)
    sync_script = Path(__file__).parent.parent / "sync" / "sync_ly_pessoa_by_id.py"
    
    if not sync_script.exists():
        logger.error(f"Script de sync não encontrado: {sync_script}")
        return
    
    for pessoa_id in faltantes:
        logger.info(f"Sincronizando pessoa ID: {pessoa_id}")
        try:
            # Executa o script passando o ID como argumento
            subprocess.run([sys.executable, str(sync_script), str(pessoa_id)], check=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Erro ao sincronizar pessoa {pessoa_id}: {e}")