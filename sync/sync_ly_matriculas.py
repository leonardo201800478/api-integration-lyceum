#!/usr/bin/env python3
"""
Sincronização da tabela LY_MATRICULA com filtro por ano e semestre
"""
import sys
import os
import time
import logging
from datetime import datetime
from collections import Counter

# Adiciona diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importações internas - CORREÇÃO: IMPORTE CORRETAMENTE
from core.config import config
from core.database import get_db_connection  # ADICIONE ESTA LINHA
from models.ly_matricula import LyMatriculaModel

# Use o cliente já existente
from core.api_client import APIClientFactory

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def sincronizar_matriculas(ano: int = None, semestre: int = None):
    """
    Executa a sincronização da tabela LY_MATRICULA com filtros opcionais
    
    Args:
        ano: Ano para filtrar (opcional)
        semestre: Semestre para filtrar (opcional)
    """
    print("=" * 70)
    print("SINCRONIZAÇÃO DA TABELA LY_MATRICULA")
    
    # Mostrar filtros aplicados
    filtro_str = ""
    if ano is not None and semestre is not None:
        filtro_str = f" (Filtro: Ano={ano}, Semestre={semestre})"
    elif ano is not None:
        filtro_str = f" (Filtro: Ano={ano})"
    elif semestre is not None:
        filtro_str = f" (Filtro: Semestre={semestre})"
    
    print(filtro_str)
    print(f"Início: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 70)
    
    start_time = time.time()
    
    try:
        # 1. Criar/verificar tabela
        print("\n[1/4] 📋 Criando/verificando tabela LY_MATRICULA...")
        LyMatriculaModel.create_table()
        
        # Resumo inicial
        resumo_inicial = LyMatriculaModel.get_summary()
        print(f"   Total inicial: {resumo_inicial.get('total_matriculas', 0)} matrículas")
        
        # 2. Buscar dados da API com filtros
        print("\n[2/4] 🔗 Conectando e buscando dados da API...")
        
        # Use a fábrica para criar o cliente
        client = APIClientFactory.create_matricula_client()
        
        # Use o novo método com filtros
        print(f"   Buscando com filtros: ano={ano}, semestre={semestre}")
        
        # Verifique se o cliente tem o método com filtros
        if hasattr(client, 'get_matriculas_filtradas'):
            matriculas = client.get_matriculas_filtradas(ano=ano, semestre=semestre)
        else:
            # Fallback: busca todas e filtra localmente
            print("   ⚠️  Cliente não suporta filtros diretos, buscando tudo...")
            all_matriculas = client.get_matriculas()
            matriculas = []
            for m in all_matriculas:
                if ano is not None and m.get('ano') != ano:
                    continue
                if semestre is not None and m.get('semestre') != semestre:
                    continue
                matriculas.append(m)
        
        if not matriculas:
            print("   ⚠️  Nenhum dado retornado pela API")
            return True
        
        print(f"   ✅ Total retornado pela API: {len(matriculas)} matrículas")
        
        # 3. Limpar tabela existente
        print(f"\n[3/4] 🧹 Limpando tabela existente...")
        
        # CORREÇÃO: Use get_db_connection importado corretamente
        with get_db_connection(db_path=config.DB_LYCEUM_PATH) as conn:
            cursor = conn.cursor()
            
            if ano is not None and semestre is not None:
                cursor.execute(f"DELETE FROM {LyMatriculaModel.TABLE_NAME} WHERE ano = ? AND semestre = ?", 
                             (ano, semestre))
                print(f"   ✅ Limpadas matrículas do ano {ano} e semestre {semestre}")
            elif ano is not None:
                cursor.execute(f"DELETE FROM {LyMatriculaModel.TABLE_NAME} WHERE ano = ?", (ano,))
                print(f"   ✅ Limpadas matrículas do ano {ano}")
            elif semestre is not None:
                cursor.execute(f"DELETE FROM {LyMatriculaModel.TABLE_NAME} WHERE semestre = ?", (semestre,))
                print(f"   ✅ Limpadas matrículas do semestre {semestre}")
            else:
                cursor.execute(f"DELETE FROM {LyMatriculaModel.TABLE_NAME}")
                print(f"   ✅ Limpadas TODAS as matrículas")
            
            conn.commit()
        
        # 4. Inserir no banco
        print(f"\n[4/4] 💾 Inserindo {len(matriculas)} matrículas no banco...")
        
        total_processadas = LyMatriculaModel.batch_insert(matriculas)
        
        # 5. Resumo final
        tempo_total = time.time() - start_time
        resumo_final = LyMatriculaModel.get_summary()
        
        print(f"\n[5/5] 📊 Gerando resumo...")
        
        print("\n" + "=" * 70)
        print("RESUMO DA SINCRONIZAÇÃO")
        print("=" * 70)
        
        print(f"\n🎯 FILTROS APLICADOS:")
        if ano is not None and semestre is not None:
            print(f"   Ano: {ano}, Semestre: {semestre}")
        elif ano is not None:
            print(f"   Ano: {ano}")
        elif semestre is not None:
            print(f"   Semestre: {semestre}")
        else:
            print(f"   Nenhum filtro (todos os dados)")
        
        print(f"\n📈 DADOS DA API:")
        print(f"   Total retornado: {len(matriculas)} matrículas")
        
        print(f"\n🗃️  OPERAÇÕES NO BANCO:")
        print(f"   Inseridas com sucesso: {total_processadas}")
        
        print(f"\n📊 SITUAÇÃO DO BANCO:")
        print(f"   Antes da sincronização: {resumo_inicial.get('total_matriculas', 0)} matrículas")
        print(f"   Após a sincronização: {resumo_final.get('total_matriculas', 0)} matrículas")
        
        print(f"\n⏱️  PERFORMANCE:")
        print(f"   Tempo total: {tempo_total:.2f} segundos")
        
        print("\n" + "=" * 70)
        
        if total_processadas > 0:
            print("✅ SINCRONIZAÇÃO CONCLUÍDA COM SUCESSO!")
        else:
            print("⚠️  NENHUMA MATRÍCULA INSERIDA")
        
        print("=" * 70)
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO NA SINCRONIZAÇÃO: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Função principal com interface para escolha de filtros"""
    print("🚀 Sincronização de Matrículas - LY_MATRICULA")
    print("=" * 50)
    
    try:
        # Verificar configurações
        if not all([config.LYCEUM_BASE_URL, config.LYCEUM_USERNAME, config.LYCEUM_PASSWORD]):
            print("❌ Configurações da API incompletas")
            return False
        
        # Perguntar se deseja aplicar filtros
        print("\n📋 OPÇÕES DE FILTRO:")
        print("   1. Sincronizar TODAS as matrículas (sem filtro)")
        print("   2. Filtrar por ANO específico")
        print("   3. Filtrar por ANO e SEMESTRE")
        print("   4. Filtrar por SEMESTRE (todos os anos)")
        
        opcao = input("\n👉 Escolha uma opção (1-4): ").strip()
        
        ano = None
        semestre = None
        
        if opcao == "1":
            print("\n📥 Sincronizando TODAS as matrículas...")
        elif opcao == "2":
            try:
                ano = int(input("📅 Digite o ano (ex: 2024): ").strip())
                print(f"\n📥 Sincronizando matrículas do ano {ano}...")
            except ValueError:
                print("❌ Ano inválido!")
                return False
        elif opcao == "3":
            try:
                ano = int(input("📅 Digite o ano (ex: 2024): ").strip())
                semestre = int(input("📚 Digite o semestre (1 ou 2): ").strip())
                if semestre not in [1, 2]:
                    print("❌ Semestre deve ser 1 ou 2!")
                    return False
                print(f"\n📥 Sincronizando matrículas do ano {ano}, semestre {semestre}...")
            except ValueError:
                print("❌ Valor inválido!")
                return False
        elif opcao == "4":
            try:
                semestre = int(input("📚 Digite o semestre (1 ou 2): ").strip())
                if semestre not in [1, 2]:
                    print("❌ Semestre deve ser 1 ou 2!")
                    return False
                print(f"\n📥 Sincronizando matrículas do semestre {semestre} (todos os anos)...")
            except ValueError:
                print("❌ Semestre inválido!")
                return False
        else:
            print("❌ Opção inválida!")
            return False
        
        # Executar sincronização
        sucesso = sincronizar_matriculas(ano=ano, semestre=semestre)
        
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