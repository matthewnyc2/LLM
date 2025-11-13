# Quick Reference - main3.py Dynamic Project Detection

## What Gets Created in Your Project Root

When you use **Option 4 (Install All to Project)**, these files/folders are created:

```
project_root/
├── .amazonq/
│   └── mcp.json              [JSON] Amazon Q config
│
├── .gemini/
│   └── settings.json         [JSON] Gemini CLI config
│
├── .vscode/
│   └── mcp.json              [JSON] Claude Code & GitHub Copilot
│
├── .kilocode/
│   └── mcp.json              [JSON] Kilo Code config
│
├── .roo/
│   └── mcp.json              [JSON] Roo Code config
│
├── .codex/
│   └── config.toml           [TOML] Codex config (TOML format!)
│
├── .mcp.json                 [JSON] Claude Code (root level)
├── .claude_desktop_config.json [JSON] Claude Desktop
├── .clinerules               [JSON] Cline
├── opencode.json             [JSON] Opencode (root level)
│
└── [your other project files...]
```

## Detection Logic

**Project Root Detection Order:**

1. **Is there a `.git` directory?**
   - Walks up directory tree to find `.git`
   - If found → Uses that directory as project root

2. **No `.git` found?**
   - Uses main3.py's directory as project root

## Both Options Auto-Deploy

### Option 2: Configure MCP Servers
```
Select: 1 (Select CLI)
Select: 2 (Configure Servers)
→ Automatically deploys to BOTH:
  - Global locations (user home, AppData, etc.)
  - Project locations (detected root)
```

### Option 4: Install All to Project
```
Select: 1 (Select CLI)
Select: 2 (Configure Servers)
Select: 4 (Install All to Project)
→ Deploys to ALL 10 CLI project configs at once
```

## Usage Examples

### Example 1: Simple Git Project

```bash
cd ~/projects/myapp
python main3.py
  → Detects ~/projects/myapp as root
  → Creates .vscode/mcp.json in ~/projects/myapp/
```

### Example 2: main3.py in Subdirectory

```bash
cd ~/projects/myapp/scripts
python main3.py
  → Finds .git in ~/projects/myapp/
  → Still creates configs in ~/projects/myapp/ (correct!)
```

### Example 3: Non-Git Project

```bash
cd ~/projects/legacy_project
python main3.py
  → No .git found
  → Uses script directory as root
  → Creates .vscode/mcp.json in ~/projects/legacy_project/
```

## What Each File Contains

All files contain MCP server configurations in JSON format (except Codex which uses TOML):

```json
{
  "mcpServers": {
    "playwright": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@microsoft/playwright-mcp"]
    },
    "github": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@github/github-mcp-server"]
    },
    "exa": {
      "type": "http",
      "url": "https://server.smithery.ai/exa/mcp?..."
    }
  }
}
```

Codex uses TOML format instead:

```toml
[mcp_servers.playwright]
type = "stdio"
command = "npx"
args = ["-y", "@microsoft/playwright-mcp"]

[mcp_servers.github]
type = "stdio"
command = "npx"
args = ["-y", "@github/github-mcp-server"]
```

## Checking What Was Deployed

**After running Option 4, verify with:**

```bash
# Check if .vscode/mcp.json was created
ls -la .vscode/mcp.json

# Check its contents
cat .vscode/mcp.json

# Check .amazonq/ directory
ls -la .amazonq/

# Verify .kilocode/ directory
ls -la .kilocode/
```

## Undoing Deployments

To remove configs from project:

```bash
# Remove specific directory
rm -rf .amazonq/
rm -rf .vscode/

# Remove root-level configs
rm .mcp.json
rm .claude_desktop_config.json
rm .clinerules
rm opencode.json

# Remove Codex directory
rm -rf .codex/
```

## Git Integration

**Committing configs to Git:**

```bash
# Add the deployed configs
git add .vscode/mcp.json
git add .amazonq/
git add .kilocode/
git add .gemini/
git add .roo/
git add .codex/
git add .mcp.json
git add .claude_desktop_config.json
git add .clinerules
git add opencode.json

# Commit
git commit -m "Add MCP server configurations for Claude Code, Cline, etc."

# Push to team
git push
```

**Team members can now:**
```bash
git clone <repo>
# Configs automatically available from project files
# All 10 CLI tools have same MCP servers configured
```

## Troubleshooting

**Q: Is my project root being detected correctly?**

A: main3.py will print:
```
Detected project root: /path/to/your/project
```

Look for this message when deploying.

**Q: Why is .git not found?**

Check if `.git` directory exists:
```bash
ls -la | grep .git
```

If using Git submodules or shallow clones, `.git` might be a file instead. main3.py only checks for directories.

**Q: Can I use this with a project without Git?**

Yes! Just place main3.py in your project root:
```
myproject/
├── main3.py
└── .vscode/
    └── mcp.json (created here)
```

## File Locations Reference

| Tool | File | Location | Format |
|------|------|----------|--------|
| Amazon Q | mcp.json | .amazonq/ | JSON |
| Claude Code | mcp.json | .vscode/ | JSON |
| Claude Desktop | .claude_desktop_config.json | root | JSON |
| Cline | .clinerules | root | JSON |
| Gemini CLI | settings.json | .gemini/ | JSON |
| GitHub Copilot | mcp.json | .vscode/ | JSON |
| Kilo Code | mcp.json | .kilocode/ | JSON |
| Opencode | opencode.json | root | JSON |
| Roo Code | mcp.json | .roo/ | JSON |
| Codex | config.toml | .codex/ | TOML |

## Summary

✓ Automatic project root detection
✓ Works with Git repos of any structure
✓ Works with non-Git projects
✓ No hardcoded paths needed
✓ Shows you the detected path
✓ Both Option 2 and Option 4 use same detection
✓ Team-friendly (can commit configs)
✓ Commitable to Git version control

---

**For detailed info:** See DYNAMIC_PROJECT_DETECTION.md
**For full guide:** See CLAUDE.md
