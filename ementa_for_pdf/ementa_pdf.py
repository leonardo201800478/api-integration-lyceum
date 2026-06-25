import os
import re
import pandas as pd

from reportlab.lib.pagesizes import A4
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import black
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
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
IMAGEM_LOGO_FOA = os.path.join(PASTA_BASE, "foa.png")

INSTITUICAO = "Fundação Oswaldo Aranha"

os.makedirs(PASTA_SAIDA, exist_ok=True)

# =========================
# LEITURA DA PLANILHA
# =========================
df = pd.read_excel(ARQUIVO_EXCEL)

# Remove colunas vazias
df = df.loc[:, ~df.columns.str.contains("^Unnamed")]

# =========================
# ESTILOS PDF (CONFORME ABNT)
# =========================
# Margens: esquerda e superior = 3 cm; direita e inferior = 2 cm
MARGEM_ESQ = 3 * cm
MARGEM_DIR = 2 * cm
MARGEM_SUP = 3 * cm
MARGEM_INF = 2 * cm

# Fonte: Times New Roman (ou similar) – recomendada pela ABNT
# Tamanhos: 12 para texto, 14 para títulos, espaçamento 1,5
FONTE_TEXTO = "Times-Roman"
FONTE_TITULO = "Times-Bold"
TAM_TEXTO = 12
TAM_TITULO = 14
ESPACO_1_5_TEXTO = TAM_TEXTO * 1.5  # 18 pt
ESPACO_1_5_TITULO = TAM_TITULO * 1.5  # 21 pt
RECUO_PRIMEIRA_LINHA = 1.25 * cm

# Estilo para o nome da instituição (cabeçalho)
instituicao_style = ParagraphStyle(
    "Instituicao",
    fontName=FONTE_TITULO,
    fontSize=TAM_TITULO,
    leading=ESPACO_1_5_TITULO,
    alignment=TA_CENTER,
    textColor=black,
    spaceAfter=6
)

# Estilo para o código da disciplina
codigo_style = ParagraphStyle(
    "Codigo",
    fontName=FONTE_TEXTO,
    fontSize=TAM_TEXTO,
    leading=ESPACO_1_5_TEXTO,
    alignment=TA_CENTER,
    spaceAfter=6
)

# Estilo para o título da disciplina (nome da disciplina)
titulo_style = ParagraphStyle(
    "Titulo",
    fontName=FONTE_TITULO,
    fontSize=TAM_TITULO,
    leading=ESPACO_1_5_TITULO,
    alignment=TA_CENTER,
    textColor=black,
    spaceAfter=12
)

# Estilo para o rótulo "EMENTA" (subtítulo)
ementa_rotulo_style = ParagraphStyle(
    "EmentaRotulo",
    fontName=FONTE_TITULO,
    fontSize=TAM_TEXTO,
    leading=ESPACO_1_5_TEXTO,
    alignment=TA_LEFT,
    spaceAfter=6
)

# Estilo para o conteúdo da ementa (texto justificado, recuo de 1,25 cm)
texto_style = ParagraphStyle(
    "Texto",
    fontName=FONTE_TEXTO,
    fontSize=TAM_TEXTO,
    leading=ESPACO_1_5_TEXTO,
    alignment=TA_JUSTIFY,
    firstLineIndent=RECUO_PRIMEIRA_LINHA,
    spaceAfter=0
)

# =========================
# FUNÇÕES
# =========================
def limpar_nome_arquivo(nome):
    nome = str(nome)
    return re.sub(r'[\\/*?:"<>|]', "_", nome)

def desenhar_fundo(canvas, doc):
    """
    Desenha o timbre como marca d'água, ocupando toda a folha A4,
    preservando a proporção da imagem.
    """
    canvas.saveState()

    img = ImageReader(IMAGEM_LOGO_FOA)
    img_w, img_h = img.getSize()
    page_w, page_h = A4

    # Escala para preencher completamente a página
    escala = max(page_w / img_w, page_h / img_h)

    nova_largura = img_w * escala
    nova_altura = img_h * escala

    x = (page_w - nova_largura) / 2
    y = (page_h - nova_altura) / 2

    canvas.drawImage(
        img,
        x,
        y,
        width=nova_largura,
        height=nova_altura,
        preserveAspectRatio=True,
        mask='auto'
    )

    canvas.restoreState()

def gerar_pdf(codigo, titulo, ementa):
    nome_arquivo = limpar_nome_arquivo(f"{codigo}.pdf")
    caminho_pdf = os.path.join(PASTA_SAIDA, nome_arquivo)

    doc = SimpleDocTemplate(
        caminho_pdf,
        pagesize=A4,
        topMargin=MARGEM_SUP,
        bottomMargin=MARGEM_INF,
        leftMargin=MARGEM_ESQ,
        rightMargin=MARGEM_DIR
    )

    story = []

    # =========================
    # CABEÇALHO
    # =========================
    story.append(Paragraph(INSTITUICAO, instituicao_style))
    story.append(Paragraph(f"Código da Disciplina: {codigo}", codigo_style))
    story.append(Spacer(1, 0.3 * cm))

    # =========================
    # TÍTULO DA DISCIPLINA
    # =========================
    story.append(Paragraph(str(titulo), titulo_style))
    story.append(Spacer(1, 0.5 * cm))

    # =========================
    # EMENTA (conteúdo)
    # =========================
    story.append(Paragraph("EMENTA", ementa_rotulo_style))
    story.append(Spacer(1, 0.2 * cm))

    # Limpeza e substituição de quebras de linha
    texto = str(ementa).replace("\n", "<br/>")
    # Remove espaços extras e caracteres problemáticos (opcional)
    texto = re.sub(r'\s+', ' ', texto)  # normaliza espaços
    # Trata caracteres especiais (já é feito pelo reportlab)
    story.append(Paragraph(texto, texto_style))

    # =========================
    # CONSTRUÇÃO DO PDF
    # =========================
    doc.build(
        story,
        onFirstPage=desenhar_fundo,
        onLaterPages=desenhar_fundo
    )

# =========================
# EXECUÇÃO
# =========================
for i, row in df.iterrows():
    gerar_pdf(
        row["atc_cd_atividade"],
        row["atc_nm_atividade"],
        row["atc_ds_ementa"]
    )

    if (i + 1) % 100 == 0:
        print(f"{i+1} PDFs gerados...")

print("✔ Todos os PDFs foram gerados com sucesso.")