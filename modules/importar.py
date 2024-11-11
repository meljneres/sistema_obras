# modules/importar.py
import streamlit as st
import pandas as pd
import numpy as np
from database.db_utils import get_db_connection
from datetime import datetime


def importar_dados():
    st.header("Importar Dados")

    uploaded_file = st.file_uploader("Escolha a planilha Excel", type=['xlsx'])

    if uploaded_file is not None:
        try:
            # Ler a planilha
            df = pd.read_excel(uploaded_file)

            # Buscar dados diretamente das linhas específicas
            try:
                # Converter todas as colunas para string primeiro
                df_str = df.astype(str)

                # Encontrar as linhas corretas
                previsto_idx = \
                df_str.index[df_str.iloc[:, 0].str.contains('Previsto acumulado', case=False, na=False)].tolist()[0]
                realizado_idx = \
                df_str.index[df_str.iloc[:, 0].str.contains('Realizado acumulado', case=False, na=False)].tolist()[0]

                # Extrair os valores
                previsto_acumulado = df.iloc[previsto_idx, 1:13].values
                realizado_acumulado = df.iloc[realizado_idx, 1:13].values

                # Converter para float, tratando valores vazios
                previsto_acumulado = pd.to_numeric(previsto_acumulado, errors='coerce').fillna(0)
                realizado_acumulado = pd.to_numeric(realizado_acumulado, errors='coerce').fillna(0)

                # Buscar valores financeiros (últimas linhas)
                valores_previsto = []
                valores_realizado = []

                # Procurar a última ocorrência dos valores financeiros
                for i in range(len(df)):
                    row = df.iloc[i]
                    if isinstance(row[0], str) and 'R$' in str(row[1]):
                        valores_previsto = row[1:13].values
                        if i + 1 < len(df):
                            valores_realizado = df.iloc[i + 1, 1:13].values

                # Converter valores financeiros para float
                def convert_currency(val):
                    if pd.isna(val):
                        return 0.0
                    if isinstance(val, str):
                        return float(val.replace('R$', '').replace('.', '').replace(',', '.').strip())
                    return float(val)

                valores_previsto = [convert_currency(x) for x in valores_previsto]
                valores_realizado = [convert_currency(x) for x in valores_realizado]

                # Mostrar preview dos dados extraídos
                st.write("### Dados Extraídos")

                col1, col2 = st.columns(2)
                with col1:
                    st.write("Percentuais Acumulados:")
                    df_percentuais = pd.DataFrame({
                        'Medição': range(1, 13),
                        'Previsto (%)': previsto_acumulado,
                        'Realizado (%)': realizado_acumulado
                    })
                    st.dataframe(df_percentuais)

                with col2:
                    st.write("Valores Financeiros:")
                    df_valores = pd.DataFrame({
                        'Medição': range(1, 13),
                        'Previsto (R$)': valores_previsto,
                        'Realizado (R$)': valores_realizado
                    })
                    st.dataframe(df_valores)

                if st.button("Confirmar Importação"):
                    conn = get_db_connection()
                    cursor = conn.cursor()

                    try:
                        # Inserir obra
                        cursor.execute('''
                        INSERT INTO obras (
                            nome, valor_total, data_inicio, duracao_prevista, num_medicoes
                        ) VALUES (?, ?, ?, ?, ?)
                        ''', ('Obra Importada', valores_previsto[-1], datetime.now().date(), 12, 12))

                        obra_id = cursor.lastrowid

                        # Inserir medições
                        for i in range(12):
                            cursor.execute('''
                            INSERT INTO medicoes (
                                obra_id, numero_medicao, valor_previsto, valor_realizado,
                                percentual_previsto, percentual_realizado, data_medicao
                            ) VALUES (?, ?, ?, ?, ?, ?, ?)
                            ''', (
                                obra_id,
                                i + 1,
                                valores_previsto[i],
                                valores_realizado[i] if valores_realizado[i] != 0 else None,
                                previsto_acumulado[i],
                                realizado_acumulado[i] if realizado_acumulado[i] != 0 else None,
                                datetime.now().date()
                            ))

                        conn.commit()
                        st.success("Dados importados com sucesso!")

                    except Exception as e:
                        st.error(f"Erro ao importar dados: {str(e)}")
                        conn.rollback()
                    finally:
                        conn.close()

            except Exception as e:
                st.error(f"Erro ao processar dados: {str(e)}")

        except Exception as e:
            st.error(f"Erro ao ler planilha: {str(e)}")