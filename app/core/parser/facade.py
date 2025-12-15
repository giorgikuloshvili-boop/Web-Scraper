from typing import Dict, Any

from app.core.parser.service import WebsiteParserService


class ParserFacade:
    """
    Hides the complexity of the parsing pipeline (Parse -> Clean).
    """
    def __init__(self) -> None:
        self._service = WebsiteParserService()

    async def extract_clean_content(self, html: str) -> Dict[str, Any]:
        parsed_data = await self._service.parse(html)
        cleaned_data = await self._service.clean(parsed_data)
        return cleaned_data