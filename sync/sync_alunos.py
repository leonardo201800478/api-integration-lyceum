from core.api_client import AlunoAPIClient
from models.aluno import AlunoModel
import time
import logging

logger = logging.getLogger(__name__)


def sync_alunos(modo='completo'):
    """
    Sincroniza alunos da API para o banco
    
    Args:
        modo: 'completo' (padrão) ou 'incremental'
    """
    logger.info("=" * 60)
    logger.info("INICIANDO SINCRONIZACAO DE ALUNOS")
    logger.info(f"Modo: {modo.upper()}")
    logger.info("=" * 60)
    
    print("Criando/verificando tabela LY_ALUNO...")
    AlunoModel.create_table()
    
    print("Buscando alunos na API...")
    api_client = AlunoAPIClient()
    
    start_time = time.time()
    alunos_api = api_client.get_alunos()
    tempo_busca = time.time() - start_time
    
    if alunos_api is None:
        logger.error("Erro ao buscar alunos da API")
        return
    
    logger.info(f"API retornou {len(alunos_api)} alunos")
    logger.info(f"Tempo de busca: {tempo_busca:.2f} segundos")
    
    if len(alunos_api) == 0:
        logger.warning("API retornou lista vazia")
        return
    
    # Conjunto de matrículas atualizadas
    matriculas_atualizadas = set()
    
    # Estatísticas
    stats = {
        'inseridos': 0,
        'atualizados': 0,
        'erros': 0,
        'ignorados': 0
    }
    
    print(f"\nProcessando {len(alunos_api)} alunos...")
    logger.info(f"Processando {len(alunos_api)} alunos...")
    
    batch_size = 100
    for i, aluno_data in enumerate(alunos_api, 1):
        try:
            if not isinstance(aluno_data, dict):
                stats['ignorados'] += 1
                logger.warning(f"Registro {i} nao e dicionario: {type(aluno_data)}")
                continue
            
            matricula = aluno_data.get('aluno')
            if not matricula:
                stats['ignorados'] += 1
                logger.warning(f"Registro {i} sem matricula")
                continue
            
            # Adiciona à lista de matrículas atualizadas
            matriculas_atualizadas.add(str(matricula))
            
            # Verifica se precisa atualizar (modo incremental)
            if modo == 'incremental':
                from core.database import get_db_connection
                with get_db_connection() as conn:
                    cursor = conn.execute(
                        "SELECT stamp_atualizacao FROM LY_ALUNO WHERE aluno = ?",
                        (matricula,)
                    )
                    existe = cursor.fetchone()
                    
                    if existe:
                        # Verifica se houve alteração
                        stamp_local = existe[0]
                        stamp_api = aluno_data.get('stamp_atualizacao')
                        
                        # Se não tem stamp de atualização ou é o mesmo, pode pular
                        if not stamp_api or str(stamp_local) == str(stamp_api):
                            stats['ignorados'] += 1
                            if i % 500 == 0:
                                logger.info(f"Aluno {matricula} nao alterado, ignorando...")
                            continue
            
            # Faz o upsert
            try:
                # Verifica se já existe antes do upsert
                from core.database import get_db_connection
                with get_db_connection() as conn:
                    cursor = conn.execute(
                        "SELECT aluno FROM LY_ALUNO WHERE aluno = ?",
                        (matricula,)
                    )
                    existe_antes = cursor.fetchone() is not None
                
                AlunoModel.upsert(aluno_data)
                
                if existe_antes:
                    stats['atualizados'] += 1
                else:
                    stats['inseridos'] += 1
                    
            except Exception as e:
                stats['erros'] += 1
                logger.error(f"Erro no aluno {matricula}: {str(e)[:100]}")
            
            # Log de progresso
            if i % batch_size == 0:
                progresso = (i / len(alunos_api)) * 100
                logger.info(f"Progresso: {i}/{len(alunos_api)} ({progresso:.1f}%)")
                print(f"  Processados: {i} alunos")
                
        except Exception as e:
            stats['erros'] += 1
            logger.error(f"Erro geral processando aluno {i}: {str(e)}")
    
    # Remoção de obsoletos (apenas no modo completo)
    if modo == 'completo':
        print("\nVerificando alunos obsoletos...")
        logger.info("Verificando alunos obsoletos...")
        AlunoModel.delete_obsoletos(matriculas_atualizadas)
    
    # Estatísticas finais
    tempo_total = time.time() - start_time
    
    logger.info("=" * 60)
    logger.info("ESTATISTICAS DA SINCRONIZACAO")
    logger.info(f"Total na API: {len(alunos_api)}")
    logger.info(f"Matriculas atualizadas: {len(matriculas_atualizadas)}")
    logger.info(f"Novos inseridos: {stats['inseridos']}")
    logger.info(f"Atualizados: {stats['atualizados']}")
    logger.info(f"Erros: {stats['erros']}")
    logger.info(f"Ignorados: {stats['ignorados']}")
    logger.info(f"Tempo total: {tempo_total:.2f} segundos")
    logger.info("=" * 60)
    
    # Verificação final no banco
    try:
        from core.database import get_db_connection
        with get_db_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM LY_ALUNO")
            total_banco = cursor.fetchone()[0]
            
            logger.info(f"Total no banco: {total_banco}")
            
            # Tenta contar os recentes, mas não falha se a coluna não existir
            try:
                cursor = conn.execute("""
                    SELECT COUNT(*) as recentes
                    FROM LY_ALUNO 
                    WHERE data_sincronizacao >= datetime('now', '-1 minute')
                """)
                recentes = cursor.fetchone()[0]
                logger.info(f"Sincronizados recentemente: {recentes}")
            except Exception as e:
                logger.warning(f"Nao foi possivel contar sincronizacoes recentes: {e}")
    
    except Exception as e:
        logger.error(f"Erro ao verificar banco: {e}")
    
    print(f"\nSincronizacao concluida!")
    print(f"   Total no banco: {total_banco}")
    print(f"   Tempo total: {tempo_total:.2f} segundos")
    
    return {
        'total_api': len(alunos_api),
        'matriculas_atualizadas': len(matriculas_atualizadas),
        'inseridos': stats['inseridos'],
        'atualizados': stats['atualizados'],
        'erros': stats['erros'],
        'tempo_total': tempo_total
    }


def sync_incremental():
    """Sincronização incremental (apenas alterações recentes)"""
    return sync_alunos(modo='incremental')


if __name__ == "__main__":
    import sys
    
    # Configura logging básico
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Verifica argumentos de linha de comando
    if len(sys.argv) > 1 and sys.argv[1] == '--incremental':
        sync_incremental()
    else:
        sync_alunos()