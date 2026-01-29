#!/usr/bin/env python3
"""
Sincronização da tabela LY_CURSO
COM chave primária no campo 'curso' - faz upsert (insert/update)
"""
import sys
import os
import time
import logging
from datetime import datetime

# Adiciona diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importações internas
from core.config import config
from core.api_client import CursoAPIClient
from models.ly_curso import LyCursoModel

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def sincronizar_cursos():
    """Executa a sincronização completa da tabela LY_CURSO"""
    print("=" * 60)
    print("SINCRONIZAÇÃO DA TABELA LY_CURSO")
    print(f"Início: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        # 1. Criar/verificar tabela
        print("\n[1/4] 📋 Criando/verificando tabela LY_CURSO...")
        LyCursoModel.create_table()
        
        # Resumo inicial
        resumo_inicial = LyCursoModel.get_summary()
        print(f"   Total inicial: {resumo_inicial.get('total_cursos', 0)} cursos")
        print(f"   Cursos ativos: {resumo_inicial.get('cursos_ativos', 0)}")
        print(f"   Modalidades distintas: {resumo_inicial.get('modalidades_distintas', 0)}")
        
        # 2. Buscar dados da API
        print("\n[2/4] 🔗 Conectando e buscando dados da API...")
        print(f"   URL: {config.LYCEUM_BASE_URL}")
        print(f"   Endpoint: /v2/tabela/cursos")
        print(f"   Paginação: page=0, size={config.API_PAGE_SIZE}")
        
        client = CursoAPIClient()
        cursos = client.get_cursos()
        
        if not cursos:
            print("   ❌ Nenhum dado retornado pela API")
            return False
        
        print(f"   ✅ Total retornado pela API: {len(cursos)} cursos")
        
        # Filtrar registros válidos (com código de curso)
        cursos_validos = []
        cursos_sem_codigo = 0
        
        for c in cursos:
            if c.get('curso'):
                cursos_validos.append(c)
            else:
                cursos_sem_codigo += 1
        
        if cursos_sem_codigo > 0:
            print(f"   ⚠️  Cursos sem código: {cursos_sem_codigo}")
        
        print(f"   📊 Cursos válidos para processamento: {len(cursos_validos)}")
        
        if len(cursos_validos) == 0:
            print("   ⚠️  Nenhum curso válido encontrado")
            return True  # Considera sucesso, mas sem dados
        
        # Mostrar amostra e estatísticas
        if cursos_validos:
            primeiro = cursos_validos[0]
            print(f"   📋 Amostra do primeiro curso:")
            print(f"      Código: {primeiro.get('curso')}")
            print(f"      Nome: {primeiro.get('nome', 'N/A')[:30]}...")
            print(f"      Modalidade: {primeiro.get('modalidade', 'N/A')}")
            print(f"      Nível: {primeiro.get('nivel', 'N/A')}")
            print(f"      Ativo: {primeiro.get('ativo', 'N/A')}")
            
            # Estatísticas básicas
            ativos = sum(1 for c in cursos_validos if c.get('ativo') == 'S')
            inativos = len(cursos_validos) - ativos
            
            print(f"   📈 Estatísticas dos dados:")
            print(f"      Total: {len(cursos_validos)}")
            print(f"      Ativos: {ativos}")
            print(f"      Inativos: {inativos}")
            
            # Contar modalidades
            modalidades = {}
            for c in cursos_validos:
                modalidade = c.get('modalidade', 'Não informado')
                modalidades[modalidade] = modalidades.get(modalidade, 0) + 1
            
            print(f"   🎯 Distribuição por modalidade:")
            for modalidade, count in sorted(modalidades.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"      {modalidade}: {count} cursos")
            
            # Contar níveis
            niveis = {}
            for c in cursos_validos:
                nivel = c.get('nivel', 'Não informado')
                niveis[nivel] = niveis.get(nivel, 0) + 1
            
            print(f"   📊 Distribuição por nível:")
            for nivel, count in sorted(niveis.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"      {nivel}: {count} cursos")
        
        # 3. Inserir/Atualizar no banco (Upsert)
        print(f"\n[3/4] 💾 Gravando {len(cursos_validos)} cursos no banco (Upsert)...")
        print(f"   Operação: INSERT OR REPLACE (atualiza se já existe)")
        
        total_processados = LyCursoModel.batch_upsert(cursos_validos)
        
        # 4. Resumo final
        tempo_total = time.time() - start_time
        resumo_final = LyCursoModel.get_summary()
        
        print(f"\n[4/4] 📊 Gerando resumo...")
        
        print("\n" + "=" * 60)
        print("RESUMO DA SINCRONIZAÇÃO")
        print("=" * 60)
        
        print(f"\n📈 DADOS DA API:")
        print(f"   Total retornado: {len(cursos)} cursos")
        print(f"   Válidos para processamento: {len(cursos_validos)}")
        if cursos_sem_codigo > 0:
            print(f"   Inválidos (sem código): {cursos_sem_codigo}")
        
        print(f"\n🗃️  OPERAÇÕES NO BANCO:")
        print(f"   Processados com sucesso: {total_processados}")
        if len(cursos_validos) > total_processados:
            print(f"   Cursos com erro: {len(cursos_validos) - total_processados}")
        
        print(f"\n📊 SITUAÇÃO DO BANCO:")
        print(f"   Antes da sincronização: {resumo_inicial.get('total_cursos', 0)} cursos")
        print(f"   Após a sincronização: {resumo_final.get('total_cursos', 0)} cursos")
        print(f"   Cursos ativos: {resumo_final.get('cursos_ativos', 0)}")
        print(f"   Modalidades distintas: {resumo_final.get('modalidades_distintas', 0)}")
        print(f"   Níveis distintos: {resumo_final.get('niveis_distintos', 0)}")
        
        if resumo_final.get('ultima_atualizacao'):
            print(f"   Última atualização: {resumo_final['ultima_atualizacao']}")
        
        print(f"\n⏱️  PERFORMANCE:")
        print(f"   Tempo total: {tempo_total:.2f} segundos")
        
        if len(cursos_validos) > 0:
            taxa = len(cursos_validos) / tempo_total
            print(f"   Taxa: {taxa:.2f} cursos/segundo")
        
        print("\n" + "=" * 60)
        
        if total_processados == len(cursos_validos):
            print("✅ SINCRONIZAÇÃO CONCLUÍDA COM SUCESSO!")
        else:
            print(f"⚠️  SINCRONIZAÇÃO PARCIALMENTE CONCLUÍDA ({total_processados}/{len(cursos_validos)})")
        
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO NA SINCRONIZAÇÃO: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Função principal"""
    print("🚀 Iniciando sincronização de cursos...")
    
    try:
        # Verificar configurações
        if not all([config.LYCEUM_BASE_URL, config.LYCEUM_USERNAME, config.LYCEUM_PASSWORD]):
            print("❌ Configurações da API incompletas no arquivo .env")
            print("   Verifique: API_BASE_URL, API_USERNAME, API_PASSWORD")
            return False
        
        # Executar sincronização
        sucesso = sincronizar_cursos()
        
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