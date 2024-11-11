import streamlit as st
import pandas as pd
from datetime import datetime
from database.db_utils import get_db_connection
from utils.formatters import format_currency_br, format_percentage


# modules/cadastro.py

def cadastrar_obra():
    st.header("Cadastro de Nova Obra")

    # Dados básicos
    col1, col2 = st.columns(2)
    with col1:
        nome = st.text_input("Nome da Obra")
        contrato = st.text_input("Número do Contrato")
        ordem_servico = st.text_input("Número da OS")
        contratante = st.text_input("Contratante")

    with col2:
        contratada = st.text_input("Contratada")
        data_inicio = st.date_input("Data de Início")
        data_fim = st.date_input("Data de Término")
        duracao_prevista = st.number_input("Duração Prevista (meses)", min_value=1, value=12)

    # Configuração das medições e descrições
    st.subheader("Planejamento de Medições")
    col1, col2 = st.columns(2)
    with col1:
        num_descricoes = st.number_input("Número de Descrições", min_value=1, value=5)
    with col2:
        num_medicoes = st.number_input("Número de Medições", min_value=1, value=12)

    # Reinicializar DataFrame se necessário
    if 'df_valores' not in st.session_state or st.session_state.df_valores is None:
        st.session_state.df_valores = pd.DataFrame(
            0.0,
            index=range(num_descricoes),
            columns=['Descrição'] + [f'Medição {i + 1}' for i in range(num_medicoes)] + ['Total']
        )

    # Verificar se o número de linhas/colunas mudou
    current_rows = len(st.session_state.df_valores.index)
    current_cols = len(st.session_state.df_valores.columns)
    expected_cols = num_medicoes + 2  # +2 para 'Descrição' e 'Total'

    if current_rows != num_descricoes or current_cols != expected_cols:
        st.session_state.df_valores = pd.DataFrame(
            0.0,
            index=range(num_descricoes),
            columns=['Descrição'] + [f'Medição {i + 1}' for i in range(num_medicoes)] + ['Total']
        )

    st.write("### Valores Previstos por Descrição e Medição")

    # Input de valores por descrição
    for i in range(num_descricoes):
        st.write(f"#### Descrição {i + 1}")
        desc = st.text_input(f"Nome da Descrição", key=f"desc_{i}")
        st.session_state.df_valores.at[i, 'Descrição'] = desc

        cols = st.columns(4)
        for j in range(num_medicoes):
            col_idx = j % 4
            with cols[col_idx]:
                valor_str = st.text_input(
                    f"Medição {j + 1}",
                    value="0,00",
                    key=f"med_{i}_{j}"
                )
                try:
                    valor = float(valor_str.replace('.', '').replace(',', '.'))
                except ValueError:
                    valor = 0.0
                st.session_state.df_valores.iloc[i, j + 1] = valor

        # Calcular total da descrição
        total_descricao = st.session_state.df_valores.iloc[i, 1:-1].sum()
        st.session_state.df_valores.iloc[i, -1] = total_descricao
        st.write(f"Total desta descrição: {format_currency_br(total_descricao)}")

    # Mostrar resumo
    st.subheader("Resumo dos Valores")

    # Tabela com todas as descrições e medições
    df_display = st.session_state.df_valores.copy()
    for col in df_display.columns:
        if col != 'Descrição':
            df_display[col] = df_display[col].apply(format_currency_br)
    st.dataframe(df_display)

    # Mostrar valor total da obra
    valor_total = st.session_state.df_valores['Total'].sum()
    st.write(f"### Valor Total da Obra: {format_currency_br(valor_total)}")

    if st.button("Salvar Obra"):
        if not nome or st.session_state.df_valores['Descrição'].isna().all():
            st.error("Preencha o nome da obra e pelo menos uma descrição")
            return

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # Inserir obra
            cursor.execute('''
            INSERT INTO obras (
                nome, contrato, ordem_servico, contratante, contratada,
                valor_total, data_inicio, data_fim, duracao_prevista, num_medicoes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                nome, contrato, ordem_servico, contratante, contratada,
                valor_total, data_inicio, data_fim, duracao_prevista, num_medicoes
            ))

            obra_id = cursor.lastrowid

            # Inserir itens/descrições
            for i in range(num_descricoes):
                desc = st.session_state.df_valores.iloc[i]['Descrição']
                if pd.isna(desc):
                    continue

                valor_total_item = st.session_state.df_valores.iloc[i, -1]

                cursor.execute('''
                INSERT INTO itens_obra (obra_id, descricao, valor_previsto)
                VALUES (?, ?, ?)
                ''', (obra_id, desc, valor_total_item))

                item_id = cursor.lastrowid

                # Inserir medições previstas para cada item
                for j in range(num_medicoes):
                    valor_previsto = st.session_state.df_valores.iloc[i, j + 1]
                    percentual = (valor_previsto / valor_total * 100) if valor_total > 0 else 0

                    cursor.execute('''
                    INSERT INTO medicoes (
                        obra_id, item_id, numero_medicao, valor_previsto, 
                        percentual_previsto, percentual_realizado
                    ) VALUES (?, ?, ?, ?, ?, 0)
                    ''', (obra_id, item_id, j + 1, valor_previsto, percentual))

            conn.commit()
            st.success("Obra cadastrada com sucesso!")

            # Reinicializar DataFrame para nova obra
            st.session_state.df_valores = pd.DataFrame(
                0.0,
                index=range(num_descricoes),
                columns=['Descrição'] + [f'Medição {i + 1}' for i in range(num_medicoes)] + ['Total']
            )

        except Exception as e:
            st.error(f"Erro ao cadastrar obra: {str(e)}")
        finally:
            conn.close()