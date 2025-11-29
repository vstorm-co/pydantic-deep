# Backends

Backends provide file storage for deep agents. All backends implement the `BackendProtocol`.

## Available Backends

| Backend | Persistence | Execution | Use Case |
|---------|-------------|-----------|----------|
| `StateBackend` | Ephemeral | No | Testing, temporary files |
| `FilesystemBackend` | Persistent | No | Real file operations |
| `DockerSandbox` | Ephemeral | Yes | Safe code execution |
| `CompositeBackend` | Mixed | Depends | Route by path prefix |

## StateBackend

In-memory storage, ideal for testing and temporary operations.

```python
from pydantic_deep import StateBackend, DeepAgentDeps

backend = StateBackend()
deps = DeepAgentDeps(backend=backend)

# Files are stored in memory
backend.write("/src/app.py", "print('hello')")
print(backend.read("/src/app.py"))

# Access all files
print(backend.files.keys())
```

### Characteristics

- ✅ Fast - no disk I/O
- ✅ Isolated - no side effects
- ✅ Perfect for testing
- ❌ Data lost when process ends
- ❌ No command execution

## FilesystemBackend

Real filesystem operations with optional virtual mode.

```python
from pydantic_deep import FilesystemBackend

# Direct filesystem access
backend = FilesystemBackend("/path/to/workspace")

# Virtual mode - tracks writes but doesn't persist
backend = FilesystemBackend("/path/to/workspace", virtual_mode=True)
```

### Virtual Mode

Virtual mode tracks all operations without modifying the actual filesystem:

```python
backend = FilesystemBackend("/workspace", virtual_mode=True)

# Write goes to virtual storage
backend.write("/workspace/new_file.py", "content")

# Read from virtual if exists, else from real filesystem
content = backend.read("/workspace/existing_file.py")

# Get list of virtual writes
print(backend.virtual_files)
```

### Ripgrep Integration

FilesystemBackend uses ripgrep for fast searching when available:

```python
# Fast regex search across files
matches = backend.grep_raw(r"def \w+\(", path="/workspace/src")
```

## DockerSandbox

Isolated execution environment using Docker containers.

!!! warning "Requires Docker"
    Make sure Docker is installed and running.

```python
from pydantic_deep.backends.sandbox import DockerSandbox

sandbox = DockerSandbox(
    image="python:3.12-slim",
    work_dir="/workspace",
)

try:
    deps = DeepAgentDeps(backend=sandbox)

    # Agent can now execute code safely
    agent = create_deep_agent(
        interrupt_on={"execute": True},  # Still require approval
    )

    result = await agent.run(
        "Create and run a Python script",
        deps=deps,
    )
finally:
    sandbox.stop()  # Clean up container
```

### Execution

```python
# Execute commands in container
response = sandbox.execute("python script.py", timeout=30)
print(response.output)
print(response.exit_code)
```

## CompositeBackend

Route operations to different backends based on path prefix.

```python
from pydantic_deep import CompositeBackend, StateBackend, FilesystemBackend

backend = CompositeBackend(
    default=StateBackend(),  # Default for unmatched paths
    routes={
        "/project/": FilesystemBackend("/my/project"),
        "/workspace/": FilesystemBackend("/tmp/workspace"),
        # /temp/ goes to default (StateBackend)
    },
)

deps = DeepAgentDeps(backend=backend)
```

### Use Cases

- Persistent project files + ephemeral scratch space
- Multiple project directories
- Read-only sources + writable outputs

## Backend Protocol

All backends implement this protocol:

```python
from typing import Protocol

class BackendProtocol(Protocol):
    def ls_info(self, path: str) -> list[FileInfo]:
        """List directory contents."""
        ...

    def read(self, path: str, offset: int = 0, limit: int = 2000) -> str:
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

    def glob_info(self, pattern: str, path: str = "/") -> list[FileInfo]:
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

Extends BackendProtocol with execution:

```python
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

## Custom Backends

Create your own backend by implementing the protocol:

```python
from pydantic_deep import BackendProtocol, FileInfo, WriteResult

class S3Backend:
    """Store files in S3."""

    def __init__(self, bucket: str):
        self.bucket = bucket
        self._client = boto3.client('s3')

    def read(self, path: str, offset: int = 0, limit: int = 2000) -> str:
        response = self._client.get_object(Bucket=self.bucket, Key=path)
        content = response['Body'].read().decode('utf-8')
        lines = content.split('\n')
        # Add line numbers like StateBackend
        return '\n'.join(
            f"{i+1}\t{line}"
            for i, line in enumerate(lines[offset:offset+limit])
        )

    def write(self, path: str, content: str) -> WriteResult:
        self._client.put_object(
            Bucket=self.bucket,
            Key=path,
            Body=content.encode('utf-8'),
        )
        return WriteResult(path=path)

    # Implement other methods...
```

## Path Security

All backends validate paths to prevent directory traversal:

```python
# These will fail with an error:
backend.read("../etc/passwd")      # Parent directory
backend.read("~/secrets")          # Home directory expansion
backend.read("C:\\Windows\\...")   # Windows absolute paths
```

## Next Steps

- [Toolsets](toolsets.md) - How tools use backends
- [Docker Sandbox Example](../examples/docker-sandbox.md) - Full example
- [API Reference](../api/backends.md) - Complete API
