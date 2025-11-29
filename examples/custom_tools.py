"""Example adding custom tools to the agent.

This example demonstrates:
- Adding custom tools alongside built-in toolsets
- Accessing dependencies in custom tools
- Combining custom logic with file operations
"""

import asyncio
from datetime import datetime

from pydantic_ai import RunContext

from pydantic_deep import DeepAgentDeps, StateBackend, create_deep_agent


# Define custom tools as functions
async def get_current_time(ctx: RunContext[DeepAgentDeps]) -> str:
    """Get the current date and time.

    Returns:
        Current timestamp in ISO format.
    """
    return datetime.now().isoformat()


async def log_message(
    ctx: RunContext[DeepAgentDeps],
    message: str,
    level: str = "INFO",
) -> str:
    """Log a message to /logs/agent.log.

    Args:
        message: The message to log.
        level: Log level (INFO, WARNING, ERROR).
    """
    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] [{level}] {message}\n"

    # Use the backend to append to log file
    backend = ctx.deps.backend

    # Read existing log
    existing = backend.read("/logs/agent.log")
    if "Error:" in existing:
        # File doesn't exist, create it
        content = log_entry
    else:
        # Extract content (remove line numbers)
        lines = []
        for line in existing.split("\n"):
            if "\t" in line:
                lines.append(line.split("\t", 1)[1])
        content = "\n".join(lines) + log_entry

    backend.write("/logs/agent.log", content)

    return f"Logged: {log_entry.strip()}"


async def analyze_code_complexity(
    ctx: RunContext[DeepAgentDeps],
    file_path: str,
) -> str:
    """Analyze the complexity of a Python file.

    Args:
        file_path: Path to the Python file to analyze.

    Returns:
        Complexity analysis report.
    """
    content = ctx.deps.backend.read(file_path)

    if "Error:" in content:
        return content

    # Simple complexity metrics
    lines = content.split("\n")
    total_lines = len(lines)

    # Count various elements (simple heuristics)
    functions = sum(1 for line in lines if "def " in line)
    classes = sum(1 for line in lines if "class " in line)
    imports = sum(1 for line in lines if line.strip().startswith(("import ", "from ")))
    comments = sum(1 for line in lines if "#" in line)

    return f"""Code Complexity Analysis for {file_path}:
- Total lines: {total_lines}
- Functions: {functions}
- Classes: {classes}
- Imports: {imports}
- Comment lines: {comments}
- Code density: {(total_lines - comments) / max(total_lines, 1):.1%}
"""


async def main():
    # Create agent with custom tools
    agent = create_deep_agent(
        model="anthropic:claude-sonnet-4-20250514",
        instructions="""
        You are a development assistant with custom tools:
        - get_current_time: Get the current timestamp
        - log_message: Log messages to /logs/agent.log
        - analyze_code_complexity: Analyze Python file complexity

        Use these tools along with the built-in filesystem tools.
        Always log important actions.
        """,
        tools=[
            get_current_time,
            log_message,
            analyze_code_complexity,
        ],
    )

    deps = DeepAgentDeps(backend=StateBackend())

    # Run the agent
    result = await agent.run(
        """
        1. Log that we're starting a new task
        2. Create a Python module at /src/calculator.py with add, subtract, multiply functions
        3. Analyze the complexity of the created file
        4. Log the completion with the complexity summary
        5. Get the current time and save a summary to /summary.txt
        """,
        deps=deps,
    )

    print("Agent output:")
    print(result.output)

    # Show the log file
    print("\n" + "=" * 50)
    print("Log file contents:")
    log_content = deps.backend.read("/logs/agent.log")
    print(log_content)


if __name__ == "__main__":
    asyncio.run(main())
