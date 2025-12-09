from dataclasses import dataclass

from app.core.scraper.schemas import WebScraperRequest, WebScraperResponse


@dataclass
class WebScraperInteractor:
    @classmethod
    def create(cls) -> WebScraperInteractor:
        return cls()

    def run_scraping(self, request: WebScraperRequest) -> WebScraperResponse:
        pass