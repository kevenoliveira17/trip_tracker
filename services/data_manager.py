"""Data access layer for the Travel Expenses app.

This module encapsulates all interactions with the SQLite database so that the
Streamlit UI remains completely agnostic of the storage layer. If you ever need
to migrate to Postgres or Google Sheets, only this file should require changes.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, date as date_type
from pathlib import Path
from typing import Any, List, Optional

import pandas as pd

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DB_PATH = Path("expenses.db")  # Persisted in the project root; substitute as needed.

# ---------------------------------------------------------------------------
# Low‑level helpers
# ---------------------------------------------------------------------------

def _connect() -> sqlite3.Connection:
    """Return a SQLite connection with sensible defaults."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    # Enable type detection and return rows as dict‑like objects
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db() -> None:
    """Create the *expenses* table if it doesn't exist."""
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                date TEXT NOT NULL,             -- ISO‑8601 string (YYYY‑MM‑DD)
                amount REAL NOT NULL,
                currency TEXT NOT NULL DEFAULT 'BRL',
                category TEXT,
                description TEXT,
                account TEXT,
                receipt_path TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            """
        )


# ---------------------------------------------------------------------------
# CRUD operations
# ---------------------------------------------------------------------------

def add_expense(
    *,
    user_id: str,
    date: date_type | str,
    amount: float,
    category: str,
    description: str,
    account: str,
    receipt_path: Optional[str] = None,
    currency: str = "BRL",
) -> int:
    """Insert a new expense and return the newly created *id*."""

    if isinstance(date, datetime):
        date = date.date()
    if isinstance(date, date_type):
        date = date.isoformat()

    with _connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO expenses (
                user_id, date, amount, currency, category, description, account, receipt_path
            ) VALUES (?,?,?,?,?,?,?,?);
            """,
            (
                user_id,
                date,
                float(amount),
                currency,
                category,
                description,
                account,
                receipt_path,
            ),
        )
        return cur.lastrowid  # type: ignore[return‑value]


def list_expenses(
    *,
    user_id: str,
    start_date: date_type | str | None = None,
    end_date: date_type | str | None = None,
    category: Optional[str] = None,
    account: Optional[str] = None,
    as_dataframe: bool = True,
) -> pd.DataFrame | List[dict[str, Any]]:
    """Fetch expenses filtered by the given parameters.

    If **as_dataframe** is *True* (default) returns a pandas *DataFrame*; otherwise
    a list of dicts.
    """

    sql = ["SELECT * FROM expenses WHERE user_id = ?"]
    params: List[Any] = [user_id]

    if start_date is not None:
        if isinstance(start_date, datetime):
            start_date = start_date.date()
        if isinstance(start_date, date_type):
            start_date = start_date.isoformat()
        sql.append("AND date >= ?")
        params.append(start_date)

    if end_date is not None:
        if isinstance(end_date, datetime):
            end_date = end_date.date()
        if isinstance(end_date, date_type):
            end_date = end_date.isoformat()
        sql.append("AND date <= ?")
        params.append(end_date)

    if category is not None:
        sql.append("AND category = ?")
        params.append(category)

    if account is not None:
        sql.append("AND account = ?")
        params.append(account)

    sql.append("ORDER BY date DESC, id DESC")

    with _connect() as conn:
        cur = conn.execute(" ".join(sql), params)
        rows = cur.fetchall()

    if as_dataframe:
        return pd.DataFrame(rows, columns=rows[0].keys() if rows else None)
    return [dict(r) for r in rows]


def delete_expense(*, expense_id: int, user_id: str) -> None:
    """Delete an expense that belongs to *user_id*."""
    with _connect() as conn:
        conn.execute("DELETE FROM expenses WHERE id = ? AND user_id = ?", (expense_id, user_id))


def update_expense(
    *,
    expense_id: int,
    user_id: str,
    **fields: Any,
) -> None:
    """Patch only the specified *fields* of an existing expense.

    Example::
        update_expense(
            expense_id=5,
            user_id="keven",
            amount=450.75,
            description="Hotel + jantar",
        )
    """
    if not fields:
        return  # Nothing to update

    allowed = {
        "date",
        "amount",
        "currency",
        "category",
        "description",
        "account",
        "receipt_path",
    }
    unknown = set(fields) - allowed
    if unknown:
        raise ValueError(f"Unknown field(s): {', '.join(unknown)}")

    assignments = ", ".join(f"{k} = ?" for k in fields)
    params = list(fields.values()) + [datetime.utcnow().isoformat(), expense_id, user_id]

    with _connect() as conn:
        conn.execute(
            f"UPDATE expenses SET {assignments}, updated_at = ? WHERE id = ? AND user_id = ?",
            params,
        )


# ---------------------------------------------------------------------------
# Aggregations & helpers (optional but handy)
# ---------------------------------------------------------------------------

def total_spent(
    *,
    user_id: str,
    start_date: date_type | str | None = None,
    end_date: date_type | str | None = None,
) -> float:
    """Return the sum of *amount* over the filtered period."""
    sql = ["SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE user_id = ?"]
    params: List[Any] = [user_id]

    if start_date is not None:
        if isinstance(start_date, datetime):
            start_date = start_date.date()
        if isinstance(start_date, date_type):
            start_date = start_date.isoformat()
        sql.append("AND date >= ?")
        params.append(start_date)

    if end_date is not None:
        if isinstance(end_date, datetime):
            end_date = end_date.date()
        if isinstance(end_date, date_type):
            end_date = end_date.isoformat()
        sql.append("AND date <= ?")
        params.append(end_date)

    with _connect() as conn:
        cur = conn.execute(" ".join(sql), params)
        (total,) = cur.fetchone()
    return float(total)


# ---------------------------------------------------------------------------
# Ensure the database exists when the module is first imported
# ---------------------------------------------------------------------------
init_db()
