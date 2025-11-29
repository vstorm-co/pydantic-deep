"""Sandbox backends for isolated command execution."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from pydantic_deep.types import EditResult, ExecuteResponse, FileInfo, GrepMatch, WriteResult

if TYPE_CHECKING:
    pass


class BaseSandbox(ABC):
    """Abstract base class for sandbox backends.

    Sandboxes provide isolated environments for executing commands and
    managing files. Subclasses must implement the execute() method.
    """

    def __init__(self, sandbox_id: str | None = None):
        """Initialize the sandbox.

        Args:
            sandbox_id: Unique identifier for this sandbox. Generated if not provided.
        """
        self._id = sandbox_id or str(uuid.uuid4())  # pragma: no cover

    @property
    def id(self) -> str:
        """Unique identifier for this sandbox."""
        return self._id  # pragma: no cover

    @abstractmethod
    def execute(
        self, command: str, timeout: int | None = None
    ) -> ExecuteResponse:  # pragma: no cover
        """Execute a command in the sandbox.

        Args:
            command: Command to execute.
            timeout: Maximum execution time in seconds.

        Returns:
            ExecuteResponse with output, exit code, and truncation status.
        """
        ...

    def ls_info(self, path: str) -> list[FileInfo]:  # pragma: no cover
        """List files using ls command."""
        result = self.execute(f"ls -la {path}")
        if result.exit_code != 0:
            return []

        entries: list[FileInfo] = []
        for line in result.output.strip().split("\n")[1:]:  # Skip total line
            if not line.strip():
                continue

            parts = line.split()
            if len(parts) < 9:
                continue

            perms = parts[0]
            size = int(parts[4]) if parts[4].isdigit() else None
            name = " ".join(parts[8:])

            if name in (".", ".."):
                continue

            full_path = f"{path.rstrip('/')}/{name}"
            entries.append(
                FileInfo(
                    name=name,
                    path=full_path,
                    is_dir=perms.startswith("d"),
                    size=size,
                )
            )

        return sorted(entries, key=lambda x: (not x["is_dir"], x["name"]))

    def read(self, path: str, offset: int = 0, limit: int = 2000) -> str:  # pragma: no cover
        """Read file using cat command with line numbers."""
        # Use sed to handle offset and limit
        start = offset + 1  # sed is 1-indexed
        end = offset + limit

        result = self.execute(f"sed -n '{start},{end}p' {path} | cat -n")

        if result.exit_code != 0:
            return f"Error: {result.output}"

        if result.truncated:
            return result.output + "\n\n... (output truncated)"

        return result.output

    def write(self, path: str, content: str) -> WriteResult:  # pragma: no cover
        """Write file using cat with heredoc."""
        # Escape special characters for heredoc
        escaped = content.replace("\\", "\\\\").replace("$", "\\$").replace("`", "\\`")

        # Use a unique delimiter
        delimiter = f"EOF_{uuid.uuid4().hex[:8]}"

        result = self.execute(
            f"mkdir -p $(dirname {path}) && cat > {path} << '{delimiter}'\n{escaped}\n{delimiter}"
        )

        if result.exit_code != 0:
            return WriteResult(error=result.output)

        return WriteResult(path=path)

    def edit(  # pragma: no cover
        self, path: str, old_string: str, new_string: str, replace_all: bool = False
    ) -> EditResult:
        """Edit file using sed."""
        # First check if file exists and count occurrences
        check = self.execute(f"grep -c '{old_string}' {path}")

        if check.exit_code != 0:
            if "No such file" in check.output:
                return EditResult(error=f"File '{path}' not found")
            return EditResult(error=f"String '{old_string}' not found in file")

        try:
            occurrences = int(check.output.strip())
        except ValueError:
            occurrences = 0

        if occurrences == 0:
            return EditResult(error=f"String '{old_string}' not found in file")

        if occurrences > 1 and not replace_all:
            return EditResult(
                error=f"String '{old_string}' found {occurrences} times. "
                "Use replace_all=True to replace all, or provide more context."
            )

        # Escape special sed characters
        old_escaped = old_string.replace("/", "\\/").replace("&", "\\&")
        new_escaped = new_string.replace("/", "\\/").replace("&", "\\&")

        if replace_all:
            result = self.execute(f"sed -i 's/{old_escaped}/{new_escaped}/g' {path}")
        else:
            result = self.execute(f"sed -i '0,/{old_escaped}/s//{new_escaped}/' {path}")

        if result.exit_code != 0:
            return EditResult(error=result.output)

        return EditResult(path=path, occurrences=occurrences if replace_all else 1)

    def glob_info(self, pattern: str, path: str = "/") -> list[FileInfo]:  # pragma: no cover
        """Find files using find command."""
        # Convert glob to find pattern
        result = self.execute(f"find {path} -name '{pattern}' -type f 2>/dev/null")

        if result.exit_code != 0:
            return []

        entries: list[FileInfo] = []
        for file_path in result.output.strip().split("\n"):
            if not file_path:
                continue

            name = file_path.split("/")[-1]
            entries.append(
                FileInfo(
                    name=name,
                    path=file_path,
                    is_dir=False,
                    size=None,
                )
            )

        return sorted(entries, key=lambda x: x["path"])

    def grep_raw(  # pragma: no cover
        self, pattern: str, path: str | None = None, glob: str | None = None
    ) -> list[GrepMatch] | str:
        """Search using grep command."""
        search_path = path or "/"

        if glob:
            cmd = f"grep -rn '{pattern}' {search_path} --include='{glob}'"
        else:
            cmd = f"grep -rn '{pattern}' {search_path}"

        result = self.execute(cmd)

        if result.exit_code == 1:  # No matches
            return []
        if result.exit_code != 0:
            return f"Error: {result.output}"

        matches: list[GrepMatch] = []
        for line in result.output.strip().split("\n"):
            if not line:
                continue

            # Parse grep output: file:line:content
            parts = line.split(":", 2)
            if len(parts) >= 3:
                try:
                    matches.append(
                        GrepMatch(
                            path=parts[0],
                            line_number=int(parts[1]),
                            line=parts[2],
                        )
                    )
                except ValueError:
                    continue

        return matches


class DockerSandbox(BaseSandbox):  # pragma: no cover
    """Docker-based sandbox for isolated command execution.

    Creates a Docker container for running commands in an isolated environment.
    Requires the docker Python package to be installed.
    """

    def __init__(
        self,
        image: str = "python:3.12-slim",
        sandbox_id: str | None = None,
        work_dir: str = "/workspace",
        auto_remove: bool = True,
    ):
        """Initialize Docker sandbox.

        Args:
            image: Docker image to use.
            sandbox_id: Unique identifier for this sandbox.
            work_dir: Working directory inside container.
            auto_remove: Remove container when stopped.
        """
        super().__init__(sandbox_id)
        self._image = image
        self._work_dir = work_dir
        self._auto_remove = auto_remove
        self._container = None

    def _ensure_container(self):
        """Ensure Docker container is running."""
        if self._container is not None:
            return

        try:
            import docker
        except ImportError as e:
            raise ImportError(
                "Docker package not installed. Install with: pip install docker"
            ) from e

        client = docker.from_env()

        self._container = client.containers.run(
            self._image,
            command="sleep infinity",
            detach=True,
            working_dir=self._work_dir,
            auto_remove=self._auto_remove,
            volumes={},  # Can be configured for persistent storage
        )

    def execute(self, command: str, timeout: int | None = None) -> ExecuteResponse:
        """Execute command in Docker container."""
        self._ensure_container()

        try:
            exit_code, output = self._container.exec_run(
                ["sh", "-c", command],
                workdir=self._work_dir,
                timeout=timeout,
            )

            output_str = output.decode("utf-8", errors="replace")

            # Truncate if too long
            max_output = 100000
            truncated = len(output_str) > max_output
            if truncated:
                output_str = output_str[:max_output]

            return ExecuteResponse(
                output=output_str,
                exit_code=exit_code,
                truncated=truncated,
            )
        except Exception as e:
            return ExecuteResponse(
                output=f"Error: {e}",
                exit_code=1,
                truncated=False,
            )

    def stop(self):
        """Stop and remove the container."""
        import contextlib

        if self._container:
            with contextlib.suppress(Exception):
                self._container.stop()
            self._container = None

    def __del__(self):
        """Cleanup container on deletion."""
        self.stop()


class LocalSandbox(BaseSandbox):  # pragma: no cover
    """Local sandbox using subprocess (no isolation).

    WARNING: This sandbox executes commands directly on the host system
    without isolation. Use DockerSandbox for production workloads.
    """

    def __init__(
        self,
        work_dir: str = "/tmp/pydantic-deep-sandbox",
        sandbox_id: str | None = None,
    ):
        """Initialize local sandbox.

        Args:
            work_dir: Working directory for commands.
            sandbox_id: Unique identifier for this sandbox.
        """
        super().__init__(sandbox_id)
        self._work_dir = work_dir

        # Create work directory
        import os

        os.makedirs(work_dir, exist_ok=True)

    def execute(self, command: str, timeout: int | None = None) -> ExecuteResponse:
        """Execute command using subprocess."""
        import subprocess

        try:
            result = subprocess.run(
                ["sh", "-c", command],
                cwd=self._work_dir,
                capture_output=True,
                text=True,
                timeout=timeout or 120,
            )

            output = result.stdout + result.stderr

            # Truncate if too long
            max_output = 100000
            truncated = len(output) > max_output
            if truncated:
                output = output[:max_output]

            return ExecuteResponse(
                output=output,
                exit_code=result.returncode,
                truncated=truncated,
            )
        except subprocess.TimeoutExpired:
            return ExecuteResponse(
                output="Error: Command timed out",
                exit_code=124,
                truncated=False,
            )
        except Exception as e:
            return ExecuteResponse(
                output=f"Error: {e}",
                exit_code=1,
                truncated=False,
            )
