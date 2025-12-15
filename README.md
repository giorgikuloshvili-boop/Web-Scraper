# Web Scraper

This project is a comprehensive and scalable web scraper designed to efficiently extract, process, and store data from various websites. It is built with a modular architecture, making it adaptable to different scraping needs and easy to maintain. The core functionalities include advanced parsing, flexible data conversion, robust storage mechanisms, and an intelligent scheduling system for automated scraping tasks.

## Features

*   **Modular Architecture:** Easily extendable and maintainable components for parsing, conversion, storage, and scraping.
*   **Asynchronous Scraping:** Leverages `asyncio` for high-performance, concurrent web requests.
*   **Configurable Scrapers:** Define scraping rules and targets through flexible configuration.
*   **Data Transformation:** Convert scraped raw data into structured formats.
*   **Persistent Storage:** Store extracted data using various configurable storage solutions.
*   **Task Scheduling:** Automate scraping jobs with a built-in scheduler.
*   **API Interface:** Expose scraping functionalities via a RESTful API.
*   **Robust Error Handling:** Comprehensive error management and logging to ensure reliability.

## Technologies Used

*   **Python 3.9+:** The primary programming language.
*   **FastAPI:** Modern, fast (high-performance) web framework for building APIs.
*   **Pydantic:** Data validation and settings management using Python type hints.
*   **Beautiful Soup 4:** For parsing HTML and XML documents.
*   **HTTPX:** A fully-featured HTTP client for Python, supporting HTTP/1.1 and HTTP/2.
*   **uvloop:** (Optional) A fast, drop-in replacement for the default asyncio event loop.
*   **Uvicorn:** An ASGI web server for Python.
*   **Pytest:** A testing framework for Python.
*   **uv:** A fast Python package installer and resolver.

## Error Handling

The project incorporates robust error handling mechanisms across its modules. Custom exceptions are defined within each core service (e.g., `app/core/converter/exceptions.py`, `app/core/parser/exceptions.py`, `app/core/scraper/exceptions.py`, `app/core/storage/exceptions.py`) to provide specific error contexts. Global exception handling is managed at the API level to ensure graceful degradation and informative error responses for clients. Detailed logs are generated to assist in debugging and monitoring.

## Testing Strategy

The project employs a comprehensive testing strategy comprising:

*   **Unit Tests:** Located in `tests/unit/`, these tests verify the functionality of individual modules and functions in isolation. `pytest` is used as the testing framework, along with `conftest.py` for shared fixtures.
*   **Integration Tests:** Located in `tests/integration/`, these tests ensure that different components of the system work correctly when integrated. This includes tests for API endpoints (`test_api_endpoints.py`), the end-to-end scraping workflow (`test_e2e_scraping_workflow.py`), error handling scenarios (`test_error_handling_scenarios.py`), and scheduler functionality (`test_scheduler_functionality.py`).

All tests can be run using the `pytest` command from the project root.
## Project Structure

```
app/                               # Main application source code
├── core/                          # Core business logic, services, and schemas
│   ├── config.py                  # Manages application-wide settings and configurations.
│   ├── converter/                 # Contains services for transforming scraped data into desired formats.
│   │   ├── exceptions.py          # Defines custom exceptions for data conversion operations.
│   │   └── service.py             # Implements the data conversion logic.
│   ├── interactor.py              # Orchestrates the flow between different core services, acting as the main application interface.
│   ├── logger.py                  # Provides centralized logging utilities for the application.
│   ├── parser/                    # Houses services responsible for parsing raw HTML content.
│   │   ├── exceptions.py          # Defines custom exceptions for parsing operations.
│   │   ├── facade.py              # Provides a simplified interface to the parsing services.
│   │   └── service.py             # Implements the core HTML parsing logic.
│   ├── scheduler.py               # Manages and schedules periodic web scraping tasks.
│   ├── scraper/                   # Contains services for making HTTP requests and initiating the scraping process.
│   │   ├── exceptions.py          # Defines custom exceptions for scraping operations.
│   │   ├── facade.py              # Provides a simplified interface to the scraping services.
│   │   └── service.py             # Implements the core web scraping logic.
│   ├── storage/                   # Provides services for storing extracted data into various persistent layers.
│   │   ├── exceptions.py          # Defines custom exceptions for storage operations.
│   │   └── service.py             # Implements the data storage logic.
│   └── schemas.py                 # Defines data structures and validation schemas using Pydantic.
├── infra/                         # Infrastructure-related components, such as API and dependency management
│   ├── api/                       # Houses the RESTful API definitions.
│   │   └── v1/                    # Version 1 of the API.
│   │       └── endpoints.py       # Defines API endpoints for interacting with the scraper.
│   └── dependables.py             # Manages dependency injection for FastAPI endpoints.
└── runner/                        # Application entry points and ASGI server setup
    ├── __main__.py                # The main entry point for running the application directly.
    └── asgi.py                    # The ASGI application entry point for deployment with ASGI servers (e.g., Uvicorn).

tests/                             # Contains all unit and integration tests for the project.
├── integration/                   # End-to-end and integration tests to verify interactions between components.
│   ├── test_api_endpoints.py      # Tests for the API endpoints.
│   ├── test_e2e_scraping_workflow.py # Comprehensive tests for the entire scraping workflow.
│   ├── test_error_handling_scenarios.py # Tests various error handling scenarios.
│   └── test_scheduler_functionality.py # Tests the functionality of the scheduler.
└── unit/                          # Unit tests for individual modules and functions.
    ├── conftest.py                # Pytest conftest file for test fixtures.
    ├── test_converter_service.py  # Unit tests for the converter service.
    ├── test_interactor.py         # Unit tests for the interactor.
    ├── test_parser_service.py     # Unit tests for the parser service.
    ├── test_scheduler.py          # Unit tests for the scheduler.
    ├── test_scraper_service.py    # Unit tests for the scraper service.
    └── test_storage_service.py    # Unit tests for the storage service.

pyproject.toml                     # Project metadata and build system configuration (e.g., Poetry or Hatch).
requirements.txt                   # Lists all Python dependencies required for the project.
uv.lock                            # Lock file generated by `uv` for reproducible dependency installations.
```

## Installation

1. Clone the repository:

   ```bash
   git clone <repository_url>
   cd web_scraper
   ```

2. Create and activate a virtual environment (recommended):

   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   # or using uv
   uv pip install -r requirements.txt
   ```

## Usage

To run the application, which includes the API, use the following command:

```bash
python -m app.runner
```

This will start the FastAPI application, typically accessible at `http://localhost:8000` (or as configured).

### API Usage

The primary way to interact with the scraper is through its RESTful API. Below is an example of how to trigger a scraping task using the `/trigger` endpoint:

**Endpoint:** `POST /api/v1/trigger`

**Request Body Example:**

```json
{
  "url": "https://example.com",
  "force": false
}
```

**Example using `curl`:**

```bash
curl -X POST "http://localhost:8000/api/v1/trigger" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://example.com", "force": false}'
```

Upon successful submission, the API will return a `201 Created` status with a `task_id` that can be used to monitor the scraping job's status.

### Monitoring Task Status

(This section is a placeholder. Further API endpoints for task status monitoring would be detailed here once implemented.)

## Running Tests

To run the tests, use `pytest`:

```bash
pytest
```

## Configuration

Configuration settings are managed through `app/core/config.py` and can be overridden using environment variables. This allows for flexible deployment and local development. Key configuration parameters include:

*   **Application Settings:** `APP_NAME`, `APP_VERSION`, `DEBUG`.
*   **API Settings:** `API_V1_STR` for the base path of the API.
*   **Scraping Schedule:** `SCRAPE_SCHEDULE_TIME` and `TIMEZONE` for automated tasks.
*   **Scraper Parameters:** `TARGET_URL`, `MAX_CRAWL_DEPTH`, `REQUEST_TIMEOUT`, `MAX_CONCURRENT_REQUESTS`, `RETRY_ATTEMPTS` to control scraping behavior.
*   **Storage Paths:** `HTML_STORAGE_PATH` and `MARKDOWN_STORAGE_PATH` to define where scraped data is stored.
*   **Logging:** `LOG_LEVEL` and `LOG_FILE` for controlling the verbosity and output location of logs.

You can customize these settings by creating a `.env` file in the project root or by setting environment variables directly.

## Contributing

Contributions are highly encouraged! To contribute to this project, please follow these guidelines:

### Coding Standards

*   Adhere to [PEP 8](https://www.python.org/dev/peps/pep-0008/) for Python code style.
*   Use clear, descriptive variable and function names.
*   Include docstrings for all modules, classes, and functions.
*   Write type hints for function arguments and return values.

### Testing

*   All new features and bug fixes should be accompanied by appropriate unit and/or integration tests.
*   Ensure existing tests pass before submitting a pull request.
*   Run tests using `pytest`.

### Pull Request Process

1.  Fork the repository.
2.  Create a new branch (`git checkout -b feature/your-feature-name`).
3.  Make your changes and ensure they adhere to the coding standards.
4.  Write and run tests to ensure your changes work as expected and do not introduce regressions.
5.  Commit your changes with a clear and concise commit message (e.g., `feat: Add new feature`, `fix: Resolve bug in parser`).
6.  Push your branch to your forked repository (`git push origin feature/your-feature-name`).
7.  Open a Pull Request to the `main` branch of the upstream repository, describing your changes and their purpose.
