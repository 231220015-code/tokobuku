from fastapi import APIRouter, HTTPException, Query, status

import database as db
from models import Book, BookCreate

router = APIRouter(prefix="/books", tags=["Buku"])


async def _get_or_404(book_id: int) -> dict:
    book = await db.fetch_one("SELECT * FROM books WHERE id = ?", (book_id,))
    if book is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Buku tidak ditemukan")
    return book


@router.get("", response_model=list[Book])
async def list_books(skip: int = Query(0, ge=0), limit: int = Query(10, ge=1, le=100)):
    return await db.fetch_all("SELECT * FROM books ORDER BY id LIMIT ? OFFSET ?", (limit, skip))


@router.get("/{book_id}", response_model=Book)
async def get_book(book_id: int):
    return await _get_or_404(book_id)


@router.post("", response_model=Book, status_code=status.HTTP_201_CREATED)
async def create_book(data: BookCreate):
    new_id, _ = await db.execute(
        "INSERT INTO books (judul, penulis, kategori, harga, stok) VALUES (?, ?, ?, ?, ?)",
        (data.judul, data.penulis, data.kategori, data.harga, data.stok),
    )
    return await _get_or_404(new_id)


@router.put("/{book_id}", response_model=Book)
async def update_book(book_id: int, data: BookCreate):
    await _get_or_404(book_id)
    await db.execute(
        "UPDATE books SET judul = ?, penulis = ?, kategori = ?, harga = ?, stok = ? WHERE id = ?",
        (data.judul, data.penulis, data.kategori, data.harga, data.stok, book_id),
    )
    return await _get_or_404(book_id)


@router.delete("/{book_id}", status_code=status.HTTP_200_OK)
async def delete_book(book_id: int):
    await _get_or_404(book_id)
    await db.execute("DELETE FROM books WHERE id = ?", (book_id,))
    return {"message": "Buku dihapus permanen", "id": book_id}
