#!/usr/bin/env python3
"""
Sincronização simples da tabela LY_CURRICULO
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
from core.api_client import CurriculoAPIClient
from models.ly_curriculo import LyCurriculoModel

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def sincronizar_curriculos():
    """Executa a sincronização completa"""
    print("=" * 60)
    print("SINCRONIZAÇÃO DA TABELA LY_CURRICULO")
    print(f"Início: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        # 1. Criar/verificar tabela
        print("\n[1/4] 📋 Criando/verificando tabela LY_CURRICULO...")
        LyCurriculoModel.create_table()
        
        # Resumo inicial
        resumo_inicial = LyCurriculoModel.get_summary()
        print(f"   Total inicial: {resumo_inicial.get('total_curriculos', 0)} registros")
        
        # 2. Buscar dados da API
        print("\n[2/4] 🔗 Conectando e buscando dados da API...")
        print(f"   URL: {config.LYCEUM_BASE_URL}")
        print(f"   Endpoint: /v2/tabela/curriculos")
        
        client = CurriculoAPIClient()
        curriculos = client.get_curriculos()
        
        if not curriculos:
            print("   ❌ Nenhum dado retornado pela API")
            return False
        
        print(f"   ✅ Total retornado pela API: {len(curriculos)} registros")
        
        # Filtrar registros válidos
        curriculos_validos = []
        for c in curriculos:
            if c.get('curriculo') and c.get('curso'):
                curriculos_validos.append(c)
        
        print(f"   📊 Registros válidos para processamento: {len(curriculos_validos)}")
        
        if len(curriculos_validos) == 0:
            print("   ⚠️  Nenhum registro válido encontrado")
            return True  # Considera sucesso, mas sem dados
        
        # Mostrar amostra
        if curriculos_validos:
            primeiro = curriculos_validos[0]
            print(f"   📋 Amostra do primeiro registro:")
            print(f"      Currículo: {primeiro.get('curriculo')}")
            print(f"      Curso: {primeiro.get('curso')}")
            print(f"      Turno: {primeiro.get('turno', 'N/A')}")
            print(f"      Situação: {primeiro.get('situacao', 'N/A')}")
        
        # 3. Inserir/Atualizar no banco
        print(f"\n[3/4] 💾 Gravando {len(curriculos_validos)} registros no banco...")
        
        total_processados = LyCurriculoModel.batch_upsert(curriculos_validos)
        
        # 4. Resumo final
        tempo_total = time.time() - start_time
        resumo_final = LyCurriculoModel.get_summary()
        
        print(f"\n[4/4] 📊 Gerando resumo...")
        
        print("\n" + "=" * 60)
        print("RESUMO DA SINCRONIZAÇÃO")
        print("=" * 60)
        
        print(f"\n📈 DADOS DA API:")
        print(f"   Total retornado: {len(curriculos)}")
        print(f"   Válidos para processamento: {len(curriculos_validos)}")
        
        print(f"\n🗃️  OPERAÇÕES NO BANCO:")
        print(f"   Processados com sucesso: {total_processados}")
        if len(curriculos_validos) > total_processados:
            print(f"   Registros com erro: {len(curriculos_validos) - total_processados}")
        
        print(f"\n📊 SITUAÇÃO DO BANCO:")
        print(f"   Antes da sincronização: {resumo_inicial.get('total_curriculos', 0)} registros")
        print(f"   Após a sincronização: {resumo_final.get('total_curriculos', 0)} registros")
        print(f"   Cursos distintos: {resumo_final.get('cursos_distintos', 0)}")
        
        if resumo_final.get('ultima_atualizacao'):
            print(f"   Última atualização: {resumo_final['ultima_atualizacao']}")
        
        print(f"\n⏱️  PERFORMANCE:")
        print(f"   Tempo total: {tempo_total:.2f} segundos")
        
        if len(curriculos_validos) > 0:
            taxa = len(curriculos_validos) / tempo_total
            print(f"   Taxa: {taxa:.2f} registros/segundo")
        
        print("\n" + "=" * 60)
        
        if total_processados == len(curriculos_validos):
            print("✅ SINCRONIZAÇÃO CONCLUÍDA COM SUCESSO!")
        else:
            print(f"⚠️  SINCRONIZAÇÃO PARCIALMENTE CONCLUÍDA ({total_processados}/{len(curriculos_validos)})")
        
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO NA SINCRONIZAÇÃO: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Função principal"""
    print("🚀 Iniciando sincronização de currículos...")
    
    try:
        # Verificar configurações
        if not all([config.LYCEUM_BASE_URL, config.LYCEUM_USERNAME, config.LYCEUM_PASSWORD]):
            print("❌ Configurações da API incompletas no arquivo .env")
            print("   Verifique: API_BASE_URL, API_USERNAME, API_PASSWORD")
            return False
        
        # Executar sincronização
        sucesso = sincronizar_curriculos()
        
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