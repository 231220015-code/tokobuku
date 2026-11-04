from typing import Literal

from pydantic import BaseModel, Field


class BookCreate(BaseModel):
    judul: str = Field(min_length=1, max_length=200)
    penulis: str = Field(min_length=1, max_length=100)
    kategori: str = Field(min_length=1, max_length=50)
    harga: float = Field(gt=0)
    stok: int = Field(ge=0)


class Book(BaseModel):
    # Tanpa batas stok >= 0 agar demo tanpa lock bisa menampilkan stok negatif.
    id: int
    judul: str
    penulis: str
    kategori: str
    harga: float
    stok: int


class TransactionCreate(BaseModel):
    item_id: int = Field(ge=1, description="ID buku yang dibeli")
    qty: int = Field(ge=1)


class Transaction(BaseModel):
    id: int
    book_id: int
    qty: int
    status: Literal["pending", "processing", "completed", "failed"]
    created_at: str


class TransactionAccepted(BaseModel):
    id: int
    status: Literal["pending"]
    message: str
