import asyncio
import os
from contextlib import asynccontextmanager

import aiosqlite

DB_PATH = os.environ.get("TOKOBUKU_DB", os.path.join(os.path.dirname(__file__), "tokobuku.db"))

# Tanpa CHECK (stok >= 0): versi tanpa lock harus bisa menghasilkan stok negatif
# agar overselling terlihat. Validasi stok >= 0 dilakukan oleh model Pydantic.
CREATE_BOOKS_TABLE = """
CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    judul TEXT NOT NULL,
    penulis TEXT NOT NULL,
    kategori TEXT NOT NULL,
    harga REAL NOT NULL,
    stok INTEGER NOT NULL
)
"""

CREATE_TRANSACTIONS_TABLE = """
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL REFERENCES books(id),
    qty INTEGER NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
)
"""

# Satu gembok per proses. Berlaku untuk semua coroutine di event loop yang sama.
stok_lock = asyncio.Lock()

# USE_LOCK=0 mengaktifkan versi tanpa lock untuk Tahap 1 pengujian race condition.
USE_LOCK = os.environ.get("USE_LOCK", "1") != "0"


@asynccontextmanager
async def connect():
    # Koneksi per operasi: tiap worker Uvicorn punya event loop sendiri,
    # dan mode WAL mengizinkan banyak pembaca bersamaan.
    async with aiosqlite.connect(DB_PATH, timeout=30) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("PRAGMA busy_timeout=30000")
        yield db


async def init_db() -> None:
    async with connect() as db:
        await db.execute(CREATE_BOOKS_TABLE)
        await db.execute(CREATE_TRANSACTIONS_TABLE)
        await db.commit()


async def fetch_all(query: str, params: tuple = ()) -> list[dict]:
    async with connect() as db:
        async with db.execute(query, params) as cursor:
            return [dict(row) for row in await cursor.fetchall()]


async def fetch_one(query: str, params: tuple = ()) -> dict | None:
    async with connect() as db:
        async with db.execute(query, params) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def execute(query: str, params: tuple = ()) -> tuple[int, int]:
    """Jalankan satu perintah tulis. Mengembalikan (lastrowid, rowcount)."""
    async with connect() as db:
        cursor = await db.execute(query, params)
        await db.commit()
        return cursor.lastrowid, cursor.rowcount


async def get_stok(book_id: int) -> int | None:
    row = await fetch_one("SELECT stok FROM books WHERE id = ?", (book_id,))
    return row["stok"] if row else None


async def decrement_stok(book_id: int, qty: int) -> None:
    await execute("UPDATE books SET stok = stok - ? WHERE id = ?", (qty, book_id))


async def update_trx_status(trx_id: int, status: str) -> None:
    await execute("UPDATE transactions SET status = ? WHERE id = ?", (status, trx_id))


async def insert_transaction(book_id: int, qty: int, status: str) -> int:
    trx_id, _ = await execute(
        "INSERT INTO transactions (book_id, qty, status) VALUES (?, ?, ?)",
        (book_id, qty, status),
    )
    return trx_id


async def potong_stok_tanpa_lock(book_id: int, qty: int) -> bool:
    stok_terkini = await get_stok(book_id)
    # Jeda ini membuka jendela waktu: request lain sempat membaca stok yang sama.
    await asyncio.sleep(0.01)
    if stok_terkini is None or stok_terkini < qty:
        return False
    await decrement_stok(book_id, qty)
    return True


async def potong_stok_dengan_lock(book_id: int, qty: int) -> bool:
    # Critical section: baca, cek, dan kurangi stok berjalan satu per satu.
    # Coroutine lain menunggu di `async with` sampai blok ini selesai.
    async with stok_lock:
        stok_terkini = await get_stok(book_id)
        await asyncio.sleep(0.01)
        if stok_terkini is None or stok_terkini < qty:
            return False
        await decrement_stok(book_id, qty)
        return True


async def potong_stok(book_id: int, qty: int) -> bool:
    if USE_LOCK:
        return await potong_stok_dengan_lock(book_id, qty)
    return await potong_stok_tanpa_lock(book_id, qty)
