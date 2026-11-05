import os

from locust import HttpUser, constant, task

# Total request per skenario; run dihentikan begitu semua slot terpakai.
MAX_REQUESTS = int(os.environ.get("MAX_REQUESTS", "100"))
slot_terpakai = 0


def ambil_slot(environment) -> bool:
    """Reservasi satu slot sebelum request dikirim agar total tepat MAX_REQUESTS."""
    global slot_terpakai
    if slot_terpakai >= MAX_REQUESTS:
        environment.runner.quit()
        return False
    slot_terpakai += 1
    return True


class ReadUser(HttpUser):
    """Skenario Read: GET /books, 100 request, 20 user."""

    wait_time = constant(0)

    @task
    def list_books(self):
        if ambil_slot(self.environment):
            self.client.get("/books?skip=0&limit=10", name="GET /books")


class WriteUser(HttpUser):
    """Skenario Write: POST /transactions, 50 request, 10 user."""

    wait_time = constant(0)

    @task
    def create_transaction(self):
        if ambil_slot(self.environment):
            self.client.post(
                "/transactions", json={"item_id": 8, "qty": 1}, name="POST /transactions"
            )
