"""Type definitions for pydantic-deep."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypedDict

from pydantic import BaseModel
from typing_extensions import NotRequired


class FileData(TypedDict):
    """Data structure for storing file content."""

    content: list[str]  # Lines of the file
    created_at: str  # ISO 8601 timestamp
    modified_at: str  # ISO 8601 timestamp


class FileInfo(TypedDict):
    """Information about a file or directory."""

    name: str
    path: str
    is_dir: bool
    size: int | None


@dataclass
class WriteResult:
    """Result of a write operation."""

    path: str | None = None
    error: str | None = None


@dataclass
class EditResult:
    """Result of an edit operation."""

    path: str | None = None
    error: str | None = None
    occurrences: int | None = None


@dataclass
class ExecuteResponse:
    """Response from command execution."""

    output: str
    exit_code: int | None = None
    truncated: bool = False


class GrepMatch(TypedDict):
    """A single grep match result."""

    path: str
    line_number: int
    line: str


class Todo(BaseModel):
    """A todo item for task tracking."""

    content: str
    status: Literal["pending", "in_progress", "completed"]
    active_form: str  # Present continuous form (e.g., "Implementing feature X")


class SubAgentConfig(TypedDict):
    """Configuration for a subagent."""

    name: str
    description: str
    instructions: str
    tools: NotRequired[list]
    model: NotRequired[str]


class CompiledSubAgent(TypedDict):
    """A pre-compiled subagent ready for use."""

    name: str
    description: str
    agent: NotRequired[object]  # Agent instance - typed as object to avoid circular imports


class SkillFrontmatter(TypedDict):
    """YAML frontmatter from a SKILL.md file."""

    name: str
    description: str
    tags: NotRequired[list[str]]
    version: NotRequired[str]
    author: NotRequired[str]


class Skill(TypedDict):
    """A loaded skill with its metadata and content."""

    name: str
    description: str
    path: str  # Path to the skill directory
    tags: list[str]
    version: str
    author: str
    frontmatter_loaded: bool  # Whether only frontmatter is loaded
    instructions: NotRequired[str]  # Full instructions (loaded on demand)
    resources: NotRequired[list[str]]  # List of additional files in the skill directory


class SkillDirectory(TypedDict):
    """Configuration for a skill directory."""

    path: str  # Path to the skills directory
    recursive: NotRequired[bool]  # Whether to search recursively
