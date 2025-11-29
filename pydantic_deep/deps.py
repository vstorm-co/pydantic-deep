"""Dependency injection container for deep agents."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from pydantic_deep.backends.protocol import BackendProtocol
from pydantic_deep.backends.state import StateBackend
from pydantic_deep.types import FileData, Todo

if TYPE_CHECKING:
    pass


@dataclass
class DeepAgentDeps:
    """Dependencies for deep agents.

    This container holds all the state and resources needed by the agent
    and its tools during execution.

    Attributes:
        backend: File storage backend (StateBackend, FilesystemBackend, etc.)
        files: In-memory file cache (used with StateBackend)
        todos: Task list for planning
        subagents: Pre-configured subagents available for delegation
    """

    backend: BackendProtocol = field(default_factory=StateBackend)
    files: dict[str, FileData] = field(default_factory=dict)
    todos: list[Todo] = field(default_factory=list)
    subagents: dict[str, Any] = field(default_factory=dict)  # Agent instances

    def __post_init__(self):
        """Initialize backend with files if using StateBackend."""
        if isinstance(self.backend, StateBackend) and self.files:
            # Sync files to state backend
            self.backend._files = self.files

    def get_todo_prompt(self) -> str:
        """Generate system prompt section for todos."""
        if not self.todos:
            return ""

        lines = ["## Current Todos"]
        for todo in self.todos:
            status_icon = {
                "pending": "[ ]",
                "in_progress": "[*]",
                "completed": "[x]",
            }.get(todo.status, "[ ]")
            lines.append(f"- {status_icon} {todo.content}")

        return "\n".join(lines)

    def get_files_summary(self) -> str:
        """Generate summary of files in memory."""
        if not self.files:
            return ""

        lines = ["## Files in Memory"]
        for path, data in sorted(self.files.items()):
            line_count = len(data["content"])
            lines.append(f"- {path} ({line_count} lines)")

        return "\n".join(lines)

    def get_subagents_summary(self) -> str:
        """Generate summary of available subagents."""
        if not self.subagents:
            return ""

        lines = ["## Available Subagents"]
        for name in sorted(self.subagents.keys()):
            lines.append(f"- {name}")

        return "\n".join(lines)

    def clone_for_subagent(self) -> DeepAgentDeps:
        """Create a new deps instance for a subagent.

        Subagents get:
        - Same backend (shared)
        - Empty todos (isolated)
        - Empty subagents (no nested delegation)
        - Same files (shared)
        """
        return DeepAgentDeps(
            backend=self.backend,
            files=self.files,  # Shared reference
            todos=[],  # Fresh todo list
            subagents={},  # No nested subagents
        )
