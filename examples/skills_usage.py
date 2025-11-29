"""Example demonstrating skills usage with pydantic-deep.

This example shows:
- Discovering skills from directories
- Listing available skills
- Loading skill instructions on demand
- Using skill resources
- Progressive disclosure (frontmatter vs full instructions)

Skills are modular packages that extend agent capabilities. Each skill is a folder
containing a SKILL.md file with YAML frontmatter and Markdown instructions.
"""

import asyncio
from pathlib import Path

from pydantic_deep import DeepAgentDeps, StateBackend, create_deep_agent

# Get the skills directory relative to this example
SKILLS_DIR = Path(__file__).parent / "skills"


async def main():
    # Create the agent with skills
    agent = create_deep_agent(
        model="anthropic:claude-sonnet-4-20250514",
        instructions="""
        You are a helpful coding assistant with access to specialized skills.

        When asked to review code or generate tests, first check your available
        skills using `list_skills`. Then load the relevant skill with `load_skill`
        to get detailed instructions on how to perform the task.

        Always follow the skill's guidelines when performing specialized tasks.
        """,
        skill_directories=[
            {"path": str(SKILLS_DIR), "recursive": True},
        ],
    )

    deps = DeepAgentDeps(backend=StateBackend())

    # Example 1: List available skills
    print("=" * 60)
    print("Example 1: Listing available skills")
    print("=" * 60)

    result = await agent.run(
        "What skills do you have available? List them with their descriptions.",
        deps=deps,
    )
    print(result.output)

    # Example 2: Use a skill to review code
    print("\n" + "=" * 60)
    print("Example 2: Using the code-review skill")
    print("=" * 60)

    # First, create a file to review
    deps.backend.write(
        "/code/example.py",
        """def calculate_total(items):
    total = 0
    for item in items:
        total = total + item["price"] * item["quantity"]
    return total

def get_user_data(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return db.execute(query)
""",
    )

    result = await agent.run(
        """Load the code-review skill and then review the code in /code/example.py.
        Follow the skill's guidelines for the review.""",
        deps=deps,
        message_history=result.all_messages(),
    )
    print(result.output)

    # Example 3: Use a skill to generate tests
    print("\n" + "=" * 60)
    print("Example 3: Using the test-generator skill")
    print("=" * 60)

    result = await agent.run(
        """Load the test-generator skill and generate pytest tests for the
        calculate_total function in /code/example.py.""",
        deps=deps,
        message_history=result.all_messages(),
    )
    print(result.output)

    # Show generated files
    print("\n" + "=" * 60)
    print("Files created:")
    print("=" * 60)
    for path in sorted(deps.backend.files.keys()):
        print(f"  {path}")


async def demo_skill_discovery():
    """Demonstrate skill discovery from multiple directories."""
    from pydantic_deep.toolsets.skills import discover_skills

    print("Discovering skills from:", SKILLS_DIR)
    print()

    skills = discover_skills([{"path": str(SKILLS_DIR), "recursive": True}])

    for skill in skills:
        print(f"Skill: {skill['name']}")
        print(f"  Description: {skill['description']}")
        print(f"  Version: {skill['version']}")
        print(f"  Tags: {', '.join(skill['tags'])}")
        print(f"  Path: {skill['path']}")
        if skill.get("resources"):
            print(f"  Resources: {', '.join(skill['resources'])}")
        print()


async def demo_skill_loading():
    """Demonstrate loading full skill instructions."""
    from pydantic_deep.toolsets.skills import discover_skills, load_skill_instructions

    skills = discover_skills([{"path": str(SKILLS_DIR), "recursive": True}])

    if skills:
        skill = skills[0]
        print(f"Loading full instructions for: {skill['name']}")
        print("=" * 60)

        instructions = load_skill_instructions(skill["path"])
        print(instructions[:500] + "..." if len(instructions) > 500 else instructions)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--discover":
        asyncio.run(demo_skill_discovery())
    elif len(sys.argv) > 1 and sys.argv[1] == "--load":
        asyncio.run(demo_skill_loading())
    else:
        print("Running full example (requires ANTHROPIC_API_KEY)")
        print("Use --discover to just list discovered skills")
        print("Use --load to demo loading skill instructions")
        print()
        asyncio.run(main())
