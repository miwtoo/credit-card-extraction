# ADR-003: Footer Noise Trimming & Balance Fallbacks

## Status
Decided

## Context
PDF extraction can inject control characters and footer content into transaction
descriptions. Additionally, some statements provide only one of `new_balance` or
`outstanding_balance`, which can leave the other field as `0.0` despite the
statement clearly indicating a balance.

## Decision
1. **Text Sanitization**: Strip control characters and collapse whitespace before
   parsing.
2. **Footer Trimming**: Detect footer keywords and trim descriptions at the first
   footer marker when still inside transaction parsing.
3. **Balance Fallbacks**: If `outstanding_balance` is zero but `new_balance` is
   present, copy `new_balance` into `outstanding_balance`, and vice versa.

## Consequences
* **Pros**:
  * Cleaner transaction descriptions without garbage text.
  * Less leakage of footer text into transaction rows.
  * Consistent balances when the statement only exposes one of the fields.
* **Cons**:
  * Over-trimming is possible if a merchant description contains a footer keyword.
  * Balance fallback may mask a truly zero balance if the other field is filled
    incorrectly.
