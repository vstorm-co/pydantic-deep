"""Extended tests for skills toolset to reach 100% coverage."""

from pydantic_deep.backends.state import StateBackend
from pydantic_deep.deps import DeepAgentDeps
from pydantic_deep.toolsets.skills import (
    create_skills_toolset,
    discover_skills,
    get_skills_system_prompt,
    load_skill_instructions,
    parse_skill_md,
)
from pydantic_deep.types import Skill, SkillDirectory


class TestParseSkillMd:
    """Tests for parse_skill_md function."""

    def test_parse_with_frontmatter(self):
        """Test parsing skill with frontmatter."""
        content = """---
name: test-skill
description: A test skill
version: 1.0.0
author: Test Author
tags:
  - test
  - example
---

# Instructions

This is the skill instructions.
"""
        frontmatter, instructions = parse_skill_md(content)

        assert frontmatter["name"] == "test-skill"
        assert frontmatter["description"] == "A test skill"
        assert frontmatter["version"] == "1.0.0"
        assert frontmatter["author"] == "Test Author"
        assert frontmatter["tags"] == ["test", "example"]
        assert "# Instructions" in instructions

    def test_parse_without_frontmatter(self):
        """Test parsing skill without frontmatter."""
        content = """# Just Instructions

No frontmatter here.
"""
        frontmatter, instructions = parse_skill_md(content)

        assert frontmatter == {}
        assert "Just Instructions" in instructions

    def test_parse_with_quoted_values(self):
        """Test parsing with quoted values."""
        content = """---
name: "quoted-name"
description: 'single quoted'
---

Instructions.
"""
        frontmatter, instructions = parse_skill_md(content)

        assert frontmatter["name"] == "quoted-name"
        assert frontmatter["description"] == "single quoted"

    def test_parse_with_empty_lines_in_frontmatter(self):
        """Test parsing with empty lines in frontmatter."""
        content = """---
name: test

description: test desc
---

Instructions.
"""
        frontmatter, instructions = parse_skill_md(content)

        assert frontmatter["name"] == "test"
        assert frontmatter["description"] == "test desc"

    def test_parse_with_key_no_value(self):
        """Test parsing with key that has no value (for list)."""
        content = """---
name: test
tags:
  - tag1
  - tag2
---

Instructions.
"""
        frontmatter, instructions = parse_skill_md(content)

        assert frontmatter["name"] == "test"
        assert frontmatter["tags"] == ["tag1", "tag2"]

    def test_parse_line_without_colon(self):
        """Test parsing with a line that doesn't contain colon."""
        content = """---
name: test
some random text without colon
description: test desc
---

Instructions.
"""
        frontmatter, instructions = parse_skill_md(content)

        assert frontmatter["name"] == "test"
        assert frontmatter["description"] == "test desc"


class TestDiscoverSkills:
    """Tests for discover_skills function."""

    def test_discover_in_empty_directory(self, tmp_path):
        """Test discovering skills in empty directory."""
        directories: list[SkillDirectory] = [
            {"path": str(tmp_path), "recursive": True},
        ]
        skills = discover_skills(directories)
        assert skills == []

    def test_discover_in_nonexistent_directory(self):
        """Test discovering skills in nonexistent directory."""
        directories: list[SkillDirectory] = [
            {"path": "/nonexistent/path", "recursive": True},
        ]
        skills = discover_skills(directories)
        assert skills == []

    def test_discover_with_valid_skill(self, tmp_path):
        """Test discovering a valid skill."""
        skill_dir = tmp_path / "test-skill"
        skill_dir.mkdir()
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("""---
name: test-skill
description: A test skill
version: 1.0.0
---

# Instructions
""")

        directories: list[SkillDirectory] = [
            {"path": str(tmp_path), "recursive": True},
        ]
        skills = discover_skills(directories)

        assert len(skills) == 1
        assert skills[0]["name"] == "test-skill"

    def test_discover_with_resources(self, tmp_path):
        """Test discovering skill with resources."""
        skill_dir = tmp_path / "test-skill"
        skill_dir.mkdir()
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("""---
name: test-skill
description: A test skill
---

Instructions.
""")
        # Add resource file
        resource = skill_dir / "template.txt"
        resource.write_text("template content")

        directories: list[SkillDirectory] = [
            {"path": str(tmp_path), "recursive": True},
        ]
        skills = discover_skills(directories)

        assert len(skills) == 1
        assert "resources" in skills[0]
        assert "template.txt" in skills[0]["resources"]

    def test_discover_without_recursion(self, tmp_path):
        """Test discovering skills without recursion."""
        skill_dir = tmp_path / "test-skill"
        skill_dir.mkdir()
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("""---
name: test-skill
description: A test skill
---

Instructions.
""")

        directories: list[SkillDirectory] = [
            {"path": str(tmp_path), "recursive": False},
        ]
        skills = discover_skills(directories)
        assert len(skills) == 1

    def test_discover_skips_skill_without_name(self, tmp_path):
        """Test that skills without name are skipped."""
        skill_dir = tmp_path / "test-skill"
        skill_dir.mkdir()
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("""---
description: No name skill
---

Instructions.
""")

        directories: list[SkillDirectory] = [
            {"path": str(tmp_path), "recursive": True},
        ]
        skills = discover_skills(directories)
        assert len(skills) == 0


class TestLoadSkillInstructions:
    """Tests for load_skill_instructions function."""

    def test_load_valid_skill(self, tmp_path):
        """Test loading valid skill instructions."""
        skill_dir = tmp_path / "test-skill"
        skill_dir.mkdir()
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("""---
name: test-skill
---

# Detailed Instructions

Follow these steps...
""")

        instructions = load_skill_instructions(str(skill_dir))
        assert "Detailed Instructions" in instructions
        assert "Follow these steps" in instructions

    def test_load_nonexistent_skill(self):
        """Test loading nonexistent skill."""
        instructions = load_skill_instructions("/nonexistent/skill")
        assert "Error" in instructions
        assert "not found" in instructions


class TestGetSkillsSystemPrompt:
    """Tests for get_skills_system_prompt function."""

    def test_empty_skills(self):
        """Test system prompt with no skills."""
        deps = DeepAgentDeps(backend=StateBackend())
        prompt = get_skills_system_prompt(deps, [])
        assert prompt == ""

    def test_with_skills(self):
        """Test system prompt with skills."""
        deps = DeepAgentDeps(backend=StateBackend())
        skills: list[Skill] = [
            {
                "name": "test-skill",
                "description": "A test skill",
                "path": "/path/to/skill",
                "tags": ["test", "example"],
                "version": "1.0.0",
                "author": "",
                "frontmatter_loaded": True,
            },
        ]
        prompt = get_skills_system_prompt(deps, skills)

        assert "Available Skills" in prompt
        assert "test-skill" in prompt
        assert "test, example" in prompt

    def test_with_skills_no_tags(self):
        """Test system prompt with skills without tags."""
        deps = DeepAgentDeps(backend=StateBackend())
        skills: list[Skill] = [
            {
                "name": "test-skill",
                "description": "A test skill",
                "path": "/path/to/skill",
                "tags": [],
                "version": "1.0.0",
                "author": "",
                "frontmatter_loaded": True,
            },
        ]
        prompt = get_skills_system_prompt(deps, skills)

        assert "test-skill" in prompt
        # No tags section


class TestCreateSkillsToolset:
    """Tests for create_skills_toolset function."""

    def test_create_with_skills(self):
        """Test creating toolset with skills."""
        skills: list[Skill] = [
            {
                "name": "test-skill",
                "description": "A test skill",
                "path": "/path/to/skill",
                "tags": [],
                "version": "1.0.0",
                "author": "",
                "frontmatter_loaded": True,
            },
        ]
        toolset = create_skills_toolset(skills=skills)
        assert toolset is not None
        assert toolset.id == "skills"

    def test_create_with_directories(self, tmp_path):
        """Test creating toolset with directories."""
        skill_dir = tmp_path / "test-skill"
        skill_dir.mkdir()
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("""---
name: test-skill
description: A test skill
---

Instructions.
""")

        directories: list[SkillDirectory] = [
            {"path": str(tmp_path), "recursive": True},
        ]
        toolset = create_skills_toolset(directories=directories)
        assert toolset is not None

    def test_create_with_default_directory(self):
        """Test creating toolset with default directory (may not exist)."""
        toolset = create_skills_toolset()
        assert toolset is not None

    def test_create_with_custom_id(self):
        """Test creating toolset with custom ID."""
        toolset = create_skills_toolset(id="custom-skills")
        assert toolset.id == "custom-skills"
