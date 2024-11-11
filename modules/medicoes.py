import streamlit as st
import pandas as pd
from datetime import datetime
from database.db_utils import get_db_connection
from utils.formatters import format_currency_br, format_percentage


# modules/medicoes.py

def registrar_medicao():
    st.header("Registro de Medição")

    conn = get_db_connection()
    cursor = conn.cursor()

    # Seleção da obra
    cursor.execute('SELECT id, nome FROM obras')
    obras = cursor.fetchall()

    if not obras:
        st.warning("Nenhuma obra cadastrada")
        conn.close()
        return

    obras_dict = {obra[0]: obra[1] for obra in obras}
    obra_selecionada = st.selectbox("Selecione a Obra", list(obras_dict.values()))
    obra_id = [k for k, v in obras_dict.items() if v == obra_selecionada][0]

    # Selecionar número da medição
    cursor.execute('SELECT num_medicoes FROM obras WHERE id = ?', (obra_id,))
    num_medicoes = cursor.fetchone()[0]
    numero_medicao = st.selectbox("Selecione o número da medição", range(1, num_medicoes + 1))

    # Buscar todos os itens da obra
    cursor.execute('''
    SELECT 
        i.id,
        i.descricao,
        i.valor_previsto as valor_total_previsto,
        m.valor_previsto,
        m.valor_realizado
    FROM itens_obra i
    LEFT JOIN medicoes m ON i.id = m.item_id 
        AND m.numero_medicao = ?
    WHERE i.obra_id = ?
    ''', (numero_medicao, obra_id))

    itens = cursor.fetchall()

    if itens:
        st.subheader(f"Medição #{numero_medicao}")

        # Criar tabs para cada item
        item_tabs = st.tabs([f"Item {i + 1}: {item[1]}" for i, item in enumerate(itens)])

        valores_realizados = {}

        for idx, (item_tab, item) in enumerate(zip(item_tabs, itens)):
            with item_tab:
                item_id, descricao, valor_total, valor_previsto, valor_realizado = item

                st.write(f"### {descricao}")
                st.write(f"Valor total previsto: {format_currency_br(valor_total)}")
                st.write(f"Valor previsto para esta medição: {format_currency_br(valor_previsto)}")

                valor_str = st.text_input(
                    "Valor da medição",
                    value=format_currency_br(valor_realizado or 0).replace('R$ ', ''),
                    key=f"med_{item_id}"
                )

                try:
                    valor = float(valor_str.replace('.', '').replace(',', '.'))
                except ValueError:
                    valor = 0.0

                valores_realizados[item_id] = valor

        # Mostrar resumo
        st.subheader("Resumo da Medição")

        df_resumo = pd.DataFrame({
            'Item': [item[1] for item in itens],
            'Valor Previsto': [item[3] for item in itens],
            'Valor da Medição': [valores_realizados[item[0]] for item in itens]
        })

        df_resumo['Desvio'] = df_resumo['Valor da Medição'] - df_resumo['Valor Previsto']

        # Formatar valores
        df_display = df_resumo.copy()
        for col in ['Valor Previsto', 'Valor da Medição', 'Desvio']:
            df_display[col] = df_display[col].apply(format_currency_br)

        st.dataframe(df_display)

        # Mostrar totais
        total_previsto = df_resumo['Valor Previsto'].sum()
        total_realizado = df_resumo['Valor da Medição'].sum()
        total_desvio = total_realizado - total_previsto

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Previsto", format_currency_br(total_previsto))
        with col2:
            st.metric("Total Realizado", format_currency_br(total_realizado))
        with col3:
            st.metric("Desvio Total", format_currency_br(total_desvio))

        if st.button("Salvar Medição"):
            try:
                for item_id, valor_realizado in valores_realizados.items():
                    cursor.execute('''
                    INSERT OR REPLACE INTO medicoes (
                        obra_id, item_id, numero_medicao, valor_realizado, data_medicao
                    ) VALUES (?, ?, ?, ?, ?)
                    ''', (obra_id, item_id, numero_medicao, valor_realizado, datetime.now().date()))

                conn.commit()
                st.success(f"Medição #{numero_medicao} salva com sucesso!")

            except Exception as e:
                st.error(f"Erro ao salvar medição: {str(e)}")

    conn.close()