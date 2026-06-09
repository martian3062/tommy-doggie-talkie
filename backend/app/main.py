from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import analysis_jobs, dogs
from app.core.config import get_settings
from app.core.database import init_db


settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Dog Translator API",
    description="Multimodal dog behavior interpretation API with Supabase storage and SQLite fallback.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.parsed_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str | bool]:
    return {
        "status": "ok",
        "app_env": settings.app_env,
        "supabase_enabled": settings.supabase_enabled,
        "sqlite_fallback": settings.database_url.startswith("sqlite"),
    }


app.include_router(dogs.router, prefix="/api/v1")
app.include_router(analysis_jobs.router, prefix="/api/v1")
