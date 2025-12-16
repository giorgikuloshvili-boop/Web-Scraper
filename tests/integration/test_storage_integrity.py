import pytest
import json
import shutil
from pathlib import Path
from app.core.storage.service import FileSystemStorageService
from app.core.storage.exceptions import StorageException


@pytest.mark.asyncio
async def test_storage_writes_and_reads_complex_content(tmp_path):
    """
    Verifies that the storage service creates physical files and
    handles content integrity (UTF-8, special chars).
    """
    service = FileSystemStorageService()

    # Test Data with Emojis and Special Chars
    url = "https://complex-data.com/🚀"
    original_content = "# Header 🚀\n\nText with symbols: ©, ®, €."

    # 1. Write File
    saved_path_str = await service.save(url, original_content, "md")
    saved_path = Path(saved_path_str)

    # 2. Verify Physical Existence
    assert saved_path.exists(), "File was not physically created on disk"
    assert saved_path.is_file()

    # 3. Verify Content Integrity (Read directly from disk)
    disk_content = saved_path.read_text(encoding="utf-8")
    assert disk_content == original_content
    assert "🚀" in disk_content


@pytest.mark.asyncio
async def test_storage_metadata_creation(tmp_path):
    """
    Verifies that saving a file with metadata actually creates the sidecar .json file.
    """
    service = FileSystemStorageService()
    url = "https://metadata-test.com"
    content = "Just some content"
    metadata = {
        "author": "Tester",
        "tags": ["python", "pytest"],
        "nested": {"key": "value"}
    }

    # 1. Save
    saved_path_str = await service.save(url, content, "md", metadata)
    md_path = Path(saved_path_str)

    # 2. Locate Expected JSON file
    # If file is hash.md, json should be hash.json
    json_path = md_path.with_suffix(".json")

    assert json_path.exists(), "Metadata JSON sidecar was not created"

    # 3. Verify JSON Content
    loaded_meta = json.loads(json_path.read_text(encoding="utf-8"))
    assert loaded_meta["author"] == "Tester"
    assert "python" in loaded_meta["tags"]
    assert loaded_meta["source_url"] == url  # Service adds this automatically


@pytest.mark.asyncio
async def test_storage_handles_write_permissions(tmp_path, mock_settings, monkeypatch):
    """
    Verifies that the service raises a StorageException if it cannot write to the disk.
    (Simulates a Permission Denied error).
    """
    service = FileSystemStorageService()

    # Create a read-only directory
    read_only_dir = tmp_path / "readonly"
    read_only_dir.mkdir()

    # Mock settings to point to this read-only dir
    # (We use monkeypatch to safely change the setting for just this test)
    monkeypatch.setattr(mock_settings, "MARKDOWN_STORAGE_PATH", read_only_dir)

    # Remove write permissions from the folder (chmod 444)
    # Note: This might not work perfectly on Windows, but works on Linux/Mac
    import os
    os.chmod(read_only_dir, 0o444)

    try:
        # Try to save - should fail
        with pytest.raises(StorageException) as excinfo:
            await service.save("https://fail.com", "content", "md")

        assert "Failed to save file" in str(excinfo.value)

    finally:
        # Cleanup: Restore permissions so the test runner can delete the temp dir later
        os.chmod(read_only_dir, 0o777)