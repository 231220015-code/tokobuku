import asyncio

import database as db

BUKU = [
    ("Laskar Pelangi", "Andrea Hirata", "Novel", 89000, 40),
    ("Bumi Manusia", "Pramoedya Ananta Toer", "Novel", 120000, 25),
    ("Filosofi Teras", "Henry Manampiring", "Pengembangan Diri", 98000, 30),
    ("Atomic Habits", "James Clear", "Pengembangan Diri", 108000, 35),
    ("Sapiens", "Yuval Noah Harari", "Sejarah", 135000, 20),
    ("Clean Code", "Robert C. Martin", "Komputer", 295000, 12),
    ("Algoritma dan Pemrograman", "Rinaldi Munir", "Komputer", 150000, 18),
    ("Dilan 1990", "Pidi Baiq", "Novel", 79000, 100000),
    ("Negeri 5 Menara", "Ahmad Fuadi", "Novel", 85000, 28),
    ("Cantik Itu Luka", "Eka Kurniawan", "Novel", 110000, 15),
    ("Rich Dad Poor Dad", "Robert Kiyosaki", "Ekonomi", 95000, 22),
    ("Pemrograman Python", "Abdul Kadir", "Komputer", 130000, 16),
]


async def main() -> None:
    await db.init_db()
    await db.execute("DELETE FROM transactions")
    await db.execute("DELETE FROM books")
    await db.execute("DELETE FROM sqlite_sequence WHERE name IN ('books', 'transactions')")
    for judul, penulis, kategori, harga, stok in BUKU:
        await db.execute(
            "INSERT INTO books (judul, penulis, kategori, harga, stok) VALUES (?, ?, ?, ?, ?)",
            (judul, penulis, kategori, harga, stok),
        )
    print(f"Seed selesai: {len(BUKU)} buku dimasukkan.")


if __name__ == "__main__":
    asyncio.run(main())
