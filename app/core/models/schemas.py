from datetime import datetime
from enum import Enum

from pydantic import BaseModel

class ResponseStatus(Enum):
    STARTED = "started"
    QUEUED = "queued"


class WebScraperResponse(BaseModel):
    task_id: int
    status: ResponseStatus
    estimated_time: datetime