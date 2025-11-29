"""Extended tests for agent factory to reach 100% coverage."""

from pydantic_ai.models.test import TestModel

from pydantic_deep import (
    DeepAgentDeps,
    StateBackend,
    create_deep_agent,
)
from pydantic_deep.types import Skill, SkillDirectory

TEST_MODEL = TestModel()


class TestCreateDeepAgentExtended:
    """Extended tests for create_deep_agent factory."""

    def test_create_without_skills(self):
        """Test creating an agent without skills toolset."""
        agent = create_deep_agent(model=TEST_MODEL, include_skills=False)
        assert agent is not None

    def test_create_without_general_purpose_subagent(self):
        """Test creating without general-purpose subagent."""
        agent = create_deep_agent(
            model=TEST_MODEL,
            include_general_purpose_subagent=False,
        )
        assert agent is not None

    def test_create_with_custom_toolsets(self):
        """Test creating with additional custom toolsets."""
        from pydantic_ai.toolsets import FunctionToolset

        custom_toolset = FunctionToolset(id="custom")

        @custom_toolset.tool
        async def custom_tool() -> str:
            """Custom tool."""
            return "custom"

        agent = create_deep_agent(
            model=TEST_MODEL,
            toolsets=[custom_toolset],
        )
        assert agent is not None

    def test_create_with_custom_tools(self):
        """Test creating with additional custom tools."""

        async def custom_function() -> str:
            """Custom function."""
            return "custom"

        agent = create_deep_agent(
            model=TEST_MODEL,
            tools=[custom_function],
        )
        assert agent is not None

    def test_create_with_skills_list(self):
        """Test creating with pre-loaded skills."""
        skills: list[Skill] = [
            {
                "name": "test-skill",
                "description": "A test skill",
                "path": "/tmp/test-skill",
                "tags": ["test"],
                "version": "1.0.0",
                "author": "Test",
                "frontmatter_loaded": True,
            },
        ]
        agent = create_deep_agent(
            model=TEST_MODEL,
            skills=skills,
        )
        assert agent is not None

    def test_create_with_skill_directories(self, tmp_path):
        """Test creating with skill directories."""
        # Create a test skill
        skill_dir = tmp_path / "test-skill"
        skill_dir.mkdir()
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("""---
name: test-skill
description: A test skill
version: 1.0.0
---

# Test Skill Instructions

This is a test skill.
""")

        directories: list[SkillDirectory] = [
            {"path": str(tmp_path), "recursive": True},
        ]
        agent = create_deep_agent(
            model=TEST_MODEL,
            skill_directories=directories,
        )
        assert agent is not None

    def test_create_with_interrupt_on_edit_file(self):
        """Test creating with edit_file in interrupt_on."""
        agent = create_deep_agent(
            model=TEST_MODEL,
            interrupt_on={"edit_file": True},
        )
        assert agent is not None


class TestDeepAgentDepsExtended:
    """Extended tests for DeepAgentDeps."""

    def test_post_init_syncs_files(self):
        """Test that __post_init__ syncs files to StateBackend."""
        backend = StateBackend()
        files = {
            "/test.txt": {
                "content": ["test content"],
                "created_at": "2024-01-01",
                "modified_at": "2024-01-01",
            }
        }
        _ = DeepAgentDeps(backend=backend, files=files)

        # Files should be synced to backend
        assert "/test.txt" in backend.files

    def test_get_files_summary_with_files(self):
        """Test get_files_summary with files."""
        deps = DeepAgentDeps(backend=StateBackend())
        deps.files["/test.txt"] = {
            "content": ["line1", "line2"],
            "created_at": "2024-01-01",
            "modified_at": "2024-01-01",
        }

        summary = deps.get_files_summary()
        assert "Files in Memory" in summary
        assert "/test.txt" in summary
        assert "2 lines" in summary

    def test_get_subagents_summary_empty(self):
        """Test get_subagents_summary with no subagents."""
        deps = DeepAgentDeps(backend=StateBackend())
        summary = deps.get_subagents_summary()
        assert summary == ""

    def test_get_subagents_summary_with_subagents(self):
        """Test get_subagents_summary with subagents."""
        deps = DeepAgentDeps(backend=StateBackend())
        deps.subagents = {"researcher": object(), "writer": object()}

        summary = deps.get_subagents_summary()
        assert "Available Subagents" in summary
        assert "researcher" in summary
        assert "writer" in summary
