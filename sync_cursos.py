#!/usr/bin/env python3
"""
Script de sincronização para tabela IMP-001 - Cursos
"""
import sys
import pandas as pd
from datetime import datetime
from typing import List, Dict, Set

# Importações internas
from core.config import config
from core.api_client import CursoAPIClient, CurriculoAPIClient
from models.curso import CursoModel
from processors.curso_processor import CursoProcessor, CurriculoProcessor

class CursoSync:
    """Sincronizador de cursos"""
    
    def __init__(self):
        self.curso_api = CursoAPIClient()
        self.curriculo_api = CurriculoAPIClient()
        self.processor = CursoProcessor()
        self.curriculo_processor = CurriculoProcessor()
        
        # Resultados
        self.inserted = 0
        self.updated = 0
        self.errors = 0
        self.inactivated = 0
    
    def initialize_database(self):
        """Inicializa o banco de dados"""
        print("🗄️  Configurando banco de dados para cursos...")
        CursoModel.create_table(config.DB_NAME)
    
    def get_initial_summary(self):
        """Obtém resumo inicial"""
        print("📊 Situação inicial do banco de cursos:")
        summary = CursoModel.get_summary(config.DB_NAME)
        
        print(f"   Total de cursos: {summary['total_cursos']}")
        print(f"   Cursos ativos: {summary['cursos_ativos']}")
        print(f"   Unidades distintas: {summary['unidades_distintas']}")
        
        return summary
    
    def fetch_cursos_from_api(self):
        """Busca cursos da API"""
        print(f"\n{'='*50}")
        print("CONECTANDO À API E BUSCANDO CURSOS")
        print(f"{'='*50}")
        
        print("🔗 Conectando à API de cursos...")
        cursos_api = self.curso_api.get_cursos()
        
        if not cursos_api:
            print("❌ Nenhum curso encontrado na API")
            return None
        
        return cursos_api
    
    def fetch_curriculos_from_api(self):
        """Busca currículos da API"""
        print(f"\n{'='*50}")
        print("CONECTANDO À API E BUSCANDO CURRÍCULOS")
        print(f"{'='*50}")
        
        print("🔗 Conectando à API de currículos...")
        curriculos_api = self.curriculo_api.get_curriculos()
        
        if not curriculos_api:
            print("❌ Nenhum currículo encontrado na API")
            return None
        
        return curriculos_api
    
    def process_cursos(self, cursos_api: List[Dict], curriculos_api: List[Dict] = None):
        """Processa dados dos cursos e adiciona informações dos currículos"""
        print(f"\n{'='*50}")
        print("PROCESSANDO DADOS DOS CURSOS")
        print(f"{'='*50}")
        
        # Processar cursos (filtra e mapeia)
        cursos_processados = self.processor.process_batch(cursos_api)
        
        if not cursos_processados:
            print("❌ Nenhum curso processado com sucesso")
            return None
        
        # Se temos currículos, processá-los
        if curriculos_api:
            print("\n📋 Processando currículos para obter quantPeriodos...")
            
            # Obter o maior currículo por curso
            maiores_curriculos = self.curriculo_processor.get_maior_curriculo_por_curso(curriculos_api)
            
            # Para cada curso processado, buscar o prazo_ideal do maior currículo
            for curso in cursos_processados:
                codigo_curso = curso['codigoCurso']
                
                if codigo_curso in maiores_curriculos:
                    curriculo = maiores_curriculos[codigo_curso]
                    prazo_ideal = self.curriculo_processor.extrair_prazo_ideal(curriculo)
                    
                    if prazo_ideal is not None:
                        curso['quantPeriodos'] = prazo_ideal
                        print(f"   ✅ Curso {codigo_curso}: prazo_ideal = {prazo_ideal}")
                    else:
                        print(f"   ⚠️  Curso {codigo_curso}: prazo_ideal não encontrado ou inválido")
                else:
                    print(f"   ⚠️  Curso {codigo_curso}: nenhum currículo encontrado")
        
        print(f"✅ Cursos processados para importação: {len(cursos_processados)}")
        return cursos_processados
    
    def import_to_database(self, cursos_processados: List[Dict]):
        """Importa cursos para o banco de dados"""
        print(f"\n{'='*50}")
        print("IMPORTANDO CURSOS PARA O BANCO DE DADOS")
        print(f"{'='*50}")
        
        # Obter códigos existentes
        codigos_existentes = CursoModel.get_existing_codigos(config.DB_NAME)
        print(f"📊 Códigos de curso existentes no banco: {len(codigos_existentes)}")
        
        # Processar cada curso
        codigos_atualizados = set()
        
        for curso in cursos_processados:
            codigo = curso['codigoCurso']
            codigos_atualizados.add(codigo)
            
            try:
                if codigo in codigos_existentes:
                    # Atualizar
                    CursoModel.update_curso(codigo, curso, config.DB_NAME)
                    self.updated += 1
                    print(f"🔄 Curso {codigo} atualizado")
                else:
                    # Inserir
                    CursoModel.insert_curso(curso, config.DB_NAME)
                    self.inserted += 1
                    print(f"✅ Curso {codigo} inserido")
                    
            except Exception as e:
                print(f"❌ Erro ao importar curso {codigo}: {e}")
                self.errors += 1
        
        # Marcar cursos não encontrados como inativos
        inactivated = CursoModel.set_inactive(codigos_atualizados, config.DB_NAME)
        self.inactivated = inactivated
        
        if inactivated > 0:
            print(f"⚠️  {inactivated} cursos marcados como inativos (não encontrados na busca atual)")
    
    def export_to_csv(self, cursos_processados: List[Dict]):
        """Exporta dados para CSV"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"cursos_imp001_{timestamp}.csv"
        
        df = pd.DataFrame(cursos_processados)
        
        # Selecionar colunas para exportação
        colunas_exportar = [
            'codigoCurso', 'nomeCurso', 'codigoUnidadeOrganizacional', 'quantPeriodos'
        ]
        
        # Filtrar colunas que existem
        colunas_disponiveis = [col for col in colunas_exportar if col in df.columns]
        df = df[colunas_disponiveis]
        
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"✅ Dados exportados para: {filename}")
        return filename
    
    def show_examples(self, cursos_processados: List[Dict], limit=5):
        """Mostra exemplos de cursos importados"""
        print(f"\n{'='*50}")
        print("EXEMPLOS DE CURSOS IMPORTADOS")
        print(f"{'='*50}")
        
        if cursos_processados:
            for i, curso in enumerate(cursos_processados[:limit]):
                print(f"\nCurso {i+1}:")
                print(f"  Código: {curso['codigoCurso']}")
                print(f"  Nome: {curso['nomeCurso'][:30]}..." if len(curso['nomeCurso']) > 30 else f"  Nome: {curso['nomeCurso']}")
                print(f"  Unidade: {curso['codigoUnidadeOrganizacional']}")
                print(f"  Períodos: {curso.get('quantPeriodos', 'N/A')}")
        else:
            print("⚠️  Nenhum curso para mostrar")
    
    def run(self):
        """Executa o processo completo de sincronização"""
        print("="*60)
        print("SISTEMA DE SINCRONIZAÇÃO DE CURSOS - IMP-001")
        print(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print("="*60)
        
        try:
            # 1. Inicializar banco
            self.initialize_database()
            
            # 2. Resumo inicial
            resumo_inicial = self.get_initial_summary()
            
            # 3. Buscar dados da API (cursos e currículos)
            cursos_api = self.fetch_cursos_from_api()
            if not cursos_api:
                return
            
            curriculos_api = self.fetch_curriculos_from_api()
            # Nota: mesmo que não haja currículos, podemos processar os cursos
            
            # 4. Processar dados
            cursos_processados = self.process_cursos(cursos_api, curriculos_api)
            if not cursos_processados:
                return
            
            # 5. Importar para banco
            self.import_to_database(cursos_processados)
            
            # 6. Resumo final
            resumo_final = CursoModel.get_summary(config.DB_NAME)
            
            print(f"\n{'='*50}")
            print("RESUMO FINAL")
            print(f"{'='*50}")
            
            print(f"\n📊 SITUAÇÃO DO BANCO APÓS SINCRONIZAÇÃO:")
            print(f"   Total de cursos: {resumo_final['total_cursos']}")
            print(f"   Cursos ativos: {resumo_final['cursos_ativos']}")
            print(f"   Cursos inativos: {resumo_final['cursos_inativos']}")
            print(f"   Unidades distintas: {resumo_final['unidades_distintas']}")
            
            print(f"\n📊 RESULTADO DA IMPORTAÇÃO:")
            print(f"   Novos cursos inseridos: {self.inserted}")
            print(f"   Cursos atualizados: {self.updated}")
            print(f"   Erros: {self.errors}")
            print(f"   Cursos inativados: {self.inactivated}")
            
            print(f"\n📈 VARIAÇÃO DESTA EXECUÇÃO:")
            print(f"   Cursos ativos: {resumo_inicial['cursos_ativos']} → {resumo_final['cursos_ativos']}")
            print(f"   Diferença: {resumo_final['cursos_ativos'] - resumo_inicial['cursos_ativos']}")
            
            # 7. Exportar CSV (opcional)
            if cursos_processados:
                exportar = input("\n💾 Exportar dados para CSV? (s/n): ").strip().lower()
                if exportar == 's':
                    self.export_to_csv(cursos_processados)
            
            # 8. Mostrar exemplos
            self.show_examples(cursos_processados)
            
            print(f"\n{'='*60}")
            print("✅ SINCORNIZAÇÃO DE CURSOS CONCLUÍDA COM SUCESSO!")
            print(f"{'='*60}")
            print(f"\n💡 Banco de dados: {config.DB_NAME}")
            print(f"📊 Total de cursos sincronizados: {len(cursos_processados)}")
            print("👋 Processo finalizado!")
            
        except Exception as e:
            print(f"\n❌ Erro durante a sincronização: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

def main():
    """Função principal"""
    sync = CursoSync()
    sync.run()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Processo interrompido pelo usuário")
        sys.exit(0)