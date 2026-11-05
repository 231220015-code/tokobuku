import asyncio

import httpx

BASE = "http://127.0.0.1:8000"


async def main() -> None:
    payload = {"item_id": 1, "qty": 1}
    async with httpx.AsyncClient() as client:
        # gather mengirim kedua request pada saat yang sama.
        res1, res2 = await asyncio.gather(
            client.post(f"{BASE}/transactions", json=payload),
            client.post(f"{BASE}/transactions", json=payload),
        )
        print("Respon Request 1:", res1.status_code, res1.json())
        print("Respon Request 2:", res2.status_code, res2.json())
        buku = (await client.get(f"{BASE}/books/1")).json()
        print("Stok akhir buku 1:", buku["stok"])


if __name__ == "__main__":
    asyncio.run(main())
