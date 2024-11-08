import pandas as pd

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

def format_millions_br(value):
    """Formata valor em milhões no padrão brasileiro"""
    if pd.isna(value) or value == 0:
        return "R$ 0,00"
    value_millions = value / 1000000
    return f"R$ {value_millions:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.')