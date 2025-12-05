#!/usr/bin/env python3
"""Small CLI to install/uninstall/list agent manifests to the user-level agents folder.

Usage:
  python tools/install_agent.py list
  python tools/install_agent.py install <path-to-agent-file>
  python tools/install_agent.py install-repo <agent-filename>
  python tools/install_agent.py uninstall <agent-filename>

- Install accepts either a path to a JSON manifest (.json) or a markdown agent spec (.agent.md).
- install-repo looks in the repository's `.amazonq/agents` and `.github/agents` for the named file.

This aids making repo-level agents visible to local agent UIs by copying them into the user-level
agents directory (e.g., %USERPROFILE%\.aws\amazonq\agents or ~/.aws/amazonq/agents).
"""
import argparse
import os
import shutil
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
USER_DIR = Path(os.environ.get('USERPROFILE') or os.environ.get('HOME'))
DEST_DIR = USER_DIR / '.aws' / 'amazonq' / 'agents'

REPO_AGENT_DIRS = [REPO_ROOT / '.amazonq' / 'agents', REPO_ROOT / '.github' / 'agents']


def ensure_dest():
    DEST_DIR.mkdir(parents=True, exist_ok=True)


def list_user_agents():
    if not DEST_DIR.exists():
        print(f"No user agent directory found at {DEST_DIR}")
        return 1
    files = sorted(DEST_DIR.glob('*'))
    if not files:
        print(f"No agents installed in {DEST_DIR}")
        return 0
    for f in files:
        print(f.name)
    return 0


def install_from_path(path: Path):
    if not path.exists():
        print(f"Agent file not found: {path}")
        return 2
    ensure_dest()
    dest = DEST_DIR / path.name
    shutil.copy2(path, dest)
    print(f"Installed {path.name} -> {dest}")
    return 0


def find_in_repo(name: str) -> Path | None:
    for d in REPO_AGENT_DIRS:
        p = d / name
        if p.exists():
            return p
    return None


def uninstall(name: str):
    p = DEST_DIR / name
    if not p.exists():
        print(f"No installed agent named {name}")
        return 1
    p.unlink()
    print(f"Uninstalled {name} from {DEST_DIR}")
    return 0


def main():
    parser = argparse.ArgumentParser(description='Install/uninstall/list agents to user agents folder')
    sub = parser.add_subparsers(dest='cmd')

    sub.add_parser('list')

    p_install = sub.add_parser('install')
    p_install.add_argument('path', help='Path to agent file (.json or .agent.md)')

    p_install_repo = sub.add_parser('install-repo')
    p_install_repo.add_argument('name', help='Agent file name to copy from repo .amazonq/.github agent directories')

    p_uninstall = sub.add_parser('uninstall')
    p_uninstall.add_argument('name', help='Agent file name to remove from user agent folder')

    args = parser.parse_args()

    if args.cmd == 'list':
        return list_user_agents()
    elif args.cmd == 'install':
        return install_from_path(Path(args.path))
    elif args.cmd == 'install-repo':
        found = find_in_repo(args.name)
        if not found:
            print(f"Agent not found in repo agent directories: {args.name}")
            print("Search locations:")
            for d in REPO_AGENT_DIRS:
                print(' -', d)
            return 2
        return install_from_path(found)
    elif args.cmd == 'uninstall':
        return uninstall(args.name)
    else:
        parser.print_help()
        return 2


if __name__ == '__main__':
    sys.exit(main())
