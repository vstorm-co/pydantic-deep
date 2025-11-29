"""Example using CompositeBackend for mixed storage.

This example demonstrates:
- Combining multiple backends
- Routing operations by path prefix
- Using persistent and ephemeral storage together
"""

import asyncio
import tempfile
from pathlib import Path

from pydantic_deep import (
    CompositeBackend,
    DeepAgentDeps,
    FilesystemBackend,
    StateBackend,
    create_deep_agent,
)


async def main():
    # Create a temporary directory for persistent storage
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        print(f"Persistent storage: {workspace}")

        # Create backends:
        # - StateBackend for temporary/scratch files
        # - FilesystemBackend for persistent project files
        memory_backend = StateBackend()
        fs_backend = FilesystemBackend(workspace, virtual_mode=True)

        # Create composite backend with routing rules
        backend = CompositeBackend(
            default=memory_backend,  # Default to memory for unmatched paths
            routes={
                "/project/": fs_backend,  # Project files go to disk
                "/workspace/": fs_backend,  # Workspace files go to disk
            },
        )

        # Create the agent
        agent = create_deep_agent(
            model="anthropic:claude-sonnet-4-20250514",
            instructions="""
            You are a project assistant.

            File organization:
            - /project/ - Persistent project files (saved to disk)
            - /workspace/ - Working files (saved to disk)
            - /temp/ or /scratch/ - Temporary files (in memory only)

            Use the appropriate location based on whether files should persist.
            """,
        )

        deps = DeepAgentDeps(backend=backend)

        # Run the agent
        result = await agent.run(
            """Create a small Python project:
            1. Create /project/src/app.py with a simple Flask app
            2. Create /project/requirements.txt with dependencies
            3. Create /scratch/notes.txt with implementation notes (temporary)
            4. Create /project/README.md with project description
            """,
            deps=deps,
        )

        print("Agent output:")
        print(result.output)

        # Show what's in memory (temporary files)
        print("\nTemporary files (in memory):")
        for path in sorted(memory_backend.files.keys()):
            print(f"  {path}")

        # Show what's on disk (persistent files)
        print("\nPersistent files (on disk):")
        for path in workspace.rglob("*"):
            if path.is_file():
                rel_path = path.relative_to(workspace)
                print(f"  {rel_path}")

        # Read a persistent file
        readme = workspace / "project" / "README.md"
        if readme.exists():
            print("\nContent of README.md:")
            print(readme.read_text())


if __name__ == "__main__":
    asyncio.run(main())
