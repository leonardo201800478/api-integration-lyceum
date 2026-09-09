"""V2: alunos."""
from sync_v2.core.legacy_adapter import run_legacy

def run(modo="incremental"):
    return run_legacy("sync.sync_ly_alunos", modo=modo)
