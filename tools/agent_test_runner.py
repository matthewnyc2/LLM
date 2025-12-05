#!/usr/bin/env python3
"""Simple harness to validate code_reviewer_small_patch samples.

This script verifies expected_output.json is valid JSON, checks the target file exists,
applies a simple unified diff parser to the file, and runs pytest for the sample test (if pytest is available).

It is intentionally small (no external dependencies) so it can run locally on Windows and Unix.
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAMPLES_DIR = ROOT / "tests" / "agents" / "code_reviewer"


def apply_unified_diff(file_path: Path, diff_text: str) -> str:
    # Very small parser for unified diffs that handles simple one-hunk replacement
    orig = file_path.read_text(encoding="utf-8")
    lines = orig.splitlines(keepends=True)

    # find @@ hunk header
    hunk_match = re.search(r"@@ .*@@\n([\s\S]*)", diff_text)
    if not hunk_match:
        raise ValueError("Unsupported diff format: missing hunk")
    hunk_body = hunk_match.group(1)

    # we'll do a simple replacement approach: find the lines in the original that match the '-' lines
    removed = []
    added = []
    for line in hunk_body.splitlines():
        if line.startswith("-"):
            removed.append(line[1:])
        elif line.startswith("+"):
            added.append(line[1:])
        else:
            # context lines (space or otherwise)
            removed.append(line[1:] if line.startswith(' ') else line)
            added.append(line[1:] if line.startswith(' ') else line)

    # naïve replace: join removed then replace in file
    removed_text = "\n".join(l.rstrip('\n') for l in removed).rstrip('\n') + ("\n" if removed else "")
    added_text = "\n".join(l.rstrip('\n') for l in added).rstrip('\n') + ("\n" if added else "")

    if removed_text not in orig:
        raise ValueError("Hunk removal snippet not found in original file (parser is intentionally strict)")

    new = orig.replace(removed_text, added_text, 1)
    return new


def run_sample(sample_dir: Path) -> int:
    print(f"\n=== Running sample {sample_dir.name} ===")
    expected = sample_dir / "expected_output.json"
    if not expected.exists():
        print("expected_output.json not found")
        return 2

    try:
        data = json.loads(expected.read_text(encoding='utf-8'))
    except Exception as e:
        print("Failed to parse expected_output.json:", e)
        return 3

    patch = data.get("patch")
    if not patch:
        print("No patch provided in expected output; nothing to validate")
        return 4

    file_rel = patch.get("file")
    if not file_rel:
        print("patch.file is missing")
        return 5

    target = sample_dir / file_rel
    if not target.exists():
        print("Target file does not exist:", target)
        return 6

    diff_text = patch.get("diff")
    if not diff_text or '---' not in diff_text:
        print("Invalid or missing diff text")
        return 7

    try:
        new_content = apply_unified_diff(target, diff_text)
    except Exception as e:
        print("Failed to apply diff:", str(e))
        return 8

    # write to temporary file and run the test
    tmp_file = target.with_suffix(".patched.tmp")
    tmp_file.write_text(new_content, encoding='utf-8')

    # For this test harness we'll copy the patched file over into a temporary directory to run pytest there
    import tempfile
    import shutil

    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        # copy repo_snapshot into the temp dir root
        shutil.copytree(sample_dir / "repo_snapshot", td_path, dirs_exist_ok=True)
        # compute the relative path of the file inside repo_snapshot
        from pathlib import PurePosixPath

        orig_rel = Path(file_rel)
        if len(orig_rel.parts) > 0 and orig_rel.parts[0] == "repo_snapshot":
            relative = Path(*orig_rel.parts[1:])
        else:
            relative = orig_rel

        # overwrite the file with patched contents
        patched_target = td_path / relative
        patched_target.parent.mkdir(parents=True, exist_ok=True)
        patched_target.write_text(new_content, encoding='utf-8')

        # copy the test file
        test_file = sample_dir / "test_sample.py"
        if not test_file.exists():
            print("test_sample.py not found in sample folder; cannot run pytest")
            return 9
        shutil.copy(test_file, td_path / "test_sample.py")

        # run pytest in the temp dir
        try:
            result = subprocess.run([sys.executable, "-m", "pytest", "-q", "test_sample.py"], cwd=td_path, capture_output=True, text=True, timeout=10)
            print("pytest stdout:\n", result.stdout)
            print("pytest stderr:\n", result.stderr)
            if result.returncode != 0:
                print("Patched repo did not pass tests (exit code)", result.returncode)
                return 10
        except Exception as e:
            print("Failed running pytest:", str(e))
            return 11

    print("Patch applied and tests passed for sample:", sample_dir.name)
    return 0


if __name__ == '__main__':
    rc = 0
    for s in sorted(SAMPLES_DIR.iterdir()):
        if s.is_dir():
            rc |= run_sample(s)
    sys.exit(rc)
