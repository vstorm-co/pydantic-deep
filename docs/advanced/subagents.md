# Subagents

Subagents allow the main agent to delegate specialized tasks to focused, context-isolated agents.

## Why Subagents?

- **Focused context** - Each subagent has a clear, specific purpose
- **Isolation** - Fresh todo list, no nested delegation
- **Specialization** - Expert instructions for specific tasks
- **Reduced confusion** - Less context = better performance

## Defining Subagents

```python
from pydantic_deep import create_deep_agent, SubAgentConfig

subagents = [
    SubAgentConfig(
        name="code-reviewer",
        description="Reviews code for quality, security, and best practices",
        instructions="""
        You are an expert code reviewer. When reviewing code:

        1. Check for security vulnerabilities
        2. Look for performance issues
        3. Verify proper error handling
        4. Assess code readability

        Provide specific, actionable feedback.
        """,
    ),
    SubAgentConfig(
        name="test-writer",
        description="Generates pytest test cases for Python code",
        instructions="""
        You are a testing expert. Generate comprehensive tests:

        - Unit tests for individual functions
        - Edge cases and error conditions
        - Use pytest fixtures and parametrize
        - Include docstrings explaining each test
        """,
    ),
    SubAgentConfig(
        name="doc-writer",
        description="Writes documentation and docstrings",
        instructions="""
        You are a technical writer. Create clear documentation:

        - Use Google-style docstrings
        - Include examples in docstrings
        - Write clear README sections
        - Document edge cases and gotchas
        """,
    ),
]

agent = create_deep_agent(subagents=subagents)
```

## How the Task Tool Works

The main agent can call the `task` tool:

```python
task(
    description="Review the authentication module for security issues",
    subagent_type="code-reviewer",
)
```

This:

1. Creates a new agent with the subagent's instructions
2. Clones dependencies with:
   - Same backend (shared files)
   - Empty todo list (isolated planning)
   - No nested subagents
3. Runs the subagent with the description as prompt
4. Returns the subagent's output to the main agent

## Context Isolation

Subagents receive isolated context:

```python
def clone_for_subagent(self) -> DeepAgentDeps:
    """Create deps for a subagent."""
    return DeepAgentDeps(
        backend=self.backend,      # Shared - can read/write same files
        files=self.files,          # Shared reference
        todos=[],                  # Fresh - subagent plans independently
        subagents={},              # Empty - no nested delegation
    )
```

This prevents:

- Context bloat from accumulated todos
- Infinite recursion from nested delegation
- Confusion from mixed responsibilities

## General-Purpose Subagent

By default, a general-purpose subagent is included:

```python
agent = create_deep_agent(
    include_general_purpose_subagent=True,  # Default: True
)
```

This allows delegation for tasks without a specialized subagent:

```python
task(
    description="Research the best Python logging libraries",
    subagent_type="general-purpose",
)
```

Disable if you only want specific subagents:

```python
agent = create_deep_agent(
    subagents=subagents,
    include_general_purpose_subagent=False,
)
```

## Custom Model per Subagent

Use different models for different subagents:

```python
subagents = [
    SubAgentConfig(
        name="code-reviewer",
        description="Reviews code (uses powerful model)",
        instructions="...",
        model="anthropic:claude-sonnet-4-20250514",
    ),
    SubAgentConfig(
        name="simple-formatter",
        description="Formats code (uses fast model)",
        instructions="...",
        model="anthropic:claude-3-haiku-20240307",
    ),
]
```

## Custom Tools per Subagent

Subagents can have custom tools:

```python
async def run_tests(ctx, path: str) -> str:
    """Run pytest on the given path."""
    ...

subagents = [
    SubAgentConfig(
        name="test-writer",
        description="Writes and runs tests",
        instructions="...",
        tools=[run_tests],
    ),
]
```

## Example: Code Review Pipeline

```python
import asyncio
from pydantic_deep import create_deep_agent, DeepAgentDeps, StateBackend, SubAgentConfig

async def main():
    subagents = [
        SubAgentConfig(
            name="code-reviewer",
            description="Reviews code for issues",
            instructions="""
            Review code thoroughly. Check for:
            - Security issues
            - Performance problems
            - Error handling
            - Code style

            Format your review as markdown with sections.
            """,
        ),
        SubAgentConfig(
            name="test-writer",
            description="Generates pytest tests",
            instructions="""
            Write comprehensive pytest tests.
            Cover happy paths, edge cases, and error conditions.
            Use fixtures and parametrize decorators.
            """,
        ),
    ]

    agent = create_deep_agent(subagents=subagents)
    deps = DeepAgentDeps(backend=StateBackend())

    # Create some code to review
    deps.backend.write("/src/auth.py", '''
def authenticate(username, password):
    query = f"SELECT * FROM users WHERE username = '{username}'"
    user = db.execute(query)
    if user and user.password == password:
        return True
    return False
    ''')

    result = await agent.run(
        """
        1. Review /src/auth.py for security issues
        2. Generate tests for the authenticate function
        3. Report findings
        """,
        deps=deps,
    )

    print(result.output)

asyncio.run(main())
```

## Best Practices

### 1. Clear Descriptions

The description helps the main agent choose:

```python
# Good - clear when to use
SubAgentConfig(
    name="security-reviewer",
    description="Reviews code specifically for security vulnerabilities like SQL injection, XSS, and authentication issues",
    ...
)

# Bad - too vague
SubAgentConfig(
    name="reviewer",
    description="Reviews code",
    ...
)
```

### 2. Focused Instructions

Keep subagent instructions focused:

```python
# Good - specific focus
instructions="""
You are a security expert. Focus ONLY on:
- SQL injection
- XSS vulnerabilities
- Authentication issues
- Authorization flaws

Do NOT comment on code style or performance.
"""

# Bad - too broad
instructions="Review the code and check everything."
```

### 3. Output Format

Specify expected output format:

```python
instructions="""
...

Output your review in this format:
## Summary
[1-2 sentence overview]

## Critical Issues
- [Issue 1]
- [Issue 2]

## Recommendations
- [Recommendation 1]
"""
```

### 4. Limited Subagents

Use 3-5 focused subagents, not many generic ones:

```python
# Good - focused experts
subagents = [
    SubAgentConfig(name="security-reviewer", ...),
    SubAgentConfig(name="test-writer", ...),
    SubAgentConfig(name="doc-writer", ...),
]

# Bad - too many similar agents
subagents = [
    SubAgentConfig(name="python-reviewer", ...),
    SubAgentConfig(name="javascript-reviewer", ...),
    SubAgentConfig(name="typescript-reviewer", ...),
    SubAgentConfig(name="go-reviewer", ...),
    # ... 10 more language-specific reviewers
]
```

## Next Steps

- [Streaming](streaming.md) - Monitor subagent progress
- [Examples](../examples/index.md) - More examples
- [API Reference](../api/toolsets.md) - SubAgentToolset API
