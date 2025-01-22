import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from database.db_utils import get_db_connection
from utils.formatters import format_currency_br, format_percentage
from datetime import datetime
from utils.calculadora import calcular_glosa, calcular_valor_glosa


def gerar_relatorios():
    st.header("Relatórios")

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
           valor_total, data_inicio, data_fim, duracao_prevista
    FROM obras WHERE id = ?
    ''', (obra_id,))
    obra_data = cursor.fetchone()

    # 1. IDENTIFICAÇÃO
    st.subheader("1. Identificação")
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Contrato nº:** {obra_data[1]}")
        st.write(f"**Nº da OS:** {obra_data[2]}")
        st.write(f"**Objeto:** {obra_data[0]}")
    with col2:
        st.write(f"**Contratante:** {obra_data[3]}")
        st.write(f"**Contratada:** {obra_data[4]}")
        st.write(f"**Valor Total:** {format_currency_br(obra_data[5])}")

    # 2. DESEMPENHO FÍSICO
    st.subheader("2. Desempenho Físico")

    # Buscar dados das medições
    cursor.execute('''
    SELECT 
        m.numero_medicao,
        SUM(m.valor_previsto) as valor_previsto,
        SUM(m.valor_realizado) as valor_realizado,
        o.valor_total
    FROM medicoes m
    JOIN obras o ON m.obra_id = o.id
    WHERE m.obra_id = ?
    GROUP BY m.numero_medicao
    ORDER BY m.numero_medicao
    ''', (obra_id,))

    dados = cursor.fetchall()
    if not dados:
        st.warning("Não há medições registradas para esta obra.")
        return

    df = pd.DataFrame(dados, columns=['Medição', 'Previsto', 'Realizado', 'Valor Total'])
    valor_total = df['Valor Total'].iloc[0] if not df.empty else 1

    # Calcular percentuais acumulados
    if not df.empty:
        df['Previsto Acumulado'] = (df['Previsto'].cumsum() / valor_total * 100).round(2)
        df['Realizado Acumulado'] = (df['Realizado'].fillna(0).cumsum() / valor_total * 100).round(2)
        df['Desvio'] = (df['Realizado Acumulado'] - df['Previsto Acumulado']).round(2)

    # Gráfico de Desempenho Físico (Curva S)
    fig = go.Figure()

    # Linha do previsto
    fig.add_trace(go.Scatter(
        x=df['Medição'],
        y=df['Previsto Acumulado'],
        name='Previsto acumulado',
        mode='lines+markers+text',
        text=df['Previsto Acumulado'].apply(lambda x: f'{x:.2f}%'),
        textposition='top center',
        line=dict(color='blue')
    ))

    # Linha do realizado
    fig.add_trace(go.Scatter(
        x=df['Medição'],
        y=df['Realizado Acumulado'],
        name='Realizado acumulado',
        mode='lines+markers+text',
        text=df['Realizado Acumulado'].apply(lambda x: f'{x:.2f}%'),
        textposition='bottom center',
        line=dict(color='red')
    ))

    fig.update_layout(
        title='Curva de Desempenho Físico da Obra',
        xaxis_title='Medição',
        yaxis_title='Percentual (%)',
        yaxis=dict(
            range=[0, 100],
            tickformat='.2f',
            ticksuffix='%'
        ),
        showlegend=True,
        height=500
    )

    st.plotly_chart(fig, use_container_width=True, key="plot_curva_s")

    # Tabela de Percentuais
    st.write("### Valores Percentuais")
    df_display = pd.DataFrame({
        'Medição': df['Medição'],
        'Previsto acumulado': df['Previsto Acumulado'].apply(lambda x: f"{x:.2f}%"),
        'Realizado acumulado': df['Realizado Acumulado'].apply(lambda x: f"{x:.2f}%"),
        'Desvio': df['Desvio'].apply(lambda x: f"{x:.2f}%")
    })
    st.dataframe(df_display)

    # 3. INDICADORES
    st.subheader("3. Indicadores")

    # Calcular IDP
    df['IDP'] = (df['Realizado'] / df['Previsto']).round(2)
    df['META'] = 1.0

    # Tabela IDP
    st.write("### Índice de Desempenho de Prazo (IDP)")
    df_idp = pd.DataFrame({
        'Medição': df['Medição'],
        'IDP': df['IDP'].apply(lambda x: f"{x:.2f}"),
        'META': df['META'].apply(lambda x: f"{x:.2f}")
    })
    st.dataframe(df_idp)

    # Gráfico IDP
    fig_idp = go.Figure()

    # Linha do IDP
    fig_idp.add_trace(go.Scatter(
        x=df['Medição'],
        y=df['IDP'],
        name='IDP',
        mode='lines+markers+text',
        text=df['IDP'].apply(lambda x: f'{x:.2f}'),
        textposition='top center',
        line=dict(color='blue')
    ))

    # Linha da META
    fig_idp.add_trace(go.Scatter(
        x=df['Medição'],
        y=df['META'],
        name='Meta',
        mode='lines',
        line=dict(color='red', dash='dash')
    ))

    fig_idp.update_layout(
        title='Variação do IDP ao longo das medições',
        xaxis_title='Medição',
        yaxis_title='IDP',
        yaxis=dict(
            range=[0, 2],
            tickformat='.2f'
        ),
        showlegend=True,
        height=500
    )

    st.plotly_chart(fig_idp, use_container_width=True, key="plot_idp_1")


    # Adicionar seção de IMR no relatório
    st.subheader("5. Instrumento de Medição de Resultado")

    # Buscar fatores IMR da obra
    cursor.execute('''
    SELECT numero_medicao, fator_ponderacao 
    FROM imr_fatores 
    WHERE obra_id = ?
    ORDER BY numero_medicao
    ''', (obra_id,))

    fatores_imr = cursor.fetchall()

    # Criar DataFrame com fatores IMR
    df_imr = pd.DataFrame(fatores_imr, columns=['Medição', 'Fator IMR'])

    # Adicionar colunas de IDP e Glosa
    df_imr['IDP'] = df['IDP']
    df_imr['Glosa'] = df_imr.apply(
        lambda row: calcular_glosa(obra_id, row['IDP'], row['Medição']),
        axis=1
    )

    # Mostrar tabela IMR
    st.write("### Fatores e Glosas por Medição")
    df_display_imr = df_imr.copy()
    df_display_imr['Fator IMR'] = df_display_imr['Fator IMR'].apply(lambda x: f"{x:.2f}")
    df_display_imr['IDP'] = df_display_imr['IDP'].apply(lambda x: f"{x:.2f}")
    df_display_imr['Glosa'] = df_display_imr['Glosa'].apply(lambda x: f"{x:.2%}")
    st.dataframe(df_display_imr)

    # Gráfico de Glosas
    fig_glosas = go.Figure()
    fig_glosas.add_trace(go.Bar(
        x=df_imr['Medição'],
        y=df_imr['Glosa'] * 100,
        name='Glosa (%)',
        text=df_imr['Glosa'].apply(lambda x: f'{x:.2%}'),
        textposition='auto',
    ))

    fig_glosas.update_layout(
        title='Glosas Aplicadas por Medição',
        xaxis_title='Medição',
        yaxis_title='Glosa (%)',
        yaxis=dict(
            tickformat='.2f',
            ticksuffix='%'
        ),
        showlegend=True,
        height=400
    )

    st.plotly_chart(fig_glosas, use_container_width=True, key="plot_glosas")

    # Gráfico IDP
    fig_idp = go.Figure()

    # Linha do IDP
    fig_idp.add_trace(go.Scatter(
        x=df['Medição'],
        y=df['IDP'],
        name='IDP',
        mode='lines+markers+text',
        text=df['IDP'].apply(lambda x: f'{x:.2f}'),
        textposition='top center',
        line=dict(color='blue')
    ))

    # Linha da META
    fig_idp.add_trace(go.Scatter(
        x=df['Medição'],
        y=df['META'],
        name='Meta',
        mode='lines',
        line=dict(color='red', dash='dash')
    ))

    fig_idp.update_layout(
        title='Variação do IDP ao longo das medições',
        xaxis_title='Medição',
        yaxis_title='IDP',
        yaxis=dict(
            range=[0, 2],
            tickformat='.2f'
        ),
        showlegend=True,
        height=500
    )

