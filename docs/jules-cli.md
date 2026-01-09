# Jules CLI Complete Reference

Jules is an experimental coding agent that helps developers fix bugs, add documentation, and build new features. It integrates with GitHub, understands your codebase, and works asynchronously.

## Table of Contents
- [Installation](#installation)
- [Authentication](#authentication)
- [Core Commands](#core-commands)
- [Session Management](#session-management)
- [Parallel Sessions](#parallel-sessions)
- [API Integration](#api-integration)
- [Usage Examples](#usage-examples)

## Installation

Jules is a web-based tool accessible through the Jules web app at [jules.google](https://jules.google).

### Prerequisites
- GitHub account for repository integration
- API key from Jules settings

## Authentication

### API Key Setup
1. Visit [jules.google](https://jules.google)
2. Go to Settings page
3. Create a new API key (maximum 3 keys allowed)
4. Store the key securely

### API Usage
```bash
# Include API key in all requests
curl 'https://jules.googleapis.com/v1alpha/sessions' \
    -X POST \
    -H "Content-Type: application/json" \
    -H 'X-Goog-Api-Key: YOUR_API_KEY' \
    -d '{
        "prompt": "Create a boba app!",
        "sourceContext": {
            "source": "sources/github/bobalover/boba",
            "githubRepoContext": {
                "startingBranch": "main"
            }
        },
        "title": "Boba App"
    }'
```

## Core Commands

Jules operates through API calls and web interface. There are no CLI commands - all interactions happen via HTTP requests.

### Session Creation
```bash
curl 'https://jules.googleapis.com/v1alpha/sessions' \
    -X POST \
    -H "Content-Type: application/json" \
    -H 'X-Goog-Api-Key: YOUR_API_KEY' \
    -d '{
        "prompt": "Your task description",
        "sourceContext": {
            "source": "sources/github/owner/repo",
            "githubRepoContext": {
                "startingBranch": "main"
            }
        },
        "title": "Session Title"
    }'
```

### Session Management
```bash
# Get session details
curl 'https://jules.googleapis.com/v1alpha/sessions/SESSION_ID' \
    -H 'X-Goog-Api-Key: YOUR_API_KEY'

# List all sessions
curl 'https://jules.googleapis.com/v1alpha/sessions' \
    -H 'X-Goog-Api-Key: YOUR_API_KEY'

# Delete session
curl 'https://jules.googleapis.com/v1alpha/sessions/SESSION_ID' \
    -X DELETE \
    -H 'X-Goog-Api-Key: YOUR_API_KEY'
```

### Activity Monitoring
```bash
# List session activities
curl 'https://jules.googleapis.com/v1alpha/sessions/SESSION_ID/activities' \
    -H 'X-Goog-Api-Key: YOUR_API_KEY'

# Get specific activity
curl 'https://jules.googleapis.com/v1alpha/sessions/SESSION_ID/activities/ACTIVITY_ID' \
    -H 'X-Goog-Api-Key: YOUR_API_KEY'
```

### Plan Approval
```bash
# Approve a generated plan
curl 'https://jules.googleapis.com/v1alpha/sessions/SESSION_ID/activities/ACTIVITY_ID:approvePlan' \
    -X POST \
    -H "Content-Type: application/json" \
    -H 'X-Goog-Api-Key: YOUR_API_KEY' \
    -d '{}'
```

## Session Management

### Session States
- **Created**: Initial session creation
- **Planning**: Agent analyzing requirements and creating plan
- **Executing**: Agent implementing the approved plan
- **Completed**: Task finished successfully
- **Failed**: Task encountered errors

### Session Context
```json
{
    "sourceContext": {
        "source": "sources/github/owner/repo",
        "githubRepoContext": {
            "startingBranch": "main"
        }
    }
}
```

### Session Metadata
- **ID**: Unique session identifier
- **Title**: User-provided session title
- **Prompt**: Original task description
- **Created Time**: Session creation timestamp
- **Status**: Current execution status

## Parallel Sessions

### Multiple Repository Sessions
Jules supports working on multiple repositories simultaneously:

```bash
# Session 1: Frontend app
curl -X POST 'https://jules.googleapis.com/v1alpha/sessions' \
    -H 'X-Goog-Api-Key: YOUR_API_KEY' \
    -d '{
        "prompt": "Implement user authentication",
        "sourceContext": {
            "source": "sources/github/company/frontend-app"
        },
        "title": "Frontend Auth"
    }'

# Session 2: Backend API
curl -X POST 'https://jules.googleapis.com/v1alpha/sessions' \
    -H 'X-Goog-Api-Key: YOUR_API_KEY' \
    -d '{
        "prompt": "Add user management endpoints",
        "sourceContext": {
            "source": "sources/github/company/backend-api"
        },
        "title": "Backend User API"
    }'

# Session 3: Mobile app
curl -X POST 'https://jules.googleapis.com/v1alpha/sessions' \
    -H 'X-Goog-Api-Key: YOUR_API_KEY' \
    -d '{
        "prompt": "Integrate authentication flow",
        "sourceContext": {
            "source": "sources/github/company/mobile-app"
        },
        "title": "Mobile Auth Integration"
    }'
```

### Parallel Task Execution
```bash
#!/bin/bash
# parallel-jules.sh

# Start multiple sessions in parallel
SESSION1=$(curl -s -X POST 'https://jules.googleapis.com/v1alpha/sessions' \
    -H 'X-Goog-Api-Key: YOUR_API_KEY' \
    -d '{"prompt": "Fix login bug", "sourceContext": {"source": "sources/github/company/app"}, "title": "Bug Fix"}' | jq -r '.name')

SESSION2=$(curl -s -X POST 'https://jules.googleapis.com/v1alpha/sessions' \
    -H 'X-Goog-Api-Key: YOUR_API_KEY' \
    -d '{"prompt": "Add dark mode", "sourceContext": {"source": "sources/github/company/app"}, "title": "Feature"}' | jq -r '.name')

# Monitor progress
while true; do
    STATUS1=$(curl -s "https://jules.googleapis.com/v1alpha/sessions/$SESSION1" -H 'X-Goog-Api-Key: YOUR_API_KEY' | jq -r '.status')
    STATUS2=$(curl -s "https://jules.googleapis.com/v1alpha/sessions/$SESSION2" -H 'X-Goog-Api-Key: YOUR_API_KEY' | jq -r '.status')

    echo "Session 1: $STATUS1"
    echo "Session 2: $STATUS2"

    if [[ "$STATUS1" == "completed" && "$STATUS2" == "completed" ]]; then
        break
    fi

    sleep 30
done

echo "All sessions completed!"
```

### Batch Session Creation
```bash
#!/bin/bash
# batch-sessions.sh

TASKS=(
    "Implement user registration"
    "Add password reset functionality"
    "Create user profile page"
    "Add email notifications"
)

for task in "${TASKS[@]}"; do
    curl -X POST 'https://jules.googleapis.com/v1alpha/sessions' \
        -H 'X-Goog-Api-Key: YOUR_API_KEY' \
        -d "{
            \"prompt\": \"$task\",
            \"sourceContext\": {
                \"source\": \"sources/github/company/web-app\"
            },
            \"title\": \"$task\"
        }" &
done

wait
echo "All sessions created"
```

## API Integration

### REST API Endpoints

#### Sessions
- `POST /v1alpha/sessions` - Create new session
- `GET /v1alpha/sessions` - List all sessions
- `GET /v1alpha/sessions/{id}` - Get session details
- `DELETE /v1alpha/sessions/{id}` - Delete session

#### Activities
- `GET /v1alpha/sessions/{id}/activities` - List session activities
- `GET /v1alpha/sessions/{id}/activities/{activityId}` - Get activity details
- `POST /v1alpha/sessions/{id}/activities/{activityId}:approvePlan` - Approve plan

#### Sources
- `GET /v1alpha/sources` - List available sources

### Activity Types
- `planGenerated` - Agent created implementation plan
- `planApproved` - User approved the plan
- `progressUpdated` - Task execution progress
- `changeSet` - Code changes applied
- `bashOutput` - Command execution results

### Response Format
```json
{
    "activities": [
        {
            "name": "sessions/123/activities/456",
            "createTime": "2025-01-15T10:30:00Z",
            "originator": "agent",
            "planGenerated": {
                "plan": {
                    "id": "plan-789",
                    "steps": [
                        {
                            "id": "step-1",
                            "title": "Setup environment",
                            "description": "Install dependencies"
                        }
                    ]
                }
            }
        }
    ]
}
```

## Usage Examples

### Bug Fix Session
```bash
curl -X POST 'https://jules.googleapis.com/v1alpha/sessions' \
    -H 'X-Goog-Api-Key: YOUR_API_KEY' \
    -d '{
        "prompt": "Fix the null pointer exception in user login",
        "sourceContext": {
            "source": "sources/github/company/auth-service",
            "githubRepoContext": {
                "startingBranch": "develop"
            }
        },
        "title": "Login Bug Fix"
    }'
```

### Feature Implementation
```bash
curl -X POST 'https://jules.googleapis.com/v1alpha/sessions' \
    -H 'X-Goog-Api-Key: YOUR_API_KEY' \
    -d '{
        "prompt": "Add real-time notifications for user actions",
        "sourceContext": {
            "source": "sources/github/company/notification-service"
        },
        "title": "Real-time Notifications"
    }'
```

### Documentation Update
```bash
curl -X POST 'https://jules.googleapis.com/v1alpha/sessions' \
    -H 'X-Goog-Api-Key: YOUR_API_KEY' \
    -d '{
        "prompt": "Update API documentation for v2.0 endpoints",
        "sourceContext": {
            "source": "sources/github/company/api-docs"
        },
        "title": "API Docs Update"
    }'
```

### Code Review Session
```bash
curl -X POST 'https://jules.googleapis.com/v1alpha/sessions' \
    -H 'X-Goog-Api-Key: YOUR_API_KEY' \
    -d '{
        "prompt": "Review pull request #123 for security vulnerabilities and code quality",
        "sourceContext": {
            "source": "sources/github/company/web-app",
            "githubRepoContext": {
                "startingBranch": "feature/new-payment"
            }
        },
        "title": "Security Code Review"
    }'
```

### Parallel Development Workflow
```bash
#!/bin/bash
# parallel-development.sh

# Define repositories and tasks
declare -A TASKS=(
    ["frontend"]="Implement responsive dashboard UI"
    ["backend"]="Add GraphQL API endpoints"
    ["mobile"]="Integrate push notifications"
    ["docs"]="Update deployment guides"
)

# Create sessions for each repository
for repo in "${!TASKS[@]}"; do
    curl -X POST 'https://jules.googleapis.com/v1alpha/sessions' \
        -H 'X-Goog-Api-Key: YOUR_API_KEY' \
        -d "{
            \"prompt\": \"${TASKS[$repo]}\",
            \"sourceContext\": {
                \"source\": \"sources/github/company/$repo\"
            },
            \"title\": \"$repo: ${TASKS[$repo]}\"
        }" &
done

wait
echo "All development sessions initiated"
```

### Monitoring Script
```bash
#!/bin/bash
# monitor-sessions.sh

# Get all active sessions
SESSIONS=$(curl -s 'https://jules.googleapis.com/v1alpha/sessions' \
    -H 'X-Goog-Api-Key: YOUR_API_KEY' | jq -r '.sessions[].name')

for session in $SESSIONS; do
    # Get latest activity
    ACTIVITY=$(curl -s "$session/activities?orderBy=createTime%20desc&pageSize=1" \
        -H 'X-Goog-Api-Key: YOUR_API_KEY' | jq -r '.activities[0]')

    STATUS=$(echo $ACTIVITY | jq -r '.progressUpdated.title // "Planning"')
    TIME=$(echo $ACTIVITY | jq -r '.createTime')

    echo "$session: $STATUS ($TIME)"
done
```

### CI/CD Integration
```bash
#!/bin/bash
# ci-integration.sh

# Trigger Jules session on PR
if [ "$GITHUB_EVENT_NAME" = "pull_request" ]; then
    PR_NUMBER=$(jq -r '.number' "$GITHUB_EVENT_PATH")
    BRANCH=$(jq -r '.pull_request.head.ref' "$GITHUB_EVENT_PATH")

    curl -X POST 'https://jules.googleapis.com/v1alpha/sessions' \
        -H 'X-Goog-Api-Key: YOUR_API_KEY' \
        -d "{
            \"prompt\": \"Review PR #$PR_NUMBER for code quality and potential issues\",
            \"sourceContext\": {
                \"source\": \"sources/github/$GITHUB_REPOSITORY\",
                \"githubRepoContext\": {
                    \"startingBranch\": \"$BRANCH\"
                }
            },
            \"title\": \"PR #$PR_NUMBER Review\"
        }"
fi
```

## Parallelism Features

### Asynchronous Execution
- **Non-blocking**: Sessions run asynchronously without blocking other operations
- **Background Processing**: Multiple sessions can execute simultaneously
- **Resource Isolation**: Each session operates independently
- **Scalable**: Handle multiple repositories and tasks concurrently

### Multi-Repository Support
- **Parallel Development**: Work on multiple codebases simultaneously
- **Cross-Repository Tasks**: Coordinate changes across services
- **Independent Workflows**: Each repository maintains separate session history
- **Branch Isolation**: Work with different branches per repository

### Batch Operations
- **Bulk Session Creation**: Create multiple sessions in parallel
- **Coordinated Tasks**: Related tasks across different repositories
- **Workflow Orchestration**: Chain dependent operations
- **Progress Monitoring**: Track multiple sessions simultaneously

### Integration Capabilities
- **CI/CD Pipelines**: Trigger sessions from automated workflows
- **API Automation**: Programmatic session management
- **Monitoring Systems**: Real-time status tracking
- **Notification Systems**: Alert on session completion

## Best Practices

### Session Organization
- Use descriptive titles for sessions
- Group related tasks in batches
- Monitor session progress regularly
- Clean up completed sessions

### Error Handling
- Check API response codes
- Implement retry logic for failed requests
- Log session creation and monitoring
- Handle rate limiting appropriately

### Security Considerations
- Store API keys securely
- Use environment variables for credentials
- Limit API key permissions
- Rotate keys regularly

### Performance Optimization
- Batch related operations
- Monitor API rate limits
- Use appropriate polling intervals
- Cache frequently accessed data</content>
<parameter name="filePath">C:\Users\matt\Dropbox\projects\LLM\docs\jules-cli.md