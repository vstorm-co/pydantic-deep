"""Todo toolset for task planning and tracking."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field
from pydantic_ai import RunContext
from pydantic_ai.toolsets import FunctionToolset

from pydantic_deep.deps import DeepAgentDeps
from pydantic_deep.types import Todo


class TodoItem(BaseModel):
    """A todo item for the write_todos tool."""

    content: str = Field(
        ..., description="The task description in imperative form (e.g., 'Implement feature X')"
    )
    status: Literal["pending", "in_progress", "completed"] = Field(
        ..., description="Task status: pending, in_progress, or completed"
    )
    active_form: str = Field(
        ...,
        description="Present continuous form during execution (e.g., 'Implementing feature X')",
    )


TODO_TOOL_DESCRIPTION = """
Use this tool to create and manage a structured task list for your current session.
This helps you track progress, organize complex tasks, and demonstrate thoroughness.

## When to Use This Tool
Use this tool in these scenarios:
1. Complex multi-step tasks - When a task requires 3 or more distinct steps
2. Non-trivial tasks - Tasks that require careful planning
3. User provides multiple tasks - When users provide a list of things to be done
4. After receiving new instructions - Capture user requirements as todos
5. When starting a task - Mark it as in_progress BEFORE beginning work
6. After completing a task - Mark it as completed immediately

## Task States
- pending: Task not yet started
- in_progress: Currently working on (limit to ONE at a time)
- completed: Task finished successfully

## Important
- Exactly ONE task should be in_progress at any time
- Mark tasks complete IMMEDIATELY after finishing (don't batch completions)
- If you encounter blockers, keep the task as in_progress and create a new task for the blocker
"""

TODO_SYSTEM_PROMPT = """
## Task Management

You have access to the `write_todos` tool to track your tasks.
Use it frequently to:
- Plan complex tasks before starting
- Show progress to the user
- Keep track of what's done and what's pending

When working on tasks:
1. Break down complex tasks into smaller steps
2. Mark exactly one task as in_progress at a time
3. Mark tasks as completed immediately after finishing
"""


def create_todo_toolset(id: str | None = None) -> FunctionToolset[DeepAgentDeps]:
    """Create a todo toolset for task management.

    Args:
        id: Optional unique ID for the toolset.

    Returns:
        FunctionToolset with the write_todos tool.
    """
    toolset: FunctionToolset[DeepAgentDeps] = FunctionToolset(id=id)

    @toolset.tool
    async def write_todos(  # pragma: no cover
        ctx: RunContext[DeepAgentDeps],
        todos: list[TodoItem],
    ) -> str:
        """Update the todo list with new items.

        Use this tool to create and manage a structured task list.
        This helps track progress and organize complex tasks.

        Args:
            todos: List of todo items with content, status, and active_form.
        """
        # Convert to internal Todo format
        ctx.deps.todos = [
            Todo(content=t.content, status=t.status, active_form=t.active_form) for t in todos
        ]

        # Count by status
        counts = {"pending": 0, "in_progress": 0, "completed": 0}
        for todo in ctx.deps.todos:
            counts[todo.status] += 1

        return (
            f"Updated {len(todos)} todos: "
            f"{counts['completed']} completed, "
            f"{counts['in_progress']} in progress, "
            f"{counts['pending']} pending"
        )

    return toolset


def get_todo_system_prompt(deps: DeepAgentDeps) -> str:
    """Generate dynamic system prompt section for todos.

    Args:
        deps: The agent dependencies containing todos.

    Returns:
        System prompt section with current todos, or empty string if no todos.
    """
    if not deps.todos:
        return TODO_SYSTEM_PROMPT

    lines = [TODO_SYSTEM_PROMPT, "", "## Current Todos"]

    for todo in deps.todos:
        status_icon = {
            "pending": "[ ]",
            "in_progress": "[*]",
            "completed": "[x]",
        }.get(todo.status, "[ ]")
        lines.append(f"- {status_icon} {todo.content}")

    return "\n".join(lines)


# Alias for convenience
TodoToolset = create_todo_toolset
