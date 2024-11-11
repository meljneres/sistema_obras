# modules/editar.py
import streamlit as st
import pandas as pd
from database.db_utils import get_db_connection
from utils.formatters import format_currency_br


def editar_previsoes():
    st.header("Editar Previsões de Obra")
    st.write("""
    Nesta página você pode editar as previsões de uma obra já cadastrada.
    1. Selecione a obra que deseja editar
    2. Ajuste os valores previstos para cada item e medição
    3. Salve as alterações
    """)

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
    obra_selecionada = st.selectbox(
        "Selecione a Obra",
        list(obras_dict.values()),
        help="Escolha a obra que deseja editar"
    )
    obra_id = [k for k, v in obras_dict.items() if v == obra_selecionada][0]

    # Buscar dados da obra
    cursor.execute('''
    SELECT num_medicoes FROM obras WHERE id = ?
    ''', (obra_id,))
    num_medicoes = cursor.fetchone()[0]

    # Buscar itens e valores previstos
    cursor.execute('''
    SELECT 
        i.id,
        i.descricao,
        i.valor_previsto,
        m.numero_medicao,
        m.valor_previsto
    FROM itens_obra i
    LEFT JOIN medicoes m ON i.id = m.item_id
    WHERE i.obra_id = ?
    ORDER BY i.id, m.numero_medicao
    ''', (obra_id,))

    dados = cursor.fetchall()

    if dados:
        # Organizar dados em DataFrame
        itens = {}
        for item_id, desc, valor_total, num_med, valor_prev in dados:
            if item_id not in itens:
                itens[item_id] = {
                    'Descrição': desc,
                    'Valor Total': valor_total,
                    'Medições': {}
                }
            if num_med:
                itens[item_id]['Medições'][num_med] = valor_prev

        # Interface para edição
        st.subheader("Editar Valores Previstos")

        for item_id, item_data in itens.items():
            st.write(f"### {item_data['Descrição']}")
            st.write(f"Valor total atual: {format_currency_br(item_data['Valor Total'])}")

            cols = st.columns(4)
            valores_novos = []

            for i in range(num_medicoes):
                col_idx = i % 4
                with cols[col_idx]:
                    valor_atual = item_data['Medições'].get(i + 1, 0)
                    valor_str = st.text_input(
                        f"Medição {i + 1}",
                        value=format_currency_br(valor_atual).replace('R$ ', ''),
                        key=f"edit_{item_id}_{i}"
                    )
                    try:
                        valor = float(valor_str.replace('.', '').replace(',', '.'))
                    except ValueError:
                        valor = 0.0
                    valores_novos.append(valor)

            novo_total = sum(valores_novos)
            st.write(f"Novo valor total: {format_currency_br(novo_total)}")

            # Botão para salvar alterações deste item
            if st.button(f"Salvar Alterações - {item_data['Descrição']}", key=f"save_{item_id}"):
                try:
                    # Atualizar valor total do item
                    cursor.execute('''
                    UPDATE itens_obra 
                    SET valor_previsto = ?
                    WHERE id = ?
                    ''', (novo_total, item_id))

                    # Atualizar valores previstos das medições
                    for i, valor in enumerate(valores_novos, 1):
                        cursor.execute('''
                        UPDATE medicoes 
                        SET valor_previsto = ?,
                            percentual_previsto = ?
                        WHERE item_id = ? AND numero_medicao = ?
                        ''', (valor, (valor / novo_total * 100), item_id, i))

                    conn.commit()
                    st.success(f"Alterações salvas com sucesso para {item_data['Descrição']}")

                except Exception as e:
                    st.error(f"Erro ao salvar alterações: {str(e)}")

    conn.close()