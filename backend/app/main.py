"""
FastAPI application entrypoint.

Assembles the app factory: settings, logging, CORS, exception handlers,
request logging middleware, and routers.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.config import get_settings
from app.core.logging_config import configure_logging
from app.db.session import engine
from app.middleware.error_handlers import register_exception_handlers
from app.middleware.logging import RequestLoggingMiddleware
from app.routers import (
    attendance,
    auth,
    exams,
    fees,
    health,
    notifications,
    reference_data,
    reports,
    results,
    schedule,
    users,
)

settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger("app.startup")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s in '%s' environment", app.title, settings.environment)
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        logger.info("Database connection verified")
    except Exception:
        logger.exception("Database connection could not be established at startup")
    yield
    logger.info("Shutting down")


def create_app() -> FastAPI:
    # Milestone 11 (Security Strategy, System_Architecture.md §11): the
    # interactive API docs/schema expose the full endpoint surface and are
    # a reasonable target to close off in production, while staying
    # available in every other environment for grading/demo purposes.
    docs_enabled = not settings.is_production

    app = FastAPI(
        title="University Management System API",
        description="REST API for the University Management System (ICT Education) — "
        "attendance, exams, results, fees, and scheduling.",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if docs_enabled else None,
        redoc_url="/redoc" if docs_enabled else None,
        openapi_url="/openapi.json" if docs_enabled else None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestLoggingMiddleware)

    register_exception_handlers(app)

    app.include_router(health.router)
    app.include_router(auth.router, prefix=settings.api_v1_prefix)
    app.include_router(reference_data.router, prefix=settings.api_v1_prefix)
    app.include_router(users.router, prefix=settings.api_v1_prefix)
    app.include_router(schedule.router, prefix=settings.api_v1_prefix)
    app.include_router(attendance.router, prefix=settings.api_v1_prefix)
    app.include_router(exams.router, prefix=settings.api_v1_prefix)
    app.include_router(results.router, prefix=settings.api_v1_prefix)
    app.include_router(fees.router, prefix=settings.api_v1_prefix)
    app.include_router(notifications.router, prefix=settings.api_v1_prefix)
    app.include_router(reports.router, prefix=settings.api_v1_prefix)

    return app


app = create_app()
