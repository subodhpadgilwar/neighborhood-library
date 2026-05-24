from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.seeder import seed_default_admin
from app.database import AsyncSessionLocal


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncSessionLocal() as db:
        await seed_default_admin(db)
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(api_router, prefix="/api/v1")
