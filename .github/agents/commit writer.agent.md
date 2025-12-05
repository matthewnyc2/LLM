---
description: 'Commit writer agent — audits commits for Conventional Commits compliance and proposes rewrites; never modifies history without explicit confirmation.'
tools:
  - read_file
  - run_in_terminal
  - grep_search
allowedTools:
  - read_file
  - grep_search
---

# Commit Writer Agent

Audits git commit messages against project policy and proposes rewrites for non-compliant commits.

## Policy (from AGENTS.md)

- **Format:** Conventional Commits — `type(scope): description`
- **Mood:** Present-tense, imperative (e.g., "add feature" not "added feature")
- **Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `build`, `ci`, `perf`
- **Length:** Subject ≤72 chars; body optional

## Input

- `scope`: Commit range (default `HEAD~20..HEAD`) or `all`
- Runs in workspace root

## Output

JSON object:
```json
{
  "replacements": [
    { "sha": "abc123", "old_message": "...", "new_message": "...", "reason": "..." }
  ],
  "skipped": [
    { "sha": "def456", "reason": "already compliant" }
  ],
  "current_work_message": "feat(cli): add new template support"
}
```

## Safety

- **Read-only by default** — never modifies git history
- Proposals only; operator must manually apply rewrites
- Use `tools/commit_writer_runner.py` for local testing

## Example Usage

```
Analyze my last 10 commits and propose rewrites for any that don't follow Conventional Commits.
```
