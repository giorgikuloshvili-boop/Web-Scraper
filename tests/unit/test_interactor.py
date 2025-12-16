import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from app.core.interactor import WebScraperInteractor
from app.core.schemas import WebScraperRequest
from app.core.config import settings
from urllib.parse import urlparse

from app.core.scraper.service import SeleniumScraperService
from app.core.parser.service import WebsiteParserService
from app.core.converter.service import MarkDownConverterService
from app.core.storage.service import FileSystemStorageService

@pytest.fixture
def mock_services(mocker):
    mock_scraper = MagicMock(spec=SeleniumScraperService)
    mock_scraper.start_session = AsyncMock(return_value=True)
    mock_scraper.stop_session = AsyncMock()
    mock_scraper.fetch_page = AsyncMock(return_value="<html>test</html>")
    mock_scraper.extract_links = AsyncMock(return_value=[])

    mock_parser = MagicMock(spec=WebsiteParserService)
    mock_parser.parse = AsyncMock(return_value={"title": "Test Title", "metadata": {"description": "Test Desc"}, "content": "<html>cleaned</html>"})
    mock_parser.clean = AsyncMock(return_value={"title": "Test Title", "metadata": {"description": "Test Desc"}, "cleaned_content": "cleaned content"})
    mock_parser.extract_links = AsyncMock(return_value=[])

    mock_converter = MagicMock(spec=MarkDownConverterService)
    mock_converter.convert = AsyncMock(return_value="# Test Markdown")

    mock_storage = MagicMock(spec=FileSystemStorageService)
    mock_storage.save = AsyncMock(return_value="path/to/file")
    mock_storage.get = AsyncMock(return_value=None)

    mocker.patch.object(settings, "MAX_CRAWL_DEPTH", 1)
    mocker.patch.object(settings, "MAX_CONCURRENT_REQUESTS", 1)
    mocker.patch.object(settings, "TARGET_URL", "https://default.com")

    return {
        "scraper": mock_scraper,
        "parser": mock_parser,
        "converter": mock_converter,
        "storage": mock_storage,
    }

@pytest.fixture
def interactor(mock_services):
    return WebScraperInteractor(
        scraper=mock_services["scraper"],
        parser=mock_services["parser"],
        converter=mock_services["converter"],
        storage=mock_services["storage"],
    )

@pytest.fixture(autouse=True)
def mock_logger(mocker):
    mock_log = MagicMock()
    mocker.patch("app.core.interactor.logger", new=mock_log)
    return mock_log

@pytest.fixture(autouse=True)
def mock_time(mocker):
    mocker.patch("time.time", side_effect=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]) # Simulate time progression


@pytest.mark.asyncio
async def test_create_interactor(mocker):
    mock_selenium_scraper_service = MagicMock(spec=SeleniumScraperService)
    mock_website_parser_service = MagicMock(spec=WebsiteParserService)
    mock_markdown_converter_service = MagicMock(spec=MarkDownConverterService)
    mock_file_system_storage_service = MagicMock(spec=FileSystemStorageService)

    mocker.patch("app.core.interactor.SeleniumScraperService", return_value=mock_selenium_scraper_service)
    mocker.patch("app.core.interactor.WebsiteParserService", return_value=mock_website_parser_service)
    mocker.patch("app.core.interactor.MarkDownConverterService", return_value=mock_markdown_converter_service)
    mocker.patch("app.core.interactor.FileSystemStorageService", return_value=mock_file_system_storage_service)

    interactor_instance = WebScraperInteractor.create()
    assert isinstance(interactor_instance, WebScraperInteractor)
    assert interactor_instance.scraper == mock_selenium_scraper_service
    assert interactor_instance.parser == mock_website_parser_service
    assert interactor_instance.converter == mock_markdown_converter_service
    assert interactor_instance.storage == mock_file_system_storage_service

@pytest.mark.asyncio
async def test_run_scraping_single_page_success(interactor, mock_services, mocker):
    request = WebScraperRequest(url="https://example.com/start")
    stats = await interactor.run_scraping(request)

    mock_services["scraper"].start_session.assert_called_once()
    mock_services["scraper"].fetch_page.assert_called_once_with("https://example.com/start")
    mock_services["storage"].save.assert_any_call("https://example.com/start", "<html>test</html>", "html")
    mock_services["parser"].parse.assert_called_once_with("<html>test</html>")
    mock_services["parser"].clean.assert_called_once_with(mock_services["parser"].parse.return_value)
    mock_services["converter"].convert.assert_called_once_with("cleaned content")

    # Use mocker.ANY for the dynamic 'crawled_at' timestamp
    mock_services["storage"].save.assert_any_call(
        "https://example.com/start", 
        "# Test Markdown", 
        "md", 
        {'title': 'Test Title', 'depth': 0, 'crawled_at': mocker.ANY}
    )
    mock_services["parser"].extract_links.assert_called_once() # Called even if max_depth is 0, but returns empty
    mock_services["scraper"].stop_session.assert_called_once()

    assert stats["processed"] == 1
    assert stats["failed"] == 0
    assert len(stats["errors"]) == 0
    assert stats["duration"] >= 0 # duration is calculated based on mocked time.time, so just check it exists and is non-negative

@pytest.mark.asyncio
async def test_run_scraping_start_session_failure(interactor, mock_services, mock_logger):
    mock_services["scraper"].start_session.return_value = False
    request = WebScraperRequest(url="https://example.com/fail")
    stats = await interactor.run_scraping(request)

    mock_services["scraper"].start_session.assert_called_once()
    mock_services["scraper"].fetch_page.assert_not_called()
    mock_services["scraper"].stop_session.assert_not_called() # Should not call stop_session if start_session fails
    mock_logger.error.assert_called_with("Critical: Failed to start browser session for https://example.com/fail")

    assert stats["processed"] == 0
    assert stats["failed"] == 1
    assert len(stats["errors"]) == 1
    assert "Failed to start scraper for https://example.com/fail" in stats["errors"]
    assert stats["duration"] >= 0

@pytest.mark.asyncio
async def test_process_url_pipeline_empty_html(interactor, mock_services, mock_logger):
    interactor.scraper.fetch_page.return_value = None
    stats = {"processed": 0, "failed": 0, "errors": []}
    to_visit = []
    visited_urls = set()
    
    await interactor._process_url_pipeline("https://example.com/empty", 0, 1, to_visit, visited_urls, stats, "example.com")

    assert stats["failed"] == 1
    mock_logger.warning.assert_called_with("Empty HTML received for https://example.com/empty")
    mock_services["storage"].save.assert_not_called()
    mock_services["parser"].parse.assert_not_called()

@pytest.mark.asyncio
async def test_process_url_pipeline_empty_cleaned_content(interactor, mock_services, mock_logger):
    mock_services["parser"].clean.return_value = {"title": "Test Title", "metadata": {"description": "Test Desc"}, "cleaned_content": ""}
    stats = {"processed": 0, "failed": 0, "errors": []}
    to_visit = []
    visited_urls = set()

    await interactor._process_url_pipeline("https://example.com/empty-clean", 0, 1, to_visit, visited_urls, stats, "example.com")

    assert stats["processed"] == 1 # Still considered processed, but content is empty
    mock_logger.warning.assert_called_with("Content empty after cleaning for https://example.com/empty-clean")
    mock_services["converter"].convert.assert_called_once_with("") # Should attempt to convert empty string

@pytest.mark.asyncio
async def test_process_url_pipeline_with_new_links(interactor, mock_services):
    mock_services["parser"].extract_links.return_value = [
        "https://example.com/page1",
        "https://example.com/page2",
    ]
    stats = {"processed": 0, "failed": 0, "errors": []}
    to_visit = []
    visited_urls = set()

    await interactor._process_url_pipeline("https://example.com/main", 0, 1, to_visit, visited_urls, stats, "example.com")

    assert stats["processed"] == 1
    assert len(to_visit) == 2 # page1 and page2 should be added once
    assert ("https://example.com/page1", 1) in to_visit
    assert ("https://example.com/page2", 1) in to_visit
    mock_services["parser"].extract_links.assert_called_once()

@pytest.mark.asyncio
async def test_process_url_pipeline_exception_handling(interactor, mock_services, mock_logger):
    mock_services["scraper"].fetch_page.side_effect = Exception("Scraper error")
    stats = {"processed": 0, "failed": 0, "errors": []}
    to_visit = []
    visited_urls = set()

    await interactor._process_url_pipeline("https://example.com/error", 0, 1, to_visit, visited_urls, stats, "example.com")

    assert stats["failed"] == 0 # Pipeline errors don't increment failed, but add to errors list
    assert "https://example.com/error: Scraper error" in stats["errors"][0]
    mock_logger.error.assert_called_with(f"Pipeline failed for https://example.com/error: Scraper error", exc_info=True)

@pytest.mark.asyncio
async def test_run_scraping_multiple_pages_and_depth(interactor, mock_services, mocker):
    # Override settings for this specific test
    mocker.patch.object(settings, "MAX_CRAWL_DEPTH", 1)
    mocker.patch.object(settings, "MAX_CONCURRENT_REQUESTS", 2)

    # Simulate multiple pages and link extraction
    # First page (depth 0) links to page1 and page2 (depth 1)
    mock_services["scraper"].fetch_page.side_effect = [
        "<html>start</html>", # For start_url
        "<html>page1</html>",  # For page1
        "<html>page2</html>"   # For page2
    ]
    mock_services["parser"].extract_links.side_effect = [
        ["https://example.com/page1", "https://example.com/page2"], # From start_url
        [], # From page1
        []  # From page2
    ]
    # Mock save and parse/clean/convert results
    mock_services["parser"].parse.side_effect = [
        {"title": "Start", "metadata": {}, "content": "<html>start</html>"},
        {"title": "Page 1", "metadata": {}, "content": "<html>page1</html>"},
        {"title": "Page 2", "metadata": {}, "content": "<html>page2</html>"},
    ]
    mock_services["parser"].clean.side_effect = [
        {"title": "Start", "metadata": {}, "cleaned_content": "start content"},
        {"title": "Page 1", "metadata": {}, "cleaned_content": "page1 content"},
        {"title": "Page 2", "metadata": {}, "cleaned_content": "page2 content"},
    ]
    mock_services["converter"].convert.side_effect = [
        "# Start Markdown",
        "# Page 1 Markdown",
        "# Page 2 Markdown",
    ]
    
    request = WebScraperRequest(url="https://example.com/start")
    stats = await interactor.run_scraping(request)

    assert stats["processed"] == 3
    assert stats["failed"] == 0
    assert len(stats["errors"]) == 0
    assert mock_services["scraper"].fetch_page.call_count == 3
    assert mock_services["storage"].save.call_count == 6 # 3 HTML + 3 MD
    assert mock_services["scraper"].stop_session.call_count == 1


