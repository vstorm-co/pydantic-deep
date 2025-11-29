"""Example using streaming for real-time output.

This example demonstrates:
- Using agent.iter() for streaming
- Processing nodes as they execute
- Tracking progress in real-time
"""

import asyncio

from pydantic_ai._agent_graph import CallToolsNode, End, ModelRequestNode, UserPromptNode

from pydantic_deep import DeepAgentDeps, StateBackend, create_deep_agent


async def main():
    # Create the agent
    agent = create_deep_agent(
        model="anthropic:claude-sonnet-4-20250514",
        instructions="You are a helpful assistant.",
    )

    deps = DeepAgentDeps(backend=StateBackend())

    print("Starting agent with streaming...\n")

    # Use iter() for streaming execution
    async with agent.iter(
        "Create a simple Python module with 3 utility functions and save it to /utils.py",
        deps=deps,
    ) as run:
        step = 0
        async for node in run:
            step += 1
            node_type = type(node).__name__

            if isinstance(node, UserPromptNode):
                print(f"[Step {step}] Processing user prompt...")

            elif isinstance(node, ModelRequestNode):
                print(f"[Step {step}] Calling model...")

            elif isinstance(node, CallToolsNode):
                # Extract tool calls from the model response
                tool_calls = []
                for part in node.model_response.parts:
                    if hasattr(part, "tool_name"):
                        tool_calls.append(part.tool_name)

                if tool_calls:
                    print(f"[Step {step}] Executing tools: {', '.join(tool_calls)}")
                else:
                    print(f"[Step {step}] Processing response...")

            elif isinstance(node, End):
                print(f"[Step {step}] Completed!")

            else:
                print(f"[Step {step}] {node_type}")

        # Get the final result
        result = run.result

    print(f"\n{'=' * 50}")
    print("Final output:")
    print(result.output)

    # Show usage statistics
    print("\nUsage:")
    print(f"  Input tokens: {result.usage().input_tokens}")
    print(f"  Output tokens: {result.usage().output_tokens}")
    print(f"  Total requests: {result.usage().requests}")

    # Show created files
    print("\nFiles created:")
    for path in sorted(deps.files.keys()):
        print(f"  {path}")


if __name__ == "__main__":
    asyncio.run(main())
