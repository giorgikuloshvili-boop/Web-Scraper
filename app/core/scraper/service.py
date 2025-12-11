import logging
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from typing import Set, List, Optional, Callable, Any
from urllib.parse import urlparse

# Selenium & Undetected Chromedriver
import undetected_chromedriver as uc
from selenium.webdriver import ChromeOptions
from selenium.webdriver.common.by import By

logger = logging.getLogger(__name__)

class ScraperService:
    """
        Pure Scraper Service.
        Responsibility: Browser Automation, Navigation, Link Discovery.
    """
    BLOCK_INDICATORS = [
        "Enable JavaScript",
        "Access denied",
        "403 Forbidden",
        "Please enable JavaScript",
        "Checking your browser",
        "Just a moment",
        "Cloudflare",
        "Verify you are human"
    ]

    def __init__(self):
        self.max_workers = 5
        self.max_retries = 1

        self.driver_lock = Lock()
        self.visited_lock = Lock()
        self.progress_lock = Lock()


    async def scrape_website(
            self,
            start_url: str,
            max_depth: int,
            data_handler: Callable[[str, str, int, dict], Any]
    ) -> dict:
        """
        Async entry point.

        Args:
            start_url: Target URL
            max_depth: Crawl depth
            data_handler: Callback function (url, html, depth, stats) -> None
                         This is called when HTML is successfully fetched.
        """
        logger.info(f"Starting Scrape for {start_url}")

        # Run blocking sync logic in a separate thread
        stats = await asyncio.to_thread(
            self._scrape_sync_logic,
            start_url,
            max_depth,
            data_handler
        )
        return stats

    def _scrape_sync_logic(
            self,
            start_url: str,
            max_depth: int,
            data_handler: Callable[[str, str, int, dict], Any]
    ) -> dict:
        stats = {"processed": 0, "failed": 0, "errors": []}
        visited_urls = set()

        driver = self._init_driver()
        if not driver:
            stats["errors"].append("Failed to initialize driver")
            return stats



    def _init_driver(self) -> Optional[uc.Chrome]:
        try:
            options = ChromeOptions()
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-popup-blocking")
            options.add_argument("--window-size=800,800")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-extensions")
            options.page_load_strategy = "eager"

            driver = uc.Chrome(
                options=options,
                use_subprocess=True,
                version_main=142
            )
            return driver
        except Exception as e:
            logger.error(f"Failed to init driver: {e}")
            return None