"""
Funções de transformação de dados
"""

import re
import unicodedata

def extrair_usuario_email(email):
    """
    Extrai a parte do email antes do '@' e converte para minúsculas
    Exemplo: LUIGI.ANDRIGHI@FOA.ORG.BR -> luigi.andrighi
    """
    if not email:
        return None
    
    email_str = str(email).strip()
    
    # Encontrar a posição do '@'
    pos_arroba = email_str.find('@')
    
    if pos_arroba > 0:
        # Extrair parte antes do '@' e converter para minúsculas
        usuario = email_str[:pos_arroba].lower()
        return usuario
    else:
        # Se não encontrar '@', retorna o email em minúsculas
        return email_str.lower()

def converter_minusculas(texto):
    """Converte texto para minúsculas"""
    if texto:
        return str(texto).lower()
    return texto

def converter_inteiro(valor):
    """Converte valor para inteiro"""
    if valor is None:
        return None
    
    try:
        return int(float(valor))
    except (ValueError, TypeError):
        return None

def valor_fixo_4000000001(texto):
    """Retorna valor fixo '4000000001'"""
    return '4000000001'

def valor_fixo_2026_2(texto):
    """Retorna valor fixo '2026.2'"""
    return '2026.2'

def valor_fixo_vazio(texto):
    """Retorna string vazia"""
    return ''

def formatar_cpf(cpf):
    """Formata CPF para o padrão 000.000.000-00"""
    if not cpf:
        return None
    
    cpf_str = str(cpf).replace('.', '').replace('-', '').strip()
    
    if len(cpf_str) == 11 and cpf_str.isdigit():
        return f"{cpf_str[:3]}.{cpf_str[3:6]}.{cpf_str[6:9]}-{cpf_str[9:]}"
    
    return cpf_str

def truncar_texto(texto, limite=None):
    """Trunca texto para o limite especificado"""
    if limite is None:
        limite = 100
    
    if texto and len(str(texto)) > limite:
        return str(texto)[:limite]
    return texto

def remover_acentos(texto):
    """Remove acentos do texto"""
    if not texto:
        return texto
    
    texto = unicodedata.normalize('NFD', str(texto))
    texto = texto.encode('ascii', 'ignore').decode('utf-8')
    return texto

def gerar_codigo_disciplina_curso(codigo_disciplina, nome_curso, curso_id):
    """
    Gera código da disciplina formatado: código-disciplina + '-' + iniciais do curso
    
    Args:
        codigo_disciplina (str): Código original da disciplina
        nome_curso (str): Nome do curso
        curso_id (str): ID do curso (para verificar se é medicina)
    
    Returns:
        str: Código formatado da disciplina
    """
    # Se for curso de medicina (IDs 093 ou 118), retorna apenas o código da disciplina
    if curso_id in ['093', '118']:
        return str(codigo_disciplina)[:30]
    
    # Extrair as três primeiras letras de cada palavra do nome do curso
    palavras = str(nome_curso).strip().split()
    iniciais = []
    
    for palavra in palavras:
        # Remover caracteres especiais e pegar as 3 primeiras letras
        palavra_limpa = re.sub(r'[^a-zA-ZÀ-ÿ]', '', palavra)
        if len(palavra_limpa) >= 3:
            iniciais.append(palavra_limpa[:3].upper())
        elif len(palavra_limpa) > 0:
            iniciais.append(palavra_limpa.upper())
    
    # Juntar as iniciais
    iniciais_str = ''.join(iniciais)
    
    # Montar código final: código-disciplina + '-' + iniciais
    if iniciais_str:
        codigo_final = f"{codigo_disciplina}-{iniciais_str}"
    else:
        codigo_final = str(codigo_disciplina)
    
    # Limitar a 30 caracteres
    return codigo_final[:30]

def extrair_iniciais_curso(nome_curso, limite=30):
    """
    Extrai as três primeiras letras de cada palavra do nome do curso
    
    Args:
        nome_curso (str): Nome do curso
        limite (int): Limite máximo de caracteres para as iniciais
    
    Returns:
        str: Iniciais concatenadas
    """
    if not nome_curso:
        return ""
    
    palavras = str(nome_curso).strip().split()
    iniciais = []
    
    for palavra in palavras:
        # Remover caracteres não alfabéticos e pegar as 3 primeiras letras
        palavra_limpa = re.sub(r'[^a-zA-ZÀ-ÿ]', '', palavra)
        if len(palavra_limpa) >= 3:
            iniciais.append(palavra_limpa[:3].upper())
        elif len(palavra_limpa) > 0:
            iniciais.append(palavra_limpa.upper())
    
    # Juntar as iniciais
    iniciais_str = ''.join(iniciais)
    
    # Limitar ao tamanho máximo
    return iniciais_str[:limite]

def gerar_codigo_oferta(disciplina, turma, ano, semestre):
    """
    Gera código da oferta: disciplina + '_' + turma + '_' + ano + semestre
    """
    if not all([disciplina, turma, ano, semestre]):
        return None
    
    codigo = f"{disciplina}_{turma}_{ano}{semestre}"
    return codigo[:30]

def gerar_codigo_disciplina_oferta(disciplina, nome_curso, curso_id):
    """
    Função auxiliar para gerar código da disciplina para ofertas
    (Usa a mesma lógica de gerar_codigo_disciplina_curso)
    """
    return gerar_codigo_disciplina_curso(disciplina, nome_curso, curso_id)

def gerar_codigo_tipo_oferta(turma):
    """
    Determina o tipo de oferta com base no início do código da turma:
    T0 -> REG, T2 -> REC, T3 -> REP
    """
    if not turma:
        return None
    
    turma_str = str(turma).strip()
    
    if turma_str.startswith('T0'):
        return 'REG'
    elif turma_str.startswith('T2'):
        return 'REC'
    elif turma_str.startswith('T3'):
        return 'REP'
    else:
        return None

def gerar_codigo_oferta_origem(disciplina, turma, ano, semestre, turmas_regulares):
    """
    Gera código da oferta de origem para turmas REC ou REP
    """
    if not turma or not turma.startswith(('T2', 'T3')):
        return ''
    
    # Buscar turma regular correspondente
    turma_regular = None
    for reg_turma in turmas_regulares.get((disciplina, ano, semestre), []):
        if reg_turma.startswith('T0'):
            turma_regular = reg_turma
            break
    
    if turma_regular:
        return gerar_codigo_oferta(disciplina, turma_regular, ano, semestre)
    
    return ''

def mapear_turno(turno):
    """
    Mapeia o turno para os valores possíveis: M, T, N, I, O
    """
    if not turno:
        return None
    
    turno_str = str(turno).strip().upper()
    
    # Mapeamento básico (pode ser ajustado conforme necessidade)
    if turno_str in ['M', 'MANHÃ', 'MANHA', 'MANH']:
        return 'M'
    elif turno_str in ['T', 'TARDE', 'TARD']:
        return 'T'
    elif turno_str in ['N', 'NOITE', 'NOIT']:
        return 'N'
    elif turno_str in ['I', 'INTEGRAL', 'INT']:
        return 'I'
    else:
        return 'O'