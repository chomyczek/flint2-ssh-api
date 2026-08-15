import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.api.v1.devices import router as devices_router
from app.config import settings
from app.services.ssh_manager import ssh_manager

logging.basicConfig(level=settings.log_level.upper())
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    await ssh_manager.connect()
    yield
    logger.info("Shutting down..")
    await ssh_manager.disconnect()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
)


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")


@app.get("/health")
async def health():
    return {"status": "ok", "version": settings.app_version, "router_connected": ssh_manager.is_connected(),
            "SSH_reconnects": ssh_manager.reconnect_count, "router_host": settings.router_host}


app.include_router(devices_router, prefix="/api/v1")

if __name__ == "__main__":
    if not settings.debug:
        logger.info("Application without DEBUG flag should be run with 'uvicorn app.main:app' command")
        exit(0)
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
