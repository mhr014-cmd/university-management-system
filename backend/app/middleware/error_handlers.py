"""
Global exception handlers (see docs/System_Architecture.md Section 9).

Translates every raised error into the single consistent JSON error shape:
    { "error": { "code": "...", "message": "...", "details": [...] } }
"""

import logging

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("app.errors")

# Fields whose raw submitted value must never reach a log line or an HTTP
# response body, even inside a validation-error's `input` echo. Pydantic
# v2's ValidationError.errors() always includes the raw pre-validation
# input verbatim regardless of the field's declared type (SecretStr does
# not suppress this), so this is the only place that actually stops the
# leak (CLAUDE.md §12/§13, System_Architecture.md §11 — no plaintext
# passwords in logs or responses).
_SENSITIVE_FIELD_NAMES = {"password", "current_password", "new_password"}
_REDACTED = "[REDACTED]"


def _redact_sensitive(value):
    if isinstance(value, dict):
        return {
            key: (_REDACTED if key in _SENSITIVE_FIELD_NAMES else _redact_sensitive(val))
            for key, val in value.items()
        }
    return value


def _sanitize_validation_errors(errors: list[dict]) -> list[dict]:
    """Strips any password value out of a validation error's `input` echo.

    Field-level errors (e.g. `new_password` too short) have `loc` naming
    the offending field directly, with `input` set to that field's raw
    value. Whole-model errors (e.g. the current/new password `model_validator`)
    have an empty `loc` and `input` set to the *entire* submitted body as a
    dict — both shapes are handled here.
    """
    sanitized = []
    for error in errors:
        error = dict(error)
        loc = error.get("loc", ())
        if any(isinstance(part, str) and part in _SENSITIVE_FIELD_NAMES for part in loc):
            error["input"] = _REDACTED
        elif "input" in error:
            error["input"] = _redact_sensitive(error["input"])
        sanitized.append(error)
    return sanitized


def _error_response(status_code: int, code: str, message: str, details: list | None = None) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message, "details": details or []}},
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        sanitized_errors = _sanitize_validation_errors(exc.errors())
        logger.info("Validation error on %s %s: %s", request.method, request.url.path, sanitized_errors)
        # Pydantic v2 embeds the raw exception instance in error["ctx"]["error"] for
        # custom validators (e.g. @model_validator raising ValueError) — not JSON
        # serializable as-is, so it must go through jsonable_encoder before json.dumps.
        return _error_response(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "validation_error",
            "Request validation failed.",
            details=jsonable_encoder(sanitized_errors),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        log_level = logging.WARNING if exc.status_code >= 500 else logging.INFO
        logger.log(log_level, "HTTPException on %s %s: %s", request.method, request.url.path, exc.detail)
        return _error_response(
            exc.status_code,
            _code_for_status(exc.status_code),
            str(exc.detail),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
        return _error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "internal_server_error",
            "An unexpected error occurred.",
        )


def _code_for_status(status_code: int) -> str:
    return {
        status.HTTP_400_BAD_REQUEST: "bad_request",
        status.HTTP_401_UNAUTHORIZED: "unauthorized",
        status.HTTP_403_FORBIDDEN: "forbidden",
        status.HTTP_404_NOT_FOUND: "not_found",
        status.HTTP_409_CONFLICT: "conflict",
        status.HTTP_422_UNPROCESSABLE_CONTENT: "validation_error",
    }.get(status_code, "error")
