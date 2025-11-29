"""Skills toolset for pydantic-deep agents.

Skills are modular packages that extend agent capabilities. Each skill is a folder
containing a SKILL.md file with YAML frontmatter and Markdown instructions, along
with optional resource files (documents, scripts, etc.).

Progressive disclosure: Only YAML frontmatter is loaded by default. The full
instructions are loaded on-demand when the agent needs them.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pydantic_ai import RunContext
from pydantic_ai.toolsets import FunctionToolset

from pydantic_deep.deps import DeepAgentDeps
from pydantic_deep.types import Skill, SkillDirectory

if TYPE_CHECKING:
    pass


# Default skills directory (can be overridden)
DEFAULT_SKILLS_DIR = "~/.pydantic-deep/skills"


def parse_skill_md(content: str) -> tuple[dict[str, Any], str]:
    """Parse a SKILL.md file into frontmatter and instructions.

    Args:
        content: Full content of the SKILL.md file.

    Returns:
        Tuple of (frontmatter_dict, instructions_markdown).
    """
    # Match YAML frontmatter between --- delimiters
    frontmatter_pattern = r"^---\s*\n(.*?)\n---\s*\n?"
    match = re.match(frontmatter_pattern, content, re.DOTALL)

    if not match:
        # No frontmatter, treat entire content as instructions
        return {}, content.strip()

    frontmatter_yaml = match.group(1)
    instructions = content[match.end() :].strip()

    # Parse YAML manually (simple key: value format)
    frontmatter: dict[str, Any] = {}
    current_key = None
    current_list: list[str] | None = None

    for line in frontmatter_yaml.split("\n"):
        line = line.rstrip()

        # Skip empty lines
        if not line:
            continue

        # Check for list item
        if line.startswith("  - ") and current_key:
            if current_list is None:
                current_list = []
                frontmatter[current_key] = current_list
            current_list.append(line[4:].strip())
            continue

        # Check for key: value
        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip()

            current_key = key
            current_list = None

            if value:
                # Handle quoted strings
                if (
                    value.startswith('"')
                    and value.endswith('"')
                    or value.startswith("'")
                    and value.endswith("'")
                ):
                    value = value[1:-1]
                frontmatter[key] = value
            # If no value, might be a list (will be populated by subsequent lines)

    return frontmatter, instructions


def discover_skills(
    directories: list[SkillDirectory],
    backend: Any | None = None,
) -> list[Skill]:
    """Discover skills from the filesystem.

    Args:
        directories: List of directories to search for skills.
        backend: Optional backend for virtual filesystem support.

    Returns:
        List of discovered skills (frontmatter only).
    """
    skills: list[Skill] = []

    for skill_dir in directories:
        dir_path = Path(skill_dir["path"]).expanduser()
        recursive = skill_dir.get("recursive", True)

        if not dir_path.exists():
            continue

        # Find all SKILL.md files
        pattern = "**/SKILL.md" if recursive else "*/SKILL.md"
        for skill_file in dir_path.glob(pattern):
            try:
                content = skill_file.read_text()
                frontmatter, _ = parse_skill_md(content)

                if not frontmatter.get("name"):
                    # Skip skills without a name
                    continue

                # Get list of resources (other files in the skill directory)
                skill_folder = skill_file.parent
                resources = [
                    str(f.relative_to(skill_folder))
                    for f in skill_folder.iterdir()
                    if f.is_file() and f.name != "SKILL.md"
                ]

                skill: Skill = {
                    "name": frontmatter.get("name", skill_folder.name),
                    "description": frontmatter.get("description", ""),
                    "path": str(skill_folder),
                    "tags": frontmatter.get("tags", []),
                    "version": frontmatter.get("version", "1.0.0"),
                    "author": frontmatter.get("author", ""),
                    "frontmatter_loaded": True,
                }

                if resources:
                    skill["resources"] = resources

                skills.append(skill)

            except Exception:  # pragma: no cover
                # Skip invalid skill files
                continue

    return skills


def load_skill_instructions(skill_path: str) -> str:
    """Load full instructions for a skill.

    Args:
        skill_path: Path to the skill directory.

    Returns:
        Full markdown instructions from SKILL.md.
    """
    skill_file = Path(skill_path) / "SKILL.md"

    if not skill_file.exists():
        return f"Error: SKILL.md not found at {skill_path}"

    content = skill_file.read_text()
    _, instructions = parse_skill_md(content)

    return instructions


def get_skills_system_prompt(
    deps: DeepAgentDeps,
    skills: list[Skill] | None = None,
) -> str:
    """Generate system prompt for skills.

    Args:
        deps: Agent dependencies.
        skills: List of available skills.

    Returns:
        System prompt section describing available skills.
    """
    if not skills:
        return ""

    lines = [
        "## Available Skills",
        "",
        "You have access to skills that extend your capabilities. "
        "Use `list_skills` to see available skills and `load_skill` to load instructions.",
        "",
    ]

    for skill in skills:
        tags_str = ", ".join(skill["tags"]) if skill["tags"] else ""
        tags_part = f" [{tags_str}]" if tags_str else ""
        lines.append(f"- **{skill['name']}**{tags_part}: {skill['description']}")

    return "\n".join(lines)


class SkillsToolset(FunctionToolset[DeepAgentDeps]):
    """Toolset for skills functionality."""

    pass


def create_skills_toolset(  # noqa: C901
    *,
    id: str = "skills",
    directories: list[SkillDirectory] | None = None,
    skills: list[Skill] | None = None,
) -> SkillsToolset:
    """Create a skills toolset.

    Args:
        id: Unique identifier for this toolset.
        directories: List of directories to discover skills from.
        skills: Pre-loaded skills (alternative to directories).

    Returns:
        Configured SkillsToolset instance.
    """
    toolset = SkillsToolset(id=id)

    # Discover or use provided skills
    if skills is None and directories:
        skills = discover_skills(directories)
    elif skills is None:
        # Default skills directory
        skills = discover_skills([{"path": DEFAULT_SKILLS_DIR, "recursive": True}])

    # Store skills in toolset for access by tools
    _skills_cache: dict[str, Skill] = {skill["name"]: skill for skill in (skills or [])}

    @toolset.tool
    async def list_skills(ctx: RunContext[DeepAgentDeps]) -> str:  # pragma: no cover
        """List all available skills.

        Returns a summary of each skill with its name, description, and tags.
        Use load_skill to get full instructions for a specific skill.

        Returns:
            Formatted list of available skills.
        """
        if not _skills_cache:
            return "No skills available."

        lines = ["Available Skills:", ""]

        for name, skill in sorted(_skills_cache.items()):
            tags_str = ", ".join(skill["tags"]) if skill["tags"] else "none"
            resources_str = ""
            if skill.get("resources"):
                resources_str = f" (resources: {', '.join(skill['resources'])})"

            lines.append(f"**{name}** (v{skill['version']})")
            lines.append(f"  Description: {skill['description']}")
            lines.append(f"  Tags: {tags_str}")
            lines.append(f"  Path: {skill['path']}{resources_str}")
            lines.append("")

        return "\n".join(lines)

    @toolset.tool
    async def load_skill(  # pragma: no cover
        ctx: RunContext[DeepAgentDeps],
        skill_name: str,
    ) -> str:
        """Load full instructions for a skill.

        This loads the complete SKILL.md content including detailed instructions
        on how to use the skill.

        Args:
            skill_name: Name of the skill to load.

        Returns:
            Full skill instructions in markdown format.
        """
        if skill_name not in _skills_cache:
            available = ", ".join(_skills_cache.keys()) if _skills_cache else "none"
            return f"Error: Skill '{skill_name}' not found. Available skills: {available}"

        skill = _skills_cache[skill_name]
        instructions = load_skill_instructions(skill["path"])

        # Update cache with full instructions
        skill["instructions"] = instructions
        skill["frontmatter_loaded"] = False

        # Format response
        lines = [
            f"# Skill: {skill['name']}",
            f"Version: {skill['version']}",
            f"Path: {skill['path']}",
            "",
            "## Instructions",
            "",
            instructions,
        ]

        if skill.get("resources"):
            lines.extend(
                [
                    "",
                    "## Available Resources",
                    "",
                ]
            )
            for resource in skill["resources"]:
                lines.append(f"- {skill['path']}/{resource}")

        return "\n".join(lines)

    @toolset.tool
    async def read_skill_resource(  # pragma: no cover
        ctx: RunContext[DeepAgentDeps],
        skill_name: str,
        resource_name: str,
    ) -> str:
        """Read a resource file from a skill.

        Skills can include additional files (scripts, templates, documents)
        that support their functionality.

        Args:
            skill_name: Name of the skill.
            resource_name: Name of the resource file within the skill.

        Returns:
            Content of the resource file.
        """
        if skill_name not in _skills_cache:
            return f"Error: Skill '{skill_name}' not found."

        skill = _skills_cache[skill_name]
        resource_path = Path(skill["path"]) / resource_name

        if not resource_path.exists():
            available = skill.get("resources", [])
            return f"Error: Resource '{resource_name}' not found. Available: {available}"

        # Security check: ensure resource is within skill directory
        try:
            resource_path.resolve().relative_to(Path(skill["path"]).resolve())
        except ValueError:
            return "Error: Resource path escapes skill directory."

        try:
            return resource_path.read_text()
        except Exception as e:
            return f"Error reading resource: {e}"

    return toolset
