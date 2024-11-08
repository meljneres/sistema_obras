import streamlit as st
from database.db_utils import create_tables, get_db_connection
from modules.cadastro import cadastrar_obra
from modules.medicoes import registrar_medicao
from modules.relatorios import gerar_relatorios

# Configuração inicial do Streamlit
st.set_page_config(page_title="Sistema de Gestão de Obras", layout="wide")


def main():
    st.title("Sistema de Gestão de Obras")

    if 'initialized' not in st.session_state:
        create_tables()
        st.session_state.initialized = True

    menu = ["Início", "Cadastro de Obra", "Medições", "Relatórios"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Início":
        st.write("Bem-vindo ao Sistema de Gestão de Obras")
        st.write("Selecione uma opção no menu lateral para começar")
    elif choice == "Cadastro de Obra":
        cadastrar_obra()
    elif choice == "Medições":
        registrar_medicao()
    elif choice == "Relatórios":
        gerar_relatorios()


if __name__ == "__main__":
    main()