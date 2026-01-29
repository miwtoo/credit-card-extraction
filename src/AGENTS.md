# AGENTS

- TTB statements include foreign currency continuation lines (e.g., `JPY 2,000.00`) following the main transaction row.
- `PREVIOUS BALANCE` is a key anchor for identifying the start of transaction sections in TTB/KBANK PDFs.
- Positional extraction (coordinates) is preferred over raw text streams to handle bilingual (Thai/English) interleaving.
- Card number parsing expects only digits and `X` in masked patterns (avoid letter placeholders in tests/fixtures).
- Normalized lines can include multiple transactions; parsing should split a single line into multiple transactions when possible.
- Header balances have a fallback: if one of `new_balance`/`outstanding_balance` is zero, copy the other.
- Footer keywords may appear inside transaction rows; trimming should occur before finalizing descriptions.
