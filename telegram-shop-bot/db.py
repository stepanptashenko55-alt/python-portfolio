"""SQLite storage for carts and orders."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "shop.db"


def connect() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


def init() -> None:
    with connect() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS cart (
                user_id INTEGER, product_id TEXT, qty INTEGER,
                PRIMARY KEY (user_id, product_id)
            );
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER, name TEXT, phone TEXT, total REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        """)


def add_to_cart(user_id: int, product_id: str) -> None:
    with connect() as conn:
        conn.execute("""
            INSERT INTO cart (user_id, product_id, qty) VALUES (?, ?, 1)
            ON CONFLICT(user_id, product_id) DO UPDATE SET qty = qty + 1
        """, (user_id, product_id))


def get_cart(user_id: int) -> list[tuple[str, int]]:
    with connect() as conn:
        return conn.execute("SELECT product_id, qty FROM cart WHERE user_id = ?", (user_id,)).fetchall()


def clear_cart(user_id: int) -> None:
    with connect() as conn:
        conn.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))


def create_order(user_id: int, name: str, phone: str, total: float) -> int:
    with connect() as conn:
        cur = conn.execute("INSERT INTO orders (user_id, name, phone, total) VALUES (?, ?, ?, ?)",
                           (user_id, name, phone, total))
        return cur.lastrowid


def list_orders(limit: int = 10) -> list[tuple]:
    with connect() as conn:
        return conn.execute("SELECT id, name, phone, total, created_at FROM orders ORDER BY id DESC LIMIT ?",
                            (limit,)).fetchall()
