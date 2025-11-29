# Skills

Skills are modular packages that extend agent capabilities through filesystem-based configuration. They enable **progressive disclosure** - only loading detailed instructions when needed.

## What are Skills?

A skill is a folder containing:

- `SKILL.md` - Definition with YAML frontmatter and instructions
- Optional resource files (templates, scripts, documents)

```
~/.pydantic-deep/skills/
├── code-review/
│   ├── SKILL.md
│   └── checklist.md
├── test-generator/
│   ├── SKILL.md
│   └── templates/
│       └── pytest.py
└── documentation/
    └── SKILL.md
```

## SKILL.md Format

```markdown
---
name: code-review
description: Review Python code for quality and security
version: 1.0.0
tags:
  - code
  - review
  - python
author: your-name
---

# Code Review Skill

Detailed instructions for the agent...

## Review Process

1. Read the entire file first
2. Check for security issues
3. Review code structure
...
```

### Frontmatter Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Unique skill identifier |
| `description` | Yes | Brief description (shown in list) |
| `version` | No | Semantic version (default: "1.0.0") |
| `tags` | No | List of tags for categorization |
| `author` | No | Skill author |

## Progressive Disclosure

Skills use progressive disclosure to optimize token usage:

### 1. Discovery (Low Cost)

Only YAML frontmatter is loaded:

```python
# Agent calls list_skills()
# Returns:
# - code-review: Review Python code for quality and security [code, review]
# - test-generator: Generate pytest test cases [testing, python]
```

### 2. Loading (On Demand)

Full instructions loaded when needed:

```python
# Agent calls load_skill("code-review")
# Returns complete SKILL.md content
```

### 3. Resources (As Needed)

Additional files accessed individually:

```python
# Agent calls read_skill_resource("code-review", "checklist.md")
# Returns specific resource file
```

## Using Skills

### Enable Skills

```python
from pydantic_deep import create_deep_agent

agent = create_deep_agent(
    skill_directories=[
        {"path": "~/.pydantic-deep/skills", "recursive": True},
    ],
    include_skills=True,
)
```

### Available Tools

| Tool | Description |
|------|-------------|
| `list_skills` | List all available skills |
| `load_skill` | Load full instructions for a skill |
| `read_skill_resource` | Read a resource file from a skill |

### Agent Workflow

The agent typically:

1. Receives a task ("Review this code for security issues")
2. Lists available skills to find relevant ones
3. Loads the appropriate skill instructions
4. Follows the skill's guidelines
5. Accesses resources as needed

## Creating Skills

### Step 1: Create Directory

```bash
mkdir -p ~/.pydantic-deep/skills/my-skill
```

### Step 2: Write SKILL.md

```markdown
---
name: api-design
description: Design RESTful APIs following best practices
version: 1.0.0
tags:
  - api
  - rest
  - design
author: your-name
---

# API Design Skill

You are an API design expert. When designing APIs, follow these principles:

## REST Conventions

- Use nouns for resources: `/users`, `/orders`
- Use HTTP methods correctly: GET, POST, PUT, DELETE
- Version your API: `/v1/users`

## Response Format

Always return JSON with consistent structure:

```json
{
  "data": {...},
  "meta": {
    "page": 1,
    "total": 100
  }
}
```

## Error Handling

Return appropriate status codes:
- 400: Bad request
- 401: Unauthorized
- 404: Not found
- 500: Server error
```

### Step 3: Add Resources (Optional)

```bash
# Create a template file
cat > ~/.pydantic-deep/skills/api-design/openapi-template.yaml << 'EOF'
openapi: 3.0.0
info:
  title: API Name
  version: 1.0.0
paths: {}
EOF
```

## Skill Discovery

### From Directories

```python
from pydantic_deep.toolsets.skills import discover_skills

skills = discover_skills([
    {"path": "~/.pydantic-deep/skills", "recursive": True},
    {"path": "./project-skills", "recursive": False},
])

for skill in skills:
    print(f"{skill['name']}: {skill['description']}")
```

### Pre-loaded Skills

```python
skills = [
    {
        "name": "code-review",
        "description": "Review code for quality",
        "path": "/path/to/skill",
        "tags": ["code"],
        "version": "1.0.0",
        "author": "",
        "frontmatter_loaded": True,
    }
]

agent = create_deep_agent(skills=skills)
```

## Example: Code Review Skill

### SKILL.md

```markdown
---
name: code-review
description: Review Python code for quality, security, and best practices
version: 1.0.0
tags:
  - code
  - review
  - python
  - security
---

# Code Review Skill

When reviewing code, follow this checklist:

## Security

- [ ] No hardcoded secrets
- [ ] Input validation on external data
- [ ] No SQL injection vulnerabilities
- [ ] Proper error handling

## Code Quality

- [ ] Functions have single responsibility
- [ ] Descriptive variable names
- [ ] Type hints present
- [ ] Docstrings for public functions

## Output Format

```markdown
## Summary
[Brief assessment]

## Critical Issues
- [List security/major bugs]

## Improvements
- [Suggested improvements]

## Good Practices
- [Positive aspects]
```
```

### Usage

```python
agent = create_deep_agent(
    skill_directories=[{"path": "./skills"}],
)

result = await agent.run(
    "Load the code-review skill and review /src/auth.py",
    deps=deps,
)
```

## Best Practices

### 1. Clear Names

Use descriptive, hyphenated names:
- ✅ `code-review`, `test-generator`, `api-design`
- ❌ `cr`, `skill1`, `mySkill`

### 2. Focused Skills

Each skill should do one thing well:
- ✅ `code-review` - Reviews code
- ❌ `code-review-and-testing-and-docs` - Too broad

### 3. Actionable Instructions

Write instructions the agent can follow:

```markdown
# Good
When you find a security issue:
1. Note the file and line number
2. Describe the vulnerability
3. Suggest a fix with code example

# Bad
Be careful about security.
```

### 4. Include Examples

Show expected output format:

```markdown
## Example Review

**File:** auth.py:42
**Issue:** SQL Injection
**Severity:** Critical

```python
# Bad
query = f"SELECT * FROM users WHERE id = {user_id}"

# Good
query = "SELECT * FROM users WHERE id = ?"
cursor.execute(query, (user_id,))
```
```

### 5. Version Your Skills

Update version when making changes:

```yaml
version: 1.0.0  # Initial release
version: 1.1.0  # Added new checklist items
version: 2.0.0  # Breaking changes to format
```

## Next Steps

- [Skills Example](../examples/skills.md) - Complete working example
- [API Reference](../api/toolsets.md#skillstoolset) - SkillsToolset API
