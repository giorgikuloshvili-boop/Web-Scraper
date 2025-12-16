import pytest
import uuid
from unittest.mock import AsyncMock, patch
from app.core.interactor import WebScraperInteractor


@pytest.mark.asyncio
async def test_trigger_endpoint_happy_path(async_client, monkeypatch):
    """
    Test that calling /trigger starts a job and returns the correct JSON structure.
    """
    # 1. Mock the heavy lifting (Interactor) so we don't actually scrape
    mock_run = AsyncMock(return_value={"processed": 5, "failed": 0, "errors": []})
    monkeypatch.setattr(WebScraperInteractor, "run_scraping", mock_run)

    # 2. Trigger the scrape
    payload = {"url": "https://example.com", "force": False}
    response = await async_client.post("/scraper/trigger", json=payload)

    # 3. Validate Response
    assert response.status_code == 201
    data = response.json()
    assert "task_id" in data
    assert data["status"] == "queued"

    # 4. Verify Background Task Execution
    # Since FastAPI TestClient/AsyncClient runs background tasks immediately in tests:
    task_id = data["task_id"]

    # Check if status endpoint reflects the completion (because background task ran)
    status_response = await async_client.get(f"/scraper/status/{task_id}")
    assert status_response.status_code == 200
    status_data = status_response.json()

    # It should have moved from QUEUED to COMPLETED because the mock finished instantly
    assert status_data["status"] == "completed"
    assert status_data["pages_processed"] == 5


@pytest.mark.asyncio
async def test_trigger_endpoint_validation_error(async_client):
    """Test that invalid URLs are rejected."""
    payload = {"url": "not-a-url", "force": False}
    response = await async_client.post("/scraper/trigger", json=payload)

    assert response.status_code == 422  # Unprocessable Entity


@pytest.mark.asyncio
async def test_get_status_not_found(async_client):
    """Test 404 for non-existent task IDs."""
    random_id = str(uuid.uuid4())
    response = await async_client.get(f"/scraper/status/{random_id}")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]