# AGENTS

- Always use `uv` for Python installs, venvs, tools, and builds unless explicitly told otherwise.
- Project uses `pydantic` for core domain models and `pytest` for validation.
- PDFs in `test-pdf/` are the primary source for regression tests and layout analysis.
- The `plans/tech.md` document contains the architectural vision, including a state-machine parser design.
- `uv run pytest` is the preferred way to run tests within the managed environment.
- When creating/editing GitHub issues via `gh`, prefer `--body-file -` with a single-quoted heredoc (`cat <<'EOF'`) to avoid zsh interpreting backticks/parentheses/`<...>` in the body.
- For public issues, never paste real statement/account values; use placeholders and verify removal by searching issues (`gh issue list --state all --search "<needle>"`).
- If `gh issue view <n>` unexpectedly fails, confirm the target repo context (`gh repo view`, `git remote -v`) and re-list issues to validate existence.
