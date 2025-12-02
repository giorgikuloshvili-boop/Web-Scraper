from fastapi import APIRouter
from pydantic import BaseModel
from http import HTTPStatus

from app.core.models.schemas import WebScraperResponse

web_scraper_api = APIRouter()

class WebScraperBase(BaseModel):
    url: str
    force: bool = False


@web_scraper_api.post("/trigger",
                      response_model=WebScraperResponse,
                      status_code=HTTPStatus.CREATED
                      )
async def scrape_web(request: WebScraperBase) -> WebScraperResponse:
    pass

