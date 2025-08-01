# services/settings_manager.py
"""Gerencia configurações do usuário (categorias, contas, orçamento)."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import List, Optional

DB_PATH = Path("expenses.db")

DEFAULT_CATEGORIES = [
    "Alimentação",
    "Transporte",
    "Hospedagem",
    "Lazer",
    "Compras",
    "Outros",
]

DEFAULT_ACCOUNTS: list[str] = []

# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id TEXT PRIMARY KEY,
                categories TEXT,          -- JSON array
                accounts TEXT,            -- JSON array
                monthly_budget REAL
            );
            """
        )

init_db()

# ---------------------------------------------------------------------------
# Internal util
# ---------------------------------------------------------------------------

def _ensure_row(user_id: str) -> None:
    """Cria linha default se não existir."""
    with _connect() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO user_settings (user_id, categories, accounts, monthly_budget) VALUES (?,?,?,?)",
            (
                user_id,
                json.dumps(DEFAULT_CATEGORIES),
                json.dumps(DEFAULT_ACCOUNTS),
                None,
            ),
        )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_settings(user_id: str) -> dict:
    _ensure_row(user_id)
    with _connect() as conn:
        cur = conn.execute("SELECT * FROM user_settings WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
    return {
        "categories": json.loads(row["categories"]),
        "accounts": json.loads(row["accounts"]),
        "monthly_budget": row["monthly_budget"],
    }


def add_category(user_id: str, category: str) -> None:
    category = category.strip()
    if not category:
        return
    settings = get_settings(user_id)
    if category in settings["categories"]:
        return
    settings["categories"].append(category)
    _update_field(user_id, "categories", settings["categories"])


def remove_category(user_id: str, category: str) -> None:
    settings = get_settings(user_id)
    if category in settings["categories"]:
        settings["categories"].remove(category)
        _update_field(user_id, "categories", settings["categories"])


def add_account(user_id: str, account: str) -> None:
    account = account.strip()
    if not account:
        return
    settings = get_settings(user_id)
    if account in settings["accounts"]:
        return
    settings["accounts"].append(account)
    _update_field(user_id, "accounts", settings["accounts"])


def remove_account(user_id: str, account: str) -> None:
    settings = get_settings(user_id)
    if account in settings["accounts"]:
        settings["accounts"].remove(account)
        _update_field(user_id, "accounts", settings["accounts"])


def set_monthly_budget(user_id: str, budget: Optional[float]) -> None:
    with _connect() as conn:
        conn.execute("UPDATE user_settings SET monthly_budget = ? WHERE user_id = ?", (budget, user_id))


def _update_field(user_id: str, field: str, value: List[str]) -> None:
    with _connect() as conn:
        conn.execute(
            f"UPDATE user_settings SET {field} = ? WHERE user_id = ?",
            (json.dumps(value), user_id),
        )


def get_categories(user_id: str) -> list[str]:
    return get_settings(user_id)["categories"]


def get_accounts(user_id: str) -> list[str]:
    return get_settings(user_id)["accounts"]


def get_monthly_budget(user_id: str) -> Optional[float]:
    return get_settings(user_id)["monthly_budget"]
