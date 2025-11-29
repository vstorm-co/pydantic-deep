"""In-memory state backend for ephemeral file storage."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from wcmatch import glob as wcglob

from pydantic_deep.types import EditResult, FileData, FileInfo, GrepMatch, WriteResult

if TYPE_CHECKING:
    pass


def _validate_path(path: str) -> str | None:
    """Validate path for security issues.

    Returns error message if invalid, None if valid.
    """
    if ".." in path:
        return "Path cannot contain '..'"
    if path.startswith("~"):
        return "Path cannot start with '~'"
    if len(path) > 1 and path[1] == ":":
        return "Windows absolute paths are not allowed"
    return None


def _normalize_path(path: str) -> str:
    """Normalize path to consistent format."""
    if not path.startswith("/"):
        path = "/" + path
    # Remove trailing slash except for root
    if len(path) > 1 and path.endswith("/"):
        path = path.rstrip("/")
    return path


class StateBackend:
    """In-memory file storage backend.

    Files are stored in a dictionary and are ephemeral (lost when the
    process ends). Useful for testing and temporary file operations.
    """

    def __init__(self, files: dict[str, FileData] | None = None):
        """Initialize the backend.

        Args:
            files: Optional initial file dictionary.
        """
        self._files: dict[str, FileData] = files if files is not None else {}

    @property
    def files(self) -> dict[str, FileData]:
        """Get the internal files dictionary."""
        return self._files

    def _get_timestamp(self) -> str:
        """Get current ISO 8601 timestamp."""
        return datetime.now(timezone.utc).isoformat()

    def ls_info(self, path: str) -> list[FileInfo]:
        """List files and directories at the given path."""
        error = _validate_path(path)
        if error:
            return []

        path = _normalize_path(path)

        # Collect all entries at this level
        entries: dict[str, FileInfo] = {}
        prefix = path if path == "/" else path + "/"

        for file_path, file_data in self._files.items():
            if not file_path.startswith(prefix) and file_path != path:
                continue  # pragma: no cover

            # Get the relative path from the directory
            if file_path == path:
                # This is a file, not a directory
                name = file_path.split("/")[-1]
                entries[name] = FileInfo(
                    name=name,
                    path=file_path,
                    is_dir=False,
                    size=sum(len(line) for line in file_data["content"]),
                )
            else:  # pragma: no cover
                rel_path = file_path[len(prefix) :]
                parts = rel_path.split("/")
                name = parts[0]

                if name not in entries:
                    if len(parts) == 1:
                        # Direct child file
                        entries[name] = FileInfo(
                            name=name,
                            path=file_path,
                            is_dir=False,
                            size=sum(len(line) for line in file_data["content"]),
                        )
                    else:
                        # Directory (has more parts)
                        entries[name] = FileInfo(
                            name=name,
                            path=prefix + name,
                            is_dir=True,
                            size=None,
                        )

        return sorted(entries.values(), key=lambda x: (not x["is_dir"], x["name"]))

    def read(self, path: str, offset: int = 0, limit: int = 2000) -> str:
        """Read file content with line numbers."""
        error = _validate_path(path)
        if error:  # pragma: no cover
            return f"Error: {error}"

        path = _normalize_path(path)

        if path not in self._files:
            return f"Error: File '{path}' not found"

        lines = self._files[path]["content"]
        total_lines = len(lines)

        if offset >= total_lines:
            return f"Error: Offset {offset} exceeds file length ({total_lines} lines)"

        end = min(offset + limit, total_lines)
        result_lines = []

        for i in range(offset, end):
            line_num = i + 1  # 1-indexed
            result_lines.append(f"{line_num:>6}\t{lines[i]}")

        result = "\n".join(result_lines)

        if end < total_lines:
            result += f"\n\n... ({total_lines - end} more lines)"

        return result

    def write(self, path: str, content: str) -> WriteResult:
        """Write content to a file."""
        error = _validate_path(path)
        if error:
            return WriteResult(error=error)

        path = _normalize_path(path)
        now = self._get_timestamp()

        # Split content into lines, preserving empty lines
        lines = content.split("\n")

        self._files[path] = FileData(
            content=lines,
            created_at=self._files.get(path, {}).get("created_at", now),
            modified_at=now,
        )

        return WriteResult(path=path)

    def edit(
        self, path: str, old_string: str, new_string: str, replace_all: bool = False
    ) -> EditResult:
        """Edit a file by replacing strings."""
        error = _validate_path(path)
        if error:
            return EditResult(error=error)

        path = _normalize_path(path)

        if path not in self._files:
            return EditResult(error=f"File '{path}' not found")  # pragma: no cover

        content = "\n".join(self._files[path]["content"])
        occurrences = content.count(old_string)

        if occurrences == 0:
            return EditResult(error=f"String '{old_string}' not found in file")  # pragma: no cover

        if occurrences > 1 and not replace_all:
            return EditResult(
                error=f"String '{old_string}' found {occurrences} times. "
                "Use replace_all=True to replace all, or provide more context."
            )

        if replace_all:
            new_content = content.replace(old_string, new_string)
        else:
            new_content = content.replace(old_string, new_string, 1)

        self._files[path]["content"] = new_content.split("\n")
        self._files[path]["modified_at"] = self._get_timestamp()

        return EditResult(path=path, occurrences=occurrences if replace_all else 1)

    def glob_info(self, pattern: str, path: str = "/") -> list[FileInfo]:
        """Find files matching a glob pattern."""
        error = _validate_path(path)
        if error:
            return []

        path = _normalize_path(path)

        # Combine path and pattern
        if path == "/":
            full_pattern = "/" + pattern.lstrip("/")
        else:
            full_pattern = path + "/" + pattern.lstrip("/")

        results: list[FileInfo] = []

        for file_path, file_data in self._files.items():
            # Use wcmatch for glob matching
            if wcglob.globmatch(file_path, full_pattern, flags=wcglob.GLOBSTAR):
                name = file_path.split("/")[-1]
                results.append(
                    FileInfo(
                        name=name,
                        path=file_path,
                        is_dir=False,
                        size=sum(len(line) for line in file_data["content"]),
                    )
                )

        return sorted(results, key=lambda x: x["path"])

    def grep_raw(
        self, pattern: str, path: str | None = None, glob: str | None = None
    ) -> list[GrepMatch] | str:
        """Search for pattern in files."""
        try:
            regex = re.compile(pattern)
        except re.error as e:
            return f"Error: Invalid regex pattern: {e}"

        results: list[GrepMatch] = []

        # Determine which files to search
        files_to_search: list[str] = []

        if path:
            error = _validate_path(path)
            if error:
                return f"Error: {error}"
            path = _normalize_path(path)

            if path in self._files:
                files_to_search = [path]
            else:
                # Path is a directory - search all files under it
                prefix = path if path == "/" else path + "/"
                files_to_search = [f for f in self._files if f.startswith(prefix)]
        else:
            files_to_search = list(self._files.keys())

        # Filter by glob if provided
        if glob:
            glob_pattern = "/" + glob.lstrip("/")
            files_to_search = [
                f
                for f in files_to_search
                if wcglob.globmatch(f, glob_pattern, flags=wcglob.GLOBSTAR)
            ]

        # Search each file
        for file_path in files_to_search:
            lines = self._files[file_path]["content"]
            for i, line in enumerate(lines):
                if regex.search(line):
                    results.append(
                        GrepMatch(
                            path=file_path,
                            line_number=i + 1,
                            line=line,
                        )
                    )

        return results
