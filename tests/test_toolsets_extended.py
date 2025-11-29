"""Extended tests for toolset implementations to reach 100% coverage."""

from pydantic_deep.backends.state import StateBackend
from pydantic_deep.deps import DeepAgentDeps
from pydantic_deep.toolsets.filesystem import (
    get_filesystem_system_prompt,
)
from pydantic_deep.toolsets.subagents import (
    create_subagent_toolset,
    get_subagent_system_prompt,
)
from pydantic_deep.toolsets.todo import TodoItem
from pydantic_deep.types import SubAgentConfig


class TestTodoToolsetExtended:
    """Extended tests for TodoToolset."""

    def test_todo_item_model(self):
        """Test TodoItem pydantic model."""
        item = TodoItem(
            content="Test task",
            status="pending",
            active_form="Testing",
        )
        assert item.content == "Test task"
        assert item.status == "pending"
        assert item.active_form == "Testing"


class TestFilesystemToolsetExtended:
    """Extended tests for FilesystemToolset."""

    def test_get_filesystem_system_prompt_basic(self):
        """Test basic filesystem system prompt."""
        deps = DeepAgentDeps(backend=StateBackend())
        prompt = get_filesystem_system_prompt(deps)
        assert "Filesystem Tools" in prompt

    def test_get_filesystem_system_prompt_with_sandbox(self):
        """Test filesystem system prompt with sandbox backend."""
        from pydantic_deep.backends.protocol import SandboxProtocol

        # Create a mock sandbox backend
        class MockSandbox(SandboxProtocol):
            def execute(self, command, timeout=None):
                pass

            def ls_info(self, path):
                return []

            def read(self, path, offset=0, limit=2000):
                return ""

            def write(self, path, content):
                pass

            def edit(self, path, old, new, replace_all=False):
                pass

            def glob_info(self, pattern, path="/"):
                return []

            def grep_raw(self, pattern, path=None, glob=None):
                return []

        deps = DeepAgentDeps(backend=MockSandbox())
        prompt = get_filesystem_system_prompt(deps)
        assert "Command Execution" in prompt

    def test_get_filesystem_system_prompt_with_files(self):
        """Test filesystem system prompt with files summary."""
        deps = DeepAgentDeps(backend=StateBackend())
        deps.files["/test.txt"] = {
            "content": ["test"],
            "created_at": "2024-01-01",
            "modified_at": "2024-01-01",
        }
        prompt = get_filesystem_system_prompt(deps)
        assert "Files in Memory" in prompt


class TestSubagentToolsetExtended:
    """Extended tests for SubAgentToolset."""

    def test_create_with_custom_subagents(self):
        """Test creating with custom subagent configs."""
        subagents = [
            SubAgentConfig(
                name="researcher",
                description="Research topics",
                instructions="You research topics thoroughly.",
            ),
        ]
        toolset = create_subagent_toolset(subagents=subagents)
        assert toolset is not None

    def test_create_without_general_purpose(self):
        """Test creating without general-purpose subagent."""
        toolset = create_subagent_toolset(include_general_purpose=False)
        assert toolset is not None

    def test_create_with_no_subagents(self):
        """Test creating with no subagents at all."""
        toolset = create_subagent_toolset(
            subagents=[],
            include_general_purpose=False,
        )
        assert toolset is not None

    def test_get_subagent_system_prompt_basic(self):
        """Test basic subagent system prompt."""
        deps = DeepAgentDeps(backend=StateBackend())
        prompt = get_subagent_system_prompt(deps)
        assert "Task Delegation" in prompt

    def test_get_subagent_system_prompt_with_configs(self):
        """Test subagent system prompt with configs."""
        deps = DeepAgentDeps(backend=StateBackend())
        configs = [
            SubAgentConfig(
                name="researcher",
                description="Research topics",
                instructions="Research thoroughly.",
            ),
        ]
        prompt = get_subagent_system_prompt(deps, configs)
        assert "Available Subagents" in prompt
        assert "researcher" in prompt

    def test_get_subagent_system_prompt_with_cached_subagents(self):
        """Test subagent system prompt with cached subagents."""
        deps = DeepAgentDeps(backend=StateBackend())
        deps.subagents = {"researcher": object()}

        prompt = get_subagent_system_prompt(deps)
        assert "Cached Subagents" in prompt
        assert "researcher" in prompt
