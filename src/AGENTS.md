# AGENTS

- TTB statements include foreign currency continuation lines (e.g., `JPY 2,000.00`) following the main transaction row.
- `PREVIOUS BALANCE` is a key anchor for identifying the start of transaction sections in TTB/KBANK PDFs.
- Positional extraction (coordinates) is preferred over raw text streams to handle bilingual (Thai/English) interleaving.
