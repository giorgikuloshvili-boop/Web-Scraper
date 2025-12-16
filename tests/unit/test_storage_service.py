import pytest
import json
from pathlib import Path
from app.core.storage.service import FileSystemStorageService
from app.core.config import settings


@pytest.mark.asyncio
class TestStorageService:

    async def test_save_html_file(self):
        service = FileSystemStorageService()
        url = "http://example.com"
        content = "<html>Content</html>"

        # Save
        saved_path = await service.save(url, content, "html")

        # Verify file exists
        file_path = Path(saved_path)
        assert file_path.exists()
        assert file_path.parent == settings.HTML_STORAGE_PATH

        # Verify content
        assert file_path.read_text(encoding="utf-8") == content

    async def test_save_markdown_with_metadata(self):
        service = FileSystemStorageService()
        url = "http://example.com/blog"
        content = "# Blog Post"
        metadata = {"title": "Test Title"}

        saved_path = await service.save(url, content, "md", metadata)

        # Verify Markdown file
        md_path = Path(saved_path)
        assert md_path.exists()
        assert md_path.parent == settings.MARKDOWN_STORAGE_PATH

        # Verify Metadata JSON exists alongside it
        json_path = md_path.parent / (md_path.stem + ".json")
        assert json_path.exists()

        saved_meta = json.loads(json_path.read_text())
        assert saved_meta["title"] == "Test Title"
        assert saved_meta["source_url"] == url

    async def test_get_existing_file(self):
        service = FileSystemStorageService()
        url = "http://read-test.com"
        content = "READ ME"
        await service.save(url, content, "md")

        # Read back
        retrieved_content = await service.get(url, "md")
        assert retrieved_content == content

    async def test_get_non_existent_file_returns_none(self):
        service = FileSystemStorageService()
        result = await service.get("http://fake.com", "html")
        assert result is None