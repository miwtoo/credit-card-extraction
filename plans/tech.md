# Technical Design: Credit Card PDF Statement Parser

**Date:** 2026-01-29
**Owner:** Miw

---

## Goals

- Extract statement data from PDF to structured JSON with >99% accuracy.
- Support multiple bank formats via pluggable provider modules.
- Local-only processing (no cloud).
- Provide a REST API for integration.

## Non-Goals

- OCR-first parsing (v1).
- GUI.
- Cloud deployment.

---

## Architecture Overview

```
PDF -> Extractor (PyMuPDF/fitz) -> Line Normalizer -> State Machine Parser
    -> Domain Models -> Validation -> JSON Output
```

### Core Components

1. **Extractor**
   - Uses PyMuPDF (fitz) to read text per page.
   - Prefer positional extraction (`get_text("dict")` / `get_text("blocks")`) to
     preserve columns and row ordering.
   - Exposes raw lines with page/position metadata.

2. **Line Normalizer**
   - Groups text by row (y tolerance) and sorts by x to rebuild table rows.
   - Joins broken text fragments.
   - Removes duplicate headers/footers and repeated column labels.
   - Emits normalized lines for parsing.

3. **State Machine Parser**
   - Finite states (HEADER, TRANSACTIONS, FOOTER, UNKNOWN).
   - Each line drives state transitions and record assembly.
   - Provider-specific rules define how lines are classified.

4. **Validation**
   - Date and amount validation.
   - Totals reconciliation (if statement provides totals).
   - Flags mismatches without dropping data.

5. **REST API**
   - Accepts PDF upload.
   - Returns JSON or validation errors.

---

## State Machine Design

### States

- HEADER: statement metadata.
- TRANSACTIONS: transaction rows and continuation lines.
- FOOTER: rewards/totals/disclosures.
- UNKNOWN: fallback for unclassified lines.

### Line Classification

Provider-specific classifiers return:

- `line_type`: header_key | transaction_start | transaction_continuation |
  footer_key | noise
- `confidence`: optional score

### Transition Rules (Example)

| Current State | Line Type              | Next State     | Action                          |
| ------------ | ---------------------- | -------------- | ------------------------------- |
| HEADER       | transaction_start      | TRANSACTIONS   | flush header, start txn         |
| HEADER       | header_key             | HEADER         | add header field                |
| TRANSACTIONS | transaction_start      | TRANSACTIONS   | close prev txn, start new       |
| TRANSACTIONS | transaction_continuation | TRANSACTIONS | append to previous txn          |
| TRANSACTIONS | footer_key             | FOOTER         | close prev txn, capture footer  |
| FOOTER       | footer_key             | FOOTER         | add footer field                |
| *            | noise                  | (no change)    | ignore                          |

### Transaction Assembly

- `transaction_start`: date + description + amount.
- `transaction_continuation`: foreign currency lines, location, or memo.
- On new transaction or footer, previous transaction is finalized.

---

## Observations from Test PDFs

Test set: `test-pdf/ttb credit card e-statement_2989_02Jan2026.pdf`,
`test-pdf/KBGC_1000000049729211_260110 - unlocked.pdf`,
`test-pdf/UOB - MONTHLYSTATEMENT_20260128234913726.pdf`.

- Statements are bilingual (Thai + English) and repeat column headers per page.
- Transaction tables are columnar; raw text order can interleave columns unless
  grouped by coordinates.
- `PREVIOUS BALANCE` appears as the anchor before transaction rows (TTB, KBANK).
- TTB includes foreign currency continuation lines like `JPY 2,000.00` and
  `USD 40.50` that follow the main amount and belong to the previous transaction.
- Column headers vary by bank (e.g., `POST DATE`, `TRANS DATE`, `POSTING DATE`),
  so provider-specific header dictionaries are required.

---

## Data Model (JSON)

```json
{
  "statement": {
    "provider": "ttb",
    "statement_date": "2025-03-31",
    "account_last4": "1234",
    "previous_balance": 123.45,
    "new_balance": 456.78
  },
  "transactions": [
    {
      "date": "2025-03-12",
      "description": "MERCHANT NAME",
      "amount": -42.18,
      "currency": "JPY",
      "foreign_amount": 2000.00,
      "notes": "Continuation line text"
    }
  ],
  "rewards": {
    "points_earned": 123,
    "points_balance": 456
  },
  "validation": {
    "errors": [],
    "warnings": [
      "Statement total mismatch: expected 456.78, got 457.10"
    ]
  }
}
```

---

## Provider Abstraction

### Interface (Python)

- `extract_lines(pdf_path) -> list[RawLine]`
- `classify_line(line) -> LineClassification`
- `parse_header(line, ctx)`
- `parse_transaction_start(line, ctx)`
- `parse_transaction_continuation(line, ctx)`
- `parse_footer(line, ctx)`

Provider modules live under `parsers/<provider>/`.

---

## REST API

### Endpoints

- `POST /parse`
  - Multipart upload: `file`
  - Response: JSON structure above

### Error Handling

- 400: invalid PDF
- 422: validation errors (includes partial extraction)
- 500: unexpected parsing failure

---

## Tracer Bullet (v1 Slice)

Goal: Parse a single TTB statement with:

1. Header detection
2. Transaction rows
3. Foreign currency continuation lines

Deliverable: JSON output + 2 tests (start row, continuation).

---

## Testing Strategy

- Unit tests for line classification and state transitions.
- Golden file tests with known PDF fixtures.
- Regression tests per provider layout change.

---

## Open Questions

- Which banks are in scope for v1?
- Should provider selection be manual or auto-detected?
- Is totals reconciliation required before output?
