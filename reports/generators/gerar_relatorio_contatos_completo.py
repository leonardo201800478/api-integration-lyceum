from pathlib import Path
import pandas as pd
from core.logger import logger
from reports.exporters.excel_exporter import ExcelExporter  # Novo
from reports.exporters.pdf_exporter import PDFExporter
from reports.queries.relatorio_contatos_filtros import get_dados_contatos_filtros

def gerar_relatorio_contatos_completo(anos, semestres, unidade, curso, output_dir):
    """
    Gera relatório de contatos nos formatos HTML, Excel e PDF.
    """
    logger.info("Iniciando geração completa do relatório de contatos...")
    
    dados = get_dados_contatos_filtros(anos, semestres, unidade, curso)
    
    if dados.empty:
        logger.warning("Nenhum dado encontrado para os filtros.")
        return None, None, None
    
    timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
    base_filename = f"contatos_{timestamp}"
    
    # --- HTML (já existente) ---
    html_path = output_dir / f"{base_filename}.html"
    gerar_html(dados, html_path, anos, semestres, unidade, curso)
    
    # --- Excel (substitui XML) ---
    excel_path = output_dir / f"{base_filename}.xlsx"
    ExcelExporter().export(dados, excel_path)
    
    # --- PDF (melhorado) ---
    pdf_path = output_dir / f"{base_filename}.pdf"
    
    # Selecionar e renomear colunas
    colunas_exibir = {
        'cod_aluno': 'Cód. Aluno',
        'nome_aluno': 'Nome',
        'nome_curso': 'Curso',
        'ddd_fone_celular': 'DDD Cel',
        'celular': 'Celular',
        'ddd_fone': 'DDD Res',
        'fone': 'Telefone',
        'e_mail': 'E-mail',
        'sit_matricula': 'Sit. Matr.',
        'sit_aluno': 'Sit. Aluno'
    }
    colunas_existentes = {k: v for k, v in colunas_exibir.items() if k in dados.columns}
    dados_pdf = dados[list(colunas_existentes.keys())].rename(columns=colunas_existentes)
    
    # Subtítulo
    subtitulo = f"Filtros: Anos {anos} | Semestres {semestres} | Unidade {unidade} | Curso: {curso if curso else 'Todos'}"
    
    PDFExporter(
        titulo="Relatório de Contatos de Alunos",
        subtitulo=subtitulo,
        orientacao="paisagem",
        font_size=6  # Fonte menor para caber mais conteúdo
    ).export(dados_pdf, pdf_path)
    
    logger.info(f"Relatórios gerados: {html_path}, {excel_path}, {pdf_path}")
    return html_path, excel_path, pdf_path

def gerar_html(dados, output_path, anos, semestres, unidade, curso):
    """Gera arquivo HTML com os dados agrupados por curso."""
    html_content = []
    html_content.append(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Relatório de Contatos dos Alunos</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1 {{ color: #2c3e50; }}
            h2 {{ color: #2980b9; margin-top: 30px; }}
            table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
        </style>
    </head>
    <body>
        <h1>Relatório de Contatos dos Alunos</h1>
        <p>Filtros aplicados: 
            Anos: {anos} | 
            Semestres: {semestres} | 
            Unidade: {unidade} | 
            Curso: {curso if curso else 'Todos'}
        </p>
    """)
    
    for nome_curso, grupo in dados.groupby('nome_curso'):
        html_content.append(f"<h2>Curso: {nome_curso}</h2>")
        html_content.append("""
        <table>
            <tr>
                <th>Cód. Aluno</th>
                <th>Nome</th>
                <th>DDD Celular</th>
                <th>Celular</th>
                <th>DDD Fone</th>
                <th>Fone</th>
                <th>E-mail</th>
                <th>Situação</th>
            </tr>
        """)
        for _, row in grupo.iterrows():
            html_content.append(f"""
            <tr>
                <td>{row['cod_aluno']}</td>
                <td>{row['nome_aluno']}</td>
                <td>{row['ddd_fone_celular']}</td>
                <td>{row['celular']}</td>
                <td>{row['ddd_fone']}</td>
                <td>{row['fone']}</td>
                <td>{row['e_mail']}</td>
                <td>{row['sit_aluno']}</td>
            </tr>
            """)
        html_content.append("</table>")
    
    html_content.append("</body></html>")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(html_content))