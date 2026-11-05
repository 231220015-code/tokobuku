import asyncio
from typing import Literal

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, status

import database as db
from models import Transaction, TransactionAccepted, TransactionCreate

router = APIRouter(prefix="/transactions", tags=["Transaksi"])


async def proses_transaksi_background(trx_id: int) -> None:
    """Pekerja internal, dijalankan FastAPI setelah respons terkirim (bukan endpoint HTTP)."""
    try:
        await db.update_trx_status(trx_id, "processing")
        # Simulasi pekerjaan I/O. await melepas event loop, jadi request lain
        # tetap dilayani selama 3 detik ini.
        await asyncio.sleep(3)
        await db.update_trx_status(trx_id, "completed")
    except Exception:
        await db.update_trx_status(trx_id, "failed")


@router.post("", response_model=TransactionAccepted, status_code=status.HTTP_202_ACCEPTED)
async def create_transaction(data: TransactionCreate, bg: BackgroundTasks):
    if await db.get_stok(data.item_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Buku tidak terdaftar")

    # Pemotongan stok dilindungi asyncio.Lock (lihat database.potong_stok).
    if not await db.potong_stok(data.item_id, data.qty):
        raise HTTPException(status.HTTP_409_CONFLICT, "Stok habis atau tidak mencukupi")

    trx_id = await db.insert_transaction(data.item_id, data.qty, "pending")
    # add_task menjadwalkan pekerjaan setelah respons dikirim, sehingga
    # klien langsung menerima status pending tanpa menunggu 3 detik.
    bg.add_task(proses_transaksi_background, trx_id)
    return {"id": trx_id, "status": "pending", "message": "Transaksi diproses"}


@router.get("", response_model=list[Transaction])
async def list_transactions(
    status_filter: Literal["pending", "processing", "completed", "failed"] | None = Query(
        None, alias="status"
    ),
):
    if status_filter:
        return await db.fetch_all(
            "SELECT * FROM transactions WHERE status = ? ORDER BY id", (status_filter,)
        )
    return await db.fetch_all("SELECT * FROM transactions ORDER BY id")


@router.get("/{trx_id}", response_model=Transaction)
async def get_transaction(trx_id: int):
    trx = await db.fetch_one("SELECT * FROM transactions WHERE id = ?", (trx_id,))
    if trx is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Transaksi tidak ditemukan")
    return trx
