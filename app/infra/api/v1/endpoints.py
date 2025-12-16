import uuid
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from http import HTTPStatus

from fastapi import APIRouter, Depends, BackgroundTasks, Request, HTTPException
from pydantic import BaseModel, HttpUrl

from app.core.config import settings
from app.core.interactor import WebScraperInteractor
from app.core.schemas import WebScraperResponse, WebScraperRequest, ResponseStatus
from app.infra.dependables import get_core, get_task_store


web_scraper_api = APIRouter()
logger = logging.getLogger(__name__)


async def _background_scrape_wrapper(
        task_id: uuid.UUID,
        request: WebScraperRequest,
        core: WebScraperInteractor,
        tasks_store: Dict[uuid.UUID, Dict[str, Any]]
) -> None:
    """
    Executes the scraping logic within a specific logging context.
    """
    str_task_id = str(task_id)

    # with task_logging(str_task_id):
    try:
        logger.info(f"Task Started | ID: {str_task_id} | URL: {request.url}")

        stats = await core.run_scraping(request=request)

        tasks_store[task_id].update({
            "status": "completed",
            "completed_at": datetime.now(),
            "pages_processed": stats.get("processed", 0),
            "pages_failed": stats.get("failed", 0),
            "progress": 100.0
        })

        logger.info(f"Task Completed Successfully | Processed: {stats.get('processed', 0)}")
        logger.info(f"Final Task State: {tasks_store[task_id]}")

    except Exception as exc:
        tasks_store[task_id].update({
            "status": "failed",
            "error": str(exc),
            "completed_at": datetime.now()
        })

        logger.error(f"Task Failed: {exc}", exc_info=True)
        logger.info(f"Final Task State (Failed): {tasks_store[task_id]}")


class WebScraperBase(BaseModel):
    url: Optional[HttpUrl] = settings.TARGET_URL
    force: bool = False


@web_scraper_api.post("/trigger",
                      response_model=WebScraperResponse,
                      status_code=HTTPStatus.CREATED
                      )
async def scrape_web(
        request: WebScraperBase,
        background_tasks: BackgroundTasks,
        req_info: Request,
        core: WebScraperInteractor = Depends(get_core),
        tasks_store: Dict[uuid.UUID, Dict[str, Any]] = Depends(get_task_store),
) -> WebScraperResponse:
    task_id = uuid.uuid4()
    client_ip = req_info.client.host if req_info.client else "unknown"

    logger.info(f"Manual Trigger received from IP: {client_ip} | Target: {request.url} | Task ID: {task_id}")

    tasks_store[task_id] = {
        "task_id": task_id,
        "status": ResponseStatus.QUEUED.value,
        "created_at": datetime.now(),
        "url": request.url,
        "triggered_by": client_ip
    }

    logger.info(f"Initial Task State: {tasks_store[task_id]}")

    background_tasks.add_task(
        _background_scrape_wrapper,
        task_id=task_id,
        request=WebScraperRequest(**request.model_dump()), # Use model_dump for Pydantic v2
        core=core,
        tasks_store=tasks_store,
    )

    return WebScraperResponse(
        task_id=task_id,
        status=tasks_store[task_id]["status"],
        estimated_time=None
    )


@web_scraper_api.get("/status/{task_id}",
                     response_model=Dict[str, Any],
                     status_code=HTTPStatus.OK)
async def get_status(
        task_id: uuid.UUID,
        tasks_store: Dict[uuid.UUID, Dict[str, Any]] = Depends(get_task_store)
) -> Dict[str, Any]:
    try:
        return tasks_store[task_id]
    except KeyError:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=f"Task with ID {task_id} not found")



@web_scraper_api.get("/logs",
                     status_code=HTTPStatus.OK)
async def get_logs() -> None:
    pass
