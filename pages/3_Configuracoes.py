
"""Configurações básicas do usuário (categorias, contas, orçamento)."""

from __future__ import annotations

import streamlit as st

from services import settings_manager as sm

st.set_page_config(page_title="Configurações", page_icon="⚙️", layout="centered")

# ---------------------------------------------------------------------------
# Login check
# ---------------------------------------------------------------------------
if "user_id" not in st.session_state:
    st.warning("Faça login para acessar as configurações.")
    st.stop()

user_id = st.session_state["user_id"]

st.title("⚙️ Configurações")
settings = sm.get_settings(user_id)

# ---------------------------------------------------------------------------
# Helper to display editable list
# ---------------------------------------------------------------------------

def editable_list(title: str, items: list[str], add_callback, rename_callback, remove_callback, add_key_prefix: str):
    st.write(f"### {title}")
    cols = st.columns([4, 1])
    new_val = cols[0].text_input("", key=f"{add_key_prefix}_new")
    if cols[1].button("➕", key=f"{add_key_prefix}_add"):
        add_callback(user_id, new_val)
        st.rerun()

    st.divider()
    for item in items:
        col1, col2, col3 = st.columns([4, 1, 1])
        new_name = col1.text_input("", value=item, key=f"{add_key_prefix}_{item}")
        if col2.button("💾", key=f"save_{add_key_prefix}_{item}") and new_name != item:
            remove_callback(user_id, item)
            add_callback(user_id, new_name)
            st.rerun()
        if col3.button("✖️", key=f"del_{add_key_prefix}_{item}"):
            remove_callback(user_id, item)
            st.rerun()

# ---------------------------------------------------------------------------
# Categorias
# ---------------------------------------------------------------------------
with st.expander("🗂️ Categorias", expanded=False):
    editable_list(
        title="Categorias",
        items=sm.get_categories(user_id),
        add_callback=sm.add_category,
        rename_callback=None,
        remove_callback=sm.remove_category,
        add_key_prefix="cat",
    )

# ---------------------------------------------------------------------------
# Contas
# ---------------------------------------------------------------------------
with st.expander("💳 Contas / Cartões", expanded=False):
    editable_list(
        title="Contas / Cartões",
        items=sm.get_accounts(user_id),
        add_callback=sm.add_account,
        rename_callback=None,
        remove_callback=sm.remove_account,
        add_key_prefix="acc",
    )

# ---------------------------------------------------------------------------
# Orçamento mensal
# ---------------------------------------------------------------------------
with st.expander("📅 Orçamento mensal", expanded=False):
    current_budget = sm.get_monthly_budget(user_id) or 0.0
    budget_val = st.number_input(
        "Limite de gasto mensal (BRL)",
        min_value=0.0,
        step=50.0,
        value=float(current_budget),
        format="%.2f",
    )
    if st.button("Salvar orçamento"):
        sm.set_monthly_budget(user_id, budget_val)
        st.success("Orçamento atualizado!")
