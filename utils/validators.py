import re
from datetime import datetime

def validar_valor_monetario(valor):
    """Valida se o valor está no formato correto"""
    if valor <= 0:
        return False, "O valor deve ser maior que zero"
    return True, ""

def validar_data(data):
    """Valida se a data está no formato correto e não é futura"""
    try:
        if isinstance(data, str):
            data = datetime.strptime(data, '%Y-%m-%d')
        if data > datetime.now():
            return False, "A data não pode ser futura"
        return True, ""
    except:
        return False, "Data inválida"

def validar_percentual(valor):
    """Valida se o percentual está entre 0 e 100"""
    if not 0 <= valor <= 100:
        return False, "O percentual deve estar entre 0 e 100"
    return True, ""

def validar_contrato(numero):
    """Valida formato do número do contrato"""
    padrao = r'^\d{4}/\d{4}$'
    if not re.match(padrao, numero):
        return False, "Formato inválido. Use: XXXX/XXXX"
    return True, ""
