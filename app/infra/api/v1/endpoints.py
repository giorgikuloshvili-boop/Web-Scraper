from fastapi import APIRouter, Depends
from pydantic import BaseModel
from http import HTTPStatus

from app.core.interactor import WebScraperInteractor
from app.core.schemas import WebScraperResponse, WebScraperRequest
from app.infra.dependables import get_core

web_scraper_api = APIRouter()

class WebScraperBase(BaseModel):
    url: str
    force: bool = False


@web_scraper_api.post("/trigger",
                      response_model=WebScraperResponse,
                      status_code=HTTPStatus.CREATED
                      )
async def scrape_web(request: WebScraperBase, core: WebScraperInteractor = Depends(get_core)) -> WebScraperResponse:
    return core.run_scraping(request=WebScraperRequest(**request.dict()))

