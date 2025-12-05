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


## Example specialized agent (scaffolded)

- `code_reviewer_small_patch` — a focused agent that, given a failing test and a small repo snapshot, produces exactly one JSON object describing a minimal patch to fix the failing test plus commands to validate the fix.

Files added for the example:

- `.amazonq/agents/code_reviewer_small_patch.json` — agent manifest (allowed tools, prompt, resources).
- `tests/agents/code_reviewer/sample-1/` — example failing output, a tiny repo snapshot and test, and `expected_output.json` describing the expected agent result.
- `tools/agent_test_runner.py` — small validation harness that applies the provided unified diff to the snapshot and verifies the test passes using pytest.

To run the developer harness locally:

```pwsh
python -m pip install -r requirements.txt  # ensure deps installed (pytest is required)
python tools/agent_test_runner.py
```

This is intended as a minimal local developer tool for iterating on agent output. Do not enable agent write/apply operations in production without review and proper sandboxing.

