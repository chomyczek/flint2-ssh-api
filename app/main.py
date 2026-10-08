import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from starlette.responses import JSONResponse

from app.api.v1.devices import router as devices_router
from app.config import settings
from app.exceptions import RouterUnavailableError, SSHCommandError
from app.services.cache_service import get_stats
from app.services.ssh_manager import ssh_manager
from app.utils.metadata import get_app_metadata

logger = logging.getLogger(__name__)

_meta = get_app_metadata()


def setup_logging() -> None:
    """Configure logging settings for the application."""
    uv_logger = logging.getLogger("uvicorn")
    handler = uv_logger.handlers[0] if uv_logger.handlers else logging.StreamHandler()

    root_logger = logging.getLogger(__package__) if settings.log_isolation else logging.getLogger()
    root_logger.setLevel(settings.log_level.upper())
    root_logger.handlers = [handler]
    root_logger.propagate = False


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application startup and shutdown resources.

    Args:
        app: FastApi application instance.

    Yields: Control while the application is running.
    """
    setup_logging()
    logger.info(f"Starting {_meta.name} v{_meta.version}")
    try:
        await ssh_manager.connect()
    except RouterUnavailableError as e:
        logger.warning(f"Could not connect to router on startup: {e.detail}")
        logger.warning(f"API will start but some endpoints will return 503 until router is reachable.")
    yield
    logger.info("Shutting down..")
    await ssh_manager.disconnect()


app = FastAPI(
    title=_meta.name,
    version=_meta.version,
    debug=settings.debug,
    lifespan=lifespan,
)


@app.exception_handler(RouterUnavailableError)
async def router_unavailable_exception_handler(request:Request, exc: RouterUnavailableError) ->JSONResponse:
    """Handle RouterUnavailableError exceptions and return 503 with generic message.

    Args:
        request: The incoming HTTP request.
        exc: The raised exception.

    Returns: JSON response with error and 503 status code.
    """
    logger.debug(f"RouterUnavailableError on {request.method} {request.url.path}: {exc.detail}")
    return JSONResponse(status_code=503, content={"detail": "Router is currently unavailable. Please try again later."})


@app.exception_handler(SSHCommandError)
async def ssh_command_exception_handler(request:Request, exc: SSHCommandError) -> JSONResponse:
    """Handle SSHCommandError exceptions and return 503 with generic message.

    Args:
        request: The incoming HTTP request.
        exc: The raised exception.

    Returns: JSON response with error and 503 status code.
    """
    logger.debug(f"SSHCommandError on {request.method} {request.url.path}: {exc.detail}")
    return JSONResponse(status_code=503, content={"detail": "Router is currently unavailable. Please try again later."})


@app.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    """Redirect root endpoint to the API documentation.

    Returns: Redirect response pointing to the Swagger UI
    """
    return RedirectResponse(url="/docs")


@app.get("/health")
async def health() -> dict[str, object]:
    """Return the current application health status.

    Returns: Application , SSH connection, and cache status details.
    """
    return {
        "status": "ok",
        "version": _meta.version,
        "router_connected": ssh_manager.is_connected(),
        "SSH_reconnects": ssh_manager.reconnect_count,
        "router_host": settings.router_host,
        "cache": get_stats(),
    }


app.include_router(devices_router, prefix="/api/v1")

if __name__ == "__main__":
    if not settings.debug:
        logger.info("Application without DEBUG flag should be run with 'uvicorn app.main:app' command")
        exit(0)

    from pathlib import Path

    import uvicorn

    app_dir = Path(__file__).parent

    uvicorn.run("app.main:app", reload=True, reload_dirs=[str(app_dir)])
