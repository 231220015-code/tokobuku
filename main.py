from contextlib import asynccontextmanager

from fastapi import FastAPI

import database as db
from routes import resource, transaction


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.init_db()
    yield


app = FastAPI(title="Toko Buku API", lifespan=lifespan)
app.include_router(resource.router)
app.include_router(transaction.router)
