import pytest
from pathlib import Path
from app.core.parser.service import WebsiteParserService
from app.core.converter.service import MarkDownConverterService
from app.core.storage.service import FileSystemStorageService

# Define where our source files are
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "html"


@pytest.mark.asyncio
async def test_convert_all_html_files_in_directory(tmp_path, mock_settings):
    """
    Real-world scenario:
    1. Read all .html files from 'tests/fixtures/html'
    2. Convert them to Markdown
    3. Save them to the test output directory
    """

    # 1. Setup Services
    parser = WebsiteParserService()
    converter = MarkDownConverterService()
    storage = FileSystemStorageService()

    # Ensure our source directory exists and has files
    if not FIXTURES_DIR.exists():
        pytest.fail(f"Test fixtures directory not found: {FIXTURES_DIR}")

    html_files = list(FIXTURES_DIR.glob("*.html"))
    if not html_files:
        pytest.fail("No .html files found in fixtures directory to test with.")

    print(f"\nProcessing {len(html_files)} files from {FIXTURES_DIR}...")

    for file_path in html_files:
        # 2. Read the actual file content
        raw_html = file_path.read_text(encoding="utf-8")

        # 3. Process: Parse -> Clean -> Convert
        parsed_data = await parser.parse(raw_html)
        cleaned_data = await parser.clean(parsed_data)
        markdown_content = await converter.convert(cleaned_data["cleaned_content"])

        # 4. Save to output (Storage Service)
        # We use the original filename as the 'url' to keep track
        fake_url = f"file://{file_path.name}"
        metadata = {"original_filename": file_path.name, "source": "test_fixture"}

        saved_path_str = await storage.save(fake_url, markdown_content, "md", metadata)
        saved_path = Path(saved_path_str)

        # 5. Verify the output file
        assert saved_path.exists()
        assert saved_path.suffix == ".md"

        # Check Content Logic
        content = saved_path.read_text(encoding="utf-8")
        assert "# This came from a real file" in content
        assert "batch conversion" in content
        assert "<script>" not in content  # Parser should have removed this
        assert "<nav>" not in content  # Parser should have removed this

        print(f"✅ Converted {file_path.name} -> {saved_path.name}")