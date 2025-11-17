# Repository Guidelines

## Project Structure & Module Organization
- `llm.py`: Main CLI to build MCP configs and launch selected LLMs.
- `servers/`: JSON/TOML templates for different tools (e.g., Copilot, Claude).
- `generated/`: Output configs produced by `llm.py`.
- `cli_manager/`: Secondary TUI for selecting LLMs/MCPs and building agents (`manager.py`, `config.py`, `ui_helpers.py`, `agent_builder.py`).
- `requirements.txt`: Python dependencies.

## Build, Test, and Development Commands
- Create venv: `python -m venv .venv && .venv\Scripts\activate`
- Install deps: `pip install -r requirements.txt`
- Run config builder: `python llm.py`
- Run manager UI: `python -m cli_manager.manager`
- Tail history: `type history.log` or `type cli_manager\history.log`

## Coding Style & Naming Conventions
- Python 3.10+; use 4‑space indents and type hints where practical.
- Names: `snake_case` for files/functions, `PascalCase` for classes, constants UPPER_CASE.
- Keep modules small and side‑effect free; prefer pure functions.
- Optional formatting: `black -l 100` and linting with `ruff` if available (not required).

## Testing Guidelines
- No formal test suite yet. Prefer small, testable functions and manual checks via the CLIs above.
- If adding tests: use `pytest`, place tests under `tests/`, name files `test_*.py`.

## Commit & Pull Request Guidelines
- Commits: present‑tense, imperative. Prefer Conventional Commits, e.g., `feat: add opencode template`, `fix: handle nested mcp.servers`.
- PRs: include scope/goal, linked issues, and before/after notes (e.g., sample generated config path under `generated/`). Screenshots optional for TUI changes.

## Security & Configuration Tips
- File writes target user paths (see `APP_LOCATIONS` in `llm.py`) and `cli_manager/config.py` constants. Avoid committing secrets or user‑specific paths.
- Adjust `AGENT_SAVE_PATH` in `cli_manager/config.py` if your agent directory differs.
- Windows environment variables like `%APPDATA%` and `%USERPROFILE%` are expanded at runtime.

## Agent‑Specific Notes
- Agent builder saves markdown to per‑tool subfolders under `AGENT_SAVE_PATH` with file‑safe names (e.g., `code_reviewer.md`).
- When editing templates in `servers/`, keep server keys stable; these drive selection and rendering order.

