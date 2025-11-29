# Examples

This section contains practical examples demonstrating pydantic-deep features.

## Running Examples

All examples are in the `examples/` directory:

```bash
# Set your API key
export ANTHROPIC_API_KEY=your-api-key

# Run an example
uv run python examples/<example_name>.py
```

## Example Overview

<div class="feature-grid">

<div class="feature-card">
<h3>📖 Basic Usage</h3>
<p>Getting started with pydantic-deep. Create agents, use todos, work with files.</p>
<a href="basic-usage/">View Example →</a>
</div>

<div class="feature-card">
<h3>📁 Filesystem</h3>
<p>Real filesystem operations with FilesystemBackend and CompositeBackend.</p>
<a href="filesystem/">View Example →</a>
</div>

<div class="feature-card">
<h3>🎯 Skills</h3>
<p>Modular capability packages with progressive disclosure.</p>
<a href="skills/">View Example →</a>
</div>

<div class="feature-card">
<h3>🐳 Docker Sandbox</h3>
<p>Isolated code execution in Docker containers.</p>
<a href="docker-sandbox/">View Example →</a>
</div>

</div>

## Quick Examples

### Hello World

```python
import asyncio
from pydantic_deep import create_deep_agent, DeepAgentDeps, StateBackend

async def main():
    agent = create_deep_agent()
    deps = DeepAgentDeps(backend=StateBackend())

    result = await agent.run("Say hello!", deps=deps)
    print(result.output)

asyncio.run(main())
```

### Create a File

```python
async def main():
    agent = create_deep_agent()
    deps = DeepAgentDeps(backend=StateBackend())

    result = await agent.run(
        "Create a Python function that calculates factorials and save it to /math/factorial.py",
        deps=deps,
    )

    # Check what was created
    print("Files:", list(deps.backend.files.keys()))
    print("\nContent:")
    print(deps.backend.read("/math/factorial.py"))
```

### Plan a Task

```python
async def main():
    agent = create_deep_agent()
    deps = DeepAgentDeps(backend=StateBackend())

    result = await agent.run(
        """
        Create a simple CLI calculator with the following features:
        1. Add, subtract, multiply, divide
        2. Input validation
        3. Help command

        Plan the task first using todos, then implement.
        """,
        deps=deps,
    )

    # Check the todo list
    print("Todos:")
    for todo in deps.todos:
        status = "✓" if todo.status == "completed" else "○"
        print(f"  {status} {todo.content}")
```

### Delegate to Subagent

```python
from pydantic_deep import SubAgentConfig

async def main():
    subagents = [
        SubAgentConfig(
            name="code-reviewer",
            description="Reviews code for quality",
            instructions="You are a code review expert...",
        ),
    ]

    agent = create_deep_agent(subagents=subagents)
    deps = DeepAgentDeps(backend=StateBackend())

    # Create some code
    deps.backend.write("/src/app.py", "def add(a, b): return a + b")

    result = await agent.run(
        "Delegate a code review of /src/app.py to the code-reviewer",
        deps=deps,
    )

    print(result.output)
```

### Use Skills

```python
async def main():
    agent = create_deep_agent(
        skill_directories=[
            {"path": "./skills", "recursive": True},
        ],
    )
    deps = DeepAgentDeps(backend=StateBackend())

    result = await agent.run(
        """
        1. List available skills
        2. Load the code-review skill
        3. Use it to review /src/app.py
        """,
        deps=deps,
    )

    print(result.output)
```

## Testing Without API

Use `TestModel` for testing without API calls:

```python
from pydantic_ai.models.test import TestModel

async def main():
    agent = create_deep_agent(model=TestModel())
    deps = DeepAgentDeps(backend=StateBackend())

    # TestModel will return predefined responses
    result = await agent.run("Test prompt", deps=deps)
```

## Example Files

| File | Description |
|------|-------------|
| `basic_usage.py` | Core functionality demonstration |
| `filesystem_backend.py` | Real filesystem operations |
| `subagents.py` | Task delegation |
| `human_in_the_loop.py` | Approval workflows |
| `docker_sandbox.py` | Isolated execution |
| `composite_backend.py` | Mixed storage strategies |
| `streaming.py` | Real-time output |
| `custom_tools.py` | Adding custom tools |
| `skills_usage.py` | Skills system |

## Next Steps

- [Basic Usage](basic-usage.md) - Detailed walkthrough
- [Core Concepts](../concepts/index.md) - Understand the fundamentals
- [API Reference](../api/index.md) - Complete API documentation
