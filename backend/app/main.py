"""
ANVESHAK — FastAPI Application
Main entry point and application setup.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import candidates, observations, pipeline, sources, websocket
from app.core.config import get_settings
from app.core.logging import get_logger, setup_logging
from app.models.database import check_db_health, close_db, init_db
from app.queue.redis_client import check_redis_health, close_redis_client

# Initialize logging early
setup_logging(get_settings().log_level)
logger = get_logger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management."""
    logger.info("application_startup")
    
    # Initialize DB (creates tables if they don't exist)
    await init_db()
    
    # Load sources into DB
    from app.services.source_service import SourceService
    from app.models.database import get_session_factory
    
    async with get_session_factory()() as session:
        service = SourceService(session)
        await service.initialize_sources()
        
    yield
    
    logger.info("application_shutdown")
    await close_db()
    await close_redis_client()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    
    app = FastAPI(
        title="ANVESHAK Pipeline API",
        description="Autonomous Real-Time Astronomical Signal Detection API",
        version="1.0.0",
        lifespan=lifespan,
    )

    # CORS Configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include Routers
    app.include_router(sources.router, prefix="/api/sources", tags=["Sources"])
    app.include_router(observations.router, prefix="/api/observations", tags=["Observations"])
    app.include_router(candidates.router, prefix="/api/candidates", tags=["Candidates"])
    app.include_router(pipeline.router, prefix="/api/pipeline", tags=["Pipeline"])
    app.include_router(websocket.router, tags=["WebSocket"])

    @app.get("/api/health", tags=["System"])
    async def health_check():
        """System health check endpoint."""
        db_ok = await check_db_health()
        redis_ok = await check_redis_health()
        
        status = "healthy" if db_ok and redis_ok else "unhealthy"
        
        return {
            "status": status,
            "database": "connected" if db_ok else "unreachable",
            "redis": "connected" if redis_ok else "unreachable",
            "mode": settings.data_mode
        }

    return app

app = create_app()
