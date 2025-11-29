# Toolsets API

## TodoToolset

Task planning and tracking tools.

### Tools

| Tool | Description |
|------|-------------|
| `write_todos` | Update the todo list |

### Factory

```python
def create_todo_toolset(
    *,
    id: str = "todo",
) -> TodoToolset
```

### Tool: write_todos

```python
async def write_todos(
    ctx: RunContext[DeepAgentDeps],
    todos: list[dict],
) -> str
```

Update the todo list with new items.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `todos` | `list[dict]` | List of todo items |

Each todo item:
```python
{
    "content": str,      # Task description
    "status": str,       # "pending", "in_progress", "completed"
    "active_form": str,  # Present continuous form
}
```

**Returns:** Confirmation message.

### System Prompt

```python
def get_todo_system_prompt(deps: DeepAgentDeps) -> str
```

Generates dynamic system prompt showing current todos.

---

## FilesystemToolset

File operation tools.

### Tools

| Tool | Description |
|------|-------------|
| `ls` | List directory contents |
| `read_file` | Read file with line numbers |
| `write_file` | Create or overwrite file |
| `edit_file` | Replace strings in file |
| `glob` | Find files by pattern |
| `grep` | Search file contents |
| `execute` | Run shell command (sandbox only) |

### Factory

```python
def create_filesystem_toolset(
    *,
    id: str = "filesystem",
    include_execute: bool = False,
    require_write_approval: bool = False,
    require_execute_approval: bool = True,
) -> FilesystemToolset
```

### Tool: ls

```python
async def ls(
    ctx: RunContext[DeepAgentDeps],
    path: str = "/",
) -> str
```

List directory contents.

**Returns:** Formatted directory listing.

### Tool: read_file

```python
async def read_file(
    ctx: RunContext[DeepAgentDeps],
    path: str,
    offset: int = 0,
    limit: int = 2000,
) -> str
```

Read file contents with line numbers.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `path` | `str` | Required | File path |
| `offset` | `int` | `0` | Starting line (0-indexed) |
| `limit` | `int` | `2000` | Maximum lines |

**Returns:** File content with line numbers.

### Tool: write_file

```python
async def write_file(
    ctx: RunContext[DeepAgentDeps],
    path: str,
    content: str,
) -> str
```

Create or overwrite a file.

**Returns:** Confirmation or error message.

### Tool: edit_file

```python
async def edit_file(
    ctx: RunContext[DeepAgentDeps],
    path: str,
    old_string: str,
    new_string: str,
    replace_all: bool = False,
) -> str
```

Replace strings in a file.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `path` | `str` | Required | File path |
| `old_string` | `str` | Required | String to replace |
| `new_string` | `str` | Required | Replacement string |
| `replace_all` | `bool` | `False` | Replace all occurrences |

**Returns:** Confirmation with occurrence count.

### Tool: glob

```python
async def glob(
    ctx: RunContext[DeepAgentDeps],
    pattern: str,
    path: str = "/",
) -> str
```

Find files matching glob pattern.

**Returns:** List of matching files.

### Tool: grep

```python
async def grep(
    ctx: RunContext[DeepAgentDeps],
    pattern: str,
    path: str | None = None,
    file_glob: str | None = None,
) -> str
```

Search file contents with regex.

**Returns:** Matching lines with context.

### Tool: execute

```python
async def execute(
    ctx: RunContext[DeepAgentDeps],
    command: str,
    timeout: int = 30,
) -> str
```

Execute a shell command (sandbox only).

**Returns:** Command output or error.

---

## SubAgentToolset

Task delegation tools.

### Tools

| Tool | Description |
|------|-------------|
| `task` | Spawn a subagent for a task |

### Factory

```python
def create_subagent_toolset(
    *,
    id: str = "subagents",
    subagents: list[SubAgentConfig] | None = None,
    default_model: str | None = None,
    include_general_purpose: bool = True,
) -> SubAgentToolset
```

### Tool: task

```python
async def task(
    ctx: RunContext[DeepAgentDeps],
    description: str,
    subagent_type: str = "general-purpose",
) -> str
```

Spawn a subagent to handle a task.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `description` | `str` | Required | Task description |
| `subagent_type` | `str` | `"general-purpose"` | Subagent name |

**Returns:** Subagent's output.

### SubAgentConfig

```python
class SubAgentConfig(TypedDict):
    name: str                    # Unique identifier
    description: str             # When to use this subagent
    instructions: str            # System prompt
    tools: NotRequired[list]     # Additional tools
    model: NotRequired[str]      # Custom model
```

---

## SkillsToolset

Modular capability tools.

### Tools

| Tool | Description |
|------|-------------|
| `list_skills` | List available skills |
| `load_skill` | Load skill instructions |
| `read_skill_resource` | Read skill resource file |

### Factory

```python
def create_skills_toolset(
    *,
    id: str = "skills",
    directories: list[SkillDirectory] | None = None,
    skills: list[Skill] | None = None,
) -> SkillsToolset
```

### Tool: list_skills

```python
async def list_skills(
    ctx: RunContext[DeepAgentDeps],
) -> str
```

List all available skills.

**Returns:** Formatted list of skills with metadata.

### Tool: load_skill

```python
async def load_skill(
    ctx: RunContext[DeepAgentDeps],
    skill_name: str,
) -> str
```

Load full instructions for a skill.

**Returns:** Complete skill instructions.

### Tool: read_skill_resource

```python
async def read_skill_resource(
    ctx: RunContext[DeepAgentDeps],
    skill_name: str,
    resource_name: str,
) -> str
```

Read a resource file from a skill.

**Returns:** Resource file content.

### Type Definitions

#### Skill

```python
class Skill(TypedDict):
    name: str
    description: str
    path: str
    tags: list[str]
    version: str
    author: str
    frontmatter_loaded: bool
    instructions: NotRequired[str]
    resources: NotRequired[list[str]]
```

#### SkillDirectory

```python
class SkillDirectory(TypedDict):
    path: str
    recursive: NotRequired[bool]
```

#### SkillFrontmatter

```python
class SkillFrontmatter(TypedDict):
    name: str
    description: str
    tags: NotRequired[list[str]]
    version: NotRequired[str]
    author: NotRequired[str]
```

---

## Helper Functions

### discover_skills

```python
def discover_skills(
    directories: list[SkillDirectory],
    backend: Any | None = None,
) -> list[Skill]
```

Discover skills from filesystem directories.

### parse_skill_md

```python
def parse_skill_md(content: str) -> tuple[dict[str, Any], str]
```

Parse SKILL.md into frontmatter and instructions.

### load_skill_instructions

```python
def load_skill_instructions(skill_path: str) -> str
```

Load full instructions from a skill directory.
