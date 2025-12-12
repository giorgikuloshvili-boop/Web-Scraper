import asyncio
import logging
from dataclasses import dataclass
from typing import Set, List
from urllib.parse import urlparse, urljoin

from app.core.config import settings
from app.core.converter.service import MarkDownConverterService, IConverterService
from app.core.parser.service import WebsiteParserService, IParserService
from app.core.schemas import WebScraperRequest, WebScraperResponse
from app.core.scraper.service import IScraperService, SeleniumScraperService
from app.core.storage.service import FileSystemStorageService, IStorageService

logger = logging.getLogger(__name__)

@dataclass
class WebScraperInteractor:
    scraper: IScraperService
    parser: IParserService
    converter: IConverterService
    storage: IStorageService
    semaphore = asyncio.Semaphore(5)

    @classmethod
    def create(cls) -> WebScraperInteractor:
        return cls(
            scraper=SeleniumScraperService(),
            parser=WebsiteParserService(),
            converter=MarkDownConverterService(),
            storage=FileSystemStorageService(),
        )

    async def run_scraping(self, request: WebScraperRequest) -> dict:
        start_url = str(request.url) if request.url else settings.TARGET_URL
        logger.info(f"Running scraper for {request.url}")

        if not await self.scraper.start_session():
            return {"error": f"Failed to start scraper for {request.url}"}

        stats = {"processed": 0, "failed": 0, "errors": []}
        visited_urls: Set[str] = set()
        to_visit: List[tuple[str, int]] = [(start_url, 0)]
        base_domain = urlparse(start_url).netloc

        try:
            while to_visit:
                current_batch = []
                while to_visit and len(current_batch) < 5:     #Todo
                    url, depth = to_visit.pop(0)
                    if url not in visited_urls:
                        visited_urls.add(url)
                        current_batch.append((url, depth))

                if not current_batch:
                    break

                logger.info(f"Processing batch of {len(current_batch)} URLs")

                tasks = [
                    self._process_url_pipeline(
                        url, depth, 3, to_visit, visited_urls, stats, base_domain
                    )
                    for url, depth in current_batch
                ]

                await asyncio.gather(*tasks)

        except Exception as e:
            logger.error(f"Core run error: {e}")
            stats["errors"].append(str(e))
        finally:
            await self.scraper.stop_session()
            logger.info(f"Core finished. Stats: {stats}")

        return stats



    async def _process_url_pipeline(
            self,
            url: str,
            depth: int,
            max_depth: int,
            to_visit: list,
            visited_urls: set,
            stats: dict,
            base_domain: str,
    ) -> None:
        async with self.semaphore:
            try:
                # if depth < max_depth:
                #     links = await self.scraper.extract_links(url)
                #     for link in links:
                #         if link not in visited_urls:
                #             to_visit.append((link, depth + 1))

                html = await self.scraper.fetch_page(url)
                if not html:
                    stats["failed"] += 1
                    return

                await self.storage.save(url, html, "html")

                parsed_data = await self.parser.parse(html)
                cleaned_data = await self.parser.clean(parsed_data)

                markdown_content = await self.converter.convert(cleaned_data.get("cleaned_content", ""))

                metadata = {
                    "title": cleaned_data.get("title"),
                    "depth": depth,
                    "crawled_at": 0
                }

                await self.storage.save(url, markdown_content, "md", metadata)
                stats["processed"] += 1

                if depth < max_depth:
                    links = self._extract_links_from_html(html, url, base_domain)
                    for link in links:
                        if link not in visited_urls:
                            to_visit.append((link, depth + 1))

                logger.info(f"Pipeline completed for: {url}")

            except Exception as e:
                logger.error(f"Pipeline error for {url}: {e}")
                stats["errors"].append(f"{url}: {str(e)}")


    def _extract_links_from_html(self, html: str, current_url: str, base_domain: str) -> List[str]:
        """
        Helper to extract links using BS4 (Lightweight, doesn't need Selenium driver).
        """
        from bs4 import BeautifulSoup
        valid_links = []
        try:
            soup = BeautifulSoup(html, "html.parser")
            for a in soup.find_all("a", href=True):
                href = a["href"]
                full_url = urljoin(current_url, href)
                parsed = urlparse(full_url)
                # Cleanup
                full_url = full_url.split("#")[0].rstrip("/")

                if parsed.netloc == base_domain and parsed.scheme in ["http", "https"]:
                    valid_links.append(full_url)
        except Exception:
            pass
        return valid_links