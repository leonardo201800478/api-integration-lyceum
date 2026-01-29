#!/usr/bin/env python3
"""
Sincronização da tabela LY_TURMA_DOCENTE
Usando APENAS GET com o APIClient existente do projeto
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
from core.api_client import get_turma_docente_client
from models.ly_turma_docente import LyTurmaDocenteModel

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def sincronizar_turma_docentes():
    """Executa a sincronização completa da tabela LY_TURMA_DOCENTE usando APENAS GET"""
    print("=" * 60)
    print("SINCRONIZAÇÃO DA TABELA LY_TURMA_DOCENTE")
    print("🚫 MODO: APENAS LEITURA (GET) - Banco produção NÃO alterado")
    print(f"Início: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        # 1. Criar/verificar tabela LOCAL
        print("\n[1/4] 📋 Criando/verificando tabela LOCAL...")
        LyTurmaDocenteModel.create_table()
        
        # Resumo inicial
        resumo_inicial = LyTurmaDocenteModel.get_summary()
        print(f"   Total inicial: {resumo_inicial.get('total_registros', 0)} registros")
        print(f"   Turmas distintas: {resumo_inicial.get('turmas_distintas', 0)}")
        print(f"   Docentes distintos: {resumo_inicial.get('docentes_distintos', 0)}")
        
        # 2. Buscar dados da API usando APENAS GET
        print("\n[2/4] 🔗 Buscando dados da API (APENAS GET)...")
        print(f"   URL: {config.LYCEUM_BASE_URL}")
        print(f"   Endpoint: /v2/tabela/turma-docente")
        print(f"   Método: GET (somente leitura)")
        print(f"   Paginação: page={config.API_PAGE_START}, size={config.API_PAGE_SIZE}")
        
        # Usar o cliente existente que implementa APENAS GET
        client = get_turma_docente_client()
        
        # Verificar conexão
        print(f"   🔍 Testando conexão com API...")
        test_data = client.get("/v2/tabela/turma-docente", params={"page": 0, "size": 1})
        if test_data is None:
            print("   ❌ Falha na conexão com API")
            return False
        print("   ✅ Conexão com API estabelecida")
        
        # Buscar todos os dados usando APENAS GET via paginação
        print(f"   📥 Iniciando busca paginada (APENAS GET)...")
        turma_docentes = client.get_turmas_docentes()
        
        if not turma_docentes:
            print("   ⚠️  Nenhum dado retornado pela API (pode estar vazia)")
            return True
        
        print(f"   ✅ Total retornado pela API: {len(turma_docentes)} registros")
        
        # Filtrar registros válidos
        registros_validos = []
        registros_invalidos = 0
        
        for td in turma_docentes:
            if td.get('chave'):
                registros_validos.append(td)
            else:
                registros_invalidos += 1
        
        if registros_invalidos > 0:
            print(f"   ⚠️  Registros inválidos (sem chave): {registros_invalidos}")
        
        print(f"   📊 Registros válidos para processamento: {len(registros_validos)}")
        
        if len(registros_validos) == 0:
            print("   ⚠️  Nenhum registro válido encontrado")
            return True
        
        # Mostrar amostra
        if registros_validos:
            primeiro = registros_validos[0]
            print(f"   📋 Amostra do primeiro registro:")
            print(f"      Chave: {primeiro.get('chave')}")
            print(f"      Turma: {primeiro.get('turma')}")
            print(f"      Disciplina: {primeiro.get('disciplina')}")
            print(f"      Docente: {primeiro.get('num_func')}")
        
        # 3. Limpar tabela LOCAL (apenas banco local)
        print(f"\n[3/4] 🧹 Limpando tabela LOCAL (lyceum.db)...")
        LyTurmaDocenteModel.clear_table()
        
        # 4. Inserir no banco LOCAL (apenas banco local)
        print(f"\n[4/4] 💾 Inserindo {len(registros_validos)} registros no banco LOCAL...")
        
        total_processadas = LyTurmaDocenteModel.batch_insert(registros_validos)
        
        # 5. Resumo final
        tempo_total = time.time() - start_time
        resumo_final = LyTurmaDocenteModel.get_summary()
        
        print(f"\n" + "=" * 60)
        print("📊 RESUMO DA SINCRONIZAÇÃO")
        print("=" * 60)
        
        print(f"\n🔒 GARANTIAS DE SEGURANÇA:")
        print(f"   ✅ Método usado na API: APENAS GET")
        print(f"   ✅ Banco produção: NENHUMA alteração")
        print(f"   ✅ Banco local: Atualizado com sucesso")
        
        print(f"\n📈 DADOS DA API (APENAS LEITURA):")
        print(f"   Total retornado: {len(turma_docentes)} registros")
        print(f"   Válidos para processamento: {len(registros_validos)}")
        
        print(f"\n🗃️  OPERAÇÕES NO BANCO LOCAL:")
        print(f"   Antes da sincronização: {resumo_inicial.get('total_registros', 0)} registros")
        print(f"   Após a sincronização: {resumo_final.get('total_registros', 0)} registros")
        print(f"   Inseridos com sucesso: {total_processadas}")
        
        print(f"\n📊 ESTATÍSTICAS FINAIS:")
        print(f"   Turmas distintas: {resumo_final.get('turmas_distintas', 0)}")
        print(f"   Disciplinas distintas: {resumo_final.get('disciplinas_distintas', 0)}")
        print(f"   Docentes distintos: {resumo_final.get('docentes_distintos', 0)}")
        
        print(f"\n⏱️  PERFORMANCE:")
        print(f"   Tempo total: {tempo_total:.2f} segundos")
        if len(registros_validos) > 0:
            taxa = len(registros_validos) / tempo_total
            print(f"   Taxa: {taxa:.2f} registros/segundo")
        
        print("\n" + "=" * 60)
        
        if total_processadas == len(registros_validos):
            print("✅ SINCRONIZAÇÃO CONCLUÍDA COM SUCESSO!")
        else:
            print(f"⚠️  SINCRONIZAÇÃO PARCIAL ({total_processadas}/{len(registros_validos)})")
        
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO NA SINCRONIZAÇÃO: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Função principal"""
    print("🚀 Sincronizador LY_TURMA_DOCENTE")
    print("🔒 Garantia: APENAS método GET na API - Banco produção protegido\n")
    
    try:
        # Verificar configurações
        if not all([config.LYCEUM_BASE_URL, config.LYCEUM_USERNAME, config.LYCEUM_PASSWORD]):
            print("❌ Configurações da API incompletas")
            print("   Verifique seu arquivo .env:")
            print("   - LYCEUM_BASE_URL")
            print("   - LYCEUM_USERNAME") 
            print("   - LYCEUM_PASSWORD")
            return False
        
        # Executar sincronização
        sucesso = sincronizar_turma_docentes()
        
        if sucesso:
            print("\n✨ Processo concluído com segurança!")
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