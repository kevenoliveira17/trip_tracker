# app.py
"""Travel Expenses Tracker — Página única que combina **Login/Cadastro** e Menu inicial.

Se o usuário não estiver autenticado, exibimos as abas de login/cadastro.
Após autenticar, mostramos atalhos para as páginas de Registrar Gasto e Dashboard.
"""

from __future__ import annotations

import streamlit as st

from services import auth

st.set_page_config(page_title="💸 Travel Expenses", page_icon="💸", layout="centered")

# ---------------------------------------------------------------------------
# Sidebar — botão de logout (aparece sempre)
# ---------------------------------------------------------------------------
if st.sidebar.button("🚪 Sair", key="logout_btn"):
    for k in ("user_id",):
        st.session_state.pop(k, None)
    st.sidebar.success("Sessão encerrada.")
    st.rerun()

# ---------------------------------------------------------------------------
# Cabeçalho
# ---------------------------------------------------------------------------
st.title("💸 Travel Expenses Tracker")

# ---------------------------------------------------------------------------
# Fluxos dependendo do estado de autenticação
# ---------------------------------------------------------------------------
if "user_id" in st.session_state:
    # ------------------ USUÁRIO LOGADO ------------------
    st.success(f"Você está logado como **{st.session_state['user_id']}**.")

    st.markdown("### Ações rápidas")
    st.page_link("pages/1_Registrar_Gasto.py", label="➕ Registrar novo gasto", icon="📥")
    st.page_link("pages/2_Dashboard.py", label="📊 Ver dashboard", icon="📊")
else:
    # ------------------ NÃO LOGADO – mostrar abas Login/Cadastro ------------------
    st.info("Para começar, faça login ou crie uma conta:")

    login_tab, register_tab = st.tabs(["🔑 Login", "➕ Cadastrar"])

    with login_tab:
        st.header("🔑 Fazer login")
        login_email = st.text_input("E‑mail", key="login_email")
        login_password = st.text_input("Senha", type="password", key="login_pwd")

        if st.button("Entrar", key="login_btn"):
            if auth.verify_user(login_email, login_password):
                st.session_state["user_id"] = login_email.strip().lower()
                st.success("Login realizado com sucesso! Redirecionando…")
                st.rerun()
            else:
                st.error("Credenciais inválidas.")

    with register_tab:
        st.header("➕ Criar conta")
        reg_email = st.text_input("E‑mail", key="reg_email")
        reg_password = st.text_input("Senha", type="password", key="reg_pwd")
        reg_password2 = st.text_input("Confirmar senha", type="password", key="reg_pwd2")

        if st.button("Cadastrar", key="reg_btn"):
            if reg_password != reg_password2:
                st.error("As senhas não coincidem.")
            else:
                try:
                    auth.create_user(reg_email, reg_password)
                    st.success("Conta criada! Faça login na aba ao lado.")
                except ValueError as e:
                    st.error(str(e))

# ---------------------------------------------------------------------------
# Rodapé
# ---------------------------------------------------------------------------
st.markdown("---")
# st.caption("Desenvolvido em Streamlit · Versão demo")
