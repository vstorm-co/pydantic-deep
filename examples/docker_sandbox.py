"""Example using DockerSandbox for isolated command execution.

This example demonstrates:
- Using DockerSandbox for safe command execution
- Running code in an isolated container
- Combining file operations with execution

Note: Requires Docker to be installed and running.
"""

import asyncio

from pydantic_deep import DeepAgentDeps, create_deep_agent
from pydantic_deep.backends.sandbox import DockerSandbox


async def main():
    # Create a Docker sandbox
    # This will spin up a container when first used
    sandbox = DockerSandbox(
        image="python:3.12-slim",
        work_dir="/workspace",
    )

    try:
        # Create the agent with the sandbox backend
        agent = create_deep_agent(
            model="anthropic:claude-sonnet-4-20250514",
            instructions="""
            You are a Python development assistant.
            You can write code, save it to files, and execute it in a sandbox.
            Always test your code by running it.
            """,
            # With DockerSandbox, execute is available
            # We still require approval for safety
            interrupt_on={"execute": True},
        )

        deps = DeepAgentDeps(backend=sandbox)

        # Run the agent
        result = await agent.run(
            """Create a Python script that:
            1. Defines a function to calculate fibonacci numbers
            2. Prints the first 10 fibonacci numbers
            3. Save it to /workspace/fibonacci.py
            4. Run it and show the output
            """,
            deps=deps,
        )

        print("Agent output:")
        print(result.output)

    finally:
        # Clean up the container
        sandbox.stop()


if __name__ == "__main__":
    print("Note: This example requires Docker to be installed and running.")
    print("Install docker package: uv add docker")
    print()

    try:
        import docker  # noqa: F401

        asyncio.run(main())
    except ImportError:
        print("Docker package not installed. Run: uv add docker")
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure Docker daemon is running.")
