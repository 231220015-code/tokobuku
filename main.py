from contextlib import asynccontextmanager

from fastapi import FastAPI

import database as db
from routes import resource


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.init_db()
    yield


app = FastAPI(title="Toko Buku API", lifespan=lifespan)
app.include_router(resource.router)
