"""Example using FilesystemBackend for real file operations.

This example shows how to:
- Use FilesystemBackend for persistent file storage
- Work with real files on disk
"""

import asyncio
import tempfile
from pathlib import Path

from pydantic_deep import DeepAgentDeps, FilesystemBackend, create_deep_agent


async def main():
    # Create a temporary directory for our workspace
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        print(f"Workspace: {workspace}")

        # Create a FilesystemBackend pointing to the workspace
        backend = FilesystemBackend(workspace, virtual_mode=True)

        # Create the agent
        agent = create_deep_agent(
            model="anthropic:claude-sonnet-4-20250514",
            instructions="You are a file organization assistant.",
        )

        deps = DeepAgentDeps(backend=backend)

        # Run the agent to create some files
        result = await agent.run(
            """Create a simple project structure:
            1. Create /src/main.py with a hello world function
            2. Create /src/utils.py with a helper function
            3. Create /README.md with project description
            """,
            deps=deps,
        )

        print("Agent output:")
        print(result.output)

        # List actual files on disk
        print("\nFiles on disk:")
        for path in workspace.rglob("*"):
            if path.is_file():
                rel_path = path.relative_to(workspace)
                print(f"  {rel_path}")

        # Read a file from disk
        main_py = workspace / "src" / "main.py"
        if main_py.exists():
            print(f"\nContent of {main_py.name}:")
            print(main_py.read_text())


if __name__ == "__main__":
    asyncio.run(main())
