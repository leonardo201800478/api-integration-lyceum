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

def formatar_cpf(cpf):
    """Formata CPF para o padrão 000.000.000-00"""
    if not cpf:
        return None
    
    cpf_str = str(cpf).replace('.', '').replace('-', '').strip()
    
    if len(cpf_str) == 11 and cpf_str.isdigit():
        return f"{cpf_str[:3]}.{cpf_str[3:6]}.{cpf_str[6:9]}-{cpf_str[9:]}"
    
    return cpf_str

def truncar_texto(texto, limite):
    """Trunca texto para o limite especificado"""
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