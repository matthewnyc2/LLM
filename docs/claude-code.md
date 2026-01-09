# Claude Code Complete Reference

Claude Code is an agentic terminal tool that understands your codebase to help you code faster by executing tasks, explaining code, and handling git workflows through natural language commands.

## Table of Contents
- [Installation](#installation)
- [Configuration](#configuration)
- [Core Commands](#core-commands)
- [Session Management](#session-management)
- [Parallel Sessions](#parallel-sessions)
- [Plugin System](#plugin-system)
- [Usage Examples](#usage-examples)

## Installation

### NPM Installation
```bash
npm install -g @anthropic-ai/claude-code
claude
```

### Prerequisites
- Node.js 18+
- Anthropic API key (set `ANTHROPIC_API_KEY`)

## Configuration

### Environment Variables
```bash
export ANTHROPIC_API_KEY="your-api-key"
export ANTHROPIC_AUTH_TOKEN="your-auth-token"  # Optional
```

### Project Configuration
Create `CLAUDE.md` in project root for repository-specific instructions:

```markdown
# CLAUDE.md

## Project Overview
This is a React/TypeScript web application for task management.

## Development Guidelines
- Use TypeScript for all new code
- Follow existing naming conventions
- Write tests for new features
- Update documentation for API changes

## Code Style
- Use 2 spaces for indentation
- Prefer functional components
- Use hooks for state management
- Follow ESLint configuration
```

### Global Configuration
Global settings in `~/.claude/`:
- `CLAUDE.md` - Global instructions
- `commands/` - Custom commands
- `plugins/` - Custom plugins

## Core Commands

### Interactive Mode
```bash
claude
```
Starts the interactive terminal interface.

### Direct Commands
```bash
claude "explain how this function works"
claude "implement user authentication"
claude "fix the bug in login.js"
```

### Slash Commands
- `/help` - Show help and available commands
- `/clear` - Clear conversation history
- `/undo` - Undo the last action
- `/redo` - Redo the last undone action
- `/run` - Execute a shell command
- `/bash` - Run bash commands
- `/read` - Read file contents
- `/edit` - Edit files
- `/search` - Search codebase
- `/grep` - Search with regex
- `/ls` - List directory contents
- `/cd` - Change directory
- `/git` - Git operations
- `/commit` - Create commits
- `/pr` - Create pull requests

### File Operations
```bash
claude
> /read src/auth.js
> /edit src/auth.js "add error handling"
> /grep "TODO" src/
```

### Git Integration
```bash
claude
> /git status
> /git diff
> /commit "Implement user authentication"
> /pr "Add user login feature"
```

## Session Management

### Session Creation
```bash
# New session
claude --session "auth-feature"

# Continue session
claude --continue

# Session with specific prompt
claude --prompt "Debug the login issue" --session "debug-login"
```

### Session Context
- **Conversation History**: All interactions preserved
- **File Context**: Referenced files remain accessible
- **Git State**: Repository status and changes
- **Shell Environment**: Command history and working directory

### Session Persistence
- Sessions automatically saved locally
- Resume with `--continue` flag
- Context maintained across terminal sessions
- File changes tracked and reversible

## Parallel Sessions

### Multiple Terminal Sessions
```bash
# Terminal 1: Feature development
claude --session "user-auth"

# Terminal 2: Bug fixes
claude --session "bug-fixes"

# Terminal 3: Code review
claude --session "code-review"
```

### Background Processing
```bash
# Run long tasks in background
claude --session "build" "npm run build" &
claude --session "test" "npm run test" &
claude --session "lint" "npm run lint" &

wait
```

### Session Coordination
```bash
#!/bin/bash
# coordinated-development.sh

# Start API development
claude --session "api" --prompt "Implement REST API" &
API_PID=$!

# Start UI development
claude --session "ui" --prompt "Create React components" &
UI_PID=$!

# Wait for API completion
wait $API_PID

# Start integration
claude --session "integration" --prompt "Connect API to UI" &
INTEGRATION_PID=$!

wait $UI_PID $INTEGRATION_PID
echo "Development complete"
```

### Multi-Repository Parallelism
```bash
#!/bin/bash
# multi-repo-development.sh

REPOS=(
    "frontend:Implement dashboard UI"
    "backend:Add user management API"
    "mobile:Integrate authentication"
)

for repo_task in "${REPOS[@]}"; do
    IFS=':' read -r repo task <<< "$repo_task"
    cd "$repo"
    claude --session "$repo-dev" --prompt "$task" &
    cd ..
done

wait
echo "All repositories updated"
```

## Plugin System

### Plugin Development
Create plugins in `~/.claude/plugins/`:

```javascript
// hello-world.js
export const description = "A simple hello world plugin";

export async function run(args) {
    console.log("Hello, World!");
    if (args.length > 0) {
        console.log(`Arguments: ${args.join(', ')}`);
    }
    return { success: true };
}
```

### Plugin Commands
```bash
claude
> /plugin install hello-world
> /hello world argument
```

### MCP Integration

Claude Code supports Model Context Protocol (MCP) servers for extended tool capabilities.

#### MCP Server Configuration
Create `~/.claude/mcp.json` to configure MCP servers:

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

#### MCP Tool Usage in Plugins
```javascript
// mcp-plugin.js
export const mcpServers = {
    "filesystem": {
        command: "npx",
        args: ["@modelcontextprotocol/server-filesystem", "/workspace"]
    },
    "git": {
        command: "uvx",
        args: ["mcp-server-git", "--repository", "/workspace"]
    }
};

export async function useMcpTool(serverName, toolName, args) {
    // Implementation for MCP tool usage
    const result = await callMcpTool(serverName, toolName, args);
    return result;
}

export async function run(args) {
    // Use MCP tools in plugin logic
    const files = await useMcpTool('filesystem', 'list_directory', { path: '.' });
    const gitStatus = await useMcpTool('git', 'status', {});

    return {
        success: true,
        data: { files, gitStatus }
    };
}
```

#### Interactive MCP Commands
```bash
claude
> /mcp filesystem read_file src/main.js
> /mcp git get_status
> /mcp database query "SELECT * FROM users LIMIT 5"
```

#### Parallel MCP Sessions
```bash
# Start multiple sessions with MCP access
claude --session "file-ops" --mcp-enabled &
claude --session "git-ops" --mcp-enabled &
claude --session "db-ops" --mcp-enabled &

# Each session can use different MCP tools
# Session 1: File system operations
# Session 2: Git repository management
# Session 3: Database queries

wait
```

### Custom Commands
Create commands in `~/.claude/commands/`:

```markdown
---
description: Deploy application to environment
argument-hint: [environment] [version]
allowed-tools: Bash, Git
---

Deploy $2 to $1 environment

**Steps:**
1. Build application: `npm run build`
2. Run tests: `npm run test`
3. Deploy to $1: `deploy-to-$1.sh $2`
4. Verify deployment: `curl https://$1-api.example.com/health`

Success! Deployed version $2 to $1.
```

## Usage Examples

### Development Workflow
```bash
# 1. Start feature development
claude --session "user-auth"
# In session: "Implement JWT authentication with refresh tokens"

# 2. Parallel testing
claude --session "auth-tests"
# In session: "Write comprehensive tests for authentication"

# 3. Documentation
claude --session "auth-docs"
# In session: "Document the authentication API"
```

### Bug Fixing Process
```bash
# Debug session
claude --session "debug-login"
# In session: "Debug the login failure issue"

# Fix implementation
claude --session "fix-login"
# In session: "Fix the null pointer exception in login function"
```

### Code Review
```bash
# Automated review
claude --session "review" --prompt "Review PR for security issues"

# Manual review
claude --session "manual-review"
# In session: "Conduct thorough code review of authentication module"
```

### Refactoring Tasks
```bash
# Analysis
claude --session "refactor-analysis"
# In session: "Analyze authentication code for refactoring opportunities"

# Implementation
claude --session "refactor-impl"
# In session: "Refactor auth module to use dependency injection"
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
    claude --session "$session_name" --prompt "$feature" &
    echo "Started: $session_name"
done

wait
echo "All features initiated"
```

### CI/CD Integration
```bash
#!/bin/bash
# ci-integration.sh

# Code quality check
claude --session "quality" --format json \
    --prompt "Check code quality and suggest improvements" > quality.json

# Security audit
claude --session "security" --format json \
    --prompt "Audit for security vulnerabilities" > security.json

# Performance analysis
claude --session "performance" --format json \
    --prompt "Analyze performance bottlenecks" > perf.json

# Check results
if jq -e '.issues | length > 0' quality.json; then
    echo "Quality issues found"
    exit 1
fi
```

### Custom Plugin Examples
```javascript
// deployment-plugin.js
export const description = "Application deployment plugin";

export async function deploy(args) {
    const [environment, version] = args;

    if (!environment || !version) {
        throw new Error("Usage: /deploy <environment> <version>");
    }

    console.log(`Deploying ${version} to ${environment}...`);

    // Build
    await runCommand(`npm run build`);

    // Test
    await runCommand(`npm run test`);

    // Deploy
    await runCommand(`deploy-to-${environment}.sh ${version}`);

    // Verify
    const response = await runCommand(`curl https://${environment}-api.example.com/health`);
    if (response.includes('"status":"ok"')) {
        console.log(`✅ Successfully deployed ${version} to ${environment}`);
        return { success: true };
    } else {
        throw new Error("Deployment verification failed");
    }
}

async function runCommand(cmd) {
    // Implementation to run shell command
}
```

### Git Workflow Automation
```bash
#!/bin/bash
# git-workflow.sh

# Create feature branch
claude --session "branch" --prompt "Create feature branch for user auth"

# Implement feature
claude --session "implement" --prompt "Implement user authentication"

# Run tests
claude --session "test" --prompt "Run all tests and fix any failures"

# Create PR
claude --session "pr" --prompt "Create pull request for user authentication feature"

echo "Feature development complete"
```

### Multi-Agent Collaboration
```bash
# Different agents for different aspects
claude --agent "code-reviewer" --session "review" --prompt "Review authentication implementation" &
claude --agent "security-auditor" --session "security" --prompt "Audit auth for security issues" &
claude --agent "performance-optimizer" --session "perf" --prompt "Optimize auth performance" &

wait
```

## Parallelism Features

### Session-Based Parallelism
- **Multiple Sessions**: Independent conversations running simultaneously
- **Isolated Contexts**: Each session maintains separate state and history
- **Resource Sharing**: Shared access to codebase and tools
- **Concurrent Execution**: Background processing with job control

### Command-Level Parallelism
- **Background Commands**: Execute long-running operations asynchronously
- **Batch Operations**: Process multiple files or tasks concurrently
- **Pipeline Support**: Chain operations with output redirection
- **Job Management**: Monitor and control background processes

### Plugin Parallelism
- **Multi-Plugin Execution**: Different plugins working simultaneously
- **Asynchronous Operations**: Non-blocking plugin calls
- **Resource Pooling**: Shared resources across plugins
- **Event-Driven Architecture**: Plugins responding to events in parallel

### Agent Parallelism
- **Multi-Agent Sessions**: Different specialized agents working simultaneously
- **Collaborative Workflows**: Agents working together on complex tasks
- **Quality Assurance**: Parallel validation and testing
- **Specialized Processing**: Different agents for different development aspects

### Integration Parallelism
- **Multi-Repository**: Work across different codebases simultaneously
- **Cross-Service**: Coordinate between microservices
- **Team Collaboration**: Multiple developers working in parallel
- **CI/CD Integration**: Parallel pipeline execution and monitoring

## Best Practices

### Session Organization
- Use descriptive session names
- Group related tasks logically
- Clean up completed sessions regularly
- Document session purposes and outcomes

### Performance Optimization
- Use appropriate model configurations
- Limit file context when possible
- Configure tool permissions appropriately
- Monitor resource usage

### Security Considerations
- Review plugin permissions regularly
- Use environment variables for sensitive data
- Limit tool access to necessary operations
- Audit session activities and file changes

### Workflow Integration
- Integrate with existing development workflows
- Use custom commands for repetitive tasks
- Leverage plugins for extended functionality
- Automate routine development tasks

### Plugin Development
- Follow plugin development guidelines
- Test plugins thoroughly before deployment
- Document plugin usage and requirements
- Keep plugins updated and secure</content>
<parameter name="filePath">C:\Users\matt\Dropbox\projects\LLM\docs\claude-code.md