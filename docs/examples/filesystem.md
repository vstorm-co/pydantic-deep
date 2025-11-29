# Filesystem Example

This example demonstrates working with real files using FilesystemBackend and CompositeBackend.

## FilesystemBackend

### Source Code

:material-file-code: `examples/filesystem_backend.py`

### Overview

```python
"""Working with real files on disk."""

import asyncio
import tempfile
from pathlib import Path

from pydantic_deep import (
    create_deep_agent,
    DeepAgentDeps,
    FilesystemBackend,
)


async def main():
    # Create a temporary workspace
    with tempfile.TemporaryDirectory() as workspace:
        print(f"Workspace: {workspace}")

        # Create backend pointing to real filesystem
        # virtual_mode=True tracks changes without persisting (safe for demos)
        backend = FilesystemBackend(workspace, virtual_mode=True)

        agent = create_deep_agent()
        deps = DeepAgentDeps(backend=backend)

        result = await agent.run(
            """
            Create a Python project structure:
            1. src/app.py - Main application
            2. src/utils.py - Utility functions
            3. tests/test_app.py - Test file
            4. README.md - Project description
            """,
            deps=deps,
        )

        print(result.output)

        # Check what was created
        print("\nFiles created:")
        for path in Path(workspace).rglob("*"):
            if path.is_file():
                print(f"  {path.relative_to(workspace)}")


asyncio.run(main())
```

### Virtual Mode

Virtual mode tracks file operations without actually writing to disk:

```python
# Writes go to virtual storage
backend = FilesystemBackend(workspace, virtual_mode=True)

# Writes go to actual filesystem
backend = FilesystemBackend(workspace, virtual_mode=False)
```

This is useful for:

- Testing without side effects
- Previewing changes before applying
- Safe demonstrations

## CompositeBackend

### Source Code

:material-file-code: `examples/composite_backend.py`

### Overview

Route operations to different backends by path prefix:

```python
"""Mixed storage strategies with CompositeBackend."""

import asyncio
import tempfile
from pathlib import Path

from pydantic_deep import (
    create_deep_agent,
    DeepAgentDeps,
    StateBackend,
    FilesystemBackend,
    CompositeBackend,
)


async def main():
    with tempfile.TemporaryDirectory() as workspace:
        # Create backends:
        # - StateBackend for temporary scratch files
        # - FilesystemBackend for persistent project files
        memory = StateBackend()
        filesystem = FilesystemBackend(workspace, virtual_mode=True)

        # Route by path prefix
        backend = CompositeBackend(
            default=memory,  # Unmatched paths go here
            routes={
                "/project/": filesystem,    # Project files to disk
                "/workspace/": filesystem,  # Workspace files to disk
                # /temp/, /scratch/ go to memory (default)
            },
        )

        agent = create_deep_agent()
        deps = DeepAgentDeps(backend=backend)

        result = await agent.run(
            """
            Create files in different locations:
            1. /project/src/app.py - Persistent application code
            2. /project/README.md - Persistent documentation
            3. /scratch/notes.txt - Temporary notes (in memory)
            """,
            deps=deps,
        )

        print(result.output)

        # Show what's where
        print("\nIn memory (temporary):")
        for path in memory.files.keys():
            print(f"  {path}")

        print("\nOn filesystem (persistent):")
        for path in Path(workspace).rglob("*"):
            if path.is_file():
                print(f"  {path.relative_to(workspace)}")


asyncio.run(main())
```

### Use Cases

| Pattern | Use Case |
|---------|----------|
| Memory default + Filesystem routes | Scratch space + persistent output |
| Multiple filesystem routes | Multi-project workspace |
| Docker route + Filesystem route | Execute code + persist results |

## Glob and Grep

Find and search files:

```python
# Find all Python files
matches = backend.glob_info("**/*.py", path="/project")
for match in matches:
    print(f"{match['path']} ({match['size']} bytes)")

# Search for function definitions
results = backend.grep_raw(r"def \w+\(", path="/project/src")
for result in results:
    print(f"{result['path']}:{result['line_number']}: {result['line']}")
```

## Reading with Offsets

For large files, read specific portions:

```python
# Read lines 100-200
content = backend.read("/large_file.py", offset=99, limit=100)
```

## Edit Operations

Replace strings in files:

```python
# Replace single occurrence
result = backend.edit(
    "/src/app.py",
    old_string="old_function",
    new_string="new_function",
)

# Replace all occurrences
result = backend.edit(
    "/src/app.py",
    old_string="TODO",
    new_string="DONE",
    replace_all=True,
)

print(f"Replaced {result.occurrences} occurrences")
```

## Running the Examples

```bash
# Filesystem backend
uv run python examples/filesystem_backend.py

# Composite backend
uv run python examples/composite_backend.py
```

## Next Steps

- [Docker Sandbox](docker-sandbox.md) - Isolated execution
- [Skills Example](skills.md) - Using skills
- [Concepts: Backends](../concepts/backends.md) - Deep dive
