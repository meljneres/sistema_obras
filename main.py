import streamlit as st
import os
from database.db_utils import create_tables
from database.init_db import init_database
from modules.auth import login, logout, check_authentication
from modules.cadastro import cadastrar_obra
from modules.medicoes import registrar_medicao
from modules.relatorios import gerar_relatorios
from modules.edicao import editar_obra


# Configuração da página Streamlit
st.set_page_config(
    page_title="Sistema de Gestão de Obras",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializar o estado da sessão se necessário
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'username' not in st.session_state:
    st.session_state.username = None


def main():
    # Inicializar banco de dados se não existir
    if not os.path.exists('obras.db'):
        create_tables()
        init_database()

    # Verificar autenticação
    if not check_authentication():
        login()
        return

    # Sidebar com informações do usuário e menu
    with st.sidebar:
        st.write(f"👤 Usuário: {st.session_state.username}")

        menu = ["Início", "Cadastro de Obra", "Editar Obra", "Medições", "Relatórios"]
        choice = st.selectbox("Menu", menu)

        if st.button("Sair"):
            st.session_state.user_id = None
            st.session_state.username = None
            st.rerun()

    # Conteúdo principal baseado na escolha do menu
    if choice == "Início":
        st.title("Sistema de Gestão de Obras")

        # Dashboard inicial
        col1, col2 = st.columns(2)
        with col1:
            st.write("### Suas Obras Recentes")
            from database.db_utils import get_db_connection
            conn = get_db_connection()
            cursor = conn.cursor()

            try:
                cursor.execute('''
                SELECT nome, contrato, data_inicio 
                FROM obras 
                WHERE user_id = ? 
                ORDER BY data_inicio DESC 
                LIMIT 5
                ''', (st.session_state.user_id,))

                obras = cursor.fetchall()
                if obras:
                    for obra in obras:
                        st.write(f"- {obra[0]} (Contrato: {obra[1]})")
                else:
                    st.info("Nenhuma obra cadastrada ainda.")
            except Exception as e:
                st.error(f"Erro ao carregar obras: {str(e)}")
            finally:
                conn.close()

        with col2:
            st.write("### Medições Pendentes")
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute('''
                SELECT o.nome, m.numero_medicao
                FROM obras o
                JOIN medicoes m ON o.id = m.obra_id
                WHERE o.user_id = ? 
                AND m.valor_realizado IS NULL
                GROUP BY o.id, m.numero_medicao
                ORDER BY m.numero_medicao
                LIMIT 5
                ''', (st.session_state.user_id,))

                medicoes = cursor.fetchall()
                if medicoes:
                    for med in medicoes:
                        st.write(f"- {med[0]} (Medição {med[1]})")
                else:
                    st.info("Nenhuma medição pendente.")
                conn.close()
            except Exception as e:
                st.error(f"Erro ao carregar medições: {str(e)}")

    elif choice == "Cadastro de Obra":
        cadastrar_obra()

    elif choice == "Editar Obra":
        editar_obra()

    elif choice == "Medições":
        registrar_medicao()

    elif choice == "Relatórios":
        gerar_relatorios()


if __name__ == "__main__":
    main()
