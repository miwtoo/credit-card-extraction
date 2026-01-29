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

### Run API (MVP1)

```bash
uv run uvicorn credit_card_extraction.api:app --reload --port 8000
```

```bash
curl -s -X POST "http://127.0.0.1:8000/parse" \
  -F "file=@test-pdf/ttb_statement_local.pdf"
```

Notes:
- Replace the PDF path with your own file if `test-pdf/ttb_statement_local.pdf` is not present.
- `test-pdf/` is git-ignored and intended for local-only fixtures.

### Run Tests

```bash
uv run pytest
```

### Fixtures and Expected Output

- `tests/fixtures/ttb_statement_sample.txt` is a sanitized, extracted-text fixture used for golden tests.
- `tests/fixtures/ttb_statement_sample_golden.json` is the expected JSON output for that fixture.
- Update the golden JSON if parser behavior changes intentionally.

### Project Structure

- `src/credit_card_extraction`: Core logic and parser implementations.
- `tests/`: Unit and integration tests.
- `test-pdf/`: Sample PDFs for development and testing.
- `plans/`: Technical documentation and progress tracking.

## Technical Design

See [plans/tech.md](plans/tech.md) for the architecture overview.
