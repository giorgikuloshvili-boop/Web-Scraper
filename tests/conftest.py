import pytest
import shutil
from pathlib import Path
from typing import AsyncGenerator, Generator
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from app.runner.setup import setup
from app.core.config import settings

# 1. Mock Settings to use a temporary directory
@pytest.fixture(scope="session", autouse=True)
def mock_settings(tmp_path_factory):
    """
    Override settings to use a temporary directory for file storage
    during tests. This prevents creating junk files in your real project.
    """
    temp_dir = tmp_path_factory.mktemp("data")
    settings.BASE_DIR = temp_dir
    settings.HTML_STORAGE_PATH = temp_dir / "storage/html"
    settings.MARKDOWN_STORAGE_PATH = temp_dir / "storage/markdown"
    settings.create_dirs()
    return settings

# 2. Async Client for API Tests
@pytest.fixture(scope="module")
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    app = setup()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

# 3. Sample HTML Data fixture
@pytest.fixture
def sample_html_content() -> str:
    return """
    <html>
        <head><title>Test Page</title></head>
        <body>
            <header>Header Content</header>
            <main>
                <h1>Main Title</h1>
                <p>Some useful text.</p>
                <script>console.log('noise');</script>
                <a href="/about">About Us</a>
            </main>
            <footer>Footer Content</footer>
        </body>
    </html>
    """