import pytest
from app.core.parser.service import WebsiteParserService
from app.core.parser.exceptions import ParsingException


@pytest.mark.asyncio
class TestParserService:

    async def test_parse_valid_html(self, sample_html_content):
        service = WebsiteParserService()
        result = await service.parse(sample_html_content)

        assert result["title"] == "Test Page"
        assert "content" in result

    async def test_clean_removes_noise(self, sample_html_content):
        service = WebsiteParserService()
        parsed = await service.parse(sample_html_content)
        cleaned = await service.clean(parsed)

        content = cleaned["cleaned_content"]

        # Check that noise is removed
        assert "<script>" not in content
        assert "header" not in content
        assert "footer" not in content

        # Check that content remains
        assert "Main Title" in content

    async def test_extract_links(self, sample_html_content):
        service = WebsiteParserService()
        base_url = "https://example.com"

        links = await service.extract_links(sample_html_content, base_url, "example.com")

        assert len(links) == 1
        assert links[0] == "https://example.com/about"

    async def test_parse_empty_html_raises_error(self):
        service = WebsiteParserService()
        with pytest.raises(ParsingException):
            await service.parse("")