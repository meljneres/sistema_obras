def calcular_idp(valor_realizado, valor_previsto):
    """
    Calcula o Índice de Desempenho de Prazo (IDP)
    IDP = Valor Realizado / Valor Previsto
    """
    if valor_previsto == 0:
        return 1.0
    return valor_realizado / valor_previsto


def calcular_desvio(realizado_acumulado, previsto_acumulado):
    """
    Calcula o desvio percentual entre realizado e previsto
    Desvio = Realizado - Previsto
    """
    return realizado_acumulado - previsto_acumulado


def calcular_glosa(obra_id, idp, numero_medicao):
    """
    Calcula glosa usando o fator configurado para a obra
    """
    from database.db_utils import get_db_connection

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
    SELECT fator_ponderacao 
    FROM imr_fatores 
    WHERE obra_id = ? AND numero_medicao = ?
    ''', (obra_id, numero_medicao))

    resultado = cursor.fetchone()
    conn.close()

    fp = resultado[0] if resultado else 1.0

    if idp >= 0.95:
        return 0.0
    elif idp >= 0.85:
        return 0.0295 * fp
    elif idp >= 0.71:
        return 0.0445 * fp
    elif idp >= 0.56:
        return 0.0546 * fp
    elif idp >= 0.42:
        return 0.0553 * fp
    else:
        return 0.0560 * fp


def calcular_valor_glosa(valor_medicao, percentual_glosa):
    """
    Calcula o valor da glosa
    """
    return valor_medicao * percentual_glosa
