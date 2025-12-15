from typing import Protocol, Any, Dict, List

from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

from app.core.parser.exceptions import ParsingException


class IParserService(Protocol):
    """
        Interface Base Class defining the contract for parsing services.
        Adheres to the Open/Closed Principle.
    """
    async def parse(self, html: str) -> Dict[str, Any]:
        """Parse raw HTML and extract extraction-ready structure."""
        pass

    async def clean(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean extracted data by removing noise and duplicates."""
        pass

    async def extract_links(self, html: str, current_url: str, base_domain: str) -> List[str]:
        """Helper to extract links using BS4"""
        pass


class WebsiteParserService(IParserService):
    """
        Concrete implementation of IParserService using BeautifulSoup.
    """

    NOISE_TAGS = [
        "script",
        "style",
        "iframe",
        "noscript",
        "meta",
        "link",
        "svg",
        "form",
        "input",
        "button",
    ]

    BOILERPLATE_TAGS = ["header", "footer", "nav", "aside"]

    async def parse(self, html: str) -> Dict[str, Any]:
        """
        Parses HTML into a dictionary structure.

        Args:
            html: Raw HTML string

        Returns:
            Dict containing title, meta_description, and raw content body.

        Raises:
            ParsingError: If HTML cannot be processed.
        """
        if not html:
            raise ParsingException("Empty HTML content provided")

        try:
            soup = BeautifulSoup(html, "html.parser")
            title = soup.title.string if soup.title else "No title"

            meta_description_tag = soup.find("meta", attrs={"name": "description"})
            meta_description = meta_description_tag["content"] if meta_description_tag else ""

            body_content = str(soup.body) if soup.body else str(soup)

            return {
                "title": title.strip(),
                "metadata": {
                    "description" : meta_description,
                },
                "content": body_content,
            }
        except Exception as e:
            raise ParsingException(f"Failed to parse HTML: {str(e)}", original_error=e)

    async def clean(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitizes the HTML content.

        Operations:
        - Removes scripts, styles, and non-content elements.
        - Removes headers, footers, and navigation (duplicates).
        - Preserves images and main content.

        Args:
            data: The dictionary output from parse()

        Returns:
            Dict with 'cleaned_content' added.
        """

        try:
            raw_html = data.get("content", "")
            if not raw_html:
                return {**data, "cleaned_content": ""}

            soup = BeautifulSoup(raw_html, "html.parser")

            for tag_name in self.NOISE_TAGS:
                for tag in soup.find_all(tag_name):
                    tag.decompose()

            for tag_name in self.BOILERPLATE_TAGS:
                for tag in soup.find_all(tag_name):
                    tag.decompose()

            for tag in soup.find_all(True):
                attrs = dict(tag.attrs)
                allowed_attrs = ["src", "href", "alt", "title"]
                for attr in attrs:
                    if attr not in allowed_attrs:
                        del tag[attr]

            cleaned_html = str(soup)

            return {
                **data,
                "cleaned_content": cleaned_html
            }

        except Exception as e:
            raise ParsingException(f"Failed to clean HTML content: {str(e)}", original_error=e)


    async def extract_links(self, html: str, current_url: str, base_domain: str) -> List[str]:
        """
        Helper to extract links using BS4

        Args:
            html: Raw HTML string
            current_url: Current URL
            base_domain: Base URL

        Returns:
            Dict containing links.

        Raises:
            ParsingError: If HTML cannot be processed.
        """
        from bs4 import BeautifulSoup
        valid_links = []
        try:
            soup = BeautifulSoup(html, "html.parser")
            for a in soup.find_all("a", href=True):
                href = a["href"]
                full_url = urljoin(current_url, href)
                parsed = urlparse(full_url)

                full_url = full_url.split("#")[0].rstrip("/")

                if parsed.netloc == base_domain and parsed.scheme in ["http", "https"]:
                    valid_links.append(full_url)
        except Exception as e:
            raise ParsingException(f"Failed to extract links: {str(e)}", original_error=e)
        return valid_links
