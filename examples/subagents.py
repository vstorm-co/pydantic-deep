"""Example using subagents for task delegation.

This example demonstrates:
- Configuring custom subagents
- Delegating specialized tasks
- Context isolation between agents
"""

import asyncio

from pydantic_deep import DeepAgentDeps, StateBackend, create_deep_agent
from pydantic_deep.types import SubAgentConfig


async def main():
    # Define specialized subagents
    subagents = [
        SubAgentConfig(
            name="code-reviewer",
            description="Reviews code for bugs, style issues, and best practices",
            instructions="""
            You are an expert code reviewer.
            When reviewing code:
            1. Check for bugs and logical errors
            2. Verify proper error handling
            3. Look for security issues
            4. Suggest improvements
            Provide a structured review with severity levels.
            """,
        ),
        SubAgentConfig(
            name="documentation-writer",
            description="Writes clear, comprehensive documentation",
            instructions="""
            You are a technical documentation specialist.
            Write clear, well-structured documentation including:
            - Overview and purpose
            - Usage examples
            - API reference
            - Best practices
            """,
        ),
        SubAgentConfig(
            name="test-generator",
            description="Generates comprehensive unit tests",
            instructions="""
            You are a test engineering expert.
            Generate thorough unit tests including:
            - Happy path tests
            - Edge cases
            - Error handling tests
            - Use pytest style
            """,
        ),
    ]

    # Create the main agent with subagents
    agent = create_deep_agent(
        model="anthropic:claude-sonnet-4-20250514",
        instructions="""
        You are a senior software engineer.
        Delegate specialized tasks to the appropriate subagents:
        - code-reviewer for code reviews
        - documentation-writer for docs
        - test-generator for tests

        Coordinate the work and synthesize results.
        """,
        subagents=subagents,
        include_general_purpose_subagent=False,  # Only use our custom subagents
    )

    deps = DeepAgentDeps(backend=StateBackend())

    # First, create some code to work with
    deps.backend.write(
        "/calculator.py",
        '''"""Simple calculator module."""

def add(a, b):
    return a + b

def divide(a, b):
    return a / b

def multiply(a, b):
    return a * b
''',
    )

    # Ask the agent to review, document, and test the code
    result = await agent.run(
        """I have a calculator module at /calculator.py.
        Please:
        1. Review the code for issues
        2. Write documentation for it
        3. Generate unit tests

        Save the documentation to /docs/calculator.md and tests to /tests/test_calculator.py
        """,
        deps=deps,
    )

    print("Agent output:")
    print(result.output)

    print("\nFiles created:")
    for path in sorted(deps.files.keys()):
        print(f"  {path}")


if __name__ == "__main__":
    asyncio.run(main())
