"""Real filesystem backend for file operations."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

from pydantic_deep.types import EditResult, FileInfo, GrepMatch, WriteResult


def _validate_path(path: str, root_dir: Path) -> str | None:
    """Validate path for security issues.

    Returns error message if invalid, None if valid.
    """
    if ".." in path:
        return "Path cannot contain '..'"
    if path.startswith("~"):
        return "Path cannot start with '~'"

    # Resolve the full path and check it's within root_dir
    try:
        full_path = (root_dir / path.lstrip("/")).resolve()
        if not str(full_path).startswith(str(root_dir.resolve())):
            return "Path escapes root directory"  # pragma: no cover
    except (ValueError, OSError) as e:  # pragma: no cover
        return f"Invalid path: {e}"

    return None


class FilesystemBackend:
    """Backend for real filesystem operations.

    All operations are relative to the root_dir.
    """

    def __init__(self, root_dir: str | Path, virtual_mode: bool = False):
        """Initialize the backend.

        Args:
            root_dir: Base directory for all operations.
            virtual_mode: If True, create the root_dir if it doesn't exist.
        """
        self._root = Path(root_dir).resolve()

        if virtual_mode:
            self._root.mkdir(parents=True, exist_ok=True)
        elif not self._root.exists():
            raise ValueError(f"Root directory does not exist: {self._root}")

    @property
    def root_dir(self) -> Path:
        """Get the root directory."""
        return self._root

    def _resolve_path(self, path: str) -> Path:
        """Resolve a virtual path to an absolute filesystem path."""
        return self._root / path.lstrip("/")

    def ls_info(self, path: str) -> list[FileInfo]:
        """List files and directories at the given path."""
        error = _validate_path(path, self._root)
        if error:  # pragma: no cover
            return []

        full_path = self._resolve_path(path)

        if not full_path.exists():
            return []

        if full_path.is_file():
            return [
                FileInfo(
                    name=full_path.name,
                    path=path,
                    is_dir=False,
                    size=full_path.stat().st_size,
                )
            ]

        results: list[FileInfo] = []
        try:
            for entry in full_path.iterdir():
                rel_path = "/" + str(entry.relative_to(self._root))
                results.append(
                    FileInfo(
                        name=entry.name,
                        path=rel_path,
                        is_dir=entry.is_dir(),
                        size=entry.stat().st_size if entry.is_file() else None,
                    )
                )
        except PermissionError:  # pragma: no cover
            return []

        return sorted(results, key=lambda x: (not x["is_dir"], x["name"]))

    def read(self, path: str, offset: int = 0, limit: int = 2000) -> str:
        """Read file content with line numbers."""
        error = _validate_path(path, self._root)
        if error:  # pragma: no cover
            return f"Error: {error}"

        full_path = self._resolve_path(path)

        if not full_path.exists():
            return f"Error: File '{path}' not found"

        if full_path.is_dir():
            return f"Error: '{path}' is a directory"

        try:
            with open(full_path, encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
        except PermissionError:  # pragma: no cover
            return f"Error: Permission denied for '{path}'"
        except OSError as e:  # pragma: no cover
            return f"Error: {e}"

        total_lines = len(lines)

        if offset >= total_lines:
            return f"Error: Offset {offset} exceeds file length ({total_lines} lines)"

        end = min(offset + limit, total_lines)
        result_lines = []

        for i in range(offset, end):
            line_num = i + 1
            # Remove trailing newline for display
            line = lines[i].rstrip("\n\r")
            result_lines.append(f"{line_num:>6}\t{line}")

        result = "\n".join(result_lines)

        if end < total_lines:
            result += f"\n\n... ({total_lines - end} more lines)"

        return result

    def write(self, path: str, content: str) -> WriteResult:
        """Write content to a file."""
        error = _validate_path(path, self._root)
        if error:
            return WriteResult(error=error)

        full_path = self._resolve_path(path)

        try:
            # Create parent directories if needed
            full_path.parent.mkdir(parents=True, exist_ok=True)

            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)

            return WriteResult(path=path)
        except PermissionError:  # pragma: no cover
            return WriteResult(error=f"Permission denied for '{path}'")
        except OSError as e:  # pragma: no cover
            return WriteResult(error=str(e))

    def edit(
        self, path: str, old_string: str, new_string: str, replace_all: bool = False
    ) -> EditResult:
        """Edit a file by replacing strings."""
        error = _validate_path(path, self._root)
        if error:  # pragma: no cover
            return EditResult(error=error)

        full_path = self._resolve_path(path)

        if not full_path.exists():
            return EditResult(error=f"File '{path}' not found")

        try:
            with open(full_path, encoding="utf-8") as f:
                content = f.read()
        except PermissionError:  # pragma: no cover
            return EditResult(error=f"Permission denied for '{path}'")
        except OSError as e:  # pragma: no cover
            return EditResult(error=str(e))

        occurrences = content.count(old_string)

        if occurrences == 0:
            return EditResult(error=f"String '{old_string}' not found in file")

        if occurrences > 1 and not replace_all:
            return EditResult(
                error=f"String '{old_string}' found {occurrences} times. "
                "Use replace_all=True to replace all, or provide more context."
            )

        if replace_all:
            new_content = content.replace(old_string, new_string)
        else:
            new_content = content.replace(old_string, new_string, 1)

        try:
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(new_content)

            return EditResult(path=path, occurrences=occurrences if replace_all else 1)
        except PermissionError:  # pragma: no cover
            return EditResult(error=f"Permission denied for '{path}'")
        except OSError as e:  # pragma: no cover
            return EditResult(error=str(e))

    def glob_info(self, pattern: str, path: str = "/") -> list[FileInfo]:
        """Find files matching a glob pattern."""
        error = _validate_path(path, self._root)
        if error:  # pragma: no cover
            return []

        base_path = self._resolve_path(path)

        if not base_path.exists():
            return []

        results: list[FileInfo] = []

        try:
            for match in base_path.glob(pattern):
                if match.is_file():
                    rel_path = "/" + str(match.relative_to(self._root))
                    results.append(
                        FileInfo(
                            name=match.name,
                            path=rel_path,
                            is_dir=False,
                            size=match.stat().st_size,
                        )
                    )
        except (PermissionError, OSError):  # pragma: no cover
            pass

        return sorted(results, key=lambda x: x["path"])

    def grep_raw(
        self, pattern: str, path: str | None = None, glob: str | None = None
    ) -> list[GrepMatch] | str:
        """Search for pattern in files.

        Uses ripgrep if available, falls back to Python regex.
        """
        # Try ripgrep first (coverage varies by system availability)
        if shutil.which("rg"):  # pragma: no cover
            return self._grep_ripgrep(pattern, path, glob)

        return self._grep_python(pattern, path, glob)  # pragma: no cover

    def _grep_ripgrep(  # pragma: no cover
        self, pattern: str, path: str | None = None, glob: str | None = None
    ) -> list[GrepMatch] | str:
        """Use ripgrep for fast searching."""
        cmd = ["rg", "--line-number", "--no-heading", pattern]

        if glob:
            cmd.extend(["--glob", glob])

        search_path = self._resolve_path(path) if path else self._root

        try:
            result = subprocess.run(
                cmd,
                cwd=search_path,
                capture_output=True,
                text=True,
                timeout=30,
            )
        except subprocess.TimeoutExpired:
            return "Error: Search timed out"
        except OSError as e:
            return f"Error: {e}"

        results: list[GrepMatch] = []

        for line in result.stdout.strip().split("\n"):
            if not line:
                continue

            # Parse ripgrep output: file:line:content
            parts = line.split(":", 2)
            if len(parts) >= 3:
                file_path = parts[0]
                try:
                    line_num = int(parts[1])
                except ValueError:
                    continue
                content = parts[2]

                # Convert to virtual path
                try:
                    full_path = (search_path / file_path).resolve()
                    rel_path = "/" + str(full_path.relative_to(self._root))
                except (ValueError, OSError):
                    rel_path = "/" + file_path

                results.append(
                    GrepMatch(
                        path=rel_path,
                        line_number=line_num,
                        line=content,
                    )
                )

        return results

    def _grep_python(
        self, pattern: str, path: str | None = None, glob_pattern: str | None = None
    ) -> list[GrepMatch] | str:
        """Use Python regex for searching (fallback)."""
        try:
            regex = re.compile(pattern)
        except re.error as e:
            return f"Error: Invalid regex pattern: {e}"

        search_path = self._resolve_path(path) if path else self._root

        if not search_path.exists():
            return f"Error: Path '{path}' not found"

        results: list[GrepMatch] = []

        # Get files to search
        if search_path.is_file():
            files = [search_path]
        else:
            if glob_pattern:
                files = list(search_path.glob(glob_pattern))
            else:
                files = list(search_path.rglob("*"))

        for file_path in files:
            if not file_path.is_file():
                continue

            try:
                with open(file_path, encoding="utf-8", errors="replace") as f:
                    for i, line in enumerate(f):
                        if regex.search(line):
                            rel_path = "/" + str(file_path.relative_to(self._root))
                            results.append(
                                GrepMatch(
                                    path=rel_path,
                                    line_number=i + 1,
                                    line=line.rstrip("\n\r"),
                                )
                            )
            except (PermissionError, OSError):  # pragma: no cover
                continue

        return results
