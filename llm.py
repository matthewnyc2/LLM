#!/usr/bin/env python3
"""Utility for assembling MCP server configuration files for multiple apps."""

import copy
import concurrent.futures
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set, Tuple

CONFIG_DIR = Path(__file__).resolve().parent
SERVERS_DIR = CONFIG_DIR / "servers"
OUTPUT_DIR = CONFIG_DIR / "generated"
CONFIG_PATH = CONFIG_DIR / "config.json"
HISTORY_PATH = CONFIG_DIR / "history.log"

DEFAULT_CONFIG = {
    "output_directory": "generated",
    "last_batch_server": None,
    "selected_llm": None,
    "selected_mcp_servers": [],
    "sync_os_modes": ["windows"],
    "claude_mcp_scope": "user",    # local | user | project
    "gemini_mcp_scope": "project", # user | project
    "qwen_mcp_scope": "project",   # user | project
}

TEMPLATE_NAME_OVERRIDES = {
    "amazonq_mcp.json": "Amazon Q",
    "claude_code_mcp.json": "Claude Code (VSCode)",
    "cline_mcp_settings.json": "Cline",
    "gemini_cli_mcp.json": "Gemini CLI",
    "github_copilot_mcp.json": "GitHub Copilot",
    "kilo_code_mcp.json": "Kilo Code",
    "qwen_mcp.json": "Qwen",
    "opencode_config.json": "Open Coder",
    "codex_config.toml": "Codex",
}

CLI_LAUNCH_COMMANDS = {
    "amazon_q": {
        "windows": r"C:\Users\matt\Dropbox\programs\batches\q2.bat",
        "wsl": "/usr/bin/q"
    },
    "claude_code": {
        "windows": "claude",
        "wsl": "/home/matt/.local/bin/claude"
    },
    "cline": {
        "windows": None,  # VS Code extension, not CLI launchable
        "wsl": None
    },
    "gemini_cli": {
        "windows": r"C:\Users\matt\AppData\Roaming\npm\gemini.cmd",
        "wsl": "/home/matt/.nvm/versions/node/v25.2.1/bin/gemini"
    },
    "github_copilot": {
        "windows": r'"C:\Program Files\GitHub CLI\gh.exe" copilot',
        "wsl": "/usr/bin/gh copilot"
    },
    "kilo_code": {
        "windows": r"C:\Users\matt\AppData\Roaming\npm\kilocode.cmd",
        "wsl": "/home/matt/.nvm/versions/node/v25.2.1/bin/kilocode"
    },
    "opencode": {
        "windows": r"C:\Users\matt\AppData\Roaming\npm\opencode.cmd",
        "wsl": "/home/matt/.nvm/versions/node/v25.2.1/bin/opencode"
    },
    "qwen": {
        "windows": r"C:\Users\matt\AppData\Roaming\npm\qwen.cmd",
        "wsl": "/home/matt/.nvm/versions/node/v25.2.1/bin/qwen"
    },
    "codex": {
        "windows": r"C:\Users\matt\AppData\Roaming\npm\codex.cmd",
        "wsl": "/home/matt/.nvm/versions/node/v25.2.1/bin/codex"
    },
}

APP_LOCATIONS = {
    "windows": {
        "amazonq_mcp.json": r"%USERPROFILE%\.aws\amazonq\mcp.json",
        "claude_code_mcp.json": r"%USERPROFILE%\.claude.json",
        "cline_mcp_settings.json": r"%APPDATA%\Code\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json",
        "gemini_cli_mcp.json": r"%USERPROFILE%\.gemini\settings.json",
        "github_copilot_mcp.json": r"%APPDATA%\Code\User\settings.json",
        "kilo_code_mcp.json": r"%USERPROFILE%\.kilocode\cli\global\settings\mcp_settings.json",
        "qwen_mcp.json": r"%APPDATA%\Code\User\globalStorage\qwen.qwen\settings\mcp_settings.json",
        "opencode_config.json": r"%USERPROFILE%\.config\opencode\opencode.json",
        "codex_config.toml": r"%USERPROFILE%\.codex\config.toml",
    },
    "wsl": {
        "amazonq_mcp.json": "~/.aws/amazonq/mcp.json",
        "claude_code_mcp.json": "~/.claude.json",
        "cline_mcp_settings.json": "~/.config/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json",
        "gemini_cli_mcp.json": "~/.gemini/settings.json",
        "github_copilot_mcp.json": "~/.config/Code/User/settings.json",
        "kilo_code_mcp.json": "~/.kilocode/cli/global/settings/mcp_settings.json",
        "qwen_mcp.json": "~/.config/Code/User/globalStorage/qwen.qwen/settings/mcp_settings.json",
        "opencode_config.json": "~/.config/opencode/opencode.json",
        "codex_config.toml": "~/.codex/config.toml",
    },
}


def get_project_locations() -> Dict[str, str]:
    """Generate project-specific locations based on current working directory."""
    cwd = Path.cwd()
    project_dir = cwd  # Use the current directory as the project directory
    
    return {
        "amazonq_mcp.json": str(project_dir / ".amazonq" / "mcp.json"),
        "claude_code_mcp.json": str(project_dir / ".mcp.json"),
        "cline_mcp_settings.json": str(project_dir / ".clinerules"),
        "gemini_cli_mcp.json": str(project_dir / ".gemini" / "settings.json"),
        "github_copilot_mcp.json": str(project_dir / ".vscode" / "mcp.json"),
        "kilo_code_mcp.json": str(project_dir / ".kilocode" / "mcp.json"),
        "qwen_mcp.json": str(project_dir / ".qwen" / "mcp.json"),
        "opencode_config.json": str(project_dir / "opencode.json"),
        "codex_config.toml": str(project_dir / ".codex" / "config.toml"),
    }


@dataclass
class ServerTemplate:
    """Represents a configuration template for a particular application and OS."""

    filename: str
    display_name: str
    path: Path
    format: str  # json or toml
    os_mode: str # windows or wsl
    server_order: List[str]
    server_blocks: Dict[str, object]
    metadata: Dict[str, object]
    container_key: Optional[str] = None
    header_lines: Optional[List[str]] = None

    @property
    def unique_id(self) -> str:
        """Unique identifier for this template (filename + os_mode)."""
        return f"{self.filename}::{self.os_mode}"

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
            
            # For JSON, we are rendering the final config file, so we don't need the 'windows'/'wsl' wrapper anymore.
            # We just output the container key (e.g. mcpServers) at the root level (or wherever it belongs).
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
                # We need to strip the [windows.mcpServers...] or [wsl.mcpServers...] prefix
                # and replace it with standard [mcpServers...] or whatever the target expects.
                # Assuming target expects [mcpServers.name] or [mcp_servers.name].
                # Based on previous file content, it seems target expects [mcp_servers.name] or similar.
                # Let's look at how we parsed it.
                
                # If we parsed `[windows.mcpServers.supabase]`, we want to output `[mcpServers.supabase]` (or snake_case if that's what it was).
                # The codex_config.toml uses `mcpServers` in my update.
                
                for line in block_lines:
                    # Replace the OS-specific section header with the generic one
                    if line.strip().startswith(f"[{self.os_mode}."):
                        # e.g. [windows.mcpServers.supabase] -> [mcpServers.supabase]
                        new_line = line.replace(f"[{self.os_mode}.", "[", 1)
                        lines.append(new_line)
                    else:
                        lines.append(line)
                
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
    config.setdefault("last_batch_server", DEFAULT_CONFIG["last_batch_server"])
    config.setdefault("selected_llm", DEFAULT_CONFIG["selected_llm"])
    config.setdefault("selected_mcp_servers", DEFAULT_CONFIG["selected_mcp_servers"])
    config.setdefault("sync_os_modes", DEFAULT_CONFIG["sync_os_modes"])
    config.setdefault("claude_mcp_scope", DEFAULT_CONFIG["claude_mcp_scope"])
    config.setdefault("gemini_mcp_scope", DEFAULT_CONFIG["gemini_mcp_scope"])
    config.setdefault("qwen_mcp_scope", DEFAULT_CONFIG["qwen_mcp_scope"])
    return config


def save_config(config: Dict[str, object]) -> None:
    with CONFIG_PATH.open("w", encoding="utf-8") as handle:
        json.dump(config, handle, indent=2)
        handle.write("\n")


def resolve_windows_executable(base: str) -> str:
    """Resolve an executable name on Windows, preferring npm-style .cmd shims."""
    if sys.platform != "win32":
        return base
    for candidate in (f"{base}.cmd", f"{base}.exe", f"{base}.ps1", base):
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    return base


def run_process(args: Sequence[str], *, os_mode: str, cwd: Optional[Path] = None) -> Tuple[int, str, str]:
    """Run a CLI command, returning (returncode, stdout, stderr)."""
    final_args: List[str] = list(args)
    if sys.platform == "win32" and os_mode == "wsl":
        wsl_exe = shutil.which("wsl")
        if not wsl_exe:
            return 127, "", "wsl executable not found on PATH"
        final_args = [wsl_exe, "-e", *final_args]
    try:
        proc = subprocess.run(
            final_args,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            check=False,
        )
        return proc.returncode, (proc.stdout or "").strip(), (proc.stderr or "").strip()
    except Exception as exc:
        return 1, "", str(exc)


def _format_headers(headers: Dict[str, str]) -> List[str]:
    return [f"{key}: {value}" for key, value in headers.items()]


def _parse_toml_string(value: str) -> Optional[str]:
    value = value.strip()
    if len(value) >= 2 and value[0] == "\"" and value[-1] == "\"":
        return value[1:-1]
    return None


def _parse_toml_array(value: str) -> Optional[List[str]]:
    value = value.strip()
    if not (value.startswith("[") and value.endswith("]")):
        return None
    inner = value[1:-1].strip()
    if not inner:
        return []
    items: List[str] = []
    for raw in inner.split(","):
        raw = raw.strip()
        parsed = _parse_toml_string(raw)
        if parsed is None:
            return None
        items.append(parsed)
    return items


def _parse_codex_server_block(block_lines: Sequence[str]) -> Dict[str, object]:
    """Parse a minimal subset of Codex TOML MCP server block lines."""
    parsed: Dict[str, object] = {}
    for line in block_lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("["):
            continue
        match = re.match(r"^([A-Za-z0-9_]+)\\s*=\\s*(.+)$", stripped)
        if not match:
            continue
        key, value = match.group(1), match.group(2).strip()
        if key in {"url", "command", "bearer_token_env_var"}:
            as_str = _parse_toml_string(value)
            if as_str is not None:
                parsed[key] = as_str
        elif key == "args":
            as_list = _parse_toml_array(value)
            if as_list is not None:
                parsed[key] = as_list
        elif key in {"http_headers", "env_http_headers"}:
            parsed[key] = value
    return parsed


@dataclass
class SyncResult:
    client: str
    os_mode: str
    ok: bool
    actions: List[str]
    error: Optional[str] = None


def sync_mcp_all_clients(templates: List["ServerTemplate"], config: Dict[str, object]) -> List[SyncResult]:
    """
    Sync selected MCP servers to all supported CLIs in parallel.

    Uses each CLI's `mcp add/remove` commands where available.
    """
    selected_servers = set(config.get("selected_mcp_servers", []))
    os_modes_value = config.get("sync_os_modes", ["windows"])
    if isinstance(os_modes_value, str):
        os_modes = [os_modes_value]
    elif isinstance(os_modes_value, list):
        os_modes = [str(item) for item in os_modes_value]
    else:
        os_modes = ["windows"]
    template_index: Dict[Tuple[str, str], ServerTemplate] = {(t.filename, t.os_mode): t for t in templates}

    targets: List[Tuple[str, str, ServerTemplate]] = []
    for os_mode in os_modes:
        for filename, client_id in (
            ("codex_config.toml", "codex"),
            ("claude_code_mcp.json", "claude"),
            ("gemini_cli_mcp.json", "gemini"),
            ("qwen_mcp.json", "qwen"),
        ):
            tmpl = template_index.get((filename, os_mode))
            if tmpl:
                targets.append((client_id, os_mode, tmpl))

    def sync_one(client_id: str, os_mode: str, tmpl: ServerTemplate) -> SyncResult:
        available = set(tmpl.server_blocks.keys())
        remove_names = sorted(available - selected_servers)
        add_names = sorted(available & selected_servers)
        actions: List[str] = []

        if client_id == "codex":
            exe = resolve_windows_executable("codex")
            for name in remove_names:
                rc, out, err = run_process([exe, "mcp", "remove", name], os_mode=os_mode)
                if rc == 0:
                    actions.append(f"removed {name}")
            for name in add_names:
                block_lines = tmpl.server_blocks.get(name)
                if not isinstance(block_lines, list):
                    continue
                spec = _parse_codex_server_block(block_lines)
                url = spec.get("url")
                command = spec.get("command")
                args = spec.get("args") if isinstance(spec.get("args"), list) else []

                if url and (spec.get("http_headers") or spec.get("env_http_headers")):
                    actions.append(f"skipped {name} (headers unsupported by codex mcp add)")
                    continue

                run_process([exe, "mcp", "remove", name], os_mode=os_mode)
                if isinstance(url, str):
                    cmd = [exe, "mcp", "add", name, "--url", url]
                    bearer = spec.get("bearer_token_env_var")
                    if isinstance(bearer, str):
                        cmd.extend(["--bearer-token-env-var", bearer])
                    rc, out, err = run_process(cmd, os_mode=os_mode)
                elif isinstance(command, str):
                    cmd = [exe, "mcp", "add", name, "--", command, *[str(a) for a in args]]
                    rc, out, err = run_process(cmd, os_mode=os_mode)
                else:
                    actions.append(f"skipped {name} (unrecognized codex block)")
                    continue

                if rc == 0:
                    actions.append(f"added {name}")
                else:
                    actions.append(f"failed {name}")
                    return SyncResult(client=client_id, os_mode=os_mode, ok=False, actions=actions, error=err or out)

            return SyncResult(client=client_id, os_mode=os_mode, ok=True, actions=actions)

        if client_id == "claude":
            exe = resolve_windows_executable("claude")
            scope = str(config.get("claude_mcp_scope", "user"))
            for name in remove_names:
                rc, out, err = run_process([exe, "mcp", "remove", "--scope", scope, name], os_mode=os_mode)
                if rc == 0:
                    actions.append(f"removed {name}")
            for name in add_names:
                server = tmpl.server_blocks.get(name)
                if not isinstance(server, dict):
                    continue
                run_process([exe, "mcp", "remove", "--scope", scope, name], os_mode=os_mode)

                headers = _format_headers(server.get("headers", {}) or {})
                env = server.get("env", {}) or {}

                if "url" in server or "httpUrl" in server:
                    url = server.get("httpUrl") or server.get("url")
                    cmd = [exe, "mcp", "add", "--scope", scope, "--transport", "http"]
                    for header in headers:
                        cmd.extend(["--header", header])
                    cmd.extend([name, str(url)])
                else:
                    cmd = [exe, "mcp", "add", "--scope", scope, "--transport", "stdio"]
                    if isinstance(env, dict):
                        for key, value in env.items():
                            cmd.extend(["--env", f"{key}={value}"])
                    command = server.get("command")
                    args = server.get("args", []) or []
                    cmd.extend([name, "--", str(command), *[str(a) for a in args]])

                rc, out, err = run_process(cmd, os_mode=os_mode)
                if rc == 0:
                    actions.append(f"added {name}")
                else:
                    actions.append(f"failed {name}")
                    return SyncResult(client=client_id, os_mode=os_mode, ok=False, actions=actions, error=err or out)

            return SyncResult(client=client_id, os_mode=os_mode, ok=True, actions=actions)

        if client_id in {"gemini", "qwen"}:
            exe = resolve_windows_executable(client_id)
            scope_key = "gemini_mcp_scope" if client_id == "gemini" else "qwen_mcp_scope"
            scope = str(config.get(scope_key, "project"))

            for name in remove_names:
                rc, out, err = run_process([exe, "mcp", "remove", "--scope", scope, name], os_mode=os_mode)
                if rc == 0:
                    actions.append(f"removed {name}")

            for name in add_names:
                server = tmpl.server_blocks.get(name)
                if not isinstance(server, dict):
                    continue
                run_process([exe, "mcp", "remove", "--scope", scope, name], os_mode=os_mode)

                headers = _format_headers(server.get("headers", {}) or {})
                env = server.get("env", {}) or {}
                timeout = server.get("timeout")

                if "url" in server or "httpUrl" in server:
                    url = server.get("httpUrl") or server.get("url")
                    transport = "http" if "httpUrl" in server else "sse"
                    cmd = [exe, "mcp", "add", "--scope", scope, "--transport", transport]
                    for header in headers:
                        cmd.extend(["--header", header])
                    if isinstance(timeout, int):
                        cmd.extend(["--timeout", str(timeout)])
                    cmd.extend([name, str(url)])
                else:
                    cmd = [exe, "mcp", "add", "--scope", scope, "--transport", "stdio"]
                    if isinstance(env, dict):
                        for key, value in env.items():
                            cmd.extend(["--env", f"{key}={value}"])
                    command = server.get("command")
                    args = server.get("args", []) or []
                    cmd.extend([name, str(command), *[str(a) for a in args]])

                rc, out, err = run_process(cmd, os_mode=os_mode)
                if rc == 0:
                    actions.append(f"added {name}")
                else:
                    actions.append(f"failed {name}")
                    return SyncResult(client=client_id, os_mode=os_mode, ok=False, actions=actions, error=err or out)

            return SyncResult(client=client_id, os_mode=os_mode, ok=True, actions=actions)

        return SyncResult(client=client_id, os_mode=os_mode, ok=False, actions=actions, error="unsupported client")

    if not targets:
        return []

    results: List[SyncResult] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(8, len(targets))) as executor:
        futures = [executor.submit(sync_one, client_id, os_mode, tmpl) for client_id, os_mode, tmpl in targets]
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())
    results.sort(key=lambda r: (r.client, r.os_mode))
    return results


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


def load_json_template(path: Path, os_mode: str) -> ServerTemplate:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if os_mode not in data:
        raise ValueError(f"Missing '{os_mode}' configuration in {path.name}")
    
    os_data = data[os_mode]
    
    container_key = None
    for key in ("mcpServers", "mcp_servers", "mcp", "servers"):
        if key in os_data:
            container_key = key
            break
    if container_key is None:
        raise ValueError(f"Could not locate MCP server container in {path} for {os_mode}")

    servers = os_data[container_key]
    if not isinstance(servers, dict):
        raise ValueError(f"Unexpected server container type in {path} for {os_mode}")

    # Metadata is everything else in the OS block + top level if needed?
    # For now, let's assume metadata is everything in the OS block except the container key.
    metadata = {key: value for key, value in os_data.items() if key != container_key}
    
    # Also merge top-level metadata if it exists and isn't 'windows' or 'wsl'
    for key, value in data.items():
        if key not in ("windows", "wsl"):
            metadata[key] = value

    server_order = list(servers.keys())
    
    display_os = "Windows" if os_mode == "windows" else "WSL"

    return ServerTemplate(
        filename=path.name,
        display_name=f"{friendly_name(path.name)} ({display_os})",
        path=path,
        format="json",
        os_mode=os_mode,
        server_order=server_order,
        server_blocks=servers,
        metadata=metadata,
        container_key=container_key,
    )


def load_toml_template(path: Path, os_mode: str) -> ServerTemplate:
    header_lines: List[str] = []
    server_blocks: Dict[str, List[str]] = {}
    server_order: List[str] = []

    current_name: Optional[str] = None
    current_block: List[str] = []
    
    # Prefix to look for: e.g. [windows.mcp_servers. or [windows.mcpServers.
    # Codex uses mcp_servers, others might use mcpServers
    prefixes = [f"[{os_mode}.mcp_servers.", f"[{os_mode}.mcpServers."]
    other_os = "wsl" if os_mode == "windows" else "windows"
    other_prefixes = [f"[{other_os}.mcp_servers.", f"[{other_os}.mcpServers."]

    with path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.rstrip("\n")
            
            # Check if this line starts a server block for our OS
            matched_prefix = None
            for prefix in prefixes:
                if line.strip().startswith(prefix):
                    matched_prefix = prefix
                    break
            
            if matched_prefix:
                # Save previous block if it was for our OS
                if current_name is not None:
                    server_blocks[current_name] = current_block
                
                # Start new block
                # Extract name: [windows.mcp_servers.name] -> name
                # Remove prefix and trailing ]
                content = line.strip()[len(matched_prefix):].rstrip("]")
                # Handle nested keys like [windows.mcp_servers.server.env]
                current_name = content.split(".")[0]
                if current_name not in server_order:
                    server_order.append(current_name)
                    current_block = [line]
                else:
                    # This is a sub-table for an existing server
                    server_blocks[current_name].append(line)
                    current_name = content.split(".")[0]  # Keep tracking the same server
                    current_block = server_blocks[current_name]
            
            elif current_name is not None:
                # We are inside a block for our OS
                # Check if we hit a block for the OTHER OS
                is_other_os = any(line.strip().startswith(op) for op in other_prefixes)
                
                if is_other_os:
                    # End of our block, start of irrelevant block
                    server_blocks[current_name] = current_block
                    current_name = None
                    current_block = []
                else:
                    current_block.append(line)
            else:
                # Header lines or irrelevant blocks
                # We only want header lines that are NOT for the other OS
                # This is tricky with TOML structure. 
                # For now, assume top-level keys are shared or we just take them?
                # But wait, the file structure is:
                # [windows.mcp_servers.x]
                # ...
                # [wsl.mcp_servers.x]
                # ...
                # So there might not be global headers.
                pass

    if current_name is not None:
        server_blocks[current_name] = current_block

    display_os = "Windows" if os_mode == "windows" else "WSL"

    return ServerTemplate(
        filename=path.name,
        display_name=f"{friendly_name(path.name)} ({display_os})",
        path=path,
        format="toml",
        os_mode=os_mode,
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
        
        # Load for Windows
        try:
            if path.suffix.lower() == ".json":
                t_win = load_json_template(path, "windows")
            else:
                t_win = load_toml_template(path, "windows")
            templates.append(t_win)
        except ValueError as exc:
            print(f"Skipping Windows template for {path.name}: {exc}")

        # Load for WSL
        try:
            if path.suffix.lower() == ".json":
                t_wsl = load_json_template(path, "wsl")
            else:
                t_wsl = load_toml_template(path, "wsl")
            templates.append(t_wsl)
        except ValueError as exc:
            print(f"Skipping WSL template for {path.name}: {exc}")

    return templates


def get_all_mcp_servers(templates: List[ServerTemplate]) -> List[str]:
    """Get all unique MCP server names from all templates."""
    all_servers: Set[str] = set()
    for template in templates:
        all_servers.update(template.server_order)
    return sorted(all_servers)


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def print_centered(text: str):
    columns = shutil.get_terminal_size().columns
    print(text.center(columns))


def select_llm(templates: List[ServerTemplate], config: Dict[str, object]) -> None:
    """Screen to select LLM with numbered list."""
    clear_screen()
    print_centered("=== Select LLM Application ===")
    print()
    
    options = templates # templates are already distinct objects
    
    for idx, template in enumerate(options, start=1):
        print(f"  {idx}. {template.display_name}")
    print("  X. Cancel")
    print()
    
    choice = input("Select LLM: ").strip().lower()
    if choice == "x":
        return
    
    if choice.isdigit():
        index = int(choice)
        if 1 <= index <= len(options):
            selected_template = options[index - 1]
            config["selected_llm"] = selected_template.unique_id
            save_config(config)
            print(f"\nSelected: {selected_template.display_name}")
            return
    
    print("Invalid selection.")
    input("Press Enter to continue...")


def select_mcp_servers(templates: List[ServerTemplate], config: Dict[str, object]) -> None:
    """Screen to select MCP servers from all available servers."""
    all_servers = get_all_mcp_servers(templates)
    selected_servers = set(config.get("selected_mcp_servers", []))
    
    while True:
        clear_screen()
        print_centered("=== Select MCP Servers ===")
        print()
        
        for idx, server in enumerate(all_servers, start=1):
            mark = "[x]" if server in selected_servers else "[ ]"
            print(f"  {idx:>2}. {mark} {server}")
        print("  A. Toggle all")
        print("  X. Return to main menu")
        print()
        
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

    clear_screen()
    print_centered("Syncing MCP servers to all supported CLIs...")
    print()
    results = sync_mcp_all_clients(templates, config)
    if not results:
        print("No supported CLI targets found for the selected OS modes.")
        input("Press Enter to continue...")
        return
    for result in results:
        status = "✓" if result.ok else "✗"
        print(f"{status} {result.client} ({result.os_mode})")
        if result.error:
            print(f"    {result.error}")
    print()
    input("Press Enter to continue...")


def launch_llm_with_config(templates: List[ServerTemplate], config: Dict[str, object]) -> None:
    """Launch the selected CLI (MCP servers are synced separately)."""
    selected_id = config.get("selected_llm")
    if not selected_id:
        print("No LLM selected. Please select an LLM first.\n")
        input("Press Enter to continue...")
        return
    
    # Find the template
    template = None
    for t in templates:
        if t.unique_id == selected_id:
            template = t
            break
    
    if not template:
        print("Selected LLM template not found.\n")
        input("Press Enter to continue...")
        return
    
    # MCP servers are synced via each CLI's `mcp add/remove` commands (handled in
    # `select_mcp_servers`). Launching a CLI no longer rewrites config files.

    # Launch LLM
    cli_key = template.filename.replace(".json", "").replace(".toml", "").replace("_mcp", "").replace("_settings", "").replace("_config", "")
    cli_map = {
        "amazonq": "amazon_q",
        "claude_code": "claude_code",
        "claude_desktop": "claude_desktop",
        "cline": "cline",
        "gemini_cli": "gemini_cli",
        "github_copilot": "github_copilot",
        "kilo_code": "kilo_code",
        "opencode": "opencode",
        "qwen": "qwen",
        "codex": "codex",
    }
    
    cli_key = cli_map.get(cli_key, cli_key)
    
    cmd_config = CLI_LAUNCH_COMMANDS.get(cli_key)
    if cmd_config and isinstance(cmd_config, dict):
        cmd = cmd_config.get(template.os_mode)
    else:
        cmd = None
    
    if cmd:
        clear_screen()
        print_centered(f"Launching {template.display_name}...")
        print_centered(f"Command: {cmd}")
        print()
        
        log_history("launch_llm", {"template": template.unique_id, "command": cmd})
        
        # Special handling for WSL commands on Windows if we are running python on Windows
        if sys.platform == "win32" and template.os_mode == "wsl":
            # If the command is just 'cline' or 'gemini', we might need 'wsl -e bash -c "..."'
            # But if the user configured 'wsl' command to be 'wsl ...', then we just run it.
            # Our CLI_LAUNCH_COMMANDS for wsl just say "gemini", "cline", etc.
            # So we should wrap them in wsl call if we are on Windows.
            full_cmd = f'wsl -e bash -c "{cmd}"'
            subprocess.run(full_cmd, shell=True)
        else:
            # Run directly in current terminal for proper interaction
            if sys.platform == "win32":
                os.system(cmd)
            else:
                subprocess.run(cmd, shell=True)
    else:
        print(f"No launch command configured for {template.display_name}\n")
        input("Press Enter to continue...")


def batch_commands(templates: List[ServerTemplate], config: Dict[str, object]) -> None:
    """Batch command mode with simplified interface."""
    clear_screen()
    print_centered("=== Batch Commands ===")
    print("Enter commands and select which LLM to execute them with.")
    print("Press Ctrl+C to exit.\n")
    
    while True:
        try:
            cmd = input("Enter command (or 'quit' to exit): ").strip()
            if not cmd or cmd.lower() in ("quit", "exit", "q"):
                break
            
            # Show LLM options
            print("\nSelect LLM:")
            options = templates
            
            # Get last used or default
            last_server_id = config.get("last_batch_server")
            default_idx = None
            if last_server_id:
                for idx, template in enumerate(templates):
                    if template.unique_id == last_server_id:
                        default_idx = idx
                        break
            
            for idx, template in enumerate(options, start=1):
                marker = " (default)" if default_idx is not None and idx - 1 == default_idx else ""
                print(f"  {idx}. {template.display_name}{marker}")
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
            config["last_batch_server"] = selected_template.unique_id
            save_config(config)
            
            print(f"Executing with {selected_template.display_name}: {cmd}\n")
            log_history("batch_command", {"template": selected_template.unique_id, "command": cmd})
            
            try:
                # For batch commands, we might want to use the same launch logic (wsl vs windows)
                # But batch commands usually imply running the LLM with arguments?
                # Or is this running a system command?
                # The original code ran `subprocess.run(cmd, shell=True)`.
                # This seems to be running a shell command, not the LLM itself.
                # So the "Select LLM" here is just for logging/context? 
                # Or does it imply running the command IN the environment of the LLM?
                # Original code just ran `subprocess.run(cmd)`. 
                # It seems the "Select LLM" was just to record "I am doing this for X".
                # OR, maybe it was intended to wrap the command?
                # Given the original code, it just runs the command locally.
                
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
    clear_screen()
    print_centered("=== MCP Configuration Manager ===")
    print()
    
    # Show selected LLM
    selected_id = config.get("selected_llm")
    if selected_id:
        # We need templates to look up name, but we don't have them passed here.
        # We can just show the ID or try to parse it.
        # Ideally we pass templates or look it up.
        # For simplicity, let's just print the ID or a placeholder.
        # Or better, load templates in main loop and pass them.
        print(f"Selected LLM: {selected_id}") 
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
    print("  1. Select LLM Application")
    print("  2. Select MCP Servers (sync all)")
    print("  3. Sync MCP Servers (re-apply)")
    print("  4. Launch Application")
    print("  5. Batch Commands")
    print("  6. History")
    print("  7. Exit")
    print()


def main() -> None:
    ensure_environment()
    templates = load_templates()
    if not templates:
        print("No templates found in", SERVERS_DIR)
        return

    config = load_config()

    while True:
        # Update display name for selected LLM if possible
        selected_id = config.get("selected_llm")
        display_name = "None"
        if selected_id:
            for t in templates:
                if t.unique_id == selected_id:
                    display_name = t.display_name
                    break
        
        clear_screen()
        print_centered("=== MCP Configuration Manager ===")
        print()
        print_centered(f"Selected LLM: {display_name}")
        
        selected_servers = config.get("selected_mcp_servers", [])
        server_str = ", ".join(selected_servers) if selected_servers else "None"
        # Truncate if too long
        if len(server_str) > 60:
            server_str = server_str[:57] + "..."
        print_centered(f"MCP Servers: {server_str}")
        
        print("==================================================".center(shutil.get_terminal_size().columns))
        print()
        
        # Centered options? Or just left aligned in center?
        # Let's keep standard left aligned menu for readability
        print("  1. Select LLM Application")
        print("  2. Select MCP Servers (sync all)")
        print("  3. Sync MCP Servers (re-apply)")
        print("  4. Launch Application")
        print("  5. Batch Commands")
        print("  6. History")
        print("  7. Exit")
        print()
        
        choice = input("Choose an option: ").strip()

        if choice == "1":
            select_llm(templates, config)
        elif choice == "2":
            select_mcp_servers(templates, config)
        elif choice == "3":
            clear_screen()
            print_centered("Syncing MCP servers to all supported CLIs...")
            print()
            results = sync_mcp_all_clients(templates, config)
            if not results:
                print("No supported CLI targets found for the selected OS modes.")
            else:
                for result in results:
                    status = "✓" if result.ok else "✗"
                    print(f"{status} {result.client} ({result.os_mode})")
                    if result.error:
                        print(f"    {result.error}")
            print()
            input("Press Enter to continue...")
        elif choice == "4":
            launch_llm_with_config(templates, config)
        elif choice == "5":
            batch_commands(templates, config)
        elif choice == "6":
            display_history()
            input("Press Enter to continue...")
        elif choice == "7":
            print("Goodbye!")
            break
        else:
            print("Invalid option.")
            input("Press Enter to continue...")


if __name__ == "__main__":
    main()
