import streamlit as st
from database.db_utils import get_db_connection, add_user, verify_user


def login():
    st.title("Sistema de Gestão de Obras")

    # Criar duas colunas
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Login")
        # Formulário de login
        with st.form("login_form"):
            username = st.text_input("Usuário")
            password = st.text_input("Senha", type="password")
            submit_login = st.form_submit_button("Entrar")

            if submit_login:
                user_id = verify_user(username, password)
                if user_id:
                    st.session_state.user_id = user_id
                    st.session_state.username = username
                    st.success("Login realizado com sucesso!")
                    st.rerun()
                else:
                    st.error("Usuário ou senha inválidos")

    with col2:
        st.subheader("Cadastro")
        # Formulário de cadastro
        with st.form("signup_form"):
            new_username = st.text_input("Novo Usuário")
            new_password = st.text_input("Nova Senha", type="password")
            confirm_password = st.text_input("Confirmar Senha", type="password")
            submit_signup = st.form_submit_button("Cadastrar")

            if submit_signup:
                if new_password != confirm_password:
                    st.error("As senhas não coincidem")
                elif len(new_password) < 6:
                    st.error("A senha deve ter pelo menos 6 caracteres")
                else:
                    if add_user(new_username, new_password):
                        st.success("Usuário cadastrado com sucesso! Faça login para continuar.")
                    else:
                        st.error("Nome de usuário já existe")


def logout():
    if st.sidebar.button("Sair"):
        st.session_state.user_id = None
        st.session_state.username = None
        st.rerun()


def check_authentication():
    return 'user_id' in st.session_state and st.session_state.user_id is not None
