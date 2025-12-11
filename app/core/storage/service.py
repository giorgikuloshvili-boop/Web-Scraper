import hashlib
import json

import aiofiles
from typing import Protocol, Dict, Any, Optional

from app.core.config import settings
from app.core.storage.exceptions import StorageException


class IStorageService(Protocol):
    """
        Interface for storage backends.
        Designed to support future RAG integrations (Vector DB).
    """
    async def save(
            self,
            url: str,
            content: str,
            extension: str,
            metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        pass

    async def get(
            self,
            url: str,
            extension: str,
    ) -> Optional[str]:
        pass



class FileSystemStorageService(IStorageService):
    """
        Concrete implementation storing files on the local disk.

        Locations:
        - HTML -> storage/html/
        - Markdown -> storage/markdown/
    """

    async def save(
            self,
            url: str,
            content: str,
            extension: str,
            metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
            Saves content to disk, overwriting existing files[cite: 53].
        """

        try:
            if extension.lower() in ["html", "htm"]:
                base_path = settings.HTML_STORAGE_PATH
            elif extension.lower() in ["markdown", "md"]:
                base_path = settings.MARKDOWN_STORAGE_PATH
            else:
                base_path = settings.BASE_DIR / "storage" / "misc"
                base_path.mkdir(parents=True, exist_ok=True)


            filename = self._generate_filename(url)
            file_path = base_path / f"{filename}.{extension}"

            async with aiofiles.open(file_path, mode="w", encoding="utf-8") as file:
                await file.write(content)

            if metadata:
                metadata_path = base_path / f"{filename}.json"
                metadata["source_url"] = url
                async with aiofiles.open(metadata_path, mode="w", encoding="utf-8") as file:
                    await file.write(json.dumps(metadata, indent=2, ensure_ascii=False))

            return str(file_path)

        except Exception as e:
            raise StorageException(f"Failed to save file for {url}: {str(e)}", original_error=e)

    async def get(
            self,
            url: str,
            extension: str,
    ) -> Optional[str]:
        """
            Retrieves content from disk.
        """
        try:
            filename = self._generate_filename(url)

            if extension.lower() in ["html", "htm"]:
                base_path = settings.HTML_STORAGE_PATH
            else:
                base_path = settings.MARKDOWN_STORAGE_PATH

            file_path = base_path / f"{filename}.{extension}"

            if not file_path.exists():
                return None

            async with aiofiles.open(file_path, mode="r", encoding="utf-8") as f:
                return await f.read()

        except Exception as e:
            raise StorageException(f"Failed to read file for {url}: {str(e)}", original_error=e)


    @staticmethod
    def _generate_filename(url: str) -> str:
        """
        Generates a consistent, filesystem-safe filename from a URL using MD5 hash.
        Requirement: Consistent naming convention (URL hash).
        """
        url_hash = hashlib.md5(url.encode("utf-8")).hexdigest()
        return url_hash
