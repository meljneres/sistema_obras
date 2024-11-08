import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database.db_utils import get_db_connection
from utils.formatters import format_currency_br, format_percentage, format_millions_br


def gerar_relatorios():
    st.header("Relatórios")

    tabs = st.tabs([
        "Tabelas",
        "Aderência",
        "Desempenho Físico",
        "Desempenho Financeiro",
        "IDP"
    ])

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

    with tabs[0]:
        gerar_tabelas(obra_id)

    with tabs[1]:
        gerar_graficos_aderencia(obra_id)

    with tabs[2]:
        gerar_graficos_desempenho_fisico(obra_id)

    with tabs[3]:
        gerar_graficos_desempenho_financeiro(obra_id)

    with tabs[4]:
        gerar_grafico_idp(obra_id)

    conn.close()


def gerar_tabelas(obra_id):
    st.subheader("Tabelas de Acompanhamento")

    conn = get_db_connection()
    cursor = conn.cursor()

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

    if dados:
        df = pd.DataFrame(dados, columns=[
            'Medição',
            'Valor Previsto',
            'Valor Realizado',
            'Valor Total'
        ])

        # Calcular percentuais e valores acumulados
        df['Previsto Acumulado'] = df['Valor Previsto'].cumsum()
        df['Realizado Acumulado'] = df['Valor Realizado'].fillna(0).cumsum()
        df['% Previsto Acumulado'] = (df['Previsto Acumulado'] / df['Valor Total'] * 100).round(2)
        df['% Realizado Acumulado'] = (df['Realizado Acumulado'] / df['Valor Total'] * 100).round(2)
        df['Desvio'] = (df['% Realizado Acumulado'] - df['% Previsto Acumulado']).round(2)

        # Formatar valores para exibição
        df_display = df.copy()
        for col in ['Valor Previsto', 'Valor Realizado', 'Previsto Acumulado', 'Realizado Acumulado']:
            df_display[col] = df_display[col].apply(format_currency_br)

        for col in ['% Previsto Acumulado', '% Realizado Acumulado', 'Desvio']:
            df_display[col] = df_display[col].apply(format_percentage)

        # Mostrar tabelas
        st.write("### Valores Mensais")
        st.dataframe(df_display[['Medição', 'Valor Previsto', 'Valor Realizado']])

        st.write("### Valores Acumulados")
        st.dataframe(df_display[['Medição', 'Previsto Acumulado', 'Realizado Acumulado']])

        st.write("### Percentuais e Desvios")
        st.dataframe(df_display[['Medição', '% Previsto Acumulado', '% Realizado Acumulado', 'Desvio']])


def gerar_graficos_aderencia(obra_id):
    st.subheader("Gráficos de Aderência")

    conn = get_db_connection()
    cursor = conn.cursor()

    col1, col2 = st.columns(2)

    with col1:
        # Gráfico 1 - Aderência à duração contratual
        cursor.execute('''
        SELECT duracao_prevista, duracao_realizada 
        FROM obras WHERE id = ?
        ''', (obra_id,))
        duracao_data = cursor.fetchone()

        df_duracao = pd.DataFrame({
            'Tipo': ['Contrato', 'EMTEC'],
            'Meses': [duracao_data[0], duracao_data[1] or 0]
        })

        fig1 = px.bar(df_duracao,
                      x='Tipo',
                      y='Meses',
                      title='Aderência à duração contratual em meses',
                      color='Tipo',
                      color_discrete_sequence=['blue', 'red'])
        fig1.update_layout(showlegend=False)
        st.plotly_chart(fig1)

    with col2:
        # Gráfico 2 - Aderência ao avanço físico
        cursor.execute('''
        SELECT 
            MAX(percentual_previsto) as previsto_total,
            MAX(percentual_realizado) as realizado_total
        FROM medicoes 
        WHERE obra_id = ?
        ''', (obra_id,))

        percentuais = cursor.fetchone()

        df_avanco = pd.DataFrame({
            'Tipo': ['Contrato', 'EMTEC'],
            'Previsto': [86.85, percentuais[0] or 0],
            'Realizado': [0, percentuais[1] or 0]
        })

        fig2 = px.bar(df_avanco,
                      x='Tipo',
                      y=['Previsto', 'Realizado'],
                      title='Aderência ao avanço físico em relação ao contratual',
                      barmode='group',
                      color_discrete_sequence=['blue', 'red'])
        fig2.update_layout(yaxis_tickformat='.2f%')
        st.plotly_chart(fig2)


def gerar_graficos_desempenho_fisico(obra_id):
    st.subheader("Desempenho Físico")

    conn = get_db_connection()
    cursor = conn.cursor()

    # Buscar dados percentuais
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
    df = pd.DataFrame(dados, columns=['Medição', 'Previsto', 'Realizado', 'Valor Total'])

    # Calcular percentuais acumulados
    df['Previsto Acumulado'] = (df['Previsto'].cumsum() / df['Valor Total'] * 100).round(2)
    df['Realizado Acumulado'] = (df['Realizado'].fillna(0).cumsum() / df['Valor Total'] * 100).round(2)
    df['Desvio'] = (df['Realizado Acumulado'] - df['Previsto Acumulado']).round(2)

    # Gráfico 5 - Curva completa
    fig5 = go.Figure()
    fig5.add_trace(go.Scatter(
        x=df['Medição'],
        y=df['Previsto Acumulado'],
        name='Previsto acumulado',
        mode='lines+markers',
        text=df['Previsto Acumulado'].apply(lambda x: f'{x:.2f}%'),
        textposition='top center',
        line=dict(color='blue')
    ))
    fig5.add_trace(go.Scatter(
        x=df['Medição'],
        y=df['Realizado Acumulado'],
        name='Realizado acumulado',
        mode='lines+markers',
        text=df['Realizado Acumulado'].apply(lambda x: f'{x:.2f}%'),
        textposition='bottom center',
        line=dict(color='red')
    ))
    fig5.update_layout(
        title='Curva de Desempenho Físico da Obra',
        xaxis_title='Medição',
        yaxis_title='Percentual (%)',
        yaxis=dict(
            range=[0, 100],
            tickformat='.2f',
            ticksuffix='%'
        ),
        showlegend=True
    )
    st.plotly_chart(fig5)

    # Gráfico 6 - Até última medição registrada
    ultima_medicao = df[df['Realizado'].notna()]['Medição'].max()
    df_atual = df[df['Medição'] <= ultima_medicao].copy()

    fig6 = go.Figure()
    fig6.add_trace(go.Scatter(
        x=df_atual['Medição'],
        y=df_atual['Previsto Acumulado'],
        name='Previsto acumulado',
        mode='lines+markers',
        text=df_atual['Previsto Acumulado'].apply(lambda x: f'{x:.2f}%'),
        textposition='top center',
        line=dict(color='blue')
    ))
    fig6.add_trace(go.Scatter(
        x=df_atual['Medição'],
        y=df_atual['Realizado Acumulado'],
        name='Realizado acumulado',
        mode='lines+markers',
        text=df_atual['Realizado Acumulado'].apply(lambda x: f'{x:.2f}%'),
        textposition='bottom center',
        line=dict(color='red')
    ))
    fig6.update_layout(
        title=f'Curva de Desempenho Físico até a {ultima_medicao}ª Medição',
        xaxis_title='Medição',
        yaxis_title='Percentual (%)',
        yaxis=dict(
            range=[0, 100],
            tickformat='.2f',
            ticksuffix='%'
        ),
        showlegend=True
    )
    st.plotly_chart(fig6)


def gerar_graficos_desempenho_financeiro(obra_id):
    st.subheader("Desempenho Financeiro")

    conn = get_db_connection()
    cursor = conn.cursor()

    # Buscar dados financeiros
    cursor.execute('''
    SELECT 
        m.numero_medicao,
        SUM(m.valor_previsto) as valor_previsto,
        SUM(m.valor_realizado) as valor_realizado
    FROM medicoes m
    WHERE m.obra_id = ?
    GROUP BY m.numero_medicao
    ORDER BY m.numero_medicao
    ''', (obra_id,))

    dados = cursor.fetchall()
    df = pd.DataFrame(dados, columns=['Medição', 'Previsto', 'Realizado'])

    # Calcular valores acumulados em milhões
    df['Previsto Acumulado'] = df['Previsto'].cumsum() / 1_000_000
    df['Realizado Acumulado'] = df['Realizado'].fillna(0).cumsum() / 1_000_000

    # Gráfico 3 - Curva completa
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(
        x=df['Medição'],
        y=df['Previsto Acumulado'],
        name='Previsto acumulado',
        mode='lines+markers',
        text=df['Previsto Acumulado'].apply(lambda x: f'R$ {x:.2f}M'),
        textposition='top center',
        line=dict(color='blue')
    ))
    fig3.add_trace(go.Scatter(
        x=df['Medição'],
        y=df['Realizado Acumulado'],
        name='Realizado acumulado',
        mode='lines+markers',
        text=df['Realizado Acumulado'].apply(lambda x: f'R$ {x:.2f}M'),
        textposition='bottom center',
        line=dict(color='red')
    ))
    fig3.update_layout(
        title='Curva de Desempenho Financeiro da Obra',
        xaxis_title='Medição',
        yaxis_title='Milhões (R$)',
        yaxis=dict(
            tickformat='R$ ,.2f',
            tickprefix='R$ '
        )
    )
    st.plotly_chart(fig3)

    # Gráfico 4 - Até última medição registrada
    ultima_medicao = df[df['Realizado'].notna()]['Medição'].max()
    df_atual = df[df['Medição'] <= ultima_medicao].copy()

    fig4 = go.Figure()
    fig4.add_trace(go.Scatter(
        x=df_atual['Medição'],
        y=df_atual['Previsto Acumulado'],
        name='Previsto acumulado',
        mode='lines+markers',
        text=df_atual['Previsto Acumulado'].apply(lambda x: f'R$ {x:.2f}M'),
        textposition='top center',
        line=dict(color='blue')
    ))
    fig4.add_trace(go.Scatter(
        x=df_atual['Medição'],
        y=df_atual['Realizado Acumulado'],
        name='Realizado acumulado',
        mode='lines+markers',
        text=df_atual['Realizado Acumulado'].apply(lambda x: f'R$ {x:.2f}M'),
        textposition='bottom center',
        line=dict(color='red')
    ))

    # Continuação do gráfico 4 em gerar_graficos_desempenho_financeiro
    fig4.update_layout(
        title=f'Curva de Desempenho Financeiro até a {ultima_medicao}ª Medição',
        xaxis_title='Medição',
        yaxis_title='Milhões (R$)',
        yaxis=dict(
            tickformat='R$ ,.2f',
            tickprefix='R$ '
        ),
        showlegend=True,
        height=400
    )
    st.plotly_chart(fig4)

    # Mostrar tabela de valores financeiros
    st.write("### Valores Financeiros")
    df_display = df.copy()
    df_display['Previsto'] = df_display['Previsto'].apply(format_currency_br)
    df_display['Realizado'] = df_display['Realizado'].apply(format_currency_br)
    df_display['Previsto Acumulado'] = df_display['Previsto Acumulado'].apply(
        lambda x: format_millions_br(x * 1_000_000))
    df_display['Realizado Acumulado'] = df_display['Realizado Acumulado'].apply(
        lambda x: format_millions_br(x * 1_000_000))
    st.dataframe(df_display)


def gerar_grafico_idp(obra_id):
    st.subheader("Índice de Desempenho de Prazo (IDP)")

    conn = get_db_connection()
    cursor = conn.cursor()

    # Calcular IDP
    cursor.execute('''
    SELECT 
        numero_medicao,
        CASE 
            WHEN SUM(valor_previsto) = 0 THEN 1
            ELSE CAST(SUM(valor_realizado) AS FLOAT) / 
                 CAST(SUM(valor_previsto) AS FLOAT)
        END as idp
    FROM medicoes
    WHERE obra_id = ?
    GROUP BY numero_medicao
    ORDER BY numero_medicao
    ''', (obra_id,))

    dados = cursor.fetchall()
    df = pd.DataFrame(dados, columns=['Medição', 'IDP'])
    df['META'] = 1.0

    # Gráfico 7 - IDP
    fig7 = go.Figure()
    fig7.add_trace(go.Scatter(
        x=df['Medição'],
        y=df['IDP'],
        name='IDP',
        mode='lines+markers',
        text=df['IDP'].apply(lambda x: f'{x:.2f}'),
        textposition='top center',
        line=dict(color='blue')
    ))
    fig7.add_trace(go.Scatter(
        x=df['Medição'],
        y=df['META'],
        name='Meta',
        mode='lines',
        line=dict(color='red', dash='dash')
    ))
    fig7.update_layout(
        title='Variação do IDP ao longo das medições',
        xaxis_title='Medição',
        yaxis_title='IDP',
        yaxis=dict(
            range=[0, 2],
            tickformat='.2f'
        ),
        showlegend=True,
        height=400
    )
    st.plotly_chart(fig7)

    # Mostrar tabela de IDP
    st.write("### Valores de IDP por Medição")
    df_display = df[['Medição', 'IDP']].copy()
    df_display['IDP'] = df_display['IDP'].apply(lambda x: f"{x:.2f}")
    st.dataframe(df_display)

    # Mostrar análise do IDP
    st.write("### Análise do IDP")
    idp_atual = df[df['IDP'].notna()]['IDP'].iloc[-1]

    col1, col2 = st.columns(2)
    with col1:
        st.metric("IDP Atual", f"{idp_atual:.2f}")

    with col2:
        if idp_atual > 1:
            st.success("Projeto adiantado")
        elif idp_atual == 1:
            st.info("Projeto no prazo")
        else:
            st.warning("Projeto atrasado")

    # Mostrar tabela completa com todos os índices
    st.write("### Tabela Completa de Índices")
    df_indices = pd.DataFrame({
        'Medição': df['Medição'],
        'IDP': df['IDP'],
        'Meta': df['META'],
        'Status': df['IDP'].apply(lambda x:
                                  'Adiantado' if x > 1 else
                                  'No prazo' if x == 1 else
                                  'Atrasado' if x > 0 else 'Não iniciado'
                                  )
    })

    df_indices['IDP'] = df_indices['IDP'].apply(lambda x: f"{x:.2f}")
    df_indices['Meta'] = df_indices['Meta'].apply(lambda x: f"{x:.2f}")
    st.dataframe(df_indices)

    conn.close()