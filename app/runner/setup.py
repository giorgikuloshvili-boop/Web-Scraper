from fastapi import FastAPI

from app.core.interactor import WebScraperInteractor
from app.infra.api.v1.endpoints import web_scraper_api


def setup() -> FastAPI:
    app = FastAPI()
    app.include_router(web_scraper_api, prefix="/scraper", tags=["scraper"])
    app.state.core = WebScraperInteractor.create()
    return app