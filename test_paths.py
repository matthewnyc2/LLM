#!/usr/bin/env python3
"""Quick test to verify path construction in main3.py"""

from pathlib import Path
import copy

# Simulate the template and construction logic
CONFIG_DIR = Path(__file__).resolve().parent
print(f"Script directory (CONFIG_DIR): {CONFIG_DIR}\n")

# Test project root detection
def get_project_root():
    try:
        current = CONFIG_DIR
        while current != current.parent:
            if (current / ".git").exists():
                return current
            current = current.parent
    except Exception:
        pass
    return CONFIG_DIR

project_root = get_project_root()
print(f"Detected project root: {project_root}\n")

# Test template with sample paths
APP_LOCATIONS_TEMPLATE = {
    "project": {
        "amazonq_mcp.json": "{project_root}/.amazonq/mcp.json",
        "claude_code_mcp.json": "{project_root}/.mcp.json",
        "github_copilot_mcp.json": "{project_root}/.vscode/mcp.json",
        "codex_config.toml": "{project_root}/.codex/config.toml",
    }
}

print("Path construction test:")
print("-" * 60)

locations = copy.deepcopy(APP_LOCATIONS_TEMPLATE)

for cli_name, path_template in locations.get("project", {}).items():
    if isinstance(path_template, str):
        if "{project_root}" in path_template:
            relative_path = path_template.replace("{project_root}/", "")
            parts = relative_path.split("/")
            full_path = project_root.joinpath(*parts)

            print(f"\nTemplate: {path_template}")
            print(f"Relative path: {relative_path}")
            print(f"Path parts: {parts}")
            print(f"Full path: {full_path}")
            print(f"Exists: {full_path.exists()}")
            print(f"Parent exists: {full_path.parent.exists()}")

print("\n" + "-" * 60)
print("\nTest complete!")
