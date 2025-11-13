# Dynamic Project Detection in main3.py

## Overview

main3.py now features **automatic project root detection**, eliminating the need for hardcoded project paths. Both Option 2 (Configure MCP Servers) and Option 4 (Install All to Project) use this feature to deploy configs to the correct project directory.

## How It Works

### Detection Algorithm

When main3.py runs, it automatically detects the project root using this priority order:

1. **Git Repository Root** (if available)
   - Searches for `.git` directory starting from CONFIG_DIR
   - Walks up the directory tree until it finds `.git`
   - Returns the directory containing `.git`

2. **Script Directory** (fallback)
   - If not in a Git repository
   - Uses the directory containing main3.py (CONFIG_DIR)

### Key Functions

```python
def get_project_root() -> Path:
    """Returns the detected project root directory"""
    # Tries to find .git directory
    # Falls back to script directory if not found

def get_app_locations() -> Dict[str, Dict[str, str]]:
    """Returns app locations with {project_root} dynamically substituted"""
    # Calls get_project_root()
    # Replaces {project_root} placeholders in template
    # Returns complete app locations
```

## Usage Scenarios

### Scenario 1: Project is a Git Repository

```
my-project/
├── .git/                    ← Git repository marker
├── main3.py                 ← Can be anywhere
├── src/
│   └── main.py
└── config/
    └── settings.json
```

**What happens:**
- main3.py detects `/my-project` as project root
- Option 4 deploys to `/my-project/.vscode/mcp.json`
- Option 2 deploys to `/my-project/.amazonq/mcp.json`, etc.
- Works from any directory within the project

**Command examples:**
```bash
# Run from project root
cd /my-project && python main3.py

# Run from subdirectory - still works!
cd /my-project/src && python ../main3.py

# Run from anywhere
python /path/to/my-project/main3.py
```

### Scenario 2: Non-Git Project

```
my-project/
├── main3.py                 ← Script directory is the project root
├── src/
│   └── main.py
└── config/
    └── settings.json
```

**What happens:**
- main3.py detects `/my-project` (its own directory) as project root
- Option 4 deploys to `/my-project/.vscode/mcp.json`
- Works from `/my-project` directory

### Scenario 3: main3.py in Subdirectory

```
my-project/
├── .git/                    ← Git repository marker
├── scripts/
│   └── main3.py             ← Script is in subdirectory
├── src/
│   └── main.py
└── config/
    └── settings.json
```

**What happens:**
- main3.py detects `/my-project` (Git root) as project root
- Not `/my-project/scripts/` (script directory)
- Option 4 deploys to `/my-project/.vscode/mcp.json` (correct location!)
- Works correctly even though script is in subdirectory

## Project-Level Files Created

When "Install All to Project" (Option 4) is selected, main3.py creates these files in the detected project root:

```
{detected_project_root}/
│
├── .amazonq/
│   └── mcp.json
├── .gemini/
│   └── settings.json
├── .vscode/
│   └── mcp.json
├── .kilocode/
│   └── mcp.json
├── .roo/
│   └── mcp.json
├── .codex/
│   └── config.toml
│
├── .mcp.json
├── .claude_desktop_config.json
├── .clinerules
└── opencode.json
```

## Option 2 (Configure MCP Servers) - Automatic Deployment

When you configure servers for a CLI tool (Option 2), main3.py:

1. Detects the project root
2. Shows the detected path to you
3. Deploys to:
   - **Global locations** (user home, AppData, etc.)
   - **Project locations** (auto-detected root)

Example output:
```
Detected project root: C:\Users\matt\Dropbox\projects\MyProject
Deploying configuration to app locations...
✓ C:\Users\matt\.aws\amazonq\mcp.json
✓ C:\Users\matt\Dropbox\projects\MyProject\.amazonq\mcp.json
```

## Option 4 (Install All to Project) - Full Sync

When you install all servers to project (Option 4), main3.py:

1. Detects the project root
2. Shows the detected path
3. Deploys the same servers to ALL project CLI configs
4. Shows success/failure for each

Example output:
```
Detected project root: C:\Users\matt\Dropbox\projects\MyProject
Installing 5 servers to ALL project configurations...

✓ Amazon Q
✓ Claude Code (VSCode)
✓ Claude Desktop
✓ Cline
✓ Gemini CLI
✓ GitHub Copilot
✓ Kilo (Cursor fork)
✓ Opencode
✓ Roo Code
✓ Codex

Installed 5 servers to 10 project locations!
```

## Git Integration Benefits

### Works with Git Workflows

Since main3.py detects Git repo root, you can:

1. **Distribute the script with your project**
   ```bash
   git add scripts/main3.py
   git commit -m "Add MCP config manager"
   git push
   ```

2. **Team members can run it from anywhere**
   ```bash
   # Everyone's project root is detected correctly
   python scripts/main3.py
   ```

3. **Deploy to consistent locations**
   - All configs go to same relative paths in Git repo
   - Can commit project-level configs
   - Reproducible across team

4. **IDE integration**
   - Can be called from VS Code, JetBrains, etc.
   - Detects project root correctly even from IDE

## Configuration File Format

The `APP_LOCATIONS_TEMPLATE` uses `{project_root}` placeholder:

```python
"project": {
    "amazonq_mcp.json": "{project_root}/.amazonq/mcp.json",
    "claude_code_mcp.json": "{project_root}/.mcp.json",
    "cline_mcp_settings.json": "{project_root}/.clinerules",
    # ... etc
}
```

When `get_app_locations()` is called:
- Detects project root
- Replaces `{project_root}` with actual path
- Returns ready-to-use locations

## Environment Variables Still Supported

Global (non-project) locations still use environment variables:

```python
"windows": {
    "cline_mcp_settings.json": r"%APPDATA%\Code\User\...",
    "codex_config.toml": r"%USERPROFILE%\.codex\config.toml",
}
```

These are expanded using `os.path.expandvars()`.

## Troubleshooting

### Project root not detected correctly?

Check where the `.git` directory is:
```bash
# Find .git from current location
find . -name ".git" -type d

# Current directory contains
ls -la | grep .git
```

If `.git` is multiple levels up and not found:
- Ensure the search walks all the way to filesystem root
- main3.py will fall back to script directory

### Deployed to wrong location?

1. Run main3.py and note the "Detected project root" message
2. Verify `.git` is in that location or a parent
3. Check that `.git` is a directory (not a file in submodules)

### Want to use non-Git project root?

1. Place main3.py in your project root directory
2. Run main3.py from that directory
3. It will use the script's directory as project root

## Examples

### Example 1: Install All to GitHub Project

```bash
# Clone your repo
git clone https://github.com/user/myproject.git
cd myproject

# Copy main3.py to project (or it was already there)
cp ../main3.py .

# Run the manager
python main3.py

# Select Option 1: Claude Code
# Select Option 2: Configure servers (add playwright, github)
# Select Option 4: Install All to Project

# Now myproject/ has:
# .vscode/mcp.json
# .amazonq/mcp.json
# .kilocode/mcp.json
# etc. - all configured!

# Commit the changes
git add .vscode/mcp.json .amazonq/ .kilocode/ ...
git commit -m "Add MCP server configs"
git push
```

### Example 2: Use from Scripts Directory

```bash
# Project structure
myproject/
├── .git/
├── scripts/
│   ├── main3.py           ← main3.py is here
│   └── deploy.sh
└── src/
    └── main.py

# From anywhere in project
cd myproject
python scripts/main3.py

# Or from src directory
cd myproject/src
python ../scripts/main3.py

# Both detect myproject/ as root (Git repo)
```

### Example 3: Multiple Projects

```bash
# Project 1 (Git)
~/projects/app1/.git
~/projects/app1/main3.py
→ Detects ~/projects/app1 as root

# Project 2 (Git)
~/projects/app2/.git
~/projects/app2/tools/main3.py
→ Detects ~/projects/app2 as root

# Project 3 (Non-Git)
~/projects/app3/main3.py
→ Detects ~/projects/app3 as root (no .git found)

# Each main3.py deploys to correct project!
```

## Summary

✅ **No hardcoded paths** - Automatic detection
✅ **Works anywhere** - Run from any directory in project
✅ **Git-aware** - Detects Git repo root
✅ **Fallback** - Uses script directory if not in Git
✅ **Both options** - Option 2 AND Option 4 use dynamic detection
✅ **Team-friendly** - Reproducible across team members
✅ **Commitable configs** - Project-level configs can be in Git

---

**Version:** 1.0
**Last Updated:** November 2025
