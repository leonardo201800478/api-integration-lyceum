#!/usr/bin/env python3
"""
Script de sincronização para tabela LY_CURRICULOS
Utiliza o CurriculoAPIClient do api_client.py
"""
import sys
import os
import time
from datetime import datetime
from typing import List, Dict
from collections import Counter

# CORREÇÃO DO IMPORT - Adiciona diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importações internas
from core.config import config
from core.api_client import CurriculoAPIClient
from models.ly_curriculo import LyCurriculoModel

class LyCurriculoSync:
    """Sincronizador da tabela LY_CURRICULOS usando api_client"""
    
    def __init__(self):
        self.client = CurriculoAPIClient()
        
        # Resultados
        self.total_curriculos = 0
        self.inseridos = 0
        self.erros = 0
    
    def initialize_database(self):
        """Inicializa o banco de dados"""
        print("🗄️  Configurando banco de dados para LY_CURRICULOS...")
        LyCurriculoModel.create_table(config.DB_NAME)
    
    def get_initial_summary(self):
        """Obtém resumo inicial"""
        print("📊 Situação inicial da tabela LY_CURRICULOS:")
        summary = LyCurriculoModel.get_summary(config.DB_NAME)
        
        print(f"   Total de currículos: {summary['total_curriculos']}")
        print(f"   Cursos distintos: {summary['cursos_distintos']}")
        print(f"   Turnos distintos: {summary['turnos_distintos']}")
        print(f"   Situações distintas: {summary['situacoes_distintas']}")
        print(f"   Média prazo ideal: {summary['media_prazo_ideal']}")
        print(f"   Média prazo máximo: {summary['media_prazo_max']}")
        
        return summary
    
    def buscar_curriculos(self):
        """Busca currículos da API usando o cliente já paginado"""
        print(f"\n{'='*50}")
        print("BUSCANDO CURRÍCULOS DA API LYCEUM")
        print(f"{'='*50}")
        
        curriculos = self.client.get_curriculos()
        
        if not curriculos:
            print("❌ Nenhum currículo encontrado na API")
            return None
        
        self.total_curriculos = len(curriculos)
        print(f"✅ Total de currículos encontrados: {self.total_curriculos}")
        
        # Estatísticas
        cursos_unicos = set(str(c.get('curso', '')).strip() for c in curriculos)
        cursos_unicos = {c for c in cursos_unicos if c}
        
        print(f"📊 Cursos distintos encontrados: {len(cursos_unicos)}")
        
        # Contar currículos por curso
        cursos_counter = Counter(str(c.get('curso', '')).strip() for c in curriculos)
        
        # Remover entradas vazias
        if '' in cursos_counter:
            del cursos_counter['']
        
        print("📋 Top 10 cursos com mais currículos:")
        for curso, count in cursos_counter.most_common(10):
            print(f"  Curso {curso}: {count} currículos")
        
        # Contar por situação
        situacoes_counter = Counter(str(c.get('situacao', 'N/A')).strip() for c in curriculos)
        print("\n📋 Distribuição por situação:")
        for situacao, count in situacoes_counter.most_common():
            print(f"  {situacao}: {count}")
        
        # Mostrar amostra da primeira página
        if curriculos and len(curriculos) > 0:
            print(f"\n📋 Amostra dos primeiros currículos:")
            for i, curriculo in enumerate(curriculos[:3]):
                curso = curriculo.get('curso', 'N/A')
                curriculo_id = curriculo.get('curriculo', 'N/A')
                prazo_ideal = curriculo.get('prazo_ideal', 'N/A')
                prazo_max = curriculo.get('prazo_max', 'N/A')
                turno = curriculo.get('turno', 'N/A')
                situacao = curriculo.get('situacao', 'N/A')
                print(f"     {i+1}. Curso: {curso}, Currículo: {curriculo_id}, "
                      f"Turno: {turno}, Prazo Ideal: {prazo_ideal}, "
                      f"Prazo Máx: {prazo_max}, Situação: {situacao}")
        
        return curriculos
    
    def processar_curriculos(self, curriculos: List[Dict]):
        """Processa e valida currículos"""
        print(f"\n{'='*50}")
        print("PROCESSANDO CURRÍCULOS")
        print(f"{'='*50}")
        
        # Filtrar currículos válidos (com curriculo e curso)
        curriculos_validos = []
        curriculos_invalidos = 0
        
        for curriculo in curriculos:
            curriculo_id = curriculo.get('curriculo')
            curso = curriculo.get('curso')
            
            if curriculo_id and curso:
                curriculos_validos.append(curriculo)
            else:
                curriculos_invalidos += 1
        
        print(f"📊 Currículos válidos: {len(curriculos_validos)}/{len(curriculos)}")
        if curriculos_invalidos > 0:
            print(f"📊 Currículos inválidos (sem ID ou curso): {curriculos_invalidos}")
        
        return curriculos_validos
    
    def importar_para_banco(self, curriculos: List[Dict]):
        """Importa currículos para o banco de dados"""
        print(f"\n{'='*50}")
        print("IMPORTANDO PARA BANCO DE DADOS")
        print(f"{'='*50}")
        
        if not curriculos:
            print("⚠️  Nenhum currículo para importar")
            return
        
        print(f"💾 Importando {len(curriculos)} currículos...")
        
        # Inserir em lotes para melhor performance
        batch_size = 50
        total_batches = (len(curriculos) + batch_size - 1) // batch_size
        
        for i in range(total_batches):
            start_idx = i * batch_size
            end_idx = min((i + 1) * batch_size, len(curriculos))
            batch = curriculos[start_idx:end_idx]
            
            print(f"  📦 Processando lote {i+1}/{total_batches} ({len(batch)} currículos)...")
            
            try:
                saved = LyCurriculoModel.insert_batch(batch, config.DB_NAME)
                self.inseridos += saved
                print(f"  ✅ Lote {i+1}: {saved} currículos salvos")
                
            except Exception as e:
                print(f"  ❌ Erro no lote {i+1}: {e}")
                self.erros += 1
            
            # Pequeno delay entre lotes
            if i < total_batches - 1:
                time.sleep(0.3)
    
    def mostrar_exemplos(self):
        """Mostra exemplos de currículos importados"""
        print(f"\n{'='*50}")
        print("EXEMPLOS DE CURRÍCULOS IMPORTADOS")
        print(f"{'='*50}")
        
        # Buscar currículos recentes
        curriculos_recentes = LyCurriculoModel.get_curriculos_recentes(limit=5, db_name=config.DB_NAME)
        
        if not curriculos_recentes:
            print("⚠️  Nenhum currículo encontrado no banco")
            return
        
        print("📋 Últimos currículos importados:")
        for i, curriculo in enumerate(curriculos_recentes, 1):
            print(f"\n  {i}. Curso: {curriculo[1]}")
            print(f"     Currículo: {curriculo[0]}")
            print(f"     Turno: {curriculo[2]}")
            print(f"     Prazo Ideal: {curriculo[3]}")
            print(f"     Prazo Máx: {curriculo[4]}")
            print(f"     Situação: {curriculo[5]}")
        
        # Mostrar estatísticas por curso
        cursos_com_curriculos = LyCurriculoModel.get_cursos_com_curriculos(db_name=config.DB_NAME)
        if cursos_com_curriculos:
            print(f"\n📊 Cursos com currículos disponíveis: {len(cursos_com_curriculos)}")
            print("📋 Primeiros 10 cursos:")
            for i, curso in enumerate(cursos_com_curriculos[:10]):
                print(f"  {i+1}. Curso {curso}")
    
    def run(self):
        """Executa o processo completo de sincronização"""
        print("="*60)
        print("SISTEMA DE SINCRONIZAÇÃO DE CURRÍCULOS - LY_CURRICULOS")
        print(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print("="*60)
        
        try:
            # 1. Inicializar banco
            self.initialize_database()
            
            # 2. Resumo inicial
            resumo_inicial = self.get_initial_summary()
            
            # 3. Buscar currículos da API
            curriculos = self.buscar_curriculos()
            if not curriculos:
                return
            
            # 4. Processar currículos
            curriculos_processados = self.processar_curriculos(curriculos)
            
            # 5. Importar para banco
            self.importar_para_banco(curriculos_processados)
            
            # 6. Resumo final
            resumo_final = LyCurriculoModel.get_summary(config.DB_NAME)
            
            print(f"\n{'='*50}")
            print("RESUMO FINAL")
            print(f"{'='*50}")
            
            print(f"\n📊 SITUAÇÃO DA TABELA LY_CURRICULOS:")
            print(f"   Total de currículos: {resumo_final['total_curriculos']}")
            print(f"   Cursos distintos: {resumo_final['cursos_distintos']}")
            print(f"   Turnos distintos: {resumo_final['turnos_distintos']}")
            print(f"   Situações distintas: {resumo_final['situacoes_distintas']}")
            print(f"   Média prazo ideal: {resumo_final['media_prazo_ideal']}")
            print(f"   Média prazo máximo: {resumo_final['media_prazo_max']}")
            
            print(f"\n📊 RESULTADO DA SINCRONIZAÇÃO:")
            print(f"   Currículos encontrados na API: {self.total_curriculos}")
            print(f"   Currículos inseridos/atualizados: {self.inseridos}")
            print(f"   Erros: {self.erros}")
            
            print(f"\n📈 VARIAÇÃO DESTA EXECUÇÃO:")
            print(f"   Total de currículos: {resumo_inicial['total_curriculos']} → {resumo_final['total_curriculos']}")
            print(f"   Diferença: {resumo_final['total_curriculos'] - resumo_inicial['total_curriculos']}")
            
            # 7. Mostrar exemplos
            self.mostrar_exemplos()
            
            print(f"\n{'='*60}")
            print("✅ SINCORNIZAÇÃO DE LY_CURRICULOS CONCLUÍDA COM SUCESSO!")
            print(f"{'='*60}")
            print(f"\n💡 Banco de dados: {config.DB_NAME}")
            print(f"📊 Total de currículos sincronizados: {self.total_curriculos}")
            print("👋 Processo finalizado!")
            
        except Exception as e:
            print(f"\n❌ Erro durante a sincronização: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

def main():
    """Função principal"""
    sync = LyCurriculoSync()
    sync.run()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Processo interrompido pelo usuário")
        sys.exit(0)