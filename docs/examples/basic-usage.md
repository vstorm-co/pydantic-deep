# Basic Usage

This example demonstrates the fundamental features of pydantic-deep.

## Source Code

:material-file-code: `examples/basic_usage.py`

## Overview

This example shows:

- Creating a deep agent
- Using in-memory StateBackend
- Todo toolset for planning
- Filesystem toolset for file operations

## Full Example

```python
"""Basic usage example for pydantic-deep."""

import asyncio
from pydantic_deep import create_deep_agent, DeepAgentDeps, StateBackend


async def main():
    # Create a deep agent with default settings
    # This includes: TodoToolset, FilesystemToolset, SubAgentToolset, SkillsToolset
    agent = create_deep_agent(
        model="anthropic:claude-sonnet-4-20250514",
        instructions="""
        You are a helpful coding assistant.
        When given complex tasks, break them down using the todo list.
        """,
    )

    # Create dependencies with in-memory storage
    deps = DeepAgentDeps(backend=StateBackend())

    # Run the agent
    result = await agent.run(
        """
        Create a simple Python calculator module with:
        1. add, subtract, multiply, divide functions
        2. A main function that demonstrates usage
        3. Save it to /src/calculator.py
        """,
        deps=deps,
    )

    # Print the agent's response
    print("Agent Response:")
    print("=" * 50)
    print(result.output)

    # Check what files were created
    print("\nFiles Created:")
    print("=" * 50)
    for path in sorted(deps.backend.files.keys()):
        print(f"  {path}")

    # Show the content of created files
    for path in sorted(deps.backend.files.keys()):
        print(f"\n--- {path} ---")
        content = deps.backend.read(path)
        print(content)

    # Show the todo list state
    print("\nTodo List:")
    print("=" * 50)
    for todo in deps.todos:
        status_icon = {
            "pending": "[ ]",
            "in_progress": "[*]",
            "completed": "[x]",
        }.get(todo.status, "[ ]")
        print(f"  {status_icon} {todo.content}")

    # Show usage statistics
    usage = result.usage()
    print(f"\nUsage Statistics:")
    print(f"  Input tokens: {usage.input_tokens}")
    print(f"  Output tokens: {usage.output_tokens}")
    print(f"  Total requests: {usage.requests}")


if __name__ == "__main__":
    asyncio.run(main())
```

## Running the Example

```bash
export ANTHROPIC_API_KEY=your-api-key
uv run python examples/basic_usage.py
```

## Expected Output

```
Agent Response:
==================================================
I'll create a calculator module for you. Let me break this down...

Files Created:
==================================================
  /src/calculator.py

--- /src/calculator.py ---
     1  """Simple calculator module."""
     2
     3  def add(a: float, b: float) -> float:
     4      """Add two numbers."""
     5      return a + b
     6
     7  def subtract(a: float, b: float) -> float:
     8      """Subtract b from a."""
     9      return a - b
    10
    11  def multiply(a: float, b: float) -> float:
    12      """Multiply two numbers."""
    13      return a * b
    14
    15  def divide(a: float, b: float) -> float:
    16      """Divide a by b."""
    17      if b == 0:
    18          raise ValueError("Cannot divide by zero")
    19      return a / b
    20
    21  def main():
    22      """Demonstrate calculator usage."""
    23      print(f"10 + 5 = {add(10, 5)}")
    24      print(f"10 - 5 = {subtract(10, 5)}")
    25      print(f"10 * 5 = {multiply(10, 5)}")
    26      print(f"10 / 5 = {divide(10, 5)}")
    27
    28  if __name__ == "__main__":
    29      main()

Todo List:
==================================================
  [x] Create calculator module structure
  [x] Implement arithmetic functions
  [x] Add main demonstration function
  [x] Save to /src/calculator.py

Usage Statistics:
  Input tokens: 1234
  Output tokens: 567
  Total requests: 3
```

## Key Concepts

### Agent Creation

```python
agent = create_deep_agent(
    model="anthropic:claude-sonnet-4-20250514",  # LLM model
    instructions="...",                           # System prompt
)
```

The agent is created with all default toolsets enabled.

### Dependencies

```python
deps = DeepAgentDeps(backend=StateBackend())
```

- `StateBackend` stores files in memory
- `deps.backend.files` - Dictionary of all files
- `deps.todos` - List of todo items

### Running

```python
result = await agent.run(prompt, deps=deps)
```

- `result.output` - Agent's text response
- `result.usage()` - Token usage statistics
- `result.all_messages()` - Full conversation history

### Accessing Files

```python
# List all files
deps.backend.files.keys()

# Read a file (with line numbers)
deps.backend.read("/src/calculator.py")

# Write a file directly
deps.backend.write("/test.py", "print('hello')")
```

## Variations

### Without Planning

```python
agent = create_deep_agent(include_todo=False)
```

### With Custom Instructions

```python
agent = create_deep_agent(
    instructions="""
    You are a Python expert specializing in clean code.
    Always use type hints and docstrings.
    Follow PEP 8 style guidelines.
    """
)
```

### Testing Without API

```python
from pydantic_ai.models.test import TestModel

agent = create_deep_agent(model=TestModel())
```

## Next Steps

- [Filesystem Example](filesystem.md) - Real file operations
- [Skills Example](skills.md) - Using skills
- [Concepts: Agents](../concepts/agents.md) - Deep dive
