Video presentasi: https://youtu.be/39Rprb163L8

# Toko Buku API

Hafiz Saklinov, NIM 231220015.

REST API toko buku untuk UTS Komputasi Paralel dan Terdistribusi, dibangun dengan FastAPI, SQLite (aiosqlite), `BackgroundTasks`, dan `asyncio.Lock`.

Resource utama: `books`. Resource transaksi: `transactions` (pembelian buku).

## Instalasi

Python 3.10 atau lebih baru.

```bash
pip install -r requirements.txt
python seed.py
```

`seed.py` mengisi 12 buku. Buku id 8 sengaja berstok besar untuk benchmark tulis.

## Menjalankan

```bash
uvicorn main:app --port 8000
```

Swagger UI ada di http://127.0.0.1:8000/docs.

Untuk beberapa worker: `uvicorn main:app --port 8000 --workers 4`.

## Endpoint

| Method | Path | Fungsi |
|---|---|---|
| GET | /books?skip=0&limit=10 | Daftar buku |
| GET | /books/{id} | Detail buku |
| POST | /books | Tambah buku (201) |
| PUT | /books/{id} | Perbarui buku |
| DELETE | /books/{id} | Hapus permanen |
| POST | /transactions | Buat transaksi, langsung `pending` (202) |
| GET | /transactions?status=pending | Daftar transaksi, bisa difilter |
| GET | /transactions/{id} | Status transaksi terkini |

Status transaksi: `pending` -> `processing` -> `completed` atau `failed`.
Stok tidak cukup menghasilkan 409, buku tidak ada 404, input salah 422.

## Uji race condition

Atur stok buku 1 ke 1 lebih dulu, lalu jalankan server tanpa lock:

```bash
python -c "import sqlite3;c=sqlite3.connect('tokobuku.db');c.execute('update books set stok=1 where id=1');c.commit()"
USE_LOCK=0 uvicorn main:app --port 8000
python test_race.py
```

Server dengan lock (default):

```bash
uvicorn main:app --port 8000
python test_race.py
```

Pada Windows PowerShell, setel variabel dengan `$env:USE_LOCK="0"`.

## Uji beban

Jalankan server terlebih dahulu (1 worker atau 4 worker), lalu jalankan pengujian dengan Locust:

```bash
# Opsi 1: Mode Web UI (buka browser di http://127.0.0.1:8089)
locust -f locustfile.py --host http://127.0.0.1:8000

# Opsi 2: Mode Headless (terminal)
# 1. Skenario Read: GET /books (100 request, 20 users)
locust -f locustfile.py ReadUser --headless -u 20 -r 20 --host http://127.0.0.1:8000

# 2. Skenario Write: POST /transactions (50 request, 10 users)
# PowerShell:
$env:MAX_REQUESTS="50"; locust -f locustfile.py WriteUser --headless -u 10 -r 10 --host http://127.0.0.1:8000
# Bash / Linux:
MAX_REQUESTS=50 locust -f locustfile.py WriteUser --headless -u 10 -r 10 --host http://127.0.0.1:8000
```

## Catatan desain

- Kolom `stok` tidak memakai `CHECK (stok >= 0)`. Dengan CHECK, versi tanpa lock akan gagal di database dan overselling tidak terlihat. Validasi stok tidak negatif dilakukan lewat Pydantic pada input.
- `asyncio.Lock` hanya berlaku dalam satu proses. Dengan `--workers 4`, tiap worker punya lock sendiri, jadi dua request yang jatuh ke worker berbeda masih bisa melakukan overselling. Pengujian race condition dilakukan dengan 1 worker.
- Pemotongan stok terjadi saat `POST /transactions`, sebelum respons `pending` dikirim. Background task hanya mengubah status.

## Referensi

- FastAPI: https://fastapi.tiangolo.com/
- FastAPI Background Tasks: https://fastapi.tiangolo.com/tutorial/background-tasks/
- Python asyncio: https://docs.python.org/3/library/asyncio.html
- asyncio Lock: https://docs.python.org/3/library/asyncio-sync.html#asyncio.Lock
- aiosqlite: https://aiosqlite.omnilib.dev/
- SQLite WAL: https://www.sqlite.org/wal.html
- Uvicorn: https://www.uvicorn.org/deployment/
- Locust: https://docs.locust.io/
- Pydantic: https://docs.pydantic.dev/
