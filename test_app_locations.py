#!/usr/bin/env python3
"""Test to see exactly what get_app_locations() returns"""

import sys
sys.path.insert(0, r"C:\Users\matt\Dropbox\projects\LLM")

# Import from main3.py
from main3 import get_app_locations, LLM_DISPLAY_NAMES

print("=" * 70)
print("GET_APP_LOCATIONS TEST")
print("=" * 70)

locations = get_app_locations()

print("\nAvailable location types:")
for location_type in sorted(locations.keys()):
    print(f"\n  [{location_type}]")
    for cli_name in sorted(locations[location_type].keys()):
        path = locations[location_type][cli_name]
        if isinstance(path, list):
            print(f"    {cli_name}: (list with {len(path)} items)")
            for i, p in enumerate(path):
                print(f"      [{i}] {p}")
        else:
            print(f"    {cli_name}: {path}")

print("\n" + "=" * 70)
print("\nTest: Claude Code deployment")
print("-" * 70)

cli_filename = "claude_code_mcp.json"
print(f"\nCLI: {cli_filename}")

for location_type in ["windows", "project"]:
    locations_dict = locations.get(location_type, {})
    target_paths = locations_dict.get(cli_filename)
    print(f"\n  {location_type}:")
    if target_paths:
        print(f"    ✓ Found: {target_paths}")
    else:
        print(f"    ✗ NOT FOUND in {location_type}")
        print(f"    Available keys: {list(locations_dict.keys())}")

print("\n" + "=" * 70)
