# services/auth.py
"""Módulo de autenticação simples para o Travel Expenses App.

⚠️ Segurança básica – usa SHA‑256 + salt para prototipagem. Para produção,
substitua por `bcrypt` ou `argon2`.
"""

from __future__ import annotations

import hashlib
import os
import sqlite3
from pathlib import Path
from typing import List

# Usamos o mesmo arquivo SQLite principal
DB_PATH = Path("expenses.db")

# Salt global (idealmente variável de ambiente)
_SALT = os.getenv("APP_AUTH_SALT", "\u2744auth_salt")

# ---------------------------------------------------------------------------
# Inicialização do schema
# ---------------------------------------------------------------------------

def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Cria a tabela `users` se ainda não existir."""
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            """
        )

# Garantir que o schema exista quando o módulo é importado
init_db()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _hash(pwd: str) -> str:
    return hashlib.sha256((pwd + _SALT).encode()).hexdigest()

# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def create_user(email: str, password: str) -> None:
    """Cria um usuário novo. Lança ValueError se já existir."""
    email = email.strip().lower()
    if not email or not password:
        raise ValueError("E‑mail e senha são obrigatórios.")

    try:
        with _connect() as conn:
            conn.execute(
                "INSERT INTO users (email, password_hash) VALUES (?, ?)",
                (email, _hash(password)),
            )
    except sqlite3.IntegrityError:
        raise ValueError("E‑mail já cadastrado.") from None


def verify_user(email: str, password: str) -> bool:
    """Retorna True se as credenciais forem válidas."""
    email = email.strip().lower()
    if not email or not password:
        return False

    with _connect() as conn:
        cur = conn.execute("SELECT password_hash FROM users WHERE email = ?", (email,))
        row = cur.fetchone()
        if row is None:
            return False
        return row["password_hash"] == _hash(password)


def list_users() -> List[str]:
    """Retorna lista de e‑mails cadastrados (debug)."""
    with _connect() as conn:
        cur = conn.execute("SELECT email FROM users ORDER BY id")
        return [r["email"] for r in cur.fetchall()]
