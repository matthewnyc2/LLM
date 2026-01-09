# Kilo Code CLI Complete Reference

Kilo Code is an open-source VS Code AI agent that generates code from natural language, runs terminal commands, automates browsers, and refactors code, merging features from Roo Code and Cline.

## Table of Contents
- [Installation](#installation)
- [Configuration](#configuration)
- [Core Commands](#core-commands)
- [Session Management](#session-management)
- [Parallel Sessions](#parallel-sessions)
- [MCP Integration](#mcp-integration)
- [Usage Examples](#usage-examples)

## Installation

### NPM Installation
```bash
npm install -g @kilocode/cli
kilocode
```

### Docker Installation
```dockerfile
FROM node:20-alpine

RUN apk add --no-cache git
RUN npm install -g @kilocode/cli

WORKDIR /workspace
CMD ["kilocode"]
```

### Development Setup
```bash
git clone https://github.com/kilo-org/kilocode.git
cd kilocode
pnpm install
pnpm storybook  # For UI development
```

## Configuration

### Environment Variables
```bash
# Core settings
export KILO_MODE=code
export KILO_TELEMETRY=true
export KILO_THEME=dark

# Provider configuration
export KILO_PROVIDER_TYPE=kilocode
export KILOCODE_TOKEN=your-api-token
export KILOCODE_MODEL=x-ai/grok-code-fast-1
export KILOCODE_ORGANIZATION_ID=org-123

# Auto-approval settings
export KILO_AUTO_APPROVAL_ENABLED=true
export KILO_AUTO_APPROVAL_READ_ENABLED=true
export KILO_AUTO_APPROVAL_WRITE_ENABLED=true
export KILO_AUTO_APPROVAL_BROWSER_ENABLED=false
export KILO_AUTO_APPROVAL_EXECUTE_ALLOWED="ls,cat,echo,pwd,npm,yarn,pnpm"
export KILO_AUTO_APPROVAL_EXECUTE_DENIED="rm -rf,sudo"
```

### Project Configuration
Create `.kilocode` directory in project root with:
- `AGENTS.md` - Repository-specific instructions
- Custom commands in `commands/` subdirectory
- Agent configurations in `agents/` subdirectory

### Global Configuration
Global settings in `~/.kilocode/`:
- `AGENTS.md` - Global working agreements
- `commands/` - Global custom commands
- `agents/` - Global agent configurations

## Core Commands

### Interactive Mode
```bash
kilocode
```
Starts the interactive terminal interface.

### Direct Execution
```bash
kilocode "implement user authentication"
```

### File Operations
```xml
<read_file>
<path>src/auth.js</path>
</read_file>

<edit_file>
<path>src/auth.js</path>
<old_string>function login() {</old_string>
<new_string>async function login(credentials) {
    // Validate credentials
    if (!credentials.email || !credentials.password) {
        throw new Error('Email and password required');
    }</old_string>
</edit_file>
```

### Terminal Commands
```xml
<execute_command>
<command>npm install</command>
</execute_command>

<execute_command>
<command>npm run build && npm test</command>
</execute_command>
```

### Browser Automation
```xml
<launch_browser>
<url>http://localhost:3000</url>
</launch_browser>

<take_screenshot>
<name>login-page</name>
</take_screenshot>
```

### MCP Tool Usage
```xml
<use_mcp_tool>
<server_name>system-monitor</server_name>
<tool_name>get_current_status</tool_name>
<arguments>{}</arguments>
</use_mcp_tool>
```

## Session Management

### Session Creation
```bash
# New session
kilocode --session "feature-auth"

# Continue session
kilocode --session "feature-auth" --continue

# Session with specific model
kilocode --model x-ai/grok-code-fast-1 --session "debug"
```

### Session Context
- **Conversation History**: All interactions preserved
- **File Context**: Referenced files remain accessible
- **Tool State**: Available tools and permissions
- **Browser State**: Active browser sessions

### Session Persistence
- Sessions automatically saved
- Resume with `--continue` flag
- Context maintained across restarts
- State synchronized across instances

## Parallel Sessions

### Multiple Terminal Sessions
```bash
# Terminal 1: API development
kilocode --session "api-dev"

# Terminal 2: UI development
kilocode --session "ui-dev"

# Terminal 3: Testing
kilocode --session "testing"
```

### Background Processing
```bash
# Run tasks in background
kilocode --session "build" --command "npm run build" &
kilocode --session "test" --command "npm run test" &
kilocode --session "lint" --command "npm run lint" &

wait
```

### Session Coordination
```bash
#!/bin/bash
# coordinated-sessions.sh

# Start API development
kilocode --session "api" --prompt "Implement REST API endpoints" &
API_PID=$!

# Start UI development
kilocode --session "ui" --prompt "Create React components" &
UI_PID=$!

# Wait for API to be ready
wait $API_PID

# Start integration
kilocode --session "integration" --prompt "Integrate API with UI" &
INTEGRATION_PID=$!

wait $UI_PID $INTEGRATION_PID
echo "All sessions completed"
```

### Multi-Repository Parallelism
```bash
#!/bin/bash
# multi-repo.sh

REPOS=(
    "frontend:Implement user dashboard"
    "backend:Add user API endpoints"
    "mobile:Integrate user authentication"
)

for repo_task in "${REPOS[@]}"; do
    IFS=':' read -r repo task <<< "$repo_task"
    cd "$repo"
    kilocode --session "$repo-dev" --prompt "$task" &
    cd ..
done

wait
echo "All repositories updated"
```

## MCP Integration

### MCP Server Setup
```bash
# Start MCP server
kilocode mcp | your_mcp_client

# Multiple clients
kilocode mcp | tee >(client1) >(client2) >(client3)
```

### MCP Tool Configuration
Create `~/.kilocode/mcp.json` to configure MCP servers:

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

### Tool Usage Examples
```xml
<!-- File system operations -->
<use_mcp_tool>
<server_name>filesystem</server_name>
<tool_name>read_file</tool_name>
<arguments>{"path": "src/main.js"}</arguments>
</use_mcp_tool>

<!-- Git operations -->
<use_mcp_tool>
<server_name>git</server_name>
<tool_name>get_status</tool_name>
<arguments>{}</arguments>
</use_mcp_tool>
```

## Usage Examples

### Development Workflow
```bash
# 1. Start feature development
kilocode --session "user-auth"
# In session: "Implement JWT authentication with refresh tokens"

# 2. Parallel testing
kilocode --session "auth-tests"
# In session: "Write comprehensive tests for authentication"

# 3. Documentation
kilocode --session "auth-docs"
# In session: "Document the authentication API"
```

### Browser Automation
```xml
<launch_browser>
<url>http://localhost:3000/login</url>
</launch_browser>

<take_screenshot>
<name>login-before</name>
</take_screenshot>

<!-- Implement login functionality -->

<take_screenshot>
<name>login-after</name>
</take_screenshot>
```

### Complex Refactoring
```bash
kilocode --session "refactor-auth"
# In session: "Refactor authentication module to use dependency injection"

# Commands executed:
# 1. Analyze current structure
# 2. Create dependency injection container
# 3. Refactor auth service
# 4. Update all consumers
# 5. Run tests
```

### CI/CD Integration
```bash
#!/bin/bash
# ci-integration.sh

# Code review
kilocode --session "review" --format json \
    --prompt "Review codebase for quality issues" > review.json

# Security audit
kilocode --session "security" --format json \
    --prompt "Audit for security vulnerabilities" > security.json

# Performance analysis
kilocode --session "performance" --format json \
    --prompt "Analyze performance bottlenecks" > perf.json

# Check results
if jq -e '.issues | length > 0' review.json; then
    echo "Code quality issues found"
    exit 1
fi
```

### Custom Command Creation
```markdown
---
description: Deploy application with full pipeline
argument-hint: [environment] [version]
allowed-tools: Bash(docker,kubectl), Browser
---

Deploy $2 to $1 environment

**Build Phase:**
1. Build Docker image: `docker build -t myapp:$2 .`
2. Run tests: `docker run --rm myapp:$2 npm test`
3. Push image: `docker push myapp:$2`

**Deploy Phase:**
1. Update Kubernetes deployment
2. Wait for rollout completion
3. Run integration tests

**Verification:**
1. Check application health
2. Run smoke tests
3. Update monitoring
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
    "Add email notification system"
)

for i in "${!FEATURES[@]}"; do
    feature="${FEATURES[$i]}"
    session_name="feature-$((i+1))"
    kilocode --session "$session_name" --prompt "$feature" &
    echo "Started session: $session_name"
done

# Monitor progress
while true; do
    running=0
    for i in "${!FEATURES[@]}"; do
        session_name="feature-$((i+1))"
        # Check if session still active
        if kill -0 $(pgrep -f "kilocode --session $session_name") 2>/dev/null; then
            ((running++))
        fi
    done

    if [ $running -eq 0 ]; then
        break
    fi

    echo "Active sessions: $running"
    sleep 30
done

echo "All features completed"
```

### Multi-Agent Collaboration
```bash
# Start different agents for different aspects
kilocode --agent "code-reviewer" --session "review" --prompt "Review authentication implementation" &
kilocode --agent "security-auditor" --session "security" --prompt "Audit auth for security issues" &
kilocode --agent "performance-optimizer" --session "perf" --prompt "Optimize auth performance" &

wait
```

### Automated Testing Pipeline
```bash
#!/bin/bash
# test-pipeline.sh

# Unit tests
kilocode --session "unit-tests" --command "npm run test:unit" &

# Integration tests
kilocode --session "integration-tests" --command "npm run test:integration" &

# E2E tests with browser
kilocode --session "e2e-tests" --prompt "Run end-to-end tests with browser automation" &

# Performance tests
kilocode --session "perf-tests" --command "npm run test:perf" &

# Wait for all tests
wait

# Generate report
kilocode --session "test-report" --prompt "Generate comprehensive test report from all test results"
```

## Parallelism Features

### Session-Based Parallelism
- **Multiple Sessions**: Independent conversations running simultaneously
- **Isolated Contexts**: Each session maintains separate state and history
- **Resource Sharing**: Shared access to codebase and MCP servers
- **Concurrent Execution**: Background processing with job control

### MCP Server Parallelism
- **Multi-Client Support**: Single MCP server serving multiple Kilo Code instances
- **Tool Distribution**: Shared tool access across all connected sessions
- **State Synchronization**: Optional state sharing between sessions
- **Load Balancing**: Automatic distribution of computational tasks

### Command-Level Parallelism
- **Background Commands**: Execute long-running operations asynchronously
- **Batch Processing**: Process multiple files or tasks concurrently
- **Pipeline Support**: Chain operations with output redirection
- **Job Control**: Monitor and manage background processes

### Agent Parallelism
- **Multi-Agent Sessions**: Different specialized agents working simultaneously
- **Collaborative Workflows**: Agents working together on complex tasks
- **Quality Assurance**: Parallel validation and testing
- **Specialized Processing**: Different agents for different aspects of development

### Integration Parallelism
- **Multi-Repository**: Work across different codebases simultaneously
- **Cross-Service**: Coordinate changes between microservices
- **Team Collaboration**: Multiple developers working in parallel
- **CI/CD Integration**: Parallel pipeline execution and monitoring

## Best Practices

### Session Organization
- Use descriptive session names
- Group related tasks logically
- Clean up completed sessions
- Document session purposes and outcomes

### Performance Optimization
- Use appropriate models for different tasks
- Configure auto-approval settings appropriately
- Limit browser automation when possible
- Monitor resource usage and MCP server load

### Security Considerations
- Review auto-approval settings regularly
- Use environment variables for sensitive data
- Limit tool permissions to necessary operations
- Audit session activities and file changes

### Workflow Integration
- Integrate with existing development workflows
- Use custom commands for repetitive tasks
- Leverage MCP servers for extended functionality
- Automate routine development and testing tasks

### MCP Server Management
- Configure MCP servers appropriately for your needs
- Monitor MCP server performance and resource usage
- Use appropriate tool permissions for MCP operations
- Keep MCP servers updated and secure</content>
<parameter name="filePath">C:\Users\matt\Dropbox\projects\LLM\docs\kilocode-cli.md