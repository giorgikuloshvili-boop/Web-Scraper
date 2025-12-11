from typing import Protocol, Dict, Any, Optional


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
        pass

    async def get(
            self,
            url: str,
            extension: str,
    ) -> Optional[str]:
        pass
