#!/usr/bin/env python3
"""Safe runner for commit_writer agent proposals.

This tool DOES NOT automatically rewrite history. It inspects commit messages, scores them against a simple heuristic, and emits proposed commit message replacements. If `--apply` and `--confirm` are both set, it applies changes using `git filter-branch` or `git rebase -i` after prompting for final confirmation. Use cautiously.
"""
import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# Simple heuristic for commit message quality
MIN_LEN = 60
REQUIRED_SECTIONS = ["Project Description", "Changes Made", "Affected User Stories", "Directory Tree", "Tags"]

@dataclass
class Proposal:
    sha: str
    old_message: str
    new_message: str
    reason: str


def git_log(scope: str = 'HEAD~20..HEAD'):
    # use pretty format to get sha and message
    cmd = ['git', 'log', '--pretty=format:%H%x1f%B%x1e', scope]
    p = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"git log failed: {p.stderr}")
    out = p.stdout
    entries = [e for e in out.strip().split('\x1e') if e.strip()]
    commits = []
    for e in entries:
        try:
            sha, body = e.split('\x1f', 1)
        except ValueError:
            continue
        commits.append((sha.strip(), body.strip()))
    return commits


def score_message(msg: str):
    score = 0
    if len(msg) >= MIN_LEN:
        score += 1
    for s in REQUIRED_SECTIONS:
        if s in msg:
            score += 1
    # penalize vague single-line messages
    if '\n' not in msg:
        score -= 1
    return score


def generate_markdown_for_commit(old_msg: str, sha: str, repo_files_snapshot_tree: str = ''):
    # produce a structured commit message following project format
    prs = [s.strip() for s in old_msg.splitlines() if s.strip()][:3]
    summary = prs[0] if prs else 'Improve commit message clarity'
    new_md = f"# Project Description\n\nRefine commit {sha} to be descriptive and follow project commit standard.\n\n## Changes Made\n\n- **Change:** Clarified intent of commit {sha}.\n- **Added:** None.\n- **Removed:** None.\n\n## Affected User Stories\n\n- As a reviewer, I want commit messages to explain why changes were made so I don't have to read the code to understand it.\n\n## Directory Tree\n\n```
{repo_files_snapshot_tree}
```\n\n## Tags\n\n#commit #cleanup\n"
    return new_md


def inspect_commits(scope: str='HEAD~20..HEAD'):
    commits = git_log(scope)
    proposals = []
    skipped = []
    for sha, body in commits:
        s = score_message(body)
        if s < 2:
            reason = f"low score ({s})"
            new_message = generate_markdown_for_commit(body, sha)
            proposals.append(Proposal(sha=sha, old_message=body, new_message=new_message, reason=reason))
        else:
            skipped.append({"sha": sha, "message_excerpt": body[:120]})
    return proposals, skipped


def apply_rewrites(proposals, dry_run=True):
    # Provide a conservative apply method: produce a script that can be inspected and run manually.
    script = []
    for p in proposals:
        # We will create commands to amend the commit message using interactive rebase strategy.
        cmd = f"# Replace message for {p.sha}\n# git rebase -i <base> then change pick -> reword for {p.sha} and paste the new message\n"
        script.append(cmd)
    return '\n'.join(script)


def main():
    parser = argparse.ArgumentParser(description='Inspect git history for poor commit messages and propose rewrites')
    parser.add_argument('--scope', default='HEAD~20..HEAD', help='git log scope (default: HEAD~20..HEAD)')
    parser.add_argument('--apply', action='store_true', help='Generate an apply script (do NOT run it)')
    parser.add_argument('--confirm', action='store_true', help='If set with --apply, the runner will automatically run the apply script (DANGEROUS)')
    parser.add_argument('--out', default='commit_rewrite_proposals.json', help='Where to write the proposals')

    args = parser.parse_args()
    proposals, skipped = inspect_commits(args.scope)
    out = {
        'replacements': [p.__dict__ for p in proposals],
        'skipped': skipped,
        'current_work_message': None
    }

    # if there's a staged commit or changes, craft a message for current work
    # Heuristic: if there are staged changes, get git diff --staged --name-only and summarise
    try:
        staged = subprocess.run(['git', 'diff', '--cached', '--name-only'], cwd=REPO_ROOT, capture_output=True, text=True)
        if staged.returncode == 0 and staged.stdout.strip():
            files = [f.strip() for f in staged.stdout.strip().splitlines()]
            summary = f"Work in progress: changes in {', '.join(files[:3])}"
            out['current_work_message'] = generate_markdown_for_commit(summary, 'WORK-IN-PROGRESS', '\n'.join(files[:20]))
    except Exception:
        pass

    Path(args.out).write_text(json.dumps(out, indent=2), encoding='utf-8')
    print('Wrote proposals to', args.out)

    if args.apply:
        script = apply_rewrites(proposals, dry_run=True)
        script_path = Path('apply_commit_rewrites.sh')
        script_path.write_text(script, encoding='utf-8')
        print('Wrote apply script to', script_path)
        if args.confirm:
            print('CONFIRM flagged — applying rewrites automatically is dangerous. Asking for final confirmation...')
            confirm = input('Type YES to continue: ')
            if confirm == 'YES':
                print('Would run the apply script here — disabled by default for safety.')
            else:
                print('Aborting apply.')

if __name__ == '__main__':
    main()
