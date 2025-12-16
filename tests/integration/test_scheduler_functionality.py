import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from apscheduler.triggers.cron import CronTrigger

from app.core.scheduler import start_scheduler, shutdown_scheduler, scheduled_scrape_job, scheduler as global_scheduler
from app.core.config import settings
from app.core.interactor import WebScraperInteractor
from app.core.schemas import WebScraperRequest

@pytest.fixture(autouse=True)
def mock_logger(mocker):
    mock_log = MagicMock()
    mocker.patch("app.core.scheduler.logger", new=mock_log)
    return mock_log

@pytest.fixture
def mock_interactor(mocker):
    mock_scraper_interactor = MagicMock(spec=WebScraperInteractor)
    mock_scraper_interactor.run_scraping = AsyncMock(return_value={"processed": 1, "failed": 0})
    mocker.patch("app.core.interactor.WebScraperInteractor.create", return_value=mock_scraper_interactor)
    return mock_scraper_interactor

@pytest.fixture
def mock_scheduler(mocker):
    # Patch the global scheduler instance
    mock_sched = MagicMock(spec=type(global_scheduler)) # Use type of actual scheduler to get its methods
    mock_sched.running = False
    mock_sched.start.return_value = None
    mock_sched.shutdown.return_value = None
    mock_sched.remove_all_jobs.return_value = None
    mocker.patch("app.core.scheduler.scheduler", new=mock_sched)
    return mock_sched

@pytest.mark.asyncio
async def test_scheduler_starts_and_executes_job(mock_interactor, mock_logger, mock_scheduler, mocker):
    # Set a schedule time in the very near future for testing
    now = datetime.now()
    schedule_time = (now + timedelta(seconds=2)).strftime("%H:%M")
    mocker.patch.object(settings, "SCRAPE_SCHEDULE_TIME", schedule_time)
    mocker.patch.object(settings, "TARGET_URL", "https://scheduled-integration.com")
    mocker.patch.object(settings, "TIMEZONE", "UTC")

    # Ensure scheduler is clean and not running before test
    mock_scheduler.remove_all_jobs()

    # Simulate scheduler start
    mock_scheduler.running = True
    start_scheduler()

    mock_logger.info.assert_any_call(f"Scheduler started. Next run at: {schedule_time} (UTC)")

    # Manually call the scheduled job since the actual scheduler is mocked
    await scheduled_scrape_job()

    # Assertions
    mock_interactor.run_scraping.assert_called_once_with(WebScraperRequest(url="https://scheduled-integration.com"))
    mock_logger.info.assert_any_call("Starting scheduled daily scrape job...")
    mock_logger.info.assert_any_call("Scheduled scrape completed. Stats: {'processed': 1, 'failed': 0}")

    # Simulate scheduler shutdown
    mock_scheduler.running = False
    shutdown_scheduler()
    mock_logger.info.assert_any_call("Shutting down scheduler...")

@pytest.mark.asyncio
async def test_scheduler_shutdown_stops_jobs(mock_interactor, mock_logger, mock_scheduler, mocker):
    # Set a schedule time for the job that won't run during this test's short duration
    mocker.patch.object(settings, "SCRAPE_SCHEDULE_TIME", "23:59")
    mocker.patch.object(settings, "TARGET_URL", "https://never-run.com")
    mocker.patch.object(settings, "TIMEZONE", "UTC")

    # Ensure scheduler is clean and not running before test
    mock_scheduler.remove_all_jobs()

    # Simulate scheduler start and then shutdown
    mock_scheduler.running = True
    start_scheduler()
    mock_scheduler.start.assert_called_once()

    mock_scheduler.running = False
    shutdown_scheduler()
    mock_scheduler.shutdown.assert_called_once()

    # Give it a moment to ensure no background tasks somehow start after shutdown
    await asyncio.sleep(0.1)

    mock_interactor.run_scraping.assert_not_called()
    mock_logger.info.assert_any_call("Shutting down scheduler...")


def test_scheduler_initialization_parameters(mock_scheduler, mock_logger, mocker):
    """
    Verifies that the scheduler is initialized with the correct time and timezone settings.
    Replacement for test_start_scheduler_success_job_added.
    """
    # 1. Setup deterministic settings (Mock both Time and Timezone)
    target_time = "04:30"
    target_tz = "UTC"

    mocker.patch.object(settings, "SCRAPE_SCHEDULE_TIME", target_time)
    mocker.patch.object(settings, "TIMEZONE", target_tz)

    # 2. Run the initialization
    start_scheduler()

    # 3. Verify Job Addition
    mock_scheduler.add_job.assert_called_once()
    args, kwargs = mock_scheduler.add_job.call_args

    # Verify the task function (1st Positional Arg)
    assert args[0] == scheduled_scrape_job

    # Verify Trigger (2nd Positional Arg)
    trigger = args[1]
    assert isinstance(trigger, CronTrigger)

    # Robustly check hour/minute (04:30 -> Hour="4", Minute="30")
    # APScheduler field indices: 5=hour, 6=minute
    assert str(trigger.fields[5].expressions[0]) == "4"
    assert str(trigger.fields[6].expressions[0]) == "30"

    # 4. Verify Logger
    # Since we mocked settings.TIMEZONE to "UTC", the log must match "UTC"
    mock_logger.info.assert_any_call(f"Scheduler started. Next run at: {target_time} ({target_tz})")

def test_start_scheduler_invalid_time_format_error_handling(mock_scheduler, mock_settings, mock_logger):
    mock_settings.SCRAPE_SCHEDULE_TIME = "invalid-time"
    with pytest.raises(Exception) as excinfo:
        start_scheduler()
    mock_logger.error.assert_called_with("Failed to start scheduler: not enough values to unpack (expected 2, got 1)")
    assert "not enough values to unpack" in str(excinfo.value)
    mock_scheduler.start.assert_not_called()
