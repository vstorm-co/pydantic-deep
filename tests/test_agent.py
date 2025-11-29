"""Tests for the agent factory."""

from pydantic_ai.models.test import TestModel

from pydantic_deep import (
    DeepAgentDeps,
    StateBackend,
    create_deep_agent,
    create_default_deps,
)
from pydantic_deep.types import SubAgentConfig

# Use TestModel to avoid requiring API keys
TEST_MODEL = TestModel()


class TestCreateDeepAgent:
    """Tests for create_deep_agent factory."""

    def test_create_default_agent(self):
        """Test creating an agent with default settings."""
        agent = create_deep_agent(model=TEST_MODEL)

        assert agent is not None

    def test_create_with_custom_model(self):
        """Test creating an agent with a custom model."""
        agent = create_deep_agent(model=TEST_MODEL)
        assert agent is not None

    def test_create_with_instructions(self):
        """Test creating an agent with custom instructions."""
        agent = create_deep_agent(model=TEST_MODEL, instructions="You are a test agent")
        assert agent is not None

    def test_create_without_todo(self):
        """Test creating an agent without todo toolset."""
        agent = create_deep_agent(model=TEST_MODEL, include_todo=False)
        assert agent is not None

    def test_create_without_filesystem(self):
        """Test creating an agent without filesystem toolset."""
        agent = create_deep_agent(model=TEST_MODEL, include_filesystem=False)
        assert agent is not None

    def test_create_without_subagents(self):
        """Test creating an agent without subagent toolset."""
        agent = create_deep_agent(model=TEST_MODEL, include_subagents=False)
        assert agent is not None

    def test_create_with_subagent_configs(self):
        """Test creating an agent with custom subagent configs."""
        subagents = [
            SubAgentConfig(
                name="researcher",
                description="A research agent",
                instructions="You research topics",
            ),
        ]
        agent = create_deep_agent(model=TEST_MODEL, subagents=subagents)
        assert agent is not None

    def test_create_with_interrupt_on(self):
        """Test creating an agent with interrupt_on config."""
        agent = create_deep_agent(
            model=TEST_MODEL,
            interrupt_on={
                "execute": True,
                "write_file": True,
            },
        )
        assert agent is not None


class TestCreateDefaultDeps:
    """Tests for create_default_deps."""

    def test_create_with_defaults(self):
        """Test creating deps with default settings."""
        deps = create_default_deps()

        assert deps is not None
        assert isinstance(deps.backend, StateBackend)
        assert deps.todos == []
        assert deps.subagents == {}

    def test_create_with_custom_backend(self):
        """Test creating deps with a custom backend."""
        backend = StateBackend()
        deps = create_default_deps(backend=backend)

        assert deps.backend is backend


class TestDeepAgentDeps:
    """Tests for DeepAgentDeps."""

    def test_get_todo_prompt_empty(self):
        """Test todo prompt with no todos."""
        deps = DeepAgentDeps(backend=StateBackend())
        prompt = deps.get_todo_prompt()

        assert prompt == ""

    def test_get_todo_prompt_with_todos(self):
        """Test todo prompt with todos."""
        from pydantic_deep.types import Todo

        deps = DeepAgentDeps(
            backend=StateBackend(),
            todos=[
                Todo(content="Test task", status="pending", active_form="Testing"),
            ],
        )
        prompt = deps.get_todo_prompt()

        assert "Test task" in prompt
        assert "[ ]" in prompt

    def test_clone_for_subagent(self):
        """Test cloning deps for a subagent."""
        from pydantic_deep.types import Todo

        original = DeepAgentDeps(
            backend=StateBackend(),
            todos=[Todo(content="Task", status="pending", active_form="Working")],
        )
        original.files["/test.txt"] = {
            "content": ["test"],
            "created_at": "2024-01-01",
            "modified_at": "2024-01-01",
        }

        cloned = original.clone_for_subagent()

        # Should share backend and files
        assert cloned.backend is original.backend
        assert cloned.files is original.files

        # Should have empty todos and subagents
        assert cloned.todos == []
        assert cloned.subagents == {}
