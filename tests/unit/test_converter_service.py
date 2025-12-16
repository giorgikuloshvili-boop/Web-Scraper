import pytest
from app.core.converter.service import MarkDownConverterService


@pytest.mark.asyncio
async def test_convert_html_to_markdown():
    service = MarkDownConverterService()
    html = "<h1>Hello World</h1><p>This is a test.</p>"

    md = await service.convert(html)

    # Assert Markdown syntax
    assert "# Hello World" in md
    assert "This is a test." in md
    # Ensure excessive newlines are cleaned (from your _clean_whitespace logic)
    assert "\n\n\n" not in md