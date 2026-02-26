# lxp/main.py
import sys
from pathlib import Path
# Adiciona a raiz do projeto ao path para permitir imports absolutos
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.logger import logger
from lxp.exportadores import exp_001_cursos, exp_002_curriculum, exp_003_enrollment, exp_004_desenturmar_alunos_cursos_livres_ead
import sync.sync_ly_alunos


EXPORTADORES = [
    ("Cursos", exp_001_cursos),
    ("Currículos", exp_002_curriculum),
    ("Enturmações", exp_003_enrollment),
    ("Desenturmações (delete)", exp_004_desenturmar_alunos_cursos_livres_ead),
]

def run() -> bool:
    logger.info("=== INÍCIO DA EXPORTAÇÃO LXP ===")
    
    # Etapa 1: Sincronizar alunos via API Lyceum
    logger.info("Executando sincronização de alunos (sync_ly_alunos)...")
    try:
        if not sync.sync_ly_alunos.run():
            logger.error("Sincronização de alunos falhou. Abortando exportação LXP.")
            return False
        logger.info("Sincronização de alunos concluída com sucesso.")
    except Exception as e:
        logger.exception(f"Erro crítico ao executar sync_ly_alunos: {e}")
        return False

    # Etapa 2: Executar os exportadores LXP
    sucesso = True
    for nome, modulo in EXPORTADORES:
        try:
            logger.info(f"Executando exportador: {nome}")
            if not modulo.run():
                logger.error(f"Exportador {nome} falhou.")
                sucesso = False
        except Exception as e:
            logger.exception(f"Erro crítico no exportador {nome}: {e}")
            sucesso = False

    if sucesso:
        logger.info("=== EXPORTAÇÃO LXP CONCLUÍDA ===")
    else:
        logger.error("=== EXPORTAÇÃO LXP FINALIZOU COM FALHAS ===")
    return sucesso

if __name__ == "__main__":
    sys.exit(0 if run() else 1)