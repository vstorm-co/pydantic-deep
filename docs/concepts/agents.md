# Agents

The `create_deep_agent()` function is the main entry point for creating deep agents.

## Basic Usage

```python
from pydantic_deep import create_deep_agent, DeepAgentDeps, StateBackend

# Create agent with defaults
agent = create_deep_agent()

# Run with dependencies
deps = DeepAgentDeps(backend=StateBackend())
result = await agent.run("Hello!", deps=deps)
```

## Configuration Options

### Model Selection

```python
# Anthropic (default)
agent = create_deep_agent(model="anthropic:claude-sonnet-4-20250514")

# OpenAI
agent = create_deep_agent(model="openai:gpt-4")

# For testing (no API calls)
from pydantic_ai.models.test import TestModel
agent = create_deep_agent(model=TestModel())
```

### Custom Instructions

```python
agent = create_deep_agent(
    instructions="""
    You are a Python expert specializing in data science.

    When writing code:
    - Use type hints
    - Include docstrings
    - Prefer pandas for data manipulation
    """
)
```

### Enabling/Disabling Features

```python
agent = create_deep_agent(
    include_todo=True,        # Planning tools (default: True)
    include_filesystem=True,  # File operations (default: True)
    include_subagents=True,   # Task delegation (default: True)
    include_skills=True,      # Skill packages (default: True)
)
```

### Human-in-the-Loop

Require approval for sensitive operations:

```python
agent = create_deep_agent(
    interrupt_on={
        "execute": True,      # Require approval for command execution
        "write_file": True,   # Require approval for file writes
        "edit_file": True,    # Require approval for file edits
    }
)
```

## Dependencies

The `DeepAgentDeps` class holds all runtime state:

```python
from dataclasses import dataclass
from pydantic_deep import BackendProtocol, Todo

@dataclass
class DeepAgentDeps:
    backend: BackendProtocol  # File storage
    files: dict[str, FileData]  # File cache
    todos: list[Todo]  # Task list
    subagents: dict[str, Any]  # Preconfigured agents
```

### Creating Dependencies

```python
# Simple - in-memory storage
deps = DeepAgentDeps(backend=StateBackend())

# With filesystem storage
deps = DeepAgentDeps(backend=FilesystemBackend("/workspace"))

# With initial todos
from pydantic_deep import Todo
deps = DeepAgentDeps(
    backend=StateBackend(),
    todos=[
        Todo(content="Review code", status="pending", active_form="Reviewing code"),
    ]
)
```

## Running Agents

### Basic Run

```python
result = await agent.run("Create a calculator module", deps=deps)
print(result.output)  # Agent's text response
```

### Streaming

```python
from pydantic_ai._agent_graph import CallToolsNode

async with agent.iter("Create a calculator", deps=deps) as run:
    async for node in run:
        if isinstance(node, CallToolsNode):
            # Get tool calls from the response
            for part in node.model_response.parts:
                if hasattr(part, 'tool_name'):
                    print(f"Calling: {part.tool_name}")

    result = run.result
```

### Continuing Conversations

```python
# First interaction
result1 = await agent.run("Create a file", deps=deps)

# Continue with history
result2 = await agent.run(
    "Now modify it",
    deps=deps,
    message_history=result1.all_messages(),
)
```

## Adding Custom Tools

### Function Tools

```python
from pydantic_ai import RunContext

async def get_weather(
    ctx: RunContext[DeepAgentDeps],
    city: str,
) -> str:
    """Get current weather for a city.

    Args:
        city: Name of the city.

    Returns:
        Weather description.
    """
    return f"Weather in {city}: Sunny, 22°C"

agent = create_deep_agent(tools=[get_weather])
```

### Accessing Dependencies in Tools

```python
async def save_report(
    ctx: RunContext[DeepAgentDeps],
    content: str,
) -> str:
    """Save a report to the filesystem."""
    # Access the backend through dependencies
    result = ctx.deps.backend.write("/reports/latest.md", content)
    return f"Saved to {result.path}"
```

## Subagent Configuration

Pre-configure specialized subagents:

```python
from pydantic_deep import SubAgentConfig

subagents = [
    SubAgentConfig(
        name="code-reviewer",
        description="Reviews code for quality and security issues",
        instructions="""
        You are an expert code reviewer. Focus on:
        - Security vulnerabilities
        - Performance issues
        - Code style
        """,
    ),
    SubAgentConfig(
        name="test-writer",
        description="Generates pytest test cases",
        instructions="Generate comprehensive pytest tests...",
    ),
]

agent = create_deep_agent(subagents=subagents)
```

The main agent can then delegate:

```python
# Agent can call: task(description="Review the calculator module", subagent_type="code-reviewer")
```

## Skills Configuration

Load skills from directories:

```python
agent = create_deep_agent(
    skill_directories=[
        {"path": "~/.pydantic-deep/skills", "recursive": True},
        {"path": "./project-skills", "recursive": False},
    ]
)
```

Or provide skills directly:

```python
skills = [
    {
        "name": "code-review",
        "description": "Review code for quality",
        "path": "/path/to/skill",
        "tags": ["code", "review"],
        "version": "1.0.0",
        "author": "",
        "frontmatter_loaded": True,
    }
]

agent = create_deep_agent(skills=skills)
```

## Usage Statistics

```python
result = await agent.run("Create a module", deps=deps)

usage = result.usage()
print(f"Input tokens: {usage.input_tokens}")
print(f"Output tokens: {usage.output_tokens}")
print(f"Total requests: {usage.requests}")
```

## Error Handling

```python
try:
    result = await agent.run(prompt, deps=deps)
except Exception as e:
    print(f"Agent error: {e}")
```

## Next Steps

- [Backends](backends.md) - Storage options
- [Toolsets](toolsets.md) - Available tools
- [Skills](skills.md) - Modular capabilities
