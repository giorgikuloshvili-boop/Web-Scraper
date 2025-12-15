import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Set, List, Dict, Any
from urllib.parse import urlparse

from app.core.config import settings
from app.core.converter.service import MarkDownConverterService, IConverterService
from app.core.parser.service import WebsiteParserService, IParserService
from app.core.schemas import WebScraperRequest
from app.core.scraper.service import IScraperService, SeleniumScraperService
from app.core.storage.service import FileSystemStorageService, IStorageService

logger = logging.getLogger(__name__)


@dataclass
class WebScraperInteractor:
    scraper: IScraperService
    parser: IParserService
    converter: IConverterService
    storage: IStorageService
    semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_REQUESTS)

    @classmethod
    def create(cls) -> "WebScraperInteractor":
        return cls(
            scraper=SeleniumScraperService(),
            parser=WebsiteParserService(),
            converter=MarkDownConverterService(),
            storage=FileSystemStorageService(),
        )

    async def run_scraping(self, request: WebScraperRequest) -> Dict[str, Any]:
        start_time = time.time()
        start_url = str(request.url) if request.url else settings.TARGET_URL

        logger.info(
            f"Starting Scraper Job | Target: {start_url} | "
            f"Max Depth: {settings.MAX_CRAWL_DEPTH} | "
            f"Concurrency: {settings.MAX_CONCURRENT_REQUESTS}"
        )

        if not await self.scraper.start_session():
            logger.error(f"Critical: Failed to start browser session for {start_url}")
            return {"error": f"Failed to start scraper for {request.url}"}

        stats: Dict[str, Any] = {"processed": 0, "failed": 0, "errors": []}
        visited_urls: Set[str] = set()
        to_visit: List[tuple[str, int]] = [(start_url, 0)]
        base_domain = urlparse(start_url).netloc

        try:
            while to_visit:
                current_batch: List[tuple[str, int]] = []
                while to_visit and len(current_batch) < settings.MAX_CONCURRENT_REQUESTS:
                    url, depth = to_visit.pop(0)
                    if url not in visited_urls:
                        visited_urls.add(url)
                        current_batch.append((url, depth))

                if not current_batch:
                    break

                logger.info(f"Processing Batch: {len(current_batch)} URLs | Queue Size: {len(to_visit)}")

                tasks = [
                    self._process_url_pipeline(
                        url, depth, settings.MAX_CRAWL_DEPTH, to_visit, visited_urls, stats, base_domain
                    )
                    for url, depth in current_batch
                ]

                await asyncio.gather(*tasks)

        except Exception as e:
            logger.exception("Critical Core Error during execution")
            stats["errors"].append(str(e))
        finally:
            await self.scraper.stop_session()

            duration = time.time() - start_time
            processed = int(stats['processed'])
            speed = processed / duration if duration > 0 else 0

            logger.info(
                f"Job Finished | Duration: {duration:.2f}s | "
                f"Processed: {processed} | Failed: {stats['failed']} | "
                f"Speed: {speed:.2f} pages/sec | "
                f"Total Errors: {len(stats['errors'])}"
            )

        return stats

    async def _process_url_pipeline(
            self,
            url: str,
            depth: int,
            max_depth: int,
            to_visit: List[tuple[str, int]],
            visited_urls: Set[str],
            stats: Dict[str, Any],
            base_domain: str,
    ) -> None:
        async with self.semaphore:
            try:
                html = await self.scraper.fetch_page(url)
                if not html:
                    logger.warning(f"Empty HTML received for {url}")
                    stats["failed"] += 1
                    return

                await self.storage.save(url, html, "html")

                parsed_data = await self.parser.parse(html)
                cleaned_data = await self.parser.clean(parsed_data)

                content = cleaned_data.get("cleaned_content", "")
                if not content:
                    logger.warning(f"Content empty after cleaning for {url}")

                markdown_content = await self.converter.convert(content)

                metadata = {
                    "title": cleaned_data.get("title"),
                    "depth": depth,
                    "crawled_at": time.time()
                }

                await self.storage.save(url, markdown_content, "md", metadata)
                stats["processed"] += 1

                links_found = 0
                if depth < max_depth:
                    links = await self.parser.extract_links(html, url, base_domain)
                    links_found = len(links)

                    new_links = 0
                    for link in links:
                        if link not in visited_urls:
                            to_visit.append((link, depth + 1))
                            new_links += 1

                    logger.debug(f"{url}: Found {links_found} links ({new_links} new)")

                logger.info(f"Pipeline OK: {url} (Depth: {depth}, Links: {links_found})")

            except Exception as e:
                logger.error(f"Pipeline failed for {url}: {e}", exc_info=True)
                stats["errors"].append(f"{url}: {str(e)}")