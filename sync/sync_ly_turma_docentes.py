"""
Módulo de sincronização para a tabela LY_TURMA_DOCENTE.
Implementa paginação via GET para buscar dados da API do Lyceum.
"""
import requests
import logging
import sys
import os
from typing import Dict, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

# Adiciona o diretório raiz ao path para importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from models.ly_turma_docente import LY_TURMA_DOCENTE
    from core.database import SessionLocal, engine
    from core.config import settings
except ImportError as e:
    print(f"Erro de importação: {e}")
    print("Certifique-se de que está executando do diretório raiz do projeto")
    sys.exit(1)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SyncTurmaDocente:
    """
    Classe responsável pela sincronização de turmas de docentes.
    Implementa apenas GET com paginação para buscar todos os registros.
    """
    
    def __init__(self):
        self.base_url = getattr(settings, 'LYCEUM_API_URL', 'https://api.lyceum.com.br')
        self.session = SessionLocal()
        self.total_sync = 0
        
    def fetch_all_turma_docentes(self) -> List[Dict]:
        """
        Busca TODOS os registros de turma_docente usando paginação via GET.
        
        Returns:
            Lista de dicionários com todos os dados das turmas de docentes
        """
        all_turma_docentes = []
        page = 1
        page_size = 100  # Tamanho fixo por página
        
        try:
            while True:
                logger.info(f"Buscando página {page} de turma_docentes (size={page_size})...")
                
                # Parâmetros da requisição GET com paginação
                params = {
                    'page': page,
                    'size': page_size
                }
                
                # Headers da requisição
                headers = {
                    'Accept': 'application/json'
                }
                
                # Adiciona token se existir
                api_token = getattr(settings, 'LYCEUM_API_TOKEN', None)
                if api_token:
                    headers['Authorization'] = f'Bearer {api_token}'
                
                # Faz a requisição GET para a API
                response = requests.get(
                    f"{self.base_url}/v2/tabela/turma-docente",
                    params=params,
                    headers=headers,
                    timeout=30
                )
                
                # Verifica resposta
                if response.status_code != 200:
                    logger.error(f"Erro {response.status_code}: {response.text}")
                    break
                
                # Processa resposta
                data = response.json()
                
                # Verifica estrutura da resposta paginada
                if isinstance(data, dict) and 'items' in data:
                    # Resposta com estrutura paginada
                    page_data = data['items']
                    total_pages = data.get('pages', 1)
                    current_page = data.get('page', page)
                    
                    logger.info(f"Página {current_page}/{total_pages}: {len(page_data)} registros")
                    
                    all_turma_docentes.extend(page_data)
                    
                    # Verifica se chegou na última página
                    if current_page >= total_pages:
                        break
                    
                    page += 1
                    
                elif isinstance(data, list):
                    # Resposta direta como lista (sem paginação explícita)
                    page_data = data
                    logger.info(f"Página {page}: {len(page_data)} registros")
                    
                    all_turma_docentes.extend(page_data)
                    
                    # Se veio menos que o page_size, é a última página
                    if len(page_data) < page_size:
                        break
                    
                    page += 1
                    
                else:
                    logger.error(f"Formato de resposta inesperado: {type(data)}")
                    break
                
                # Limite de segurança
                if page > 100:
                    logger.warning("Limite de 100 páginas atingido")
                    break
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro na requisição HTTP: {e}")
        except Exception as e:
            logger.error(f"Erro inesperado: {e}")
        
        logger.info(f"Busca concluída. Total: {len(all_turma_docentes)} registros")
        return all_turma_docentes
    
    def process_and_save(self, turma_docentes_data: List[Dict]):
        """
        Processa e salva os dados no banco local.
        """
        if not turma_docentes_data:
            logger.warning("Nenhum dado para processar")
            return
        
        processed_count = 0
        error_count = 0
        
        try:
            # Limpa a tabela antes de inserir novos dados
            logger.info("Limpando tabela LY_TURMA_DOCENTE...")
            self.session.query(LY_TURMA_DOCENTE).delete()
            self.session.commit()
            logger.info("Tabela limpa com sucesso")
            
            # Processa cada registro
            objects_to_save = []
            
            for data in turma_docentes_data:
                try:
                    # Converte datas se existirem
                    for date_field in ['dt_inicio', 'dt_fim', 'dt_ultalt']:
                        if data.get(date_field):
                            try:
                                # Remove o 'Z' do final se existir e converte
                                date_str = str(data[date_field])
                                if date_str.endswith('Z'):
                                    date_str = date_str[:-1] + '+00:00'
                                data[date_field] = datetime.fromisoformat(date_str)
                            except (ValueError, AttributeError) as e:
                                logger.debug(f"Erro ao converter data {date_field}: {e}")
                                data[date_field] = None
                    
                    # Cria objeto do modelo
                    turma_docente = LY_TURMA_DOCENTE(**data)
                    objects_to_save.append(turma_docente)
                    processed_count += 1
                    
                except Exception as e:
                    logger.warning(f"Erro ao processar registro {data.get('chave')}: {e}")
                    error_count += 1
                    continue
            
            # Salva em lote
            if objects_to_save:
                logger.info(f"Salvando {len(objects_to_save)} registros...")
                self.session.bulk_save_objects(objects_to_save)
                self.session.commit()
                self.total_sync = len(objects_to_save)
                logger.info(f"Registros salvos: {len(objects_to_save)}")
            
            # Log de resumo
            logger.info(f"""
            ===== RESUMO DA SINCRONIZAÇÃO =====
            Total processado: {processed_count}
            Salvo com sucesso: {self.total_sync}
            Erros no processamento: {error_count}
            ===================================
            """)
            
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Erro no banco de dados: {e}")
        except Exception as e:
            logger.error(f"Erro inesperado: {e}")
    
    def sync_turma_docentes(self):
        """
        Método principal de sincronização.
        """
        logger.info("===== INICIANDO SINCRONIZAÇÃO DE LY_TURMA_DOCENTE =====")
        
        try:
            # 1. Busca todos os dados via GET com paginação
            turma_docentes_data = self.fetch_all_turma_docentes()
            
            # 2. Processa e salva no banco local
            self.process_and_save(turma_docentes_data)
            
            logger.info("===== SINCRONIZAÇÃO CONCLUÍDA =====")
            
        except Exception as e:
            logger.error(f"Falha na sincronização: {e}")
        finally:
            self.session.close()


def main():
    """
    Função principal para execução do script.
    """
    # Cria tabela se não existir
    try:
        LY_TURMA_DOCENTE.__table__.create(bind=engine, checkfirst=True)
        logger.info("Tabela LY_TURMA_DOCENTE verificada/criada com sucesso")
    except Exception as e:
        logger.error(f"Erro ao criar tabela: {e}")
    
    sync = SyncTurmaDocente()
    sync.sync_turma_docentes()


if __name__ == "__main__":
    main()