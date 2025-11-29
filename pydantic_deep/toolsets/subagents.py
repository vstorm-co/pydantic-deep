"""SubAgent toolset for task delegation."""

from __future__ import annotations

from pydantic_ai import Agent, RunContext
from pydantic_ai.toolsets import FunctionToolset

from pydantic_deep.deps import DeepAgentDeps
from pydantic_deep.types import SubAgentConfig

SUBAGENT_SYSTEM_PROMPT = """
## Task Delegation

You have access to the `task` tool for delegating work to specialized subagents.
Use this when:

1. A task requires specialized knowledge or tools
2. You want to isolate a complex subtask
3. Parallel work would be beneficial
4. The task would benefit from a fresh context

Subagents have:
- Their own system prompts and tools
- Fresh context (no access to your conversation history)
- Access to the same filesystem

When delegating:
- Provide clear, specific instructions
- Specify the expected output format
- The subagent will return a summary of their work
"""

DEFAULT_GENERAL_PURPOSE_DESCRIPTION = """
A general-purpose agent for complex, multi-step tasks.
Use this for tasks that don't match a specific subagent type.
The agent can search code, analyze files, and perform research.
"""

TASK_TOOL_DESCRIPTION = """
Launch a subagent to handle a specific task autonomously.

The subagent will:
- Receive your task description as their prompt
- Have access to file operations
- Return a summary of their findings/actions

Use this for:
- Complex research tasks
- Multi-step operations
- Tasks requiring different expertise
"""


def create_subagent_toolset(
    subagents: list[SubAgentConfig] | None = None,
    default_model: str = "anthropic:claude-sonnet-4-20250514",
    include_general_purpose: bool = True,
    id: str | None = None,
) -> FunctionToolset[DeepAgentDeps]:
    """Create a subagent toolset for task delegation.

    Args:
        subagents: List of subagent configurations.
        default_model: Default model for subagents.
        include_general_purpose: Whether to include a general-purpose subagent.
        id: Optional unique ID for the toolset.

    Returns:
        FunctionToolset with the task tool.
    """
    subagent_configs = list(subagents or [])

    # Add general-purpose subagent if requested
    if include_general_purpose:
        gp_config = SubAgentConfig(
            name="general-purpose",
            description=DEFAULT_GENERAL_PURPOSE_DESCRIPTION,
            instructions="You are a general-purpose agent. "
            "Complete the given task thoroughly and report your findings.",
        )
        subagent_configs.append(gp_config)

    # Build description of available subagents
    subagent_descriptions = []
    for config in subagent_configs:
        subagent_descriptions.append(f"- {config['name']}: {config['description'].strip()}")

    available_subagents = (
        "\n".join(subagent_descriptions) if subagent_descriptions else "No subagents configured"
    )

    toolset: FunctionToolset[DeepAgentDeps] = FunctionToolset(id=id)

    @toolset.tool
    async def task(  # pragma: no cover
        ctx: RunContext[DeepAgentDeps],
        description: str,
        subagent_type: str,
    ) -> str:
        """Launch a subagent to handle a specific task.

        The subagent will work autonomously and return a summary of their work.
        Subagents have access to the same filesystem but a fresh context.

        Args:
            description: Detailed description of the task for the subagent.
            subagent_type: Type of subagent to use (e.g., "general-purpose").
        """
        # Find the subagent config
        config = None
        for c in subagent_configs:
            if c["name"] == subagent_type:
                config = c
                break

        if config is None:
            available = ", ".join(c["name"] for c in subagent_configs)
            return f"Error: Unknown subagent type '{subagent_type}'. Available: {available}"

        # Check if we have a pre-built agent
        if subagent_type in ctx.deps.subagents:
            subagent = ctx.deps.subagents[subagent_type]
        else:
            # Create the subagent on-the-fly
            from pydantic_deep.toolsets.filesystem import create_filesystem_toolset
            from pydantic_deep.toolsets.todo import create_todo_toolset

            model = config.get("model", default_model)
            tools = config.get("tools", [])

            # Create toolsets for the subagent
            fs_toolset = create_filesystem_toolset(
                include_execute=True,
                require_write_approval=False,
                require_execute_approval=False,
            )
            todo_toolset = create_todo_toolset()

            subagent = Agent(
                model,
                instructions=config["instructions"],
                deps_type=type(ctx.deps),
                toolsets=[fs_toolset, todo_toolset],
            )

            # Add custom tools if any
            for tool in tools:
                subagent.tool(tool)

            # Cache the subagent
            ctx.deps.subagents[subagent_type] = subagent

        # Create isolated deps for the subagent
        subagent_deps = ctx.deps.clone_for_subagent()

        # Run the subagent
        try:
            result = await subagent.run(description, deps=subagent_deps)
            return f"Subagent '{subagent_type}' completed:\n\n{result.output}"
        except Exception as e:
            return f"Subagent '{subagent_type}' failed: {e}"

    # Update the tool's docstring with available subagents
    if task.__doc__:  # pragma: no branch
        task.__doc__ += f"\n\nAvailable subagent types:\n{available_subagents}"

    return toolset


def get_subagent_system_prompt(
    deps: DeepAgentDeps, subagent_configs: list[SubAgentConfig] | None = None
) -> str:
    """Generate dynamic system prompt for subagent tools.

    Args:
        deps: The agent dependencies.
        subagent_configs: List of subagent configurations.

    Returns:
        System prompt section for subagent tools.
    """
    prompt = SUBAGENT_SYSTEM_PROMPT

    if subagent_configs:
        prompt += "\n\n### Available Subagents\n"
        for config in subagent_configs:
            prompt += f"\n**{config['name']}**: {config['description'].strip()}\n"

    if deps.subagents:
        prompt += "\n\n### Cached Subagents\n"
        prompt += f"Active subagents: {', '.join(deps.subagents.keys())}\n"

    return prompt


# Alias for convenience
SubAgentToolset = create_subagent_toolset
