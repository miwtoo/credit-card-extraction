# Credit Card Extraction

PDF to structured JSON extraction for Thai credit card statements.

## Development Setup

This project uses `uv` for dependency management.

### Prerequisites

- [uv](https://github.com/astral-sh/uv)

### Install Dependencies

```bash
uv sync
```

### Run Tests

```bash
uv run pytest
```

### Project Structure

- `src/credit_card_extraction`: Core logic and parser implementations.
- `tests/`: Unit and integration tests.
- `test-pdf/`: Sample PDFs for development and testing.
- `plans/`: Technical documentation and progress tracking.

## Technical Design

See [plans/tech.md](plans/tech.md) for the architecture overview.
