#!/usr/bin/env python3
"""
Sincronização da tabela LY_GRADE
SEM chave primária fixa - similar a LY_TURMA e LY_CURRICULO
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
from core.api_client import get_grade_client
from models.ly_grade import LyGradeModel

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def sincronizar_grades():
    """Executa a sincronização completa da tabela LY_GRADE"""
    print("=" * 60)
    print("SINCRONIZAÇÃO DA TABELA LY_GRADE")
    print(f"Início: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        # 1. Criar/verificar tabela
        print("\n[1/4] 📋 Criando/verificando tabela LY_GRADE...")
        LyGradeModel.create_table()
        
        # Resumo inicial
        resumo_inicial = LyGradeModel.get_summary()
        print(f"   Total inicial: {resumo_inicial.get('total_grades', 0)} grades")
        print(f"   Currículos distintos: {resumo_inicial.get('curriculos_distintos', 0)}")
        print(f"   Cursos distintos: {resumo_inicial.get('cursos_distintos', 0)}")
        
        # 2. Buscar dados da API
        print("\n[2/4] 🔗 Conectando e buscando dados da API...")
        print(f"   URL: {config.LYCEUM_BASE_URL}")
        print(f"   Endpoint: /v2/tabela/grades")
        print(f"   Paginação: page={config.API_PAGE_START}, size={config.API_PAGE_SIZE}")
        
        client = get_grade_client()
        grades = client.get_grades()
        
        if not grades:
            print("   ⚠️  Nenhum dado retornado pela API")
            return True
        
        print(f"   ✅ Total retornado pela API: {len(grades)} grades")
        
        # Filtrar registros válidos
        grades_validas = []
        grades_invalidas = 0
        
        for g in grades:
            # Campos obrigatórios: curriculo, curso, disciplina
            if all([g.get('curriculo'), g.get('curso'), g.get('disciplina')]):
                grades_validas.append(g)
            else:
                grades_invalidas += 1
        
        if grades_invalidas > 0:
            print(f"   ⚠️  Grades inválidas (sem campos obrigatórios): {grades_invalidas}")
        
        print(f"   📊 Grades válidas para processamento: {len(grades_validas)}")
        
        if len(grades_validas) == 0:
            print("   ⚠️  Nenhuma grade válida encontrada")
            return True
        
        # Mostrar amostra e estatísticas
        if grades_validas:
            primeiro = grades_validas[0]
            print(f"   📋 Amostra da primeira grade:")
            print(f"      Currículo: {primeiro.get('curriculo')}")
            print(f"      Curso: {primeiro.get('curso')}")
            print(f"      Disciplina: {primeiro.get('disciplina')}")
            print(f"      Série ideal: {primeiro.get('serie_ideal', 'N/A')}")
            print(f"      Obrigatória: {primeiro.get('obrigatoria', 'N/A')}")
            print(f"      Turno: {primeiro.get('turno', 'N/A')}")
            
            # Estatísticas básicas
            obrigatorias = sum(1 for g in grades_validas if g.get('obrigatoria') == 'S')
            optativas = len(grades_validas) - obrigatorias
            
            print(f"   📈 Estatísticas dos dados:")
            print(f"      Total: {len(grades_validas)}")
            print(f"      Obrigatórias: {obrigatorias}")
            print(f"      Optativas: {optativas}")
            
            # Contar por currículo
            curriculos = Counter()
            for g in grades_validas:
                curriculo = g.get('curriculo', 'Não informado')
                curriculos[curriculo] += 1
            
            print(f"   📚 Distribuição por currículo (top 5):")
            for curriculo, count in curriculos.most_common(5):
                print(f"      {curriculo}: {count} grades")
            
            # Contar por curso
            cursos = Counter()
            for g in grades_validas:
                curso = g.get('curso', 'Não informado')
                cursos[curso] += 1
            
            print(f"   🎓 Distribuição por curso (top 5):")
            for curso, count in cursos.most_common(5):
                print(f"      {curso}: {count} grades")
            
            # Contar por série ideal
            series = Counter()
            for g in grades_validas:
                serie = g.get('serie_ideal', 'Não informado')
                series[serie] += 1
            
            print(f"   📊 Distribuição por série ideal:")
            for serie, count in sorted(series.items()):
                if serie != 'Não informado':
                    print(f"      Série {serie}: {count} grades")
            
            # Analisar combinações únicas
            combinacoes = set()
            for g in grades_validas:
                chave = f"{g.get('curriculo')}-{g.get('curso')}-{g.get('disciplina')}"
                combinacoes.add(chave)
            
            print(f"   🔍 Análise de combinações únicas:")
            print(f"      Registros totais: {len(grades_validas)}")
            print(f"      Combinações únicas (curriculo-curso-disciplina): {len(combinacoes)}")
            print(f"      Duplicatas: {len(grades_validas) - len(combinacoes)}")
            
            # Mostrar duplicatas mais frequentes (se houver)
            if len(grades_validas) > len(combinacoes):
                combinacoes_counter = Counter()
                for g in grades_validas:
                    chave = f"{g.get('curriculo')}-{g.get('curso')}-{g.get('disciplina')}"
                    combinacoes_counter[chave] += 1
                
                print(f"   🔢 Grades com múltiplas ocorrências (top 5):")
                for chave, count in combinacoes_counter.most_common(5):
                    if count > 1:
                        print(f"      {chave}: {count} ocorrências")
        
        # 3. Limpar tabela existente (sincronização completa)
        print(f"\n[3/4] 🧹 Limpando tabela existente...")
        LyGradeModel.clear_table()
        
        # 4. Inserir no banco
        print(f"\n[4/4] 💾 Inserindo {len(grades_validas)} grades no banco...")
        
        total_processadas = LyGradeModel.batch_insert(grades_validas)
        
        # 5. Resumo final
        tempo_total = time.time() - start_time
        resumo_final = LyGradeModel.get_summary()
        
        print(f"\n[5/5] 📊 Gerando resumo...")
        
        print("\n" + "=" * 60)
        print("RESUMO DA SINCRONIZAÇÃO")
        print("=" * 60)
        
        print(f"\n📈 DADOS DA API:")
        print(f"   Total retornado: {len(grades)} grades")
        print(f"   Válidas para processamento: {len(grades_validas)}")
        if grades_invalidas > 0:
            print(f"   Inválidas (sem campos obrigatórios): {grades_invalidas}")
        
        print(f"\n🗃️  OPERAÇÕES NO BANCO:")
        print(f"   Inseridas com sucesso: {total_processadas}")
        if len(grades_validas) > total_processadas:
            print(f"   Grades com erro: {len(grades_validas) - total_processadas}")
        
        print(f"\n📊 SITUAÇÃO DO BANCO:")
        print(f"   Antes da sincronização: {resumo_inicial.get('total_grades', 0)} grades")
        print(f"   Após a sincronização: {resumo_final.get('total_grades', 0)} grades")
        print(f"   Currículos distintos: {resumo_final.get('curriculos_distintos', 0)}")
        print(f"   Cursos distintos: {resumo_final.get('cursos_distintos', 0)}")
        print(f"   Disciplinas distintas: {resumo_final.get('disciplinas_distintas', 0)}")
        print(f"   Grades obrigatórias: {resumo_final.get('obrigatorias', 0)}")
        print(f"   Grades optativas: {resumo_final.get('optativas', 0)}")
        
        if resumo_final.get('ultima_atualizacao'):
            print(f"   Última atualização: {resumo_final['ultima_atualizacao']}")
        
        print(f"\n⏱️  PERFORMANCE:")
        print(f"   Tempo total: {tempo_total:.2f} segundos")
        
        if len(grades_validas) > 0:
            taxa = len(grades_validas) / tempo_total
            print(f"   Taxa: {taxa:.2f} grades/segundo")
        
        print("\n" + "=" * 60)
        
        if total_processadas == len(grades_validas):
            print("✅ SINCRONIZAÇÃO CONCLUÍDA COM SUCESSO!")
        else:
            print(f"⚠️  SINCRONIZAÇÃO PARCIALMENTE CONCLUÍDA ({total_processadas}/{len(grades_validas)})")
        
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO NA SINCRONIZAÇÃO: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Função principal"""
    print("🚀 Iniciando sincronização de grades...")
    
    try:
        # Verificar configurações
        if not all([config.LYCEUM_BASE_URL, config.LYCEUM_USERNAME, config.LYCEUM_PASSWORD]):
            print("❌ Configurações da API incompletas no arquivo .env")
            print("   Verifique: API_BASE_URL, API_USERNAME, API_PASSWORD")
            return False
        
        # Executar sincronização
        sucesso = sincronizar_grades()
        
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