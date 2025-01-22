import streamlit as st
import pandas as pd
from datetime import datetime
from database.db_utils import get_db_connection
from utils.formatters import format_currency_br
from utils.validators import validar_valor_monetario, validar_data


def cadastrar_obra():
    st.header("Cadastro de Nova Obra")
    st.write("""
    Nesta página você deve:
    1. Preencher os dados básicos da obra
    2. Definir as descrições dos itens
    3. Cadastrar os valores previstos para cada medição
    """)

    # 1. DADOS BÁSICOS
    st.subheader("1. Dados Básicos da Obra")

    col1, col2 = st.columns(2)
    with col1:
        nome = st.text_input("Nome da Obra", help="Digite o nome completo da obra")
        contrato = st.text_input("Número do Contrato", help="Digite o número do contrato (Ex: 2024/0001)")
        ordem_servico = st.text_input("Número da OS", help="Digite o número da Ordem de Serviço")
        contratante = st.text_input("Contratante", help="Nome da empresa/órgão contratante")
        data_inicio = st.date_input("Data de Início", help="Data de início da obra")

    with col2:
        contratada = st.text_input("Contratada", help="Nome da empresa contratada")
        valor_total = st.number_input("Valor Total da Obra (R$)", min_value=0.0, format="%.2f",
                                      help="Valor total do contrato")
        duracao_prevista = st.number_input("Duração Prevista (meses)", min_value=1, max_value=60, value=12,
                                           help="Quantidade de meses previstos para a obra")
        data_fim = st.date_input("Data de Término", help="Data prevista para término da obra")

    # 2. PLANEJAMENTO DE MEDIÇÕES
    st.subheader("2. Planejamento de Medições")

    col1, col2 = st.columns(2)
    with col1:
        num_itens = st.number_input("Quantidade de Itens", min_value=1, max_value=20, value=5,
                                    help="Número de itens/serviços que compõem a obra")
    with col2:
        num_medicoes = st.number_input("Quantidade de Medições", min_value=1, max_value=60, value=12,
                                       help="Número total de medições previstas")

    # 3. CADASTRO DE ITENS E VALORES
    st.subheader("3. Itens e Valores Previstos")

    # Inicializar DataFrame
    if 'df_valores' not in st.session_state:
        st.session_state.df_valores = pd.DataFrame(
            data={
                'Descrição': ['Insira o nome do item'] * num_itens,
                **{f'Medição {i + 1}': [0.0] * num_itens for i in range(num_medicoes)},
                'Total': [0.0] * num_itens
            },
            index=range(num_itens)
        )

    # Verificar mudanças no número de itens/medições
    current_rows = len(st.session_state.df_valores.index)
    current_cols = len(st.session_state.df_valores.columns)
    expected_cols = num_medicoes + 2

    if current_rows != num_itens or current_cols != expected_cols:
        st.session_state.df_valores = pd.DataFrame(
            data={
                'Descrição': ['Insira o nome do item'] * num_itens,
                **{f'Medição {i + 1}': [0.0] * num_itens for i in range(num_medicoes)},
                'Total': [0.0] * num_itens
            },
            index=range(num_itens)
        )

    # Interface de seleção de item
    col1, col2 = st.columns([3, 1])
    with col1:
        if 'item_atual' not in st.session_state:
            st.session_state.item_atual = 1

        item_selecionado = st.selectbox(
            "Selecione o Item para Editar",
            options=range(1, num_itens + 1),
            format_func=lambda x: f"Item {x}: {st.session_state.df_valores.at[x - 1, 'Descrição']}",
            key="item_selector",
            index=st.session_state.item_atual - 1
        )
        if item_selecionado != st.session_state.item_atual:
            st.session_state.item_atual = item_selecionado

    with col2:
        if st.button("Limpar Item Atual", key="btn_limpar_item"):
            i = item_selecionado - 1
            st.session_state.df_valores.iloc[i, 1:-1] = 0.0
            st.session_state.df_valores.at[i, 'Descrição'] = 'Insira o nome do item'
            st.rerun()

    # Ajustar índice e mostrar status
    i = item_selecionado - 1
    desc_atual = st.session_state.df_valores.at[i, 'Descrição']
    tem_valores = st.session_state.df_valores.iloc[i, 1:-1].sum() > 0
    status_item = "✅ Item Salvo" if desc_atual != 'Insira o nome do item' and tem_valores else "📝 Item não salvo"
    st.info(f"Status: {status_item}")


    # Input da descrição
    desc = st.text_input(
        "Descrição do Item",
        value=st.session_state.df_valores.at[i, 'Descrição'],
        key=f"desc_{i}",
        help="Descreva o item/serviço a ser medido"
    )
    st.session_state.df_valores.at[i, 'Descrição'] = desc

    # Interface de valores
    st.write(f"### Valores Previstos para: {desc}")
    st.write("Digite os valores previstos para cada medição:")

    # Organizar medições em 3 colunas
    cols_per_row = 3
    for j in range(0, num_medicoes, cols_per_row):
        cols = st.columns(cols_per_row)
        for k, col in enumerate(cols):
            medicao_num = j + k + 1
            if medicao_num <= num_medicoes:
                with col:
                    valor_anterior = st.session_state.df_valores.iloc[i, medicao_num]
                    valor_str = st.text_input(
                        f"Medição {medicao_num} (R$)",
                        value=format_currency_br(valor_anterior).replace('R$ ', ''),
                        key=f"med_{i}_{medicao_num}",
                        help=f"Valor previsto para a medição {medicao_num}"
                    )
                    try:
                        valor = float(valor_str.replace('.', '').replace(',', '.'))
                    except ValueError:
                        valor = 0.0
                    st.session_state.df_valores.iloc[i, medicao_num] = valor

    # Atualizar total no DataFrame silenciosamente
    valores_medicoes = [st.session_state.df_valores.iloc[i, j] for j in range(1, num_medicoes + 1)]
    total_item = sum(valores_medicoes)
    st.session_state.df_valores.iloc[i, -1] = total_item


    # Botão salvar item
    if st.button("Salvar Item", key=f"btn_salvar_item_{i}"):
        if not desc or desc == 'Insira o nome do item':
            st.error("❌ Insira uma descrição para o item")
            return
        if total_item <= 0:
            st.error("❌ O item deve ter valor maior que zero")
            return
        st.session_state.df_valores.at[i, 'Descrição'] = desc
        st.success(f"✅ Item '{desc}' salvo com sucesso!")

    # Mostrar tabela resumo
    df_display = st.session_state.df_valores.copy()
    for col in df_display.columns:
        if col != 'Descrição':
            df_display[col] = df_display[col].apply(format_currency_br)
    st.dataframe(df_display)

    # Calcular e mostrar total geral
    valor_total_calculado = st.session_state.df_valores['Total'].sum()
    st.write(f"### Valor Total Calculado: {format_currency_br(valor_total_calculado)}")

    # Botão salvar obra
    if st.button("Salvar Obra", key="btn_salvar_obra"):
        # Validações
        if not nome:
            st.error("❌ O nome da obra é obrigatório")
            return
        if not contrato:
            st.error("❌ O número do contrato é obrigatório")
            return
        if valor_total <= 0:
            st.error("❌ O valor total deve ser maior que zero")
            return
        if abs(valor_total_calculado - valor_total) > 0.01 and valor_total > 0:
            st.warning(
                f"⚠️ Atenção: O valor total calculado ({format_currency_br(valor_total_calculado)}) "
                f"é diferente do valor informado ({format_currency_br(valor_total)}). "
                f"Ajuste o valor total informado no início do cadastro ou verifique os valores das medições."
            )
            return


        # Salvar no banco
        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # Inserir obra
            cursor.execute('''
            INSERT INTO obras (
                user_id, nome, contrato, ordem_servico, contratante, contratada,
                valor_total, data_inicio, data_fim, duracao_prevista, num_medicoes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                st.session_state.user_id, nome, contrato, ordem_servico,
                contratante, contratada, valor_total, data_inicio, data_fim,
                duracao_prevista, num_medicoes
            ))

            obra_id = cursor.lastrowid

            # Inserir itens e medições
            for i in range(num_itens):
                desc = st.session_state.df_valores.iloc[i]['Descrição']
                if pd.isna(desc):
                    continue

                valor_total_item = st.session_state.df_valores.iloc[i, -1]
                cursor.execute('''
                INSERT INTO itens_obra (obra_id, descricao, valor_previsto)
                VALUES (?, ?, ?)
                ''', (obra_id, desc, valor_total_item))

                item_id = cursor.lastrowid

                for j in range(num_medicoes):
                    valor_previsto = st.session_state.df_valores.iloc[i, j + 1]
                    percentual = (valor_previsto / valor_total * 100) if valor_total > 0 else 0
                    cursor.execute('''
                    INSERT INTO medicoes (
                        obra_id, item_id, numero_medicao, valor_previsto, 
                        percentual_previsto, valor_realizado, percentual_realizado
                    ) VALUES (?, ?, ?, ?, ?, NULL, NULL)
                    ''', (obra_id, item_id, j + 1, valor_previsto, percentual))

            conn.commit()
            st.success("✅ Obra cadastrada com sucesso!")
            # Primeiro fazer o rerun, depois limpar o DataFrame
            st.rerun()

        except Exception as e:
            st.error(f"❌ Erro ao cadastrar obra: {str(e)}")
            conn.rollback()
        finally:
            conn.close()
