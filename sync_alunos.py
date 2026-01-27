#!/usr/bin/env python3
"""
Script de sincronização para tabela IMP-010 - Alunos
CORRIGIDO: Apenas alunos com sit_aluno='Ativo' são processados
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
    """Sincronizador de alunos - APENAS ALUNOS ATIVOS"""
    
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
        print(f"   Alunos ativos (flag): {summary['alunos_ativos']}")
        print(f"   Alunos com situação 'Ativo': {summary.get('situacao_ativo', 'N/A')}")
        print(f"   Cursos distintos: {summary['cursos_distintos']}")
        
        return summary
    
    def fetch_alunos_from_api(self, apenas_ativos=True):
        """Busca alunos da API - APENAS ATIVOS POR PADRÃO"""
        print(f"\n{'='*50}")
        print("CONECTANDO À API E BUSCANDO ALUNOS")
        print(f"{'='*50}")
        
        print("🔗 Conectando à API...")
        
        if apenas_ativos:
            print("🎯 Buscando APENAS alunos ATIVOS (filtro sit_aluno='Ativo')")
            alunos_api = self.api_client.get_alunos_ativos()
        else:
            print("⚠️  Buscando TODOS os alunos (sem filtro)")
            alunos_api = self.api_client.get_todos_alunos()
        
        if not alunos_api:
            print("❌ Nenhum aluno encontrado na API")
            return None
        
        # Contar quantos estão ativos (para verificação)
        if not apenas_ativos:
            ativos = sum(1 for a in alunos_api if a.get("sit_aluno") == "Ativo")
            print(f"📊 Total geral: {len(alunos_api)} alunos")
            print(f"📊 Ativos: {ativos}, Não ativos: {len(alunos_api) - ativos}")
        else:
            print(f"✅ Total de alunos ativos encontrados na API: {len(alunos_api)}")
        
        return alunos_api
    
    def process_alunos(self, alunos_api: List[Dict]):
        """Processa dados dos alunos - APENAS ATIVOS"""
        print(f"\n{'='*50}")
        print("PROCESSANDO DADOS DOS ALUNOS (APENAS ATIVOS)")
        print(f"{'='*50}")
        
        # Contar quantos não estão ativos antes do processamento
        nao_ativos = sum(1 for a in alunos_api if a.get("sit_aluno") != "Ativo")
        if nao_ativos > 0:
            print(f"⚠️  Atenção: {nao_ativos} alunos não ativos serão ignorados")
        
        alunos_processados = self.processor.process_batch(alunos_api)
        
        if not alunos_processados:
            print("❌ Nenhum aluno ativo processado com sucesso")
            return None
        
        # Verificar se todos os processados estão realmente ativos
        for aluno in alunos_processados:
            if aluno.get("sit_aluno") != "Ativo":
                print(f"❌ ERRO CRÍTICO: Aluno {aluno.get('matriculaAluno')} processado mas não está ativo!")
        
        print(f"✅ Alunos ATIVOS processados para importação: {len(alunos_processados)}")
        return alunos_processados
    
    def import_to_database(self, alunos_processados: List[Dict]):
        """Importa alunos para o banco de dados - APENAS ATIVOS"""
        print(f"\n{'='*50}")
        print("IMPORTANDO PARA O BANCO DE DADOS (APENAS ATIVOS)")
        print(f"{'='*50}")
        
        # Obter matrículas existentes
        matriculas_existentes = AlunoModel.get_existing_matriculas(config.DB_NAME)
        print(f"📊 Matrículas existentes no banco: {len(matriculas_existentes)}")
        
        # Processar cada aluno
        matriculas_atualizadas = set()
        alunos_nao_ativos_detectados = 0
        
        for aluno in alunos_processados:
            matricula = aluno['matriculaAluno']
            sit_aluno = aluno.get('sit_aluno', '')
            
            # VERIFICAÇÃO FINAL: garantir que só alunos ativos são importados
            if sit_aluno != "Ativo":
                print(f"❌ ALERTA: Tentando importar aluno não ativo: {matricula} - {sit_aluno}")
                alunos_nao_ativos_detectados += 1
                continue
            
            matriculas_atualizadas.add(matricula)
            
            try:
                if matricula in matriculas_existentes:
                    # Atualizar
                    AlunoModel.update_aluno(matricula, aluno, config.DB_NAME)
                    self.result.add_updated()
                    print(f"🔄 Aluno {matricula} atualizado (Ativo)")
                else:
                    # Inserir
                    AlunoModel.insert_aluno(aluno, config.DB_NAME)
                    self.result.add_inserted()
                    print(f"✅ Aluno {matricula} inserido (Ativo)")
                    
            except Exception as e:
                print(f"❌ Erro ao importar aluno {matricula}: {e}")
                self.result.add_error()
        
        # Registrar alunos não ativos detectados
        if alunos_nao_ativos_detectados > 0:
            print(f"⚠️  {alunos_nao_ativos_detectados} alunos não ativos detectados e ignorados")
            self.result.add_ignored_non_active(alunos_nao_ativos_detectados)
        
        # Marcar alunos não encontrados como inativos
        inactivated = AlunoModel.set_inactive(matriculas_atualizadas, config.DB_NAME)
        self.result.add_inactivated(inactivated)
        
        if inactivated > 0:
            print(f"⚠️  {inactivated} alunos marcados como inativos (não encontrados na busca atual)")
    
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
        print("EXEMPLOS DE ALUNOS ATIVOS IMPORTADOS")
        print(f"{'='*50}")
        
        if alunos_processados:
            for i, aluno in enumerate(alunos_processados[:limit]):
                print(f"\nAluno {i+1}:")
                print(f"  Matrícula: {aluno['matriculaAluno']}")
                print(f"  Nome: {aluno['nomeAluno'][:30]}..." if len(aluno['nomeAluno']) > 30 else f"  Nome: {aluno['nomeAluno']}")
                print(f"  Email: {aluno['emailAluno']}")
                print(f"  Curso: {aluno['codigoCurso']}")
                print(f"  Turno: {aluno['turno']}")
                print(f"  Situação: {aluno['sit_aluno']}")
        else:
            print("⚠️  Nenhum aluno para mostrar")
    
    def run(self):
        """Executa o processo completo de sincronização"""
        print("="*60)
        print("SISTEMA DE SINCRONIZAÇÃO DE ALUNOS - IMP-010")
        print("REGRAS: Apenas alunos com sit_aluno='Ativo' são processados")
        print(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print("="*60)
        
        try:
            # 1. Inicializar banco
            self.initialize_database()
            
            # 2. Resumo inicial
            resumo_inicial = self.get_initial_summary()
            
            # 3. Buscar dados da API (APENAS ATIVOS)
            alunos_api = self.fetch_alunos_from_api(apenas_ativos=True)
            if not alunos_api:
                return
            
            # 4. Processar dados (APENAS ATIVOS)
            alunos_processados = self.process_alunos(alunos_api)
            if not alunos_processados:
                return
            
            # 5. Importar para banco (APENAS ATIVOS)
            self.import_to_database(alunos_processados)
            
            # 6. Resumo final
            resumo_final = AlunoModel.get_summary(config.DB_NAME)
            
            print(f"\n{'='*50}")
            print("RESUMO FINAL")
            print(f"{'='*50}")
            
            print(f"\n📊 SITUAÇÃO DO BANCO APÓS SINCRONIZAÇÃO:")
            print(f"   Total de alunos: {resumo_final['total_alunos']}")
            print(f"   Alunos ativos (flag): {resumo_final['alunos_ativos']}")
            print(f"   Alunos com situação 'Ativo': {resumo_final.get('situacao_ativo', 'N/A')}")
            print(f"   Alunos inativos: {resumo_final['alunos_inativos']}")
            print(f"   Cursos distintos: {resumo_final['cursos_distintos']}")
            
            print(f"\n📊 RESULTADO DA IMPORTAÇÃO:")
            results = self.result.summary()
            print(f"   Novos alunos inseridos: {results['inserted']}")
            print(f"   Alunos atualizados: {results['updated']}")
            print(f"   Erros: {results['errors']}")
            print(f"   Alunos inativados: {results['inactivated']}")
            
            if results['ignored_non_active'] > 0:
                print(f"   Alunos não ativos ignorados: {results['ignored_non_active']}")
            
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
            print(f"\n🎯 Apenas alunos ATIVOS foram processados")
            print(f"💡 Banco de dados: {config.DB_NAME}")
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