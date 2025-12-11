class ConvertingException(Exception):
    """Raised when data cleaning or markdown conversion fails."""
    def __init__(self, message: str, original_error: Exception = None) -> None:
        super().__init__(message)
        self.original_error = original_error