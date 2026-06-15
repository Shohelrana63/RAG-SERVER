from contextlib import asynccontextmanager

from beanie import init_beanie
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.auth import router as auth_router
from app.core.config import settings
from app.models.user import User


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_beanie(
        connection_string=settings.mongodb_uri,
        document_models=[User],
    )
    yield


app = FastAPI(title="AI PDF Knowledge Assistant API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.client_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1")


@app.get("/health")
def health():
    return {"success": True, "data": {"status": "ok"}}


@app.get("/api/v1/health")
def health_v1():
    return {"success": True, "data": {"status": "ok"}}
