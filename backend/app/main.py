from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .database import engine, Base
from .routers import jobs
from .routers import sessions


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Interview Copilot API",
        version="1.0.0",
        docs_url=f"{settings.api_prefix}/docs",
        redoc_url=f"{settings.api_prefix}/redoc",
        openapi_url=f"{settings.api_prefix}/openapi.json",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(jobs.router, prefix=settings.api_prefix)
    app.include_router(sessions.router)

    @app.get("/health", tags=["health"])
    def health():
        return {"status": "healthy", "environment": settings.environment}

    return app


app = create_app()
