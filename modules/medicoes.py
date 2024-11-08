import streamlit as st
import pandas as pd
from datetime import datetime
from database.db_utils import get_db_connection
from utils.formatters import format_currency_br, format_percentage


def registrar_medicao():
    st.header("Registro de Medição")

    conn = get_db_connection()
    cursor = conn.cursor()

    # Buscar obras
    cursor.execute('SELECT id, nome FROM obras')
    obras = cursor.fetchall()

    if not obras:
        st.warning("Nenhuma obra cadastrada")
        conn.close()
        return

    # Seleção da obra
    obras_dict = {obra[0]: obra[1] for obra in obras}
    obra_selecionada = st.selectbox("Selecione a Obra", list(obras_dict.values()))
    obra_id = [k for k, v in obras_dict.items() if v == obra_selecionada][0]

    # Buscar número total de medições e valor total da obra
    cursor.execute('SELECT num_medicoes, valor_total FROM obras WHERE id = ?', (obra_id,))
    num_medicoes, valor_total = cursor.fetchone()

    # Permitir selecionar qualquer medição
    medicoes_disponiveis = list(range(1, num_medicoes + 1))
    numero_medicao = st.selectbox("Selecione o número da medição", medicoes_disponiveis)

    # Buscar dados da medição
    cursor.execute('''
    SELECT id, valor_previsto, valor_realizado, percentual_previsto
    FROM medicoes
    WHERE obra_id = ? AND numero_medicao = ?
    ''', (obra_id, numero_medicao))

    medicao = cursor.fetchone()

    if medicao:
        medicao_id, valor_previsto, valor_realizado, percentual_previsto = medicao

        st.subheader(f"Medição #{numero_medicao}")

        # Mostrar valor previsto
        st.write(f"Valor previsto para esta medição: {format_currency_br(valor_previsto)}")
        st.write(f"Percentual previsto: {format_percentage(percentual_previsto)}")

        # Input do valor realizado
        valor_str = st.text_input(
            "Valor da medição",
            value=format_currency_br(valor_realizado or 0).replace('R$ ', ''),
            key=f"med_{medicao_id}"
        )

        try:
            valor_realizado = float(valor_str.replace('.', '').replace(',', '.'))
        except ValueError:
            valor_realizado = 0.0

        # Calcular percentual realizado
        percentual_realizado = (valor_realizado / valor_total * 100) if valor_total > 0 else 0

        # Mostrar resumo
        st.subheader("Resumo da Medição")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Valor Previsto", format_currency_br(valor_previsto))
        with col2:
            st.metric("Valor da Medição", format_currency_br(valor_realizado))
        with col3:
            desvio = valor_realizado - valor_previsto
            st.metric("Desvio", format_currency_br(desvio))

        # Mostrar percentuais
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("% Previsto", format_percentage(percentual_previsto))
        with col2:
            st.metric("% Realizado", format_percentage(percentual_realizado))
        with col3:
            desvio_perc = percentual_realizado - percentual_previsto
            st.metric("Desvio %", format_percentage(desvio_perc))

        if st.button("Salvar Medição"):
            try:
                cursor.execute('''
                UPDATE medicoes 
                SET valor_realizado = ?,
                    percentual_realizado = ?,
                    data_medicao = ?
                WHERE id = ?
                ''', (valor_realizado, percentual_realizado, datetime.now().date(), medicao_id))

                conn.commit()
                st.success(f"Medição #{numero_medicao} salva com sucesso!")

            except Exception as e:
                st.error(f"Erro ao salvar medição: {str(e)}")

    conn.close()