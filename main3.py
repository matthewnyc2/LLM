#!/usr/bin/env python3
"""MCP Server Configuration Manager - Self-Contained Version (main3.py)

MAIN DIFFERENCES FROM main2.py:
1. No dependency on servers/ directory - it's auto-created if missing
2. Can be run from ANY directory, not just the project directory
3. Uses bootstrap_templates() to auto-generate minimal templates on first run
4. Can copy existing servers/ from original location if available
5. Same features as main2.py (CLI selection, MCP config, project deployment)

ADVANTAGES:
- Completely portable - run from anywhere
- Self-healing - creates missing directories/files automatically
- No external Python dependencies (except optional colorama)
- Can be distributed as a single script

USAGE:
    python main3.py              # Runs from current directory
    python path/to/main3.py      # Can run from anywhere

The script will:
1. Create config.json, history.log, selections/ for state
2. Create servers/ with template files (auto-generated if needed)
3. Create generated/ for output configs
4. Reference external app locations defined in APP_LOCATIONS

This is ideal for distributed usage or as a standalone tool.
"""

import copy
import json
import os
import shutil
import subprocess
import sys
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
    "github_copilot_mcp.json": "copilot --allow-all-tools --allow-all-paths",
    "kilo_code_mcp.json": "kilocode",
    "opencode_config.json": "opencode",
    "roo_code_mcp.json": "roo-code",
    "codex_config.toml": "codex",
}

# Template for app locations - {project_root} will be replaced dynamically
APP_LOCATIONS_TEMPLATE = {
    "windows": {
        "amazonq_mcp.json": [r"C:\Users\matt\.aws\amazonq\mcp.json", r"C:\Users\matt\.aitk\mcp.json"],
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
        "amazonq_mcp.json": ["/home/matt/.aws/amazonq/mcp.json", "~/.aws/amazonq/mcp.json"],
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
        "amazonq_mcp.json": "{project_root}/.amazonq/mcp.json",
        "claude_code_mcp.json": "{project_root}/.mcp.json",
        "claude_desktop_config.json": "{project_root}/.claude_desktop_config.json",
        "cline_mcp_settings.json": "{project_root}/.clinerules",
        "gemini_cli_mcp.json": "{project_root}/.gemini/settings.json",
        "github_copilot_mcp.json": "{project_root}/.vscode/mcp.json",
        "kilo_code_mcp.json": "{project_root}/.kilocode/mcp.json",
        "opencode_config.json": "{project_root}/opencode.json",
        "roo_code_mcp.json": "{project_root}/.roo/mcp.json",
        "codex_config.toml": "{project_root}/.codex/config.toml",
    },
}

# Comprehensive MCP Server Database (100+ servers)
# Configuration format: MCP servers can use stdio (npx), http (remote), or docker (container)
MCP_SERVERS_DB = {
    "Browser Automation": {
        "playwright": {
            "name": "Playwright MCP",
            "description": "Browser automation and web scraping",
            "repo": "https://github.com/microsoft/playwright-mcp",
            "config": {"type": "stdio", "command": "npx", "args": ["@playwright/mcp@latest"]},
        },
        "puppeteer": {
            "name": "Puppeteer MCP",
            "description": "Headless browser control via Puppeteer",
            "repo": "https://github.com/modelcontextprotocol/servers",
            "config": {"type": "stdio", "command": "npx", "args": ["@modelcontextprotocol/server-puppeteer"]},
        },
        "browserbase": {
            "name": "Browserbase MCP",
            "description": "Cloud-based browser automation",
            "repo": "https://github.com/browserbase/mcp-server-browserbase",
            "config": {"type": "http", "url": "https://server.smithery.ai/@browserbasehq/mcp-browserbase/mcp"},
        },
        "skyvern": {
            "name": "Skyvern MCP",
            "description": "Browser control for LLMs via Skyvern",
            "repo": "https://github.com/Skyvern-AI/skyvern",
            "config": {"type": "stdio", "command": "npx", "args": ["skyvern-mcp"]},
        },
    },
    "Code & Version Control": {
        "github": {
            "name": "GitHub MCP",
            "description": "Interact with GitHub repositories, issues, and PRs",
            "repo": "https://github.com/github/github-mcp-server",
            "config": {"type": "stdio", "command": "docker", "args": ["run", "-i", "--rm", "-e", "GITHUB_PERSONAL_ACCESS_TOKEN", "ghcr.io/github/github-mcp-server"]},
        },
        "git": {
            "name": "Git MCP",
            "description": "Git repository operations and analysis",
            "repo": "https://github.com/modelcontextprotocol/servers",
            "config": {"type": "stdio", "command": "npx", "args": ["@modelcontextprotocol/server-git"]},
        },
        "gitlab": {
            "name": "GitLab MCP",
            "description": "GitLab integration and API access",
            "repo": "https://github.com/modelcontextprotocol/servers",
            "config": {"type": "stdio", "command": "npx", "args": ["@modelcontextprotocol/server-gitlab"]},
        },
    },
    "Databases": {
        "postgres": {
            "name": "PostgreSQL MCP",
            "description": "Query and manage PostgreSQL databases",
            "repo": "https://github.com/modelcontextprotocol/servers",
            "config": {"type": "stdio", "command": "npx", "args": ["@modelcontextprotocol/server-postgres"]},
        },
        "supabase": {
            "name": "Supabase MCP",
            "description": "Supabase database and auth integration",
            "repo": "https://github.com/supabase-community/supabase-mcp",
            "config": {"type": "http", "url": "https://server.smithery.ai/supabase/mcp"},
        },
        "mongodb": {
            "name": "MongoDB MCP",
            "description": "MongoDB database access and queries",
            "repo": "https://github.com/modelcontextprotocol/servers",
            "config": {"type": "stdio", "command": "npx", "args": ["@modelcontextprotocol/server-mongodb"]},
        },
        "mysql": {
            "name": "MySQL MCP",
            "description": "MySQL/MariaDB database access",
            "repo": "https://github.com/modelcontextprotocol/servers",
            "config": {"type": "stdio", "command": "npx", "args": ["@modelcontextprotocol/server-mysql"]},
        },
        "mindsdb": {
            "name": "MindsDB MCP",
            "description": "Connect AI to multiple data sources",
            "repo": "https://github.com/mindsdb/mindsdb_mcp_server",
            "config": {"type": "stdio", "command": "npx", "args": ["mindsdb-mcp"]},
        },
        "sqlite": {
            "name": "SQLite MCP",
            "description": "SQLite database operations and business insights",
            "repo": "https://github.com/modelcontextprotocol/servers",
            "config": {"type": "stdio", "command": "npx", "args": ["@modelcontextprotocol/server-sqlite"]},
        },
    },
    "Communication": {
        "slack": {
            "name": "Slack MCP",
            "description": "Send messages and manage Slack workspace",
            "repo": "https://github.com/modelcontextprotocol/servers",
            "config": {"type": "http", "url": "https://server.smithery.ai/slack/mcp"},
        },
        "gmail": {
            "name": "Gmail MCP",
            "description": "Read and send emails via Gmail",
            "repo": "https://github.com/modelcontextprotocol/servers",
            "config": {"type": "stdio", "command": "npx", "args": ["gmail-mcp"]},
        },
        "discord": {
            "name": "Discord MCP",
            "description": "Discord server and message management",
            "repo": "https://github.com/modelcontextprotocol/servers",
            "config": {"type": "stdio", "command": "npx", "args": ["discord-mcp"]},
        },
    },
    "Cloud Platforms": {
        "aws": {
            "name": "AWS MCP",
            "description": "Amazon Web Services integration",
            "repo": "https://github.com/aws/aws-mcp-server",
            "config": {"type": "stdio", "command": "npx", "args": ["@aws-sdk/mcp-server"]},
        },
        "azure": {
            "name": "Azure MCP",
            "description": "Microsoft Azure services integration",
            "repo": "https://github.com/modelcontextprotocol/servers",
            "config": {"type": "stdio", "command": "npx", "args": ["azure-mcp"]},
        },
        "cloudflare": {
            "name": "Cloudflare MCP",
            "description": "Cloudflare Workers, KV, R2, D1",
            "repo": "https://github.com/cloudflare/mcp-server-cloudflare",
            "config": {"type": "stdio", "command": "npx", "args": ["@cloudflare/mcp-server-cloudflare"]},
        },
        "kubernetes": {
            "name": "Kubernetes MCP",
            "description": "Kubernetes cluster management",
            "repo": "https://github.com/modelcontextprotocol/servers",
            "config": {"type": "stdio", "command": "npx", "args": ["@modelcontextprotocol/server-kubernetes"]},
        },
        "docker": {
            "name": "Docker MCP",
            "description": "Docker container and image management",
            "repo": "https://github.com/docker/mcp-server-docker",
            "config": {"type": "stdio", "command": "docker", "args": ["run", "-i", "--rm", "-v", "/var/run/docker.sock:/var/run/docker.sock", "mcp-docker"]},
        },
    },
    "Productivity & Collaboration": {
        "notion": {
            "name": "Notion MCP",
            "description": "Notion databases and pages access",
            "repo": "https://github.com/modelcontextprotocol/servers",
            "config": {"type": "http", "url": "https://server.smithery.ai/notion/mcp"},
        },
        "airtable": {
            "name": "Airtable MCP",
            "description": "Airtable base and records management",
            "repo": "https://github.com/modelcontextprotocol/servers",
            "config": {"type": "stdio", "command": "npx", "args": ["@modelcontextprotocol/server-airtable"]},
        },
        "jira": {
            "name": "Jira MCP",
            "description": "Jira project and issue management",
            "repo": "https://github.com/modelcontextprotocol/servers",
            "config": {"type": "http", "url": "https://server.smithery.ai/jira/mcp"},
        },
        "asana": {
            "name": "Asana MCP",
            "description": "Asana project and task management",
            "repo": "https://github.com/modelcontextprotocol/servers",
            "config": {"type": "stdio", "command": "npx", "args": ["@modelcontextprotocol/server-asana"]},
        },
        "trello": {
            "name": "Trello MCP",
            "description": "Trello board and card management",
            "repo": "https://github.com/modelcontextprotocol/servers",
            "config": {"type": "stdio", "command": "npx", "args": ["@modelcontextprotocol/server-trello"]},
        },
        "monday": {
            "name": "Monday.com MCP",
            "description": "Monday.com workspace management",
            "repo": "https://github.com/modelcontextprotocol/servers",
            "config": {"type": "stdio", "command": "npx", "args": ["@modelcontextprotocol/server-monday"]},
        },
    },
    "Search & Data Extraction": {
        "exa": {
            "name": "Exa MCP",
            "description": "Web search and content extraction",
            "repo": "https://github.com/exa-labs/mcp",
            "config": {"type": "http", "url": "https://server.smithery.ai/exa/mcp"},
        },
        "perplexity": {
            "name": "Perplexity MCP",
            "description": "Perplexity AI search integration",
            "repo": "https://github.com/modelcontextprotocol/servers",
            "config": {"type": "stdio", "command": "npx", "args": ["@modelcontextprotocol/server-perplexity"]},
        },
        "brave-search": {
            "name": "Brave Search MCP",
            "description": "Brave Search API integration",
            "repo": "https://github.com/modelcontextprotocol/servers",
            "config": {"type": "stdio", "command": "npx", "args": ["@modelcontextprotocol/server-brave"]},
        },
        "fetch": {
            "name": "Fetch MCP",
            "description": "Web content fetching and HTML to markdown conversion",
            "repo": "https://github.com/modelcontextprotocol/servers",
            "config": {"type": "stdio", "command": "uvx", "args": ["mcp-server-fetch"]},
        },
    },
    "Developer Tools": {
        "openapi": {
            "name": "OpenAPI MCP",
            "description": "Access any API with OpenAPI documentation",
            "repo": "https://github.com/modelcontextprotocol/servers",
            "config": {"type": "stdio", "command": "npx", "args": ["@modelcontextprotocol/server-openapi"]},
        },
        "pulumi": {
            "name": "Pulumi MCP",
            "description": "Infrastructure as Code with Pulumi",
            "repo": "https://github.com/pulumi/pulumi-mcp",
            "config": {"type": "stdio", "command": "npx", "args": ["@pulumi/mcp-server"]},
        },
        "terraform": {
            "name": "Terraform MCP",
            "description": "Terraform infrastructure management",
            "repo": "https://github.com/modelcontextprotocol/servers",
            "config": {"type": "stdio", "command": "npx", "args": ["@modelcontextprotocol/server-terraform"]},
        },
        "ref": {
            "name": "Ref Tools MCP",
            "description": "Access documentation for APIs, services, libraries",
            "repo": "https://github.com/ref-tools/ref-tools-mcp",
            "config": {"type": "stdio", "command": "npx", "args": ["ref-tools-mcp"]},
        },
        "desktop-commander": {
            "name": "Desktop Commander MCP",
            "description": "Terminal control, file system search and diff editing",
            "repo": "https://github.com/wonderwhy-er/DesktopCommanderMCP",
            "config": {"type": "stdio", "command": "npx", "args": ["@wonderwhy-er/desktop-commander"]},
        },
        "serena": {
            "name": "Serena MCP",
            "description": "Semantic code retrieval and editing toolkit",
            "repo": "https://github.com/oraios/serena",
            "config": {"type": "stdio", "command": "uvx", "args": ["serena"]},
        },
    },
    "File Systems": {
        "local-filesystem": {
            "name": "Local Filesystem MCP",
            "description": "Read/write local file system",
            "repo": "https://github.com/modelcontextprotocol/servers",
            "config": {"type": "stdio", "command": "npx", "args": ["@modelcontextprotocol/server-filesystem"]},
        },
        "s3": {
            "name": "AWS S3 MCP",
            "description": "Amazon S3 bucket management",
            "repo": "https://github.com/modelcontextprotocol/servers",
            "config": {"type": "stdio", "command": "npx", "args": ["@modelcontextprotocol/server-s3"]},
        },
    },
    "Knowledge & Memory": {
        "obsidian": {
            "name": "Obsidian Notes MCP",
            "description": "Obsidian vault access and management",
            "repo": "https://github.com/modelcontextprotocol/servers",
            "config": {"type": "stdio", "command": "npx", "args": ["@modelcontextprotocol/server-obsidian"]},
        },
        "memory": {
            "name": "Memory MCP",
            "description": "Knowledge graph-based persistent memory system",
            "repo": "https://github.com/modelcontextprotocol/servers",
            "config": {"type": "stdio", "command": "npx", "args": ["@modelcontextprotocol/server-memory"]},
        },
    },
    "Finance": {
        "alpha-vantage": {
            "name": "Alpha Vantage MCP",
            "description": "Stock market data and analysis",
            "repo": "https://github.com/modelcontextprotocol/servers",
            "config": {"type": "stdio", "command": "npx", "args": ["@modelcontextprotocol/server-alpha-vantage"]},
        },
        "cryptocompare": {
            "name": "CryptoCompare MCP",
            "description": "Cryptocurrency price and market data",
            "repo": "https://github.com/modelcontextprotocol/servers",
            "config": {"type": "stdio", "command": "npx", "args": ["@modelcontextprotocol/server-cryptocompare"]},
        },
    },
    "Media Processing": {
        "mermaid": {
            "name": "Mermaid MCP",
            "description": "AI-powered diagram generation",
            "repo": "https://github.com/modelcontextprotocol/servers",
            "config": {"type": "stdio", "command": "npx", "args": ["@modelcontextprotocol/server-mermaid"]},
        },
        "imagemagick": {
            "name": "ImageMagick MCP",
            "description": "Image processing and manipulation",
            "repo": "https://github.com/modelcontextprotocol/servers",
            "config": {"type": "stdio", "command": "npx", "args": ["@modelcontextprotocol/server-imagemagick"]},
        },
    },
    "Social Media": {
        "youtube": {
            "name": "YouTube MCP",
            "description": "YouTube video search and access",
            "repo": "https://github.com/modelcontextprotocol/servers",
            "config": {"type": "stdio", "command": "npx", "args": ["@modelcontextprotocol/server-youtube"]},
        },
        "twitter": {
            "name": "Twitter/X MCP",
            "description": "Twitter/X API integration",
            "repo": "https://github.com/modelcontextprotocol/servers",
            "config": {"type": "stdio", "command": "npx", "args": ["@modelcontextprotocol/server-twitter"]},
        },
        "reddit": {
            "name": "Reddit MCP",
            "description": "Reddit data and community access",
            "repo": "https://github.com/modelcontextprotocol/servers",
            "config": {"type": "stdio", "command": "npx", "args": ["@modelcontextprotocol/server-reddit"]},
        },
    },
    "AI & Research": {
        "sequential-thinking": {
            "name": "Sequential Thinking MCP",
            "description": "Advanced reasoning and problem solving",
            "repo": "https://github.com/modelcontextprotocol/servers",
            "config": {"type": "http", "url": "https://server.smithery.ai/@smithery-ai/server-sequential-thinking/mcp"},
        },
        "context7": {
            "name": "Context7 MCP",
            "description": "Fetch documentation and code examples",
            "repo": "https://github.com/context7-ai/context7-mcp",
            "config": {"type": "http", "url": "https://mcp.context7.com/mcp"},
        },
        "zen": {
            "name": "Zen MCP",
            "description": "Multi-AI orchestration for code analysis and development",
            "repo": "https://github.com/BeehiveInnovations/zen-mcp-server",
            "config": {"type": "stdio", "command": "uvx", "args": ["zen-mcp"]},
        },
        "gemini-cli-server": {
            "name": "Gemini CLI MCP Server",
            "description": "Gemini CLI running as MCP server with custom tools",
            "repo": "https://github.com/google-gemini/gemini-cli",
            "config": {"type": "stdio", "command": "gemini", "args": ["mcp", "server"]},
        },
        "claude-desktop-server": {
            "name": "Claude Desktop MCP Server",
            "description": "Claude Desktop as MCP server with FastMCP integration",
            "repo": "https://github.com/modelcontextprotocol/python-sdk",
            "config": {"type": "stdio", "command": "uv", "args": ["run", "--with", "mcp[cli]", "mcp", "run"]},
        },
    },
}

@dataclass
class LLMTemplate:
    """Represents a configuration template for a particular LLM."""

    filename: str
    display_name: str
    path: Path
    format: str  # json or toml
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


def ensure_environment() -> None:
    """Ensure directories and default files exist."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    SERVERS_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    SELECTIONS_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_PATH.exists():
        save_config(DEFAULT_CONFIG)
    if not HISTORY_PATH.exists():
        HISTORY_PATH.touch()

    # Auto-bootstrap: If templates don't exist, create minimal ones
    bootstrap_templates()


def get_project_root() -> Path:
    """Auto-detect project root directory.

    Priority order:
    1. Git repository root (if running inside a git repo)
    2. Directory containing this script (CONFIG_DIR)

    This allows main3.py to work with any project automatically.
    """

    # Try to find git repository root
    try:
        current = CONFIG_DIR
        while current != current.parent:  # Stop at filesystem root
            if (current / ".git").exists():
                return current
            current = current.parent
    except Exception:
        pass

    # Fall back to script's directory
    return CONFIG_DIR


def get_app_locations() -> Dict[str, Dict[str, str]]:
    """Get app locations with project root dynamically substituted.

    Returns a copy of APP_LOCATIONS_TEMPLATE with {project_root} replaced
    with the actual detected project root path.
    """
    project_root = get_project_root()
    locations = copy.deepcopy(APP_LOCATIONS_TEMPLATE)

    # Replace {project_root} placeholders in project locations using Path operations
    for cli_name, path_template in locations.get("project", {}).items():
        if isinstance(path_template, str):
            if "{project_root}" in path_template:
                # Extract relative path by removing {project_root}/ prefix
                # Template format is always "{project_root}/<relative_path>"
                relative_path = path_template.replace("{project_root}/", "")
                # Split by forward slashes and build path with joinpath
                parts = relative_path.split("/")
                full_path = project_root.joinpath(*parts)
                locations["project"][cli_name] = str(full_path)
            else:
                locations["project"][cli_name] = path_template

        elif isinstance(path_template, list):
            resolved_paths = []
            for p in path_template:
                if "{project_root}" in p:
                    relative_path = p.replace("{project_root}/", "")
                    parts = relative_path.split("/")
                    full_path = project_root.joinpath(*parts)
                    resolved_paths.append(str(full_path))
                else:
                    resolved_paths.append(p)
            locations["project"][cli_name] = resolved_paths

    return locations


def bootstrap_templates() -> None:
    """Auto-create template files if they don't exist (for self-contained usage).

    This allows main3.py to be run from anywhere without requiring the servers/ directory.
    """
    # List of template files to create if missing
    required_templates = [
        "amazonq_mcp.json",
        "claude_code_mcp.json",
        "claude_desktop_config.json",
        "cline_mcp_settings.json",
        "gemini_cli_mcp.json",
        "github_copilot_mcp.json",
        "kilo_code_mcp.json",
        "opencode_config.json",
        "roo_code_mcp.json",
        "codex_config.toml",
    ]

    # Check if any templates are missing
    missing_templates = [t for t in required_templates if not (SERVERS_DIR / t).exists()]

    if not missing_templates:
        return  # All templates exist

    # Try to copy from alternate location first (in case we're in a different directory)
    original_servers_dir = Path(__file__).parent / "servers"
    if original_servers_dir.exists() and original_servers_dir != SERVERS_DIR:
        print(f"{Fore.CYAN}Copying template files from {original_servers_dir}...{Style.RESET_ALL}")
        for template_file in original_servers_dir.glob("*"):
            if template_file.suffix in [".json", ".toml"]:
                try:
                    shutil.copy2(template_file, SERVERS_DIR / template_file.name)
                except Exception as e:
                    print(f"{Fore.YELLOW}Warning: Could not copy {template_file.name}: {e}{Style.RESET_ALL}")
        return

    # If templates still missing, create minimal templates with empty mcpServers
    print(f"{Fore.YELLOW}Auto-creating minimal template files in {SERVERS_DIR}...{Style.RESET_ALL}")

    for template_name in required_templates:
        template_path = SERVERS_DIR / template_name

        if template_path.exists():
            continue

        try:
            if template_name.endswith(".toml"):
                # Create empty TOML template
                content = "# MCP Servers Configuration\n# Add servers with [[mcp_servers.NAME]] sections\n"
                template_path.write_text(content)
            else:
                # Create empty JSON template with proper structure
                if "settings" in template_name or template_name == "cline_mcp_settings.json":
                    # Cline uses mcp_servers
                    data = {"mcp_servers": {}}
                else:
                    # Most use mcpServers
                    data = {"mcpServers": {}}

                template_path.write_text(json.dumps(data, indent=2))

            print(f"  {Fore.GREEN}✓{Style.RESET_ALL} Created {template_name}")
        except Exception as e:
            print(f"  {Fore.RED}✗{Style.RESET_ALL} Failed to create {template_name}: {e}")


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
    with CONFIG_PATH.open("w", encoding="utf-8") as handle:
        json.dump(config, handle, indent=2)


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
    selection_file = SELECTIONS_DIR / f"{cli_name}.json"
    with selection_file.open("w", encoding="utf-8") as f:
        json.dump({
            "cli": cli_name,
            "selected_servers": sorted(list(selected)),
            "timestamp": datetime.now().isoformat()
        }, f, indent=2)


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


def load_toml_template(path: Path) -> tuple[LLMTemplate, Dict[str, object]]:
    """Load a TOML template and return both the template and available servers."""
    header_lines: List[str] = []
    server_blocks: Dict[str, List[str]] = {}

    current_name: Optional[str] = None
    current_block: List[str] = []

    with path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.rstrip("\n")
            if current_name is None:
                if line.startswith("[mcp_servers."):
                    current_name = line[len("[mcp_servers.") :].rstrip("]")
                    current_block = [line]
                else:
                    header_lines.append(line)
            else:
                if line.startswith("[mcp_servers."):
                    server_blocks[current_name] = current_block
                    current_name = line[len("[mcp_servers.") :].rstrip("]")
                    current_block = [line]
                else:
                    current_block.append(line)

    if current_name is not None:
        server_blocks[current_name] = current_block

    while header_lines and not header_lines[-1].strip():
        header_lines.pop()

    template = LLMTemplate(
        filename=path.name,
        display_name=LLM_DISPLAY_NAMES.get(path.name, path.stem.replace("_", " ").title()),
        path=path,
        format="toml",
        metadata={},
        header_lines=header_lines,
    )

    return template, server_blocks


def load_all_llms_and_servers() -> tuple[List[LLMTemplate], Dict[str, object]]:
    """Load all LLM templates and aggregate all available MCP servers."""
    llms: List[LLMTemplate] = []
    all_servers: Dict[str, object] = {}

    for path in sorted(SERVERS_DIR.iterdir()):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".json", ".toml"}:
            continue
        try:
            if path.suffix.lower() == ".json":
                template, servers = load_json_template(path)
            else:
                template, servers = load_toml_template(path)

            llms.append(template)
            for server_name, server_config in servers.items():
                if server_name not in all_servers:
                    all_servers[server_name] = server_config
        except ValueError as exc:
            print(f"Skipping {path.name}: {exc}")
            continue

    return llms, all_servers


def display_server_selector(cli_name: str, cli_display_name: str) -> Set[str]:
    """Display servers organized by category with column layout."""
    
    # Load previously selected servers
    selected = load_selections(cli_name)
    selected_keys = set(selected)
    
    # Build numbered list for selection
    server_index = {}
    num = 1
    
    while True:
        # Clear screen
        os.system("cls" if os.name == "nt" else "clear")
        
        print(f"\n{Fore.CYAN}{'='*80}")
        print(f"MCP Server Selection for: {Fore.YELLOW}{cli_display_name}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}Selected: {len(selected_keys)} servers{Style.RESET_ALL}\n")
        
        # Reset numbering
        server_index.clear()
        num = 1
        
        # Display by category
        for category, servers in MCP_SERVERS_DB.items():
            print(f"{Fore.MAGENTA}{category}:{Style.RESET_ALL}")
            print(f"{Fore.MAGENTA}{'-' * len(category)}{Style.RESET_ALL}")
            
            # Display servers in 4 columns
            server_list = list(servers.items())
            for i in range(0, len(server_list), 4):
                line_parts = []
                for j in range(4):
                    if i + j < len(server_list):
                        key, info = server_list[i + j]
                        selected = "[x]" if key in selected_keys else "[ ]"
                        color = Fore.GREEN if key in selected_keys else Fore.WHITE
                        server_index[num] = key
                        line_parts.append(f"{num:2d}. {selected} {color}{info['name']:<18}{Style.RESET_ALL}")
                        num += 1
                    else:
                        line_parts.append(" " * 25)
                
                print(f"  {line_parts[0]}  {line_parts[1]}  {line_parts[2]}  {line_parts[3]}")
            print()
        
        print(f"{Fore.CYAN}{'-' * 80}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Commands:{Style.RESET_ALL}")
        print(f"  {Fore.WHITE}[1-{num-1}] toggle selection  | [all] select all    | [none] clear all{Style.RESET_ALL}")
        print(f"  {Fore.WHITE}[done] finish & save        | [q] quit without saving{Style.RESET_ALL}")
        
        cmd = input(f"\n{Fore.CYAN}Command: {Style.RESET_ALL}").strip().lower()
        
        if cmd == 'q':
            break
        elif cmd == 'done':
            save_selections(cli_name, selected_keys)
            return selected_keys
        elif cmd == 'all':
            for category, servers in MCP_SERVERS_DB.items():
                for server_key in servers.keys():
                    selected_keys.add(server_key)
        elif cmd == 'none':
            selected_keys.clear()
        elif cmd.isdigit():
            num_cmd = int(cmd)
            if num_cmd in server_index:
                server_key = server_index[num_cmd]
                if server_key in selected_keys:
                    selected_keys.discard(server_key)
                else:
                    selected_keys.add(server_key)

    return set()


def select_cli() -> Optional[str]:
    """Select CLI program to configure."""
    llms, _ = load_all_llms_and_servers()
    
    if not llms:
        print(f"{Fore.RED}No LLM templates found!{Style.RESET_ALL}")
        return None

    while True:
        os.system("cls" if os.name == "nt" else "clear")
        print(f"\n{Fore.CYAN}{'='*80}")
        print(f"Select CLI Program to Configure")
        print(f"{'='*80}{Style.RESET_ALL}\n")

        for idx, llm in enumerate(llms, start=1):
            print(f"  {Fore.YELLOW}{idx}.{Style.RESET_ALL} {Fore.WHITE}{llm.display_name}{Style.RESET_ALL}")

        print(f"  {Fore.RED}Q.{Style.RESET_ALL} {Fore.WHITE}Exit{Style.RESET_ALL}\n")

        choice = input(f"{Fore.CYAN}Selection: {Style.RESET_ALL}").strip().lower()

        if choice == 'q':
            return None

        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(llms):
                return llms[idx].filename

        print(f"{Fore.RED}Invalid selection{Style.RESET_ALL}")
        input("Press Enter...")

    return None


def apply_servers_to_cli(cli_filename: str, selected_servers: Set[str]) -> None:
    """Apply selected MCP servers to all JSON config files."""
    json_files = [
        f
        for f in SERVERS_DIR.iterdir()
        if f.suffix.lower() == ".json" and f.name.endswith(cli_filename)
    ]

    if not json_files:
        print(f"No config file found: {cli_filename}")
        return

    print(f"\nApplying {len(selected_servers)} servers to {cli_filename}...")

    for json_file in json_files:
        try:
            with json_file.open("r", encoding="utf-8") as f:
                data = json.load(f)

            # Find the servers container key
            container_key = None
            for key in ("mcpServers", "mcp_servers", "mcp"):
                if key in data:
                    container_key = key
                    break

            if container_key is None:
                continue

            # Build server configs from DB
            # Filter out 'type' field for JSON configs (type is for transport negotiation, not config format)
            new_servers = {}
            for category, servers in MCP_SERVERS_DB.items():
                for server_key, server_info in servers.items():
                    if server_key in selected_servers:
                        config = server_info["config"].copy()
                        # Remove 'type' field - it's for internal use, not for JSON output
                        if "type" in config:
                            del config["type"]
                        new_servers[server_key] = config

            # Update servers
            data[container_key] = {**data[container_key], **new_servers}

            # Write back
            with json_file.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            print(f"  ✓ {json_file.name}: Updated")

        except Exception as exc:
            print(f"  ✗ {json_file.name}: {exc}")


def _extract_toml_prefix_before_mcp(target_path: Path) -> str:
    """Return any TOML content that appears before the first [mcp_servers.*] table."""
    if not target_path.exists():
        return ""

    lines = target_path.read_text(encoding="utf-8").splitlines()
    prefix_lines: List[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[mcp_servers."):
            break
        prefix_lines.append(line)

    return "\n".join(prefix_lines).rstrip()


def _write_toml_mcp_servers(target_path: Path, new_servers: Dict[str, Dict[str, object]]) -> None:
    """Write MCP server definitions to a TOML file while preserving non-MCP sections."""
    prefix = _extract_toml_prefix_before_mcp(target_path)
    sections: List[str] = []

    if prefix:
        sections.append(prefix)

    server_blocks: List[str] = []
    for server_name in sorted(new_servers.keys()):
        server_config = new_servers[server_name]
        block_lines = [f"[mcp_servers.{server_name}]"]
        if isinstance(server_config, dict):
            for key, value in server_config.items():
                if key == "args" and isinstance(value, list):
                    args_str = ", ".join(f'"{arg}"' for arg in value)
                    block_lines.append(f"{key} = [{args_str}]")
                elif isinstance(value, str):
                    block_lines.append(f'{key} = "{value}"')
                elif isinstance(value, bool):
                    bool_str = "true" if value else "false"
                    block_lines.append(f"{key} = {bool_str}")
                else:
                    block_lines.append(f"{key} = {value}")
        server_blocks.append("\n".join(block_lines))

    if server_blocks:
        sections.append("\n\n".join(server_blocks))

    filtered_sections = [section.rstrip() for section in sections if section and section.strip()]
    content = "\n\n".join(filtered_sections).rstrip() + "\n"

    with target_path.open("w", encoding="utf-8") as f:
        f.write(content)


def deploy_config_to_app_locations(cli_filename: str, selected_servers: Set[str], location_types: List[str] = None) -> None:
    """Deploy MCP server configuration to app locations.

    By default, deploys to both global (windows) and project-level locations.
    Automatically detects project root for project-level deployments.

    Args:
        cli_filename: The CLI config filename (e.g., "claude_code_mcp.json")
        selected_servers: Set of selected server keys to deploy
        location_types: List of location types to deploy to (default: ["windows", "project"])
    """

    if location_types is None:
        location_types = ["windows", "project"]

    # Build server configs from DB
    # Filter out 'type' field for JSON configs (type is for transport negotiation, not config format)
    new_servers = {}
    for category, servers in MCP_SERVERS_DB.items():
        for server_key, server_info in servers.items():
            if server_key in selected_servers:
                config = server_info["config"].copy()
                # Remove 'type' field - it's for internal use, not for JSON output
                if "type" in config:
                    del config["type"]
                new_servers[server_key] = config

    # Show detected project root at start
    project_root = get_project_root()
    print(f"\n{Fore.GREEN}Detected project root: {project_root}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Deploying configuration to app locations...{Style.RESET_ALL}\n")

    # Get all locations with dynamic substitution
    all_locations = get_app_locations()

    # Deploy to each location type
    for location_type in location_types:
        locations = all_locations.get(location_type, {})
        target_paths = locations.get(cli_filename)

        if not target_paths:
            print(f"  {Fore.YELLOW}⚠ {location_type.upper()}: No locations configured for {cli_filename}{Style.RESET_ALL}")
            continue

        # Print which location type we're deploying to
        if location_type == "project":
            print(f"{Fore.CYAN}→ To Project ({location_type}):{Style.RESET_ALL}")
        else:
            print(f"{Fore.CYAN}→ To {location_type.upper()}:{Style.RESET_ALL}")

        # Handle single path or list of paths
        if isinstance(target_paths, str):
            target_paths = [target_paths]

        for target_path_raw in target_paths:
            try:
                # Expand environment variables
                target_path = Path(os.path.expandvars(target_path_raw))

                # Create parent directories if needed
                target_path.parent.mkdir(parents=True, exist_ok=True)

                # Determine if JSON or TOML
                if target_path.suffix.lower() == ".toml":
                    _write_toml_mcp_servers(target_path, new_servers)
                    print(f"  {Fore.GREEN}✓{Style.RESET_ALL} {target_path}")
                else:
                    # For JSON files
                    if target_path.exists():
                        with target_path.open("r", encoding="utf-8") as f:
                            data = json.load(f)
                    else:
                        data = {}

                    # Find or create container key
                    container_key = None
                    for key in ("mcpServers", "mcp_servers", "mcp"):
                        if key in data:
                            container_key = key
                            break

                    if container_key is None:
                        container_key = "mcpServers"

                    # Update servers
                    if container_key not in data:
                        data[container_key] = {}
                    data[container_key].update(new_servers)

                    # Write JSON
                    with target_path.open("w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)

                    print(f"  {Fore.GREEN}✓{Style.RESET_ALL} {target_path}")

            except Exception as exc:
                print(f"  {Fore.RED}✗{Style.RESET_ALL} {target_path_raw}: {exc}")



def install_all_to_project(config: Dict[str, object]) -> None:
    """Deploy selected MCP servers to project-level config files for ALL CLI programs.

    Automatically detects project root and deploys to all configured project locations.
    """

    # Get currently selected CLI
    current_cli = config.get("selected_llm")
    if not current_cli:
        print(f"\n{Fore.RED}No CLI selected. Please select one first (Option 1).{Style.RESET_ALL}")
        input("Press Enter to continue...")
        return

    # Load selections for current CLI
    selected_servers = load_selections(current_cli)
    if not selected_servers:
        print(f"\n{Fore.RED}No servers selected for {LLM_DISPLAY_NAMES.get(current_cli, current_cli)}.{Style.RESET_ALL}")
        print(f"Please configure servers first (Option 2).")
        input("Press Enter to continue...")
        return

    # Build server configs from DB
    # Filter out 'type' field for JSON configs (type is for transport negotiation, not config format)
    new_servers = {}
    for category, servers in MCP_SERVERS_DB.items():
        for server_key, server_info in servers.items():
            if server_key in selected_servers:
                config = server_info["config"].copy()
                # Remove 'type' field - it's for internal use, not for JSON output
                if "type" in config:
                    del config["type"]
                new_servers[server_key] = config

    # Get project locations with dynamic root substitution
    locations = get_app_locations().get("project", {})

    if not locations:
        print(f"\n{Fore.RED}No project locations configured.{Style.RESET_ALL}")
        input("Press Enter to continue...")
        return

    # Show detected project root
    project_root = get_project_root()
    print(f"\n{Fore.GREEN}Detected project root: {project_root}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Installing {len(selected_servers)} servers to ALL project configurations...{Style.RESET_ALL}\n")

    deployed_count = 0
    for cli_filename, target_path_raw in locations.items():
        try:
            # Handle single path or list of paths
            if isinstance(target_path_raw, list):
                target_path_raw = target_path_raw[0]

            # Expand environment variables
            target_path = Path(os.path.expandvars(target_path_raw))

            # Create parent directories
            target_path.parent.mkdir(parents=True, exist_ok=True)

            # Determine format and write
            if target_path.suffix.lower() == ".toml":
                _write_toml_mcp_servers(target_path, new_servers)
            else:
                # JSON format
                if target_path.exists():
                    with target_path.open("r", encoding="utf-8") as f:
                        try:
                            data = json.load(f)
                        except:
                            data = {}
                else:
                    data = {}

                container_key = None
                for key in ("mcpServers", "mcp_servers", "mcp"):
                    if key in data:
                        container_key = key
                        break

                if container_key is None:
                    container_key = "mcpServers"

                if container_key not in data:
                    data[container_key] = {}
                data[container_key].update(new_servers)

                with target_path.open("w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

            cli_display_name = LLM_DISPLAY_NAMES.get(cli_filename, cli_filename)
            print(f"  {Fore.GREEN}✓{Style.RESET_ALL} {cli_display_name}")
            deployed_count += 1

        except Exception as exc:
            cli_display_name = LLM_DISPLAY_NAMES.get(cli_filename, cli_filename)
            print(f"  {Fore.RED}✗{Style.RESET_ALL} {cli_display_name}: {exc}")

    print(f"\n{Fore.GREEN}Installed {len(selected_servers)} servers to {deployed_count} project locations!{Style.RESET_ALL}")
    log_history("install_all_to_project", {"servers": list(selected_servers), "count": deployed_count})
    input("Press Enter to continue...")


def main_menu(llms: List[LLMTemplate], all_servers: Dict[str, object], config: Dict[str, object]) -> None:
    """Display the main menu."""
    while True:
        os.system("cls" if os.name == "nt" else "clear")

        print(f"\n{Fore.CYAN}{'='*50}")
        print(f"MCP Configuration Manager")
        print(f"{'='*50}{Style.RESET_ALL}")

        # Display detected project root
        project_root = get_project_root()
        print(f"\n{Fore.MAGENTA}Project Root: {project_root}{Style.RESET_ALL}")

        selected_llm_filename = config.get("selected_llm")
        if selected_llm_filename:
            selected_llm = next((llm for llm in llms if llm.filename == selected_llm_filename), None)
            if selected_llm:
                print(f"{Fore.GREEN}Current CLI: {selected_llm.display_name}{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}Current CLI: None selected{Style.RESET_ALL}")

        print(f"\n{Fore.CYAN}{'-'*50}{Style.RESET_ALL}")
        print(f"\n{Fore.YELLOW}Options:{Style.RESET_ALL}")
        print(f"  {Fore.WHITE}1. Select CLI Program{Style.RESET_ALL}")
        print(f"  {Fore.WHITE}2. Configure MCP Servers{Style.RESET_ALL}")
        print(f"  {Fore.WHITE}3. Launch Selected CLI{Style.RESET_ALL}")
        print(f"  {Fore.WHITE}4. Install All to Project{Style.RESET_ALL}")
        print(f"  {Fore.WHITE}5. Load Super Assistant{Style.RESET_ALL}")
        print(f"  {Fore.WHITE}6. Exit{Style.RESET_ALL}")

        choice = input(f"\n{Fore.CYAN}Select option: {Style.RESET_ALL}").strip()

        if choice == "1":
            cli_filename = select_cli()
            if cli_filename:
                config["selected_llm"] = cli_filename
                save_config(config)
                print(f"\n{Fore.GREEN}✓ Selected {LLM_DISPLAY_NAMES.get(cli_filename, cli_filename)}{Style.RESET_ALL}")
                input("Press Enter to continue...")
        elif choice == "2":
            if not config.get("selected_llm"):
                print(f"\n{Fore.RED}No CLI selected. Please select one first.{Style.RESET_ALL}")
                input("Press Enter to continue...")
                continue

            cli_filename = config.get("selected_llm")
            cli_display_name = LLM_DISPLAY_NAMES.get(cli_filename, cli_filename)
            selected_servers = display_server_selector(cli_filename, cli_display_name)
            if selected_servers:
                apply_servers_to_cli(cli_filename, selected_servers)
                # Deploy to both global (windows) and project locations automatically
                deploy_config_to_app_locations(cli_filename, selected_servers)
                print(f"\n{Fore.GREEN}✓ Configured {len(selected_servers)} servers for {cli_display_name}{Style.RESET_ALL}")
                input("Press Enter to continue...")
        elif choice == "3":
            if not config.get("selected_llm"):
                print(f"\n{Fore.RED}No CLI selected. Please select one first.{Style.RESET_ALL}")
                input("Press Enter to continue...")
                continue

            cli_filename = config.get("selected_llm")
            cmd = CLI_LAUNCH_COMMANDS.get(cli_filename)
            if cmd:
                print(f"\n{Fore.GREEN}Launching {LLM_DISPLAY_NAMES.get(cli_filename, cli_filename)}...{Style.RESET_ALL}")
                try:
                    if sys.platform == "win32":
                        subprocess.run(cmd, shell=True)
                    else:
                        subprocess.run([cmd])
                except Exception as exc:
                    print(f"\n{Fore.RED}Error: {exc}{Style.RESET_ALL}")
                input("\nPress Enter to continue...")
        elif choice == "4":
            install_all_to_project(config)
        elif choice == "5":
            amazon_q_config = r"C:\Users\matt\.aws\amazonq\mcp.json"
            if not os.path.exists(amazon_q_config):
                print(f"\n{Fore.RED}Error: Amazon Q config not found at {amazon_q_config}{Style.RESET_ALL}")
                input("Press Enter to continue...")
                continue

            cmd = f"npx @srbhptl39/mcp-superassistant-proxy@latest --config {amazon_q_config} --outputTransport sse"
            print(f"\n{Fore.GREEN}Launching Super Assistant...{Style.RESET_ALL}")
            try:
                if sys.platform == "win32":
                    subprocess.run(cmd, shell=True)
                else:
                    subprocess.run(cmd.split())
            except Exception as exc:
                print(f"\n{Fore.RED}Error: {exc}{Style.RESET_ALL}")
            input("\nPress Enter to continue...")
        elif choice == "6":
            print(f"\n{Fore.GREEN}Goodbye!{Style.RESET_ALL}")
            break
        else:
            print(f"\n{Fore.RED}Invalid option.{Style.RESET_ALL}")
            input("Press Enter...")


def main() -> None:
    ensure_environment()
    llms, all_servers = load_all_llms_and_servers()

    if not llms:
        print("No LLM templates found!")
        return

    config = load_config()
    main_menu(llms, all_servers, config)


if __name__ == "__main__":
    main()
