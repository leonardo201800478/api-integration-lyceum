# reports/exporters/pdf_exporter.py

from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
import pandas as pd
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class PDFExporter:
    """
    Exporta DataFrame para PDF mantendo layout semelhante ao HTML:

    - Título principal
    - Parágrafo de filtros
    - Separação por curso
    - Uma tabela por curso
    - Cabeçalho estilizado
    - Linhas alternadas
    """

    def __init__(
        self,
        titulo: str = "Relatório",
        subtitulo: str = "",
        orientacao: str = "paisagem",
        font_size: int = 8
    ):
        self.titulo = titulo
        self.subtitulo = subtitulo
        self.pagesize = landscape(A4) if orientacao == "paisagem" else A4
        self.font_size = font_size

        self.styles = self._build_styles()

    # ==========================================================
    # Estilos
    # ==========================================================

    def _build_styles(self):
        """
        Cria e retorna todos os estilos reutilizáveis do documento.
        Evita recriação a cada célula.
        """
        base = getSampleStyleSheet()

        styles = {
            "title": base["Title"],
            "filters": ParagraphStyle(
                "Filters",
                parent=base["Normal"],
                fontSize=9,
                textColor=colors.black,
                spaceAfter=10
            ),
            "course": ParagraphStyle(
                "Course",
                parent=base["Heading2"],
                fontSize=11,
                textColor=colors.HexColor("#2980b9"),
                spaceBefore=12,
                spaceAfter=6
            ),
            "cell": ParagraphStyle(
                "Cell",
                parent=base["Normal"],
                fontSize=self.font_size,
                leading=self.font_size + 2,
                wordWrap="CJK"
            ),
            "header_cell": ParagraphStyle(
                "HeaderCell",
                parent=base["Normal"],
                fontSize=self.font_size + 1,
                textColor=colors.white,
                leading=self.font_size + 2
            )
        }

        return styles

    # ==========================================================
    # Utilitário
    # ==========================================================

    def _p(self, text, style_key="cell"):
        """
        Converte texto para Paragraph usando estilo configurado.
        """
        return Paragraph(str(text) if pd.notna(text) else "", self.styles[style_key])

    # ==========================================================
    # Tabela
    # ==========================================================

    def _build_table(self, df: pd.DataFrame) -> Table:
        """
        Cria uma tabela formatada com:
        - Cabeçalho cinza
        - Linhas alternadas
        - Bordas finas
        - Largura proporcional
        """

        colunas = list(df.columns)

        # Cabeçalho
        data = [[self._p(col, "header_cell") for col in colunas]]

        # Linhas
        for _, row in df.iterrows():
            data.append([self._p(row[col]) for col in colunas])

        # Cálculo de largura proporcional
        total_width = self.pagesize[0] - (2 * cm)
        col_width = total_width / len(colunas)
        col_widths = [col_width] * len(colunas)

        tabela = Table(
            data,
            colWidths=col_widths,
            repeatRows=1
        )

        tabela.setStyle(TableStyle([
            # Cabeçalho
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),

            # Corpo
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),

            # Linhas alternadas
            ('ROWBACKGROUNDS', (0, 1), (-1, -1),
             [colors.white, colors.HexColor("#f9f9f9")]),

            # Bordas
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),

            # Padding semelhante ao HTML (8px aprox.)
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))

        return tabela

    # ==========================================================
    # Exportação
    # ==========================================================

    def export(
        self,
        data: pd.DataFrame,
        output_path: Path,
        curso: str | None = None,
        filtros_texto: str = ""
    ) -> bool:
        """
        Gera o PDF.

        Parâmetros:
        ----------
        data : DataFrame
            Dados completos contendo coluna 'Curso'
        output_path : Path
            Caminho de saída do PDF
        curso : str | None
            Se informado, filtra apenas esse curso
        filtros_texto : str
            Texto descritivo dos filtros aplicados
        """

        try:
            doc = SimpleDocTemplate(
                str(output_path),
                pagesize=self.pagesize,
                rightMargin=1 * cm,
                leftMargin=1 * cm,
                topMargin=1.5 * cm,
                bottomMargin=1 * cm,
            )

            story = []

            # Título
            story.append(Paragraph(self.titulo, self.styles["title"]))
            story.append(Spacer(1, 0.4 * cm))

            # Filtros
            if filtros_texto:
                story.append(Paragraph(filtros_texto, self.styles["filters"]))
                story.append(Spacer(1, 0.3 * cm))

            # Filtro por curso
            if curso:
                data = data[data["Curso"] == curso]

            # Agrupar por curso
            if "Curso" in data.columns:
                grupos = data.groupby("Curso")
            else:
                grupos = [("Geral", data)]

            for nome_curso, df_curso in grupos:

                # Título do curso
                story.append(
                    Paragraph(f"Curso: {nome_curso}", self.styles["course"])
                )

                story.append(self._build_table(df_curso.drop(columns=["Curso"], errors="ignore")))
                story.append(Spacer(1, 0.6 * cm))

            doc.build(story)

            logger.info(f"PDF gerado com sucesso: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Erro ao gerar PDF: {e}", exc_info=True)
            return False