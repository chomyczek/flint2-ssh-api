import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.api.v1.devices import router as devices_router

logging.basicConfig(level=settings.log_level.upper())
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    yield
    logger.info("Shutting down...")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
)


@app.get("/health")
async def health():
    return {"status": "ok", "version": settings.app_version}


app.include_router(devices_router, prefix="/api/v1")
