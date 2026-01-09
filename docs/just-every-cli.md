# Code CLI (just-every) Complete Reference

Code is a fast, local coding agent for your terminal, a community-driven fork of `openai/codex` focused on developer ergonomics with features like browser integration, multi-agents, theming, and reasoning control.

## Table of Contents
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Core Commands](#core-commands)
- [Configuration](#configuration)
- [Parallel Sessions](#parallel-sessions)
- [Advanced Features](#advanced-features)
- [Usage Examples](#usage-examples)

## Installation

### NPM Installation
```bash
npm install -g @just-every/code
code
```

### Development Setup
```bash
git clone https://github.com/just-every/code.git
cd code
npm install
./build-fast.sh
./codex-rs/target/dev-fast/code
```

### Homebrew Installation
```bash
brew tap just-every/tap
brew install code
```

## Quick Start

### Basic Usage
```bash
# Start interactive session
code

# Direct prompt
code "explain this codebase to me"

# Full auto mode (create, run, commit)
code --full-auto "create the fanciest todo-list app"
```

### First Time Setup
```bash
# Install optional AI tools
npm install -g @anthropic-ai/claude-code @google/gemini-cli

# Verify installations
claude "Just checking you're working!"
gemini -i "Just checking you're working!"
```

## Core Commands

### Interactive Mode
```bash
code
```
Starts the interactive terminal interface where you can chat with the AI agent.

### Direct Prompt Mode
```bash
code "your prompt here"
```
Execute a single prompt without entering interactive mode.

### Full Auto Mode
```bash
code --full-auto "create a todo app"
```
Automatically creates, runs, and commits code changes based on your prompt.

### MCP Server Mode
```bash
code mcp | your_mcp_client
```
Starts Code as an MCP (Model Context Protocol) server that can be connected to MCP clients.

### MCP Configuration
Create `~/.codex/mcp.json` to configure MCP servers:

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-filesystem", "/workspace"],
      "env": {}
    },
    "git": {
      "command": "uvx",
      "args": ["mcp-server-git", "--repository", "/workspace"],
      "env": {}
    },
    "database": {
      "command": "uvx",
      "args": ["mcp-server-sqlite", "--db-path", "/data/app.db"],
      "env": {}
    }
  }
}
```

### MCP Tool Usage
```bash
# Use MCP tools in interactive mode
code
> /mcp filesystem read_file src/main.js
> /mcp git get_status
> /mcp database query "SELECT * FROM users"
```

## Configuration

### Environment Variables
```bash
# Core settings
export CODEX_MODE=code
export CODEX_TELEMETRY=true
export CODEX_THEME=dark

# Provider configuration
export CODEX_PROVIDER_TYPE=code
export CODEX_TOKEN=your-api-token
export CODEX_MODEL=x-ai/grok-code-fast-1
export CODEX_ORGANIZATION_ID=org-123

# Auto-approval settings
export CODEX_AUTO_APPROVAL_ENABLED=true
export CODEX_AUTO_APPROVAL_READ_ENABLED=true
export CODEX_AUTO_APPROVAL_WRITE_ENABLED=true
export CODEX_AUTO_APPROVAL_BROWSER_ENABLED=false
export CODEX_AUTO_APPROVAL_EXECUTE_ALLOWED="ls,cat,echo,pwd,npm,yarn,pnpm"
export CODEX_AUTO_APPROVAL_EXECUTE_DENIED="rm -rf,sudo"
```

### Project Configuration
Create a `.codex` directory in your project root with:
- `AGENTS.md` - Repository-specific instructions
- Custom commands in `commands/` subdirectory
- Agent configurations in `agents/` subdirectory

### Global Configuration
Global settings are stored in `~/.codex/`:
- `AGENTS.md` - Global working agreements
- `commands/` - Global custom commands
- `agents/` - Global agent configurations

## Parallel Sessions

### Multiple Terminal Sessions
Code supports running multiple independent sessions simultaneously:

```bash
# Terminal 1: Feature development
code --session feature-auth

# Terminal 2: Bug fixes
code --session bug-fixes

# Terminal 3: Documentation
code --session docs-update
```

### MCP Server Parallelism
```bash
# Start MCP server
code mcp | tee >(client1) >(client2) >(client3)
```

### Background Processing
```bash
# Run in background
code --full-auto "implement user auth" &

# Continue with other work
code --session "ui-improvements"
```

### Session Isolation
Each session maintains:
- Independent conversation history
- Separate file context
- Isolated tool permissions
- Individual model configurations

## Advanced Features

### Multi-Agent Support
Code supports multiple specialized agents:

```bash
# Switch agents during session
/agent code-reviewer
/agent performance-optimizer
/agent security-auditor
```

### Browser Integration
```bash
# Open browser for testing
/browse open http://localhost:3000

# Take screenshots
/browse screenshot login-page.png
```

### Custom Commands
Create reusable commands in `~/.codex/commands/`:

```markdown
---
description: Run full test suite with coverage
argument-hint: [component]
---

Run comprehensive tests for $1

1. Unit tests: `npm test -- --testPathPattern=$1`
2. Integration tests: `npm run test:integration`
3. E2E tests: `npm run test:e2e`
4. Coverage report: `npm run coverage`

Generate summary report.
```

### Tool Permissions
Configure tool access levels:
```toml
[permissions]
read = "allow"
write = "ask"
bash = "ask"
browser = "deny"
```

### Theming and UI
```bash
# Available themes
/themes

# Set theme
/theme dark-modern
/theme light-minimal
```

## Usage Examples

### Development Workflow
```bash
# 1. Start new feature session
code --session "user-dashboard"

# In session:
/init  # Analyze codebase
"Create a user dashboard component with real-time data"

# 2. Parallel testing session
code --session "dashboard-tests"

# In session:
"Write comprehensive tests for the dashboard component"

# 3. Code review session
code --session "dashboard-review"

# In session:
/agent code-reviewer
"Review the dashboard implementation for best practices"
```

### Automated Workflows
```bash
# Full auto implementation
code --full-auto "add dark mode toggle to settings"

# Background processing
code --full-auto "optimize database queries" &
code --full-auto "update API documentation" &
wait  # Wait for completion
```

### MCP Integration
```bash
# Start server for multiple clients
code mcp | tee >(web-client) >(mobile-client) >(api-client)

# Each client can work independently
# Web client: "Update React components"
# Mobile client: "Update React Native components"
# API client: "Update backend APIs"
```

### Custom Command Examples
```bash
# Create deployment command
echo '---
description: Deploy to staging
argument-hint: [version]
---
Deploy version $1 to staging environment
1. Build: npm run build
2. Test: npm run test:staging
3. Deploy: kubectl apply -f k8s/staging/
4. Verify: curl https://staging-api.example.com/health
' > ~/.codex/commands/deploy.md

# Use command
/deploy v1.2.3
```

### Parallel Feature Development
```bash
#!/bin/bash
# parallel-features.sh

# Start three parallel sessions
code --session "auth-feature" --full-auto "implement JWT authentication" &
code --session "ui-redesign" --full-auto "redesign user interface" &
code --session "api-optimization" --full-auto "optimize API performance" &

# Wait for all to complete
wait

# Review session
code --session "integration-review"
# In session: "Review all implemented features for integration"
```

### CI/CD Integration
```bash
#!/bin/bash
# ci-review.sh

# Automated code review
code --agent code-reviewer --format json "Review recent changes" > review.json

# Security audit
code --agent security --format json "Audit for vulnerabilities" > security.json

# Performance analysis
code --agent performance --format json "Analyze performance bottlenecks" > perf.json

# Check results
if jq -e '.issues | length > 0' review.json; then
    echo "Code review issues found"
    exit 1
fi
```

## Parallelism Features

### Session-Based Parallelism
- **Multiple Sessions**: Run independent conversations simultaneously
- **Isolated Contexts**: Each session maintains separate state and history
- **Resource Sharing**: Share MCP servers and tools across sessions
- **Concurrent Execution**: Background processing with `&` operator

### MCP Server Parallelism
- **Multi-Client Support**: Single server serving multiple clients
- **Tool Distribution**: Shared tool access across all connected clients
- **State Synchronization**: Optional state sharing between clients
- **Load Balancing**: Automatic distribution of requests

### Command-Level Parallelism
- **Background Commands**: Execute long-running tasks in background
- **Batch Processing**: Process multiple items concurrently
- **Pipeline Support**: Chain commands with output redirection
- **Job Control**: Monitor and manage background jobs

### Agent Parallelism
- **Multi-Agent Sessions**: Different agents working on same codebase
- **Specialized Workflows**: Code review, testing, documentation in parallel
- **Collaborative Development**: Multiple agents contributing to same feature
- **Quality Assurance**: Parallel validation and testing

## Best Practices

### Session Management
- Use descriptive session names
- Create separate sessions for different tasks
- Regularly clean up old sessions
- Document session purposes

### Performance Optimization
- Use background processing for long tasks
- Configure appropriate model sizes
- Limit file context when possible
- Use MCP servers for shared resources

### Security Considerations
- Review tool permissions regularly
- Use environment variables for sensitive data
- Limit browser access in production
- Audit command executions

### Workflow Integration
- Integrate with existing CI/CD pipelines
- Use custom commands for repetitive tasks
- Leverage multi-agent capabilities
- Automate routine development tasks</content>
<parameter name="filePath">C:\Users\matt\Dropbox\projects\LLM\docs\just-every-cli.md