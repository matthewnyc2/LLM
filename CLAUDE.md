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

### Run the application
```bash
python llm.py
```

### View execution history
```bash
python llm.py
# Then select option 5 from the menu
```

## Key Architecture & Code Structure

### Main Entry Point
- **`llm.py`**: The primary application with interactive UI for LLM and MCP server selection, configuration deployment, and batch command execution

### Core Data Flow

1. **Template Loading** (`load_templates()` in llm.py, ~lines 293-309):
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

- **`ServerTemplate`** (dataclass, ~line 96): Represents a single LLM's configuration template with methods to parse and render configs
- **`load_templates()`** (~line 293): Discovers and loads all templates from `servers/` directory
- **`select_llm()`** (~line 320): Interactive menu for LLM selection
- **`select_mcp_servers()`** (~line 345): Multi-select menu for enabling/disabling MCP servers
- **`launch_llm_with_config()`** (~line 382): Deploys config to app location and launches the LLM interactively
- **`batch_commands()`** (~line 479): Non-interactive batch execution with command input and output capture
- **`show_main_menu()`** (~line 550): Renders the main interactive menu

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

## WSL Support for Cline

When running llm.py on Windows and launching Cline, the application automatically uses WSL (Windows Subsystem for Linux) to launch Cline. This ensures cross-platform compatibility even when the main application is run from Windows.

The implementation automatically detects:
- If running on Windows (`sys.platform == "win32"`)
- If the selected LLM is Cline
- Then launches via: `wsl -e bash -c cline`

## File Organization

```
servers/              # LLM application templates (JSON/TOML format)
generated/            # Output directory for generated configs
config.json          # Persistent user selections
history.log          # Audit log of all operations
llm.py               # Primary application
```

## Supported LLM Applications

The following LLM applications are supported:
- **Amazon Q**: AWS's AI assistant
- **Claude Code (VSCode)**: Claude AI integration for VSCode
- **Claude Desktop**: Anthropic's desktop application
- **Cline**: Terminal-based LLM interface (with WSL support on Windows)
- **Gemini CLI**: Google's Gemini command-line interface
- **GitHub Copilot**: GitHub's AI coding assistant
- **Kilo (Cursor fork)**: Cursor-based code editor
- **Opencode**: Open-source code assistant
- **Codex**: OpenAI's code generation model

## Testing & Debugging

- Check `config.json` to verify selections are being persisted correctly
- Review `history.log` to see the sequence of operations
- Check `generated/` directory to see deployed configs before they're copied to app locations
- To test with different platform locations, modify `location_type` in `config.json` between "windows", "unix", and "project"
