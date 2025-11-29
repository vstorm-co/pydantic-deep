# pydantic-deep

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen.svg)](https://github.com/vstorm-co/pydantic-deep)

Deep agent framework built on [pydantic-ai](https://github.com/pydantic/pydantic-ai) with planning, filesystem, and subagent capabilities.

## Features

- **Multiple Backends**: StateBackend (in-memory), FilesystemBackend, DockerSandbox, CompositeBackend
- **Rich Toolsets**: TodoToolset, FilesystemToolset, SubAgentToolset, SkillsToolset
- **Skills System**: Extensible skill definitions with markdown prompts
- **Human-in-the-Loop**: Built-in support for human confirmation workflows
- **Streaming**: Full streaming support for agent responses

## Installation

```bash
pip install pydantic-deep
```

Or with uv:

```bash
uv add pydantic-deep
```

### Optional dependencies

```bash
# Docker sandbox support
pip install pydantic-deep[sandbox]
```

## Quick Start

```python
import asyncio
from pydantic_deep import create_deep_agent, create_default_deps
from pydantic_deep.backends import StateBackend

async def main():
    # Create a deep agent with state backend
    backend = StateBackend()
    deps = create_default_deps(backend)
    agent = create_deep_agent()

    # Run the agent
    result = await agent.run("Help me organize my tasks", deps=deps)
    print(result.output)

asyncio.run(main())
```

## Documentation

Full documentation is available at the [docs site](https://github.com/vstorm-co/pydantic-deep).

## Development

```bash
# Clone the repository
git clone https://github.com/vstorm-co/pydantic-deep.git
cd pydantic-deep

# Install dependencies
make install

# Run tests
make test

# Run all checks
make all
```

## License

MIT License - see [LICENSE](LICENSE) for details.
