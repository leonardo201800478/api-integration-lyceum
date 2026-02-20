#!/usr/bin/env python
# run_reports.py
import argparse
from pathlib import Path
from core.logger import logger
from reports.generators.gerar_relatorio_alunos import gerar_relatorio_alunos
# futuramente: from reports.generators.gerar_relatorio_turmas import gerar_relatorio_turmas

def main():
    parser = argparse.ArgumentParser(description="Geração de relatórios do Lyceum")
    parser.add_argument(
        '--formats', nargs='+', default=['xml', 'pdf'],
        choices=['xml', 'pdf'], help="Formatos de saída"
    )
    parser.add_argument(
        '--output', type=Path, default=Path('exportacoes/relatorios'),
        help="Diretório de saída"
    )
    parser.add_argument(
        '--reports', nargs='+', default=['alunos'],
        choices=['alunos', 'turmas', 'docentes'],
        help="Relatórios a gerar"
    )
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)

    for relatorio in args.reports:
        if relatorio == 'alunos':
            gerar_relatorio_alunos(args.output, args.formats)
        # Adicione outros elif conforme criar novos relatórios

if __name__ == "__main__":
    main()