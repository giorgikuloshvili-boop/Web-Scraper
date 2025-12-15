import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings
from app.core.interactor import WebScraperInteractor
from app.core.schemas import WebScraperRequest

logger = logging.getLogger(__name__)

# global scheduler instance
scheduler = AsyncIOScheduler()


async def scheduled_scrape_job() -> None:
    """
    The job function to be executed by the scheduler.
    It creates a fresh scraper instance and runs the job for the target URL.
    """
    logger.info("Starting scheduled daily scrape job...")
    try:
        scraper = WebScraperInteractor.create()

        stats = await scraper.run_scraping(WebScraperRequest(url=settings.TARGET_URL))

        logger.info(f"Scheduled scrape completed. Stats: {stats}")

    except Exception as e:
        logger.error(f"Scheduled scrape job failed: {e}", exc_info=True)


def start_scheduler() -> None:
    """
    Initialize and start the scheduler.
    Parses the SCRAPE_SCHEDULE_TIME (HH:MM) from settings.
    """
    try:
        hour, minute = settings.SCRAPE_SCHEDULE_TIME.split(":")

        scheduler.add_job(
            scheduled_scrape_job,
            CronTrigger(hour=hour, minute=minute, timezone=settings.TIMEZONE),
            id="daily_scrape",
            replace_existing=True
        )

        scheduler.start()
        logger.info(f"Scheduler started. Next run at: {settings.SCRAPE_SCHEDULE_TIME} ({settings.TIMEZONE})")

    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")
        raise


def shutdown_scheduler() -> None:
    """Gracefully shut down the scheduler."""
    logger.info("Shutting down scheduler...")
    scheduler.shutdown()