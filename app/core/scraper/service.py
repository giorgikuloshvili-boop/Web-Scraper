import asyncio
import logging
import time
from threading import Lock
from typing import List, Optional, Protocol

import undetected_chromedriver as uc
from selenium.common import WebDriverException
from selenium.webdriver import ChromeOptions
from selenium.webdriver.common.by import By

from app.core.config import settings

logger = logging.getLogger(__name__)


class IScraperService(Protocol):
    """
    Interface for scraper services.
    Designed to support implementation using all modules
    """

    async def start_session(self) -> bool:
        pass

    async def stop_session(self) -> None:
        pass

    async def fetch_page(self, url: str) -> Optional[str]:
        pass

    async def extract_links(self, url: str) -> List[str]:
        pass


class SeleniumScraperService(IScraperService):
    """
    Service responsible ONLY for Browser Automation.
    It exposes async methods that internally handle the blocking Selenium operations.
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

    def __init__(self) -> None:
        self._driver: Optional[uc.Chrome] = None
        self._driver_lock = Lock()

    async def start_session(self) -> bool:
        """Async wrapper to initialize the browser."""
        return await asyncio.to_thread(self._init_driver_sync)

    async def stop_session(self) -> None:
        """Async wrapper to quit the browser."""
        await asyncio.to_thread(self._quit_driver_sync)

    async def fetch_page(self, url: str) -> Optional[str]:
        """Async wrapper for the complex tab-management logic."""
        return await asyncio.to_thread(self._fetch_page_sync, url)

    async def extract_links(self, url: str) -> List[str]:
        """Async wrapper to extract links."""
        return await asyncio.to_thread(self._extract_links_sync, url)


    def _init_driver_sync(self) -> bool:
        try:
            if self._driver:
                logger.debug("Driver already initialized, skipping.")
                return True

            logger.info("Initializing Chrome Driver...")
            start_time = time.time()

            options = ChromeOptions()
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-popup-blocking")
            options.add_argument("--window-size=800,800")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-extensions")
            options.page_load_strategy = "eager"

            self._driver = uc.Chrome(
                options=options,
                use_subprocess=True,
                version_main=142
            )

            self._driver.set_page_load_timeout(settings.REQUEST_TIMEOUT)

            duration = time.time() - start_time
            logger.info(f"Driver initialized successfully in {duration:.2f}s")
            return True

        except Exception as e:
            logger.error(f"Failed to init driver: {e}", exc_info=True)
            return False

    def _quit_driver_sync(self) -> None:
        if self._driver:
            logger.info("Closing Chrome driver...")
            try:
                self._driver.quit()
                logger.info("Driver closed.")
            except WebDriverException:
                pass
            except Exception as e:
                logger.warning(f"Unexpected error closing driver: {e}", exc_info=True)
            self._driver = None
        else:
            logger.debug("Quit called but driver was None.")

    def _fetch_page_sync(self, url: str) -> Optional[str]:
        """
        Opens a tab, navigates, checks for blockers, returns HTML, closes tab.
        Protected by locks.
        """
        if not self._driver:
            logger.error("Attempted to fetch page with no active driver.")
            return None

        window_handle = None
        html_content = None
        start_time = time.time()

        try:
            with self._driver_lock:
                logger.debug(f"Opening new tab for: {url}")
                self._driver.execute_script("window.open('');")
                time.sleep(0.2)

                window_handle = self._driver.window_handles[-1]
                self._driver.switch_to.window(window_handle)

                logger.info(f"Navigating to: {url}")
                self._driver.get(url)

            html_content = self._wait_for_load_sync(window_handle)

            if html_content:
                duration = time.time() - start_time
                size_kb = len(html_content) / 1024
                logger.info(f"Fetched {url} in {duration:.2f}s (Size: {size_kb:.1f} KB)")
            else:
                logger.warning(f"Fetched {url} but content was empty or blocked.")

        except Exception as e:
            logger.warning(f"Fetch failed for {url}: {e}", exc_info=True)
        finally:
            try:
                with self._driver_lock:
                    if window_handle and window_handle in self._driver.window_handles:
                        logger.debug(f"Closing tab for: {url}")
                        self._driver.switch_to.window(window_handle)
                        self._driver.close()

                        if len(self._driver.window_handles) > 0:
                            self._driver.switch_to.window(self._driver.window_handles[0])
            except WebDriverException:
                pass
            except Exception as e:
                logger.error(f"Error cleaning up tab for {url}: {e}", exc_info=True)

        return html_content

    def _wait_for_load_sync(self, window_handle: str) -> Optional[str]:
        try:
            time.sleep(1.0)

            with self._driver_lock:
                self._driver.switch_to.window(window_handle)
                html = self._driver.page_source

            attempts = 0
            while any(ind in html for ind in self.BLOCK_INDICATORS) and attempts < 5:
                logger.debug(f"Potential blocker detected. waiting... (Attempt {attempts + 1}/5)")
                time.sleep(1.0)
                with self._driver_lock:
                    self._driver.switch_to.window(window_handle)
                    html = self._driver.page_source
                attempts += 1

            for indicator in self.BLOCK_INDICATORS:
                if indicator in html:
                    logger.warning(f"Access Denied/Blocked by '{indicator}' on current page.")
                    return None

            return html

        except WebDriverException as e:
            logger.warning(f"WebDriver error during wait: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in wait_for_load: {e}", exc_info=True)
            return None

    def _extract_links_sync(self, url: str) -> List[str]:
        """
        Uses the driver to find links.
        WARNING: Relies on driver state. Best used with parser service instead.
        """
        target_links = set()
        if not self._driver:
            return []

        try:
            with self._driver_lock:
                logger.debug("Extracting links via Selenium from current page...")
                elements = self._driver.find_elements(By.TAG_NAME, "a")

                for link in elements:
                    try:
                        href = link.get_attribute("href")
                        if href and url in href:
                            clean_url = href.split("#")[0].rstrip("/")
                            target_links.add(clean_url)
                    except WebDriverException:
                        continue
                    except Exception as e:
                        logger.warning(f"Error parsing specific link: {e}")
                        continue

            logger.info(f"Extracted {len(target_links)} valid links from DOM.")

        except Exception as e:
            logger.error(f"Link extraction failed: {e}", exc_info=True)

        return list(target_links)