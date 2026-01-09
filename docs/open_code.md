# OpenCode Complete Reference

OpenCode is an open-source AI coding agent that helps you write code in your terminal, IDE, or desktop app. This comprehensive guide covers all commands, session management, parallel sessions, and headless operation.

## Table of Contents
- [Installation](#installation)
- [Quick Start](#quick-start)
- [CLI Commands](#cli-commands)
- [TUI Commands](#tui-commands)
- [Session Management](#session-management)
- [Parallel Sessions](#parallel-sessions)
- [Headless Operation](#headless-operation)
- [Configuration](#configuration)
- [Environment Variables](#environment-variables)
- [Server API](#server-api)
- [Usage Examples](#usage-examples)

## Installation

### Install Script (Recommended)
```bash
curl -fsSL https://opencode.ai/install | bash
```

### Package Managers
```bash
# npm
npm install -g opencode-ai

# bun
bun install -g opencode-ai

# Homebrew (macOS/Linux)
brew install opencode

# Chocolatey (Windows)
choco install opencode

# Scoop (Windows)
scoop bucket add extras
scoop install extras/opencode
```

### Binary Download
Download from [GitHub Releases](https://github.com/sst/opencode/releases)

## Quick Start

```bash
# Navigate to your project
cd /path/to/project

# Start OpenCode TUI
opencode

# Initialize project (creates AGENTS.md)
/init

# Or run non-interactively
opencode run "Explain this codebase"
```

## CLI Commands

### Main Commands

#### `opencode` (TUI Mode)
Start the terminal user interface.
```bash
opencode [project_path]
```

**Flags:**
- `--continue`, `-c`: Continue the last session
- `--session`, `-s`: Session ID to continue
- `--prompt`, `-p`: Prompt to use
- `--model`, `-m`: Model to use (provider/model)
- `--agent`: Agent to use
- `--port`: Port to listen on
- `--hostname`: Hostname to listen on

#### `opencode run` (Non-interactive)
Execute a prompt without TUI.
```bash
opencode run "Explain async/await in JavaScript"
```

**Flags:**
- `--command`: Command to run
- `--continue`, `-c`: Continue last session
- `--session`, `-s`: Session ID to continue
- `--share`: Share the session
- `--model`, `-m`: Model to use
- `--agent`: Agent to use
- `--file`, `-f`: File(s) to attach
- `--format`: Output format (default/json)
- `--title`: Title for the session
- `--attach`: Attach to running server (http://localhost:4096)
- `--port`: Port for local server

#### `opencode serve` (Headless Server)
Start HTTP API server.
```bash
opencode serve [--port 4096] [--hostname 127.0.0.1]
```

#### `opencode auth` (Authentication)
Manage provider credentials.
```bash
# Login to providers
opencode auth login

# List authenticated providers
opencode auth list

# Logout from provider
opencode auth logout
```

#### `opencode models` (Model Listing)
List available models.
```bash
# List all models
opencode models

# List models for specific provider
opencode models anthropic

# Refresh model cache
opencode models --refresh

# Verbose output with costs
opencode models --verbose
```

#### `opencode agent` (Agent Management)
Manage custom agents.
```bash
# Create new agent
opencode agent create
```

#### `opencode github` (GitHub Integration)
Manage GitHub agent.
```bash
# Install GitHub agent
opencode github install

# Run GitHub agent (for GitHub Actions)
opencode github run --event push --token $TOKEN
```

#### `opencode upgrade` (Updates)
Update OpenCode.
```bash
# Update to latest
opencode upgrade

# Update to specific version
opencode upgrade v0.1.48

# Specify installation method
opencode upgrade --method npm
```

### Global Flags
- `--help`, `-h`: Display help
- `--version`, `-v`: Print version
- `--print-logs`: Print logs to stderr
- `--log-level`: Log level (DEBUG, INFO, WARN, ERROR)

## TUI Commands

Type `/` followed by command name in the TUI. Most commands have keybinds with `ctrl+x` as leader.

### Core Commands

#### `/help`
Show help dialog.
**Keybind:** `ctrl+x h`

#### `/new` or `/clear`
Start new session.
**Keybind:** `ctrl+x n`

#### `/sessions` or `/resume` or `/continue`
List and switch between sessions.
**Keybind:** `ctrl+x l`

#### `/exit` or `/quit` or `/q`
Exit OpenCode.
**Keybind:** `ctrl+x q`

#### `/undo`
Undo last message and file changes.
**Keybind:** `ctrl+x u`

#### `/redo`
Redo previously undone message.
**Keybind:** `ctrl+x r`

#### `/share`
Share current session.
**Keybind:** `ctrl+x s`

#### `/unshare`
Unshare current session.

#### `/compact` or `/summarize`
Compact current session.
**Keybind:** `ctrl+x c`

#### `/details`
Toggle tool execution details.
**Keybind:** `ctrl+x d`

#### `/editor`
Open external editor for composing messages.
**Keybind:** `ctrl+x e`

#### `/export`
Export conversation to Markdown.
**Keybind:** `ctrl+x x`

#### `/init`
Create/update AGENTS.md file.
**Keybind:** `ctrl+x i`

#### `/models`
List available models.
**Keybind:** `ctrl+x m`

#### `/themes`
List available themes.
**Keybind:** `ctrl+x t`

#### `/connect`
Add provider and configure API keys.

### TUI Features

#### File References
Use `@` to reference files:
```
How is auth handled in @packages/functions/src/api/index.ts?
```

#### Bash Commands
Start message with `!` to run shell commands:
```
!ls -la
```

## Session Management

### Creating New Sessions

#### Method 1: TUI Command
```
/new
```

#### Method 2: CLI Flag
```bash
opencode --session "new-session-name"
```

#### Method 3: Non-interactive
```bash
opencode run --title "Bug Fix Session" "Fix the login issue"
```

### Session Persistence
- Sessions are automatically saved
- Can be resumed using `/sessions` command
- Each session has unique ID and title
- Conversation history is preserved

### Session Switching
```
/sessions
# Shows list of sessions
# Use arrow keys to select
# Press enter to switch
```

### Session Metadata
- **Session ID**: Unique identifier
- **Title**: Derived from first prompt or explicitly set
- **Created**: Timestamp
- **Message Count**: Number of exchanges
- **Model**: LLM used in session

## Parallel Sessions

OpenCode supports multiple concurrent sessions on the same project.

### Method 1: Multiple TUI Instances
```bash
# Terminal 1
opencode --session session-1

# Terminal 2  
opencode --session session-2
```

### Method 2: Server + Multiple Clients
```bash
# Start headless server
opencode serve --port 4096

# Terminal 1: Attach to server
opencode run --attach http://localhost:4096 --session session-1 "Task 1"

# Terminal 2: Attach to same server
opencode run --attach http://localhost:4096 --session session-2 "Task 2"
```

### Method 3: Background Server
```bash
# Start server in background
opencode serve --port 4096 &

# Create multiple sessions
opencode run --attach http://localhost:4096 --session "feature-a" "Implement feature A"
opencode run --attach http://localhost:4096 --session "feature-b" "Implement feature B"
opencode run --attach http://localhost:4096 --session "bug-fix" "Fix critical bug"
```

### Parallel Session Benefits
- **Isolation**: Each session has independent context
- **Concurrent Work**: Multiple developers can work simultaneously
- **Task Separation**: Different features in separate sessions
- **Resource Sharing**: Same MCP servers and tools

## Headless Operation

### Server Mode
Start HTTP API server for programmatic access:
```bash
opencode serve --port 4096 --hostname 0.0.0.0
```

### Non-interactive Mode
Execute tasks without TUI:
```bash
# Simple prompt
opencode run "Refactor this function"

# With files
opencode run --file src/main.ts "Review this code"

# With specific model
opencode run --model anthropic/claude-sonnet "Explain this"

# JSON output for scripting
opencode run --format json "List all functions" > output.json
```

### Batch Processing
```bash
#!/bin/bash
# Process multiple files
for file in src/*.ts; do
    opencode run --file "$file" --title "Review $file" "Review this TypeScript file"
done
```

### Automation Examples
```bash
# Code review
opencode run --agent code-reviewer --file pr.patch "Review this PR"

# Documentation generation
opencode run --title "Generate API docs" "Generate API documentation for src/api/"

# Test generation
opencode run --file src/utils.ts "Write unit tests for these utilities"
```

## Configuration

### Config File Locations
1. **Global**: `~/.config/opencode/opencode.json`
2. **Project**: `./opencode.json` (in project root)
3. **Custom**: `OPENCODE_CONFIG` environment variable
4. **Directory**: `OPENCODE_CONFIG_DIR` environment variable

### Basic Config
```json
{
  "$schema": "https://opencode.ai/config.json",
  "model": "anthropic/claude-sonnet-4-5",
  "theme": "opencode",
  "autoupdate": true,
  "share": "manual"
}
```

### Provider Configuration
```json
{
  "provider": {
    "anthropic": {
      "models": {},
      "options": {
        "apiKey": "{env:ANTHROPIC_API_KEY}"
      }
    },
    "openai": {
      "models": {},
      "options": {
        "apiKey": "{env:OPENAI_API_KEY}"
      }
    }
  }
}
```

### Tool Permissions
```json
{
  "tools": {
    "write": true,
    "edit": true,
    "bash": true,
    "read": true
  },
  "permission": {
    "bash": "ask",
    "edit": "ask"
  }
}
```

### Custom Agents
```json
{
  "agent": {
    "code-reviewer": {
      "description": "Reviews code for best practices",
      "model": "anthropic/claude-sonnet-4-5",
      "prompt": "You are a code reviewer. Focus on security, performance, and maintainability.",
      "tools": {
        "write": false,
        "edit": false
      }
    }
  }
}
```

### Custom Commands
```json
{
  "command": {
    "test": {
      "template": "Run the full test suite with coverage report.",
      "description": "Run tests with coverage",
      "agent": "build"
    },
    "component": {
      "template": "Create a new React component named $ARGUMENTS with TypeScript.",
      "description": "Create new component"
    }
  }
}
```

## Environment Variables

### Core Variables
- `OPENCODE_CONFIG`: Path to custom config file
- `OPENCODE_CONFIG_DIR`: Path to custom config directory
- `OPENCODE_CONFIG_CONTENT`: Inline JSON config
- `OPENCODE_AUTO_SHARE`: Automatically share sessions (boolean)
- `OPENCODE_CLIENT`: Client identifier (defaults to "cli")

### Feature Flags
- `OPENCODE_DISABLE_AUTOUPDATE`: Disable automatic updates
- `OPENCODE_DISABLE_PRUNE`: Disable data pruning
- `OPENCODE_DISABLE_TERMINAL_TITLE`: Disable title updates
- `OPENCODE_DISABLE_DEFAULT_PLUGINS`: Disable default plugins
- `OPENCODE_DISABLE_LSP_DOWNLOAD`: Disable LSP downloads
- `OPENCODE_ENABLE_EXPERIMENTAL_MODELS`: Enable experimental models
- `OPENCODE_ENABLE_EXA`: Enable Exa web search

### Experimental Features
- `OPENCODE_EXPERIMENTAL`: Enable all experimental features
- `OPENCODE_EXPERIMENTAL_ICON_DISCOVERY`: Enable icon discovery
- `OPENCODE_EXPERIMENTAL_DISABLE_COPY_ON_SELECT`: Disable copy on select
- `OPENCODE_EXPERIMENTAL_BASH_MAX_OUTPUT_LENGTH`: Max bash output length
- `OPENCODE_EXPERIMENTAL_BASH_DEFAULT_TIMEOUT_MS`: Bash timeout in ms
- `OPENCODE_EXPERIMENTAL_OUTPUT_TOKEN_MAX`: Max output tokens
- `OPENCODE_EXPERIMENTAL_FILEWATCHER`: Enable file watcher
- `OPENCODE_EXPERIMENTAL_OXFMT`: Enable oxfmt formatter

### Platform Specific
- `OPENCODE_GIT_BASH_PATH`: Git Bash path on Windows

## Server API

### Starting Server
```bash
opencode serve --port 4096 --hostname 127.0.0.1
```

### Key API Endpoints

#### Sessions
```bash
# List sessions
GET /session

# Create session
POST /session
{
  "parentID": "optional-parent",
  "title": "Session Title"
}

# Get session
GET /session/:id

# Send message
POST /session/:id/message
{
  "messageID": "optional",
  "model": "anthropic/claude-sonnet-4-5",
  "agent": "default",
  "parts": [{"type": "text", "text": "Hello"}]
}

# Delete session
DELETE /session/:id
```

#### Files
```bash
# List files
GET /file?path=/path/to/dir

# Read file
GET /file/content?path=/path/to/file

# Search files
GET /find/file?query=pattern

# Search content
GET /find?pattern=search_term
```

#### Models & Providers
```bash
# List providers
GET /provider

# List models
GET /models

# Get config
GET /config
```

#### Tools
```bash
# Run shell command
POST /session/:id/shell
{
  "command": "ls -la",
  "agent": "default"
}

# Execute slash command
POST /session/:id/command
{
  "command": "help",
  "arguments": []
}
```

### Server Events
```bash
# Server-sent events
GET /event

# Global events
GET /global/event
```

### OpenAPI Documentation
Access at: `http://localhost:4096/doc`

## Usage Examples

### Basic Workflows

#### Code Review Session
```bash
# Start with specific agent
opencode run --agent code-reviewer --file src/main.ts "Review this code"

# Or in TUI
/agent code-reviewer
@src/main.ts
Please review this file for security and performance issues.
```

#### Feature Development
```bash
# Create new session for feature
opencode run --session "user-auth" --title "User Authentication" "
Implement user authentication with JWT tokens. Include:
1. Login endpoint
2. Registration endpoint  
3. Token validation middleware
4. Password reset functionality
"

# Continue in same session
opencode run --session "user-auth" "Add email verification"
```

#### Bug Fixing
```bash
# Attach to server for faster startup
opencode serve &
opencode run --attach http://localhost:4096 --session "bug-fix" "
Fix the memory leak in the image processing module.
Look at src/image/processor.ts
"
```

### Scripting Examples

#### Automated Code Review
```bash
#!/bin/bash
# review-pr.sh
PR_FILE=$1

opencode run \
  --agent code-reviewer \
  --file "$PR_FILE" \
  --format json \
  --title "PR Review" \
  "Review this pull request for security, performance, and maintainability issues." \
  > review-results.json

echo "Review complete. Results saved to review-results.json"
```

#### Documentation Generation
```bash
#!/bin/bash
# generate-docs.sh

opencode run \
  --title "API Documentation" \
  --format json \
  "Generate comprehensive API documentation for all endpoints in src/api/. Include request/response examples, error codes, and authentication requirements." \
  > api-docs.json

# Convert to Markdown
opencode run \
  --file api-docs.json \
  --title "Convert to Markdown" \
  "Convert this JSON documentation to well-formatted Markdown" \
  > README.md
```

#### Test Generation
```bash
#!/bin/bash
# generate-tests.sh

for file in src/**/*.ts; do
    if [[ $file != *test* ]]; then
        echo "Generating tests for $file"
        opencode run \
            --file "$file" \
            --title "Tests for $(basename $file)" \
            "Generate comprehensive unit tests for this TypeScript file using Jest. Include edge cases and error handling." \
            > "test/$(basename $file .ts).test.ts"
    fi
done
```

### Parallel Session Examples

#### Multi-Feature Development
```bash
#!/bin/bash
# parallel-development.sh

# Start server
opencode serve --port 4096 &
SERVER_PID=$!
sleep 2

# Create parallel sessions
opencode run --attach http://localhost:4096 --session "auth" "Implement JWT authentication" &
opencode run --attach http://localhost:4096 --session "database" "Set up PostgreSQL database schema" &
opencode run --attach http://localhost:4096 --session "frontend" "Create React components for auth UI" &

# Wait for all sessions
wait

# Clean up
kill $SERVER_PID
```

#### Code Review Pipeline
```bash
#!/bin/bash
# parallel-review.sh

opencode serve --port 4096 &
SERVER_PID=$!
sleep 2

# Parallel reviews
opencode run --attach http://localhost:4096 --agent security --session "security-review" --file pr.patch "Review for security vulnerabilities" &
opencode run --attach http://localhost:4096 --agent performance --session "performance-review" --file pr.patch "Review for performance issues" &
opencode run --attach http://localhost:4096 --agent code-reviewer --session "code-review" --file pr.patch "Review for code quality" &

wait
kill $SERVER_PID
```

### Headless Automation

#### CI/CD Integration
```bash
#!/bin/bash
# ci-check.sh

# Code quality checks
opencode run --agent code-reviewer --format json --file . "Review entire codebase for quality issues" > quality-report.json

# Security scan
opencode run --agent security --format json "Scan for security vulnerabilities" > security-report.json

# Performance analysis
opencode run --agent performance --format json "Analyze performance bottlenecks" > performance-report.json

# Check results
if jq -e '.issues | length > 0' quality-report.json; then
    echo "Code quality issues found"
    exit 1
fi

if jq -e '.vulnerabilities | length > 0' security-report.json; then
    echo "Security vulnerabilities found"
    exit 1
fi

echo "All checks passed"
```

#### Documentation Maintenance
```bash
#!/bin/bash
# update-docs.sh

# Update API docs
opencode run --title "Update API Docs" "Regenerate API documentation for current codebase" > docs/api.md

# Update README
opencode run --file README.md --title "Update README" "Update the README with latest project information and setup instructions" > README-new.md

mv README-new.md README.md
```

### Advanced Configuration

#### Multi-Provider Setup
```json
{
  "model": "anthropic/claude-sonnet-4-5",
  "small_model": "anthropic/claude-haiku-4-5",
  "provider": {
    "anthropic": {
      "options": {
        "apiKey": "{env:ANTHROPIC_API_KEY}"
      }
    },
    "openai": {
      "options": {
        "apiKey": "{env:OPENAI_API_KEY}"
      }
    },
    "together": {
      "options": {
        "apiKey": "{env:TOGETHER_API_KEY}"
      }
    }
  },
  "enabled_providers": ["anthropic", "openai"],
  "disabled_providers": ["gemini"]
}
```

#### Enterprise Security
```json
{
  "permission": {
    "write": "ask",
    "edit": "ask", 
    "bash": "ask",
    "read": "allow"
  },
  "share": "disabled",
  "tools": {
    "webfetch": false,
    "websearch": false
  },
  "autoupdate": false,
  "disabled_providers": ["openai", "anthropic"],
  "enabled_providers": ["local-llama"]
}
```

#### Development Environment
```json
{
  "model": "anthropic/claude-sonnet-4-5",
  "theme": "github-dark",
  "autoupdate": "notify",
  "share": "auto",
  "tui": {
    "scroll_speed": 2,
    "scroll_acceleration": {
      "enabled": true
    }
  },
  "formatter": {
    "prettier": {
      "disabled": false
    }
  },
  "mcp": {
    "filesystem": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-filesystem", "/path/to/project"]
    }
  }
}
```

## Troubleshooting

### Common Issues

#### Server Won't Start
```bash
# Check port availability
netstat -an | grep 4096

# Use different port
opencode serve --port 5000
```

#### Session Not Found
```bash
# List all sessions
opencode run --command sessions

# Check session status
curl http://localhost:4096/session/status
```

#### Provider Authentication
```bash
# Check configured providers
opencode auth list

# Re-authenticate
opencode auth login

# Check environment variables
env | grep -E "(ANTHROPIC|OPENAI|GEMINI)"
```

#### Performance Issues
```bash
# Use smaller model for quick tasks
opencode run --model anthropic/claude-haiku "Quick question"

# Attach to server to avoid cold starts
opencode serve &
opencode run --attach http://localhost:4096 "Your prompt"
```

### Debug Mode
```bash
# Enable debug logging
opencode --log-level DEBUG run "Test prompt"

# Print logs to stderr
opencode --print-logs run "Test prompt"
```

## Tips and Best Practices

### Session Management
- Use descriptive session titles
- Create separate sessions for different tasks
- Use `/sessions` to navigate between sessions
- Export important sessions with `/export`

### Performance
- Use server mode for repeated operations
- Choose appropriate models for tasks
- Limit file attachments in prompts
- Use compact mode for long sessions

### Security
- Review permissions in production
- Disable sharing for sensitive projects
- Use environment variables for API keys
- Regularly update OpenCode

### Collaboration
- Share sessions for code reviews
- Use consistent agent configurations
- Document custom commands
- Version control configuration files

---

This comprehensive reference covers all aspects of OpenCode for headless operation, parallel sessions, and automation. For the most up-to-date information, visit the [official OpenCode documentation](https://opencode.ai/docs/).