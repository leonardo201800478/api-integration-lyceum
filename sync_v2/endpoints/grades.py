"""V2: grades."""
from sync_v2.core.legacy_adapter import run_legacy

def run():
    return run_legacy("sync.sync_ly_grades")
