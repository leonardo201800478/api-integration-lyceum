"""
Exportação para Excel no formato de planilha de carga
"""

import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter
from datetime import datetime
import os

class ExportadorExcel:
    def __init__(self, caminho_saida='./exportacoes'):
        self.caminho_saida = caminho_saida
        os.makedirs(caminho_saida, exist_ok=True)

    def criar_planilha_carga(self, nome_tabela, dados, config_tabela):
        """
        Cria planilha no formato de carga Qstione.
        Gera a planilha MESMO que a lista de dados esteja vazia (apenas cabeçalho).
        """
        # Criar nome do arquivo
        data_hora = datetime.now().strftime('%Y%m%d_%H%M%S')
        nome_arquivo = f"{nome_tabela}_{data_hora}.xlsx"
        caminho_arquivo = os.path.join(self.caminho_saida, nome_arquivo)

        # Criar workbook
        wb = openpyxl.Workbook()

        # ---------- Aba "Dados a Importar" ----------
        ws_dados = wb.active
        ws_dados.title = "Dados a Importar"

        # Estilos
        fonte_titulo = Font(name='Calibri', size=11, bold=True, color='FFFFFF')
        alinhamento_esquerda = Alignment(horizontal='left', vertical='center')
        alinhamento_direita = Alignment(horizontal='right', vertical='center')
        preenchimento_titulo = PatternFill(fill_type='solid', start_color='366092', end_color='366092')
        preenchimento_cabecalho = PatternFill(fill_type='solid', start_color='C5D9F1', end_color='C5D9F1')

        # Cabeçalho da planilha de carga (sempre presente)
        cabecalho = [
            ["Tipo de Carga:", config_tabela.get('tipo_carga', 'Incremental')],
            ["Escopo da Carga:", config_tabela.get('escopo_carga', 'Instituicao')],
            ["Limite do Escopo:", ""],
            ["Conteúdo da Carga:", config_tabela.get('nome_planilha', nome_tabela)],
            [""],  # Linha vazia separadora
        ]

        for linha_idx, linha in enumerate(cabecalho, 1):
            for col_idx, valor in enumerate(linha, 1):
                celula = ws_dados.cell(row=linha_idx, column=col_idx, value=valor)
                if col_idx == 1 and linha_idx <= 4:  # Títulos (coluna A)
                    celula.font = fonte_titulo
                    celula.alignment = alinhamento_direita
                    celula.fill = preenchimento_titulo
                elif col_idx == 2 and linha_idx <= 4:  # Valores (coluna B)
                    celula.font = Font(name='Calibri', size=11, bold=False, color='000000')
                    celula.alignment = alinhamento_esquerda

        # Cabeçalho das colunas de dados (sempre incluso)
        colunas = [campo['nome_qstione'] for campo in config_tabela['campos']]
        linha_cabecalho = 6  # após as 5 linhas de cabeçalho

        for col_idx, coluna in enumerate(colunas, 1):
            celula = ws_dados.cell(row=linha_cabecalho, column=col_idx, value=coluna)
            celula.font = Font(name='Calibri', size=11, bold=True)
            celula.fill = preenchimento_cabecalho
            celula.alignment = Alignment(horizontal='center', vertical='center')

        # **Agora os dados: se existirem, preenche; se não, apenas o cabeçalho permanece**
        for linha_idx, registro in enumerate(dados, linha_cabecalho + 1):
            for col_idx, coluna in enumerate(colunas, 1):
                valor = registro.get(coluna, '')
                ws_dados.cell(row=linha_idx, column=col_idx, value=valor)

        # Ajuste automático da largura das colunas (com limite razoável)
        for col_idx, coluna in enumerate(colunas, 1):
            col_letter = get_column_letter(col_idx)
            ws_dados.column_dimensions[col_letter].width = 25

        # ---------- Aba "Configurações" ----------
        ws_config = wb.create_sheet(title="Configurações")

        config_content = [
            ["ATENÇÃO: Os dados desta planilha de Configurações não devem ser alterados, pois possuem apenas caráter informativo e de configurações para a planilha de Dados a Importar."],
            [""],
            ["Tipos de Carga"],
            ["Incremental", "Os dados constantes na planilha serão adicionados ou atualizarão os já existentes no sistema."],
            ["Completa", "Ocorre o comportamento previsto na Incremental e, adicionalmente, os dados que estejam no sistema, mas não na planilha, serão inativados."],
            [""],
            ["Escopos de Carga"],
            ["Instituicao", "Engloba todos os usuários da instituição de ensino."],
            ["Unidade Organizacional", "Engloba todos os cursos da unidade organizacional."],
            ["Curso", "Engloba todas as vinculações referentes ao curso com código preenchido no campo Limite do Escopo."],
            ["Disciplina", "Engloba todas as vinculações referentes à disciplina com código preenchido no campo Limite do Escopo."],
            ["Oferta de Disciplina", "Engloba todas as vinculações referentes à oferta de disciplina com código preenchido no campo Limite do Escopo."],
        ]

        for linha_idx, linha in enumerate(config_content, 1):
            for col_idx, valor in enumerate(linha, 1):
                ws_config.cell(row=linha_idx, column=col_idx, value=valor)

        ws_config.column_dimensions['A'].width = 50
        ws_config.column_dimensions['B'].width = 70

        # Salvar arquivo
        wb.save(caminho_arquivo)

        # Mensagem de resultado
        print(f"✓ Planilha gerada: {caminho_arquivo}")
        if dados:
            print(f"  Total de registros: {len(dados)}")
        else:
            print(f"  (Planilha vazia – apenas cabeçalho)")

        return caminho_arquivo

    def exportar_todas_tabelas(self, dados_por_tabela, config_tabelas):
        """
        Exporta múltiplas tabelas para arquivos Excel separados.
        Agora gera planilha mesmo quando a lista de dados está vazia.
        """
        arquivos_gerados = []

        for nome_tabela, dados in dados_por_tabela.items():
            if nome_tabela in config_tabelas:
                # Não verifica mais 'if dados' – sempre tenta criar
                arquivo = self.criar_planilha_carga(
                    nome_tabela,
                    dados,          # pode ser []
                    config_tabelas[nome_tabela]
                )
                if arquivo:
                    arquivos_gerados.append(arquivo)
            else:
                print(f"⚠️  Tabela '{nome_tabela}' não encontrada na configuração. Ignorada.")

        return arquivos_gerados