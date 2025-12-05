# Agent examples and test harness

This file documents the `code_reviewer_small_patch` example agent and how to run the local validation harness.

## Files added
- `.amazonq/agents/code_reviewer_small_patch.json` — agent manifest.
- `tests/agents/code_reviewer/sample-1/` — sample failing output, repo snapshot, expected_output.json and test file.
- `tools/agent_test_runner.py` — a small harness that validates expected_output.json and tries applying the patch, then runs pytest against the patched snapshot to confirm the test passes.

## How to run the sample harness

Open a powershell or terminal in the repository root and run:

```bash
python -m pip install pytest  # if pytest is not installed
python tools/agent_test_runner.py
```

This will run the sample-1 case and print details of the patch application and pytest run.

Note: the harness is intentionally small and conservative — it will attempt to apply a simple unified diff pattern and run pytest to validate the sample. It is meant as a developer tool for quickly iterating on agent outputs.

## Run the commit-writer agent from VS Code

If you want to run the `commit_writer` subagent directly from VS Code, the workspace includes a couple of helpful tasks and launch configurations.

1. Open the Command Palette (Ctrl+Shift+P) and choose 'Tasks: Run Task' → 'Commit Writer: Inspect commits (dry-run)' to generate `commit_writer_proposals.json`.
2. Run 'Commit Writer: Generate apply script' to have the agent prepare an apply script (`apply_commit_rewrites.sh`) but **not** execute rewriting.
3. If you truly want to let the agent attempt to apply rewrites automatically (dangerous and requires manual confirmation), use 'Commit Writer: Apply rewrites (confirm)'.

Or use the debugger launch configurations 'Run Commit Writer (inspect)' or 'Run Commit Writer (apply - dry)'.
