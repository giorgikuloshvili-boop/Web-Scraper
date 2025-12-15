from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import settings
from app.core.interactor import WebScraperInteractor
from app.core.logger import configure_logging
from app.core.scheduler import start_scheduler, shutdown_scheduler
from app.infra.api.v1.endpoints import web_scraper_api



@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    shutdown_scheduler()


def setup() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        lifespan=lifespan,
    )
    app.include_router(web_scraper_api, prefix="/scraper", tags=["scraper"])
    app.state.core = WebScraperInteractor.create()
    configure_logging()
    return app