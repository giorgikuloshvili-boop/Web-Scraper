class ParsingException(Exception):
    """Raised when HTML content cannot be parsed or data extraction fails."""
    def __init__(self, message: str, original_error: Exception | None = None) -> None:
        super().__init__(message)
        self.original_error = original_error