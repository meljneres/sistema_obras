import streamlit as st
import pandas as pd
from database.db_utils import get_db_connection
from utils.formatters import format_currency_br


def editar_obra():
    st.header("Editar Obra")
    st.write("""
    Nesta página você pode:
    1. Selecionar a obra que deseja editar
    2. Modificar os dados cadastrais
    3. Ajustar os valores dos itens
    4. Salvar as alterações
    """)

    conn = get_db_connection()
    cursor = conn.cursor()

    # Buscar obras do usuário logado
    cursor.execute('''
    SELECT id, nome, contrato 
    FROM obras 
    WHERE user_id = ?
    ORDER BY nome
    ''', (st.session_state.user_id,))

    obras = cursor.fetchall()

    if not obras:
        st.warning("Nenhuma obra cadastrada")
        conn.close()
        return

    # Seleção da obra
    obras_dict = {obra[0]: f"{obra[1]} (Contrato: {obra[2]})" for obra in obras}
    obra_selecionada = st.selectbox("Selecione a Obra", list(obras_dict.values()))
    obra_id = [k for k, v in obras_dict.items() if v == obra_selecionada][0]

    # Buscar dados da obra
    cursor.execute('''
    SELECT nome, contrato, ordem_servico, contratante, contratada, 
           valor_total, num_medicoes, data_inicio, data_fim
    FROM obras 
    WHERE id = ?
    ''', (obra_id,))

    obra = cursor.fetchone()

    with st.form("editar_obra_form"):
        st.subheader("Dados da Obra")

        nome = st.text_input("Nome da Obra", value=obra[0])
        contrato = st.text_input("Número do Contrato", value=obra[1])
        ordem_servico = st.text_input("Ordem de Serviço", value=obra[2])
        contratante = st.text_input("Contratante", value=obra[3])
        contratada = st.text_input("Contratada", value=obra[4])
        valor_total = st.text_input("Valor Total", value=format_currency_br(obra[5]).replace('R$ ', ''))
        num_medicoes = st.number_input("Número de Medições", min_value=1, value=obra[6])
        data_inicio = st.date_input("Data de Início", value=obra[7])
        data_fim = st.date_input("Data de Término", value=obra[8])

        # Buscar e exibir itens da obra
        cursor.execute('SELECT id, descricao, valor_previsto FROM itens_obra WHERE obra_id = ?', (obra_id,))
        itens = cursor.fetchall()

        st.subheader("Itens da Obra")

        valores_itens = {}
        for item in itens:
            item_id, descricao, valor_previsto = item
            valor_str = st.text_input(
                f"Valor do item: {descricao}",
                value=format_currency_br(valor_previsto).replace('R$ ', ''),
                key=f"item_{item_id}"
            )
            try:
                valores_itens[item_id] = float(valor_str.replace('.', '').replace(',', '.'))
            except ValueError:
                valores_itens[item_id] = 0.0

        if st.form_submit_button("Salvar Alterações"):
            try:
                valor_total = float(valor_total.replace('.', '').replace(',', '.'))

                cursor.execute('''
                UPDATE obras 
                SET nome = ?, contrato = ?, ordem_servico = ?, contratante = ?,
                    contratada = ?, valor_total = ?, num_medicoes = ?,
                    data_inicio = ?, data_fim = ?
                WHERE id = ?
                ''', (nome, contrato, ordem_servico, contratante, contratada,
                      valor_total, num_medicoes, data_inicio, data_fim, obra_id))

                for item_id, valor in valores_itens.items():
                    cursor.execute('''
                    UPDATE itens_obra 
                    SET valor_previsto = ?
                    WHERE id = ?
                    ''', (valor, item_id))

                conn.commit()
                st.success("✅ Obra atualizada com sucesso!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao atualizar obra: {str(e)}")
                conn.rollback()

    conn.close()
