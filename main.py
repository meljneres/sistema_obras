import streamlit as st
from database.db_utils import create_tables
from modules.cadastro import cadastrar_obra
from modules.medicoes import registrar_medicao
from modules.relatorios import gerar_relatorios
from modules.editar import editar_previsoes  # Adicione esta linha

st.set_page_config(page_title="Sistema de Gestão de Obras", layout="wide")


def main():
    st.title("Sistema de Gestão de Obras")

    if 'initialized' not in st.session_state:
        create_tables()
        st.session_state.initialized = True

    menu = ["Início", "Cadastro de Obra", "Medições", "Editar Previsões", "Relatórios"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Início":
        st.write("""
        # Bem-vindo ao Sistema de Gestão de Obras

        Este sistema permite:

        - **Cadastro de Obra**: Cadastre uma nova obra com seus itens e previsões
        - **Medições**: Registre as medições realizadas para cada item
        - **Editar Previsões**: Ajuste os valores previstos de obras já cadastradas
        - **Relatórios**: Visualize gráficos e tabelas de acompanhamento

        Selecione uma opção no menu lateral para começar.
        """)
    elif choice == "Cadastro de Obra":
        st.write("""
        ### Cadastro de Nova Obra

        Nesta página você deve:
        1. Preencher os dados básicos da obra
        2. Definir o número de itens e medições
        3. Cadastrar os valores previstos para cada item
        4. Salvar a obra
        """)
        cadastrar_obra()
    elif choice == "Medições":
        st.write("""
        ### Registro de Medições

        Nesta página você pode:
        1. Selecionar uma obra cadastrada
        2. Escolher qual medição deseja registrar
        3. Informar os valores realizados para cada item
        4. Salvar a medição
        """)
        registrar_medicao()
    elif choice == "Editar Previsões":
        editar_previsoes()
    elif choice == "Relatórios":
        st.write("""
        ### Relatórios e Gráficos

        Aqui você encontra:
        - Tabelas com valores e percentuais
        - Gráficos de desempenho físico e financeiro
        - Indicadores de desempenho (IDP)
        - Análise de aderência ao planejado

        Selecione uma obra para visualizar seus dados.
        """)
        gerar_relatorios()


if __name__ == "__main__":
    main()