# ADR-002: Transaction Line Parsing & Splitting

## Status
Decided

## Context
Normalized PDF lines can merge multiple transactions into a single text row because
text blocks are grouped by Y-coordinate. The previous parsing approach relied on
loose date/amount extraction and could drift descriptions or amounts when multiple
transactions were present in one line.

## Decision
1. **Strict Transaction Patterns**: Introduce explicit regex patterns for
   transactions with two dates (transaction + posting) and a fallback for
   one-date lines.
2. **Multi-Transaction Splitting**: When a line contains multiple transactions,
   parse all matches and append each as a separate transaction in order.
3. **Fallback Preservation**: Keep the legacy heuristic parsing path when no
   strict match is found, to avoid dropping edge cases.

## Consequences
* **Pros**:
  * More accurate parsing when lines contain multiple transactions.
  * Reduced description/amount drift due to explicit boundaries.
  * Clearer separation of responsibilities between strict and fallback paths.
* **Cons**:
  * Transactions that deviate from the expected date/amount format may be skipped
    by the strict parser and fall back to heuristics.
  * Regex patterns assume two-decimal amounts and may need adjustments for
    providers with different formats.
