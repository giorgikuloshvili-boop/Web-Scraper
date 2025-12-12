import uuid
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, HttpUrl
from http import HTTPStatus

from app.core.interactor import WebScraperInteractor
from app.core.schemas import WebScraperResponse, WebScraperRequest, ResponseStatus
from app.infra.dependables import get_core

web_scraper_api = APIRouter()

class WebScraperBase(BaseModel):
    url: Optional[HttpUrl] = "https://www.gloworld.com/"
    force: bool = False


@web_scraper_api.post("/trigger",
                      response_model=WebScraperResponse,
                      status_code=HTTPStatus.CREATED
                      )
async def scrape_web(request: WebScraperBase, core: WebScraperInteractor = Depends(get_core)) -> WebScraperResponse:
    task_id = uuid.uuid4()
    stats = await core.run_scraping(request=WebScraperRequest(**request.dict()))
    return WebScraperResponse(
        task_id=task_id,
        status=ResponseStatus.QUEUED,
        estimated_time=None
    )

