"""
Script principal para importação e exportação de dados Qstione
"""

import sqlite3
import os
from pathlib import Path

# Importações do projeto
from qstione.config.tabelas import TABELAS_CONFIG
from qstione.importadores.imp_001_cursos import ImportadorCursos
from qstione.importadores.imp_002_disciplina import ImportadorDisciplinas
from qstione.importadores.imp_005_ofertas import ImportadorOfertas
from qstione.importadores.imp_006_usuarios import ImportadorUsuarios
from qstione.importadores.imp_007_usuarios_cursos import ImportadorUsuariosCursos
from qstione.importadores.imp_008_usuarios_disciplinas import ImportadorUsuariosDisciplinas
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

    # ------------------------------------------------------------
    # Métodos de importação (um por tabela)
    # ------------------------------------------------------------
    def importar_tabela_cursos(self):
        """Importa dados para a tabela imp_001_cursos"""
        try:
            con_lyceum = sqlite3.connect(self.caminho_lyceum)
            con_qstione = sqlite3.connect(self.caminho_qstione)
            importador = ImportadorCursos(con_lyceum, con_qstione)
            dados_transformados = importador.executar_importacao()
            self.dados_exportar['imp_001_cursos'] = dados_transformados
            con_lyceum.close()
            con_qstione.close()
            return True
        except Exception as e:
            print(f"Erro na importação: {e}")
            return False

    def importar_tabela_disciplinas(self):
        """Importa dados para a tabela imp_002_disciplina"""
        try:
            con_lyceum = sqlite3.connect(self.caminho_lyceum)
            con_qstione = sqlite3.connect(self.caminho_qstione)
            importador = ImportadorDisciplinas(con_lyceum, con_qstione)
            dados_transformados = importador.executar_importacao()
            self.dados_exportar['imp_002_disciplina'] = dados_transformados
            con_lyceum.close()
            con_qstione.close()
            return True
        except Exception as e:
            print(f"Erro na importação: {e}")
            return False

    def importar_tabela_ofertas(self):
        """Importa dados para a tabela imp_005_ofertas"""
        try:
            con_lyceum = sqlite3.connect(self.caminho_lyceum)
            con_qstione = sqlite3.connect(self.caminho_qstione)
            importador = ImportadorOfertas(con_lyceum, con_qstione)
            dados_transformados = importador.executar_importacao()
            self.dados_exportar['imp_005_ofertas'] = dados_transformados
            con_lyceum.close()
            con_qstione.close()
            return True
        except Exception as e:
            print(f"Erro na importação: {e}")
            return False

    def importar_tabela_usuarios(self):
        """Importa dados para a tabela imp_006_usuarios"""
        try:
            con_lyceum = sqlite3.connect(self.caminho_lyceum)
            con_qstione = sqlite3.connect(self.caminho_qstione)
            importador = ImportadorUsuarios(con_lyceum, con_qstione)
            dados_transformados = importador.executar_importacao()
            self.dados_exportar['imp_006_usuarios'] = dados_transformados
            con_lyceum.close()
            con_qstione.close()
            return True
        except Exception as e:
            print(f"Erro na importação: {e}")
            return False

    def importar_tabela_usuarios_cursos(self):
        """Importa dados para a tabela imp_007_usuarios_cursos"""
        try:
            con_lyceum = sqlite3.connect(self.caminho_lyceum)
            con_qstione = sqlite3.connect(self.caminho_qstione)
            importador = ImportadorUsuariosCursos(con_lyceum, con_qstione)
            dados_transformados = importador.executar_importacao()
            self.dados_exportar['imp_007_usuarios_cursos'] = dados_transformados
            con_lyceum.close()
            con_qstione.close()
            return True
        except Exception as e:
            print(f"Erro na importação: {e}")
            return False

    def importar_tabela_usuarios_disciplinas(self):
        """Importa dados para a tabela imp_008_usuarios_disciplinas"""
        try:
            con_lyceum = sqlite3.connect(self.caminho_lyceum)
            con_qstione = sqlite3.connect(self.caminho_qstione)
            importador = ImportadorUsuariosDisciplinas(con_lyceum, con_qstione)
            dados_transformados = importador.executar_importacao()
            self.dados_exportar['imp_008_usuarios_disciplinas'] = dados_transformados
            con_lyceum.close()
            con_qstione.close()
            return True
        except Exception as e:
            print(f"Erro na importação: {e}")
            return False

    # ------------------------------------------------------------
    # Exportações
    # ------------------------------------------------------------
    def exportar_para_excel(self):
        """Exporta dados para planilhas Excel"""
        print("\n" + "=" * 60)
        print("EXPORTAÇÃO PARA PLANILHAS EXCEL")
        print("=" * 60)

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
        print("\n" + "=" * 60)
        print("EXPORTAÇÃO PARA ARQUIVO SQL")
        print("=" * 60)

        exportador = ExportadorSQL()
        arquivo_sql = exportador.exportar_banco_completo(
            self.caminho_qstione,
            'backups'
        )
        return arquivo_sql

    # ------------------------------------------------------------
    # Verificação e relatórios
    # ------------------------------------------------------------
    def verificar_tabela(self, nome_tabela):
        """Verifica os dados na tabela especificada"""
        print(f"\n" + "=" * 60)
        print(f"VERIFICAÇÃO DA TABELA: {nome_tabela}")
        print("=" * 60)

        try:
            con_qstione = sqlite3.connect(self.caminho_qstione)
            cursor = con_qstione.cursor()

            # Contar registros
            cursor.execute(f"SELECT COUNT(*) FROM {nome_tabela}")
            total = cursor.fetchone()[0]
            print(f"Total de registros: {total}")

            # Amostras específicas por tabela
            if nome_tabela == 'imp_001_cursos':
                cursor.execute(f"""
                    SELECT codigoCurso, nomeCurso, quantPeriodos, codigoUnidadeOrganizacional
                    FROM {nome_tabela}
                    ORDER BY data_atualizacao DESC
                    LIMIT 3
                """)
                registros = cursor.fetchall()
                if registros:
                    print("\nÚltimos 3 registros:")
                    for reg in registros:
                        print(f"  Código: {reg[0]}")
                        print(f"    Nome: {reg[1][:30]}...")
                        print(f"    Períodos: {reg[2]}")
                        print(f"    Unidade: {reg[3]}\n")

            elif nome_tabela == 'imp_002_disciplina':
                cursor.execute(f"""
                    SELECT codigoDisciplina, nomeDisciplina, codigoCurso, periodo
                    FROM {nome_tabela}
                    ORDER BY data_atualizacao DESC
                    LIMIT 3
                """)
                registros = cursor.fetchall()
                if registros:
                    print("\nÚltimos 3 registros:")
                    for reg in registros:
                        print(f"  Código: {reg[0]}")
                        print(f"    Nome: {reg[1][:30]}...")
                        print(f"    Curso: {reg[2]}")
                        print(f"    Período: {reg[3]}\n")

            elif nome_tabela == 'imp_005_ofertas':
                cursor.execute(f"""
                    SELECT codigoOferta, nomeOferta, codigoDisciplina, codigoTipoOferta
                    FROM {nome_tabela}
                    ORDER BY data_atualizacao DESC
                    LIMIT 3
                """)
                registros = cursor.fetchall()
                if registros:
                    print("\nÚltimos 3 registros:")
                    for reg in registros:
                        print(f"  Código: {reg[0]}")
                        print(f"    Nome: {reg[1][:30]}...")
                        print(f"    Disciplina: {reg[2]}")
                        print(f"    Tipo: {reg[3]}\n")

            elif nome_tabela == 'imp_006_usuarios':
                cursor.execute(f"""
                    SELECT matriculaUsuario, codigoUsuario, emailUsuario, nomeUsuario, DATE(data_atualizacao)
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
                        print(f"    Atualizado em: {reg[4]}\n")

            elif nome_tabela == 'imp_007_usuarios_cursos':
                cursor.execute(f"""
                    SELECT codigoCurso, emailUsuario, papelUsuario, DATE(data_atualizacao)
                    FROM {nome_tabela}
                    ORDER BY data_atualizacao DESC
                    LIMIT 5
                """)
                registros = cursor.fetchall()
                if registros:
                    print("\nÚltimos 5 registros:")
                    for reg in registros:
                        papel = "Coordenador" if reg[2] == 1 else "Professor"
                        print(f"  Curso: {reg[0]}")
                        print(f"    Email: {reg[1]}")
                        print(f"    Papel: {reg[2]} ({papel})")
                        print(f"    Atualizado em: {reg[3]}\n")

                    cursor.execute("""
                        SELECT papelUsuario, COUNT(*)
                        FROM imp_007_usuarios_cursos
                        GROUP BY papelUsuario
                    """)
                    contagem = cursor.fetchall()
                    print("📊 Distribuição por papel:")
                    for papel, count in contagem:
                        papel_desc = "Coordenadores" if papel == 1 else "Professores"
                        print(f"  {papel_desc}: {count}")

            elif nome_tabela == 'imp_008_usuarios_disciplinas':
                cursor.execute(f"""
                    SELECT codigoDisciplina, emailUsuario, DATE(data_atualizacao)
                    FROM {nome_tabela}
                    ORDER BY data_atualizacao DESC
                    LIMIT 5
                """)
                registros = cursor.fetchall()
                if registros:
                    print("\nÚltimos 5 registros:")
                    for reg in registros:
                        print(f"  Código Disciplina: {reg[0]}")
                        print(f"    Email: {reg[1]}")
                        print(f"    Atualizado em: {reg[2]}\n")

            else:
                print("Tabela não reconhecida para exibição detalhada.")

            cursor.close()
            con_qstione.close()

        except Exception as e:
            print(f"Erro ao verificar tabela: {e}")

    # ------------------------------------------------------------
    # Menu interativo
    # ------------------------------------------------------------
    def menu_principal(self):
        print("\n" + "=" * 70)
        print("GESTOR DE IMPORTAÇÃO QSTIONE")
        print("=" * 70)

        if not self.verificar_banco_lyceum():
            return

        while True:
            print("\n📋 MENU PRINCIPAL:")
            print("  1. Importar tabela imp_001_cursos")
            print("  2. Importar tabela imp_002_disciplina")
            print("  3. Importar tabela imp_005_ofertas")
            print("  4. Importar tabela imp_006_usuarios")
            print("  5. Importar tabela imp_007_usuarios_cursos")
            print("  6. Importar tabela imp_008_usuarios_disciplinas")  # NOVA
            print("  7. Exportar para Excel (planilhas de carga)")
            print("  8. Exportar backup SQL")
            print("  9. Verificar tabelas importadas")
            print(" 10. Executar tudo (importar + exportar Excel + backup)")
            print(" 11. Sair")

            opcao = input("\nEscolha uma opção (1-11): ").strip()

            if opcao == '1':
                self.importar_tabela_cursos()
            elif opcao == '2':
                self.importar_tabela_disciplinas()
            elif opcao == '3':
                self.importar_tabela_ofertas()
            elif opcao == '4':
                self.importar_tabela_usuarios()
            elif opcao == '5':
                self.importar_tabela_usuarios_cursos()
            elif opcao == '6':
                self.importar_tabela_usuarios_disciplinas()
            elif opcao == '7':
                arquivos = self.exportar_para_excel()
                if arquivos:
                    print("\nArquivos gerados:")
                    for arquivo in arquivos:
                        print(f"  ✓ {os.path.basename(arquivo)}")
            elif opcao == '8':
                arquivo = self.exportar_para_sql()
                if arquivo:
                    print(f"Backup gerado: {arquivo}")
            elif opcao == '9':
                tabela = input("Digite o nome da tabela (ex: imp_001_cursos, imp_002_disciplina, imp_005_ofertas, imp_006_usuarios, imp_007_usuarios_cursos, imp_008_usuarios_disciplinas): ").strip()
                if tabela:
                    self.verificar_tabela(tabela)
                else:
                    print("Tabela não especificada.")
            elif opcao == '10':
                print("\nExecutando todas as importações e exportações...")
                self.importar_tabela_cursos()
                self.importar_tabela_disciplinas()
                self.importar_tabela_ofertas()
                self.importar_tabela_usuarios()
                self.importar_tabela_usuarios_cursos()
                self.importar_tabela_usuarios_disciplinas()
                self.exportar_para_excel()
                self.exportar_para_sql()
                # Verifica algumas tabelas como amostra
                self.verificar_tabela('imp_001_cursos')
                self.verificar_tabela('imp_002_disciplina')
                self.verificar_tabela('imp_005_ofertas')
                self.verificar_tabela('imp_006_usuarios')
                self.verificar_tabela('imp_007_usuarios_cursos')
                self.verificar_tabela('imp_008_usuarios_disciplinas')
            elif opcao == '11':
                print("\nSaindo do Gestor Qstione...")
                break
            else:
                print("\nOpção inválida! Tente novamente.")


def main():
    gestor = GestorQstione()
    gestor.menu_principal()


if __name__ == "__main__":
    main()