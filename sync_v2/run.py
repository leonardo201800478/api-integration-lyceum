"""Runner da Sync V2.

Fase 1: executa a mesma lógica já validada, porém através da interface V2.
Fase 2: cada endpoint será migrado para coleta otimizada, checkpoints e
sincronização incremental próprios sem alterar a camada Qstione.
"""

from __future__ import annotations

import argparse
import logging
import time

from sync_v2.endpoints import (
    aceit_contrato, alunos, coordenacoes, curriculos, cursos, disciplinas,
    docentes, grades, matriculas, pessoas, pessoas_pendentes, provas,
    provas_disciplinas, turma_docentes, turmas,
)

STAGES = [
    ("pessoas", pessoas.run),
    ("pessoas_pendentes", pessoas_pendentes.run),
    ("alunos", alunos.run),
    ("cursos", cursos.run),
    ("curriculos", curriculos.run),
    ("disciplinas", disciplinas.run),
    ("docentes", docentes.run),
    ("coordenacoes", coordenacoes.run),
    ("grades", grades.run),
    ("turmas", turmas.run),
    ("turma_docentes", turma_docentes.run),
    ("matriculas", matriculas.run),
    ("provas", provas.run),
    ("provas_disciplinas", provas_disciplinas.run),
    ("aceit_contrato", aceit_contrato.run),
]


def run(selected=None, alunos_modo="incremental") -> bool:
    """Executa as etapas V2 selecionadas; por padrão executa todas."""
    wanted = set(selected or [name for name, _ in STAGES])
    inicio = time.time()
    logging.info("=" * 90)
    logging.info("SYNC LYCEUM V2 — execução controlada")
    logging.info("Implementação V2 em paralelo; legado preservado")
    logging.info("=" * 90)

    for name, fn in STAGES:
        if name not in wanted:
            continue
        logging.info("[V2] INÍCIO %s", name)
        try:
            result = fn(alunos_modo) if name == "alunos" else fn()
        except Exception:
            logging.exception("[V2] FALHA %s", name)
            return False
        if result is False:
            logging.error("[V2] FALHA %s: endpoint retornou False", name)
            return False
        logging.info("[V2] FIM %s", name)

    logging.info("SYNC LYCEUM V2 concluída em %.2fs", time.time() - inicio)
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Runner da sincronização Lyceum V2")
    parser.add_argument("--only", nargs="+", choices=[n for n, _ in STAGES])
    parser.add_argument("--alunos-modo", choices=["incremental", "completo"], default="incremental")
    args = parser.parse_args()
    raise SystemExit(0 if run(args.only, args.alunos_modo) else 1)
