# Streaming

pydantic-deep supports streaming execution for real-time progress monitoring.

## Basic Streaming

Use `agent.iter()` for streaming:

```python
import asyncio
from pydantic_deep import create_deep_agent, DeepAgentDeps, StateBackend

async def main():
    agent = create_deep_agent()
    deps = DeepAgentDeps(backend=StateBackend())

    async with agent.iter("Create a Python module", deps=deps) as run:
        async for node in run:
            print(f"Node: {type(node).__name__}")

        result = run.result

    print(f"\nFinal output: {result.output}")

asyncio.run(main())
```

## Node Types

During streaming, you'll receive different node types:

```python
from pydantic_ai._agent_graph import (
    UserPromptNode,
    ModelRequestNode,
    CallToolsNode,
    End,
)

async with agent.iter(prompt, deps=deps) as run:
    async for node in run:
        if isinstance(node, UserPromptNode):
            print("📝 Processing user prompt...")

        elif isinstance(node, ModelRequestNode):
            print("🤖 Calling model...")

        elif isinstance(node, CallToolsNode):
            # Extract tool names from the response
            tools = []
            for part in node.model_response.parts:
                if hasattr(part, 'tool_name'):
                    tools.append(part.tool_name)

            if tools:
                print(f"🔧 Executing: {', '.join(tools)}")

        elif isinstance(node, End):
            print("✅ Completed!")
```

## Progress Display

Show a progress indicator:

```python
import sys

async def run_with_progress(agent, prompt, deps):
    step = 0

    async with agent.iter(prompt, deps=deps) as run:
        async for node in run:
            step += 1
            node_type = type(node).__name__

            # Clear line and show progress
            sys.stdout.write(f"\r[Step {step}] {node_type}...")
            sys.stdout.flush()

        print("\n")
        return run.result
```

## Tool Call Details

Get detailed information about tool calls:

```python
async with agent.iter(prompt, deps=deps) as run:
    async for node in run:
        if isinstance(node, CallToolsNode):
            for part in node.model_response.parts:
                if hasattr(part, 'tool_name'):
                    print(f"Tool: {part.tool_name}")
                    if hasattr(part, 'args'):
                        print(f"  Args: {part.args}")
```

## Live Output

For long-running operations, show intermediate results:

```python
async def run_with_live_output(agent, prompt, deps):
    async with agent.iter(prompt, deps=deps) as run:
        async for node in run:
            if isinstance(node, CallToolsNode):
                for part in node.model_response.parts:
                    if hasattr(part, 'tool_name'):
                        tool = part.tool_name

                        # Show tool-specific output
                        if tool == "write_todos":
                            print("\n📋 Updated todo list")
                        elif tool == "write_file":
                            path = part.args.get("path", "")
                            print(f"\n📝 Writing: {path}")
                        elif tool == "read_file":
                            path = part.args.get("path", "")
                            print(f"\n📖 Reading: {path}")

        return run.result
```

## Web Streaming

For web applications using Server-Sent Events:

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import json

app = FastAPI()

@app.get("/agent/stream")
async def stream_agent(prompt: str):
    async def event_generator():
        async with agent.iter(prompt, deps=deps) as run:
            async for node in run:
                node_type = type(node).__name__

                data = {"type": node_type}

                if isinstance(node, CallToolsNode):
                    tools = []
                    for part in node.model_response.parts:
                        if hasattr(part, 'tool_name'):
                            tools.append(part.tool_name)
                    data["tools"] = tools

                yield f"data: {json.dumps(data)}\n\n"

            # Send final result
            yield f"data: {json.dumps({'type': 'complete', 'output': run.result.output})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )
```

## Cancellation

Cancel a running agent:

```python
import asyncio

async def run_with_timeout(agent, prompt, deps, timeout=60):
    try:
        async with asyncio.timeout(timeout):
            async with agent.iter(prompt, deps=deps) as run:
                async for node in run:
                    pass
                return run.result
    except asyncio.TimeoutError:
        print("Agent execution timed out")
        return None
```

## Usage Statistics

Track token usage during streaming:

```python
async with agent.iter(prompt, deps=deps) as run:
    async for node in run:
        pass

    result = run.result
    usage = result.usage()

    print(f"Input tokens: {usage.input_tokens}")
    print(f"Output tokens: {usage.output_tokens}")
    print(f"Total requests: {usage.requests}")
```

## Example: Progress Bar

Using `rich` for beautiful progress display:

```python
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

async def run_with_rich_progress(agent, prompt, deps):
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Starting...", total=None)

        async with agent.iter(prompt, deps=deps) as run:
            async for node in run:
                node_type = type(node).__name__

                if isinstance(node, ModelRequestNode):
                    progress.update(task, description="🤖 Thinking...")
                elif isinstance(node, CallToolsNode):
                    tools = []
                    for part in node.model_response.parts:
                        if hasattr(part, 'tool_name'):
                            tools.append(part.tool_name)
                    if tools:
                        progress.update(
                            task,
                            description=f"🔧 {', '.join(tools)}"
                        )

            progress.update(task, description="✅ Complete!")
            return run.result
```

## Next Steps

- [Human-in-the-Loop](human-in-the-loop.md) - Approval workflows
- [Examples](../examples/index.md) - More examples
