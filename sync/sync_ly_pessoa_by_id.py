# sync/sync_ly_pessoa_by_id.py
import sys
from core.api_client import get_pessoa_client, get_aluno_client
from core.database import fetch_one
from core.logger import logger
from models.ly_pessoa import LyPessoaModel
from models.ly_aluno import AlunoModel

def pessoa_existe_no_banco(cod_pessoa: int) -> bool:
    """Verifica se a pessoa já existe na tabela LY_PESSOA pela chave 'pessoa'."""
    query = "SELECT 1 FROM LY_PESSOA WHERE pessoa = ?"
    result = fetch_one(query, (cod_pessoa,), db_path='lyceum.db')
    return result is not None

def buscar_e_salvar_pessoa_por_id(cod_pessoa: int, buscar_alunos: bool = True) -> dict | None:
    """
    1. Verifica se a pessoa já existe no banco local.
    2. Se não existir, consulta a API Lyceum (endpoint /v2/tabela/pessoas com pk[pessoa]).
    3. Insere os dados na tabela LY_PESSOA usando LyPessoaModel.upsert().
    4. Opcionalmente, busca os alunos associados (endpoint /pessoas/{codPessoa}/alunos)
       e insere em LY_ALUNO usando AlunoModel.upsert().
    """
    # 1. Verificar existência local
    if pessoa_existe_no_banco(cod_pessoa):
        logger.info(f"Pessoa {cod_pessoa} já existe no banco local.")
        return {"status": "existente", "codPessoa": cod_pessoa}

    logger.info(f"Pessoa {cod_pessoa} não encontrada localmente. Consultando API Lyceum...")

    pessoa_client = get_pessoa_client()
    try:
        # 2. Buscar dados da pessoa pelo ID (usando pk[pessoa])
        dados_pessoa = pessoa_client.get_pessoa_by_id(cod_pessoa)
        if not dados_pessoa:
            logger.error(f"Pessoa {cod_pessoa} não encontrada na API.")
            return None

        logger.info(f"Dados da pessoa {cod_pessoa} obtidos da API. Inserindo no banco...")

        # 3. Inserir/atualizar a pessoa usando o modelo
        if not LyPessoaModel.upsert(dados_pessoa):
            logger.error(f"Falha ao inserir/atualizar pessoa {cod_pessoa}.")
            return None

        logger.info(f"Pessoa {cod_pessoa} inserida/atualizada com sucesso.")

        # 4. (Opcional) Buscar alunos relacionados
        alunos_inseridos = []
        if buscar_alunos:
            aluno_client = get_aluno_client()
            try:
                endpoint_alunos = f"/pessoas/{cod_pessoa}/alunos"
                alunos = aluno_client.get(endpoint_alunos)  # Retorna lista de alunos
                if alunos and isinstance(alunos, list):
                    logger.info(f"Encontrados {len(alunos)} alunos para a pessoa {cod_pessoa}. Inserindo/atualizando...")
                    for aluno_data in alunos:
                        # Mapeamento dos campos da API para os nomes esperados pelo modelo AlunoModel
                        aluno_adaptado = {
                            # Campos obrigatórios e principais
                            'aluno': aluno_data.get('codAluno'),
                            'pessoa': aluno_data.get('codPessoa'),
                            'nome_compl': aluno_data.get('nomeAluno'),
                            'nome_abrev': aluno_data.get('nomeAbrev'),
                            'nome_social': aluno_data.get('nomeSocial'),
                            'curso': aluno_data.get('codCurso'),
                            'turno': aluno_data.get('turno'),
                            'serie': aluno_data.get('serie'),
                            'unidade_fisica': aluno_data.get('unidadeFisica'),
                            'unidade_ensino': aluno_data.get('unidadeEnsino'),
                            'sit_aluno': aluno_data.get('situacaoAluno'),
                            # Campos que podem vir como None (mapeamos mesmo assim)
                            'stamp_atualizacao': aluno_data.get('stampAtualizacao'),
                            'dt_ingresso': aluno_data.get('dtIngresso'),
                            'e_mail_interno': aluno_data.get('eMailInterno'),
                            'num_chamada': aluno_data.get('numChamada'),
                            'anoconcl2g': aluno_data.get('anoconcl2g'),
                            'tipo_ingresso': aluno_data.get('tipoIngresso'),
                            'ano_ingresso': aluno_data.get('anoIngresso'),
                            'sem_ingresso': aluno_data.get('semIngresso'),
                            'creditos': aluno_data.get('creditos'),
                            'obs_aluno_finan': aluno_data.get('obsAlunoFinan'),
                            'representante_turma': aluno_data.get('representanteTurma'),
                            'tipo_aluno': aluno_data.get('tipoAluno'),
                            'faculdade_conveniada': aluno_data.get('faculdadeConveniada'),
                            'instituicao': aluno_data.get('instituicao'),
                            'classif_aluno': aluno_data.get('classifAluno'),
                            'dist_aluno_unidade': aluno_data.get('distAlunoUnidade'),
                            'tipo_escola': aluno_data.get('tipoEscola'),
                            'cidade2g': aluno_data.get('cidade2g'),
                            'pais2g': aluno_data.get('pais2g'),
                            'concurso': aluno_data.get('concurso'),
                            'candidato': aluno_data.get('candidato'),
                            'curriculo': aluno_data.get('curriculo'),
                            'discipoutraserie': aluno_data.get('discipoutraserie'),
                            'ref_aluno_ant': aluno_data.get('refAlunoAnt'),
                            'sit_aprov': aluno_data.get('sitAprov'),
                            'cod_cartao': aluno_data.get('codCartao'),
                            'curso_ant': aluno_data.get('cursoAnt'),
                            'nome_conjuge': aluno_data.get('nomeConjuge'),
                            'obs_tel_res': aluno_data.get('obsTelRes'),
                            'obs_tel_com': aluno_data.get('obsTelCom'),
                            'outra_faculdade': aluno_data.get('outraFaculdade'),
                            'areacnpq': aluno_data.get('areacnpq'),
                            'grupo': aluno_data.get('grupo'),
                            'turma_pref': aluno_data.get('turmaPref') or aluno_data.get('turma'),  # fallback para 'turma'
                            'cred_educativo': aluno_data.get('credEducativo'),
                        }
                        # Remove chaves com valor None se desejar, mas o modelo lida com None
                        if aluno_adaptado['aluno'] is None:
                            logger.warning(f"Registro de aluno sem matrícula (codAluno) para pessoa {cod_pessoa}, ignorado.")
                            continue

                        if AlunoModel.upsert(aluno_adaptado):
                            alunos_inseridos.append(aluno_adaptado['aluno'])
                        else:
                            logger.warning(f"Falha ao upsert do aluno {aluno_adaptado.get('aluno')}")
                    logger.info(f"{len(alunos_inseridos)} alunos processados.")
                else:
                    logger.info(f"Nenhum aluno encontrado para a pessoa {cod_pessoa}.")
            except Exception as e:
                logger.error(f"Erro ao buscar alunos: {e}")
            finally:
                aluno_client.close()

        return {
            "status": "inserido",
            "pessoa": dados_pessoa,
            "alunos": alunos_inseridos
        }

    except Exception as e:
        logger.error(f"Falha ao processar pessoa {cod_pessoa}: {e}")
        return None
    finally:
        pessoa_client.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            codigo = int(sys.argv[1])
            resultado = buscar_e_salvar_pessoa_por_id(codigo, buscar_alunos=True)
            print(resultado)
        except ValueError:
            print("Código da pessoa deve ser um número inteiro.")
    else:
        print("Uso: python -m sync.sync_ly_pessoa_by_id <codPessoa>")