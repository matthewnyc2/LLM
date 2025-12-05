#!/usr/bin/env python3
"""Commit writer runner — analyzes commits for Conventional Commits compliance.

This tool inspects commit messages, scores them against project policy
(Conventional Commits, present-tense imperative), and outputs proposals.
It NEVER modifies git history automatically.
"""
import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parents[1]

# Conventional Commits types per AGENTS.md
VALID_TYPES = {'feat', 'fix', 'docs', 'style', 'refactor', 'test', 'chore', 'build', 'ci', 'perf'}

# Regex for Conventional Commits: type(scope): description OR type: description
CC_PATTERN = re.compile(r'^(feat|fix|docs|style|refactor|test|chore|build|ci|perf)(\([a-z0-9_-]+\))?:\s+.+', re.IGNORECASE)

# Past tense indicators (simple heuristic)
PAST_TENSE_WORDS = {'added', 'fixed', 'updated', 'removed', 'changed', 'implemented', 'created', 'deleted', 'modified'}


@dataclass
class Proposal:
    sha: str
    old_message: str
    new_message: str
    reason: str


@dataclass 
class Skipped:
    sha: str
    reason: str


def git_log(scope: str = 'HEAD~20..HEAD') -> list[tuple[str, str]]:
    """Get commits as (sha, message) tuples."""
    cmd = ['git', 'log', '--pretty=format:%H%x1f%B%x1e', scope]
    result = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Warning: git log failed for scope '{scope}': {result.stderr}", file=sys.stderr)
        return []
    
    commits = []
    for entry in result.stdout.strip().split('\x1e'):
        entry = entry.strip()
        if not entry:
            continue
        try:
            sha, body = entry.split('\x1f', 1)
            commits.append((sha.strip(), body.strip()))
        except ValueError:
            continue
    return commits


def git_show_stat(sha: str) -> str:
    """Get diffstat for a commit."""
    cmd = ['git', 'show', '--stat', '--format=', sha]
    result = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else ''


def score_message(msg: str) -> tuple[int, list[str]]:
    """Score a commit message. Returns (score, list of issues).
    
    Score 0 = perfect, higher = more issues.
    """
    issues = []
    subject = msg.split('\n')[0].strip()
    
    # Check Conventional Commits format
    if not CC_PATTERN.match(subject):
        issues.append('not Conventional Commits format')
    
    # Check length
    if len(subject) > 72:
        issues.append(f'subject too long ({len(subject)} > 72 chars)')
    
    # Check for past tense
    first_word_after_colon = ''
    if ':' in subject:
        after_colon = subject.split(':', 1)[1].strip()
        first_word_after_colon = after_colon.split()[0].lower() if after_colon else ''
    
    if first_word_after_colon in PAST_TENSE_WORDS:
        issues.append(f'uses past tense "{first_word_after_colon}" instead of imperative')
    
    # Check for vague messages
    vague_patterns = ['wip', 'fix', 'update', 'changes', 'stuff', 'misc']
    if subject.lower() in vague_patterns or (len(subject) < 15 and not CC_PATTERN.match(subject)):
        issues.append('message too vague')
    
    return len(issues), issues


def infer_type_from_diff(sha: str) -> str:
    """Infer commit type from changed files."""
    stat = git_show_stat(sha)
    stat_lower = stat.lower()
    
    if 'test' in stat_lower or 'spec' in stat_lower:
        return 'test'
    if 'readme' in stat_lower or '.md' in stat_lower or 'doc' in stat_lower:
        return 'docs'
    if 'package.json' in stat_lower or 'requirements' in stat_lower or 'setup.py' in stat_lower:
        return 'build'
    if '.github/' in stat_lower or 'ci' in stat_lower:
        return 'ci'
    if 'config' in stat_lower or '.json' in stat_lower or '.toml' in stat_lower:
        return 'chore'
    return 'feat'  # default


def infer_scope_from_diff(sha: str) -> Optional[str]:
    """Infer scope from changed files."""
    stat = git_show_stat(sha)
    lines = [line for line in stat.split('\n') if '|' in line]
    if not lines:
        return None
    
    # Get common directory prefix
    paths = [line.split('|')[0].strip() for line in lines]
    if len(paths) == 1:
        parts = paths[0].split('/')
        if len(parts) > 1:
            return parts[0]
    
    # Find common prefix
    prefixes = set()
    for p in paths:
        parts = p.split('/')
        if len(parts) > 1:
            prefixes.add(parts[0])
    
    if len(prefixes) == 1:
        return prefixes.pop()
    return None


def extract_change_from_body(body: str) -> Optional[str]:
    """Extract meaningful description from Markdown commit body."""
    lines = body.split('\n')
    
    for i, line in enumerate(lines):
        # Look for **Change:** bullet point
        if line.strip().startswith('- **Change:**'):
            desc = line.split('**Change:**', 1)[1].strip()
            if desc and desc.lower() not in ['none', 'n/a', '-']:
                return desc
        # Look for the first meaningful line after ## Changes Made
        if '## Changes Made' in line:
            for j in range(i + 1, min(i + 5, len(lines))):
                next_line = lines[j].strip()
                if next_line.startswith('- ') and '**' not in next_line:
                    return next_line[2:].strip()
    
    # Fallback: look for first non-header, non-empty line
    for line in lines[1:10]:  # Skip first line (subject)
        line = line.strip()
        if line and not line.startswith('#') and not line.startswith('```'):
            if len(line) > 10:
                return line[:60] if len(line) > 60 else line
    
    return None


def rewrite_message(sha: str, old_msg: str) -> str:
    """Generate a Conventional Commits compliant message."""
    subject = old_msg.split('\n')[0].strip()
    
    # Already compliant? Return as-is
    if CC_PATTERN.match(subject):
        # Just fix past tense if present
        if ':' in subject:
            prefix, desc = subject.split(':', 1)
            desc = desc.strip()
            words = desc.split()
            if words and words[0].lower() in PAST_TENSE_WORDS:
                imperative_map = {
                    'added': 'add', 'fixed': 'fix', 'updated': 'update',
                    'removed': 'remove', 'changed': 'change', 'implemented': 'implement',
                    'created': 'create', 'deleted': 'delete', 'modified': 'modify'
                }
                words[0] = imperative_map.get(words[0].lower(), words[0])
                return f"{prefix}: {' '.join(words)}"
        return subject
    
    # Infer type and scope
    commit_type = infer_type_from_diff(sha)
    scope = infer_scope_from_diff(sha)
    
    # Try to extract description from body if subject is unhelpful
    desc = subject
    if subject.startswith('#') or len(subject) < 15:
        body_desc = extract_change_from_body(old_msg)
        if body_desc:
            desc = body_desc
    
    # Clean up the description
    for prefix in ['[WIP]', 'WIP:', 'WIP', '[FIX]', '[FEAT]', '[UPDATE]', '# ']:
        if desc.upper().startswith(prefix.upper()):
            desc = desc[len(prefix):].strip()
    
    # Convert to imperative if starts with past tense
    words = desc.split()
    if words:
        imperative_map = {
            'added': 'add', 'fixed': 'fix', 'updated': 'update',
            'removed': 'remove', 'changed': 'change', 'implemented': 'implement',
            'created': 'create', 'deleted': 'delete', 'modified': 'modify'
        }
        if words[0].lower() in imperative_map:
            words[0] = imperative_map[words[0].lower()]
            desc = ' '.join(words)
    
    # Lowercase first letter if it's uppercase (for consistency)
    if desc and desc[0].isupper() and not desc.startswith('I '):
        desc = desc[0].lower() + desc[1:]
    
    # Build new message
    if scope:
        new_msg = f"{commit_type}({scope}): {desc}"
    else:
        new_msg = f"{commit_type}: {desc}"
    
    # Truncate if too long
    if len(new_msg) > 72:
        new_msg = new_msg[:69] + '...'
    
    return new_msg


def analyze_commits(scope: str = 'HEAD~20..HEAD') -> tuple[list[Proposal], list[Skipped]]:
    """Analyze commits and generate proposals."""
    commits = git_log(scope)
    proposals = []
    skipped = []
    
    for sha, body in commits:
        score, issues = score_message(body)
        
        if score == 0:
            skipped.append(Skipped(sha=sha[:8], reason='already compliant'))
        else:
            new_message = rewrite_message(sha, body)
            old_subject = body.split('\n')[0].strip()
            
            # Only propose if actually different
            if new_message != old_subject:
                proposals.append(Proposal(
                    sha=sha[:8],
                    old_message=old_subject,
                    new_message=new_message,
                    reason='; '.join(issues)
                ))
            else:
                skipped.append(Skipped(sha=sha[:8], reason='no improvement found'))
    
    return proposals, skipped


def get_staged_changes() -> Optional[str]:
    """Get a commit message for staged changes."""
    result = subprocess.run(
        ['git', 'diff', '--cached', '--name-only'],
        cwd=REPO_ROOT, capture_output=True, text=True
    )
    if result.returncode != 0 or not result.stdout.strip():
        return None
    
    files = [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
    if not files:
        return None
    
    # Infer type from staged files
    files_str = ' '.join(files).lower()
    if 'test' in files_str:
        commit_type = 'test'
    elif '.md' in files_str or 'readme' in files_str:
        commit_type = 'docs'
    elif 'fix' in files_str:
        commit_type = 'fix'
    else:
        commit_type = 'feat'
    
    # Infer scope
    scope = None
    if len(files) == 1:
        parts = files[0].split('/')
        if len(parts) > 1:
            scope = parts[0]
    
    # Build message
    if len(files) == 1:
        desc = f"update {files[0]}"
    else:
        desc = f"update {len(files)} files"
    
    if scope:
        return f"{commit_type}({scope}): {desc}"
    return f"{commit_type}: {desc}"


def main():
    parser = argparse.ArgumentParser(
        description='Analyze git commits for Conventional Commits compliance'
    )
    parser.add_argument(
        '--scope', default='HEAD~20..HEAD',
        help='Git log scope (default: HEAD~20..HEAD)'
    )
    parser.add_argument(
        '--out', default='commit_proposals.json',
        help='Output file for proposals (default: commit_proposals.json)'
    )
    parser.add_argument(
        '--json', action='store_true',
        help='Output JSON to stdout instead of file'
    )
    
    args = parser.parse_args()
    
    proposals, skipped = analyze_commits(args.scope)
    current_work = get_staged_changes()
    
    output = {
        'replacements': [asdict(p) for p in proposals],
        'skipped': [asdict(s) for s in skipped],
        'current_work_message': current_work
    }
    
    if args.json:
        print(json.dumps(output, indent=2))
    else:
        Path(args.out).write_text(json.dumps(output, indent=2), encoding='utf-8')
        print(f"Wrote {len(proposals)} proposals to {args.out}")
        print(f"Skipped {len(skipped)} commits (already compliant or no improvement)")
        if current_work:
            print(f"Suggested message for staged changes: {current_work}")


if __name__ == '__main__':
    main()
