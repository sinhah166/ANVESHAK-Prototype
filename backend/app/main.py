"""
ANVESHAK — FastAPI Application
Autonomous Exoplanet Data Analysis & Discovery Platform
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.logging import get_logger, setup_logging
from app.models.database import check_db_health, close_db, init_db

# Initialize logging early
setup_logging(get_settings().log_level)
logger = get_logger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management."""
    logger.info("application_startup", mode=get_settings().data_mode)

    # Initialize DB (creates tables if they don't exist)
    await init_db()

    # Ensure NASA Exoplanet Archive source exists
    from app.models.database import get_session_factory
    from app.services.ingestion import IngestionService

    try:
        async with get_session_factory()() as session:
            service = IngestionService(session)
            await service.ensure_source_exists()
    except Exception as e:
        logger.warning("source_init_failed", error=str(e))

    # Auto-ingest demo data if in demo mode and no data exists
    settings = get_settings()
    if settings.data_mode == "demo":
        try:
            from sqlalchemy import select, func
            from app.models.db_models import AstronomicalObject
            async with get_session_factory()() as session:
                count_result = await session.execute(
                    select(func.count()).select_from(AstronomicalObject)
                )
                obj_count = count_result.scalar() or 0
                if obj_count == 0:
                    logger.info("auto_ingesting_demo_data")
                    service = IngestionService(session)
                    await service.ingest_dataset(
                        table="pscomppars",
                        max_records=1500,
                    )
                    logger.info("demo_data_ingested")
        except Exception as e:
            logger.warning("demo_auto_ingest_failed", error=str(e))

    yield

    logger.info("application_shutdown")
    await close_db()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="ANVESHAK — Exoplanet Data Analysis Platform",
        description=(
            "Autonomous scientific data-analysis platform that collects publicly available "
            "astronomical/exoplanet datasets, performs machine-learning-driven analysis, "
            "identifies unusual/candidate objects, and provides scientists with an interactive "
            "data-analysis workbench."
        ),
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
    )

    # CORS Configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Import routers
    from app.api import datasets, objects, analysis, jobs

    # Register versioned API routes
    app.include_router(datasets.router, prefix="/api/v1/datasets", tags=["Datasets"])
    app.include_router(objects.router, prefix="/api/v1/objects", tags=["Objects"])
    app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["Analysis"])
    app.include_router(jobs.router, prefix="/api/v1", tags=["Jobs & Ingestion"])

    @app.get("/api/health", tags=["System"])
    async def health_check():
        """System health check endpoint."""
        db_ok = await check_db_health()
        return {
            "status": "healthy" if db_ok else "degraded",
            "database": "connected" if db_ok else "unreachable",
            "mode": settings.data_mode,
            "version": "1.0.0",
        }

    @app.get("/api/v1/config/mode", tags=["System"])
    async def get_mode():
        """Get current data mode."""
        return {"mode": settings.data_mode}

    return app


app = create_app()
