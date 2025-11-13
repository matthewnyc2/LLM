#!/usr/bin/env python3
"""MCP Server Configuration Manager with Interactive Selection UI - FIXED VERSION"""

import copy
import json
import os
import shutil
import subprocess
import sys
import signal
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    from colorama import init, Fore, Back, Style
    init(autoreset=True)
    COLORS_AVAILABLE = True
except ImportError:
    class Fore:
        RED = GREEN = YELLOW = BLUE = MAGENTA = CYAN = WHITE = RESET = ""
    class Back:
        BLACK = RED = GREEN = YELLOW = BLUE = MAGENTA = CYAN = WHITE = RESET = ""
    class Style:
        DIM = NORMAL = BRIGHT = RESET_ALL = ""
    COLORS_AVAILABLE = False

CONFIG_DIR = Path(__file__).resolve().parent
SERVERS_DIR = CONFIG_DIR / "servers"
OUTPUT_DIR = CONFIG_DIR / "generated"
CONFIG_PATH = CONFIG_DIR / "config.json"
HISTORY_PATH = CONFIG_DIR / "history.log"
SELECTIONS_DIR = CONFIG_DIR / "selections"

DEFAULT_CONFIG = {
    "selected_llm": None,
    "selected_mcp_servers": [],
    "output_directory": "generated",
    "location_type": "windows",
    "last_batch_llm": None,
}

LLM_DISPLAY_NAMES = {
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
    "amazonq_mcp.json": "q2",
    "claude_code_mcp.json": "claude",
    "claude_desktop_config.json": "claude",
    "cline_mcp_settings.json": "cline",
    "gemini_cli_mcp.json": "cmd /c start gemini",
    "kilo_code_mcp.json": "kilocode",
    "opencode_config.json": "opencode",
    "codex_config.toml": "codex",
}

# Simplified MCP Servers DB for testing
MCP_SERVERS_DB = {
    "Browser Automation": {
        "playwright": {
            "name": "Playwright MCP",
            "description": "Browser automation and web scraping",
            "repo": "https://github.com/microsoft/playwright-mcp",
            "config": {"type": "stdio", "command": "npx", "args": ["-y", "@microsoft/playwright-mcp"]},
        },
        "puppeteer": {
            "name": "Puppeteer MCP",
            "description": "Headless browser control via Puppeteer",
            "repo": "https://github.com/modelcontextprotocol/servers",
            "config": {"type": "stdio", "command": "npx", "args": ["-y", "@modelcontextprotocol/server-puppeteer"]},
        },
    },
    "Code & Version Control": {
        "github": {
            "name": "GitHub MCP",
            "description": "Interact with GitHub repositories, issues, and PRs",
            "repo": "https://github.com/github/github-mcp-server",
            "config": {"type": "stdio", "command": "npx", "args": ["-y", "@github/github-mcp-server"]},
        },
        "git": {
            "name": "Git MCP",
            "description": "Git repository operations and analysis",
            "repo": "https://github.com/modelcontextprotocol/servers",
            "config": {"type": "stdio", "command": "npx", "args": ["-y", "@modelcontextprotocol/server-git"]},
        },
    },
    "Databases": {
        "postgres": {
            "name": "PostgreSQL MCP",
            "description": "Query and manage PostgreSQL databases",
            "repo": "https://github.com/modelcontextprotocol/servers",
            "config": {"type": "stdio", "command": "npx", "args": ["-y", "@modelcontextprotocol/server-postgres"]},
        },
        "mongodb": {
            "name": "MongoDB MCP",
            "description": "MongoDB database access and queries",
            "repo": "https://github.com/modelcontextprotocol/servers",
            "config": {"type": "stdio", "command": "npx", "args": ["-y", "@modelcontextprotocol/server-mongodb"]},
        },
    },
}

@dataclass
class LLMTemplate:
    """Represents a configuration template for a particular LLM."""
    filename: str
    display_name: str
    path: Path
    format: str
    metadata: Dict[str, object]
    container_key: Optional[str] = None
    header_lines: Optional[List[str]] = None

    def render(self, server_configs: Dict[str, object]) -> str:
        """Render the template with the given server configurations."""
        if self.format == "json":
            payload = copy.deepcopy(self.metadata)
            if self.container_key is None:
                raise RuntimeError("JSON template missing container key")
            payload[self.container_key] = server_configs
            return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"

        if self.format == "toml":
            lines: List[str] = []
            if self.header_lines:
                lines.extend(self.header_lines)
                if self.header_lines and self.header_lines[-1].strip():
                    lines.append("")

            for server_name, server_lines in server_configs.items():
                if isinstance(server_lines, list):
                    lines.extend(server_lines)
                    if server_lines and server_lines[-1].strip():
                        lines.append("")

            while lines and not lines[-1].strip():
                lines.pop()
            return "\n".join(lines) + "\n"

        raise ValueError(f"Unsupported format: {self.format}")


def safe_clear_screen():
    """Safely clear screen with error handling."""
    try:
        if os.name == "nt":
            os.system("cls")
        else:
            os.system("clear")
    except:
        print("\n" * 50)  # Fallback


def safe_input(prompt: str, timeout: int = 30) -> str:
    """Safe input with timeout to prevent freezing."""
    try:
        if sys.platform == "win32":
            # Windows doesn't support timeout easily, use regular input
            return input(prompt).strip()
        else:
            # Unix systems - use signal for timeout
            def timeout_handler(signum, frame):
                raise TimeoutError("Input timeout")
            
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout)
            try:
                result = input(prompt).strip()
                signal.alarm(0)
                return result
            finally:
                signal.signal(signal.SIGALRM, old_handler)
    except (TimeoutError, KeyboardInterrupt):
        print("\nTimeout or interrupted")
        return "q"
    except Exception:
        return "q"


def ensure_environment() -> None:
    """Ensure directories and default files exist."""
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        SERVERS_DIR.mkdir(parents=True, exist_ok=True)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        SELECTIONS_DIR.mkdir(parents=True, exist_ok=True)
        if not CONFIG_PATH.exists():
            save_config(DEFAULT_CONFIG)
        if not HISTORY_PATH.exists():
            HISTORY_PATH.touch()
    except Exception as e:
        print(f"Error setting up environment: {e}")


def load_config() -> Dict[str, object]:
    try:
        with CONFIG_PATH.open("r", encoding="utf-8") as handle:
            config = json.load(handle)
    except (OSError, json.JSONDecodeError):
        config = copy.deepcopy(DEFAULT_CONFIG)

    for key, default_value in DEFAULT_CONFIG.items():
        config.setdefault(key, default_value)

    return config


def save_config(config: Dict[str, object]) -> None:
    try:
        with CONFIG_PATH.open("w", encoding="utf-8") as handle:
            json.dump(config, handle, indent=2)
    except Exception as e:
        print(f"Error saving config: {e}")


def load_selections(cli_name: str) -> Set[str]:
    """Load selected MCP servers for a specific CLI."""
    selection_file = SELECTIONS_DIR / f"{cli_name}.json"
    if selection_file.exists():
        try:
            with selection_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
                return set(data.get("selected_servers", []))
        except:
            pass
    return set()


def save_selections(cli_name: str, selected: Set[str]) -> None:
    """Save selected MCP servers for a specific CLI."""
    try:
        selection_file = SELECTIONS_DIR / f"{cli_name}.json"
        with selection_file.open("w", encoding="utf-8") as f:
            json.dump({
                "cli": cli_name,
                "selected_servers": sorted(list(selected)),
                "timestamp": datetime.now().isoformat()
            }, f, indent=2)
    except Exception as e:
        print(f"Error saving selections: {e}")


def load_json_template(path: Path) -> tuple[LLMTemplate, Dict[str, object]]:
    """Load a JSON template and return both the template and available servers."""
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

    template = LLMTemplate(
        filename=path.name,
        display_name=LLM_DISPLAY_NAMES.get(path.name, path.stem.replace("_", " ").title()),
        path=path,
        format="json",
        metadata=metadata,
        container_key=container_key,
    )

    return template, servers


def load_all_llms_and_servers() -> tuple[List[LLMTemplate], Dict[str, object]]:
    """Load all LLM templates and aggregate all available MCP servers."""
    llms: List[LLMTemplate] = []
    all_servers: Dict[str, object] = {}

    try:
        for path in sorted(SERVERS_DIR.iterdir()):
            if not path.is_file() or path.suffix.lower() != ".json":
                continue
            try:
                template, servers = load_json_template(path)
                llms.append(template)
                for server_name, server_config in servers.items():
                    if server_name not in all_servers:
                        all_servers[server_name] = server_config
            except Exception as exc:
                print(f"Skipping {path.name}: {exc}")
                continue
    except Exception as e:
        print(f"Error loading templates: {e}")

    return llms, all_servers


def display_server_selector(cli_name: str, cli_display_name: str) -> Set[str]:
    """FIXED: Display interactive server selector with timeout protection."""
    
    # Build flat list of servers
    servers_list = []
    for category, servers in MCP_SERVERS_DB.items():
        for server_key, server_info in servers.items():
            servers_list.append({
                "key": server_key,
                "name": server_info["name"],
                "description": server_info["description"],
                "category": category,
            })

    # Load previous selections
    selected = load_selections(cli_name)
    selected_indices = {i for i, s in enumerate(servers_list) if s["key"] in selected}

    # Terminal state
    scroll_pos = 0
    items_per_page = 10
    max_iterations = 100  # Prevent infinite loops

    for iteration in range(max_iterations):
        try:
            safe_clear_screen()

            print(f"\n{'='*60}")
            print(f"MCP Server Selection for: {cli_display_name}")
            print(f"{'='*60}")
            print(f"Selected: {len(selected_indices)} servers")
            print("Commands: [0-9] select | [w/s] scroll | [a] all | [c] confirm | [q] back")
            print("-" * 60)

            # Display servers
            end_idx = min(scroll_pos + items_per_page, len(servers_list))
            for i in range(scroll_pos, end_idx):
                item = servers_list[i]
                selected_str = "[x]" if i in selected_indices else "[ ]"
                idx_display = (i - scroll_pos)
                print(f"  {idx_display}. {selected_str} {item['name']}")
                print(f"      {item['description'][:50]}...")

            print(f"\nShowing {scroll_pos + 1}-{end_idx} of {len(servers_list)}")

            # Get input with timeout
            ch = safe_input("\nCommand: ", timeout=30)
            
            if ch == 'q':
                break
            elif ch == 'c':
                selected = {servers_list[i]["key"] for i in selected_indices}
                save_selections(cli_name, selected)
                return selected
            elif ch.isdigit():
                idx = int(ch)
                if 0 <= idx < min(items_per_page, len(servers_list) - scroll_pos):
                    actual_index = scroll_pos + idx
                    if actual_index in selected_indices:
                        selected_indices.discard(actual_index)
                    else:
                        selected_indices.add(actual_index)
            elif ch in ['w', 'up']:
                scroll_pos = max(0, scroll_pos - items_per_page)
            elif ch in ['s', 'down']:
                scroll_pos = min(len(servers_list) - items_per_page, scroll_pos + items_per_page)
            elif ch == 'a':
                if len(selected_indices) == len(servers_list):
                    selected_indices.clear()
                else:
                    selected_indices = set(range(len(servers_list)))

        except Exception as e:
            print(f"Error in selector: {e}")
            break

    return selected


def apply_servers_to_cli(cli_filename: str, selected_servers: Set[str]) -> None:
    """Apply selected MCP servers to CLI config files."""
    try:
        print(f"\nApplying {len(selected_servers)} servers to {cli_filename}...")

        for json_file in SERVERS_DIR.glob("*.json"):
            try:
                with json_file.open("r", encoding="utf-8") as f:
                    data = json.load(f)

                # Find servers container
                container_key = None
                for key in ("mcpServers", "mcp_servers", "mcp"):
                    if key in data:
                        container_key = key
                        break

                if container_key is None:
                    continue

                # Build server configs
                new_servers = {}
                for category, servers in MCP_SERVERS_DB.items():
                    for server_key, server_info in servers.items():
                        if server_key in selected_servers:
                            new_servers[server_key] = server_info["config"]

                # Update
                data[container_key] = {**data[container_key], **new_servers}

                # Write back
                with json_file.open("w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

                print(f"  ✓ {json_file.name}")

            except Exception as exc:
                print(f"  ✗ {json_file.name}: {exc}")

    except Exception as e:
        print(f"Error applying servers: {e}")


def safe_launch_process(command: str, description: str) -> bool:
    """FIXED: Safely launch process without blocking."""
    try:
        print(f"\nLaunching {description}...")
        
        if sys.platform == "win32":
            # Windows - use CREATE_NEW_PROCESS_GROUP to avoid blocking
            subprocess.Popen(
                command,
                shell=True,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        else:
            # Unix - use nohup to detach
            subprocess.Popen(
                f"nohup {command} > /dev/null 2>&1 &",
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        
        print(f"✓ {description} launched successfully")
        return True
        
    except Exception as e:
        print(f"✗ Error launching {description}: {e}")
        return False


def select_cli_and_servers() -> Tuple[Optional[str], Optional[Set[str]]]:
    """Select CLI and configure servers."""
    llms, _ = load_all_llms_and_servers()

    if not llms:
        print("No LLM templates found!")
        return None, None

    # CLI Selection with timeout protection
    max_attempts = 10
    for attempt in range(max_attempts):
        try:
            safe_clear_screen()
            print(f"\n{'='*50}")
            print("Select LLM / CLI to Configure")
            print(f"{'='*50}\n")

            for idx, llm in enumerate(llms, start=1):
                print(f"  {idx}. {llm.display_name}")

            print(f"  q. Exit\n")

            choice = safe_input("Selection: ", timeout=30)

            if choice == 'q':
                return None, None

            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(llms):
                    selected_llm = llms[idx]
                    # Get servers for this CLI
                    selected_servers = display_server_selector(selected_llm.filename, selected_llm.display_name)
                    return selected_llm.filename, selected_servers

            print("Invalid selection")
            time.sleep(1)

        except Exception as e:
            print(f"Error in CLI selection: {e}")
            time.sleep(1)

    return None, None


def main_menu(llms: List[LLMTemplate], all_servers: Dict[str, object], config: Dict[str, object]) -> None:
    """FIXED: Main menu with timeout protection."""
    max_iterations = 50  # Prevent infinite loops
    
    for iteration in range(max_iterations):
        try:
            safe_clear_screen()

            print("\n" + "="*50)
            print("MCP Configuration Manager")
            print("="*50)

            selected_llm_filename = config.get("selected_llm")
            if selected_llm_filename:
                selected_llm = next((llm for llm in llms if llm.filename == selected_llm_filename), None)
                if selected_llm:
                    print(f"\nLLM: {selected_llm.display_name}")
            else:
                print(f"\nLLM: None selected")

            print("\n" + "-"*50)
            print("\nOptions:")
            print("  1. Select CLI & Configure MCP Servers")
            print("  2. Launch Selected CLI")
            print("  3. Load Super Assistant")
            print("  4. Exit")

            choice = safe_input("\nSelect option: ", timeout=30)

            if choice == "1":
                cli_filename, selected_servers = select_cli_and_servers()
                if cli_filename and selected_servers:
                    apply_servers_to_cli(cli_filename, selected_servers)
                    config["selected_llm"] = cli_filename
                    save_config(config)
                    print(f"\n✓ Configured {LLM_DISPLAY_NAMES.get(cli_filename, cli_filename)}")
                    time.sleep(2)

            elif choice == "2":
                if not config.get("selected_llm"):
                    print("\nNo CLI selected. Please select one first.")
                    time.sleep(2)
                    continue

                cli_filename = config.get("selected_llm")
                cmd = CLI_LAUNCH_COMMANDS.get(cli_filename)
                if cmd:
                    display_name = LLM_DISPLAY_NAMES.get(cli_filename, cli_filename)
                    safe_launch_process(cmd, display_name)
                    time.sleep(2)

            elif choice == "3":
                # FIXED: Super Assistant launch
                amazon_q_config = r"C:\Users\matt\.aws\amazonq\mcp.json"
                if not os.path.exists(amazon_q_config):
                    print(f"\nError: Amazon Q config not found at {amazon_q_config}")
                    time.sleep(2)
                    continue

                cmd = f"npx @srbhptl39/mcp-superassistant-proxy@latest --config {amazon_q_config} --outputTransport sse"
                safe_launch_process(cmd, "Super Assistant")
                time.sleep(2)

            elif choice == "4":
                print("\nGoodbye!")
                break
            else:
                print("\nInvalid option.")
                time.sleep(1)

        except Exception as e:
            print(f"Error in main menu: {e}")
            time.sleep(1)


def main() -> None:
    """Main entry point with error handling."""
    try:
        ensure_environment()
        llms, all_servers = load_all_llms_and_servers()

        if not llms:
            print("No LLM templates found!")
            return

        config = load_config()
        main_menu(llms, all_servers, config)

    except KeyboardInterrupt:
        print("\n\nExiting...")
    except Exception as e:
        print(f"Fatal error: {e}")


if __name__ == "__main__":
    main()
