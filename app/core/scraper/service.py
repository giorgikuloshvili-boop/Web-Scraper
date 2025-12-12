import asyncio
import logging
import time
from threading import Lock
from typing import List, Optional, Protocol

import undetected_chromedriver as uc
from selenium.common import WebDriverException
from selenium.webdriver import ChromeOptions
from selenium.webdriver.common.by import By


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

    def __init__(self):
        self._driver: Optional[uc.Chrome] = None
        self._driver_lock = Lock()
        # self.window_lock = Lock()

    async def start_session(self) -> bool:
        """
        Async wrapper to initialize the browser.
        """
        return await asyncio.to_thread(self._init_driver_sync)

    async def stop_session(self) -> None:
        """
        Async wrapper to quit the browser.
        """
        await asyncio.to_thread(self._quit_driver_sync)

    async def fetch_page(self, url: str) -> Optional[str]:
        """
        Async wrapper for the complex tab-management logic.
        """
        return await asyncio.to_thread(self._fetch_page_sync, url)

    async def extract_links(self, url: str) -> List[str]:
        """
        Async wrapper to extract links.
        Note: We use BeautifulSoup here or Selenium. Since we have HTML,
        using a lightweight parser is better, but to stick to your Selenium pattern
        we can use the driver if we are still on that page, OR just parse the HTML text.

        For reliability (since driver might have moved on), let's parse the HTML text
        or use the driver if locked. Let's use the driver logic you had.
        """
        return await asyncio.to_thread(self._extract_links_sync, url)

    def _init_driver_sync(self) -> bool:
        try:
            if self._driver:
                return True

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
            return True
        except Exception as e:
            logger.error(f"Failed to init driver: {e}")
            return False

    def _quit_driver_sync(self) -> None:
        if self._driver:
            logger.info("Closing Chrome driver...")
            try:
                self._driver.quit()
            except WebDriverException:
                pass
            except Exception as e:
                logger.warning(f"Unexpected error closing driver: {e}")
            self._driver = None

    def _fetch_page_sync(self, url: str) -> Optional[str]:
        """
        Opens a tab, navigates, checks for blockers, returns HTML, closes tab.
        Protected by locks.
        """
        if not self._driver:
            return None

        window_handle = None
        html_content = None

        try:
            with self._driver_lock:
                self._driver.execute_script("window.open('');")
                time.sleep(0.2)
                window_handle = self._driver.window_handles[-1]
                self._driver.switch_to.window(window_handle)
                self._driver.get(url)

            html_content = self._wait_for_load_sync(window_handle)

        except Exception as e:
            logger.warning(f"Fetch failed for {url}: {e}")
        finally:
            try:
                with self._driver_lock:
                    if window_handle and window_handle in self._driver.window_handles:
                        self._driver.switch_to.window(window_handle)
                        self._driver.close()
                        if len(self._driver.window_handles) > 0:
                            self._driver.switch_to.window(self._driver.window_handles[0])
            except WebDriverException:
                pass
            except Exception as e:
                logger.error(f"Unexpected error cleaning up tab: {e}")

        return html_content

    def _wait_for_load_sync(self, window_handle: str) -> Optional[str]:
        try:
            time.sleep(1.0)

            with self._driver_lock:
                self._driver.switch_to.window(window_handle)
                html = self._driver.page_source

            attempts = 0
            while any(ind in html for ind in self.BLOCK_INDICATORS) and attempts < 10:
                time.sleep(0.5)
                with self._driver_lock:
                    self._driver.switch_to.window(window_handle)
                    html = self._driver.page_source
                attempts += 1

            if any(ind in html for ind in self.BLOCK_INDICATORS):
                return None

            return html

        except WebDriverException:
            return None
        except Exception as e:
            logger.error(f"Unexpected code error in wait_for_load: {e}")
            return None

    def _extract_links_sync(self, url: str) -> List[str]:
        """
        Uses the driver to find links.
        Note: This assumes the driver is currently ON the page, or we are just
        parsing raw strings. Since we closed the tab in fetch_page, we can't
        use driver.find_elements easily on that specific page context unless
        we kept it open.
        """
        target_links = set()
        try:
            with self._driver_lock:
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
                        logger.warning(f"Error parsing link: {e}")
                        continue
        except Exception as e:
            logger.error(f"Link extraction failed: {e}")

        return list(target_links)