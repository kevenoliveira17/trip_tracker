
"""Página Streamlit para registrar um novo gasto (integrada às Configurações)."""

from __future__ import annotations

from datetime import date as date_type, datetime
from pathlib import Path
from typing import Optional

import streamlit as st

from services import data_manager as dm
from services import settings_manager as sm

# ---------------------------------------------------------------------------
# Config da página
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Registrar Gasto", page_icon="📥", layout="centered")

# ---------------------------------------------------------------------------
# Autenticação
# ---------------------------------------------------------------------------
if "user_id" not in st.session_state:
    st.warning("Faça login para registrar gastos.")
    st.stop()

user_id = st.session_state["user_id"]

# ---------------------------------------------------------------------------
# Banco / uploads
# ---------------------------------------------------------------------------
dm.init_db()
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


def _save_receipt(uploaded_file) -> Optional[str]:
    if uploaded_file is None:
        return None
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    filename = f"receipt_{timestamp}_{uploaded_file.name}"
    path = UPLOAD_DIR / filename
    with open(path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return str(path)

# ---------------------------------------------------------------------------
# Carrega listas personalizadas do usuário
# ---------------------------------------------------------------------------
categories = sm.get_categories(user_id)
if not categories:
    categories = ["Outros"]

accounts = sm.get_accounts(user_id)
if not accounts:
    accounts = ["Dinheiro"]

# ---------------------------------------------------------------------------
# Formulário
# ---------------------------------------------------------------------------
st.title("Registrar novo gasto")
with st.form("expense_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    date_input: date_type = col1.date_input("Data", value=date_type.today())
    amount_input: float = col2.number_input("Valor (BRL)", min_value=0.0, step=0.01, format="%.2f")

    category_input: str = st.selectbox("Categoria", categories)
    description_input: str = st.text_area("Descrição", placeholder="Ex.: Jantar em Palermo")
    account_input: str = st.selectbox("Conta / Cartão", accounts)

    st.caption("Quer adicionar novas categorias ou contas? Vá em ⚙️ Configurações no menu.")

    receipt_file = st.file_uploader("Comprovante (opcional)", type=["jpg", "jpeg", "png", "pdf"])

    submitted = st.form_submit_button("Adicionar Gasto")

if submitted:
    receipt_path = _save_receipt(receipt_file)

    dm.add_expense(
        user_id=user_id,
        date=date_input,
        amount=amount_input,
        category=category_input,
        description=description_input,
        account=account_input,
        receipt_path=receipt_path,
    )
    st.success("Gasto registrado com sucesso!")
    st.balloons()
    st.rerun()

# ---------------------------------------------------------------------------
# Últimos gastos
# ---------------------------------------------------------------------------
st.markdown("---")
st.subheader("Últimos gastos cadastrados")

recent_df = dm.list_expenses(user_id=user_id, as_dataframe=True)

if recent_df.empty:
    st.info("Nenhum gasto registrado ainda.")
else:
    st.dataframe(
        recent_df[["date", "amount", "category", "description", "account"]]
        .rename(columns={
            "date": "Data",
            "amount": "Valor (BRL)",
            "category": "Categoria",
            "description": "Descrição",
            "account": "Conta",
        }),
        use_container_width=True,
    )
    st.caption(f"**Total gasto:** R$ {dm.total_spent(user_id=user_id):,.2f}")
