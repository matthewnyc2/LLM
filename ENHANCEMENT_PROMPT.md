<instructions>
for the code i have below do the following:

1. simplify the menu so that the options are to select the LLM, select the MCP Servers, Launch the LLM,  Batch Commands, and History

2. selecting the LLM should have a new screen that only shows the names of the llms in a numbered list that i can select from.  once selected it should go back to the main menu.  

3. the main menu should show only the LLM selected, the MCP servers, and then the numbered list of options below

4. if the user selects launch LLM it should replace the config file associated with that LLM with the mcp servers that are selected currently

5. all mcp servers from the files in the templates should  be avaialbe to select from.  the the template files are just to see how they are formatted.  not to be the ones to select from

6. the batch selection should have a screen where the user enters a command and pushes enter and then the program asks which llm should execute it with the current default being selected if the user simply presses enter
</instructions>
<code>
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
from typing import Dict, List, Optional, Sequence

CONFIG_DIR = Path(__file__).resolve().parent
SERVERS_DIR = CONFIG_DIR / "servers"
OUTPUT_DIR = CONFIG_DIR / "generated"
CONFIG_PATH = CONFIG_DIR / "config.json"
HISTORY_PATH = CONFIG_DIR / "history.log"

DEFAULT_CONFIG = {
    "last_template": None,
    "output_directory": "generated",
    "selections": {},
    "location_type": "windows",
    "last_batch_server": None,
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

# Map templates to CLI launch commands
CLI_LAUNCH_COMMANDS = {
    "amazon_q": "q",
    "claude_code": "claude",
    "claude_desktop": "claude",
    "cline": "cline",
    "gemini": "gemini",
    "kilo_code": "kilocode",
    "opencode": "opencode",
    "codex": "codex",
}

APP_LOCATIONS = {
    "windows": {
        "amazonq_mcp.json": r"C:\Users\matt\.aws\amazonq\mcp.json",
        "claude_code_mcp.json": r"C:\Users\matt\.claude.json",
        "claude_desktop_config.json": r"C:\Users\matt\AppData\Roaming\Claude\claude_desktop_config.json",
        "cline_mcp_settings.json": r"%APPDATA%\Code\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json",
        "gemini_cli_mcp.json": r"C:\Users\matt\.gemini\settings.json",
        "github_copilot_mcp.json": r"C:\Users\matt\AppData\Roaming\Code\User\settings.json",
        "kilo_code_mcp.json": r"%APPDATA%\Code\User\globalStorage\kilocode.kilo-code\settings\mcp_settings.json",
        "opencode_config.json": r"C:\Users\matt\.config\opencode\opencode.json",
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
    config.setdefault("last_template", DEFAULT_CONFIG["last_template"])
    config.setdefault("output_directory", DEFAULT_CONFIG["output_directory"])
    config.setdefault("selections", {})
    config.setdefault("location_type", DEFAULT_CONFIG["location_type"])
    config.setdefault("last_batch_server", DEFAULT_CONFIG["last_batch_server"])
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


def prompt_choice(prompt: str, options: Sequence[str]) -> Optional[int]:
    for idx, label in enumerate(options, start=1):
        print(f"  {idx}. {label}")
    print("  X. Cancel")
    choice = input(f"{prompt}: ").strip().lower()
    if choice == "x":
        return None
    if choice.isdigit():
        index = int(choice)
        if 1 <= index <= len(options):
            return index - 1
    print("Invalid selection.\n")
    return None


def prompt_yes_no(prompt: str, default: bool = True) -> bool:
    suffix = "[Y/n]" if default else "[y/N]"
    while True:
        response = input(f"{prompt} {suffix}: ").strip().lower()
        if not response:
            return default
        if response in {"y", "yes"}:
            return True
        if response in {"n", "no"}:
            return False
        print("Please answer yes or no.")


def choose_template(templates: List[ServerTemplate], current: Optional[str]) -> Optional[ServerTemplate]:
    print("\nAvailable configuration targets:")
    options = []
    for template in templates:
        label = template.display_name
        if template.filename == current:
            label += " (current)"
        options.append(label)
    selected_index = prompt_choice("Select template", options)
    if selected_index is None:
        return None
    return templates[selected_index]


def edit_server_selection(template: ServerTemplate, config: Dict[str, object]) -> None:
    selections: Dict[str, List[str]] = config.setdefault("selections", {})
    current = selections.get(template.filename)
    if current is None:
        current = list(template.server_order)
        selections[template.filename] = current

    current_set = {name for name in current if name in template.server_order}

    while True:
        print("\nServers for", template.display_name)
        for idx, name in enumerate(template.server_order, start=1):
            mark = "[x]" if name in current_set else "[ ]"
            print(f"  {idx:>2}. {mark} {name}")
        print("  A. Toggle all")
        print("  X. Return to previous menu")
        choice = input("Select entry to toggle: ").strip().lower()
        if choice == "x":
            break
        if choice == "a":
            if len(current_set) == len(template.server_order):
                current_set.clear()
            else:
                current_set = set(template.server_order)
            continue
        if choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(template.server_order):
                name = template.server_order[idx - 1]
                if name in current_set:
                    current_set.remove(name)
                else:
                    current_set.add(name)
                continue
        print("Invalid selection.")

    selections[template.filename] = [name for name in template.server_order if name in current_set]
    save_config(config)


def resolve_output_directory(config: Dict[str, object]) -> Path:
    raw_value = config.get("output_directory", DEFAULT_CONFIG["output_directory"])
    expanded = Path(os.path.expanduser(str(raw_value)))
    if not expanded.is_absolute():
        expanded = (CONFIG_DIR / expanded).resolve()
    else:
        expanded = expanded.resolve()
    return expanded


def set_output_directory(config: Dict[str, object]) -> None:
    current_dir = resolve_output_directory(config)
    print(f"Current output directory: {current_dir}")
    new_path = input("Enter new directory (blank to cancel): ").strip()
    if not new_path:
        return
    resolved = Path(os.path.expanduser(new_path)).resolve()
    resolved.mkdir(parents=True, exist_ok=True)
    config["output_directory"] = str(resolved)
    save_config(config)
    print(f"Output directory set to {resolved}\n")


def set_location_type(config: Dict[str, object]) -> None:
    current = config.get("location_type", "windows")
    print(f"Current location type: {current}")
    options = ["windows", "unix", "project"]
    selected_index = prompt_choice("Select location type", options)
    if selected_index is not None:
        config["location_type"] = options[selected_index]
        save_config(config)
        print(f"Location type set to {options[selected_index]}\n")


def launch_llm(template: ServerTemplate, config: Dict[str, object]) -> None:
    """Launch the LLM with current config."""
    cli_key = template.filename.replace(".json", "").replace(".toml", "").replace("_mcp", "").replace("_settings", "").replace("_config", "")

    cli_map = {
        "amazonq": "amazon_q",
        "claude_code": "claude_code",
        "claude_desktop": "claude_desktop",
        "cline": "cline",
        "gemini_cli": "gemini",
        "kilo_code": "kilo_code",
        "opencode": "opencode",
        "codex": "codex",
    }

    cli_key = cli_map.get(cli_key, cli_key)
    cmd = CLI_LAUNCH_COMMANDS.get(cli_key)

    if not cmd:
        print(f"No launch command configured for {template.display_name}\n")
        return

    print(f"Launching {template.display_name}...\n")
    log_history("launch_llm", {"template": template.filename, "command": cmd})

    try:
        if sys.platform == "win32":
            subprocess.Popen(f"start {cmd}", shell=True)
        else:
            subprocess.Popen([cmd])
    except Exception as exc:
        print(f"Failed to launch {template.display_name}: {exc}\n")


def generate_configuration(template: ServerTemplate, config: Dict[str, object], auto_launch: bool = False) -> None:
    selections: Dict[str, List[str]] = config.setdefault("selections", {})
    selected_servers = selections.get(template.filename)
    if not selected_servers:
        selected_servers = list(template.server_order)
        selections[template.filename] = selected_servers

    output_directory = resolve_output_directory(config)
    output_directory.mkdir(parents=True, exist_ok=True)

    default_output = output_directory / template.filename
    print(f"\nDefault output path: {default_output}")
    if prompt_yes_no("Use this path?", True):
        output_path = default_output
    else:
        custom = input("Enter full output path: ").strip()
        if not custom:
            print("Aborted generation.\n")
            return
        output_path = Path(os.path.expanduser(custom)).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)

    document = template.render(selected_servers)
    with output_path.open("w", encoding="utf-8") as handle:
        handle.write(document)

    log_history(
        "generate_config",
        {
            "template": template.filename,
            "output": str(output_path),
            "servers": selected_servers,
        },
    )

    print(f"Generated {template.display_name} configuration at {output_path}\n")

    # Offer to copy to app-specific location
    location_type = config.get("location_type", "windows")
    locations = APP_LOCATIONS.get(location_type, {})
    if template.filename in locations:
        app_location_raw = locations[template.filename]
        app_location = Path(os.path.expandvars(app_location_raw))
        app_location.parent.mkdir(parents=True, exist_ok=True)
        print(f"App-specific location ({location_type}): {app_location}")
        # Always copy
        try:
            shutil.copy2(output_path, app_location)
            print(f"Copied to {app_location}\n")
        except Exception as exc:
            print(f"Failed to copy: {exc}\n")

    # Offer to launch
    if auto_launch or prompt_yes_no(f"Launch {template.display_name} now?", True):
        launch_llm(template, config)


def batch_mode(templates: List[ServerTemplate], config: Dict[str, object]) -> None:
    """Interactive batch mode for headless command execution."""
    print("\n=== Batch Mode ===")
    print("Enter commands one per line. Press Ctrl+C to exit.")
    print("Each command will use the selected MCP server configuration.\n")

    selections: Dict[str, List[str]] = config.get("selections", {})
    last_server = config.get("last_batch_server")

    while True:
        try:
            cmd = input("Enter command (or quit to exit): ").strip()
            if not cmd or cmd.lower() in ("quit", "exit", "q"):
                break

            print("\nAvailable server templates:")
            options = []
            for template in templates:
                label = template.display_name
                if last_server and template.filename == last_server:
                    label += " (last used)"
                options.append(label)

            selected_index = None
            if last_server:
                for idx, template in enumerate(templates):
                    if template.filename == last_server:
                        selected_index = idx
                        break

                print(f"\nPress Enter to use {options[selected_index]} (default):")
                for idx, label in enumerate(options, start=1):
                    marker = " <- DEFAULT" if idx - 1 == selected_index else ""
                    print(f"  {idx}. {label}{marker}")
                print("  X. Cancel")

                choice = input(f"Select server: ").strip().lower()
                if choice == "x":
                    print("Command cancelled.\n")
                    continue
                if choice == "":
                    pass
                elif choice.isdigit():
                    index = int(choice)
                    if 1 <= index <= len(options):
                        selected_index = index - 1
                    else:
                        print("Invalid selection.\n")
                        continue
                else:
                    print("Invalid selection.\n")
                    continue
            else:
                selected_index = prompt_choice("Select server", options)
                if selected_index is None:
                    print("Server selection cancelled.\n")
                    continue

            selected_template = templates[selected_index]
            config["last_batch_server"] = selected_template.filename
            save_config(config)

            print(f"\nUsing {selected_template.display_name}")
            selected_servers = selections.get(selected_template.filename)
            if not selected_servers:
                selected_servers = list(selected_template.server_order)

            location_type = config.get("location_type", "windows")
            locations = APP_LOCATIONS.get(location_type, {})
            if selected_template.filename in locations:
                output_directory = resolve_output_directory(config)
                output_path = output_directory / selected_template.filename

                document = selected_template.render(selected_servers)
                with output_path.open("w", encoding="utf-8") as handle:
                    handle.write(document)

                app_location_raw = locations[selected_template.filename]
                app_location = Path(os.path.expandvars(app_location_raw))
                app_location.parent.mkdir(parents=True, exist_ok=True)

                try:
                    shutil.copy2(output_path, app_location)
                except Exception as exc:
                    print(f"Failed to copy config: {exc}")

            print(f"Executing: {cmd}\n")
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


def show_summary(template: Optional[ServerTemplate], config: Dict[str, object]) -> None:
    print("\n=== MCP Configuration Builder ===")
    if template is None:
        print("No template selected yet.")
    else:
        print(f"Target: {template.display_name} ({template.filename})")
        selections: Dict[str, List[str]] = config.get("selections", {})
        chosen = selections.get(template.filename)
        if not chosen:
            chosen = list(template.server_order)
        print("Selected servers:")
        for name in chosen:
            print(f"  - {name}")
        if len(chosen) < len(template.server_order):
            skipped = [name for name in template.server_order if name not in chosen]
            if skipped:
                print(f"(excluded: {', '.join(skipped)})")
    print(f"Output directory: {resolve_output_directory(config)}")
    print(f"Location type: {config.get('location_type', 'windows')}")
    print("===============================\n")


def main() -> None:
    ensure_environment()
    templates = load_templates()
    if not templates:
        print("No templates found in", SERVERS_DIR)
        return

    config = load_config()

    selected_template: Optional[ServerTemplate] = None
    last_template = config.get("last_template")
    if last_template:
        for template in templates:
            if template.filename == last_template:
                selected_template = template
                break
    if selected_template is None:
        selected_template = templates[0]
        config["last_template"] = selected_template.filename
        save_config(config)

    while True:
        show_summary(selected_template, config)
        print("Options:")
        print("  1. Choose configuration target")
        print("  2. Select MCP servers")
        print("  3. Set output directory")
        print("  4. Generate configuration file")
        print("  5. Launch selected LLM now")
        print("  6. Batch mode (headless commands)")
        print("  7. Set location type")
        print("  8. View history log")
        print("  9. Exit")
        choice = input("Choose an option: ").strip()

        if choice == "1":
            result = choose_template(templates, selected_template.filename if selected_template else None)
            if result is not None:
                selected_template = result
                config["last_template"] = selected_template.filename
                save_config(config)
        elif choice == "2":
            if selected_template is None:
                print("Select a template first.\n")
                continue
            edit_server_selection(selected_template, config)
        elif choice == "3":
            set_output_directory(config)
        elif choice == "4":
            if selected_template is None:
                print("Select a template first.\n")
                continue
            generate_configuration(selected_template, config)
        elif choice == "5":
            if selected_template is None:
                print("Select a template first.\n")
                continue
            generate_configuration(selected_template, config, auto_launch=True)
        elif choice == "6":
            batch_mode(templates, config)
        elif choice == "7":
            set_location_type(config)
        elif choice == "8":
            display_history()
        elif choice == "9":
            print("Goodbye!")
            break
        else:
            print("Invalid option.\n")


if __name__ == "__main__":
    main()
</code>