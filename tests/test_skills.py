"""Tests for skills toolset."""

import tempfile
from pathlib import Path

from pydantic_deep.toolsets.skills import (
    create_skills_toolset,
    discover_skills,
    load_skill_instructions,
    parse_skill_md,
)


class TestParseSkillMd:
    """Tests for SKILL.md parsing."""

    def test_parse_basic_frontmatter(self):
        """Test parsing basic YAML frontmatter."""
        content = """---
name: test-skill
description: A test skill
version: 1.0.0
---

# Instructions

This is a test skill.
"""
        frontmatter, instructions = parse_skill_md(content)

        assert frontmatter["name"] == "test-skill"
        assert frontmatter["description"] == "A test skill"
        assert frontmatter["version"] == "1.0.0"
        assert "# Instructions" in instructions
        assert "This is a test skill." in instructions

    def test_parse_frontmatter_with_tags(self):
        """Test parsing frontmatter with list values."""
        content = """---
name: code-review
description: Reviews code for issues
tags:
  - code
  - review
  - quality
author: Test Author
---

Review code carefully.
"""
        frontmatter, instructions = parse_skill_md(content)

        assert frontmatter["name"] == "code-review"
        assert frontmatter["tags"] == ["code", "review", "quality"]
        assert frontmatter["author"] == "Test Author"
        assert "Review code carefully." in instructions

    def test_parse_no_frontmatter(self):
        """Test parsing file without frontmatter."""
        content = "Just instructions without frontmatter."

        frontmatter, instructions = parse_skill_md(content)

        assert frontmatter == {}
        assert instructions == "Just instructions without frontmatter."

    def test_parse_quoted_values(self):
        """Test parsing quoted strings in frontmatter."""
        content = """---
name: "quoted-skill"
description: 'Single quoted description'
---

Instructions here.
"""
        frontmatter, instructions = parse_skill_md(content)

        assert frontmatter["name"] == "quoted-skill"
        assert frontmatter["description"] == "Single quoted description"


class TestDiscoverSkills:
    """Tests for skill discovery."""

    def test_discover_skills_in_directory(self):
        """Test discovering skills from a directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a skill directory
            skill_dir = Path(tmpdir) / "my-skill"
            skill_dir.mkdir()

            # Create SKILL.md
            (skill_dir / "SKILL.md").write_text("""---
name: my-skill
description: My test skill
version: 2.0.0
tags:
  - test
---

# How to use

Follow these steps...
""")

            # Create a resource file
            (skill_dir / "template.py").write_text("# Template file")

            skills = discover_skills([{"path": tmpdir}])

            assert len(skills) == 1
            assert skills[0]["name"] == "my-skill"
            assert skills[0]["description"] == "My test skill"
            assert skills[0]["version"] == "2.0.0"
            assert skills[0]["tags"] == ["test"]
            assert skills[0]["frontmatter_loaded"] is True
            assert "template.py" in skills[0].get("resources", [])

    def test_discover_multiple_skills(self):
        """Test discovering multiple skills."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create first skill
            skill1 = Path(tmpdir) / "skill-a"
            skill1.mkdir()
            (skill1 / "SKILL.md").write_text("""---
name: skill-a
description: First skill
---

Instructions A
""")

            # Create second skill
            skill2 = Path(tmpdir) / "skill-b"
            skill2.mkdir()
            (skill2 / "SKILL.md").write_text("""---
name: skill-b
description: Second skill
---

Instructions B
""")

            skills = discover_skills([{"path": tmpdir}])

            assert len(skills) == 2
            names = {s["name"] for s in skills}
            assert names == {"skill-a", "skill-b"}

    def test_discover_skills_non_recursive(self):
        """Test non-recursive skill discovery."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create nested skill
            nested = Path(tmpdir) / "category" / "nested-skill"
            nested.mkdir(parents=True)
            (nested / "SKILL.md").write_text("""---
name: nested-skill
description: Nested skill
---

Instructions
""")

            # Create top-level skill
            top = Path(tmpdir) / "top-skill"
            top.mkdir()
            (top / "SKILL.md").write_text("""---
name: top-skill
description: Top skill
---

Instructions
""")

            # Non-recursive should only find top-level
            skills = discover_skills([{"path": tmpdir, "recursive": False}])

            assert len(skills) == 1
            assert skills[0]["name"] == "top-skill"

    def test_discover_skills_empty_directory(self):
        """Test discovering skills from empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skills = discover_skills([{"path": tmpdir}])
            assert skills == []

    def test_discover_skills_nonexistent_directory(self):
        """Test discovering skills from nonexistent directory."""
        skills = discover_skills([{"path": "/nonexistent/path"}])
        assert skills == []


class TestLoadSkillInstructions:
    """Tests for loading skill instructions."""

    def test_load_skill_instructions(self):
        """Test loading full instructions from a skill."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir) / "my-skill"
            skill_dir.mkdir()

            (skill_dir / "SKILL.md").write_text("""---
name: my-skill
description: Test skill
---

# Detailed Instructions

1. Step one
2. Step two
3. Step three

## Examples

Here are some examples...
""")

            instructions = load_skill_instructions(str(skill_dir))

            assert "# Detailed Instructions" in instructions
            assert "Step one" in instructions
            assert "## Examples" in instructions

    def test_load_skill_instructions_not_found(self):
        """Test loading instructions from nonexistent skill."""
        result = load_skill_instructions("/nonexistent/skill")
        assert "Error:" in result


class TestSkillsToolset:
    """Tests for skills toolset."""

    def test_create_toolset(self):
        """Test creating a skills toolset."""
        toolset = create_skills_toolset(id="test-skills")
        assert toolset is not None

    def test_create_toolset_with_skills(self):
        """Test creating toolset with pre-loaded skills."""
        skills = [
            {
                "name": "test-skill",
                "description": "A test skill",
                "path": "/tmp/test-skill",
                "tags": ["test"],
                "version": "1.0.0",
                "author": "",
                "frontmatter_loaded": True,
            }
        ]

        toolset = create_skills_toolset(id="test-skills", skills=skills)
        assert toolset is not None

    def test_create_toolset_with_directories(self):
        """Test creating toolset with skill directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a skill
            skill_dir = Path(tmpdir) / "my-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text("""---
name: my-skill
description: Test skill
---

Instructions
""")

            toolset = create_skills_toolset(
                id="test-skills",
                directories=[{"path": tmpdir}],
            )
            assert toolset is not None


def test_skills_integration():
    """Test that skills toolset integrates properly with the agent."""
    from pydantic_ai.models.test import TestModel

    from pydantic_deep import create_deep_agent

    skills = [
        {
            "name": "code-review",
            "description": "Reviews code for issues",
            "path": "/skills/code-review",
            "tags": ["code", "quality"],
            "version": "1.0.0",
            "author": "Test",
            "frontmatter_loaded": True,
            "resources": ["template.md"],
        }
    ]

    # Create agent with skills
    agent = create_deep_agent(
        model=TestModel(),
        skills=skills,
        include_skills=True,
    )

    assert agent is not None


def test_skills_integration_with_directories():
    """Test skills discovery from directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a skill
        skill_dir = Path(tmpdir) / "test-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("""---
name: test-skill
description: Test skill for testing
version: 1.0.0
---

# How to Use This Skill

Follow these detailed instructions.
""")

        from pydantic_ai.models.test import TestModel

        from pydantic_deep import create_deep_agent

        # Create agent with skill directories
        agent = create_deep_agent(
            model=TestModel(),
            skill_directories=[{"path": tmpdir}],
            include_skills=True,
        )

        assert agent is not None
