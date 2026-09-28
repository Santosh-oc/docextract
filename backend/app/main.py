import os
import time
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.types import ASGIApp

from app.api import documents, extractions, health
from app.api import settings as settings_api
from app.config import get_settings
from app.core.errors import AppError
from app.core.logging import (
    configure_logging,
    get_logger,
    new_request_id,
    request_id_ctx,
)

settings = get_settings()
configure_logging(settings.log_level)
logger = get_logger("app.request")

fastapi_app = FastAPI(title="Document Extraction", version="1.0.0")

origins = ["*"] if settings.cors_origins == "*" else settings.cors_origins.split(",")
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@fastapi_app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    request_id = new_request_id()
    token = request_id_ctx.set(request_id)
    start = time.perf_counter()
    try:
        response = await call_next(request)
    finally:
        request_id_ctx.reset(token)
    duration_ms = int((time.perf_counter() - start) * 1000)
    logger.info(
        "request handled",
        extra={
            "operation": "http_request",
            "processing_time_ms": duration_ms,
            "status": getattr(response, "status_code", None),
            "request_id": request_id,
        },
    )
    response.headers["X-Request-ID"] = request_id
    return response


@fastapi_app.middleware("http")
async def platform_auth_middleware(request: Request, call_next):
    """DKubeX's gateway authenticates the user and injects X-Auth-Request-User; this app must
    never implement its own login. /api/health is exempt because kubelet probes reach the pod
    directly, bypassing the gateway, and never carry the header."""
    if settings.platform_auth_required and request.url.path != "/api/health":
        if not request.headers.get("x-auth-request-user"):
            return JSONResponse(status_code=401, content={"error": "Not authenticated"})
    return await call_next(request)


@fastapi_app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message, "detail": exc.detail},
    )


fastapi_app.include_router(health.router)
fastapi_app.include_router(settings_api.router)
fastapi_app.include_router(documents.router)
fastapi_app.include_router(extractions.router)

_frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if _frontend_dist.exists():
    fastapi_app.mount("/", StaticFiles(directory=str(_frontend_dist), html=True), name="frontend")


class _RootPathMiddleware:
    """Sets ASGI scope["root_path"] directly instead of relying on uvicorn's
    --root-path flag.

    The DKubeX workspace nginx proxies with no URI component on proxy_pass,
    so it forwards the full request URI (base path included) unstripped.
    uvicorn's --root-path unconditionally prepends root_path to whatever
    path it receives, which would double the prefix here. Setting
    scope["root_path"] ourselves lets Starlette's router strip the matching
    prefix from the already-prefixed path for route matching (see
    starlette.routing.get_route_path), while root_path stays correct for
    OpenAPI/url_for generation.
    """

    def __init__(self, asgi_app, root_path: str):
        self._app = asgi_app
        self._root_path = root_path

    async def __call__(self, scope, receive, send):
        if self._root_path and scope["type"] in ("http", "websocket"):
            scope["root_path"] = self._root_path
        await self._app(scope, receive, send)


app: ASGIApp = _RootPathMiddleware(fastapi_app, os.environ.get("DKUBEX_BASE_PATH", ""))
