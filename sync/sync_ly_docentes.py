#!/usr/bin/env python3
"""
Sincronização da tabela LY_DOCENTE
SEM chave primária fixa - seguindo o padrão LY_TURMA
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
from core.api_client import DocenteAPIClient
from models.ly_docente import LyDocenteModel

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def sincronizar_docentes():
    """Executa a sincronização completa da tabela LY_DOCENTE"""
    print("=" * 60)
    print("SINCRONIZAÇÃO DA TABELA LY_DOCENTE")
    print(f"Início: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        # 1. Criar/verificar tabela
        print("\n[1/4] 📋 Criando/verificando tabela LY_DOCENTE...")
        LyDocenteModel.create_table()
        
        # Resumo inicial
        resumo_inicial = LyDocenteModel.get_summary()
        print(f"   Total inicial: {resumo_inicial.get('total_docentes', 0)} docentes")
        print(f"   Docentes ativos: {resumo_inicial.get('ativos', 0)}")
        print(f"   Departamentos distintos: {resumo_inicial.get('deptos_distintos', 0)}")
        
        # 2. Buscar dados da API
        print("\n[2/4] 🔗 Conectando e buscando dados da API...")
        print(f"   URL: {config.LYCEUM_BASE_URL}")
        print(f"   Endpoint: /v2/tabela/docente")
        print(f"   Paginação: page=0, size={config.API_PAGE_SIZE}")
        
        client = DocenteAPIClient()
        docentes = client.get_docentes()
        
        if not docentes:
            print("   ❌ Nenhum dado retornado pela API")
            return False
        
        print(f"   ✅ Total retornado pela API: {len(docentes)} docentes")
        
        # Filtrar registros válidos (com campos obrigatórios)
        docentes_validos = []
        docentes_invalidos = 0
        
        for d in docentes:
            # Campos obrigatórios: cpf, num_func
            if all([d.get('cpf'), d.get('num_func')]):
                docentes_validos.append(d)
            else:
                docentes_invalidos += 1
        
        if docentes_invalidos > 0:
            print(f"   ⚠️  Docentes inválidos (sem campos obrigatórios): {docentes_invalidos}")
        
        print(f"   📊 Docentes válidos para processamento: {len(docentes_validos)}")
        
        if len(docentes_validos) == 0:
            print("   ⚠️  Nenhum docente válido encontrado")
            return True  # Considera sucesso, mas sem dados
        
        # Mostrar amostra e estatísticas
        if docentes_validos:
            primeiro = docentes_validos[0]
            print(f"   📋 Amostra do primeiro docente:")
            print(f"      CPF: {primeiro.get('cpf')}")
            print(f"      Número Funcional: {primeiro.get('num_func')}")
            print(f"      Nome: {primeiro.get('nome_compl', 'N/A')}")
            print(f"      Email: {primeiro.get('email', 'N/A')}")
            print(f"      Departamento: {primeiro.get('depto', 'N/A')}")
            print(f"      Ativo: {primeiro.get('ativo', 'N/A')}")
            print(f"      Titulação: {primeiro.get('titulacao', 'N/A')}")
            
            # Estatísticas básicas
            ativos = sum(1 for d in docentes_validos if d.get('ativo') == 'S')
            inativos = len(docentes_validos) - ativos
            
            print(f"   📈 Estatísticas dos dados:")
            print(f"      Total: {len(docentes_validos)}")
            print(f"      Ativos: {ativos}")
            print(f"      Inativos: {inativos}")
            
            # Contar por departamento
            deptos = Counter()
            for d in docentes_validos:
                depto = d.get('depto', 'Não informado')
                deptos[depto] += 1
            
            print(f"   🏢 Distribuição por departamento (top 10):")
            for depto, count in deptos.most_common(10):
                print(f"      {depto}: {count} docentes")
            
            # Contar por titulação
            titulacoes = Counter()
            for d in docentes_validos:
                titulacao = d.get('titulacao', 'Não informado')
                titulacoes[titulacao] += 1
            
            print(f"   🎓 Distribuição por titulação (top 5):")
            for titulacao, count in titulacoes.most_common(5):
                print(f"      {titulacao}: {count} docentes")
            
            # Analisar combinações únicas
            combinacoes = set()
            for d in docentes_validos:
                chave = f"{d.get('cpf')}-{d.get('num_func')}"
                combinacoes.add(chave)
            
            print(f"   🔍 Análise de combinações únicas:")
            print(f"      Registros totais: {len(docentes_validos)}")
            print(f"      Combinações únicas (cpf-num_func): {len(combinacoes)}")
            print(f"      Duplicatas: {len(docentes_validos) - len(combinacoes)}")
            
            # Mostrar duplicatas mais frequentes (se houver)
            if len(docentes_validos) > len(combinacoes):
                combinacoes_counter = Counter()
                for d in docentes_validos:
                    chave = f"{d.get('cpf')}-{d.get('num_func')}"
                    combinacoes_counter[chave] += 1
                
                print(f"   🔢 Docentes com múltiplas ocorrências (top 5):")
                for chave, count in combinacoes_counter.most_common(5):
                    if count > 1:
                        print(f"      {chave}: {count} ocorrências")
        
        # 3. Limpar tabela existente (sincronização completa)
        print(f"\n[3/4] 🧹 Limpando tabela existente...")
        LyDocenteModel.clear_table()
        
        # 4. Inserir no banco
        print(f"\n[4/4] 💾 Inserindo {len(docentes_validos)} docentes no banco...")
        
        total_processados = LyDocenteModel.batch_insert(docentes_validos)
        
        # 5. Resumo final
        tempo_total = time.time() - start_time
        resumo_final = LyDocenteModel.get_summary()
        
        print(f"\n[5/5] 📊 Gerando resumo...")
        
        print("\n" + "=" * 60)
        print("RESUMO DA SINCRONIZAÇÃO")
        print("=" * 60)
        
        print(f"\n📈 DADOS DA API:")
        print(f"   Total retornado: {len(docentes)} docentes")
        print(f"   Válidos para processamento: {len(docentes_validos)}")
        if docentes_invalidos > 0:
            print(f"   Inválidos (sem campos obrigatórios): {docentes_invalidos}")
        
        print(f"\n🗃️  OPERAÇÕES NO BANCO:")
        print(f"   Inseridos com sucesso: {total_processados}")
        if len(docentes_validos) > total_processados:
            print(f"   Docentes com erro: {len(docentes_validos) - total_processados}")
        
        print(f"\n📊 SITUAÇÃO DO BANCO:")
        print(f"   Antes da sincronização: {resumo_inicial.get('total_docentes', 0)} docentes")
        print(f"   Após a sincronização: {resumo_final.get('total_docentes', 0)} docentes")
        print(f"   Docentes ativos: {resumo_final.get('ativos', 0)}")
        print(f"   Docentes inativos: {resumo_final.get('inativos', 0)}")
        print(f"   Departamentos distintos: {resumo_final.get('deptos_distintos', 0)}")
        print(f"   CPFs distintos: {resumo_final.get('cpfs_distintos', 0)}")
        print(f"   Números funcionais distintos: {resumo_final.get('num_func_distintos', 0)}")
        
        if resumo_final.get('ultima_atualizacao'):
            print(f"   Última atualização: {resumo_final['ultima_atualizacao']}")
        
        print(f"\n⏱️  PERFORMANCE:")
        print(f"   Tempo total: {tempo_total:.2f} segundos")
        
        if len(docentes_validos) > 0:
            taxa = len(docentes_validos) / tempo_total
            print(f"   Taxa: {taxa:.2f} docentes/segundo")
        
        print("\n" + "=" * 60)
        
        if total_processados == len(docentes_validos):
            print("✅ SINCRONIZAÇÃO CONCLUÍDA COM SUCESSO!")
        else:
            print(f"⚠️  SINCRONIZAÇÃO PARCIALMENTE CONCLUÍDA ({total_processados}/{len(docentes_validos)})")
        
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO NA SINCRONIZAÇÃO: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Função principal"""
    print("🚀 Iniciando sincronização de docentes...")
    
    try:
        # Verificar configurações
        if not all([config.LYCEUM_BASE_URL, config.LYCEUM_USERNAME, config.LYCEUM_PASSWORD]):
            print("❌ Configurações da API incompletas no arquivo .env")
            print("   Verifique: API_BASE_URL, API_USERNAME, API_PASSWORD")
            return False
        
        # Executar sincronização
        sucesso = sincronizar_docentes()
        
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