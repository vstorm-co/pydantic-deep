"""Main agent factory for pydantic-deep."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

from pydantic_ai import Agent
from pydantic_ai.tools import Tool

from pydantic_deep.backends.protocol import BackendProtocol, SandboxProtocol
from pydantic_deep.backends.state import StateBackend
from pydantic_deep.deps import DeepAgentDeps
from pydantic_deep.toolsets.filesystem import (
    create_filesystem_toolset,
    get_filesystem_system_prompt,
)
from pydantic_deep.toolsets.skills import create_skills_toolset, get_skills_system_prompt
from pydantic_deep.toolsets.subagents import create_subagent_toolset, get_subagent_system_prompt
from pydantic_deep.toolsets.todo import create_todo_toolset, get_todo_system_prompt
from pydantic_deep.types import Skill, SkillDirectory, SubAgentConfig

if TYPE_CHECKING:
    from pydantic_ai.toolsets import AbstractToolset


DEFAULT_MODEL = "anthropic:claude-sonnet-4-20250514"

DEFAULT_INSTRUCTIONS = """
You are a helpful AI assistant with access to planning, filesystem, subagent, and skills tools.

## Capabilities
- **Planning**: Use the todo list to break down complex tasks and track progress
- **Filesystem**: Read, write, and search files
- **Subagents**: Delegate specialized tasks to subagents
- **Skills**: Load and use modular skill packages for specialized tasks

## Best Practices
1. Plan before acting - use the todo list for complex tasks
2. Read files before editing them
3. Mark tasks as in_progress when starting, completed when done
4. Delegate specialized work to appropriate subagents
5. Check available skills for specialized tasks - load skill instructions when needed
6. Be thorough but efficient
"""


def create_deep_agent(  # noqa: C901
    model: str | None = None,
    instructions: str | None = None,
    tools: Sequence[Tool[DeepAgentDeps] | Any] | None = None,
    toolsets: Sequence[AbstractToolset[DeepAgentDeps]] | None = None,
    subagents: list[SubAgentConfig] | None = None,
    skills: list[Skill] | None = None,
    skill_directories: list[SkillDirectory] | None = None,
    backend: BackendProtocol | None = None,
    include_todo: bool = True,
    include_filesystem: bool = True,
    include_subagents: bool = True,
    include_skills: bool = True,
    include_general_purpose_subagent: bool = True,
    interrupt_on: dict[str, bool] | None = None,
    **agent_kwargs: Any,
) -> Agent[DeepAgentDeps, str]:
    """Create a deep agent with planning, filesystem, subagent, and skills capabilities.

    This factory function creates a fully-configured Agent with:
    - Todo toolset for task planning and tracking
    - Filesystem toolset for file operations
    - Subagent toolset for task delegation
    - Skills toolset for modular capability extension
    - Dynamic system prompts based on current state

    Args:
        model: Model to use (default: Claude Sonnet 4).
        instructions: Custom instructions for the agent.
        tools: Additional tools to register.
        toolsets: Additional toolsets to register.
        subagents: Subagent configurations for the task tool.
        skills: Pre-loaded skills to make available.
        skill_directories: Directories to discover skills from.
        backend: File storage backend (default: StateBackend).
        include_todo: Whether to include the todo toolset.
        include_filesystem: Whether to include the filesystem toolset.
        include_subagents: Whether to include the subagent toolset.
        include_skills: Whether to include the skills toolset.
        include_general_purpose_subagent: Whether to include a general-purpose subagent.
        interrupt_on: Map of tool names to approval requirements.
            e.g., {"execute": True, "write_file": True}
        **agent_kwargs: Additional arguments passed to Agent constructor.

    Returns:
        Configured Agent[DeepAgentDeps, str] instance.

    Example:
        ```python
        from pydantic_deep import create_deep_agent, DeepAgentDeps, StateBackend

        agent = create_deep_agent(
            model="anthropic:claude-sonnet-4-20250514",
            instructions="You are a coding assistant",
            skill_directories=[{"path": "~/.pydantic-deep/skills"}],
            interrupt_on={"execute": True},
        )

        deps = DeepAgentDeps(backend=StateBackend())
        result = await agent.run("Create a hello world script", deps=deps)
        ```
    """
    model = model or DEFAULT_MODEL
    backend = backend or StateBackend()
    interrupt_on = interrupt_on or {}

    # Build toolsets list
    all_toolsets: list[AbstractToolset[DeepAgentDeps]] = []

    if include_todo:
        todo_toolset = create_todo_toolset(id="deep-todo")
        all_toolsets.append(todo_toolset)

    if include_filesystem:
        # Determine approval requirements from interrupt_on
        require_write_approval = interrupt_on.get("write_file", False) or interrupt_on.get(
            "edit_file", False
        )
        require_execute_approval = interrupt_on.get("execute", True)
        include_execute = isinstance(backend, SandboxProtocol)

        fs_toolset = create_filesystem_toolset(
            id="deep-filesystem",
            include_execute=include_execute,
            require_write_approval=require_write_approval,
            require_execute_approval=require_execute_approval,
        )
        all_toolsets.append(fs_toolset)

    if include_subagents:
        subagent_toolset = create_subagent_toolset(
            id="deep-subagents",
            subagents=subagents,
            default_model=model,
            include_general_purpose=include_general_purpose_subagent,
        )
        all_toolsets.append(subagent_toolset)

    # Skills toolset
    loaded_skills: list[Skill] = []
    if include_skills:
        skills_toolset = create_skills_toolset(
            id="deep-skills",
            directories=skill_directories,
            skills=skills,
        )
        all_toolsets.append(skills_toolset)
        # Track loaded skills for system prompt
        if skills:
            loaded_skills = skills
        elif skill_directories:
            from pydantic_deep.toolsets.skills import discover_skills

            loaded_skills = discover_skills(skill_directories)

    # Add user-provided toolsets
    if toolsets:
        all_toolsets.extend(toolsets)

    # Build base instructions
    base_instructions = instructions or DEFAULT_INSTRUCTIONS

    # Create the agent
    agent: Agent[DeepAgentDeps, str] = Agent(
        model,
        deps_type=DeepAgentDeps,
        toolsets=all_toolsets,
        instructions=base_instructions,
        **agent_kwargs,
    )

    # Add dynamic system prompts
    @agent.instructions
    def dynamic_instructions(ctx) -> str:  # pragma: no cover
        """Generate dynamic instructions based on current state."""
        parts = []

        if include_todo:
            todo_prompt = get_todo_system_prompt(ctx.deps)
            if todo_prompt:
                parts.append(todo_prompt)

        if include_filesystem:
            fs_prompt = get_filesystem_system_prompt(ctx.deps)
            if fs_prompt:
                parts.append(fs_prompt)

        if include_subagents:
            subagent_prompt = get_subagent_system_prompt(ctx.deps, subagents)
            if subagent_prompt:
                parts.append(subagent_prompt)

        if include_skills and loaded_skills:
            skills_prompt = get_skills_system_prompt(ctx.deps, loaded_skills)
            if skills_prompt:
                parts.append(skills_prompt)

        return "\n\n".join(parts) if parts else ""

    # Add user-provided tools
    if tools:
        for tool in tools:
            if isinstance(tool, Tool):
                agent.tool(tool.function)  # pragma: no cover
            else:
                agent.tool(tool)

    return agent


def create_default_deps(
    backend: BackendProtocol | None = None,
) -> DeepAgentDeps:
    """Create default dependencies for a deep agent.

    Args:
        backend: File storage backend (default: StateBackend).

    Returns:
        DeepAgentDeps instance.
    """
    return DeepAgentDeps(backend=backend or StateBackend())
