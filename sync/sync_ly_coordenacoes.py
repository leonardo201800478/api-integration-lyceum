#!/usr/bin/env python3
"""
Sincronização da tabela LY_COORDENACAO
Baseado no padrão sync_ly_docentes.py
API: GET com paginação - traz TODOS os dados
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
from core.api_client import get_coordenacao_client
from models.ly_coordenacao import LyCoordenacaoModel

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def sincronizar_coordenacoes(forcar_recriar_tabela=False):
    """Executa a sincronização completa da tabela LY_COORDENACAO"""
    print("=" * 60)
    print("SINCRONIZAÇÃO DA TABELA LY_COORDENACAO")
    print(f"Início: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    if forcar_recriar_tabela:
        print("🔧 MODE: Forçar recriação da tabela")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        # 1. Criar/verificar tabela
        print("\n[1/4] 📋 Criando/verificando tabela LY_COORDENACAO...")
        
        if forcar_recriar_tabela:
            print("   🔨 Forçando recriação da tabela...")
            LyCoordenacaoModel.drop_and_recreate_table()
        else:
            LyCoordenacaoModel.create_table()
        
        # Resumo inicial
        resumo_inicial = LyCoordenacaoModel.get_summary()
        print(f"   Total inicial: {resumo_inicial.get('total_coordenacoes', 0)} coordenações")
        print(f"   Cursos distintos: {resumo_inicial.get('cursos_distintos', 0)}")
        print(f"   Funcionários distintos: {resumo_inicial.get('funcionarios_distintos', 0)}")
        
        # 2. Buscar dados da API
        print("\n[2/4] 🔗 Conectando e buscando dados da API...")
        print(f"   URL: {config.LYCEUM_BASE_URL}")
        print(f"   Endpoint: /v2/tabela/coordenacao")
        print(f"   Método: GET (paginação)")
        print(f"   Parâmetros: page=0, size={config.API_PAGE_SIZE}")
        print(f"   Delay entre requisições: {config.API_DELAY_BETWEEN_REQUESTS}s")
        
        client = get_coordenacao_client()
        
        # Buscar dados via paginação
        coordenacoes = client.get_coordenacoes()
        
        if not coordenacoes:
            print("   ❌ Nenhum dado retornado pela API")
            return False
        
        print(f"   ✅ Total retornado pela API: {len(coordenacoes)} registros")
        
        # Mostrar estrutura dos dados
        print(f"\n   📊 Análise dos dados recebidos:")
        
        # Contar tipos de dados
        tipos = {}
        for i, registro in enumerate(coordenacoes[:5]):  # Analisar apenas os primeiros 5
            if isinstance(registro, dict):
                print(f"\n   📋 Registro {i+1}:")
                for campo, valor in registro.items():
                    tipo = type(valor).__name__
                    if campo not in tipos:
                        tipos[campo] = tipo
                    print(f"      {campo}: {valor} ({tipo})")
            else:
                print(f"   ⚠️  Registro {i+1} não é dicionário: {type(registro)}")
        
        # Contar campos únicos
        campos_unicos = set()
        for registro in coordenacoes:
            if isinstance(registro, dict):
                campos_unicos.update(registro.keys())
        
        print(f"\n   🔍 Total de campos únicos encontrados: {len(campos_unicos)}")
        print(f"   📝 Lista de campos: {', '.join(sorted(campos_unicos))}")
        
        # Processar todos os registros
        coordenacoes_processadas = []
        registros_invalidos = 0
        
        for i, registro in enumerate(coordenacoes):
            if not isinstance(registro, dict):
                registros_invalidos += 1
                if i < 10:  # Logar apenas os primeiros 10 erros
                    logger.warning(f"Registro {i} não é um dicionário: {type(registro)}")
                continue
            
            # Limpar valores vazios
            registro_limpo = {}
            for campo, valor in registro.items():
                if valor is not None:
                    # Converter para string se não for string nem número
                    if not isinstance(valor, (str, int, float, bool)):
                        valor = str(valor)
                    registro_limpo[campo] = valor
            
            coordenacoes_processadas.append(registro_limpo)
        
        if registros_invalidos > 0:
            print(f"   ⚠️  Registros com formato inválido: {registros_invalidos}")
        
        print(f"   📊 Registros válidos para processamento: {len(coordenacoes_processadas)}")
        
        if len(coordenacoes_processadas) == 0:
            print("   ⚠️  Nenhum registro para processar")
            return True
        
        # 3. Limpar tabela existente
        print(f"\n[3/4] 🧹 Limpando tabela existente...")
        LyCoordenacaoModel.clear_table()
        
        # 4. Inserir no banco
        print(f"\n[4/4] 💾 Inserindo {len(coordenacoes_processadas)} registros no banco...")
        
        total_processados = LyCoordenacaoModel.batch_insert(coordenacoes_processadas)
        
        # 5. Resumo final
        tempo_total = time.time() - start_time
        resumo_final = LyCoordenacaoModel.get_summary()
        
        print(f"\n[5/5] 📊 Gerando resumo...")
        
        print("\n" + "=" * 60)
        print("RESUMO DA SINCRONIZAÇÃO")
        print("=" * 60)
        
        print(f"\n📈 DADOS DA API:")
        print(f"   Total retornado: {len(coordenacoes)} registros")
        print(f"   Válidos para processamento: {len(coordenacoes_processadas)}")
        if registros_invalidos > 0:
            print(f"   Inválidos (formato): {registros_invalidos}")
        
        print(f"\n🗃️  OPERAÇÕES NO BANCO:")
        print(f"   Inseridos com sucesso: {total_processados}")
        if len(coordenacoes_processadas) > total_processados:
            print(f"   Registros com erro: {len(coordenacoes_processadas) - total_processados}")
        
        print(f"\n📊 SITUAÇÃO DO BANCO:")
        print(f"   Antes da sincronização: {resumo_inicial.get('total_coordenacoes', 0)} registros")
        print(f"   Após a sincronização: {resumo_final.get('total_coordenacoes', 0)} registros")
        print(f"   Cursos distintos: {resumo_final.get('cursos_distintos', 0)}")
        print(f"   Funcionários distintos: {resumo_final.get('funcionarios_distintos', 0)}")
        print(f"   Tipos de coordenação: {resumo_final.get('tipos_coordenacao', 0)}")
        
        if resumo_final.get('ultima_atualizacao'):
            print(f"   Última atualização: {resumo_final['ultima_atualizacao']}")
        
        print(f"\n⏱️  PERFORMANCE:")
        print(f"   Tempo total: {tempo_total:.2f} segundos")
        
        if len(coordenacoes_processadas) > 0:
            taxa = len(coordenacoes_processadas) / tempo_total
            print(f"   Taxa: {taxa:.2f} registros/segundo")
        
        print("\n" + "=" * 60)
        
        if total_processados == len(coordenacoes_processadas):
            print("✅ SINCRONIZAÇÃO CONCLUÍDA COM SUCESSO!")
        else:
            print(f"⚠️  SINCRONIZAÇÃO PARCIALMENTE CONCLUÍDA ({total_processados}/{len(coordenacoes_processadas)})")
        
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO NA SINCRONIZAÇÃO: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Função principal"""
    print("🚀 Iniciando sincronização de coordenações...")
    
    try:
        # Verificar argumentos da linha de comando
        forcar_recriar = False
        if len(sys.argv) > 1:
            if sys.argv[1] == '--recriar-tabela':
                forcar_recriar = True
                print("⚠️  Modo: Forçar recriação da tabela ativado")
        
        # Verificar configurações
        if not all([config.LYCEUM_BASE_URL, config.LYCEUM_USERNAME, config.LYCEUM_PASSWORD]):
            print("❌ Configurações da API incompletas no arquivo .env")
            print("   Verifique: API_BASE_URL, API_USERNAME, API_PASSWORD")
            return False
        
        # Executar sincronização
        sucesso = sincronizar_coordenacoes(forcar_recriar_tabela=forcar_recriar)
        
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
    print("\n📝 Uso: python sync/sync_ly_coordenacoes.py [--recriar-tabela]")
    print("   --recriar-tabela: Força a recriação da tabela (útil para corrigir problemas de estrutura)")
    print("=" * 60)
    
    sucesso = main()
    sys.exit(0 if sucesso else 1)