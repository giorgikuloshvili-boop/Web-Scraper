import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from app.core.interactor import WebScraperInteractor
from app.core.schemas import WebScraperRequest


@pytest.mark.asyncio
async def test_full_scraping_pipeline_success():
    """
    Simulates a full run:
    1. Scraper fetches HTML.
    2. Storage saves HTML.
    3. Parser extracts links.
    4. Converter creates Markdown.
    5. Storage saves Markdown.
    """

    # --- Mocks ---
    mock_scraper = MagicMock()
    mock_scraper.start_session = AsyncMock(return_value=True)
    mock_scraper.stop_session = AsyncMock()
    mock_scraper.fetch_page = AsyncMock(return_value="<html><a href='/page2'>Link</a></html>")

    # Mock Parser to return links on first call, then empty on second to stop recursion
    mock_parser = MagicMock()
    mock_parser.parse = AsyncMock(return_value={"title": "Test", "content": "<html>...</html>"})
    mock_parser.clean = AsyncMock(return_value={"cleaned_content": "Clean HTML", "title": "Test"})
    mock_parser.extract_links = AsyncMock(side_effect=[
        ["http://example.com/page2"],  # First page finds one link
        []  # Second page finds no links
    ])

    mock_converter = MagicMock()
    mock_converter.convert = AsyncMock(return_value="# Markdown Content")

    mock_storage = MagicMock()
    mock_storage.save = AsyncMock()

    # --- Inject Mocks into Interactor ---
    interactor = WebScraperInteractor(
        scraper=mock_scraper,
        parser=mock_parser,
        converter=mock_converter,
        storage=mock_storage
    )

    # --- Run ---
    request = WebScraperRequest(url="http://example.com")
    stats = await interactor.run_scraping(request)

    # --- Assertions ---

    # 1. Check Stats
    assert stats["processed"] >= 1
    assert stats["failed"] == 0
    assert len(stats["errors"]) == 0

    # 2. Check Scraper Usage
    mock_scraper.start_session.assert_called_once()
    assert mock_scraper.fetch_page.call_count >= 1
    mock_scraper.stop_session.assert_called_once()

    # 3. Check Storage Usage (HTML + Markdown)
    # We expect save to be called twice per page (HTML + MD)
    assert mock_storage.save.call_count >= 2

    # Check that it actually tried to save markdown
    call_args_list = mock_storage.save.call_args_list
    extensions = [call.args[2] for call in call_args_list]  # 3rd arg is extension
    assert "md" in extensions
    assert "html" in extensions


@pytest.mark.asyncio
async def test_pipeline_handles_scraper_failure():
    """Test that if scraper fails to start, we exit gracefully."""
    mock_scraper = MagicMock()
    mock_scraper.start_session = AsyncMock(return_value=False)  # Fail start

    interactor = WebScraperInteractor(
        scraper=mock_scraper,
        parser=MagicMock(),
        converter=MagicMock(),
        storage=MagicMock()
    )

    stats = await interactor.run_scraping(WebScraperRequest(url="http://fail.com"))

    assert stats["failed"] == 1
    assert "Failed to start scraper" in stats["errors"][0]