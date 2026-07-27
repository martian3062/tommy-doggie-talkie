from litestar import Litestar, get
from litestar.config.cors import CORSConfig
from litestar.di import Provide
from litestar.openapi import OpenAPIConfig

from app.api.deps import provide_owner_id
from app.api.routes.analysis_jobs import analysis_jobs_router
from app.api.routes.dogs import breeds_router, dogs_router
from app.core.config import get_settings
from app.core.database import get_session, init_db


settings = get_settings()


@get("/health", sync_to_thread=False)
def health() -> dict[str, str | bool]:
    return {
        "status": "ok",
        "app_env": settings.app_env,
        "supabase_enabled": settings.supabase_enabled,
        "sqlite_fallback": settings.database_url.startswith("sqlite"),
    }


app = Litestar(
    route_handlers=[health, dogs_router, breeds_router, analysis_jobs_router],
    dependencies={
        "session": Provide(get_session),
        "owner_id": Provide(provide_owner_id, sync_to_thread=False),
    },
    cors_config=CORSConfig(
        allow_origins=settings.parsed_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    ),
    on_startup=[init_db],
    openapi_config=OpenAPIConfig(
        title="Dog Translator API",
        description="Multimodal dog behavior interpretation API with Supabase storage and SQLite fallback.",
        version="0.1.0",
        path="/docs",
    ),
)
