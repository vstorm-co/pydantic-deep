# Docker Sandbox Example

This example demonstrates isolated code execution using DockerSandbox.

## Source Code

:material-file-code: `examples/docker_sandbox.py`

## Prerequisites

!!! warning "Docker Required"
    This example requires Docker to be installed and running.

```bash
# Install Docker: https://docs.docker.com/get-docker/

# Pull Python image
docker pull python:3.12-slim

# Install docker package
uv add pydantic-deep[sandbox]
```

## Overview

DockerSandbox provides:

- Isolated execution environment
- Safe code execution
- Container lifecycle management
- File operations within container

## Full Example

```python
"""Docker sandbox example for isolated code execution."""

import asyncio

from pydantic_deep import create_deep_agent, DeepAgentDeps
from pydantic_deep.backends.sandbox import DockerSandbox


async def main():
    # Create Docker sandbox
    sandbox = DockerSandbox(
        image="python:3.12-slim",
        work_dir="/workspace",
    )

    try:
        # Create agent with sandbox backend
        agent = create_deep_agent(
            model="anthropic:claude-sonnet-4-20250514",
            instructions="""
            You are a Python development assistant.
            You can write code, save it to files, and execute it.
            Always test your code by running it.
            """,
            # Require approval for execute (safety)
            interrupt_on={"execute": True},
        )

        deps = DeepAgentDeps(backend=sandbox)

        # Run the agent
        result = await agent.run(
            """
            Create a Python script that:
            1. Defines a function to calculate fibonacci numbers
            2. Prints the first 10 fibonacci numbers
            3. Save it to /workspace/fibonacci.py
            4. Run it and show the output
            """,
            deps=deps,
        )

        print(result.output)

    finally:
        # Always clean up the container
        sandbox.stop()


if __name__ == "__main__":
    asyncio.run(main())
```

## Sandbox Configuration

### Basic Setup

```python
sandbox = DockerSandbox(
    image="python:3.12-slim",  # Docker image
    work_dir="/workspace",      # Working directory in container
)
```

### Custom Configuration

```python
sandbox = DockerSandbox(
    image="python:3.12",
    work_dir="/app",
    # Additional options can be added to the implementation
)
```

## Execution

The `execute` tool runs commands inside the container:

```python
# Agent can call:
execute(command="python script.py", timeout=30)
```

Response includes:

```python
@dataclass
class ExecuteResponse:
    output: str        # stdout + stderr
    exit_code: int     # Process exit code
    truncated: bool    # True if output was truncated
```

## Human-in-the-Loop

Always require approval for execution:

```python
agent = create_deep_agent(
    interrupt_on={"execute": True},
)

result = await agent.run(prompt, deps=deps)

# Handle approval...
if hasattr(result, 'deferred_tool_calls'):
    for call in result.deferred_tool_calls:
        if call.tool_name == "execute":
            print(f"Command: {call.args['command']}")
            # Review and approve/deny
```

## Container Lifecycle

### Automatic Start

The container starts automatically on first operation:

```python
sandbox = DockerSandbox(image="python:3.12-slim")
sandbox.write("/test.py", "print('hello')")  # Starts container
```

### Manual Stop

Always stop the container when done:

```python
try:
    # Use sandbox...
finally:
    sandbox.stop()
```

Or use context manager pattern:

```python
async with DockerSandbox(...) as sandbox:
    # Use sandbox...
# Container automatically stopped
```

## File Operations

All standard file operations work inside the container:

```python
# Write file
sandbox.write("/workspace/app.py", "print('hello')")

# Read file
content = sandbox.read("/workspace/app.py")

# Edit file
sandbox.edit("/workspace/app.py", "hello", "world")

# List directory
files = sandbox.ls_info("/workspace")

# Glob pattern
python_files = sandbox.glob_info("**/*.py", "/workspace")

# Search content
matches = sandbox.grep_raw("def main", "/workspace")
```

## Security Considerations

!!! danger "Security Warning"
    Even with Docker isolation, be cautious about:

    - Network access from container
    - Resource consumption
    - Malicious code execution
    - Container escape vulnerabilities

### Best Practices

1. **Always require approval** for `execute`
2. **Use minimal images** (slim variants)
3. **Set timeouts** on execution
4. **Review commands** before approval
5. **Clean up containers** after use

## Error Handling

```python
try:
    result = sandbox.execute("python script.py", timeout=30)
    if result.exit_code != 0:
        print(f"Script failed: {result.output}")
except TimeoutError:
    print("Execution timed out")
except Exception as e:
    print(f"Error: {e}")
finally:
    sandbox.stop()
```

## Alternative: LocalSandbox

For development/testing without Docker:

```python
from pydantic_deep.backends.sandbox import LocalSandbox

# Executes on local machine (DANGEROUS in production!)
sandbox = LocalSandbox(work_dir="/tmp/workspace")
```

!!! warning
    LocalSandbox runs commands on your actual machine with no isolation.
    Only use for trusted code in development.

## Running the Example

```bash
# Ensure Docker is running
docker ps

# Run example
uv run python examples/docker_sandbox.py
```

## Expected Output

```
Note: This example requires Docker to be installed and running.

Agent Response:
==================================================
I'll create a fibonacci script for you...

[Approval prompt for execute command]

Running: python /workspace/fibonacci.py

Output:
0, 1, 1, 2, 3, 5, 8, 13, 21, 34

The script successfully calculated and printed the first 10 Fibonacci numbers.
```

## Next Steps

- [Concepts: Backends](../concepts/backends.md) - Deep dive
- [Human-in-the-Loop](../advanced/human-in-the-loop.md) - Approval workflows
- [API Reference](../api/backends.md) - SandboxProtocol API
