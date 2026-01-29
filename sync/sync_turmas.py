#!/usr/bin/env python3
"""
Sincronização da tabela LY_TURMA
SEM chave primária fixa - similar a LY_CURRICULO e LY_DISCIPLINA
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
from core.api_client import TurmaAPIClient
from models.ly_turma import LyTurmaModel

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def sincronizar_turmas():
    """Executa a sincronização completa da tabela LY_TURMA"""
    print("=" * 60)
    print("SINCRONIZAÇÃO DA TABELA LY_TURMA")
    print(f"Início: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        # 1. Criar/verificar tabela
        print("\n[1/4] 📋 Criando/verificando tabela LY_TURMA...")
        LyTurmaModel.create_table()
        
        # Resumo inicial
        resumo_inicial = LyTurmaModel.get_summary()
        print(f"   Total inicial: {resumo_inicial.get('total_turmas', 0)} turmas")
        print(f"   Turmas ativas: {resumo_inicial.get('turmas_ativas', 0)}")
        print(f"   Anos distintos: {resumo_inicial.get('anos_distintos', 0)}")
        
        # 2. Buscar dados da API
        print("\n[2/4] 🔗 Conectando e buscando dados da API...")
        print(f"   URL: {config.LYCEUM_BASE_URL}")
        print(f"   Endpoint: /v2/tabela/turmas")
        print(f"   Paginação: page=0, size={config.API_PAGE_SIZE}")
        
        client = TurmaAPIClient()
        turmas = client.get_turmas()
        
        if not turmas:
            print("   ❌ Nenhum dado retornado pela API")
            return False
        
        print(f"   ✅ Total retornado pela API: {len(turmas)} turmas")
        
        # Filtrar registros válidos (com campos obrigatórios)
        turmas_validas = []
        turmas_invalidas = 0
        
        for t in turmas:
            # Campos obrigatórios: ano, semestre, turma, disciplina
            if all([t.get('ano'), t.get('semestre'), t.get('turma'), t.get('disciplina')]):
                turmas_validas.append(t)
            else:
                turmas_invalidas += 1
        
        if turmas_invalidas > 0:
            print(f"   ⚠️  Turmas inválidas (sem campos obrigatórios): {turmas_invalidas}")
        
        print(f"   📊 Turmas válidas para processamento: {len(turmas_validas)}")
        
        if len(turmas_validas) == 0:
            print("   ⚠️  Nenhuma turma válida encontrada")
            return True  # Considera sucesso, mas sem dados
        
        # Mostrar amostra e estatísticas
        if turmas_validas:
            primeiro = turmas_validas[0]
            print(f"   📋 Amostra da primeira turma:")
            print(f"      Ano: {primeiro.get('ano')}")
            print(f"      Semestre: {primeiro.get('semestre')}")
            print(f"      Turma: {primeiro.get('turma')}")
            print(f"      Disciplina: {primeiro.get('disciplina')}")
            print(f"      Curso: {primeiro.get('curso', 'N/A')}")
            print(f"      Situação: {primeiro.get('sit_turma', 'N/A')}")
            print(f"      Vagas: {primeiro.get('vagas_calouros', 'N/A')}/{primeiro.get('vagas_veteranos', 'N/A')}")
            
            # Estatísticas básicas
            ativas = sum(1 for t in turmas_validas if t.get('sit_turma') == 'A')
            inativas = len(turmas_validas) - ativas
            
            print(f"   📈 Estatísticas dos dados:")
            print(f"      Total: {len(turmas_validas)}")
            print(f"      Ativas: {ativas}")
            print(f"      Inativas: {inativas}")
            
            # Contar por ano
            anos = Counter()
            for t in turmas_validas:
                ano = t.get('ano')
                if ano:
                    anos[ano] += 1
            
            print(f"   📅 Distribuição por ano (top 5):")
            for ano, count in sorted(anos.items(), reverse=True)[:5]:
                print(f"      {ano}: {count} turmas")
            
            # Contar por semestre
            semestres = Counter()
            for t in turmas_validas:
                semestre = t.get('semestre')
                if semestre:
                    semestres[semestre] += 1
            
            print(f"   📚 Distribuição por semestre:")
            for semestre, count in sorted(semestres.items()):
                print(f"      {semestre}º semestre: {count} turmas")
            
            # Contar por curso
            cursos = Counter()
            for t in turmas_validas:
                curso = t.get('curso', 'Não informado')
                cursos[curso] += 1
            
            print(f"   🎓 Distribuição por curso (top 5):")
            for curso, count in cursos.most_common(5):
                print(f"      {curso}: {count} turmas")
            
            # Analisar combinações únicas
            combinacoes = set()
            for t in turmas_validas:
                chave = f"{t.get('ano')}-{t.get('semestre')}-{t.get('disciplina')}-{t.get('turma')}"
                combinacoes.add(chave)
            
            print(f"   🔍 Análise de combinações únicas:")
            print(f"      Registros totais: {len(turmas_validas)}")
            print(f"      Combinações únicas (ano-semestre-disciplina-turma): {len(combinacoes)}")
            print(f"      Duplicatas: {len(turmas_validas) - len(combinacoes)}")
            
            # Mostrar duplicatas mais frequentes (se houver)
            if len(turmas_validas) > len(combinacoes):
                combinacoes_counter = Counter()
                for t in turmas_validas:
                    chave = f"{t.get('ano')}-{t.get('semestre')}-{t.get('disciplina')}-{t.get('turma')}"
                    combinacoes_counter[chave] += 1
                
                print(f"   🔢 Turmas com múltiplas ocorrências (top 5):")
                for chave, count in combinacoes_counter.most_common(5):
                    if count > 1:
                        print(f"      {chave}: {count} ocorrências")
        
        # 3. Limpar tabela existente (sincronização completa)
        print(f"\n[3/4] 🧹 Limpando tabela existente...")
        LyTurmaModel.clear_table()
        
        # 4. Inserir no banco
        print(f"\n[4/4] 💾 Inserindo {len(turmas_validas)} turmas no banco...")
        
        total_processadas = LyTurmaModel.batch_insert(turmas_validas)
        
        # 5. Resumo final
        tempo_total = time.time() - start_time
        resumo_final = LyTurmaModel.get_summary()
        
        print(f"\n[5/5] 📊 Gerando resumo...")
        
        print("\n" + "=" * 60)
        print("RESUMO DA SINCRONIZAÇÃO")
        print("=" * 60)
        
        print(f"\n📈 DADOS DA API:")
        print(f"   Total retornado: {len(turmas)} turmas")
        print(f"   Válidas para processamento: {len(turmas_validas)}")
        if turmas_invalidas > 0:
            print(f"   Inválidas (sem campos obrigatórios): {turmas_invalidas}")
        
        print(f"\n🗃️  OPERAÇÕES NO BANCO:")
        print(f"   Inseridas com sucesso: {total_processadas}")
        if len(turmas_validas) > total_processadas:
            print(f"   Turmas com erro: {len(turmas_validas) - total_processadas}")
        
        print(f"\n📊 SITUAÇÃO DO BANCO:")
        print(f"   Antes da sincronização: {resumo_inicial.get('total_turmas', 0)} turmas")
        print(f"   Após a sincronização: {resumo_final.get('total_turmas', 0)} turmas")
        print(f"   Turmas distintas (código): {resumo_final.get('turmas_distintas', 0)}")
        print(f"   Turmas ativas: {resumo_final.get('turmas_ativas', 0)}")
        print(f"   Anos distintos: {resumo_final.get('anos_distintos', 0)}")
        print(f"   Semestres distintos: {resumo_final.get('semestres_distintos', 0)}")
        print(f"   Disciplinas distintas: {resumo_final.get('disciplinas_distintas', 0)}")
        
        if resumo_final.get('ultima_atualizacao'):
            print(f"   Última atualização: {resumo_final['ultima_atualizacao']}")
        
        print(f"\n⏱️  PERFORMANCE:")
        print(f"   Tempo total: {tempo_total:.2f} segundos")
        
        if len(turmas_validas) > 0:
            taxa = len(turmas_validas) / tempo_total
            print(f"   Taxa: {taxa:.2f} turmas/segundo")
        
        print("\n" + "=" * 60)
        
        if total_processadas == len(turmas_validas):
            print("✅ SINCRONIZAÇÃO CONCLUÍDA COM SUCESSO!")
        else:
            print(f"⚠️  SINCRONIZAÇÃO PARCIALMENTE CONCLUÍDA ({total_processadas}/{len(turmas_validas)})")
        
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO NA SINCRONIZAÇÃO: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Função principal"""
    print("🚀 Iniciando sincronização de turmas...")
    
    try:
        # Verificar configurações
        if not all([config.LYCEUM_BASE_URL, config.LYCEUM_USERNAME, config.LYCEUM_PASSWORD]):
            print("❌ Configurações da API incompletas no arquivo .env")
            print("   Verifique: API_BASE_URL, API_USERNAME, API_PASSWORD")
            return False
        
        # Executar sincronização
        sucesso = sincronizar_turmas()
        
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