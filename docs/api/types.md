# Types API

All type definitions used in pydantic-deep.

## File Types

### FileData

Storage format for file contents.

```python
class FileData(TypedDict):
    content: list[str]  # Lines of the file
    created_at: str     # ISO 8601 timestamp
    modified_at: str    # ISO 8601 timestamp
```

### FileInfo

File metadata for listings.

```python
class FileInfo(TypedDict):
    name: str           # File or directory name
    path: str           # Full path
    is_dir: bool        # True if directory
    size: int | None    # File size in bytes (None for directories)
```

---

## Operation Results

### WriteResult

Result of write operations.

```python
@dataclass
class WriteResult:
    path: str | None = None    # Path where file was written
    error: str | None = None   # Error message if failed
```

### EditResult

Result of edit operations.

```python
@dataclass
class EditResult:
    path: str | None = None      # Path of edited file
    error: str | None = None     # Error message if failed
    occurrences: int | None = None  # Number of replacements made
```

### ExecuteResponse

Result of command execution.

```python
@dataclass
class ExecuteResponse:
    output: str                 # stdout + stderr
    exit_code: int | None = None  # Process exit code
    truncated: bool = False     # True if output was truncated
```

### GrepMatch

Single grep match result.

```python
class GrepMatch(TypedDict):
    path: str         # File path
    line_number: int  # Line number (1-indexed)
    line: str         # Matching line content
```

---

## Todo Types

### Todo

Task item for planning.

```python
class Todo(BaseModel):
    content: str                                    # Task description
    status: Literal["pending", "in_progress", "completed"]
    active_form: str  # Present continuous form (e.g., "Implementing feature")
```

**Status Values:**

| Status | Description |
|--------|-------------|
| `pending` | Not yet started |
| `in_progress` | Currently working on |
| `completed` | Done |

---

## Subagent Types

### SubAgentConfig

Configuration for a subagent.

```python
class SubAgentConfig(TypedDict):
    name: str                      # Unique identifier
    description: str               # When to use this subagent
    instructions: str              # System prompt for subagent
    tools: NotRequired[list]       # Additional tools
    model: NotRequired[str]        # Custom model (overrides default)
```

### CompiledSubAgent

Pre-compiled subagent ready for use.

```python
class CompiledSubAgent(TypedDict):
    name: str
    description: str
    agent: NotRequired[object]  # Agent instance
```

---

## Skill Types

### Skill

Complete skill definition.

```python
class Skill(TypedDict):
    name: str                            # Unique identifier
    description: str                     # Brief description
    path: str                            # Path to skill directory
    tags: list[str]                      # Categorization tags
    version: str                         # Semantic version
    author: str                          # Skill author
    frontmatter_loaded: bool             # True if only frontmatter loaded
    instructions: NotRequired[str]       # Full instructions (loaded on demand)
    resources: NotRequired[list[str]]    # Additional files in skill directory
```

### SkillDirectory

Configuration for skill discovery.

```python
class SkillDirectory(TypedDict):
    path: str                           # Path to skills directory
    recursive: NotRequired[bool]        # Search recursively (default: True)
```

### SkillFrontmatter

YAML frontmatter from SKILL.md.

```python
class SkillFrontmatter(TypedDict):
    name: str
    description: str
    tags: NotRequired[list[str]]
    version: NotRequired[str]
    author: NotRequired[str]
```

---

## Usage Examples

### Creating a Todo

```python
from pydantic_deep import Todo

todo = Todo(
    content="Implement authentication",
    status="in_progress",
    active_form="Implementing authentication",
)
```

### Creating a SubAgentConfig

```python
from pydantic_deep import SubAgentConfig

config: SubAgentConfig = {
    "name": "code-reviewer",
    "description": "Reviews code for quality and security",
    "instructions": "You are an expert code reviewer...",
}
```

### Creating a Skill

```python
from pydantic_deep import Skill

skill: Skill = {
    "name": "api-design",
    "description": "Design RESTful APIs",
    "path": "/path/to/skill",
    "tags": ["api", "rest"],
    "version": "1.0.0",
    "author": "your-name",
    "frontmatter_loaded": True,
}
```

### Creating a SkillDirectory

```python
from pydantic_deep import SkillDirectory

dirs: list[SkillDirectory] = [
    {"path": "~/.pydantic-deep/skills", "recursive": True},
    {"path": "./project-skills", "recursive": False},
]
```

---

## Type Checking

All types support runtime checking:

```python
from pydantic_deep import Skill

def process_skill(skill: Skill) -> None:
    # Type checker knows all fields
    print(skill["name"])
    print(skill["description"])

    # Optional fields
    if "instructions" in skill:
        print(skill["instructions"])
```

Types are exported from the main module:

```python
from pydantic_deep import (
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
