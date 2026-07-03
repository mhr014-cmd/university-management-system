"""
FastAPI application entrypoint.

Assembles the app factory: settings, logging, CORS, exception handlers,
request logging middleware, and routers. Milestone 0 registers only the
health router — business routers are added starting Milestone 1.
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
from app.routers import health

settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger("app.startup")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up in '%s' environment", settings.environment)
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        logger.info("Database connection verified")
    except Exception:
        logger.exception("Database connection could not be established at startup")
    yield
    logger.info("Shutting down")


def create_app() -> FastAPI:
    app = FastAPI(
        title="ICT Education API",
        version="0.1.0",
        lifespan=lifespan,
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

    return app


app = create_app()
