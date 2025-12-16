import pytest
from unittest.mock import MagicMock, patch
from app.core.scraper.service import SeleniumScraperService


@pytest.mark.asyncio
class TestScraperService:

    @patch("app.core.scraper.service.uc.Chrome")
    async def test_start_session_success(self, mock_chrome):
        """Test that the driver initializes correctly."""
        service = SeleniumScraperService()
        result = await service.start_session()

        assert result is True
        assert service._driver is not None
        mock_chrome.assert_called_once()

    @patch("app.core.scraper.service.uc.Chrome")
    async def test_fetch_page_success(self, mock_chrome):
        """Test fetching a page returns HTML content."""
        # Setup Mock Driver
        mock_driver_instance = MagicMock()
        mock_driver_instance.page_source = "<html><body>Success</body></html>"
        mock_driver_instance.window_handles = ["tab1"]
        mock_chrome.return_value = mock_driver_instance

        service = SeleniumScraperService()
        await service.start_session()

        # Run Fetch
        html = await service.fetch_page("http://example.com")

        assert html == "<html><body>Success</body></html>"
        mock_driver_instance.get.assert_called_with("http://example.com")

    async def test_fetch_without_session_fails(self):
        """Test that fetching without starting a session returns None."""
        service = SeleniumScraperService()
        result = await service.fetch_page("http://example.com")
        assert result is None

    @patch("app.core.scraper.service.uc.Chrome")
    async def test_extract_links(self, mock_chrome):
        """Test link extraction via Selenium."""
        mock_driver = MagicMock()
        mock_element = MagicMock()
        mock_element.get_attribute.return_value = "http://example.com/page2"
        mock_driver.find_elements.return_value = [mock_element]
        mock_chrome.return_value = mock_driver

        service = SeleniumScraperService()
        await service.start_session()

        links = await service.extract_links("http://example.com")

        assert "http://example.com/page2" in links