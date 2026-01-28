#!/usr/bin/env python3
"""
Script de sincronização para tabela LY_CURRICULOS
Busca todos os currículos da API /v2/tabela/curriculos
"""
import sys
import pandas as pd
from datetime import datetime
from typing import List, Dict
import requests
from requests.auth import HTTPBasicAuth
import warnings
import time
warnings.filterwarnings('ignore')

# Importações internas
from core.config import config
from models.ly_curriculo import LyCurriculoModel

class LyCurriculoClient:
    """Cliente para API de currículos do Lyceum"""
    
    def __init__(self):
        self.base_url = config.API_BASE_URL
        self.auth = HTTPBasicAuth(config.API_USERNAME, config.API_PASSWORD)
    
    def buscar_todos_curriculos(self):
        """
        Busca TODOS os currículos da API
        Começa da página 0 e busca todas as páginas com size=100
        """
        print("🔍 Buscando TODOS os currículos da API Lyceum (página inicial=0)...")
        
        all_curriculos = []
        page = 0  # PÁGINA INICIAL = 0
        size = 100
        max_pages = 100  # Limite de segurança
        
        while page < max_pages:
            try:
                print(f"  📄 Buscando página {page} (size={size})...")
                
                response = requests.get(
                    f"{self.base_url}/v2/tabela/curriculos",
                    params={
                        "page": page,
                        "size": size
                    },
                    auth=self.auth,
                    timeout=60,
                    verify=False
                )
                
                if response.status_code != 200:
                    print(f"  ❌ Status {response.status_code} na página {page}")
                    print(f"  📄 Resposta: {response.text[:200]}")
                    break
                
                data = response.json()
                
                # Verificar estrutura da resposta
                if not isinstance(data, dict):
                    print(f"  ⚠️  Estrutura inesperada: {type(data)}")
                    break
                
                if 'data' not in data:
                    print(f"  ⚠️  Campo 'data' não encontrado. Campos disponíveis: {list(data.keys())}")
                    
                    # Tentar outras estruturas possíveis
                    if isinstance(data, list):
                        curriculos = data
                        print(f"  ✅ Dados como lista direta: {len(curriculos)} itens")
                    else:
                        # Procurar por listas nos dados
                        for key, value in data.items():
                            if isinstance(value, list):
                                curriculos = value
                                print(f"  ✅ Encontrado em campo '{key}': {len(curriculos)} itens")
                                break
                        else:
                            print("  ❌ Nenhuma lista de dados encontrada")
                            break
                else:
                    curriculos = data['data']
                
                if not curriculos:
                    print(f"  📭 Página {page} vazia - fim dos dados")
                    break
                
                all_curriculos.extend(curriculos)
                print(f"  ✅ Página {page}: {len(curriculos)} currículos (total: {len(all_curriculos)})")
                
                # Mostrar amostra da primeira página
                if page == 0 and curriculos:
                    print(f"  📋 Amostra da primeira página:")
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
                
                # Se veio menos que o solicitado, é a última página
                if len(curriculos) < size:
                    print(f"  📭 Última página (menos de {size} itens)")
                    break
                
                page += 1
                
                # Pequeno delay para não sobrecarregar a API
                time.sleep(0.5)
                    
            except Exception as e:
                print(f"  ❌ Erro na página {page}: {e}")
                import traceback
                traceback.print_exc()
                break
        
        if all_curriculos:
            print(f"\n✅ TOTAL DE CURRÍCULOS ENCONTRADOS: {len(all_curriculos)}")
            
            # Estatísticas
            cursos_unicos = set(str(c.get('curso', '')).strip() for c in all_curriculos)
            cursos_unicos = {c for c in cursos_unicos if c}  # Remover vazios
            
            print(f"📊 Cursos distintos encontrados: {len(cursos_unicos)}")
            
            # Contar currículos por curso
            from collections import Counter
            cursos_counter = Counter(str(c.get('curso', '')).strip() for c in all_curriculos)
            
            # Remover entradas vazias
            if '' in cursos_counter:
                del cursos_counter['']
            
            print("📋 Top 10 cursos com mais currículos:")
            for curso, count in cursos_counter.most_common(10):
                print(f"  Curso {curso}: {count} currículos")
            
            # Contar por situação
            situacoes_counter = Counter(str(c.get('situacao', 'N/A')).strip() for c in all_curriculos)
            print("\n📋 Distribuição por situação:")
            for situacao, count in situacoes_counter.most_common():
                print(f"  {situacao}: {count}")
            
            return all_curriculos
        else:
            print("\n❌ NENHUM CURRÍCULO ENCONTRADO")
            return []

class LyCurriculoSync:
    """Sincronizador da tabela LY_CURRICULOS"""
    
    def __init__(self):
        self.client = LyCurriculoClient()
        
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
        """Busca currículos da API"""
        print(f"\n{'='*50}")
        print("BUSCANDO CURRÍCULOS DA API LYCEUM")
        print(f"{'='*50}")
        
        curriculos = self.client.buscar_todos_curriculos()
        
        if not curriculos:
            print("❌ Nenhum currículo encontrado na API")
            return None
        
        self.total_curriculos = len(curriculos)
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
    
    def exportar_para_csv(self, curriculos: List[Dict]):
        """Exporta dados para CSV"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ly_curriculos_completo_{timestamp}.csv"
        
        df = pd.DataFrame(curriculos)
        
        # Selecionar colunas principais para exportação
        colunas_principais = [
            'curriculo', 'curso', 'turno', 'prazo_ideal', 'prazo_max',
            'ano_ini', 'sem_ini', 'regime', 'aulas_previstas', 'creditos',
            'situacao', 'modalidade', 'servico', 'valor', 'classificacao'
        ]
        
        # Filtrar colunas que existem
        colunas_disponiveis = [col for col in colunas_principais if col in df.columns]
        df = df[colunas_disponiveis]
        
        # Ordenar por curso e currículo
        if 'curso' in df.columns and 'curriculo' in df.columns:
            df = df.sort_values(['curso', 'curriculo'])
        
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"✅ Dados exportados para: {filename}")
        return filename
    
    def mostrar_exemplos(self):
        """Mostra exemplos de currículos importados"""
        print(f"\n{'='*50}")
        print("EXEMPLOS DE CURRÍCULOS IMPORTADOS")
        print(f"{'='*50}")
        
        # Buscar currículos recentes
        curriculos_recentes = LyCurriculoModel.get_curriculos_recentes(limit=5)
        
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
        cursos_com_curriculos = LyCurriculoModel.get_cursos_com_curriculos()
        if cursos_com_curriculos:
            print(f"\n📊 Cursos com currículos disponíveis: {len(cursos_com_curriculos)}")
            print("📋 Primeiros 10 cursos:")
            for i, curso in enumerate(cursos_com_curriculos[:10]):
                print(f"  {i+1}. Curso {curso}")
    
    def atualizar_cursos_com_curriculos(self):
        """Atualiza a tabela de cursos com os períodos dos currículos"""
        print(f"\n{'='*50}")
        print("ATUALIZANDO CURSOS COM PERÍODOS DOS CURRÍCULOS")
        print(f"{'='*50}")
        
        try:
            from models.curso import CursoModel
            
            # Buscar todos os cursos ativos
            cursos_ativos = CursoModel.get_cursos_ativos()
            
            if not cursos_ativos:
                print("⚠️  Nenhum curso ativo encontrado")
                return
            
            cursos_atualizados = 0
            
            for curso in cursos_ativos:
                codigo_curso = curso[0]  # codigoCurso é o primeiro campo
                
                # Buscar maior currículo para este curso
                maior_curriculo = LyCurriculoModel.get_maior_curriculo_por_curso(codigo_curso)
                
                if maior_curriculo and maior_curriculo.get('prazo_ideal') is not None:
                    try:
                        prazo_ideal = maior_curriculo['prazo_ideal']
                        
                        # Converter para inteiro
                        if isinstance(prazo_ideal, (int, float)):
                            quant_periodos = int(float(prazo_ideal))
                        else:
                            quant_periodos = int(prazo_ideal)
                        
                        # Atualizar curso
                        CursoModel.update_quant_periodos(codigo_curso, quant_periodos, config.DB_NAME)
                        cursos_atualizados += 1
                        
                        print(f"✅ Curso {codigo_curso}: prazo_ideal={prazo_ideal} → quantPeriodos={quant_periodos}")
                        
                    except (ValueError, TypeError) as e:
                        print(f"⚠️  Curso {codigo_curso}: erro ao converter prazo_ideal: {e}")
            
            print(f"\n📊 Cursos atualizados com períodos: {cursos_atualizados}/{len(cursos_ativos)}")
            
        except ImportError:
            print("⚠️  Modelo de cursos não disponível para atualização")
        except Exception as e:
            print(f"❌ Erro ao atualizar cursos: {e}")
    
    def run(self):
        """Executa o processo completo de sincronização"""
        print("="*60)
        print("SISTEMA DE SINCRONIZAÇÃO DE CURRÍCULOS - LY_CURRICULOS")
        print("API: /v2/tabela/curriculos (página inicial=0)")
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
            
            # 7. Atualizar cursos com períodos (opcional)
            atualizar = input("\n🔄 Atualizar cursos com períodos dos currículos? (s/n): ").strip().lower()
            if atualizar == 's':
                self.atualizar_cursos_com_curriculos()
            
            # 8. Exportar CSV (opcional)
            if curriculos_processados:
                exportar = input("\n💾 Exportar dados para CSV? (s/n): ").strip().lower()
                if exportar == 's':
                    self.exportar_para_csv(curriculos_processados)
            
            # 9. Mostrar exemplos
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