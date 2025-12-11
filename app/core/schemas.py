from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, HttpUrl, Field


class ResponseStatus(Enum):
    STARTED = "started"
    QUEUED = "queued"


class WebScraperRequest(BaseModel):
    """
    Request payload for triggering a scrape job.
    """
    url: Optional[HttpUrl] = "https://www.gloworld.com/"
    force: bool = Field(
        default=False,
        description="Force re-scrape even if data exists."
    )


class WebScraperResponse(BaseModel):
    """
        Response model for the trigger endpoint.
    """
    task_id: UUID = Field(..., description="Unique identifier for the task")
    status: ResponseStatus = Field(..., description="Current status of the request")
    estimated_time: Optional[datetime] = Field(
        default=None,
        description="Estimated time when the scraping will finish"
    )