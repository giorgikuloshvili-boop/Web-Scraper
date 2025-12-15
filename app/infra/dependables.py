from typing import Any, Dict
from uuid import UUID

from starlette.requests import Request


_task_store: Dict[UUID, Dict[str, Any]] = {}

def get_task_store() -> Dict[UUID, Dict[str, Any]]:
    return _task_store


def get_core(request: Request) -> Any:
    return request.app.state.core