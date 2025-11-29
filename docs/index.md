# pydantic-deep

<p style="font-size: 1.3em; color: #888; margin-top: -0.5em;">
Deep Agent Framework, the Pydantic AI way
</p>

[![CI](https://img.shields.io/badge/CI-passing-brightgreen)](https://github.com/vstorm-co/pydantic-deep)
[![coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)](https://github.com/vstorm-co/pydantic-deep)
[![pypi](https://img.shields.io/badge/pypi-v0.1.0-blue)](https://pypi.org/project/pydantic-deep/)
[![python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue)](https://www.python.org/)
[![license](https://img.shields.io/badge/license-MIT-green)](https://opensource.org/licenses/MIT)

---

**pydantic-deep** is a Python deep agent framework built on top of [Pydantic AI](https://ai.pydantic.dev/) designed to help you quickly build production-grade autonomous agents with planning, filesystem operations, subagent delegation, and skills.

## Why use pydantic-deep?

Building autonomous agents that can plan, execute multi-step tasks, and work with files is complex. pydantic-deep provides:

<div class="feature-grid">
<div class="feature-card">
<h3>📋 Planning</h3>
<p>Built-in todo list for task decomposition. Agents break down complex tasks and track progress automatically.</p>
</div>

<div class="feature-card">
<h3>📁 Filesystem</h3>
<p>Virtual and real filesystem operations. Read, write, edit files with grep and glob support.</p>
</div>

<div class="feature-card">
<h3>🤖 Subagents</h3>
<p>Delegate specialized tasks to isolated subagents. Code review, testing, documentation - each with focused context.</p>
</div>

<div class="feature-card">
<h3>🎯 Skills</h3>
<p>Modular capability packages loaded on-demand. Extend agent abilities without bloating context.</p>
</div>
</div>

## Hello World Example

```python
import asyncio
from pydantic_deep import create_deep_agent, DeepAgentDeps, StateBackend

async def main():
    # Create a deep agent with all capabilities
    agent = create_deep_agent(
        model="anthropic:claude-sonnet-4-20250514",
        instructions="You are a helpful coding assistant.",
    )

    # Create dependencies with in-memory storage
    deps = DeepAgentDeps(backend=StateBackend())

    # Run the agent
    result = await agent.run(
        "Create a Python function that calculates fibonacci numbers",
        deps=deps,
    )

    print(result.output)

asyncio.run(main())
```

## Tools & Dependency Injection Example

```python
from pydantic_ai import RunContext
from pydantic_deep import create_deep_agent, DeepAgentDeps

# Define a custom tool
async def get_weather(
    ctx: RunContext[DeepAgentDeps],
    city: str,
) -> str:
    """Get weather for a city."""
    # Access dependencies via ctx.deps
    return f"Weather in {city}: Sunny, 22°C"

# Create agent with custom tools
agent = create_deep_agent(
    tools=[get_weather],
    instructions="You can check weather and work with files.",
)
```

## Key Features

| Feature | Description |
|---------|-------------|
| **Planning** | Todo toolset for task decomposition and tracking |
| **Filesystem** | Read, write, edit, glob, grep operations |
| **Subagents** | Context-isolated task delegation |
| **Skills** | Modular capability packages with progressive disclosure |
| **Backends** | StateBackend, FilesystemBackend, DockerSandbox, CompositeBackend |
| **HITL** | Human-in-the-loop approval workflows |

## llms.txt

pydantic-deep supports the [llms.txt](https://llmstxt.org/) standard. Access documentation at `/llms.txt` for LLM-optimized content.

## Next Steps

<div class="feature-grid">
<div class="feature-card">
<h3>📖 Installation</h3>
<p>Get started with pydantic-deep in minutes.</p>
<a href="installation/">Installation Guide →</a>
</div>

<div class="feature-card">
<h3>🎓 Core Concepts</h3>
<p>Learn about agents, backends, and toolsets.</p>
<a href="concepts/">Core Concepts →</a>
</div>

<div class="feature-card">
<h3>📝 Examples</h3>
<p>See pydantic-deep in action with real examples.</p>
<a href="examples/">Examples →</a>
</div>

<div class="feature-card">
<h3>📚 API Reference</h3>
<p>Complete API documentation.</p>
<a href="api/">API Reference →</a>
</div>
</div>
