"""Tests for toolset implementations."""

from pydantic_deep.backends.state import StateBackend
from pydantic_deep.deps import DeepAgentDeps
from pydantic_deep.toolsets.filesystem import create_filesystem_toolset
from pydantic_deep.toolsets.todo import create_todo_toolset, get_todo_system_prompt
from pydantic_deep.types import Todo


class TestTodoToolset:
    """Tests for TodoToolset."""

    def test_create_toolset(self):
        """Test creating a todo toolset."""
        toolset = create_todo_toolset(id="test-todo")
        assert toolset.id == "test-todo"

    def test_get_todo_system_prompt_empty(self):
        """Test system prompt with no todos."""
        deps = DeepAgentDeps(backend=StateBackend())
        prompt = get_todo_system_prompt(deps)

        assert "Task Management" in prompt
        assert "write_todos" in prompt

    def test_get_todo_system_prompt_with_todos(self):
        """Test system prompt with todos."""
        deps = DeepAgentDeps(
            backend=StateBackend(),
            todos=[
                Todo(content="Task 1", status="completed", active_form="Completing task 1"),
                Todo(content="Task 2", status="in_progress", active_form="Working on task 2"),
                Todo(content="Task 3", status="pending", active_form="Starting task 3"),
            ],
        )
        prompt = get_todo_system_prompt(deps)

        assert "Current Todos" in prompt
        assert "[x]" in prompt  # completed
        assert "[*]" in prompt  # in_progress
        assert "[ ]" in prompt  # pending


class TestFilesystemToolset:
    """Tests for FilesystemToolset."""

    def test_create_toolset(self):
        """Test creating a filesystem toolset."""
        toolset = create_filesystem_toolset(id="test-fs")
        assert toolset.id == "test-fs"

    def test_create_without_execute(self):
        """Test creating toolset without execute."""
        toolset = create_filesystem_toolset(include_execute=False)
        # The toolset should be created successfully
        assert toolset is not None

    def test_create_with_approval(self):
        """Test creating toolset with approval requirements."""
        toolset = create_filesystem_toolset(
            require_write_approval=True,
            require_execute_approval=True,
        )
        assert toolset is not None
