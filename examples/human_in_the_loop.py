"""Example demonstrating Human-in-the-Loop approval.

This example shows:
- Configuring tools that require approval
- Handling DeferredToolRequests
- Approving or denying tool calls
"""

import asyncio

from pydantic_ai.tools import DeferredToolRequests, DeferredToolResults, ToolApproved, ToolDenied

from pydantic_deep import DeepAgentDeps, StateBackend, create_deep_agent


async def get_user_approval(tool_name: str, args: dict) -> bool:
    """Simulate getting user approval (in real app, this would be UI)."""
    print(f"\n{'=' * 50}")
    print("APPROVAL REQUIRED")
    print(f"Tool: {tool_name}")
    print(f"Arguments: {args}")
    print(f"{'=' * 50}")

    # For demo, auto-approve write_file but deny execute
    if tool_name == "write_file":
        print("Auto-approving write_file...")
        return True
    elif tool_name == "execute":
        print("Auto-denying execute for safety...")
        return False

    return True


async def main():
    # Create agent with approval required for sensitive operations
    agent = create_deep_agent(
        model="anthropic:claude-sonnet-4-20250514",
        instructions="You are a system administrator assistant.",
        interrupt_on={
            "write_file": True,  # Require approval for file writes
            "edit_file": True,  # Require approval for file edits
            "execute": True,  # Require approval for command execution
        },
    )

    deps = DeepAgentDeps(backend=StateBackend())

    # Ask the agent to do something that requires approval
    print("Running agent with task that requires approval...")

    result = await agent.run(
        "Create a backup script at /backup.sh that archives the /data directory",
        deps=deps,
    )

    # Check if we got deferred tool requests
    if isinstance(result.output, DeferredToolRequests):
        print(f"\nReceived {len(result.output.approvals)} approval request(s)")

        # Process each approval request
        approvals: dict[str, ToolApproved | ToolDenied] = {}

        for call in result.output.approvals:
            approved = await get_user_approval(call.tool_name, call.args)

            if approved:
                approvals[call.tool_call_id] = ToolApproved()
            else:
                approvals[call.tool_call_id] = ToolDenied(
                    message=f"User denied {call.tool_name} for safety reasons"
                )

        # Continue the agent with approvals
        print("\nContinuing agent with approval decisions...")

        final_result = await agent.run(
            None,  # No new prompt
            deps=deps,
            message_history=result.all_messages(),
            deferred_tool_results=DeferredToolResults(approvals=approvals),
        )

        print("\nFinal output:")
        print(final_result.output)

    else:
        # No approvals needed (shouldn't happen with our config)
        print("Output (no approvals needed):")
        print(result.output)

    # Show what files were created
    print("\nFiles in storage:")
    for path, data in deps.files.items():
        print(f"  {path}: {len(data['content'])} lines")


if __name__ == "__main__":
    asyncio.run(main())
