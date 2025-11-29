# Human-in-the-Loop

pydantic-deep supports requiring human approval for sensitive operations through the `interrupt_on` configuration.

## Configuration

```python
agent = create_deep_agent(
    interrupt_on={
        "execute": True,       # Shell command execution
        "write_file": True,    # Creating/overwriting files
        "edit_file": True,     # Modifying existing files
    }
)
```

## How It Works

When a tool requires approval:

1. Agent calls the tool
2. Tool execution is deferred
3. `DeferredToolRequests` returned instead of result
4. You review and approve/deny
5. Resume execution with decisions

## Example Flow

```python
import asyncio
from pydantic_deep import create_deep_agent, DeepAgentDeps, StateBackend

async def main():
    agent = create_deep_agent(
        interrupt_on={
            "execute": True,
            "write_file": True,
        }
    )

    deps = DeepAgentDeps(backend=StateBackend())

    # Initial run
    result = await agent.run(
        "Create a script that prints hello world and run it",
        deps=deps,
    )

    # Check if approval needed
    if hasattr(result, 'deferred_tool_calls'):
        print("Approval needed for:")
        for call in result.deferred_tool_calls:
            print(f"  - {call.tool_name}: {call.args}")

        # In a real app, you'd prompt the user
        # For this example, approve all
        approved = result.approve_all()

        # Resume with approvals
        result = await agent.run(
            approved,
            deps=deps,
            message_history=result.all_messages(),
        )

    print(result.output)

asyncio.run(main())
```

## Selective Approval

You can approve or deny individual tool calls:

```python
if hasattr(result, 'deferred_tool_calls'):
    decisions = []

    for call in result.deferred_tool_calls:
        if call.tool_name == "execute":
            # Review command before approving
            if "rm" in call.args.get("command", ""):
                decisions.append(call.deny("Destructive command not allowed"))
            else:
                decisions.append(call.approve())
        elif call.tool_name == "write_file":
            # Always approve writes
            decisions.append(call.approve())

    # Resume with decisions
    result = await agent.run(
        decisions,
        deps=deps,
        message_history=result.all_messages(),
    )
```

## Interactive Approval

For CLI applications:

```python
async def interactive_run(agent, prompt, deps):
    result = await agent.run(prompt, deps=deps)

    while hasattr(result, 'deferred_tool_calls'):
        for call in result.deferred_tool_calls:
            print(f"\nTool: {call.tool_name}")
            print(f"Args: {call.args}")

            response = input("Approve? [y/n]: ").lower()
            if response == 'y':
                call.approve()
            else:
                reason = input("Reason for denial: ")
                call.deny(reason)

        result = await agent.run(
            result.get_decisions(),
            deps=deps,
            message_history=result.all_messages(),
        )

    return result
```

## Web Application Integration

For web apps with async approval:

```python
from fastapi import FastAPI, BackgroundTasks

app = FastAPI()
pending_approvals = {}

@app.post("/agent/run")
async def run_agent(prompt: str):
    result = await agent.run(prompt, deps=deps)

    if hasattr(result, 'deferred_tool_calls'):
        # Store for later approval
        request_id = generate_id()
        pending_approvals[request_id] = {
            "result": result,
            "calls": result.deferred_tool_calls,
        }
        return {
            "status": "pending_approval",
            "request_id": request_id,
            "tools": [
                {"name": c.tool_name, "args": c.args}
                for c in result.deferred_tool_calls
            ]
        }

    return {"status": "complete", "output": result.output}

@app.post("/agent/approve/{request_id}")
async def approve(request_id: str, decisions: list[dict]):
    pending = pending_approvals.pop(request_id)

    for i, decision in enumerate(decisions):
        call = pending["calls"][i]
        if decision["approved"]:
            call.approve()
        else:
            call.deny(decision.get("reason", "Denied"))

    result = await agent.run(
        pending["result"].get_decisions(),
        deps=deps,
        message_history=pending["result"].all_messages(),
    )

    return {"status": "complete", "output": result.output}
```

## Default Behavior

By default:

| Tool | Requires Approval |
|------|-------------------|
| `execute` | Yes (if enabled) |
| `write_file` | No |
| `edit_file` | No |
| `task` | No |
| Other tools | No |

!!! tip
    Even without approval, `execute` only works with sandbox backends.

## Best Practices

### 1. Always Review Execute

```python
interrupt_on={"execute": True}
```

Shell commands can be dangerous. Always review.

### 2. Review Writes in Production

```python
interrupt_on={
    "write_file": True,
    "edit_file": True,
}
```

In production environments, review file modifications.

### 3. Log All Approvals

```python
import logging

logger = logging.getLogger(__name__)

for call in result.deferred_tool_calls:
    logger.info(f"Approving: {call.tool_name} with {call.args}")
    call.approve()
```

### 4. Set Timeouts

```python
import asyncio

try:
    approval = await asyncio.wait_for(
        get_user_approval(call),
        timeout=300,  # 5 minute timeout
    )
except asyncio.TimeoutError:
    call.deny("Approval timeout")
```

## Next Steps

- [Subagents](subagents.md) - Task delegation
- [Streaming](streaming.md) - Real-time output
- [Examples](../examples/index.md) - More examples
