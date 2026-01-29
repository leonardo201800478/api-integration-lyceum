"""
Exportação para Excel no formato de planilha de carga
"""

import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from datetime import datetime
import os

class ExportadorExcel:
    def __init__(self, caminho_saida='./exportacoes'):
        self.caminho_saida = caminho_saida
        os.makedirs(caminho_saida, exist_ok=True)
    
    def criar_planilha_carga(self, nome_tabela, dados, config_tabela):
        """
        Cria planilha no formato de carga Qstione
        """
        if not dados:
            return None
        
        # Criar nome do arquivo
        data_hora = datetime.now().strftime('%Y%m%d_%H%M%S')
        nome_arquivo = f"{nome_tabela}_{data_hora}.xlsx"
        caminho_arquivo = os.path.join(self.caminho_saida, nome_arquivo)
        
        # Criar workbook
        wb = openpyxl.Workbook()
        
        # Aba "Dados a Importar"
        ws_dados = wb.active
        ws_dados.title = "Dados a Importar"
        
        # Estilos
        fonte_titulo = Font(name='Calibri', size=11, bold=True, color='FFFFFF')
        alinhamento_esquerda = Alignment(horizontal='left', vertical='center')
        alinhamento_direita = Alignment(horizontal='right', vertical='center')
        preenchimento_titulo = PatternFill(fill_type='solid', start_color='366092', end_color='366092')
        
        # Cabeçalho da planilha de carga
        cabecalho = [
            ["Tipo de Carga:", config_tabela.get('tipo_carga', 'Incremental')],
            ["Escopo da Carga:", config_tabela.get('escopo_carga', 'Instituicao')],
            ["Limite do Escopo:", ""],
            ["Conteúdo da Carga:", config_tabela.get('nome_planilha', nome_tabela)],
            [""],  # Linha vazia
        ]
        
        # Adicionar cabeçalho
        for linha_idx, linha in enumerate(cabecalho, 1):
            for col_idx, valor in enumerate(linha, 1):
                celula = ws_dados.cell(row=linha_idx, column=col_idx, value=valor)
                if col_idx == 1 and linha_idx <= 4:  # Títulos
                    celula.font = fonte_titulo
                    celula.alignment = alinhamento_direita
                    celula.fill = preenchimento_titulo
                elif col_idx == 2 and linha_idx <= 4:  # Valores
                    celula.font = Font(name='Calibri', size=11, bold=False, color='000000')
                    celula.alignment = alinhamento_esquerda
        
        # Adicionar cabeçalho das colunas de dados
        colunas = [campo['nome_qstione'] for campo in config_tabela['campos']]
        linha_cabecalho = 6  # Após as 5 linhas de cabeçalho
        
        for col_idx, coluna in enumerate(colunas, 1):
            celula = ws_dados.cell(row=linha_cabecalho, column=col_idx, value=coluna)
            celula.font = Font(name='Calibri', size=11, bold=True)
            celula.fill = PatternFill(fill_type='solid', start_color='C5D9F1', end_color='C5D9F1')
            celula.alignment = Alignment(horizontal='center', vertical='center')
        
        # Adicionar dados
        for linha_idx, registro in enumerate(dados, linha_cabecalho + 1):
            for col_idx, coluna in enumerate(colunas, 1):
                valor = registro.get(coluna, '')
                ws_dados.cell(row=linha_idx, column=col_idx, value=valor)
        
        # Ajustar largura das colunas
        for col_idx, coluna in enumerate(colunas, 1):
            col_letter = get_column_letter(col_idx)
            ws_dados.column_dimensions[col_letter].width = 25
        
        # Aba "Configurações"
        ws_config = wb.create_sheet(title="Configurações")
        
        # Conteúdo fixo da aba Configurações
        config_content = [
            ["ATENÇÃO: Os dados desta planilha de Configurações não devem ser alterados, pois possuem apenas caráter informativo e de configurações para a planilha de Dados a Importar."],
            [""],
            ["Tipos de Carga"],
            ["Incremental", "Os dados constantes na planilha serão adicionados ou atualizarão os já existentes no sistema."],
            ["Completa", "Ocorre o comportamento previsto na Incremental e, adicionalmente, os dados que estejam no sistema, mas não na planilha, serão inativados."],
            [""],
            ["Escopos de Carga"],
            ["Instituicao", "Engloba todos os usuários da instituição de ensino."],
        ]
        
        # Adicionar conteúdo à aba Configurações
        for linha_idx, linha in enumerate(config_content, 1):
            for col_idx, valor in enumerate(linha, 1):
                ws_config.cell(row=linha_idx, column=col_idx, value=valor)
        
        # Ajustar largura da coluna A na aba Configurações
        ws_config.column_dimensions['A'].width = 40
        ws_config.column_dimensions['B'].width = 60
        
        # Salvar arquivo
        wb.save(caminho_arquivo)
        
        print(f"✓ Planilha gerada: {caminho_arquivo}")
        print(f"  Total de registros: {len(dados)}")
        
        return caminho_arquivo
    
    def exportar_todas_tabelas(self, dados_por_tabela, config_tabelas):
        """
        Exporta múltiplas tabelas para arquivos Excel separados
        """
        arquivos_gerados = []
        
        for nome_tabela, dados in dados_por_tabela.items():
            if nome_tabela in config_tabelas and dados:
                arquivo = self.criar_planilha_carga(
                    nome_tabela, 
                    dados, 
                    config_tabelas[nome_tabela]
                )
                if arquivo:
                    arquivos_gerados.append(arquivo)
        
        return arquivos_gerados