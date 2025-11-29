# Toolsets

Toolsets are collections of tools that extend agent capabilities. pydantic-deep includes four built-in toolsets.

## Built-in Toolsets

### TodoToolset

Task planning and tracking.

| Tool | Description |
|------|-------------|
| `write_todos` | Update the todo list with tasks and statuses |

```python
# Agent can call:
write_todos(todos=[
    {"content": "Create module", "status": "in_progress", "active_form": "Creating module"},
    {"content": "Write tests", "status": "pending", "active_form": "Writing tests"},
])
```

**Todo Status Values:**

- `pending` - Not started
- `in_progress` - Currently working
- `completed` - Done

### FilesystemToolset

File operations using the configured backend.

| Tool | Description |
|------|-------------|
| `ls` | List directory contents |
| `read_file` | Read file with line numbers |
| `write_file` | Create or overwrite file |
| `edit_file` | Replace strings in file |
| `glob` | Find files by pattern |
| `grep` | Search file contents |
| `execute` | Run shell command (sandbox only) |

```python
# Agent can call:
ls(path="/src")
read_file(path="/src/app.py")
write_file(path="/src/new.py", content="print('hello')")
edit_file(path="/src/app.py", old_string="old", new_string="new")
glob(pattern="**/*.py", path="/src")
grep(pattern="def main", path="/src")
execute(command="python test.py", timeout=30)  # If sandbox backend
```

### SubAgentToolset

Delegate tasks to specialized subagents.

| Tool | Description |
|------|-------------|
| `task` | Spawn a subagent to handle a task |

```python
# Agent can call:
task(
    description="Review the authentication module for security issues",
    subagent_type="code-reviewer",
)
```

**Built-in Subagent Types:**

- `general-purpose` - Default agent for any task (if enabled)
- Custom types from `subagents` configuration

### SkillsToolset

Modular capability packages.

| Tool | Description |
|------|-------------|
| `list_skills` | List available skills with metadata |
| `load_skill` | Load full instructions for a skill |
| `read_skill_resource` | Read additional files from a skill |

```python
# Agent can call:
list_skills()
load_skill(skill_name="code-review")
read_skill_resource(skill_name="code-review", resource_name="template.md")
```

## Enabling/Disabling Toolsets

```python
agent = create_deep_agent(
    include_todo=True,        # TodoToolset
    include_filesystem=True,  # FilesystemToolset
    include_subagents=True,   # SubAgentToolset
    include_skills=True,      # SkillsToolset
)
```

## Custom Toolsets

Create custom toolsets using `FunctionToolset`:

```python
from pydantic_ai import RunContext
from pydantic_ai.toolsets import FunctionToolset
from pydantic_deep import DeepAgentDeps

# Create toolset
my_toolset = FunctionToolset[DeepAgentDeps](id="my-tools")

@my_toolset.tool
async def fetch_data(
    ctx: RunContext[DeepAgentDeps],
    url: str,
) -> str:
    """Fetch data from a URL.

    Args:
        url: The URL to fetch.

    Returns:
        The response content.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.text

@my_toolset.tool
async def analyze_sentiment(
    ctx: RunContext[DeepAgentDeps],
    text: str,
) -> str:
    """Analyze sentiment of text.

    Args:
        text: Text to analyze.

    Returns:
        Sentiment analysis result.
    """
    # Your sentiment analysis logic
    return "Positive"

# Add to agent
agent = create_deep_agent(toolsets=[my_toolset])
```

## Tool Documentation

Tools use docstrings for LLM understanding:

```python
@my_toolset.tool
async def process_data(
    ctx: RunContext[DeepAgentDeps],
    data: str,
    format: str = "json",
) -> str:
    """Process and transform data.

    This tool takes raw data and processes it according to the
    specified format. Supports JSON, CSV, and XML formats.

    Args:
        data: The raw data to process.
        format: Output format - 'json', 'csv', or 'xml'. Defaults to 'json'.

    Returns:
        Processed data in the requested format.

    Example:
        >>> process_data(data="name,age\\nAlice,30", format="json")
        '[{"name": "Alice", "age": "30"}]'
    """
    ...
```

## Approval Requirements

Require human approval for sensitive tools:

```python
from pydantic_ai.common_tools.dangerous import DangerousCapability

@my_toolset.tool
async def delete_files(
    ctx: RunContext[DeepAgentDeps],
    pattern: str,
) -> str:
    """Delete files matching pattern."""
    ...

# Mark as dangerous
delete_files.dangerous = DangerousCapability.FILESYSTEM
```

Or configure via `interrupt_on`:

```python
agent = create_deep_agent(
    interrupt_on={
        "delete_files": True,
        "execute": True,
    }
)
```

## Dynamic System Prompts

Toolsets can contribute dynamic system prompts:

```python
def get_my_system_prompt(deps: DeepAgentDeps) -> str:
    """Generate system prompt based on current state."""
    if deps.some_condition:
        return "## Additional Context\nSome relevant information..."
    return ""
```

The agent factory uses these to build dynamic instructions.

## Tool Return Types

Tools can return various types:

```python
# String - most common
async def my_tool(ctx: RunContext[DeepAgentDeps]) -> str:
    return "Result text"

# Structured data (converted to string)
async def my_tool(ctx: RunContext[DeepAgentDeps]) -> dict:
    return {"status": "success", "count": 42}

# Lists
async def my_tool(ctx: RunContext[DeepAgentDeps]) -> list[str]:
    return ["item1", "item2", "item3"]
```

## Best Practices

### 1. Clear Docstrings

Write detailed docstrings - they're the LLM's documentation.

### 2. Type Hints

Use type hints for all parameters:

```python
async def process(
    ctx: RunContext[DeepAgentDeps],
    items: list[str],          # List of strings
    count: int = 10,           # Integer with default
    enabled: bool = True,      # Boolean
) -> str:
    ...
```

### 3. Error Handling

Return informative errors:

```python
async def read_config(
    ctx: RunContext[DeepAgentDeps],
    name: str,
) -> str:
    try:
        return load_config(name)
    except FileNotFoundError:
        return f"Error: Config '{name}' not found. Available: {list_configs()}"
```

### 4. Idempotent Operations

When possible, make tools idempotent:

```python
async def ensure_directory(
    ctx: RunContext[DeepAgentDeps],
    path: str,
) -> str:
    """Ensure directory exists (creates if needed)."""
    if directory_exists(path):
        return f"Directory {path} already exists"
    create_directory(path)
    return f"Created directory {path}"
```

## Next Steps

- [Skills](skills.md) - Modular capability packages
- [API Reference](../api/toolsets.md) - Complete toolset API
- [Custom Tools Example](../examples/basic-usage.md) - More examples
