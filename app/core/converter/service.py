import re
from markdownify import markdownify
from typing import Protocol

from app.core.converter.exceptions import ConvertingException


class IConverterService(Protocol):
    """
        Interface for converting HTML content to other formats.
    """
    async def convert(self, content: str) -> str:
        """
        Convert HTML string to the target format.

        Args:
            content: Cleaned HTML string

        Returns:
            Formatted string (e.g., Markdown)
        """
        pass



class MarkDownConverterService(IConverterService):
    """
        Concrete implementation using the 'markdownify' library.
        Recommended in technical decisions for better control.
    """
    async def convert(self, content: str) -> str:
        """
        Converts HTML to LLM-friendly Markdown.

        Features:
        - Maintains document structure (headings, lists) [cite: 49]
        - Preserves image references [cite: 50]
        - Removes excessive whitespace for cleaner LLM context
        """
        if not content:
            return ""

        try:
            markdown_text = markdownify(
                content,
                heading_style="ATX",
                strip=["a", "img"] if False else None
            )

            markdown_text = self._clean_whitespace(markdown_text)
            return markdown_text
        except Exception as e:
            raise ConvertingException(f"Markdown conversion failed: {str(e)}", original_error=e)


    def _clean_whitespace(self, text: str) -> str:
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()


