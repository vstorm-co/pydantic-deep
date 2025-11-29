# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Core Development Tasks

- **Install dependencies**: `make install` (requires uv and pre-commit)
- **Run all checks**: `make all` or `pre-commit run --all-files`
- **Run tests**: `make test`
- **Build docs**: `make docs` or `make docs-serve` (local development)

### Single Test Commands

- **Run specific test**: `uv run pytest tests/test_agent.py::test_function_name -v`
- **Run test file**: `uv run pytest tests/test_agent.py -v`
- **Run with debug**: `uv run pytest tests/test_agent.py -v -s`

## Project Architecture

### Core Components

**Agent Factory (`pydantic_deep/agent.py`)**
- `create_deep_agent()`: Main factory function for creating configured agents
- `create_default_deps()`: Helper for creating DeepAgentDeps with sensible defaults
- Built on top of pydantic-ai's Agent class

**Dependencies (`pydantic_deep/deps.py`)**
- `DeepAgentDeps`: Dataclass holding agent dependencies (backend, working_dir, skills_dirs, subagents)
- Passed to agent.run() for runtime configuration

**Backends (`pydantic_deep/backends/`)**
- `BackendProtocol`: Interface for file storage backends
- `StateBackend`: In-memory file storage (for testing, ephemeral use)
- `FilesystemBackend`: Real filesystem operations
- `DockerSandbox`: Isolated Docker container execution
- `CompositeBackend`: Combines multiple backends with routing

**Toolsets (`pydantic_deep/toolsets/`)**
- `TodoToolset`: Task planning and tracking tools (read_todos, write_todos)
- `FilesystemToolset`: File operations (read, write, edit, glob, grep, mkdir, execute)
- `SubAgentToolset`: Spawn and delegate to subagents
- `SkillsToolset`: Load and use skill definitions from markdown files

**Types (`pydantic_deep/types.py`)**
- Pydantic models for all data structures
- `FileData`, `FileInfo`, `WriteResult`, `EditResult`, `GrepMatch`
- `Todo`, `SubAgentConfig`, `CompiledSubAgent`
- `Skill`, `SkillDirectory`, `SkillFrontmatter`

### Key Design Patterns

**Backend Abstraction**
```python
from pydantic_deep import StateBackend, FilesystemBackend, CompositeBackend

# In-memory for testing
backend = StateBackend()

# Real filesystem
backend = FilesystemBackend(root="/path/to/workspace")

# Combined backends
backend = CompositeBackend(backends=[StateBackend(), FilesystemBackend()])
```

**Toolset Registration**
```python
from pydantic_deep import create_deep_agent, DeepAgentDeps
from pydantic_deep.toolsets import TodoToolset, FilesystemToolset

agent = create_deep_agent(
    model="anthropic:claude-sonnet-4-20250514",
    toolsets=[TodoToolset(), FilesystemToolset()],
)
```

**Skills System**
```python
# Skills are markdown files with YAML frontmatter
# Located in skills_dirs specified in DeepAgentDeps
deps = DeepAgentDeps(
    backend=StateBackend(),
    skills_dirs=["/path/to/skills"],
)
```

## Testing Strategy

- **Unit tests**: `tests/` directory with comprehensive coverage
- **Test models**: Use `TestModel` from pydantic-ai for deterministic testing
- **Async testing**: pytest-asyncio with `asyncio_mode = "auto"`
- **Coverage requirement**: 100% coverage is required for all PRs

## Key Configuration Files

- **`pyproject.toml`**: Main configuration (dependencies, tools, coverage)
- **`Makefile`**: Development task automation
- **`mkdocs.yml`**: Documentation configuration
- **`.pre-commit-config.yaml`**: Pre-commit hook configuration

## Important Implementation Notes

- **Backend Protocol**: All backends implement `BackendProtocol` for consistent file operations
- **Async-First**: Most operations are async, use `await` appropriately
- **Type Safety**: Full type annotations with Pyright strict mode
- **Sandbox Support**: DockerSandbox requires `docker` optional dependency

## Documentation Development

- **Local docs**: `make docs-serve` (serves at http://localhost:8000)
- **Docs source**: `docs/` directory (MkDocs with Material theme)
- **API reference**: Auto-generated from docstrings using mkdocstrings

## Dependencies Management

- **Package manager**: uv (fast Python package manager)
- **Lock file**: `uv.lock` (commit this file)
- **Sync command**: `make sync` to update dependencies
- **Optional extras**: sandbox, cli, dev

## Best Practices

### Coverage

Every pull request MUST have 100% coverage. You can check the coverage by running `make test`.

Use `# pragma: no cover` for legitimately untestable code (e.g., platform-specific branches).

### Type Annotations

All code must pass both Pyright and MyPy strict checking:
- `make typecheck` for Pyright
- `make typecheck-mypy` for MyPy

### Writing Documentation

Always reference Python objects with backticks and link to API reference:

```markdown
The [`create_deep_agent`][pydantic_deep.agent.create_deep_agent] function creates a configured agent.
```

### Rename a Class

When renaming a class, add deprecation warning:

```python
from typing_extensions import deprecated

class NewClass: ...

@deprecated("Use `NewClass` instead.")
class OldClass(NewClass): ...
```
