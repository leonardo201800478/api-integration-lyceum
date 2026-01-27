#!/usr/bin/env python3
"""
Script de sincronização para tabela IMP-010 - Alunos
"""
import sys
import pandas as pd
from datetime import datetime
from typing import List, Dict

# Importações internas
from core.config import config
from core.api_client import AlunoAPIClient
from models.aluno import AlunoModel
from processors.aluno_processor import AlunoProcessor, ImportResult

class AlunoSync:
    """Sincronizador de alunos"""
    
    def __init__(self):
        self.api_client = AlunoAPIClient()
        self.processor = AlunoProcessor()
        self.result = ImportResult()
    
    def initialize_database(self):
        """Inicializa o banco de dados"""
        print("🗄️  Configurando banco de dados...")
        AlunoModel.create_table(config.DB_NAME)
    
    def get_initial_summary(self):
        """Obtém resumo inicial"""
        print("📊 Situação inicial do banco:")
        summary = AlunoModel.get_summary(config.DB_NAME)
        
        print(f"   Total de alunos: {summary['total_alunos']}")
        print(f"   Alunos ativos: {summary['alunos_ativos']}")
        print(f"   Cursos distintos: {summary['cursos_distintos']}")
        
        return summary
    
    def fetch_alunos_from_api(self):
        """Busca alunos da API"""
        print(f"\n{'='*50}")
        print("CONECTANDO À API E BUSCANDO ALUNOS ATIVOS")
        print(f"{'='*50}")
        
        print("🔗 Conectando à API...")
        alunos_api = self.api_client.get_alunos_ativos()
        
        if not alunos_api:
            print("❌ Nenhum aluno encontrado na API")
            return None
        
        print(f"✅ Total de alunos ativos encontrados na API: {len(alunos_api)}")
        return alunos_api
    
    def process_alunos(self, alunos_api: List[Dict]):
        """Processa dados dos alunos"""
        print(f"\n{'='*50}")
        print("PROCESSANDO DADOS DOS ALUNOS")
        print(f"{'='*50}")
        
        alunos_processados = self.processor.process_batch(alunos_api)
        
        if not alunos_processados:
            print("❌ Nenhum aluno processado com sucesso")
            return None
        
        print(f"✅ Alunos processados para importação: {len(alunos_processados)}")
        return alunos_processados
    
    def import_to_database(self, alunos_processados: List[Dict]):
        """Importa alunos para o banco de dados"""
        print(f"\n{'='*50}")
        print("IMPORTANDO PARA O BANCO DE DADOS")
        print(f"{'='*50}")
        
        # Obter matrículas existentes
        matriculas_existentes = AlunoModel.get_existing_matriculas(config.DB_NAME)
        print(f"📊 Matrículas existentes no banco: {len(matriculas_existentes)}")
        
        # Processar cada aluno
        matriculas_atualizadas = set()
        
        for aluno in alunos_processados:
            matricula = aluno['matriculaAluno']
            matriculas_atualizadas.add(matricula)
            
            try:
                if matricula in matriculas_existentes:
                    # Atualizar
                    AlunoModel.update_aluno(matricula, aluno, config.DB_NAME)
                    self.result.add_updated()
                    print(f"🔄 Aluno {matricula} atualizado")
                else:
                    # Inserir
                    AlunoModel.insert_aluno(aluno, config.DB_NAME)
                    self.result.add_inserted()
                    print(f"✅ Aluno {matricula} inserido")
                    
            except Exception as e:
                print(f"❌ Erro ao importar aluno {matricula}: {e}")
                self.result.add_error()
        
        # Marcar alunos não encontrados como inativos
        inactivated = AlunoModel.set_inactive(matriculas_atualizadas, config.DB_NAME)
        self.result.add_inactivated(inactivated)
        
        if inactivated > 0:
            print(f"⚠️  {inactivated} alunos marcados como inativos")
    
    def export_to_csv(self, alunos_processados: List[Dict]):
        """Exporta dados para CSV"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"alunos_imp010_{timestamp}.csv"
        
        df = pd.DataFrame(alunos_processados)
        
        # Selecionar colunas para exportação
        colunas_exportar = [
            'matriculaAluno', 'nomeAluno', 'emailAluno', 
            'codigoCurso', 'turno', 'sit_aluno'
        ]
        
        # Filtrar colunas que existem
        colunas_disponiveis = [col for col in colunas_exportar if col in df.columns]
        df = df[colunas_disponiveis]
        
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"✅ Dados exportados para: {filename}")
        return filename
    
    def show_examples(self, alunos_processados: List[Dict], limit=5):
        """Mostra exemplos de alunos importados"""
        print(f"\n{'='*50}")
        print("EXEMPLOS DE ALUNOS IMPORTADOS")
        print(f"{'='*50}")
        
        if alunos_processados:
            for i, aluno in enumerate(alunos_processados[:limit]):
                print(f"\nAluno {i+1}:")
                print(f"  Matrícula: {aluno['matriculaAluno']}")
                print(f"  Nome: {aluno['nomeAluno']}")
                print(f"  Email: {aluno['emailAluno']}")
                print(f"  Curso: {aluno['codigoCurso']}")
                print(f"  Turno: {aluno['turno']}")
    
    def run(self):
        """Executa o processo completo de sincronização"""
        print("="*60)
        print("SISTEMA DE SINCRONIZAÇÃO DE ALUNOS - IMP-010")
        print(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print("="*60)
        
        try:
            # 1. Inicializar banco
            self.initialize_database()
            
            # 2. Resumo inicial
            resumo_inicial = self.get_initial_summary()
            
            # 3. Buscar dados da API
            alunos_api = self.fetch_alunos_from_api()
            if not alunos_api:
                return
            
            # 4. Processar dados
            alunos_processados = self.process_alunos(alunos_api)
            if not alunos_processados:
                return
            
            # 5. Importar para banco
            self.import_to_database(alunos_processados)
            
            # 6. Resumo final
            resumo_final = AlunoModel.get_summary(config.DB_NAME)
            
            print(f"\n{'='*50}")
            print("RESUMO FINAL")
            print(f"{'='*50}")
            
            print(f"\n📊 SITUAÇÃO DO BANCO APÓS SINCRONIZAÇÃO:")
            print(f"   Total de alunos: {resumo_final['total_alunos']}")
            print(f"   Alunos ativos: {resumo_final['alunos_ativos']}")
            print(f"   Alunos inativos: {resumo_final['alunos_inativos']}")
            print(f"   Cursos distintos: {resumo_final['cursos_distintos']}")
            
            print(f"\n📊 RESULTADO DA IMPORTAÇÃO:")
            results = self.result.summary()
            print(f"   Novos alunos inseridos: {results['inserted']}")
            print(f"   Alunos atualizados: {results['updated']}")
            print(f"   Erros: {results['errors']}")
            print(f"   Alunos inativados: {results['inactivated']}")
            
            print(f"\n📈 VARIAÇÃO DESTA EXECUÇÃO:")
            print(f"   Alunos ativos: {resumo_inicial['alunos_ativos']} → {resumo_final['alunos_ativos']}")
            print(f"   Diferença: {resumo_final['alunos_ativos'] - resumo_inicial['alunos_ativos']}")
            
            # 7. Exportar CSV (opcional)
            if alunos_processados:
                exportar = input("\n💾 Exportar dados para CSV? (s/n): ").strip().lower()
                if exportar == 's':
                    self.export_to_csv(alunos_processados)
            
            # 8. Mostrar exemplos
            self.show_examples(alunos_processados)
            
            print(f"\n{'='*60}")
            print("✅ SINCORNIZAÇÃO CONCLUÍDA COM SUCESSO!")
            print(f"{'='*60}")
            print(f"\n💡 Banco de dados: {config.DB_NAME}")
            print(f"📊 Total de alunos ativos sincronizados: {len(alunos_processados)}")
            print("👋 Processo finalizado!")
            
        except Exception as e:
            print(f"\n❌ Erro durante a sincronização: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

def main():
    """Função principal"""
    sync = AlunoSync()
    sync.run()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Processo interrompido pelo usuário")
        sys.exit(0)