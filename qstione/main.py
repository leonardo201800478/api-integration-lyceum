"""
Script principal para importação e exportação de dados Qstione
"""

import sqlite3
import os
from datetime import datetime
from pathlib import Path

# Importações do projeto
from qstione.config.tabelas import TABELAS_CONFIG
from qstione.importadores.imp_006_usuarios import ImportadorUsuarios
from qstione.exportadores.excel import ExportadorExcel
from qstione.exportadores.sql import ExportadorSQL

class GestorQstione:
    def __init__(self, caminho_lyceum='lyceum.db', caminho_qstione='qstione.db'):
        self.caminho_lyceum = caminho_lyceum
        self.caminho_qstione = caminho_qstione
        self.dados_exportar = {}
        
        # Criar pastas necessárias
        Path("exportacoes").mkdir(exist_ok=True)
        Path("backups").mkdir(exist_ok=True)
    
    def verificar_banco_lyceum(self):
        """Verifica se o banco Lyceum existe"""
        if not os.path.exists(self.caminho_lyceum):
            print(f"ERRO: Banco {self.caminho_lyceum} não encontrado!")
            print(f"Certifique-se de que o arquivo está no diretório: {os.getcwd()}")
            return False
        return True
    
    def importar_tabela_usuarios(self):
        """Importa dados para a tabela imp_006_usuarios"""
        try:
            # Conectar aos bancos
            con_lyceum = sqlite3.connect(self.caminho_lyceum)
            con_qstione = sqlite3.connect(self.caminho_qstione)
            
            # Criar importador
            importador = ImportadorUsuarios(con_lyceum, con_qstione)
            
            # Executar importação
            dados_transformados = importador.executar_importacao()
            
            # Armazenar dados para exportação
            self.dados_exportar['imp_006_usuarios'] = dados_transformados
            
            # Fechar conexões
            con_lyceum.close()
            con_qstione.close()
            
            return True
            
        except Exception as e:
            print(f"Erro na importação: {e}")
            return False
    
    def exportar_para_excel(self):
        """Exporta dados para planilhas Excel"""
        print("\n" + "="*60)
        print("EXPORTAÇÃO PARA PLANILHAS EXCEL")
        print("="*60)
        
        if not self.dados_exportar:
            print("Nenhum dado disponível para exportação.")
            return []
        
        exportador = ExportadorExcel()
        arquivos_gerados = exportador.exportar_todas_tabelas(
            self.dados_exportar, 
            TABELAS_CONFIG
        )
        
        return arquivos_gerados
    
    def exportar_para_sql(self):
        """Exporta backup do banco Qstione"""
        print("\n" + "="*60)
        print("EXPORTAÇÃO PARA ARQUIVO SQL")
        print("="*60)
        
        exportador = ExportadorSQL()
        arquivo_sql = exportador.exportar_banco_completo(
            self.caminho_qstione,
            'backups'
        )
        
        return arquivo_sql
    
    def verificar_tabela(self, nome_tabela='imp_006_usuarios'):
        """Verifica os dados na tabela especificada"""
        print(f"\n" + "="*60)
        print(f"VERIFICAÇÃO DA TABELA: {nome_tabela}")
        print("="*60)
        
        try:
            con_qstione = sqlite3.connect(self.caminho_qstione)
            cursor = con_qstione.cursor()
            
            # Contar registros
            cursor.execute(f"SELECT COUNT(*) FROM {nome_tabela}")
            total = cursor.fetchone()[0]
            
            print(f"Total de registros: {total}")
            
            # Obter amostra
            cursor.execute(f"""
                SELECT matriculaUsuario, codigoUsuario, emailUsuario, 
                       nomeUsuario, DATE(data_atualizacao)
                FROM {nome_tabela}
                ORDER BY data_atualizacao DESC
                LIMIT 3
            """)
            
            registros = cursor.fetchall()
            
            if registros:
                print("\nÚltimos 3 registros:")
                for reg in registros:
                    print(f"  Matrícula: {reg[0]}")
                    print(f"    Código: {reg[1] or 'N/A'}")
                    print(f"    Email: {reg[2]}")
                    print(f"    Nome: {reg[3][:30]}...")
                    print(f"    Atualizado em: {reg[4]}")
                    print()
            
            cursor.close()
            con_qstione.close()
            
        except Exception as e:
            print(f"Erro ao verificar tabela: {e}")
    
    def menu_principal(self):
        """Exibe menu interativo"""
        
        print("\n" + "="*70)
        print("GESTOR DE IMPORTAÇÃO QSTIONE")
        print("="*70)
        
        if not self.verificar_banco_lyceum():
            return
        
        while True:
            print(f"\n📋 MENU PRINCIPAL:")
            print("  1. Importar tabela imp_006_usuarios")
            print("  2. Exportar para Excel (planilhas de carga)")
            print("  3. Exportar backup SQL")
            print("  4. Verificar tabelas importadas")
            print("  5. Executar tudo (importar + exportar Excel + backup)")
            print("  6. Sair")
            
            opcao = input("\nEscolha uma opção (1-6): ").strip()
            
            if opcao == '1':
                self.importar_tabela_usuarios()
            
            elif opcao == '2':
                arquivos = self.exportar_para_excel()
                if arquivos:
                    print(f"\nArquivos gerados:")
                    for arquivo in arquivos:
                        print(f"  ✓ {os.path.basename(arquivo)}")
            
            elif opcao == '3':
                arquivo = self.exportar_para_sql()
                if arquivo:
                    print(f"Backup gerado: {arquivo}")
            
            elif opcao == '4':
                self.verificar_tabela('imp_006_usuarios')
            
            elif opcao == '5':
                print("\nExecutando todas as operações...")
                if self.importar_tabela_usuarios():
                    self.exportar_para_excel()
                    self.exportar_para_sql()
                    self.verificar_tabela()
            
            elif opcao == '6':
                print("\nSaindo do Gestor Qstione...")
                break
            
            else:
                print("\nOpção inválida! Tente novamente.")

def main():
    """Função principal"""
    gestor = GestorQstione()
    gestor.menu_principal()

if __name__ == "__main__":
    main()