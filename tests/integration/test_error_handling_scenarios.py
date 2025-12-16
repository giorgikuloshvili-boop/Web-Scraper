import pytest
from unittest.mock import AsyncMock, patch
from app.core.interactor import WebScraperInteractor


@pytest.mark.asyncio
async def test_background_task_failure_handling(async_client, monkeypatch):
    """
    Simulate a critical failure in the scraping core (e.g., Exception raised).
    Verify that the API task status updates to 'failed' and doesn't crash the server.
    """

    # 1. Mock run_scraping to raise an unexpected Exception
    mock_run = AsyncMock(side_effect=Exception("Selenium Driver Crashed!"))
    monkeypatch.setattr(WebScraperInteractor, "run_scraping", mock_run)

    # 2. Trigger the job
    payload = {"url": "https://crash-test.com"}
    response = await async_client.post("/scraper/trigger", json=payload)
    assert response.status_code == 201
    task_id = response.json()["task_id"]

    # 3. Check Status
    # The background task should have caught the exception and updated the store
    status_response = await async_client.get(f"/scraper/status/{task_id}")
    status_data = status_response.json()

    assert status_data["status"] == "failed"
    assert "Selenium Driver Crashed" in status_data["error"]


@pytest.mark.asyncio
async def test_interactor_handles_start_session_failure():
    """
    Integration test for the Interactor's internal error handling.
    If the scraper fails to start (e.g. no Chrome installed),
    run_scraping should return a clean stats dict indicating failure, not raise.
    """
    from app.core.schemas import WebScraperRequest

    # Mock Scraper to fail immediately
    mock_scraper = AsyncMock()
    mock_scraper.start_session.return_value = False  # Simulate failure

    # Create Interactor with faulty scraper
    interactor = WebScraperInteractor(
        scraper=mock_scraper,
        parser=AsyncMock(),
        converter=AsyncMock(),
        storage=AsyncMock()
    )

    # Run
    stats = await interactor.run_scraping(WebScraperRequest(url="http://test.com"))

    # Verify graceful failure
    assert stats["failed"] == 1
    assert stats["processed"] == 0
    assert "Failed to start scraper" in stats["errors"][0]