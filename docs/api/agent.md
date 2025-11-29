# Agent API

## create_deep_agent

::: pydantic_deep.agent.create_deep_agent
    options:
      show_source: false

### Signature

```python
def create_deep_agent(
    model: str | None = None,
    instructions: str | None = None,
    tools: Sequence[Tool[DeepAgentDeps] | Any] | None = None,
    toolsets: Sequence[AbstractToolset[DeepAgentDeps]] | None = None,
    subagents: list[SubAgentConfig] | None = None,
    skills: list[Skill] | None = None,
    skill_directories: list[SkillDirectory] | None = None,
    backend: BackendProtocol | None = None,
    include_todo: bool = True,
    include_filesystem: bool = True,
    include_subagents: bool = True,
    include_skills: bool = True,
    include_general_purpose_subagent: bool = True,
    interrupt_on: dict[str, bool] | None = None,
    **agent_kwargs: Any,
) -> Agent[DeepAgentDeps, str]
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | `str \| None` | `"anthropic:claude-sonnet-4-20250514"` | LLM model identifier |
| `instructions` | `str \| None` | Default instructions | System prompt for the agent |
| `tools` | `Sequence[Tool \| Any] \| None` | `None` | Additional custom tools |
| `toolsets` | `Sequence[AbstractToolset] \| None` | `None` | Additional toolsets |
| `subagents` | `list[SubAgentConfig] \| None` | `None` | Subagent configurations |
| `skills` | `list[Skill] \| None` | `None` | Pre-loaded skills |
| `skill_directories` | `list[SkillDirectory] \| None` | `None` | Directories to discover skills |
| `backend` | `BackendProtocol \| None` | `StateBackend()` | File storage backend |
| `include_todo` | `bool` | `True` | Include TodoToolset |
| `include_filesystem` | `bool` | `True` | Include FilesystemToolset |
| `include_subagents` | `bool` | `True` | Include SubAgentToolset |
| `include_skills` | `bool` | `True` | Include SkillsToolset |
| `include_general_purpose_subagent` | `bool` | `True` | Include general-purpose subagent |
| `interrupt_on` | `dict[str, bool] \| None` | `None` | Tools requiring approval |
| `**agent_kwargs` | `Any` | - | Additional Agent constructor args |

### Returns

`Agent[DeepAgentDeps, str]` - Configured Pydantic AI agent.

### Example

```python
from pydantic_deep import create_deep_agent, SubAgentConfig

agent = create_deep_agent(
    model="anthropic:claude-sonnet-4-20250514",
    instructions="You are a coding assistant.",
    subagents=[
        SubAgentConfig(
            name="reviewer",
            description="Reviews code",
            instructions="Review code for issues.",
        ),
    ],
    skill_directories=[
        {"path": "~/.pydantic-deep/skills", "recursive": True},
    ],
    interrupt_on={"execute": True},
)
```

---

## create_default_deps

::: pydantic_deep.agent.create_default_deps
    options:
      show_source: false

### Signature

```python
def create_default_deps(
    backend: BackendProtocol | None = None,
) -> DeepAgentDeps
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `backend` | `BackendProtocol \| None` | `StateBackend()` | File storage backend |

### Returns

`DeepAgentDeps` - Configured dependencies instance.

### Example

```python
from pydantic_deep import create_default_deps, FilesystemBackend

# With default StateBackend
deps = create_default_deps()

# With custom backend
deps = create_default_deps(backend=FilesystemBackend("/workspace"))
```

---

## DeepAgentDeps

::: pydantic_deep.deps.DeepAgentDeps
    options:
      show_source: false

### Definition

```python
@dataclass
class DeepAgentDeps:
    backend: BackendProtocol = field(default_factory=StateBackend)
    files: dict[str, FileData] = field(default_factory=dict)
    todos: list[Todo] = field(default_factory=list)
    subagents: dict[str, Any] = field(default_factory=dict)
```

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `backend` | `BackendProtocol` | File storage backend |
| `files` | `dict[str, FileData]` | In-memory file cache |
| `todos` | `list[Todo]` | Task list |
| `subagents` | `dict[str, Any]` | Pre-configured subagent instances |

### Methods

#### get_todo_prompt

```python
def get_todo_prompt(self) -> str
```

Generate system prompt section for current todos.

#### get_files_summary

```python
def get_files_summary(self) -> str
```

Generate summary of files in memory.

#### get_subagents_summary

```python
def get_subagents_summary(self) -> str
```

Generate summary of available subagents.

#### clone_for_subagent

```python
def clone_for_subagent(self) -> DeepAgentDeps
```

Create isolated dependencies for a subagent.

- Same backend (shared)
- Empty todos (isolated)
- Empty subagents (no nested delegation)
- Same files (shared reference)

### Example

```python
from pydantic_deep import DeepAgentDeps, StateBackend, Todo

deps = DeepAgentDeps(
    backend=StateBackend(),
    todos=[
        Todo(
            content="Review code",
            status="pending",
            active_form="Reviewing code",
        ),
    ],
)

# Access todo prompt
print(deps.get_todo_prompt())

# Clone for subagent
subagent_deps = deps.clone_for_subagent()
assert subagent_deps.todos == []  # Isolated
assert subagent_deps.backend is deps.backend  # Shared
```
