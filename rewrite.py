import sys

mapping = {
    "init": """# Project Description

This is a Python-based CLI tool for managing Large Language Model (LLM) configurations, including MCP (Model Context Protocol) server setups for various LLMs like Claude, Gemini, and GitHub Copilot. It provides a modular structure for templates, generated configs, and a secondary TUI manager for agent building.

## Changes Made

- **Change:** Initialized the repository with core project structure.
- **Added:** Main CLI script (`llm.py`), `servers/` directory with JSON/TOML templates, `generated/` and `selections/` directories for outputs, `requirements.txt` for dependencies, and initial documentation files.
- **Removed:** Nothing (initial commit).

## Affected User Stories

- As a developer, I want to set up the project foundation so that I can begin configuring LLMs and MCP servers.
- As a user, I want a clear project structure to understand how to contribute and use the tool.

## Directory Tree

```
.
|-- AGENTS.md
|-- llm.py
|-- requirements.txt
|-- servers/
|-- generated/
|-- selections/
`-- __pycache__/
```

## Tags

#init #project-setup #llm-config #mcp-servers
""",

    "Add .gitignore for Python cache files and project-specific files": """# Project Description

This is a Python-based CLI tool for managing Large Language Model (LLM) configurations, including MCP (Model Context Protocol) server setups for various LLMs like Claude, Gemini, and GitHub Copilot. It provides a modular structure for templates, generated configs, and a secondary TUI manager for agent building.

## Changes Made

- **Change:** Added a .gitignore file to exclude unnecessary files from version control.
- **Added:** .gitignore file with rules for Python cache, virtual environments, IDE files, generated configs, and logs.
- **Removed:** None.

## Affected User Stories

- As a developer, I want to keep the repository clean by ignoring temporary and generated files.

## Directory Tree

```
.
|-- .gitignore
|-- AGENTS.md
|-- llm.py
|-- requirements.txt
|-- servers/
|-- generated/
|-- selections/
`-- __pycache__/
```

## Tags

#gitignore #cleanup #python
""",

    "Fix critical issues in llm.py identified by verification agents": """# Project Description

This is a Python-based CLI tool for managing Large Language Model (LLM) configurations, including MCP (Model Context Protocol) server setups for various LLMs like Claude, Gemini, and GitHub Copilot. It provides a modular structure for templates, generated configs, and a secondary TUI manager for agent building.

## Changes Made

- **Change:** Fixed critical issues in `llm.py` related to configuration loading, path expansion, and CLI commands.
- **Added:** Proper path expansion for Unix systems, missing CLI mappings for GitHub Copilot and Roo Code.
- **Removed:** Unused configuration keys like 'last_template' and 'selections'.

## Affected User Stories

- As a developer, I want the CLI to work correctly across platforms without syntax errors or missing commands.
- As a user, I want reliable launching of LLMs without configuration issues.

## Directory Tree

```
.
|-- .gitignore
|-- AGENTS.md
|-- llm.py
|-- requirements.txt
|-- servers/
|-- generated/
|-- selections/
`-- __pycache__/
```

## Tags

#bugfix #llm-py #cross-platform #config
""",

    "docs: add AGENTS.md contributor guide": """# Project Description

This is a Python-based CLI tool for managing Large Language Model (LLM) configurations, including MCP (Model Context Protocol) server setups for various LLMs like Claude, Gemini, and GitHub Copilot. It provides a modular structure for templates, generated configs, and a secondary TUI manager for agent building.

## Changes Made

- **Change:** Added contributor guide documentation.
- **Added:** `AGENTS.md` file with guidelines for project structure, coding style, testing, commits, and security.
- **Removed:** None.

## Affected User Stories

- As a contributor, I want clear guidelines to follow when working on the project.

## Directory Tree

```
.
|-- .gitignore
|-- AGENTS.md
|-- llm.py
|-- requirements.txt
|-- servers/
|-- generated/
|-- selections/
`-- __pycache__/
```

## Tags

#docs #contributor-guide #agile
""",

    "Consolidate to llm.py only and fix MCP server formatting": """# Project Description

This is a Python-based CLI tool for managing Large Language Model (LLM) configurations, including MCP (Model Context Protocol) server setups for various LLMs like Claude, Gemini, and GitHub Copilot. It provides a modular structure for templates, generated configs, and a secondary TUI manager for agent building.

## Changes Made

- **Change:** Consolidated multiple entry points into a single `llm.py` and fixed MCP server configurations.
- **Added:** WSL support for launching Cline from Windows, colorful UI elements.
- **Removed:** `main2.py`, `main3.py`, `fixit.py`, and test files; removed Roo Code references.

## Affected User Stories

- As a developer, I want a single, clean entry point for the application.
- As a user, I want cross-platform support for launching LLMs.

## Directory Tree

```
.
|-- .gitignore
|-- AGENTS.md
|-- llm.py
|-- requirements.txt
|-- servers/
|-- generated/
|-- selections/
`-- __pycache__/
```

## Tags

#refactor #consolidate #mcp-fix #wsl-support
""",

    "Remove main2.py and consolidate to llm.py": """# Project Description

This is a Python-based CLI tool for managing Large Language Model (LLM) configurations, including MCP (Model Context Protocol) server setups for various LLMs like Claude, Gemini, and GitHub Copilot. It provides a modular structure for templates, generated configs, and a secondary TUI manager for agent building.

## Changes Made

- **Change:** Merged pull request to consolidate code.
- **Added:** None.
- **Removed:** `main2.py` and related redundant files.

## Affected User Stories

- As a maintainer, I want to reduce code duplication by consolidating entry points.

## Directory Tree

```
.
|-- .gitignore
|-- AGENTS.md
|-- llm.py
|-- requirements.txt
|-- servers/
|-- generated/
|-- selections/
`-- __pycache__/
```

## Tags

#merge #consolidate #cleanup
""",

    "\"Claude PR Assistant workflow\"": """# Project Description

This is a Python-based CLI tool for managing Large Language Model (LLM) configurations, including MCP (Model Context Protocol) server setups for various LLMs like Claude, Gemini, and GitHub Copilot. It provides a modular structure for templates, generated configs, and a secondary TUI manager for agent building.

## Changes Made

- **Change:** Added GitHub Actions workflow for Claude PR Assistant.
- **Added:** Workflow file for automated PR assistance using Claude.
- **Removed:** None.

## Affected User Stories

- As a team, I want automated PR reviews and assistance via GitHub Actions.

## Directory Tree

```
.
|-- .gitignore
|-- AGENTS.md
|-- llm.py
|-- requirements.txt
|-- servers/
|-- generated/
|-- selections/
|-- .github/
|   `-- workflows/
`-- __pycache__/
```

## Tags

#ci-cd #github-actions #claude #pr-assistant
""",

    "\"Claude Code Review workflow\"": """# Project Description

This is a Python-based CLI tool for managing Large Language Model (LLM) configurations, including MCP (Model Context Protocol) server setups for various LLMs like Claude, Gemini, and GitHub Copilot. It provides a modular structure for templates, generated configs, and a secondary TUI manager for agent building.

## Changes Made

- **Change:** Added GitHub Actions workflow for Claude Code Review.
- **Added:** Workflow file for automated code reviews using Claude.
- **Removed:** None.

## Affected User Stories

- As a team, I want automated code reviews via GitHub Actions.

## Directory Tree

```
.
|-- .gitignore
|-- AGENTS.md
|-- llm.py
|-- requirements.txt
|-- servers/
|-- generated/
|-- selections/
|-- .github/
|   `-- workflows/
`-- __pycache__/
```

## Tags

#ci-cd #github-actions #claude #code-review
""",

    "Add Claude Code GitHub Workflow": """# Project Description

This is a Python-based CLI tool for managing Large Language Model (LLM) configurations, including MCP (Model Context Protocol) server setups for various LLMs like Claude, Gemini, and GitHub Copilot. It provides a modular structure for templates, generated configs, and a secondary TUI manager for agent building.

## Changes Made

- **Change:** Merged pull request to add Claude GitHub workflows.
- **Added:** GitHub Actions workflows for Claude.
- **Removed:** None.

## Affected User Stories

- As a team, I want CI/CD integration with Claude for automation.

## Directory Tree

```
.
|-- .gitignore
|-- AGENTS.md
|-- llm.py
|-- requirements.txt
|-- servers/
|-- generated/
|-- selections/
|-- .github/
|   `-- workflows/
`-- __pycache__/
```

## Tags

#merge #ci-cd #claude
""",

    "Add claude GitHub actions 1763354300262": """# Project Description

This is a Python-based CLI tool for managing Large Language Model (LLM) configurations, including MCP (Model Context Protocol) server setups for various LLMs like Claude, Gemini, and GitHub Copilot. It provides a modular structure for templates, generated configs, and a secondary TUI manager for agent building.

## Changes Made

- **Change:** Merged pull request to add Claude GitHub actions.
- **Added:** Specific GitHub Actions for Claude with timestamp.
- **Removed:** None.

## Affected User Stories

- As a team, I want versioned CI/CD workflows for Claude.

## Directory Tree

```
.
|-- .gitignore
|-- AGENTS.md
|-- llm.py
|-- requirements.txt
|-- servers/
|-- generated/
|-- selections/
|-- .github/
|   `-- workflows/
`-- __pycache__/
```

## Tags

#merge #ci-cd #claude
""",

    "Fix security vulnerabilities and configuration issues": """# Project Description

This is a Python-based CLI tool for managing Large Language Model (LLM) configurations, including MCP (Model Context Protocol) server setups for various LLMs like Claude, Gemini, and GitHub Copilot. It provides a modular structure for templates, generated configs, and a secondary TUI manager for agent building.

## Changes Made

- **Change:** Fixed security issues by replacing private IPs with localhost and corrected package names.
- **Added:** Secure configurations.
- **Removed:** Hardcoded private IPs and incorrect package names.

## Affected User Stories

- As a security-conscious user, I want configurations free of exposed private information.

## Directory Tree

```
.
|-- .gitignore
|-- AGENTS.md
|-- llm.py
|-- requirements.txt
|-- servers/
|-- generated/
|-- selections/
`-- __pycache__/
```

## Tags

#security #bugfix #config
""",

    "Initial plan": """# Project Description

This is a Python-based CLI tool for managing Large Language Model (LLM) configurations, including MCP (Model Context Protocol) server setups for various LLMs like Claude, Gemini, and GitHub Copilot. It provides a modular structure for templates, generated configs, and a secondary TUI manager for agent building.

## Changes Made

- **Change:** Added initial planning document.
- **Added:** Planning file or notes.
- **Removed:** None.

## Affected User Stories

- As a planner, I want to document initial project plans.

## Directory Tree

```
.
|-- .gitignore
|-- AGENTS.md
|-- llm.py
|-- requirements.txt
|-- servers/
|-- generated/
|-- selections/
`-- __pycache__/
```

## Tags

#planning #docs
""",

    "Fix cross-platform compatibility in all JSON templates": """# Project Description

This is a Python-based CLI tool for managing Large Language Model (LLM) configurations, including MCP (Model Context Protocol) server setups for various LLMs like Claude, Gemini, and GitHub Copilot. It provides a modular structure for templates, generated configs, and a secondary TUI manager for agent building.

## Changes Made

- **Change:** Replaced Windows-specific commands with cross-platform equivalents in JSON templates.
- **Added:** npx commands for better portability.
- **Removed:** cmd /c patterns.

## Affected User Stories

- As a cross-platform user, I want the tool to work on any OS.

## Directory Tree

```
.
|-- .gitignore
|-- AGENTS.md
|-- llm.py
|-- requirements.txt
|-- servers/
|-- generated/
|-- selections/
`-- __pycache__/
```

## Tags

#cross-platform #fix #json-templates
""",

    "Fix cross-platform compatibility: Replace cmd with npx in JSON templates": """# Project Description

This is a Python-based CLI tool for managing Large Language Model (LLM) configurations, including MCP (Model Context Protocol) server setups for various LLMs like Claude, Gemini, and GitHub Copilot. It provides a modular structure for templates, generated configs, and a secondary TUI manager for agent building.

## Changes Made

- **Change:** Updated JSON templates to use npx instead of cmd for cross-platform support.
- **Added:** Portable command structures.
- **Removed:** Windows-specific cmd calls.

## Affected User Stories

- As a user on non-Windows systems, I want the configurations to work without modification.

## Directory Tree

```
.
|-- .gitignore
|-- AGENTS.md
|-- llm.py
|-- requirements.txt
|-- servers/
|-- generated/
|-- selections/
`-- __pycache__/
```

## Tags

#cross-platform #fix #templates
""",

    "Fix Windows-specific command patterns in JSON MCP server templates": """# Project Description

This is a Python-based CLI tool for managing Large Language Model (LLM) configurations, including MCP (Model Context Protocol) server setups for various LLMs like Claude, Gemini, and GitHub Copilot. It provides a modular structure for templates, generated configs, and a secondary TUI manager for agent building.

## Changes Made

- **Change:** Merged pull request to fix Windows commands in templates.
- **Added:** Cross-platform commands.
- **Removed:** Windows-specific patterns.

## Affected User Stories

- As a Windows user, I want consistent command handling.

## Directory Tree

```
.
|-- .gitignore
|-- AGENTS.md
|-- llm.py
|-- requirements.txt
|-- servers/
|-- generated/
|-- selections/
`-- __pycache__/
```

## Tags

#merge #windows #fix
""",

    "Fix MCP server configurations for all LLMs and update metadata": """# Project Description

This is a Python-based CLI tool for managing Large Language Model (LLM) configurations, including MCP (Model Context Protocol) server setups for various LLMs like Claude, Gemini, and GitHub Copilot. It provides a modular structure for templates, generated configs, and a secondary TUI manager for agent building.

## Changes Made

- **Change:** Fixed MCP server configs for security, cross-platform, and format compliance.
- **Added:** Environment variable placeholders, cross-platform commands, correct types.
- **Removed:** Hardcoded credentials, Windows-specific commands.

## Affected User Stories

- As a user, I want secure and compliant configurations for all LLMs.

## Directory Tree

```
.
|-- .gitignore
|-- AGENTS.md
|-- llm.py
|-- requirements.txt
|-- servers/
|-- generated/
|-- selections/
`-- __pycache__/
```

## Tags

#security #cross-platform #mcp #config
""",

    "Spawn agents to verify MCP servers": """# Project Description

This is a Python-based CLI tool for managing Large Language Model (LLM) configurations, including MCP (Model Context Protocol) server setups for various LLMs like Claude, Gemini, and GitHub Copilot. It provides a modular structure for templates, generated configs, and a secondary TUI manager for agent building.

## Changes Made

- **Change:** Merged pull request to add agent verification for MCP servers.
- **Added:** Verification agents.
- **Removed:** None.

## Affected User Stories

- As a developer, I want automated verification of MCP server configurations.

## Directory Tree

```
.
|-- .gitignore
|-- AGENTS.md
|-- llm.py
|-- requirements.txt
|-- servers/
|-- generated/
|-- selections/
`-- __pycache__/
```

## Tags

#merge #verification #mcp
""",

    "wip: save all unstaged changes before rebase (2025-12-05T02:08:20.729Z)": """# Project Description

This is a Python-based CLI tool for managing Large Language Model (LLM) configurations, including MCP (Model Context Protocol) server setups for various LLMs like Claude, Gemini, and GitHub Copilot. It provides a modular structure for templates, generated configs, and a secondary TUI manager for agent building.

## Changes Made

- **Change:** Saved unstaged changes before rebasing.
- **Added:** Staged changes.
- **Removed:** None.

## Affected User Stories

- As a developer, I want to preserve work during rebases.

## Directory Tree

```
.
|-- .gitignore
|-- AGENTS.md
|-- llm.py
|-- requirements.txt
|-- servers/
|-- generated/
|-- selections/
`-- __pycache__/
```

## Tags

#wip #rebase #staging
""",

    "Add colorful centered UI and WSL support for Codex": """# Project Description

This is a Python-based CLI tool for managing Large Language Model (LLM) configurations, including MCP (Model Context Protocol) server setups for various LLMs like Claude, Gemini, and GitHub Copilot. It provides a modular structure for templates, generated configs, and a secondary TUI manager for agent building.

## Changes Made

- **Change:** Added colorful UI and WSL support for Codex.
- **Added:** Colorama-based UI, centered text, WSL launching.
- **Removed:** None.

## Affected User Stories

- As a user, I want an attractive and functional UI for the CLI.

## Directory Tree

```
.
|-- .gitignore
|-- AGENTS.md
|-- llm.py
|-- requirements.txt
|-- servers/
|-- generated/
|-- selections/
`-- __pycache__/
```

## Tags

#ui #wsl #codex #colorful
""",

    "Fix MCP server configuration issues across all templates": """# Project Description

This is a Python-based CLI tool for managing Large Language Model (LLM) configurations, including MCP (Model Context Protocol) server setups for various LLMs like Claude, Gemini, and GitHub Copilot. It provides a modular structure for templates, generated configs, and a secondary TUI manager for agent building.

## Changes Made

- **Change:** Fixed MCP server issues in all templates.
- **Added:** Missing type fields, corrected keys.
- **Removed:** Incorrect configurations.

## Affected User Stories

- As a user, I want valid MCP server configurations.

## Directory Tree

```
.
|-- .gitignore
|-- AGENTS.md
|-- llm.py
|-- requirements.txt
|-- servers/
|-- generated/
|-- selections/
`-- __pycache__/
```

## Tags

#mcp #fix #templates
"""
}

input_text = sys.stdin.read()
lines = input_text.strip().split('\n')
subject = lines[0].strip()
if subject.startswith("Merge pull request"):
    title = lines[2].strip() if len(lines) > 2 else subject
else:
    title = subject

if title in mapping:
    print(mapping[title])
else:
    print(input_text)