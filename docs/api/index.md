# API Reference

Complete API documentation for pydantic-deep.

## Modules

| Module | Description |
|--------|-------------|
| [`pydantic_deep.agent`](agent.md) | Agent factory and configuration |
| [`pydantic_deep.backends`](backends.md) | Storage backends |
| [`pydantic_deep.toolsets`](toolsets.md) | Tool collections |
| [`pydantic_deep.types`](types.md) | Type definitions |

## Quick Reference

### Main Entry Points

```python
from pydantic_deep import (
    # Agent
    create_deep_agent,
    create_default_deps,
    DeepAgentDeps,

    # Backends
    BackendProtocol,
    SandboxProtocol,
    StateBackend,
    FilesystemBackend,
    CompositeBackend,
    BaseSandbox,
    DockerSandbox,

    # Toolsets
    TodoToolset,
    FilesystemToolset,
    SubAgentToolset,
    SkillsToolset,

    # Types
    FileData,
    FileInfo,
    WriteResult,
    EditResult,
    ExecuteResponse,
    GrepMatch,
    Todo,
    SubAgentConfig,
    CompiledSubAgent,
    Skill,
    SkillDirectory,
    SkillFrontmatter,
)
```

### Creating an Agent

```python
agent = create_deep_agent(
    model="anthropic:claude-sonnet-4-20250514",
    instructions="You are a helpful assistant.",
    include_todo=True,
    include_filesystem=True,
    include_subagents=True,
    include_skills=True,
    subagents=[...],
    skills=[...],
    skill_directories=[...],
    interrupt_on={"execute": True},
)
```

### Creating Dependencies

```python
deps = DeepAgentDeps(
    backend=StateBackend(),
    todos=[],
    subagents={},
)

# Or use helper
deps = create_default_deps()
```

### Running

```python
# Basic run
result = await agent.run(prompt, deps=deps)

# With history
result = await agent.run(
    prompt,
    deps=deps,
    message_history=previous_result.all_messages(),
)

# Streaming
async with agent.iter(prompt, deps=deps) as run:
    async for node in run:
        ...
    result = run.result
```

## Type Annotations

pydantic-deep is fully typed. The main agent type is:

```python
Agent[DeepAgentDeps, str]
```

Where:

- `DeepAgentDeps` - Dependencies type
- `str` - Output type (agent returns strings)

## Protocols

### BackendProtocol

```python
class BackendProtocol(Protocol):
    def ls_info(self, path: str) -> list[FileInfo]: ...
    def read(self, path: str, offset: int = 0, limit: int = 2000) -> str: ...
    def write(self, path: str, content: str) -> WriteResult: ...
    def edit(self, path: str, old_string: str, new_string: str, replace_all: bool = False) -> EditResult: ...
    def glob_info(self, pattern: str, path: str = "/") -> list[FileInfo]: ...
    def grep_raw(self, pattern: str, path: str | None = None, glob: str | None = None) -> list[GrepMatch] | str: ...
```

### SandboxProtocol

```python
class SandboxProtocol(BackendProtocol, Protocol):
    def execute(self, command: str, timeout: int | None = None) -> ExecuteResponse: ...
    @property
    def id(self) -> str: ...
```

## Exceptions

pydantic-deep uses standard Python exceptions:

| Exception | When Raised |
|-----------|-------------|
| `ValueError` | Invalid arguments (bad paths, missing files) |
| `FileNotFoundError` | File doesn't exist |
| `PermissionError` | Path traversal attempt |
| `TimeoutError` | Execution timeout |

## Next Steps

- [Agent API](agent.md) - Detailed agent documentation
- [Backends API](backends.md) - Storage backend details
- [Toolsets API](toolsets.md) - Tool collection details
