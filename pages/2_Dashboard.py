
"""Dashboard analítico de gastos — Travel Expenses App."""

from __future__ import annotations

from datetime import date, datetime, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

from services import data_manager as dm
from services import settings_manager as sm

st.set_page_config(page_title="Dashboard de Gastos", page_icon="📊", layout="wide")

# ---------------------------------------------------------------------------
# Autenticação
# ---------------------------------------------------------------------------
if "user_id" not in st.session_state:
    st.warning("Faça login para visualizar o dashboard.")
    st.stop()

user_id = st.session_state["user_id"]

# ---------------------------------------------------------------------------
# Carregar dados
# ---------------------------------------------------------------------------
full_df = dm.list_expenses(user_id=user_id, as_dataframe=True)
if full_df.empty:
    st.info("Nenhum gasto cadastrado ainda. Adicione gastos na página Registrar Gasto para visualizar o dashboard.")
    st.stop()

full_df["date"] = pd.to_datetime(full_df["date"])
full_df.sort_values("date", inplace=True)

# ---------------------------------------------------------------------------
# Sidebar — seleção de modo
# ---------------------------------------------------------------------------
st.sidebar.header("🔎 Filtros")

mode = st.sidebar.radio(
    "Período",
    options=["Todos os gastos", "Mês atual"],
    index=0,
)

min_date = full_df["date"].min().date()
max_date = full_df["date"].max().date()

if mode == "Mês atual":
    today = date.today()
    start_date = today.replace(day=1)
    end_date = today
    st.sidebar.info(f"Mostrando de {start_date.strftime('%d/%m/%Y')} até hoje.")
else:
    # Custom range (default todo o histórico)
    start_date, end_date = st.sidebar.date_input(
        "Selecione o intervalo",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

# ---------------------------------------------------------------------------
# Outros filtros (categoria / conta)
# ---------------------------------------------------------------------------
categories = sorted(full_df["category"].dropna().unique())
selected_categories = st.sidebar.multiselect("Categoria", categories, default=categories)

accounts = sorted(full_df["account"].dropna().unique())
selected_accounts = st.sidebar.multiselect("Conta", accounts, default=accounts)

# ---------------------------------------------------------------------------
# Aplicar filtros
# ---------------------------------------------------------------------------
filtered_df = full_df[
    (full_df["date"].dt.date >= start_date)
    & (full_df["date"].dt.date <= end_date)
    & (full_df["category"].isin(selected_categories))
    & (full_df["account"].isin(selected_accounts))
]

if filtered_df.empty:
    st.warning("Nenhum gasto encontrado para os filtros selecionados.")
    st.stop()

# ---------------------------------------------------------------------------
# KPIs principais
# ---------------------------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)

total_period = filtered_df["amount"].sum()
col1.metric("Total no período", f"R$ {total_period:,.2f}")

col2.metric("Transações", f"{len(filtered_df)}")

days = (end_date - start_date).days + 1
avg_day = total_period / days if days else 0
col3.metric("Média diária", f"R$ {avg_day:,.2f}")

# ---------------------------------------------------------------------------
# Orçamento mensal
# ---------------------------------------------------------------------------
budget = sm.get_monthly_budget(user_id)

if budget and mode == "Mês atual":
    percent = total_period / budget if budget else 0
    remaining = budget - total_period
    col4.metric("Orçamento restante", f"R$ {remaining:,.2f}", f"{percent*100:.1f}% usado")

    if percent >= 1:
        st.error("🚨 Você ultrapassou o orçamento mensal!")
    elif percent >= 0.8:
        st.warning("⚠️ Você já consumiu mais de 80 % do orçamento.")
else:
    col4.metric("Orçamento restante", "—", "—")

st.markdown("---")

# ---------------------------------------------------------------------------
# Gráficos
# ---------------------------------------------------------------------------
fig_daily = px.line(
    filtered_df.groupby(filtered_df["date"].dt.date)["amount"].sum().reset_index(name="amount"),
    x="date",
    y="amount",
    markers=True,
    title="Evolução diária de gastos",
    labels={"date": "Data", "amount": "Valor (BRL)"},
)
fig_daily.update_layout(showlegend=False)

fig_cat = px.pie(
    filtered_df.groupby("category")["amount"].sum().reset_index(),
    names="category",
    values="amount",
    title="Distribuição por categoria",
)

fig_acc = px.bar(
    filtered_df.groupby("account")["amount"].sum().reset_index(),
    x="account",
    y="amount",
    title="Gastos por conta/cartão",
    labels={"account": "Conta", "amount": "Valor (BRL)"},
)

st.plotly_chart(fig_daily, use_container_width=True)
st.plotly_chart(fig_cat, use_container_width=True)
st.plotly_chart(fig_acc, use_container_width=True)

st.markdown("---")

# ---------------------------------------------------------------------------
# Tabela detalhada
# ---------------------------------------------------------------------------
st.subheader("Gastos detalhados")

show_receipts = st.checkbox("Mostrar coluna de recibo", value=False)
cols = ["date", "amount", "category", "description", "account"]
if show_receipts:
    cols.append("receipt_path")

table_df = filtered_df[cols].rename(columns={
    "date": "Data",
    "amount": "Valor (BRL)",
    "category": "Categoria",
    "description": "Descrição",
    "account": "Conta",
    "receipt_path": "Recibo",
})

st.dataframe(table_df, use_container_width=True)
