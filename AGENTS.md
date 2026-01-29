# AGENTS

- Always use `uv` for Python installs, venvs, tools, and builds unless explicitly told otherwise.
- Project uses `pydantic` for core domain models and `pytest` for validation.
- PDFs in `test-pdf/` are the primary source for regression tests and layout analysis.
- The `plans/tech.md` document contains the architectural vision, including a state-machine parser design.
- `uv run pytest` is the preferred way to run tests within the managed environment.
