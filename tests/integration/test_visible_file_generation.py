import pytest
import shutil
from pathlib import Path
from app.core.parser.service import WebsiteParserService
from app.core.converter.service import MarkDownConverterService
from app.core.storage.service import FileSystemStorageService
from app.core.config import settings

# 1. Define where input fixtures are (HTML) and where output should go (Markdown)
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "html"
OUTPUT_DIR = Path(__file__).parent.parent / "outputs" / "markdown"


@pytest.mark.asyncio
async def test_convert_html_to_visible_markdown_files(monkeypatch):
    """
    Reads HTML from tests/fixtures/html/
    Converts it to Markdown.
    Saves it to tests/outputs/markdown/ (So you can see it!)
    """

    # 2. Setup: Ensure output dir exists and clean it for a fresh run
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Override the settings to force saving to our local 'tests/outputs' folder
    # instead of the temporary system folder.
    monkeypatch.setattr(settings, "MARKDOWN_STORAGE_PATH", OUTPUT_DIR)

    # 3. Initialize Services
    parser = WebsiteParserService()
    converter = MarkDownConverterService()
    storage = FileSystemStorageService()

    # Verify we have input files
    html_files = list(FIXTURES_DIR.glob("*.html"))
    if not html_files:
        pytest.fail(f"No HTML files found in {FIXTURES_DIR}. Please create 'example_page.html' there first.")

    print(f"\n🚀 Starting Batch Conversion: {len(html_files)} files")
    print(f"📂 Inputs: {FIXTURES_DIR}")
    print(f"📂 Outputs: {OUTPUT_DIR}\n")

    for file_path in html_files:
        print(f"Processing: {file_path.name}...")

        # A. Read HTML
        raw_html = file_path.read_text(encoding="utf-8")

        # B. Parse & Clean
        parsed_data = await parser.parse(raw_html)
        cleaned_data = await parser.clean(parsed_data)

        # C. Convert
        markdown_content = await converter.convert(cleaned_data["cleaned_content"])

        # D. Save (URL is fake, just for filename generation)
        # We use the filename as the URL to keep things traceable
        fake_url = f"https://local-test.com/{file_path.stem}"
        metadata = {
            "original_filename": file_path.name,
            "test_run": "visible_output"
        }

        saved_path_str = await storage.save(fake_url, markdown_content, "md", metadata)
        saved_path = Path(saved_path_str)

        # 4. EXPLICIT ASSERTIONS
        # Check 1: File must exist on disk
        assert saved_path.exists(), f"File {saved_path} was not created!"

        # Check 2: Content verification
        content = saved_path.read_text(encoding="utf-8")
        print(f"   ✅ Saved to: {saved_path.name}")

        # Verify specific content from your 'example_page.html'
        # Adjust these strings based on what is actually inside your HTML fixture
        if "This came from a real file" in raw_html:
            assert "# This came from a real file" in content
            assert "batch conversion" in content

        # Verify cleanup logic (e.g., scripts removed)
        assert "<script>" not in content
        assert "console.log" not in content

    print(f"\n✨ Done! Check the folder '{OUTPUT_DIR}' to see your Markdown files.")