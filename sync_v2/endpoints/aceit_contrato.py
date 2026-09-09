"""V2: aceite de contrato. Implementação inicial via adaptador seguro."""
from sync_v2.core.legacy_adapter import run_legacy

def run(**kwargs):
    return run_legacy("sync.sync_ly_aceit_contrato", **kwargs)
