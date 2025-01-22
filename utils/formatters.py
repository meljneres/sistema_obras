import pandas as pd
import locale
from datetime import datetime

# Configurar locale para formatação em português brasileiro
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'Portuguese_Brazil.1252')
    except:
        locale.setlocale(locale.LC_ALL, '')

def format_currency_br(value):
    """Formata valor para o padrão brasileiro de moeda"""
    if pd.isna(value) or value == 0:
        return "R$ 0,00"
    return f"R$ {value:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.')

def format_percentage(value):
    """Formata percentual com 2 casas decimais"""
    if pd.isna(value):
        return "0,00%"
    return f"{value:.2f}%".replace('.', ',')

def format_date_br(date):
    """Formata data no padrão brasileiro"""
    if isinstance(date, str):
        date = datetime.strptime(date, '%Y-%m-%d')
    return date.strftime('%d/%m/%Y')

def format_millions_br(value):
    """Formata valor em milhões no padrão brasileiro"""
    if pd.isna(value) or value == 0:
        return "R$ 0,00"
    value_millions = value / 1000000
    return f"R$ {value_millions:,.2f}M".replace(',', '_').replace('.', ',').replace('_', '.')

def deformat_currency_br(value_str):
    """Converte string de moeda BR para float"""
    try:
        return float(value_str.replace('R$ ', '').replace('.', '').replace(',', '.'))
    except:
        return 0.0
