#!/usr/bin/env python3
"""Test script to verify deploy_config_to_app_locations works correctly"""

from pathlib import Path
import copy
import json
import os

CONFIG_DIR = Path(__file__).resolve().parent

def get_project_root():
    """Auto-detect project root directory."""
    try:
        current = CONFIG_DIR
        while current != current.parent:
            if (current / ".git").exists():
                return current
            current = current.parent
    except Exception:
        pass
    return CONFIG_DIR

def get_app_locations():
    """Get app locations with project root dynamically substituted."""
    APP_LOCATIONS_TEMPLATE = {
        "windows": {
            "claude_code_mcp.json": r"C:\Users\matt\.claude.json",
        },
        "project": {
            "claude_code_mcp.json": "{project_root}/.mcp.json",
            "github_copilot_mcp.json": "{project_root}/.vscode/mcp.json",
        },
    }

    project_root = get_project_root()
    locations = copy.deepcopy(APP_LOCATIONS_TEMPLATE)

    # Replace {project_root} placeholders in project locations
    for cli_name, path_template in locations.get("project", {}).items():
        if isinstance(path_template, str):
            if "{project_root}" in path_template:
                relative_path = path_template.replace("{project_root}/", "")
                parts = relative_path.split("/")
                full_path = project_root.joinpath(*parts)
                locations["project"][cli_name] = str(full_path)

    return locations, project_root

# Test the functions
print("=" * 70)
print("DEPLOYMENT TEST")
print("=" * 70)

locations, project_root = get_app_locations()

print(f"\nDetected project root: {project_root}")
print(f"\nAll locations:")
print(json.dumps(locations, indent=2))

print(f"\n" + "-" * 70)
print(f"Testing Claude Code deployment paths:")
print(f"-" * 70)

cli_filename = "claude_code_mcp.json"

print(f"\nGlobal (windows) location:")
global_path = locations.get("windows", {}).get(cli_filename)
print(f"  Path: {global_path}")
if global_path:
    path_obj = Path(os.path.expandvars(global_path))
    print(f"  Expanded: {path_obj}")
    print(f"  Parent exists: {path_obj.parent.exists()}")

print(f"\nProject location:")
project_path = locations.get("project", {}).get(cli_filename)
print(f"  Path: {project_path}")
if project_path:
    path_obj = Path(os.path.expandvars(project_path))
    print(f"  Expanded: {path_obj}")
    print(f"  Parent exists: {path_obj.parent.exists()}")
    print(f"  Would create at: {path_obj}")
    if not path_obj.parent.exists():
        print(f"  ⚠ Parent directory would need to be created: {path_obj.parent}")

print(f"\n" + "-" * 70)
print(f"GitHub Copilot deployment paths:")
print(f"-" * 70)

cli_filename = "github_copilot_mcp.json"

print(f"\nProject location:")
project_path = locations.get("project", {}).get(cli_filename)
print(f"  Path: {project_path}")
if project_path:
    path_obj = Path(os.path.expandvars(project_path))
    print(f"  Expanded: {path_obj}")
    print(f"  Parent exists: {path_obj.parent.exists()}")
    print(f"  Would create at: {path_obj}")
    if not path_obj.parent.exists():
        print(f"  ⚠ Parent directory would need to be created: {path_obj.parent}")

print(f"\n" + "=" * 70)
