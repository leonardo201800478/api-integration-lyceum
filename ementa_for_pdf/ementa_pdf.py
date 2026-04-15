import os
import re
import pandas as pd

from reportlab.lib.pagesizes import A4
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import black
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer
)

# =========================
# CONFIGURAÇÕES
# =========================
PASTA_BASE = "ementa_sagres"
ARQUIVO_EXCEL = os.path.join(PASTA_BASE, "ementas_sagres.xlsx")
PASTA_SAIDA = os.path.join(PASTA_BASE, "pdf_ementas")

INSTITUICAO = "Fundação Oswaldo Aranha"

os.makedirs(PASTA_SAIDA, exist_ok=True)

# =========================
# LEITURA DA PLANILHA
# =========================
df = pd.read_excel(ARQUIVO_EXCEL)

# Remove colunas vazias
df = df.loc[:, ~df.columns.str.contains("^Unnamed")]

# =========================
# ESTILOS PDF
# =========================
titulo_style = ParagraphStyle(
    "Titulo",
    fontName="Helvetica-Bold",
    fontSize=14,
    leading=20,
    alignment=TA_CENTER,
    textColor=black,
    spaceAfter=12
)

subtitulo_style = ParagraphStyle(
    "Subtitulo",
    fontName="Helvetica",
    fontSize=11,
    leading=16,
    alignment=TA_CENTER,
    spaceAfter=10
)

ementa_titulo_style = ParagraphStyle(
    "EmentaTitulo",
    fontName="Helvetica-Bold",
    fontSize=11,
    leading=18,
    spaceAfter=10
)

texto_style = ParagraphStyle(
    "Texto",
    fontName="Helvetica",
    fontSize=11,
    leading=20,
    alignment=TA_JUSTIFY,
    firstLineIndent=1 * cm,
)

# =========================
# FUNÇÕES
# =========================
def limpar_nome_arquivo(nome):
    nome = str(nome)
    return re.sub(r'[\\/*?:"<>|]', "_", nome)


def gerar_pdf(codigo, titulo, ementa):
    nome_arquivo = limpar_nome_arquivo(f"{codigo}.pdf")
    caminho_pdf = os.path.join(PASTA_SAIDA, nome_arquivo)

    doc = SimpleDocTemplate(
        caminho_pdf,
        pagesize=A4,
        topMargin=2.5 * cm,
        bottomMargin=2.5 * cm,
        leftMargin=3 * cm,
        rightMargin=3 * cm
    )

    story = []

    # =========================
    # CABEÇALHO
    # =========================
    story.append(Paragraph(INSTITUICAO, titulo_style))
    story.append(Paragraph(f"Código da Disciplina: {codigo}", subtitulo_style))

    # =========================
    # TÍTULO
    # =========================
    story.append(Paragraph(str(titulo), titulo_style))
    story.append(Spacer(1, 0.5 * cm))

    # =========================
    # EMENTA
    # =========================
    story.append(Paragraph("EMENTA", ementa_titulo_style))

    texto = str(ementa).replace("\n", "<br/>")
    story.append(Paragraph(texto, texto_style))

    doc.build(story)


# =========================
# EXECUÇÃO
# =========================
for i, row in df.iterrows():
    gerar_pdf(
        row["atc_cd_atividade"],
        row["atc_nm_atividade"],
        row["atc_ds_ementa"]
    )

    # Log simples de progresso
    if i % 100 == 0:
        print(f"{i} PDFs gerados...")

print("✔ Todos os PDFs foram gerados com sucesso.")