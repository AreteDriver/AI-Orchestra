# Gorgon Code Examples

This document provides detailed code examples and usage patterns for Gorgon.

## Table of Contents
- [Basic Usage](#basic-usage)
- [Workflow Creation](#workflow-creation)
- [API Integration](#api-integration)
- [Custom Workflows](#custom-workflows)
- [Advanced Patterns](#advanced-patterns)
- [Error Handling](#error-handling)
- [Real-World Examples](#real-world-examples)
- [Best Practices](#best-practices)
- [YAML Workflow Format](#yaml-workflow-format)
- [Parallel Execution](#parallel-execution)

---

## Basic Usage

### Example 1: Simple Text Generation

```python
from test_ai import WorkflowEngine, Workflow, WorkflowStep, StepType

# Initialize the workflow engine
engine = WorkflowEngine()

# Create a simple workflow
workflow = Workflow(
    id="simple_generation",
    name="Simple Text Generation",
    description="Generate creative text with AI",
    steps=[
        WorkflowStep(
            id="generate_text",
            type=StepType.OPENAI,
            action="generate_completion",
            params={
                "prompt": "{{user_prompt}}",
                "model": "gpt-4o-mini",
                "max_tokens": 500
            }
        )
    ],
    variables={
        "user_prompt": "Write a short story about a robot learning to paint"
    }
)

# Execute the workflow
result = engine.execute_workflow(workflow)

# Access the output
print(f"Status: {result.status}")
print(f"Output: {result.outputs['generate_text']['response']}")
```

### Example 2: Using Prompt Templates

```python
from test_ai import PromptTemplateManager, PromptTemplate

# Initialize the prompt manager
manager = PromptTemplateManager()

# Create a reusable template
template = PromptTemplate(
    id="blog_post_generator",
    name="Blog Post Generator",
    description="Generate blog posts from topics",
    system_prompt="You are an expert content writer who creates engaging blog posts.",
    user_prompt="Write a 500-word blog post about: {topic}\n\nInclude:\n- Introduction\n- 3 main points\n- Conclusion",
    variables=["topic"]
)

# Save the template
manager.save_template(template)

# Use the template
loaded_template = manager.load_template("blog_post_generator")
formatted_prompt = loaded_template.format(topic="AI in Healthcare")

print(formatted_prompt)
```

---

## Workflow Creation

### Example 3: Multi-Step Workflow

```python
from test_ai import WorkflowEngine, Workflow, WorkflowStep, StepType

# Create a workflow with multiple steps
workflow = Workflow(
    id="multi_step_content",
    name="Multi-Step Content Creation",
    description="Generate outline, then full content",
    steps=[
        # Step 1: Generate outline
        WorkflowStep(
            id="create_outline",
            type=StepType.OPENAI,
            action="generate_completion",
            params={
                "prompt": "Create a detailed outline for an article about: {{topic}}",
                "model": "gpt-4o-mini"
            },
            next_step="write_content"
        ),
        # Step 2: Write full content based on outline
        WorkflowStep(
            id="write_content",
            type=StepType.OPENAI,
            action="generate_completion",
            params={
                "prompt": "Write a full article based on this outline:\n\n{{create_outline.response}}",
                "model": "gpt-4o-mini",
                "max_tokens": 2000
            },
            next_step="save_to_file"
        ),
        # Step 3: Save to GitHub
        WorkflowStep(
            id="save_to_file",
            type=StepType.GITHUB,
            action="commit_file",
            params={
                "repo": "{{github_repo}}",
                "path": "articles/{{filename}}.md",
                "content": "{{write_content.response}}",
                "message": "Add article: {{topic}}"
            }
        )
    ],
    variables={
        "topic": "The Future of AI",
        "github_repo": "username/blog",
        "filename": "future-of-ai"
    }
)

# Execute
engine = WorkflowEngine()
result = engine.execute_workflow(workflow)
```

### Example 4: Conditional Logic (Pseudo-code)

```python
# Note: This is a conceptual example showing how you might extend the system

workflow = Workflow(
    id="conditional_workflow",
    name="Workflow with Conditions",
    steps=[
        WorkflowStep(
            id="analyze_sentiment",
            type=StepType.OPENAI,
            action="generate_completion",
            params={
                "prompt": "Analyze sentiment (positive/negative): {{text}}"
            },
            next_step="check_sentiment"
        ),
        WorkflowStep(
            id="check_sentiment",
            type=StepType.CONDITION,
            condition="{{analyze_sentiment.sentiment}} == 'positive'",
            true_step="send_thank_you",
            false_step="escalate_issue"
        ),
        WorkflowStep(
            id="send_thank_you",
            type=StepType.GMAIL,
            action="send_email",
            params={
                "to": "{{customer_email}}",
                "subject": "Thank you!",
                "body": "We appreciate your positive feedback!"
            }
        ),
        WorkflowStep(
            id="escalate_issue",
            type=StepType.GITHUB,
            action="create_issue",
            params={
                "title": "Customer Issue: {{analyze_sentiment.summary}}",
                "body": "{{text}}"
            }
        )
    ]
)
```

---

## API Integration

### Example 5: Using the REST API

```python
import requests

# Base URL
BASE_URL = "http://localhost:8000"

# 1. Authenticate
login_response = requests.post(
    f"{BASE_URL}/auth/login",
    json={"user_id": "demo", "password": "demo"}
)
token = login_response.json()["access_token"]

# Headers for authenticated requests
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# 2. List available workflows
workflows_response = requests.get(
    f"{BASE_URL}/workflows",
    headers=headers
)
workflows = workflows_response.json()
print(f"Available workflows: {len(workflows)}")

# 3. Execute a workflow
execute_response = requests.post(
    f"{BASE_URL}/workflows/execute",
    headers=headers,
    json={
        "workflow_id": "simple_ai_completion",
        "variables": {
            "prompt": "Explain machine learning in simple terms"
        }
    }
)
result = execute_response.json()
print(f"Result: {result}")

# 4. Create a new prompt template
template_response = requests.post(
    f"{BASE_URL}/prompts",
    headers=headers,
    json={
        "id": "code_reviewer",
        "name": "Code Reviewer",
        "description": "Review code for best practices",
        "user_prompt": "Review this code:\n\n{code}\n\nProvide feedback on:\n- Code quality\n- Best practices\n- Potential bugs",
        "variables": ["code"]
    }
)
```

### Example 6: Async API Usage

```python
import httpx
import asyncio

async def execute_workflow_async():
    async with httpx.AsyncClient() as client:
        # Login
        login_resp = await client.post(
            "http://localhost:8000/auth/login",
            json={"user_id": "demo", "password": "demo"}
        )
        token = login_resp.json()["access_token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Execute workflow
        result = await client.post(
            "http://localhost:8000/workflows/execute",
            headers=headers,
            json={
                "workflow_id": "simple_ai_completion",
                "variables": {"prompt": "Hello AI!"}
            }
        )
        
        return result.json()

# Run async
result = asyncio.run(execute_workflow_async())
print(result)
```

---

## Custom Workflows

### Example 7: Email Processing Pipeline

```json
{
  "id": "email_processing",
  "name": "Email Processing Pipeline",
  "description": "Fetch, summarize, and organize emails",
  "steps": [
    {
      "id": "fetch_emails",
      "type": "gmail",
      "action": "get_messages",
      "params": {
        "max_results": 10,
        "query": "is:unread"
      },
      "next_step": "summarize_each"
    },
    {
      "id": "summarize_each",
      "type": "openai",
      "action": "generate_completion",
      "params": {
        "prompt": "Summarize this email in 2-3 sentences:\n\nSubject: {{fetch_emails.subject}}\n\nBody: {{fetch_emails.body}}",
        "model": "gpt-4o-mini"
      },
      "next_step": "save_summary"
    },
    {
      "id": "save_summary",
      "type": "notion",
      "action": "create_page",
      "params": {
        "parent_id": "{{notion_inbox_id}}",
        "title": "Email: {{fetch_emails.subject}}",
        "content": "**From:** {{fetch_emails.from}}\n**Date:** {{fetch_emails.date}}\n**Summary:** {{summarize_each.response}}"
      }
    }
  ],
  "variables": {
    "notion_inbox_id": "your-notion-page-id"
  }
}
```

### Example 8: Documentation Generator

```python
from test_ai import WorkflowEngine, Workflow, WorkflowStep, StepType

# Workflow that generates documentation from code
doc_workflow = Workflow(
    id="doc_generator",
    name="Documentation Generator",
    description="Generate docs from source code",
    steps=[
        WorkflowStep(
            id="read_code",
            type=StepType.TRANSFORM,
            action="read_file",
            params={"path": "{{source_file}}"}
        ),
        WorkflowStep(
            id="generate_docs",
            type=StepType.OPENAI,
            action="generate_completion",
            params={
                "prompt": """Generate comprehensive documentation for this code:

```python
{{read_code.content}}
```

Include:
- Overview
- Function descriptions
- Parameter explanations
- Usage examples
- Return values""",
                "model": "gpt-4o-mini"
            }
        ),
        WorkflowStep(
            id="save_docs",
            type=StepType.GITHUB,
            action="commit_file",
            params={
                "repo": "{{repo}}",
                "path": "docs/{{doc_filename}}.md",
                "content": "{{generate_docs.response}}",
                "message": "Add documentation for {{source_file}}"
            }
        )
    ],
    variables={
        "source_file": "src/utils.py",
        "repo": "username/project",
        "doc_filename": "utils_api"
    }
)
```

---

## Advanced Patterns

### Example 9: Batch Processing

```python
from test_ai import WorkflowEngine

engine = WorkflowEngine()
workflow = engine.load_workflow("email_processing")

# Process multiple items
items = [
    {"email_id": "123", "subject": "Important Update"},
    {"email_id": "124", "subject": "Meeting Request"},
    {"email_id": "125", "subject": "Project Status"}
]

results = []
for item in items:
    workflow.variables.update(item)
    result = engine.execute_workflow(workflow)
    results.append({
        "email_id": item["email_id"],
        "status": result.status,
        "summary": result.outputs.get("summarize_each", {}).get("response")
    })

# Process results
successful = [r for r in results if r["status"] == "completed"]
print(f"Processed {len(successful)}/{len(items)} emails successfully")
```

### Example 10: Error Handling and Retry

```python
from test_ai import WorkflowEngine
import time

def execute_with_retry(workflow, max_retries=3):
    """Execute workflow with retry logic."""
    engine = WorkflowEngine()
    
    for attempt in range(max_retries):
        try:
            result = engine.execute_workflow(workflow)
            
            if result.status == "completed":
                return result
            elif result.status == "failed":
                if attempt < max_retries - 1:
                    print(f"Attempt {attempt + 1} failed, retrying...")
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    print(f"Failed after {max_retries} attempts")
                    return result
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Error: {e}, retrying...")
                time.sleep(2 ** attempt)
            else:
                raise
    
    return None

# Usage
result = execute_with_retry(my_workflow)
```

### Example 11: Workflow Chaining

```python
from test_ai import WorkflowEngine

engine = WorkflowEngine()

# Execute workflows in sequence, passing data between them
workflow1 = engine.load_workflow("fetch_data")
result1 = engine.execute_workflow(workflow1)

# Use result from workflow1 in workflow2
workflow2 = engine.load_workflow("process_data")
workflow2.variables["input_data"] = result1.outputs["fetch"]["data"]
result2 = engine.execute_workflow(workflow2)

# Chain to workflow3
workflow3 = engine.load_workflow("save_results")
workflow3.variables["processed_data"] = result2.outputs["process"]["result"]
result3 = engine.execute_workflow(workflow3)

print(f"Pipeline complete: {result3.status}")
```

---

## Error Handling

### Example 12: Graceful Error Handling

```python
from test_ai import WorkflowEngine
from test_ai.orchestrator import WorkflowResult

def safe_execute(workflow_id: str, variables: dict = None):
    """Execute workflow with comprehensive error handling."""
    try:
        engine = WorkflowEngine()
        workflow = engine.load_workflow(workflow_id)
        
        if variables:
            workflow.variables.update(variables)
        
        result = engine.execute_workflow(workflow)
        
        if result.status == "completed":
            return {
                "success": True,
                "outputs": result.outputs,
                "message": "Workflow completed successfully"
            }
        else:
            return {
                "success": False,
                "error": result.error,
                "message": "Workflow failed"
            }
            
    except FileNotFoundError:
        return {
            "success": False,
            "error": f"Workflow '{workflow_id}' not found",
            "message": "Check workflow ID and try again"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Unexpected error occurred"
        }

# Usage
result = safe_execute("my_workflow", {"param": "value"})
if result["success"]:
    print(f"Success: {result['outputs']}")
else:
    print(f"Error: {result['error']}")
```

---

## Real-World Examples

### Example 13: Meeting Notes to Action Items

```python
from test_ai import WorkflowEngine, Workflow, WorkflowStep, StepType

meeting_notes_workflow = Workflow(
    id="meeting_notes_processor",
    name="Meeting Notes to Action Items",
    description="Extract action items from meeting notes and create GitHub issues",
    steps=[
        WorkflowStep(
            id="extract_actions",
            type=StepType.OPENAI,
            action="generate_completion",
            params={
                "prompt": """Extract action items from these meeting notes:

{{notes}}

Format each action item as:
- [ ] Action item description
- Assignee: Name
- Due date: YYYY-MM-DD

Return only the action items list.""",
                "model": "gpt-4o-mini"
            }
        ),
        WorkflowStep(
            id="create_issues",
            type=StepType.GITHUB,
            action="create_issue",
            params={
                "repo": "{{repo}}",
                "title": "Action Item: {{extract_actions.item_title}}",
                "body": "{{extract_actions.item_description}}\n\nAssignee: {{extract_actions.assignee}}\nDue: {{extract_actions.due_date}}",
                "labels": ["meeting-action-item", "{{priority}}"]
            }
        ),
        WorkflowStep(
            id="save_to_notion",
            type=StepType.NOTION,
            action="create_page",
            params={
                "parent_id": "{{notion_meetings_db}}",
                "title": "Meeting: {{meeting_date}}",
                "content": "{{notes}}\n\n## Action Items\n{{extract_actions.response}}"
            }
        )
    ],
    variables={
        "notes": "",
        "meeting_date": "2025-01-15",
        "repo": "company/projects",
        "notion_meetings_db": "meeting-db-id",
        "priority": "normal"
    }
)
```

### Example 14: Customer Support Automation

```python
support_workflow = Workflow(
    id="support_automation",
    name="Customer Support Automation",
    description="Process support emails and route appropriately",
    steps=[
        WorkflowStep(
            id="fetch_support_email",
            type=StepType.GMAIL,
            action="get_messages",
            params={
                "query": "to:support@company.com is:unread",
                "max_results": 1
            }
        ),
        WorkflowStep(
            id="categorize",
            type=StepType.OPENAI,
            action="generate_completion",
            params={
                "prompt": """Categorize this support email:

Subject: {{fetch_support_email.subject}}
Body: {{fetch_support_email.body}}

Return ONLY one of: bug, feature_request, question, complaint""",
                "model": "gpt-4o-mini"
            }
        ),
        WorkflowStep(
            id="generate_response",
            type=StepType.OPENAI,
            action="generate_completion",
            params={
                "prompt": """Generate a helpful response to this support email:

Category: {{categorize.response}}
Subject: {{fetch_support_email.subject}}
Body: {{fetch_support_email.body}}

Be professional, empathetic, and provide actionable next steps.""",
                "model": "gpt-4o-mini"
            }
        ),
        WorkflowStep(
            id="create_tracking_issue",
            type=StepType.GITHUB,
            action="create_issue",
            params={
                "repo": "company/support-tracker",
                "title": "[{{categorize.response}}] {{fetch_support_email.subject}}",
                "body": "**From:** {{fetch_support_email.from}}\n**Category:** {{categorize.response}}\n\n**Original Message:**\n{{fetch_support_email.body}}\n\n**Suggested Response:**\n{{generate_response.response}}",
                "labels": ["support", "{{categorize.response}}"]
            }
        )
    ]
)
```

---

## Best Practices

### 1. Workflow Organization
- Keep workflows focused on a single purpose
- Use descriptive IDs and names
- Document expected variables and outputs
- Version control your workflow definitions

### 2. Error Handling
- Always handle potential API failures
- Implement retry logic for critical operations
- Log errors for debugging
- Provide fallback behaviors

### 3. Security
- Never hardcode API keys in workflows
- Use environment variables for sensitive data
- Validate all user inputs
- Implement proper authentication

### 4. Performance
- Batch operations when possible
- Use appropriate AI models (gpt-4o-mini for simple tasks)
- Cache results when appropriate
- Monitor API usage and costs

### 5. Testing
- Test workflows with sample data first
- Validate outputs before production use
- Monitor execution logs
- Set up alerts for failures

---

## YAML Workflow Format

### Example 15: Basic YAML Workflow

Workflows can be defined in YAML for easier readability and version control.

```yaml
name: Feature Build
version: "1.0"
description: Multi-agent workflow for building new features

token_budget: 150000
timeout_seconds: 3600

inputs:
  feature_request:
    type: string
    required: true
    description: Description of the feature to build
  codebase_path:
    type: string
    required: true

outputs:
  - plan
  - code
  - review

steps:
  - id: plan
    type: claude_code
    params:
      role: planner
      prompt: |
        Analyze the feature request and create a plan:
        Feature: ${feature_request}
      estimated_tokens: 5000
    outputs:
      - plan
    on_failure: abort

  - id: build
    type: claude_code
    params:
      role: builder
      prompt: |
        Implement the feature: ${plan}
      estimated_tokens: 20000
    outputs:
      - code
    on_failure: retry
    max_retries: 2
```

### Step Types

| Type | Description |
|------|-------------|
| `claude_code` | Execute Claude/Anthropic API call |
| `openai` | Execute OpenAI API call |
| `shell` | Run shell command |
| `parallel` | Execute sub-steps concurrently |
| `checkpoint` | Create execution checkpoint |

### Step Configuration Options

```yaml
- id: step_name           # Unique identifier
  type: claude_code       # Step type
  params:                 # Type-specific parameters
    role: planner
    prompt: "..."
    estimated_tokens: 5000
  condition:              # Optional: conditional execution
    field: previous_result
    operator: contains    # equals, not_equals, contains, greater_than, less_than
    value: "success"
  on_failure: abort       # abort, skip, retry
  max_retries: 3          # For retry mode
  timeout_seconds: 300
  outputs:                # Variables to capture
    - result_var
```

---

## Parallel Execution

### Example 16: Parallel Steps

Run multiple independent analyses concurrently:

```yaml
steps:
  - id: parallel_analysis
    type: parallel
    params:
      strategy: threading    # threading, asyncio, or process
      max_workers: 4         # Maximum concurrent tasks
      fail_fast: false       # Continue if one fails
      steps:
        - id: security
          type: claude_code
          params:
            role: reviewer
            prompt: "Perform security analysis..."
          outputs:
            - security_report

        - id: performance
          type: claude_code
          params:
            role: analyst
            prompt: "Analyze performance..."
          outputs:
            - performance_report
```

### Parallel Configuration Options

| Parameter | Default | Description |
|-----------|---------|-------------|
| `strategy` | `threading` | Execution strategy: `threading`, `asyncio`, `process` |
| `max_workers` | `4` | Maximum concurrent tasks |
| `fail_fast` | `false` | Abort all tasks on first failure |
| `steps` | `[]` | List of sub-step configurations |

### Example 17: Dependencies with `depends_on`

Use `depends_on` to create execution order within parallel steps:

```yaml
steps:
  - id: parallel_pipeline
    type: parallel
    params:
      max_workers: 3
      steps:
        # These run concurrently (no dependencies)
        - id: security
          type: claude_code
          params:
            role: reviewer
            prompt: "Security analysis..."
          outputs:
            - security_report

        - id: performance
          type: claude_code
          params:
            role: analyst
            prompt: "Performance analysis..."
          outputs:
            - performance_report

        - id: maintainability
          type: claude_code
          params:
            role: reviewer
            prompt: "Code quality analysis..."
          outputs:
            - maintainability_report

        # This waits for all three above to complete
        - id: summary
          type: claude_code
          depends_on:
            - security
            - performance
            - maintainability
          params:
            role: reporter
            prompt: |
              Combine the analysis results:
              Security: ${security_report}
              Performance: ${performance_report}
              Maintainability: ${maintainability_report}
          outputs:
            - final_summary
```

### Dependency Patterns

```
┌─────────────────────────────────────────────┐
│              parallel_pipeline              │
│                                             │
│  ┌──────────┐ ┌───────────┐ ┌────────────┐ │
│  │ security │ │performance│ │maintainab. │ │  ← No deps, run concurrently
│  └────┬─────┘ └─────┬─────┘ └──────┬─────┘ │
│       │             │              │        │
│       └─────────────┼──────────────┘        │
│                     ▼                       │
│               ┌─────────┐                   │
│               │ summary │                   │  ← depends_on: [security, performance, maintainability]
│               └─────────┘                   │
└─────────────────────────────────────────────┘
```

### `depends_on` Syntax

```yaml
# Single dependency (string)
depends_on: security

# Multiple dependencies (list)
depends_on:
  - security
  - performance

# Inline list
depends_on: [security, performance, maintainability]
```

### Example 18: Complex Dependency Graph

```yaml
- id: parallel_build
  type: parallel
  params:
    steps:
      # Layer 1: Independent tasks
      - id: fetch_deps
        type: shell
        params:
          command: "pip install -r requirements.txt"

      - id: lint
        type: shell
        params:
          command: "ruff check ."

      # Layer 2: Depends on fetch_deps
      - id: build
        type: shell
        depends_on: fetch_deps
        params:
          command: "python -m build"

      - id: test
        type: shell
        depends_on: fetch_deps
        params:
          command: "pytest"

      # Layer 3: Depends on build and test
      - id: package
        type: shell
        depends_on:
          - build
          - test
        params:
          command: "tar -czf dist.tar.gz dist/"
```

Execution order:
1. `fetch_deps` and `lint` run concurrently
2. `build` and `test` start after `fetch_deps` completes
3. `package` starts after both `build` and `test` complete

### Example 19: Fail-Fast Mode

Stop all tasks when one fails:

```yaml
- id: critical_checks
  type: parallel
  params:
    fail_fast: true        # Abort on first failure
    max_workers: 4
    steps:
      - id: security_scan
        type: shell
        params:
          command: "bandit -r src/"

      - id: license_check
        type: shell
        params:
          command: "liccheck -s setup.cfg"

      - id: vulnerability_scan
        type: shell
        params:
          command: "safety check"
```

### Context and Output Sharing

Outputs from parallel sub-steps are merged into the workflow context:

```yaml
steps:
  - id: parallel_analysis
    type: parallel
    params:
      steps:
        - id: task_a
          type: claude_code
          params:
            prompt: "Generate report A"
          outputs:
            - report_a    # Available as ${report_a} after parallel step

        - id: task_b
          type: claude_code
          params:
            prompt: "Generate report B"
          outputs:
            - report_b    # Available as ${report_b} after parallel step

  # This step can use ${report_a} and ${report_b}
  - id: combine
    type: claude_code
    params:
      prompt: |
        Combine reports:
        Report A: ${report_a}
        Report B: ${report_b}
```

---

For more examples, see the [workflows directory](../workflows/) in the repository.
