# Codex CLI Complete Reference

Codex CLI is an open-source coding agent that pairs with you in your terminal to read, modify, and run code, helping you build features faster and understand unfamiliar code.

## Table of Contents
- [Installation](#installation)
- [Configuration](#configuration)
- [Core Commands](#core-commands)
- [Session Management](#session-management)
- [Parallel Sessions](#parallel-sessions)
- [MCP Integration](#mcp-integration)
- [Security](#security)
- [Usage Examples](#usage-examples)

## Installation

### NPM Installation
```bash
npm install -g @openai/codex
codex
```

### Homebrew Installation
```bash
brew install codex
```

### Manual Installation
Download from [GitHub Releases](https://github.com/openai/codex/releases)

## Configuration

### Environment Setup
```bash
# Set OpenAI API key
export OPENAI_API_KEY="your-api-key-here"

# Optional: Set organization
export OPENAI_ORG_ID="your-org-id"
```

### Project Configuration
Create `AGENTS.md` in project root for repository-specific instructions:

```markdown
# AGENTS.md

## Repository expectations

- Run `npm run lint` before opening a pull request.
- Document public utilities in `docs/` when you change behavior.
- Use TypeScript for all new code.
- Follow the existing code style and patterns.
```

### Global Configuration
Create `~/.codex/AGENTS.md` for global working agreements:

```markdown
# ~/.codex/AGENTS.md

## Working agreements

- Always run `npm test` after modifying JavaScript files.
- Prefer `pnpm` when installing dependencies.
- Ask for confirmation before adding new production dependencies.
```

### Custom Commands
Create custom commands in `~/.codex/commands/`:

```markdown
---
description: Prep a branch, commit, and open a draft PR
argument-hint: [FILES=<paths>] [PR_TITLE="<title>"]
---

Create a branch named `dev/<feature_name>` for this work.
If files are specified, stage them first: $FILES.
Commit the staged changes with a clear message.
Open a draft PR on the same branch. Use $PR_TITLE when supplied; otherwise write a concise summary yourself.
```

### Security Configuration
```toml
# managed_config.toml
# Set conservative defaults
approval_policy = "on-request"
sandbox_mode    = "workspace-write"

[sandbox_workspace_write]
network_access = false             # keep network disabled unless explicitly allowed

[otel]
environment = "prod"
exporter = "otlp-http"            # point at your collector
log_user_prompt = false            # keep prompts redacted
```

## Core Commands

### Interactive Mode
```bash
codex
```
Starts the interactive terminal interface.

### Direct Prompt
```bash
codex "explain how this function works"
```

### File References
```bash
codex "review the authentication logic in @src/auth.js"
```

### Shell Commands
```bash
codex
> !ls -la
> !npm test
```

### Custom Commands
```bash
codex
> /custom-command arg1 arg2
```

### Slash Commands
- `/help` - Show help
- `/clear` - Clear conversation
- `/undo` - Undo last action
- `/redo` - Redo undone action
- `/run` - Run a shell command
- `/read` - Read a file
- `/edit` - Edit a file
- `/search` - Search codebase

## Session Management

### Session Creation
```bash
# New session with prompt
codex --prompt "Implement user authentication"

# Continue previous session
codex --continue

# Session with specific model
codex --model gpt-4 "Debug this issue"
```

### Session Context
- **Conversation History**: All interactions preserved
- **File Context**: Referenced files remain accessible
- **Shell State**: Command history and environment
- **Git State**: Repository changes tracked

### Session Persistence
- Sessions automatically saved
- Resume with `--continue` flag
- Context maintained across restarts
- File changes tracked via Git

## Parallel Sessions

### Multiple Terminal Sessions
```bash
# Terminal 1: Feature development
codex --session auth-feature

# Terminal 2: Bug fixes
codex --session bug-fixes

# Terminal 3: Code review
codex --session code-review
```

### Background Processing
```bash
# Run long task in background
codex --full-auto "implement complex feature" &

# Continue with other work
codex --session "documentation"
```

### Session Isolation
Each session maintains:
- Independent conversation history
- Separate file context
- Isolated tool permissions
- Individual model configurations

### Concurrent Execution
```bash
#!/bin/bash
# parallel-tasks.sh

# Start multiple sessions
codex --session "api-dev" --prompt "Implement REST API" &
codex --session "ui-dev" --prompt "Create React components" &
codex --session "test-dev" --prompt "Write unit tests" &

# Wait for completion
wait

echo "All tasks completed"
```

## MCP Integration

Codex CLI supports Model Context Protocol (MCP) servers for extended functionality.

### MCP Server Setup
```bash
# Start MCP server mode
codex mcp | your_mcp_client

# Multiple clients
codex mcp | tee >(client1) >(client2) >(client3)
```

### MCP Configuration
Create `.codex/mcp.json` for MCP server configuration:

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
    }
  }
}
```

### MCP Tool Usage
```bash
# Use MCP tools in interactive mode
codex
> /mcp filesystem read_file src/main.js
> /mcp git get_status
```

### Parallel MCP Sessions
```bash
# Start MCP server for multiple sessions
codex mcp | tee >(session1) >(session2) >(session3) &

# Each session can use MCP tools independently
# Session 1: filesystem operations
# Session 2: git operations
# Session 3: custom MCP tools
```

## Security

### Sandbox Modes
- **workspace-write**: Can modify files in workspace
- **workspace-read**: Read-only access to workspace
- **isolated**: No file system access

### Approval Policies
- **auto**: Automatic execution
- **on-request**: Ask for approval before actions
- **never**: Manual execution only

### Tool Permissions
```toml
[permissions]
read = "allow"
write = "ask"
run = "ask"
network = "deny"
```

### Network Access Control
```toml
[sandbox_workspace_write]
network_access = false  # Disable network by default
allowed_domains = ["api.github.com", "registry.npmjs.org"]  # Allow specific domains
```

## Usage Examples

### Development Workflow
```bash
# 1. Start new feature
codex --session "user-auth"
# In session: "Implement JWT authentication with refresh tokens"

# 2. Parallel testing
codex --session "auth-tests"
# In session: "Write comprehensive tests for auth module"

# 3. Documentation
codex --session "auth-docs"
# In session: "Document the authentication API"
```

### Code Review Process
```bash
# Automated review
codex --agent code-reviewer --file src/auth.js "Review for security issues"

# Manual review session
codex --session "security-review"
# In session: "Conduct thorough security audit of authentication system"
```

### Bug Fixing
```bash
# Debug session
codex --session "debug-login"
# In session: "Debug the login failure issue in @src/auth/login.js"

# Fix implementation
codex --session "fix-login"
# In session: "Fix the null pointer exception in login function"
```

### Refactoring Tasks
```bash
# Analysis session
codex --session "refactor-analysis"
# In session: "Analyze codebase for refactoring opportunities"

# Implementation session
codex --session "refactor-impl"
# In session: "Refactor authentication module to use dependency injection"
```

### Parallel Feature Development
```bash
#!/bin/bash
# parallel-features.sh

FEATURES=(
    "Implement user registration API"
    "Create login/logout UI components"
    "Add password reset functionality"
    "Implement user profile management"
)

for feature in "${FEATURES[@]}"; do
    codex --session "$(echo $feature | tr ' ' '-' | tr '[:upper:]' '[:lower:]')" \
          --prompt "$feature" &
done

wait
echo "All features initiated"
```

### CI/CD Integration
```bash
#!/bin/bash
# ci-checks.sh

# Code quality check
codex --format json --prompt "Check code quality and suggest improvements" > quality.json

# Security audit
codex --format json --prompt "Audit for security vulnerabilities" > security.json

# Performance analysis
codex --format json --prompt "Analyze performance bottlenecks" > perf.json

# Check results
if jq -e '.issues | length > 0' quality.json; then
    echo "Quality issues found"
    exit 1
fi

if jq -e '.vulnerabilities | length > 0' security.json; then
    echo "Security issues found"
    exit 1
fi
```

### Custom Command Examples
```bash
# Create deployment command
mkdir -p ~/.codex/commands
cat > ~/.codex/commands/deploy.md << 'EOF'
---
description: Deploy application to specified environment
argument-hint: [environment] [version]
allowed-tools: Bash(git,pnpm,docker)
---

Deploy version $2 to $1 environment

**Pre-deployment:**
1. Verify $1 environment configuration
2. Check version $2 exists in registry
3. Run pre-deployment tests

**Deployment:**
1. Build Docker image: `docker build -t myapp:$2 .`
2. Push to registry: `docker push myapp:$2`
3. Update $1 deployment: `kubectl set image deployment/myapp app=myapp:$2`
4. Monitor rollout: `kubectl rollout status deployment/myapp`

**Post-deployment:**
1. Run smoke tests
2. Update monitoring dashboards
3. Notify team of successful deployment
EOF

# Use custom command
/deploy staging v1.2.3
```

### Batch Processing
```bash
#!/bin/bash
# batch-refactor.sh

# Find all JavaScript files needing refactoring
find src -name "*.js" -type f | while read file; do
    codex --session "refactor-$(basename $file .js)" \
          --file "$file" \
          --prompt "Refactor this file to use modern JavaScript patterns" &
done

wait
echo "All refactoring sessions started"
```

## Parallelism Features

### Session-Based Parallelism
- **Multiple Sessions**: Independent conversations running simultaneously
- **Isolated Contexts**: Each session maintains separate state
- **Resource Sharing**: Shared access to codebase and tools
- **Concurrent Execution**: Background processing capabilities

### Command-Level Parallelism
- **Background Tasks**: Long-running operations with `&`
- **Batch Operations**: Process multiple files/items concurrently
- **Pipeline Support**: Chain operations with output redirection
- **Job Management**: Monitor and control background processes

### Tool Parallelism
- **Multi-Tool Execution**: Different tools working simultaneously
- **Asynchronous Operations**: Non-blocking tool calls
- **Resource Pooling**: Shared tool resources across sessions
- **Load Distribution**: Automatic distribution of computational tasks

### Integration Parallelism
- **Multi-Repository**: Work across different codebases
- **Cross-Service**: Coordinate between microservices
- **CI/CD Integration**: Parallel pipeline execution
- **Team Collaboration**: Multiple developers working simultaneously

## Best Practices

### Session Organization
- Use descriptive session names
- Group related tasks logically
- Clean up completed sessions regularly
- Document session purposes and outcomes

### Performance Optimization
- Use appropriate model sizes for tasks
- Limit file context when possible
- Configure tool permissions appropriately
- Monitor resource usage

### Security Considerations
- Review approval policies regularly
- Use sandbox modes appropriately
- Limit network access to necessary domains
- Audit tool executions and file changes

### Workflow Integration
- Integrate with existing development workflows
- Use custom commands for repetitive tasks
- Leverage parallel processing for efficiency
- Automate routine development tasks</content>
<parameter name="filePath">C:\Users\matt\Dropbox\projects\LLM\docs\codex-cloud.md