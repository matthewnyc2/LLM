# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an MCP Server Configuration Manager—a Python utility that allows users to dynamically select and launch different LLM applications (Claude Code, Claude Desktop, Cline, Amazon Q, Gemini, etc.) with custom MCP server configurations.

The core functionality:
- **Template-based configuration**: Server templates in `servers/` define available MCP servers for each LLM application
- **Dynamic selection UI**: Interactive menu system where users select an LLM and choose which MCP servers to enable
- **Configuration deployment**: Generates config files and copies them to the appropriate application-specific locations on disk
- **Batch execution**: Allows users to execute arbitrary commands with a selected LLM as context

## Common Development Commands

### Run the main application
```bash
python main2.py
```

### Run the configuration builder (alternative)
```bash
python llm.py
```

### View execution history
```bash
python main2.py
# Then select option 5 from the menu
```

## Key Architecture & Code Structure

### Main Entry Points
- **`main2.py`**: The primary application with interactive UI for LLM and MCP server selection, configuration deployment, and batch command execution
- **`main3.py`**: **Self-contained version** of main2.py that requires no external directories and can be run from anywhere. Auto-creates servers/ directory and templates on first run.
- **`llm.py`**: Alternative configuration builder with similar functionality but simpler templating approach
- **`fixit.py`**: A utility script that modifies and enhances `main2.py` (applies specific fixes to launch and batch behavior)

### Core Data Flow

1. **Template Loading** (`load_templates()` in main2.py, ~lines 170-210):
   - Scans `servers/` directory for JSON and TOML template files
   - Each template defines MCP server blocks in a format-specific way
   - Parses and stores server blocks with metadata

2. **Configuration Management**:
   - Persistent state stored in `config.json`:
     - `selected_llm`: Currently selected LLM template filename
     - `selected_mcp_servers`: List of enabled MCP server names
     - `location_type`: Platform identifier ("windows", "unix", "project")
     - `last_batch_llm`: Last LLM used in batch mode
   - Deployment locations defined in `APP_LOCATIONS` dict (maps platform + template to config file path)

3. **Configuration Rendering**:
   - `LLMTemplate.render()` method takes selected servers and generates the final config file
   - For JSON templates: merges server blocks into the template's container key (e.g., `mcpServers`)
   - For TOML templates: reconstructs TOML structure from header lines and server blocks
   - Written to both `generated/` directory and app-specific locations

4. **Execution Modes**:
   - **Interactive Launch**: User selects LLM → config deployed → LLM process started and waits for completion
   - **Batch Mode**: User enters command → selects LLM → config deployed → command executed non-interactively with output capture

### Key Classes & Functions

- **`LLMTemplate`** (dataclass, ~line 110): Represents a single LLM's configuration template with methods to parse and render configs
- **`load_templates()`** (~line 170): Discovers and loads all templates from `servers/` directory
- **`select_llm()`** (~line 280): Interactive menu for LLM selection
- **`select_mcp_servers()`** (~line 310): Multi-select menu for enabling/disabling MCP servers
- **`launch_llm()`** (~line 380): Deploys config to app location and launches the LLM interactively
- **`batch_commands()`** (~line 440): Non-interactive batch execution with command input and output capture
- **`main_menu()`** (~line 540): Renders the main interactive menu

### Configuration File Locations

The tool supports three location types:
- **`windows`**: User-specific Windows paths (AppData, user home directories)
- **`unix`**: Unix-style home and config directories
- **`project`**: Project-specific paths (useful for development/testing)

Location mapping is in `APP_LOCATIONS` dict, allowing the same server selection to deploy to different app configs on different platforms.

### Server Templates Format

Templates in `servers/` directory come in two formats:

**JSON Format** (most templates):
```json
{
  "metadata": "...",
  "mcpServers": {
    "serverName": { "command": "...", "args": [...] },
    "anotherServer": { ... }
  }
}
```

**TOML Format** (e.g., `codex_config.toml`):
```toml
[header content before servers]

[mcp_servers.serverName]
[server config lines]

[mcp_servers.anotherServer]
[server config lines]
```

## Important Design Patterns

1. **Template discovery is static but server selection is dynamic**: Templates define the *format* for each app, but the actual servers to include are selected from *all available servers across all templates*. This allows mixing servers designed for different apps.

2. **Cross-platform support**: Platform-specific paths are defined centrally in `APP_LOCATIONS`, allowing the same logic to work on Windows, Unix, and project-specific locations.

3. **History logging**: All significant user actions are logged to `history.log` in JSON format for audit/debugging purposes.

4. **Configuration persistence**: User selections persist across sessions in `config.json`, so repeated launches remember previous choices.

## main2.py vs main3.py

| Feature | main2.py | main3.py |
|---------|----------|----------|
| **Dependencies** | Requires servers/ directory | Self-contained, auto-creates missing files |
| **Portability** | Must run from project directory | Can run from ANY directory |
| **Bootstrap** | Requires pre-existing servers/ | Auto-generates servers/ on first run |
| **Distribution** | Tied to this project structure | Can be distributed as standalone script |
| **Template Sync** | Reads from servers/ directly | Copies from servers/ if available, generates minimal templates otherwise |
| **Features** | All features (selection, config, deployment) | Same as main2.py |
| **Status** | Production ready | Alternative for portable usage |

**When to use main2.py:**
- Working in this project directory
- Want templates synchronized with servers/ directory
- Prefer explicit file structure

**When to use main3.py:**
- Need to run from different directory
- Want a standalone distributable script
- Operating in isolated environments
- Prefer auto-healing/self-bootstrapping
- Want automatic project detection (Git or parent directory)

## Dynamic Project Detection (main3.py)

main3.py automatically detects the project directory:

1. **Git Repository Root** (Priority 1)
   - Searches for `.git` directory in current location and parent directories
   - Uses Git repo root as the project directory
   - Allows running from any subdirectory within a Git project

2. **Script Directory** (Priority 2)
   - Falls back to the directory containing main3.py
   - Used if not in a Git repository

This means:
- Place main3.py anywhere in your project
- Run it from any subdirectory
- It automatically detects the project root
- Deploys to correct project-level config paths
- **No hardcoded paths needed**

## File Organization

```
servers/              # LLM application templates (JSON/TOML format)
generated/            # Output directory for generated configs
selections/           # Per-CLI server selection history
config.json          # Persistent user selections
history.log          # Audit log of all operations
main2.py             # Primary application (requires servers/)
main3.py             # Self-contained version (auto-bootstraps)
llm.py               # Alternative implementation
fixit.py             # Enhancement/fix utility
```

## Testing & Debugging

- Check `config.json` to verify selections are being persisted correctly
- Review `history.log` to see the sequence of operations
- Check `generated/` directory to see deployed configs before they're copied to app locations
- To test with different platform locations, modify `location_type` in `config.json` between "windows", "unix", and "project"
