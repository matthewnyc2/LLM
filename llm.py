#!/usr/bin/env python3
"""Utility for assembling MCP server configuration files for multiple apps."""

import copy
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set

CONFIG_DIR = Path(__file__).resolve().parent
SERVERS_DIR = CONFIG_DIR / "servers"
OUTPUT_DIR = CONFIG_DIR / "generated"
CONFIG_PATH = CONFIG_DIR / "config.json"
HISTORY_PATH = CONFIG_DIR / "history.log"

DEFAULT_CONFIG = {
    "output_directory": "generated",
    "location_type": "windows",
    "last_batch_server": None,
    "selected_llm": None,
    "selected_mcp_servers": [],
}

TEMPLATE_NAME_OVERRIDES = {
    "amazonq_mcp.json": "Amazon Q",
    "claude_code_mcp.json": "Claude Code (VSCode)",
    "claude_desktop_config.json": "Claude Desktop",
    "cline_mcp_settings.json": "Cline",
    "gemini_cli_mcp.json": "Gemini CLI",
    "github_copilot_mcp.json": "GitHub Copilot",
    "kilo_code_mcp.json": "Kilo (Cursor fork)",
    "opencode_config.json": "Opencode",
    "roo_code_mcp.json": "Roo Code",
    "codex_config.toml": "Codex",
}

CLI_LAUNCH_COMMANDS = {
    "amazon_q": "q2",
    "claude_code": "claude",
    "claude_desktop": "claude",
    "cline": "cline",
    "gemini": "cmd /c start gemini",
    "github_copilot": "copilot",
    "kilo_code": "kilocode",
    "opencode": "opencode",
    "roo_code": "roo-code",
    "codex": "codex",
}

APP_LOCATIONS = {
    "windows": {
        "amazonq_mcp.json": r"%USERPROFILE%\.aws\amazonq\mcp.json",
        "claude_code_mcp.json": r"%USERPROFILE%\.claude.json",
        "claude_desktop_config.json": r"%APPDATA%\Claude\claude_desktop_config.json",
        "cline_mcp_settings.json": r"%APPDATA%\Code\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json",
        "gemini_cli_mcp.json": r"%USERPROFILE%\.gemini\settings.json",
        "github_copilot_mcp.json": r"%APPDATA%\Code\User\settings.json",
        "kilo_code_mcp.json": r"%APPDATA%\Code\User\globalStorage\kilocode.kilo-code\settings\mcp_settings.json",
        "opencode_config.json": r"%USERPROFILE%\.config\opencode\opencode.json",
        "roo_code_mcp.json": r"%APPDATA%\Code\User\globalStorage\rooveterinaryinc.roo-cline\settings\cline_mcp_settings.json",
        "codex_config.toml": r"%USERPROFILE%\.codex\config.toml",
    },
    "unix": {
        "amazonq_mcp.json": "~/.aws/amazonq/mcp.json",
        "claude_code_mcp.json": "~/.claude.json",
        "claude_desktop_config.json": "~/Library/Application Support/Claude/claude_desktop_config.json",
        "cline_mcp_settings.json": "~/.config/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json",
        "gemini_cli_mcp.json": "~/.gemini/settings.json",
        "github_copilot_mcp.json": "~/.config/Code/User/settings.json",
        "kilo_code_mcp.json": "~/.config/Code/User/globalStorage/kilocode.kilo-code/settings/mcp_settings.json",
        "opencode_config.json": "~/.config/opencode/opencode.json",
        "roo_code_mcp.json": "~/.config/Code/User/globalStorage/rooveterinaryinc.roo-cline/settings/cline_mcp_settings.json",
        "codex_config.toml": "~/.codex/config.toml",
    },
    "project": {
        "amazonq_mcp.json": r"C:\Users\matt\Dropbox\projects\MAILSHIELD\.amazonq\mcp.json",
        "claude_code_mcp.json": r"C:\Users\matt\Dropbox\projects\MAILSHIELD\.mcp.json",
        "claude_desktop_config.json": r"C:\Users\matt\Dropbox\projects\MAILSHIELD\.claude_desktop_config.json",
        "cline_mcp_settings.json": r"C:\Users\matt\Dropbox\projects\MAILSHIELD\.clinerules",
        "gemini_cli_mcp.json": r"C:\Users\matt\Dropbox\projects\MAILSHIELD\.gemini\settings.json",
        "github_copilot_mcp.json": r"C:\Users\matt\Dropbox\projects\MAILSHIELD\.vscode\mcp.json",
        "kilo_code_mcp.json": r"C:\Users\matt\Dropbox\projects\MAILSHIELD\.kilocode\mcp.json",
        "opencode_config.json": r"C:\Users\matt\Dropbox\projects\MAILSHIELD\opencode.json",
        "roo_code_mcp.json": r"C:\Users\matt\Dropbox\projects\MAILSHIELD\.roo\mcp.json",
        "codex_config.toml": r"C:\Users\matt\Dropbox\projects\MAILSHIELD\.codex\config.toml",
    },
}


@dataclass
class ServerTemplate:
    """Represents a configuration template for a particular application."""

    filename: str
    display_name: str
    path: Path
    format: str  # json or toml
    server_order: List[str]
    server_blocks: Dict[str, object]
    metadata: Dict[str, object]
    container_key: Optional[str] = None
    header_lines: Optional[List[str]] = None

    def render(self, selected_servers: Sequence[str]) -> str:
        """Render the template including only the selected servers."""

        ordered_names = [name for name in self.server_order if name in selected_servers]
        if self.format == "json":
            payload = copy.deepcopy(self.metadata)
            servers = self.server_blocks
            container: Dict[str, object] = {}
            for name in ordered_names:
                container[name] = copy.deepcopy(servers[name])
            if self.container_key is None:
                raise RuntimeError("JSON template missing container key")
            payload[self.container_key] = container
            return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"

        if self.format == "toml":
            lines: List[str] = []
            if self.header_lines:
                lines.extend(self.header_lines)
                if self.header_lines and self.header_lines[-1].strip():
                    lines.append("")
            for name in ordered_names:
                block_lines = self.server_blocks[name]
                lines.extend(block_lines)
                if block_lines and block_lines[-1].strip():
                    lines.append("")
            # Remove trailing empty lines and ensure newline at end.
            while lines and not lines[-1].strip():
                lines.pop()
            return "\n".join(lines) + "\n"

        raise ValueError(f"Unsupported format: {self.format}")


def ensure_environment() -> None:
    """Ensure directories and default files exist."""

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    SERVERS_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_PATH.exists():
        save_config(DEFAULT_CONFIG)
    if not HISTORY_PATH.exists():
        HISTORY_PATH.touch()


def load_config() -> Dict[str, object]:
    try:
        with CONFIG_PATH.open("r", encoding="utf-8") as handle:
            config = json.load(handle)
    except (OSError, json.JSONDecodeError):
        config = copy.deepcopy(DEFAULT_CONFIG)
    config.setdefault("output_directory", DEFAULT_CONFIG["output_directory"])
    config.setdefault("location_type", DEFAULT_CONFIG["location_type"])
    config.setdefault("last_batch_server", DEFAULT_CONFIG["last_batch_server"])
    config.setdefault("selected_llm", DEFAULT_CONFIG["selected_llm"])
    config.setdefault("selected_mcp_servers", DEFAULT_CONFIG["selected_mcp_servers"])
    return config


def save_config(config: Dict[str, object]) -> None:
    with CONFIG_PATH.open("w", encoding="utf-8") as handle:
        json.dump(config, handle, indent=2)


def log_history(event: str, details: Optional[Dict[str, object]] = None) -> None:
    entry = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "event": event,
        "details": details or {},
    }
    try:
        with HISTORY_PATH.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry) + "\n")
    except OSError:
        pass


def display_history() -> None:
    print("\n--- History Log ---")
    try:
        with HISTORY_PATH.open("r", encoding="utf-8") as handle:
            for raw_line in handle:
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    print(line)
                    continue
                timestamp = entry.get("timestamp", "?")
                event = entry.get("event", "?")
                details = entry.get("details", {})
                print(f"[{timestamp}] {event}: {details}")
    except OSError as exc:
        print(f"Unable to read history: {exc}")
    print("-------------------\n")


def friendly_name(filename: str) -> str:
    if filename in TEMPLATE_NAME_OVERRIDES:
        return TEMPLATE_NAME_OVERRIDES[filename]
    stem = Path(filename).stem.replace("_", " ")
    return stem.title()


def load_json_template(path: Path) -> ServerTemplate:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    container_key = None
    for key in ("mcpServers", "mcp_servers", "mcp"):
        if key in data:
            container_key = key
            break
    if container_key is None:
        raise ValueError(f"Could not locate MCP server container in {path}")

    servers = data[container_key]
    if not isinstance(servers, dict):
        raise ValueError(f"Unexpected server container type in {path}")

    metadata = {key: value for key, value in data.items() if key != container_key}
    server_order = list(servers.keys())

    return ServerTemplate(
        filename=path.name,
        display_name=friendly_name(path.name),
        path=path,
        format="json",
        server_order=server_order,
        server_blocks=servers,
        metadata=metadata,
        container_key=container_key,
    )


def load_toml_template(path: Path) -> ServerTemplate:
    header_lines: List[str] = []
    server_blocks: Dict[str, List[str]] = {}
    server_order: List[str] = []

    current_name: Optional[str] = None
    current_block: List[str] = []

    with path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.rstrip("\n")
            if current_name is None:
                if line.startswith("[mcp_servers."):
                    current_name = line[len("[mcp_servers.") :].rstrip("]")
                    server_order.append(current_name)
                    current_block = [line]
                else:
                    header_lines.append(line)
            else:
                if line.startswith("[mcp_servers."):
                    server_blocks[current_name] = current_block
                    current_name = line[len("[mcp_servers.") :].rstrip("]")
                    server_order.append(current_name)
                    current_block = [line]
                else:
                    current_block.append(line)

    if current_name is not None:
        server_blocks[current_name] = current_block

    # Remove trailing blank header lines.
    while header_lines and not header_lines[-1].strip():
        header_lines.pop()

    return ServerTemplate(
        filename=path.name,
        display_name=friendly_name(path.name),
        path=path,
        format="toml",
        server_order=server_order,
        server_blocks=server_blocks,
        metadata={},
        header_lines=header_lines,
    )


def load_templates() -> List[ServerTemplate]:
    templates: List[ServerTemplate] = []
    for path in sorted(SERVERS_DIR.iterdir()):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".json", ".toml"}:
            continue
        try:
            if path.suffix.lower() == ".json":
                template = load_json_template(path)
            else:
                template = load_toml_template(path)
        except ValueError as exc:
            print(f"Skipping {path.name}: {exc}")
            continue
        templates.append(template)
    return templates


def get_all_mcp_servers(templates: List[ServerTemplate]) -> List[str]:
    """Get all unique MCP server names from all templates."""
    all_servers: Set[str] = set()
    for template in templates:
        all_servers.update(template.server_order)
    return sorted(all_servers)


def select_llm(templates: List[ServerTemplate], config: Dict[str, object]) -> None:
    """Screen to select LLM with numbered list."""
    print("\n=== Select LLM ===")
    options = [template.display_name for template in templates]
    
    for idx, name in enumerate(options, start=1):
        print(f"  {idx}. {name}")
    print("  X. Cancel")
    
    choice = input("Select LLM: ").strip().lower()
    if choice == "x":
        return
    
    if choice.isdigit():
        index = int(choice)
        if 1 <= index <= len(options):
            selected_template = templates[index - 1]
            config["selected_llm"] = selected_template.filename
            save_config(config)
            print(f"Selected: {selected_template.display_name}\n")
            return
    
    print("Invalid selection.\n")


def select_mcp_servers(templates: List[ServerTemplate], config: Dict[str, object]) -> None:
    """Screen to select MCP servers from all available servers."""
    all_servers = get_all_mcp_servers(templates)
    selected_servers = set(config.get("selected_mcp_servers", []))
    
    while True:
        print("\n=== Select MCP Servers ===")
        for idx, server in enumerate(all_servers, start=1):
            mark = "[x]" if server in selected_servers else "[ ]"
            print(f"  {idx:>2}. {mark} {server}")
        print("  A. Toggle all")
        print("  X. Return to main menu")
        
        choice = input("Select server to toggle: ").strip().lower()
        if choice == "x":
            break
        if choice == "a":
            if len(selected_servers) == len(all_servers):
                selected_servers.clear()
            else:
                selected_servers = set(all_servers)
            continue
        if choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(all_servers):
                server = all_servers[idx - 1]
                if server in selected_servers:
                    selected_servers.remove(server)
                else:
                    selected_servers.add(server)
                continue
        print("Invalid selection.")
    
    config["selected_mcp_servers"] = list(selected_servers)
    save_config(config)


def launch_llm_with_config(templates: List[ServerTemplate], config: Dict[str, object]) -> None:
    """Launch LLM and replace its config with selected MCP servers."""
    selected_llm = config.get("selected_llm")
    if not selected_llm:
        print("No LLM selected. Please select an LLM first.\n")
        return
    
    # Find the template
    template = None
    for t in templates:
        if t.filename == selected_llm:
            template = t
            break
    
    if not template:
        print("Selected LLM template not found.\n")
        return
    
    selected_servers = config.get("selected_mcp_servers", [])
    
    # Generate config with selected servers
    output_directory = Path(config.get("output_directory", "generated"))
    if not output_directory.is_absolute():
        output_directory = CONFIG_DIR / output_directory
    output_directory.mkdir(parents=True, exist_ok=True)
    
    output_path = output_directory / template.filename
    
    # Create new server blocks with only selected servers
    filtered_blocks = {}
    for server in selected_servers:
        if server in template.server_blocks:
            filtered_blocks[server] = template.server_blocks[server]
    
    # Create temporary template with filtered servers
    temp_template = ServerTemplate(
        filename=template.filename,
        display_name=template.display_name,
        path=template.path,
        format=template.format,
        server_order=[s for s in template.server_order if s in selected_servers],
        server_blocks=filtered_blocks,
        metadata=template.metadata,
        container_key=template.container_key,
        header_lines=template.header_lines,
    )
    
    document = temp_template.render(selected_servers)
    with output_path.open("w", encoding="utf-8") as handle:
        handle.write(document)
    
    # Copy to app location
    location_type = config.get("location_type", "windows")
    locations = APP_LOCATIONS.get(location_type, {})
    if template.filename in locations:
        app_location_raw = locations[template.filename]
        app_location = Path(os.path.expandvars(app_location_raw)).expanduser()
        app_location.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            shutil.copy2(output_path, app_location)
            print(f"Updated config at {app_location}")
        except Exception as exc:
            print(f"Failed to copy config: {exc}")
    
    # Launch LLM
    cli_key = template.filename.replace(".json", "").replace(".toml", "").replace("_mcp", "").replace("_settings", "").replace("_config", "")
    cli_map = {
        "amazonq": "amazon_q",
        "claude_code": "claude_code",
        "claude_desktop": "claude_desktop",
        "cline": "cline",
        "gemini_cli": "gemini",
        "github_copilot": "github_copilot",
        "kilo_code": "kilo_code",
        "opencode": "opencode",
        "roo_code": "roo_code",
        "codex": "codex",
    }
    
    cli_key = cli_map.get(cli_key, cli_key)
    cmd = CLI_LAUNCH_COMMANDS.get(cli_key)
    
    if cmd:
        print(f"Launching {template.display_name}...\n")
        log_history("launch_llm", {"template": template.filename, "command": cmd})
        try:
            if sys.platform == "win32":
                subprocess.Popen(f"start {cmd}", shell=True)
            else:
                subprocess.Popen([cmd])
        except Exception as exc:
            print(f"Failed to launch {template.display_name}: {exc}\n")
    else:
        print(f"No launch command configured for {template.display_name}\n")


def batch_commands(templates: List[ServerTemplate], config: Dict[str, object]) -> None:
    """Batch command mode with simplified interface."""
    print("\n=== Batch Commands ===")
    print("Enter commands and select which LLM to execute them with.")
    print("Press Ctrl+C to exit.\n")
    
    while True:
        try:
            cmd = input("Enter command (or 'quit' to exit): ").strip()
            if not cmd or cmd.lower() in ("quit", "exit", "q"):
                break
            
            # Show LLM options
            print("\nSelect LLM:")
            options = [template.display_name for template in templates]
            
            # Get last used or default
            last_server = config.get("last_batch_server")
            default_idx = None
            if last_server:
                for idx, template in enumerate(templates):
                    if template.filename == last_server:
                        default_idx = idx
                        break
            
            for idx, name in enumerate(options, start=1):
                marker = " (default)" if default_idx is not None and idx - 1 == default_idx else ""
                print(f"  {idx}. {name}{marker}")
            print("  X. Cancel")
            
            choice = input("Select LLM (Enter for default): ").strip().lower()
            if choice == "x":
                continue
            
            selected_idx = default_idx
            if choice and choice.isdigit():
                idx = int(choice)
                if 1 <= idx <= len(options):
                    selected_idx = idx - 1
                else:
                    print("Invalid selection.\n")
                    continue
            elif choice and not choice.isdigit():
                print("Invalid selection.\n")
                continue
            
            if selected_idx is None:
                print("No LLM selected.\n")
                continue
            
            selected_template = templates[selected_idx]
            config["last_batch_server"] = selected_template.filename
            save_config(config)
            
            print(f"Executing with {selected_template.display_name}: {cmd}\n")
            log_history("batch_command", {"template": selected_template.filename, "command": cmd})
            
            try:
                result = subprocess.run(cmd, shell=True, capture_output=False)
                if result.returncode != 0:
                    print(f"Command exited with code {result.returncode}")
            except Exception as exc:
                print(f"Error executing command: {exc}")
            
            print()
            
        except KeyboardInterrupt:
            print("\n\nBatch mode exited.")
            break


def show_main_menu(config: Dict[str, object]) -> None:
    """Show simplified main menu."""
    print("\n=== MCP Configuration Builder ===")
    
    # Show selected LLM
    selected_llm = config.get("selected_llm")
    if selected_llm:
        llm_name = friendly_name(selected_llm)
        print(f"Selected LLM: {llm_name}")
    else:
        print("Selected LLM: None")
    
    # Show selected MCP servers
    selected_servers = config.get("selected_mcp_servers", [])
    if selected_servers:
        print(f"MCP Servers: {', '.join(selected_servers)}")
    else:
        print("MCP Servers: None")
    
    print("===============================\n")
    
    print("Options:")
    print("  1. Select LLM")
    print("  2. Select MCP Servers") 
    print("  3. Launch LLM")
    print("  4. Batch Commands")
    print("  5. History")
    print("  6. Exit")


def main() -> None:
    ensure_environment()
    templates = load_templates()
    if not templates:
        print("No templates found in", SERVERS_DIR)
        return

    config = load_config()

    while True:
        show_main_menu(config)
        choice = input("Choose an option: ").strip()

        if choice == "1":
            select_llm(templates, config)
        elif choice == "2":
            select_mcp_servers(templates, config)
        elif choice == "3":
            launch_llm_with_config(templates, config)
        elif choice == "4":
            batch_commands(templates, config)
        elif choice == "5":
            display_history()
        elif choice == "6":
            print("Goodbye!")
            break
        else:
            print("Invalid option.\n")


if __name__ == "__main__":
    main()
