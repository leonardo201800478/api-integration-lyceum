#!/usr/bin/env python3
"""
Sincronização da tabela LY_DISCIPLINA
SEM chave primária fixa - similar a LY_CURRICULO
"""
import sys
import os
import time
import logging
from datetime import datetime
from collections import Counter

# Adiciona diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importações internas
from core.config import config
from core.api_client import DisciplinaAPIClient
from models.ly_disciplina import LyDisciplinaModel

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def sincronizar_disciplinas():
    """Executa a sincronização completa da tabela LY_DISCIPLINA"""
    print("=" * 60)
    print("SINCRONIZAÇÃO DA TABELA LY_DISCIPLINA")
    print(f"Início: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        # 1. Criar/verificar tabela
        print("\n[1/4] 📋 Criando/verificando tabela LY_DISCIPLINA...")
        LyDisciplinaModel.create_table()
        
        # Resumo inicial
        resumo_inicial = LyDisciplinaModel.get_summary()
        print(f"   Total inicial: {resumo_inicial.get('total_disciplinas', 0)} disciplinas")
        print(f"   Disciplinas ativas: {resumo_inicial.get('disciplinas_ativas', 0)}")
        print(f"   Faculdades distintas: {resumo_inicial.get('faculdades_distintas', 0)}")
        
        # 2. Buscar dados da API
        print("\n[2/4] 🔗 Conectando e buscando dados da API...")
        print(f"   URL: {config.LYCEUM_BASE_URL}")
        print(f"   Endpoint: /v2/tabela/disciplinas")
        print(f"   Paginação: page=0, size={config.API_PAGE_SIZE}")
        
        client = DisciplinaAPIClient()
        disciplinas = client.get_disciplinas()
        
        if not disciplinas:
            print("   ❌ Nenhum dado retornado pela API")
            return False
        
        print(f"   ✅ Total retornado pela API: {len(disciplinas)} disciplinas")
        
        # Filtrar registros válidos (com código de disciplina)
        disciplinas_validas = []
        disciplinas_sem_codigo = 0
        
        for d in disciplinas:
            if d.get('disciplina'):
                disciplinas_validas.append(d)
            else:
                disciplinas_sem_codigo += 1
        
        if disciplinas_sem_codigo > 0:
            print(f"   ⚠️  Disciplinas sem código: {disciplinas_sem_codigo}")
        
        print(f"   📊 Disciplinas válidas para processamento: {len(disciplinas_validas)}")
        
        if len(disciplinas_validas) == 0:
            print("   ⚠️  Nenhuma disciplina válida encontrada")
            return True  # Considera sucesso, mas sem dados
        
        # Mostrar amostra e estatísticas
        if disciplinas_validas:
            primeiro = disciplinas_validas[0]
            print(f"   📋 Amostra da primeira disciplina:")
            print(f"      Código: {primeiro.get('disciplina')}")
            print(f"      Nome: {primeiro.get('nome', 'N/A')[:30]}...")
            print(f"      Ativa: {primeiro.get('ativo', 'N/A')}")
            print(f"      Faculdade: {primeiro.get('faculdade', 'N/A')}")
            print(f"      Créditos: {primeiro.get('creditos', 'N/A')}")
            print(f"      Horas aula: {primeiro.get('horas_aula', 'N/A')}")
            
            # Estatísticas básicas
            ativas = sum(1 for d in disciplinas_validas if d.get('ativo') == 'S')
            inativas = len(disciplinas_validas) - ativas
            
            print(f"   📈 Estatísticas dos dados:")
            print(f"      Total: {len(disciplinas_validas)}")
            print(f"      Ativas: {ativas}")
            print(f"      Inativas: {inativas}")
            
            # Contar faculdades
            faculdades = Counter()
            for d in disciplinas_validas:
                faculdade = d.get('faculdade', 'Não informado')
                faculdades[faculdade] += 1
            
            print(f"   🏛️  Distribuição por faculdade (top 5):")
            for faculdade, count in faculdades.most_common(5):
                print(f"      {faculdade}: {count} disciplinas")
            
            # Contar departamentos
            departamentos = Counter()
            for d in disciplinas_validas:
                depto = d.get('depto', 'Não informado')
                departamentos[depto] += 1
            
            print(f"   🏢 Distribuição por departamento (top 5):")
            for depto, count in departamentos.most_common(5):
                print(f"      {depto}: {count} disciplinas")
            
            # Analisar duplicatas nos dados da API
            disciplinas_set = set()
            for d in disciplinas_validas:
                chave = d.get('disciplina')
                if chave:
                    disciplinas_set.add(chave)
            
            print(f"   🔍 Análise de códigos de disciplina:")
            print(f"      Registros totais: {len(disciplinas_validas)}")
            print(f"      Códigos únicos de disciplina: {len(disciplinas_set)}")
            print(f"      Duplicatas: {len(disciplinas_validas) - len(disciplinas_set)}")
            
            # Mostrar disciplinas com mais ocorrências (se houver duplicatas)
            if len(disciplinas_validas) > len(disciplinas_set):
                codigos_counter = Counter()
                for d in disciplinas_validas:
                    codigo = d.get('disciplina')
                    if codigo:
                        codigos_counter[codigo] += 1
                
                print(f"   🔢 Disciplinas com múltiplas ocorrências (top 5):")
                for codigo, count in codigos_counter.most_common(5):
                    if count > 1:
                        print(f"      {codigo}: {count} ocorrências")
        
        # 3. Limpar tabela existente (sincronização completa)
        print(f"\n[3/4] 🧹 Limpando tabela existente...")
        LyDisciplinaModel.clear_table()
        
        # 4. Inserir no banco
        print(f"\n[4/4] 💾 Inserindo {len(disciplinas_validas)} disciplinas no banco...")
        
        total_processadas = LyDisciplinaModel.batch_insert(disciplinas_validas)
        
        # 5. Resumo final
        tempo_total = time.time() - start_time
        resumo_final = LyDisciplinaModel.get_summary()
        
        print(f"\n[5/5] 📊 Gerando resumo...")
        
        print("\n" + "=" * 60)
        print("RESUMO DA SINCRONIZAÇÃO")
        print("=" * 60)
        
        print(f"\n📈 DADOS DA API:")
        print(f"   Total retornado: {len(disciplinas)} disciplinas")
        print(f"   Válidas para processamento: {len(disciplinas_validas)}")
        if disciplinas_sem_codigo > 0:
            print(f"   Inválidas (sem código): {disciplinas_sem_codigo}")
        
        print(f"\n🗃️  OPERAÇÕES NO BANCO:")
        print(f"   Inseridas com sucesso: {total_processadas}")
        if len(disciplinas_validas) > total_processadas:
            print(f"   Disciplinas com erro: {len(disciplinas_validas) - total_processadas}")
        
        print(f"\n📊 SITUAÇÃO DO BANCO:")
        print(f"   Antes da sincronização: {resumo_inicial.get('total_disciplinas', 0)} disciplinas")
        print(f"   Após a sincronização: {resumo_final.get('total_disciplinas', 0)} disciplinas")
        print(f"   Disciplinas distintas: {resumo_final.get('disciplinas_distintas', 0)}")
        print(f"   Disciplinas ativas: {resumo_final.get('disciplinas_ativas', 0)}")
        print(f"   Faculdades distintas: {resumo_final.get('faculdades_distintas', 0)}")
        print(f"   Departamentos distintos: {resumo_final.get('departamentos_distintos', 0)}")
        
        if resumo_final.get('ultima_atualizacao'):
            print(f"   Última atualização: {resumo_final['ultima_atualizacao']}")
        
        print(f"\n⏱️  PERFORMANCE:")
        print(f"   Tempo total: {tempo_total:.2f} segundos")
        
        if len(disciplinas_validas) > 0:
            taxa = len(disciplinas_validas) / tempo_total
            print(f"   Taxa: {taxa:.2f} disciplinas/segundo")
        
        print("\n" + "=" * 60)
        
        if total_processadas == len(disciplinas_validas):
            print("✅ SINCRONIZAÇÃO CONCLUÍDA COM SUCESSO!")
        else:
            print(f"⚠️  SINCRONIZAÇÃO PARCIALMENTE CONCLUÍDA ({total_processadas}/{len(disciplinas_validas)})")
        
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO NA SINCRONIZAÇÃO: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Função principal"""
    print("🚀 Iniciando sincronização de disciplinas...")
    
    try:
        # Verificar configurações
        if not all([config.LYCEUM_BASE_URL, config.LYCEUM_USERNAME, config.LYCEUM_PASSWORD]):
            print("❌ Configurações da API incompletas no arquivo .env")
            print("   Verifique: API_BASE_URL, API_USERNAME, API_PASSWORD")
            return False
        
        # Executar sincronização
        sucesso = sincronizar_disciplinas()
        
        if sucesso:
            print("\n✨ Processo concluído!")
            return True
        else:
            print("\n💥 Falha no processo!")
            return False
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Processo interrompido pelo usuário")
        return False


if __name__ == "__main__":
    sucesso = main()
    sys.exit(0 if sucesso else 1)