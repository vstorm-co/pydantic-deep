# Getting Help

## Documentation

This documentation is your primary resource. Use the search bar (press `/` or `s`) to find specific topics.

## GitHub Issues

For bugs, feature requests, or questions:

[:fontawesome-brands-github: Open an Issue](https://github.com/vstorm-co/pydantic-deep/issues){ .md-button }

### Before Opening an Issue

1. **Search existing issues** - Your problem may already be reported
2. **Check the docs** - The answer might be here
3. **Prepare a minimal example** - Help us reproduce the issue

### Bug Report Template

```markdown
## Description
[Clear description of the bug]

## Steps to Reproduce
1. Create agent with...
2. Call agent.run()...
3. Observe error...

## Expected Behavior
[What you expected to happen]

## Actual Behavior
[What actually happened]

## Environment
- pydantic-deep version: X.X.X
- Python version: 3.XX
- OS: [e.g., macOS 14.0]
```

## Community Resources

### Pydantic AI

pydantic-deep is built on Pydantic AI. Their documentation is an excellent resource:

- [Pydantic AI Documentation](https://ai.pydantic.dev/)
- [Pydantic AI GitHub](https://github.com/pydantic/pydantic-ai)

### Pydantic

For data validation and type hints:

- [Pydantic Documentation](https://docs.pydantic.dev/)

## FAQ

### How is pydantic-deep different from LangChain?

pydantic-deep is built on Pydantic AI, which provides:

- Type-safe agents with Pydantic models
- Simpler, more pythonic API
- Better IDE support and autocomplete
- No complex chain abstractions

### Can I use models other than Anthropic?

Yes! Pydantic AI supports multiple providers:

```python
# OpenAI
agent = create_deep_agent(model="openai:gpt-4")

# Google
agent = create_deep_agent(model="google:gemini-1.5-pro")

# Anthropic (default)
agent = create_deep_agent(model="anthropic:claude-sonnet-4-20250514")
```

### How do I run without API calls (for testing)?

Use `TestModel` from Pydantic AI:

```python
from pydantic_ai.models.test import TestModel

agent = create_deep_agent(model=TestModel())
```

### Can I use pydantic-deep with async frameworks?

Yes! pydantic-deep is fully async-native:

```python
from fastapi import FastAPI
from pydantic_deep import create_deep_agent, DeepAgentDeps, StateBackend

app = FastAPI()
agent = create_deep_agent()

@app.post("/chat")
async def chat(prompt: str):
    deps = DeepAgentDeps(backend=StateBackend())
    result = await agent.run(prompt, deps=deps)
    return {"response": result.output}
```

### How do I persist files between runs?

Use `FilesystemBackend` instead of `StateBackend`:

```python
from pydantic_deep import FilesystemBackend

backend = FilesystemBackend("/path/to/workspace")
deps = DeepAgentDeps(backend=backend)
```
