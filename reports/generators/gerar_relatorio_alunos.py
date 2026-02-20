# reports/generators/gerar_relatorio_alunos.py
from pathlib import Path
import pandas as pd
from core.logger import logger
from reports.exporters.xml_exporter import XMLExporter
from reports.exporters.pdf_exporter import PDFExporter
from reports.queries.relatorio_alunos import get_dados_alunos

def gerar_relatorio_alunos(output_dir: Path, formatos=('xml', 'pdf')):
    """
    Gera relatório de alunos nos formatos especificados.
    """
    logger.info("Iniciando geração de relatório de alunos...")
    try:
        dados = get_dados_alunos()
        if dados.empty:
            logger.warning("Nenhum dado de aluno encontrado.")
            return False

        timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
        sucesso = True

        if 'xml' in formatos:
            xml_path = output_dir / f"alunos_{timestamp}.xml"
            if not XMLExporter().export(dados, xml_path, item_tag="aluno"):
                sucesso = False

        if 'pdf' in formatos:
            pdf_path = output_dir / f"alunos_{timestamp}.pdf"
            exporter = PDFExporter(titulo="Relatório de Alunos", orientacao="retrato")
            if not exporter.export(dados, pdf_path):
                sucesso = False

        logger.info("Geração de relatório de alunos concluída.")
        return sucesso
    except Exception as e:
        logger.error(f"Erro ao gerar relatório de alunos: {e}", exc_info=True)
        return False