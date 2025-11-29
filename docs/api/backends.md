# Backends API

## Protocols

### BackendProtocol

Base protocol for all file storage backends.

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class BackendProtocol(Protocol):
    def ls_info(self, path: str) -> list[FileInfo]:
        """List directory contents."""
        ...

    def read(
        self,
        path: str,
        offset: int = 0,
        limit: int = 2000,
    ) -> str:
        """Read file contents with line numbers."""
        ...

    def write(self, path: str, content: str) -> WriteResult:
        """Write file contents."""
        ...

    def edit(
        self,
        path: str,
        old_string: str,
        new_string: str,
        replace_all: bool = False,
    ) -> EditResult:
        """Edit file by replacing strings."""
        ...

    def glob_info(
        self,
        pattern: str,
        path: str = "/",
    ) -> list[FileInfo]:
        """Find files matching glob pattern."""
        ...

    def grep_raw(
        self,
        pattern: str,
        path: str | None = None,
        glob: str | None = None,
    ) -> list[GrepMatch] | str:
        """Search file contents with regex."""
        ...
```

### SandboxProtocol

Extended protocol with command execution.

```python
@runtime_checkable
class SandboxProtocol(BackendProtocol, Protocol):
    def execute(
        self,
        command: str,
        timeout: int | None = None,
    ) -> ExecuteResponse:
        """Execute a shell command."""
        ...

    @property
    def id(self) -> str:
        """Unique identifier for this sandbox."""
        ...
```

---

## StateBackend

In-memory file storage.

### Constructor

```python
class StateBackend:
    def __init__(self) -> None
```

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `files` | `dict[str, FileData]` | Stored files |

### Example

```python
from pydantic_deep import StateBackend

backend = StateBackend()

# Write a file
backend.write("/src/app.py", "print('hello')")

# Read a file
content = backend.read("/src/app.py")
# "     1\tprint('hello')"

# List directory
files = backend.ls_info("/src")
# [FileInfo(name="app.py", path="/src/app.py", is_dir=False, size=14)]

# Edit a file
backend.edit("/src/app.py", "hello", "world")

# Glob search
matches = backend.glob_info("**/*.py")

# Grep search
matches = backend.grep_raw("print")
```

---

## FilesystemBackend

Real filesystem storage.

### Constructor

```python
class FilesystemBackend:
    def __init__(
        self,
        root: str | Path,
        virtual_mode: bool = False,
    ) -> None
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `root` | `str \| Path` | Required | Root directory |
| `virtual_mode` | `bool` | `False` | Track writes without persisting |

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `root` | `Path` | Root directory path |
| `virtual_mode` | `bool` | Whether virtual mode is enabled |
| `virtual_files` | `dict[str, str]` | Virtual file contents (when virtual_mode=True) |

### Example

```python
from pydantic_deep import FilesystemBackend

# Direct filesystem access
backend = FilesystemBackend("/workspace")

# Virtual mode (no actual writes)
backend = FilesystemBackend("/workspace", virtual_mode=True)

# Write file
backend.write("/workspace/app.py", "print('hello')")

# Read file (from virtual if exists, else real)
content = backend.read("/workspace/app.py")

# Check virtual files
if backend.virtual_mode:
    print(backend.virtual_files)
```

---

## CompositeBackend

Route operations by path prefix.

### Constructor

```python
class CompositeBackend:
    def __init__(
        self,
        default: BackendProtocol,
        routes: dict[str, BackendProtocol],
    ) -> None
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `default` | `BackendProtocol` | Backend for unmatched paths |
| `routes` | `dict[str, BackendProtocol]` | Path prefix → backend mapping |

### Example

```python
from pydantic_deep import CompositeBackend, StateBackend, FilesystemBackend

backend = CompositeBackend(
    default=StateBackend(),
    routes={
        "/project/": FilesystemBackend("/my/project"),
        "/workspace/": FilesystemBackend("/tmp/workspace"),
    },
)

# Routes to FilesystemBackend
backend.write("/project/app.py", "...")

# Routes to StateBackend (default)
backend.write("/temp/scratch.txt", "...")
```

---

## DockerSandbox

Docker container sandbox with execution.

### Constructor

```python
class DockerSandbox:
    def __init__(
        self,
        image: str,
        work_dir: str = "/workspace",
    ) -> None
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `image` | `str` | Required | Docker image name |
| `work_dir` | `str` | `"/workspace"` | Working directory in container |

### Methods

#### execute

```python
def execute(
    self,
    command: str,
    timeout: int | None = None,
) -> ExecuteResponse
```

Execute a command in the container.

#### stop

```python
def stop(self) -> None
```

Stop and remove the container.

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `id` | `str` | Container ID |

### Example

```python
from pydantic_deep.backends.sandbox import DockerSandbox

sandbox = DockerSandbox(
    image="python:3.12-slim",
    work_dir="/workspace",
)

try:
    # Write file
    sandbox.write("/workspace/script.py", "print('hello')")

    # Execute command
    result = sandbox.execute("python /workspace/script.py", timeout=30)
    print(result.output)  # "hello\n"
    print(result.exit_code)  # 0

finally:
    sandbox.stop()
```

---

## BaseSandbox

Abstract base class for sandboxes.

```python
class BaseSandbox(ABC):
    @abstractmethod
    def execute(
        self,
        command: str,
        timeout: int | None = None,
    ) -> ExecuteResponse:
        ...

    @property
    @abstractmethod
    def id(self) -> str:
        ...
```

Inherit from this to create custom sandbox implementations.

---

## Type Definitions

### FileInfo

```python
class FileInfo(TypedDict):
    name: str      # File/directory name
    path: str      # Full path
    is_dir: bool   # True if directory
    size: int | None  # File size in bytes
```

### FileData

```python
class FileData(TypedDict):
    content: list[str]  # Lines of the file
    created_at: str     # ISO 8601 timestamp
    modified_at: str    # ISO 8601 timestamp
```

### WriteResult

```python
@dataclass
class WriteResult:
    path: str | None = None
    error: str | None = None
```

### EditResult

```python
@dataclass
class EditResult:
    path: str | None = None
    error: str | None = None
    occurrences: int | None = None
```

### ExecuteResponse

```python
@dataclass
class ExecuteResponse:
    output: str
    exit_code: int | None = None
    truncated: bool = False
```

### GrepMatch

```python
class GrepMatch(TypedDict):
    path: str
    line_number: int
    line: str
```
