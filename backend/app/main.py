from __future__ import annotations

import logging
import time
from collections.abc import Callable
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from app.api.routes import assessments, dashboard, health, models, preferences
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging
from app.db.session import Database
from app.db.base import Base
from app.ml.registry import ModelRegistry

logger = logging.getLogger("glucocare.api")


def create_app(settings: Settings | None = None) -> FastAPI:
    runtime_settings = settings or get_settings()
    configure_logging(runtime_settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.settings = runtime_settings
        app.state.database = Database(runtime_settings.resolved_database_url)
        if runtime_settings.uses_local_development_database:
            Base.metadata.create_all(app.state.database.engine)
        app.state.model_registry = ModelRegistry(runtime_settings.resolved_model_artifact_path)
        yield

    app = FastAPI(
        title="GlucoCare API",
        version="0.1.0",
        description="Tabular diabetes-classification research prototype. Not a diagnostic or medical device.",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=runtime_settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Content-Type", "X-Request-ID"],
    )
    _add_operational_handlers(app)
    app.include_router(health.router, prefix=runtime_settings.api_prefix)
    app.include_router(assessments.router, prefix=runtime_settings.api_prefix)
    app.include_router(dashboard.router, prefix=runtime_settings.api_prefix)
    app.include_router(models.router, prefix=runtime_settings.api_prefix)
    app.include_router(preferences.router, prefix=runtime_settings.api_prefix)
    return app


def _add_operational_handlers(app: FastAPI) -> None:
    @app.middleware("http")
    async def request_context(request: Request, call_next: Callable[[Request], Response]) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        started_at = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            logger.exception("request_failed request_id=%s route=%s", request_id, request.url.path)
            response = JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"code": "internal_error", "message": "An unexpected server error occurred.", "request_id": request_id})
        response.headers["X-Request-ID"] = request_id
        logger.info("request_complete request_id=%s route=%s status=%s latency_ms=%.2f", request_id, request.url.path, response.status_code, (time.perf_counter() - started_at) * 1000)
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, error: RequestValidationError) -> JSONResponse:
        request_id = request.headers.get("X-Request-ID", "unknown")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"code": "validation_error", "message": "Please check the submitted fields.", "request_id": request_id, "field_errors": {str(item["loc"][-1]): item["msg"] for item in error.errors()}},
        )

    @app.exception_handler(HTTPException)
    async def http_error_handler(request: Request, error: HTTPException) -> JSONResponse:
        request_id = request.headers.get("X-Request-ID", "unknown")
        codes = {
            status.HTTP_403_FORBIDDEN: "forbidden",
            status.HTTP_404_NOT_FOUND: "not_found",
            status.HTTP_503_SERVICE_UNAVAILABLE: "dependency_unavailable",
        }
        message = error.detail if isinstance(error.detail, str) else "The request could not be completed."
        return JSONResponse(status_code=error.status_code, content={"code": codes.get(error.status_code, "request_error"), "message": message, "request_id": request_id})


app = create_app()
