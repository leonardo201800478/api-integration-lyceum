#!/usr/bin/env python
import argparse
from pathlib import Path
import webbrowser
from core.logger import logger
from reports.generators.gerar_relatorio_contatos_completo import gerar_relatorio_contatos_completo
from reports.sync_pessoas import verificar_e_sincronizar_pessoas

def obter_filtros_interativo():
    """Captura filtros via input do usuário."""
    print("\n=== Filtros para Relatório de Contatos ===\n")
    
    anos_input = input("Anos (separados por vírgula, ex: 2025,2026): ").strip()
    anos = [int(a.strip()) for a in anos_input.split(',') if a.strip()]
    
    semestres_input = input("Semestres (separados por vírgula, ex: 21,22,23,24): ").strip()
    semestres = [int(s.strip()) for s in semestres_input.split(',') if s.strip()]
    
    unidade = input("Unidade Responsável (ex: 002): ").strip()
    
    curso_input = input("Código do Curso (deixe em branco para todos): ").strip()
    curso = curso_input if curso_input else None
    
    return anos, semestres, unidade, curso

def main():
    parser = argparse.ArgumentParser(description="Geração de relatório de contatos dos alunos")
    parser.add_argument('--anos', nargs='+', type=int, help="Anos (ex: 2025 2026)")
    parser.add_argument('--semestres', nargs='+', type=int, help="Semestres (ex: 21 22 23 24)")
    parser.add_argument('--unidade', type=str, help="Unidade responsável")
    parser.add_argument('--curso', type=str, help="Código do curso (opcional)")
    parser.add_argument('--output', type=Path, default=Path('exportacoes/relatorios'), help="Diretório de saída")
    parser.add_argument('--no-browser', action='store_true', help="Não abrir o navegador automaticamente")
    parser.add_argument('--no-sync', action='store_true', help="Não sincronizar pessoas faltantes")
    
    args = parser.parse_args()
    
    # Se argumentos não foram fornecidos, entra em modo interativo
    if not args.anos or not args.semestres or not args.unidade:
        anos, semestres, unidade, curso = obter_filtros_interativo()
    else:
        anos = args.anos
        semestres = args.semestres
        unidade = args.unidade
        curso = args.curso
    
    # Sincronizar pessoas faltantes (a menos que desabilitado)
    if not args.no_sync:
        verificar_e_sincronizar_pessoas()
    
    # Gerar relatórios nos três formatos
    html_path, xml_path, pdf_path = gerar_relatorio_contatos_completo(
        anos, semestres, unidade, curso, args.output
    )
    
    if html_path and not args.no_browser:
        # Abre o HTML no navegador
        webbrowser.open(html_path.resolve().as_uri())
        logger.info("Navegador aberto com o relatório HTML.")

if __name__ == "__main__":
    main()