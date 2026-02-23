"""
Script principal para importação e exportação de dados Qstione
Adaptado para SQL Server (sem conexões SQLite)
"""

import os
from pathlib import Path

from qstione.config.tabelas import TABELAS_CONFIG, DES_CONFIG
from qstione.importadores.imp_001_cursos import ImportadorCursos
from qstione.importadores.imp_002_disciplina import ImportadorDisciplinas
from qstione.importadores.imp_005_ofertas import ImportadorOfertas
from qstione.importadores.imp_006_usuarios import ImportadorUsuarios
from qstione.importadores.imp_007_usuarios_cursos import ImportadorUsuariosCursos
from qstione.importadores.imp_008_usuarios_disciplinas import ImportadorUsuariosDisciplinas
from qstione.importadores.imp_009_professores_ofertas import ImportadorProfessoresOfertas
from qstione.importadores.imp_010_alunos import ImportadorAlunos
from qstione.importadores.imp_011_alunos_ofertas import ImportadorAlunosOfertas
from qstione.importadores.imp_013_unidades_avaliacao import ImportadorUnidadesAvaliacao
from qstione.importadores.imp_015_conteudos import ImportadorConteudos
from qstione.importadores.imp_016_unidades_organizacionais import ImportadorUnidadesOrganizacionais
from qstione.exportadores.excel import ExportadorExcel
from qstione.exportadores.sql import ExportadorSQL


class GestorQstione:
    def __init__(self):
        self.dados_exportar = {}
        # Criar diretórios necessários
        Path("exportacoes").mkdir(exist_ok=True)
        Path("backups").mkdir(exist_ok=True)

    # ----------------------------------------------------------------------
    # MÉTODOS DE IMPORTAÇÃO (IMP-*)
    # ----------------------------------------------------------------------
    def importar_tabela_cursos(self):
        try:
            importador = ImportadorCursos()
            dados = importador.executar_importacao()
            self.dados_exportar['imp_001_cursos'] = dados
            return True
        except Exception as e:
            print(f"Erro: {e}")
            return False

    def importar_tabela_disciplinas(self):
        try:
            importador = ImportadorDisciplinas()
            dados = importador.executar_importacao()
            self.dados_exportar['imp_002_disciplina'] = dados
            return True
        except Exception as e:
            print(f"Erro: {e}")
            return False

    def importar_tabela_objetivos(self):
        print("\n⚠️  IMP-003 ainda não implementado.")
        return True

    def importar_tabela_referencias(self):
        print("\n⚠️  IMP-004 ainda não implementado.")
        return True

    def importar_tabela_ofertas(self):
        try:
            importador = ImportadorOfertas()
            dados = importador.executar_importacao()
            self.dados_exportar['imp_005_ofertas'] = dados
            return True
        except Exception as e:
            print(f"Erro: {e}")
            return False

    def importar_tabela_usuarios(self):
        try:
            importador = ImportadorUsuarios()
            dados = importador.executar_importacao()
            self.dados_exportar['imp_006_usuarios'] = dados
            return True
        except Exception as e:
            print(f"Erro: {e}")
            return False

    def importar_tabela_usuarios_cursos(self):
        try:
            importador = ImportadorUsuariosCursos()
            dados = importador.executar_importacao()
            self.dados_exportar['imp_007_usuarios_cursos'] = dados
            return True
        except Exception as e:
            print(f"Erro: {e}")
            return False

    def importar_tabela_usuarios_disciplinas(self):
        try:
            importador = ImportadorUsuariosDisciplinas()
            dados = importador.executar_importacao()
            self.dados_exportar['imp_008_usuarios_disciplinas'] = dados
            return True
        except Exception as e:
            print(f"Erro: {e}")
            return False

    def importar_tabela_professores_ofertas(self):
        try:
            importador = ImportadorProfessoresOfertas()
            dados = importador.executar_importacao()
            self.dados_exportar['imp_009_professores_ofertas'] = dados
            return True
        except Exception as e:
            print(f"Erro: {e}")
            return False

    def importar_tabela_alunos(self):
        try:
            importador = ImportadorAlunos()
            dados = importador.executar_importacao()
            self.dados_exportar['imp_010_alunos'] = dados
            return True
        except Exception as e:
            print(f"Erro: {e}")
            return False

    def importar_tabela_alunos_ofertas(self):
        try:
            importador = ImportadorAlunosOfertas()
            dados = importador.executar_importacao()
            self.dados_exportar['imp_011_alunos_ofertas'] = dados
            return True
        except Exception as e:
            print(f"Erro: {e}")
            return False

    def importar_tabela_unidades_avaliacao(self):
        try:
            importador = ImportadorUnidadesAvaliacao()
            dados = importador.executar_importacao()
            self.dados_exportar['imp_013_unidades_avaliacao'] = dados
            return True
        except Exception as e:
            print(f"Erro: {e}")
            return False

    def importar_tabela_conteudos(self):
        print("\n⚠️  IMP-015 ainda não implementado.")
        return True

    def importar_tabela_unidades_organizacionais(self):
        print("\n⚠️  IMP-016 ainda não implementado.")
        return True

    # ----------------------------------------------------------------------
    # MÉTODOS DE DESATIVAÇÃO (DES-*)
    # ----------------------------------------------------------------------
    def desativar_cursos(self):
        print("\n⚠️  DES-001 ainda não implementado.")
        return True

    def desativar_disciplinas(self):
        print("\n⚠️  DES-002 ainda não implementado.")
        return True

    def desativar_ofertas(self):
        print("\n⚠️  DES-005 ainda não implementado.")
        return True

    def desativar_usuarios(self):
        print("\n⚠️  DES-006 ainda não implementado.")
        return True

    def desativar_usuarios_cursos(self):
        print("\n⚠️  DES-007 ainda não implementado.")
        return True

    def desativar_usuarios_disciplinas(self):
        print("\n⚠️  DES-008 ainda não implementado.")
        return True

    def desativar_professores_ofertas(self):
        print("\n⚠️  DES-009 ainda não implementado.")
        return True

    def desativar_alunos(self):
        print("\n⚠️  DES-010 ainda não implementado.")
        return True

    def desativar_alunos_ofertas(self):
        print("\n⚠️  DES-011 ainda não implementado.")
        return True

    def desativar_unidades_organizacionais(self):
        print("\n⚠️  DES-012 ainda não implementado.")
        return True

    # ----------------------------------------------------------------------
    # EXPORTAÇÕES
    # ----------------------------------------------------------------------
    def exportar_para_excel(self):
        print("\n" + "="*60)
        print("EXPORTAÇÃO PARA PLANILHAS EXCEL")
        print("="*60)
        print(f"Conteúdo de dados_exportar: {list(self.dados_exportar.keys())}")
        if not self.dados_exportar:
            print("Nenhum dado disponível. Execute uma importação primeiro.")
            return []
        exportador = ExportadorExcel()
        arquivos = exportador.exportar_todas_tabelas(self.dados_exportar, TABELAS_CONFIG)
        return arquivos

    def exportar_para_sql(self):
        print("\n" + "="*60)
        print("EXPORTAÇÃO PARA ARQUIVO SQL")
        print("="*60)
        print("⚠️  Exportação SQL ainda não adaptada para SQL Server.")
        return None
        # exportador = ExportadorSQL()
        # arquivo = exportador.exportar_banco_completo('qstione.db', 'backups')
        # return arquivo

    # ----------------------------------------------------------------------
    # VERIFICAÇÃO DE TABELAS
    # ----------------------------------------------------------------------
    def verificar_tabela(self, nome_tabela):
        print(f"\n" + "="*60)
        print(f"VERIFICAÇÃO DA TABELA: {nome_tabela}")
        print("="*60)
        try:
            from core.database import get_db_connection
            with get_db_connection(db_path='qstione.db') as conn:
                cursor = conn.cursor()
                cursor.execute(f"SELECT COUNT(*) FROM {nome_tabela}")
                total = cursor.fetchone()[0]
                print(f"Total de registros: {total}")
                cursor.execute(f"SELECT TOP 5 * FROM {nome_tabela} ORDER BY data_atualizacao DESC")
                rows = cursor.fetchall()
                if rows:
                    print("\nÚltimos 5 registros:")
                    for row in rows:
                        print(f"  {row}")
        except Exception as e:
            print(f"Erro: {e}")

    # ----------------------------------------------------------------------
    # MENU PRINCIPAL
    # ----------------------------------------------------------------------
    def menu_principal(self):
        print("\n" + "="*70)
        print("GESTOR DE IMPORTAÇÃO QSTIONE (v1.14.0) – SQL Server")
        print("="*70)

        while True:
            print("\n📋 MENU PRINCIPAL:")
            print("  --- IMPORTAÇÃO ---")
            print("   1. IMP-001 - Cursos")
            print("   2. IMP-002 - Disciplinas")
            print("   3. IMP-003 - Objetivos de Aprendizagem")
            print("   4. IMP-004 - Referências Bibliográficas")
            print("   5. IMP-005 - Ofertas de Disciplinas")
            print("   6. IMP-006 - Usuários")
            print("   7. IMP-007 - Usuários dos Cursos")
            print("   8. IMP-008 - Usuários das Disciplinas")
            print("   9. IMP-009 - Professores das Ofertas")
            print("  10. IMP-010 - Alunos")
            print("  11. IMP-011 - Alunos das Ofertas")
            print("  13. IMP-013 - Unidades de Avaliação")
            print("  14. IMP-015 - Conteúdos Programáticos")
            print("  15. IMP-016 - Unidades Organizacionais")
            print("\n  --- DESATIVAÇÃO ---")
            print("  16. DES-001 - Cursos")
            print("  17. DES-002 - Disciplinas")
            print("  18. DES-005 - Ofertas")
            print("  19. DES-006 - Usuários")
            print("  20. DES-007 - Usuários dos Cursos")
            print("  21. DES-008 - Usuários das Disciplinas")
            print("  22. DES-009 - Professores das Ofertas")
            print("  23. DES-010 - Alunos")
            print("  24. DES-011 - Alunos das Ofertas")
            print("  25. DES-012 - Unidades Organizacionais")
            print("\n  --- EXPORTAÇÃO / UTILITÁRIOS ---")
            print("  26. Exportar para Excel")
            print("  27. Exportar backup SQL (⚠️ não implementado)")
            print("  28. Verificar tabela")
            print("  29. Executar TODAS as importações (IMP)")
            print("  30. Sair")

            opcao = input("\nEscolha uma opção: ").strip()

            # IMPORTAÇÃO
            if opcao == '1': self.importar_tabela_cursos()
            elif opcao == '2': self.importar_tabela_disciplinas()
            elif opcao == '3': self.importar_tabela_objetivos()
            elif opcao == '4': self.importar_tabela_referencias()
            elif opcao == '5': self.importar_tabela_ofertas()
            elif opcao == '6': self.importar_tabela_usuarios()
            elif opcao == '7': self.importar_tabela_usuarios_cursos()
            elif opcao == '8': self.importar_tabela_usuarios_disciplinas()
            elif opcao == '9': self.importar_tabela_professores_ofertas()
            elif opcao == '10': self.importar_tabela_alunos()
            elif opcao == '11': self.importar_tabela_alunos_ofertas()
            elif opcao == '13': self.importar_tabela_unidades_avaliacao()
            elif opcao == '14': self.importar_tabela_conteudos()
            elif opcao == '15': self.importar_tabela_unidades_organizacionais()
            # DESATIVAÇÃO
            elif opcao == '16': self.desativar_cursos()
            elif opcao == '17': self.desativar_disciplinas()
            elif opcao == '18': self.desativar_ofertas()
            elif opcao == '19': self.desativar_usuarios()
            elif opcao == '20': self.desativar_usuarios_cursos()
            elif opcao == '21': self.desativar_usuarios_disciplinas()
            elif opcao == '22': self.desativar_professores_ofertas()
            elif opcao == '23': self.desativar_alunos()
            elif opcao == '24': self.desativar_alunos_ofertas()
            elif opcao == '25': self.desativar_unidades_organizacionais()
            # EXPORTAÇÃO / UTILITÁRIOS
            elif opcao == '26':
                arquivos = self.exportar_para_excel()
                if arquivos:
                    print("\nArquivos gerados:")
                    for arq in arquivos:
                        print(f"  ✓ {os.path.basename(arq)}")
            elif opcao == '27':
                self.exportar_para_sql()
            elif opcao == '28':
                tabela = input("Nome da tabela: ").strip()
                if tabela: self.verificar_tabela(tabela)
            elif opcao == '29':
                print("\nExecutando todas as importações IMP...")
                self.importar_tabela_cursos()
                self.importar_tabela_disciplinas()
                self.importar_tabela_objetivos()
                self.importar_tabela_referencias()
                self.importar_tabela_ofertas()
                self.importar_tabela_usuarios()
                self.importar_tabela_usuarios_cursos()
                self.importar_tabela_usuarios_disciplinas()
                self.importar_tabela_professores_ofertas()
                self.importar_tabela_alunos()
                self.importar_tabela_alunos_ofertas()
                self.importar_tabela_unidades_avaliacao()
                self.importar_tabela_conteudos()
                self.importar_tabela_unidades_organizacionais()
            elif opcao == '30':
                print("\nSaindo...")
                break
            else:
                print("\nOpção inválida!")


def main():
    gestor = GestorQstione()
    gestor.menu_principal()


if __name__ == "__main__":
    main()