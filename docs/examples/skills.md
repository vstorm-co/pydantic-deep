# Skills Example

This example demonstrates the skills system for modular capability extension.

## Source Code

:material-file-code: `examples/skills_usage.py`

## Overview

Skills are modular packages that:

- Extend agent capabilities
- Use progressive disclosure (frontmatter → full instructions)
- Include optional resource files

## Example Skills

The example includes two skills in `examples/skills/`:

### Code Review Skill

```
examples/skills/code-review/
├── SKILL.md
└── example_review.md
```

**SKILL.md:**
```yaml
---
name: code-review
description: Review Python code for quality, security, and best practices
version: 1.0.0
tags:
  - code
  - review
  - python
  - quality
author: pydantic-deep
---

# Code Review Skill

When reviewing code, follow these guidelines:

## Review Process
1. Read the entire file before making comments
2. Check for security issues first
3. Review code structure and patterns
...
```

### Test Generator Skill

```
examples/skills/test-generator/
└── SKILL.md
```

**SKILL.md:**
```yaml
---
name: test-generator
description: Generate pytest test cases for Python functions and classes
version: 1.0.0
tags:
  - testing
  - pytest
  - python
---

# Test Generator Skill

Generate comprehensive pytest tests...
```

## Full Example

```python
"""Skills usage example."""

import asyncio
from pathlib import Path

from pydantic_deep import create_deep_agent, DeepAgentDeps, StateBackend


SKILLS_DIR = Path(__file__).parent / "skills"


async def main():
    # Create agent with skills
    agent = create_deep_agent(
        model="anthropic:claude-sonnet-4-20250514",
        instructions="""
        You are a coding assistant with specialized skills.

        When asked to review code or generate tests:
        1. First check available skills with list_skills
        2. Load the relevant skill with load_skill
        3. Follow the skill's guidelines

        Always use skill instructions for specialized tasks.
        """,
        skill_directories=[
            {"path": str(SKILLS_DIR), "recursive": True},
        ],
    )

    deps = DeepAgentDeps(backend=StateBackend())

    # Create some code to review
    deps.backend.write(
        "/code/example.py",
        '''def calculate_total(items):
    total = 0
    for item in items:
        total = total + item["price"] * item["quantity"]
    return total

def get_user_data(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return db.execute(query)
''',
    )

    # Ask agent to use skills
    result = await agent.run(
        """
        1. List your available skills
        2. Load the code-review skill
        3. Review /code/example.py following the skill's guidelines
        """,
        deps=deps,
    )

    print(result.output)


asyncio.run(main())
```

## Running Without API Key

The example supports running without an API key for demonstration:

```bash
# List discovered skills
uv run python examples/skills_usage.py --discover

# Load skill instructions
uv run python examples/skills_usage.py --load
```

### Discovery Output

```
Discovering skills from: /path/to/examples/skills

Skill: test-generator
  Description: Generate pytest test cases for Python functions and classes
  Version: 1.0.0
  Tags: testing, pytest, python
  Path: /path/to/examples/skills/test-generator

Skill: code-review
  Description: Review Python code for quality, security, and best practices
  Version: 1.0.0
  Tags: code, review, python, quality
  Path: /path/to/examples/skills/code-review
  Resources: example_review.md
```

## Skill Tools

### list_skills

Returns all available skills with metadata:

```python
# Agent output:
Available Skills:

**code-review** (v1.0.0)
  Description: Review Python code for quality, security, and best practices
  Tags: code, review, python, quality
  Path: /path/to/skill (resources: example_review.md)

**test-generator** (v1.0.0)
  Description: Generate pytest test cases for Python functions and classes
  Tags: testing, pytest, python
  Path: /path/to/skill
```

### load_skill

Loads full instructions for a specific skill:

```python
# Agent calls: load_skill(skill_name="code-review")
# Returns complete SKILL.md content with detailed instructions
```

### read_skill_resource

Reads additional files from a skill:

```python
# Agent calls: read_skill_resource(
#     skill_name="code-review",
#     resource_name="example_review.md"
# )
# Returns the resource file content
```

## Creating Your Own Skills

### 1. Create Directory

```bash
mkdir -p ~/.pydantic-deep/skills/my-skill
```

### 2. Write SKILL.md

```markdown
---
name: my-skill
description: What this skill does
version: 1.0.0
tags:
  - tag1
  - tag2
author: your-name
---

# My Skill

Detailed instructions for the agent...

## When to Use

Use this skill when...

## Process

1. Step one
2. Step two
3. Step three

## Output Format

Provide output in this format:
...
```

### 3. Add Resources (Optional)

```bash
# Templates, examples, checklists, etc.
echo "# Template" > ~/.pydantic-deep/skills/my-skill/template.md
```

### 4. Configure Agent

```python
agent = create_deep_agent(
    skill_directories=[
        {"path": "~/.pydantic-deep/skills", "recursive": True},
    ],
)
```

## Best Practices

1. **Clear descriptions** - Help the agent choose the right skill
2. **Focused skills** - One skill, one purpose
3. **Actionable instructions** - Tell the agent exactly what to do
4. **Include examples** - Show expected output format
5. **Version your skills** - Track changes over time

## Next Steps

- [Concepts: Skills](../concepts/skills.md) - Deep dive
- [Docker Sandbox](docker-sandbox.md) - Isolated execution
- [API Reference](../api/toolsets.md) - SkillsToolset API
