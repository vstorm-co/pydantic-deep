"""Protocol definitions for storage backends."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from pydantic_deep.types import (
        EditResult,
        ExecuteResponse,
        FileInfo,
        GrepMatch,
        WriteResult,
    )


@runtime_checkable
class BackendProtocol(Protocol):
    """Protocol for file storage backends.

    All backends must implement these methods for basic file operations.
    """

    def ls_info(self, path: str) -> list[FileInfo]:
        """List files and directories at the given path.

        Args:
            path: Directory path to list.

        Returns:
            List of FileInfo objects for each entry.
        """
        ...

    def read(self, path: str, offset: int = 0, limit: int = 2000) -> str:
        """Read file content.

        Args:
            path: File path to read.
            offset: Line number to start reading from (0-indexed).
            limit: Maximum number of lines to read.

        Returns:
            File content as a string with line numbers.
        """
        ...

    def write(self, path: str, content: str) -> WriteResult:
        """Write content to a file.

        Args:
            path: File path to write to.
            content: Content to write.

        Returns:
            WriteResult with path or error.
        """
        ...

    def edit(
        self, path: str, old_string: str, new_string: str, replace_all: bool = False
    ) -> EditResult:
        """Edit a file by replacing strings.

        Args:
            path: File path to edit.
            old_string: String to find and replace.
            new_string: Replacement string.
            replace_all: If True, replace all occurrences. Otherwise, replace only first.

        Returns:
            EditResult with path, error, or occurrence count.
        """
        ...

    def glob_info(self, pattern: str, path: str = "/") -> list[FileInfo]:
        """Find files matching a glob pattern.

        Args:
            pattern: Glob pattern (e.g., "**/*.py").
            path: Base directory to search from.

        Returns:
            List of matching FileInfo objects.
        """
        ...

    def grep_raw(
        self, pattern: str, path: str | None = None, glob: str | None = None
    ) -> list[GrepMatch] | str:
        """Search for pattern in files.

        Args:
            pattern: Regex pattern to search for.
            path: Specific file or directory to search.
            glob: Glob pattern to filter files.

        Returns:
            List of GrepMatch objects or error string.
        """
        ...


@runtime_checkable
class SandboxProtocol(BackendProtocol, Protocol):
    """Extended protocol for backends that support command execution.

    In addition to file operations, sandbox backends can execute shell commands.
    """

    def execute(self, command: str, timeout: int | None = None) -> ExecuteResponse:
        """Execute a shell command.

        Args:
            command: Command to execute.
            timeout: Maximum execution time in seconds.

        Returns:
            ExecuteResponse with output, exit code, and truncation status.
        """
        ...

    @property
    def id(self) -> str:
        """Unique identifier for this sandbox instance."""
        ...
