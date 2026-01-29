# PRD: Credit Card PDF Statement Parser

**Date:** 2026-01-29

---

## Problem Statement

### What problem are we solving?

Bank credit-card statements are delivered as PDFs designed for humans, not machines. Users who want to track spending or automate finance workflows must manually copy data, which is slow, error-prone, and does not scale.

### Why now?

Personal finance automation and reconciliation require structured data. The cost of inaction is ongoing manual work and low data accuracy.

### Who is affected?

* **Primary users:** Individual developers and power users who want to extract transaction data.
* **Secondary users:** Personal finance apps and reporting tools consuming structured outputs.

---

## Proposed Solution

### Overview

Build a local, rule-based PDF parser with an abstract provider layer, so different bank formats can be supported by adding new parser modules. The system converts e-statements into structured JSON with high accuracy.

### User Experience

User provides a PDF file and receives a validated structured JSON output containing header fields, rewards summary, and all transactions.

---

## End State

When this PRD is complete, the following will be true:

* [ ] User can upload a bank statement PDF
* [ ] System extracts header summary fields
* [ ] System extracts transactions into structured form
* [ ] Validation ensures totals and formats are correct
* [ ] Export to JSON

---

## Success Metrics

### Quantitative

| Metric              | Current | Target      | Measurement Method          |
| ------------------- | ------- | ----------- | --------------------------- |
| Extraction accuracy | N/A     | >99%        | Manual validation vs output |
| Processing time     | N/A     | <2s per PDF | Local benchmark             |

### Qualitative

* Reduced manual effort
* Higher trust in personal finance data

---

## Acceptance Criteria

### Feature: PDF Parsing

* [ ] Abstract parser interface for multiple bank providers
* [ ] Pluggable provider-specific rules
* [ ] Can read multi-page PDFs
* [ ] Handles continuation lines (foreign currency)
* [ ] Handles negative payment rows

### Feature: Validation

* [ ] Detects invalid dates/amounts
* [ ] Flags unmatched totals

---

## Risks & Mitigations

| Risk                | Likelihood | Impact | Mitigation                |
| ------------------- | ---------- | ------ | ------------------------- |
| Bank changes layout | Med        | High   | Rule versioning + tests   |
| Broken text order   | Med        | Med    | Coordinate-based grouping |

---

## Alternatives Considered

### Alternative: OCR-based

* **Pros:** Works for scanned PDFs
* **Cons:** Lower accuracy
* **Decision:** Rejected for v1

---

## Non-Goals (v1)

* No cloud processing
* No GUI

---

## Open Questions

| Question                | Owner | Due Date | Status |
| ----------------------- | ----- | -------- | ------ |
| Support multiple banks? | Mew   | TBD      | Open   |
