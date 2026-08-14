import logging
import re
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api import cases, models, sessions, skills
from .config import AppSettings, load_settings
from .core.evaluator import EvaluationError
from .model_gateway.base import GatewayError
from .storage.case_store import CaseNotFoundError, InvalidCaseError
from .storage.session_store import SessionNotFoundError
from .storage.skill_store import InvalidSkillError, SkillNotFoundError

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("coach")


def create_app(settings: AppSettings | None = None) -> FastAPI:
    """Create an app from explicit settings so CORS policies are testable."""
    active_settings = settings or load_settings()
    application = FastAPI(title="Strategic Analysis Coach", version="0.2.0")
    application.state.settings = active_settings
    application.add_middleware(
        CORSMiddleware,
        allow_origins=active_settings.cors.allowed_origins,
        allow_origin_regex=active_settings.cors_origin_regex,
        allow_credentials=False,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "X-Request-ID"],
    )

    for router in (models.router, skills.router, cases.router, sessions.router):
        application.include_router(router)

    @application.get("/health")
    async def health():
        return {"status": "ok"}

    @application.middleware("http")
    async def request_log(request: Request, call_next):
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
        started = time.perf_counter()
        response = await call_next(request)
        response.headers["x-request-id"] = request_id
        logger.info({
            "request_id": request_id,
            "route": request.url.path,
            "status": response.status_code,
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
        })
        return response

    @application.exception_handler(Exception)
    async def safe_errors(request: Request, exc: Exception):
        mapping = {
            SessionNotFoundError: 404,
            CaseNotFoundError: 404,
            SkillNotFoundError: 404,
            InvalidCaseError: 422,
            InvalidSkillError: 422,
            EvaluationError: 502,
            GatewayError: 502,
        }
        code = next((value for kind, value in mapping.items() if isinstance(exc, kind)), 500)
        response = JSONResponse(
            status_code=code,
            content={
                "detail": str(exc) if code != 500 else "Internal server error",
                "message": str(exc) if code != 500 else "Internal server error",
                "error_type": getattr(exc, "error_type", type(exc).__name__),
                "stage": getattr(exc, "stage", None),
            },
        )
        origin = request.headers.get("origin")
        origin_allowed = bool(origin) and (
            origin in active_settings.cors.allowed_origins
            or bool(active_settings.cors_origin_regex and re.fullmatch(active_settings.cors_origin_regex, origin))
        )
        if origin_allowed:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Vary"] = "Origin"
        return response

    return application


app = create_app()
