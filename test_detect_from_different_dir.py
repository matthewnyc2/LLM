#!/usr/bin/env python3
"""Test project detection when main3.py is run from a different directory"""

from pathlib import Path

def get_project_root_from(script_location):
    """Simulate get_project_root() but from a different script location"""
    try:
        current = script_location
        while current != current.parent:
            if (current / ".git").exists():
                return current
            current = current.parent
    except Exception:
        pass
    return script_location

print("=" * 70)
print("PROJECT DETECTION TEST FROM DIFFERENT LOCATIONS")
print("=" * 70)

# Test 1: Running from LLM directory
print("\n[Test 1] If main3.py is in C:\\Users\\matt\\Dropbox\\projects\\LLM")
script_dir = Path(r"C:\Users\matt\Dropbox\projects\LLM")
detected = get_project_root_from(script_dir)
print(f"  Script location: {script_dir}")
print(f"  Detected project root: {detected}")
print(f"  Files would be created in: {detected}\\.mcp.json")

# Test 2: Running from MAILSHIELD directory (if it exists)
print("\n[Test 2] If main3.py is copied to C:\\Users\\matt\\Dropbox\\projects\\MAILSHIELD")
script_dir = Path(r"C:\Users\matt\Dropbox\projects\MAILSHIELD")
detected = get_project_root_from(script_dir)
print(f"  Script location: {script_dir}")
print(f"  Detected project root: {detected}")
print(f"  Files would be created in: {detected}\\.mcp.json")
print(f"  Directory exists: {script_dir.exists()}")

# Test 3: Running from a subdirectory
print("\n[Test 3] If main3.py is in a subdirectory of a project")
script_dir = Path(r"C:\Users\matt\Dropbox\projects\LLM\scripts\main3.py").parent
detected = get_project_root_from(script_dir)
print(f"  Script location: {script_dir}")
print(f"  Detected project root: {detected}")
print(f"  Files would be created in: {detected}\\.mcp.json")

print("\n" + "=" * 70)
print("IMPORTANT: main3.py must be IN the project directory it manages!")
print("=" * 70)
