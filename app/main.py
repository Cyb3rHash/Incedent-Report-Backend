from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker
from starlette.status import HTTP_404_NOT_FOUND, HTTP_422_UNPROCESSABLE_ENTITY, HTTP_500_INTERNAL_SERVER_ERROR

from app.api.routes.incidents import bind_session_dependency, router as incidents_router
from app.core.config import Settings, get_settings
from app.core.errors import AppError, ApiErrorPayload, NotFoundError
from app.core.logging import configure_logging
from app.db.session import create_engine, create_session_factory, get_db_session

logger = logging.getLogger(__name__)

OPENAPI_TAGS = [
    {
        "name": "Incidents",
        "description": "Incident CRUD endpoints for reporting and tracking incidents.",
    }
]


def _structured_error(status_code: int, payload: ApiErrorPayload) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": payload.code, "message": payload.message, "details": payload.details}},
    )


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(
        title=settings.app_name,
        description="Incident Reporting & Tracking API backed by Neon PostgreSQL.",
        version=settings.app_version,
        openapi_tags=OPENAPI_TAGS,
    )

    # DB engine/session factory stored on app state for reuse.
    engine: AsyncEngine = create_engine(settings)
    session_factory: async_sessionmaker = create_session_factory(engine)
    app.state.engine = engine
    app.state.session_factory = session_factory

    if settings.allowed_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.allowed_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @app.get(
        "/health",
        summary="Health check",
        description="Basic health check endpoint.",
        tags=["System"],
        operation_id="healthCheck",
    )
    async def health() -> Dict[str, Any]:
        """Health check endpoint."""
        return {"status": "ok"}

    @app.exception_handler(NotFoundError)
    async def not_found_handler(_request: Request, exc: NotFoundError) -> JSONResponse:
        return _structured_error(HTTP_404_NOT_FOUND, ApiErrorPayload(code=exc.code, message=exc.message, details=exc.details))

    @app.exception_handler(AppError)
    async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
        # Default mapping for other domain errors.
        return _structured_error(HTTP_500_INTERNAL_SERVER_ERROR, ApiErrorPayload(code=exc.code, message=exc.message, details=exc.details))

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
        # Return validation errors in a consistent top-level error envelope.
        return _structured_error(
            HTTP_422_UNPROCESSABLE_ENTITY,
            ApiErrorPayload(code="VALIDATION_ERROR", message="Request validation failed.", details={"errors": exc.errors()}),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
        # Avoid leaking stack traces to clients; keep details minimal but log full exception.
        logger.exception("Unhandled exception: %s", exc)
        return _structured_error(
            HTTP_500_INTERNAL_SERVER_ERROR,
            ApiErrorPayload(code="INTERNAL_SERVER_ERROR", message="Unexpected server error.", details=None),
        )

    # Bind router dependencies (request-scoped session).
    async def session_dep():
        async for s in get_db_session(session_factory):
            yield s

    # Include routers
    app.include_router(incidents_router)
    bind_session_dependency(incidents_router, session_dep)

    return app


# PUBLIC_INTERFACE
app = create_app()
"""FastAPI ASGI entrypoint.

Run locally:
  uvicorn app.main:app --host 0.0.0.0 --port 3002
"""
