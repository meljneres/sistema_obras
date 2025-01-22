import streamlit as st
import pandas as pd
from datetime import datetime
from database.db_utils import get_db_connection
from utils.formatters import format_currency_br, format_percentage
from utils.calculadora import calcular_idp
from utils.calculadora import calcular_glosa, calcular_valor_glosa


def registrar_medicao():
    st.header("Registro de Medição")
    st.write("""
    Nesta página você deve:
    1. Selecionar a obra
    2. Escolher a medição a ser registrada
    3. Informar os valores realizados para cada item
    4. Conferir o resumo e salvar
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
    cursor.execute('SELECT num_medicoes, valor_total FROM obras WHERE id = ?', (obra_id,))
    num_medicoes, valor_total = cursor.fetchone()

    # Seletor de medição com status
    cursor.execute('''
    SELECT DISTINCT numero_medicao, 
           CASE WHEN valor_realizado IS NOT NULL THEN 1 ELSE 0 END as realizada
    FROM medicoes 
    WHERE obra_id = ?
    GROUP BY numero_medicao
    ''', (obra_id,))
    status_medicoes = {m[0]: m[1] for m in cursor.fetchall()}

    numero_medicao = st.selectbox(
        "Selecione a Medição",
        options=range(1, num_medicoes + 1),
        format_func=lambda x: f"Medição {x} {'✅ Salva' if status_medicoes.get(x, 0) else '📝 Não salva'}",
        key="medicao_selector"
    )

    # Buscar itens da obra
    cursor.execute('''
    SELECT 
        i.id,
        i.descricao,
        i.valor_previsto as valor_total_item,
        m.valor_previsto,
        m.valor_realizado
    FROM itens_obra i
    LEFT JOIN medicoes m ON i.id = m.item_id AND m.numero_medicao = ?
    WHERE i.obra_id = ?
    ORDER BY i.id
    ''', (numero_medicao, obra_id))

    itens = cursor.fetchall()

    if itens:
        st.subheader(f"Medição #{numero_medicao}")

        valores_realizados = {}
        for idx, item in enumerate(itens):
            item_id, descricao, valor_total_item, valor_previsto, valor_realizado = item
            with st.expander(f"Item {idx + 1}: {descricao}", expanded=True):
                st.write(f"### {descricao}")
                st.write(f"Valor total do item: {format_currency_br(valor_total_item)}")
                st.write(f"Valor previsto para esta medição: {format_currency_br(valor_previsto)}")

                # Input do valor realizado
                valor_str = st.text_input(
                    "Valor realizado",
                    value=format_currency_br(valor_realizado or 0).replace('R$ ', ''),
                    key=f"med_{numero_medicao}_{item_id}"
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
            'Valor Realizado': [valores_realizados[item[0]] for item in itens]
        })

        # Calcular totais e desvios
        df_resumo['Desvio'] = df_resumo['Valor Realizado'] - df_resumo['Valor Previsto']

        # Formatar valores para exibição
        df_display = df_resumo.copy()
        for col in ['Valor Previsto', 'Valor Realizado', 'Desvio']:
            df_display[col] = df_display[col].apply(format_currency_br)

        st.dataframe(df_display)

        # Mostrar totais
        total_previsto = df_resumo['Valor Previsto'].sum()
        total_realizado = df_resumo['Valor Realizado'].sum()
        total_desvio = total_realizado - total_previsto

        # Calcular IDP
        idp = calcular_idp(total_realizado, total_previsto)

        cursor.execute('''SELECT fator_ponderacao FROM imr_fatores WHERE obra_id = ? AND numero_medicao = ?''',
                       (obra_id, numero_medicao))
        resultado = cursor.fetchone()
        fator_imr = resultado[0] if resultado else 1.0

        # Calcular glosa
        glosa = calcular_glosa(obra_id, idp, numero_medicao)

        # Mostrar informações do IMR
        st.subheader("Instrumento de Medição de Resultado (IMR)")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Fator de Ponderação", f"{fator_imr:.2f}")
        with col2:
            st.metric("IDP", f"{idp:.2f}")
        with col3:
            st.metric("Glosa Calculada", f"{glosa:.2%}")

        # Calcular valor da glosa
        valor_medicao = total_realizado
        valor_glosa = calcular_valor_glosa(valor_medicao, glosa)

        st.write(f"""
        ### Análise do IMR
        - Valor da Medição: {format_currency_br(valor_medicao)}
        - Valor da Glosa: {format_currency_br(valor_glosa)}
        - Valor Final: {format_currency_br(valor_medicao - valor_glosa)}
        """)

        # Mostrar métricas
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Previsto", format_currency_br(total_previsto))
        with col2:
            st.metric("Total Realizado", format_currency_br(total_realizado))
        with col3:
            st.metric("Desvio", format_currency_br(total_desvio))

        col1, col2 = st.columns(2)
        with col1:
            st.metric("IDP", f"{idp:.2f}")
        with col2:
            percentual_realizado = (total_realizado / valor_total * 100)
            st.metric("Percentual Realizado", f"{percentual_realizado:.2f}%")

        # Botões de ação
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Salvar Medição", key="btn_salvar_medicao"):
                try:
                    for item_id, valor_realizado in valores_realizados.items():
                        percentual = (valor_realizado / valor_total * 100) if valor_total > 0 else 0
                        cursor.execute('''
                        UPDATE medicoes 
                        SET valor_realizado = ?,
                            percentual_realizado = ?,
                            data_medicao = ?
                        WHERE obra_id = ? AND item_id = ? AND numero_medicao = ?
                        ''', (
                            valor_realizado,
                            percentual,
                            datetime.now().date(),
                            obra_id,
                            item_id,
                            numero_medicao
                        ))
                    conn.commit()
                    st.success(f"Medição #{numero_medicao} salva com sucesso!")
                except Exception as e:
                    st.error(f"Erro ao salvar medição: {str(e)}")
                    conn.rollback()

        with col2:
            if st.button("Gerar Relatório PDF", key="btn_gerar_pdf"):
                try:
                    from modules.pdf_generator import generate_pdf_report

                    # Buscar dados completos da obra
                    cursor.execute('''
                    SELECT nome, contrato, ordem_servico, contratante, contratada, valor_total
                    FROM obras WHERE id = ?
                    ''', (obra_id,))
                    obra_dados = cursor.fetchone()

                    dados_obra = {
                        'nome': obra_dados[0],
                        'contrato': obra_dados[1],
                        'ordem_servico': obra_dados[2],
                        'contratante': obra_dados[3],
                        'contratada': obra_dados[4],
                        'valor_total': obra_dados[5]
                    }

                    dados_medicao = {
                        'valor_previsto': total_previsto,
                        'valor_realizado': total_realizado,
                        'percentual_previsto': (total_previsto / valor_total * 100),
                        'percentual_realizado': percentual_realizado,
                        'idp': idp,
                        'desvio': total_desvio
                    }

                    graficos = None
                    pdf_file = generate_pdf_report(obra_id, numero_medicao, dados_obra, dados_medicao, graficos)

                    import os
                    current_dir = os.getcwd()
                    st.success(f"Relatório PDF gerado com sucesso em: {os.path.join(current_dir, pdf_file)}")
                except Exception as e:
                    st.error(f"Erro ao gerar PDF: {str(e)}")

    conn.close()
