"""V2: turmas.

Preserva a interface incremental validada do sincronizador atual nesta primeira fase.
"""
from sync_v2.core.legacy_adapter import run_legacy

def run(max_pages=None, reset_checkpoint=False, checkpoint_pages=100):
    return run_legacy(
        "sync.sync_ly_turmas",
        max_pages=max_pages,
        reset_checkpoint=reset_checkpoint,
        checkpoint_pages=checkpoint_pages,
    )
