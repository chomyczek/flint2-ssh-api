import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.api.v1.devices import router as devices_router
from app.config import settings
from app.services.cache_service import get_stats
from app.services.ssh_manager import ssh_manager
from app.utils.metadata import get_app_metadata

logging.basicConfig(level=settings.log_level.upper())
logger = logging.getLogger(__name__)

_meta = get_app_metadata()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application startup and shutdown resources.

    Args:
        app: FastApi application instance.

    Yields: Control while the application is running.
    """
    logger.info(f"Starting {_meta.name} v{_meta.version}")
    await ssh_manager.connect()
    yield
    logger.info("Shutting down..")
    await ssh_manager.disconnect()


app = FastAPI(
    title=_meta.name,
    version=_meta.version,
    debug=settings.debug,
    lifespan=lifespan,
)


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
