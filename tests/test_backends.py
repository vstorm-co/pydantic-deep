"""Tests for backend implementations."""

from pydantic_deep.backends.composite import CompositeBackend
from pydantic_deep.backends.filesystem import FilesystemBackend
from pydantic_deep.backends.state import StateBackend


class TestStateBackend:
    """Tests for StateBackend."""

    def test_write_and_read(self):
        """Test writing and reading a file."""
        backend = StateBackend()

        result = backend.write("/test.txt", "Hello, World!")
        assert result.error is None
        assert result.path == "/test.txt"

        content = backend.read("/test.txt")
        assert "Hello, World!" in content
        assert "1\t" in content  # Line number

    def test_write_multiline(self):
        """Test writing multiline content."""
        backend = StateBackend()

        content = "Line 1\nLine 2\nLine 3"
        backend.write("/multi.txt", content)

        result = backend.read("/multi.txt")
        assert "Line 1" in result
        assert "Line 2" in result
        assert "Line 3" in result

    def test_read_nonexistent(self):
        """Test reading a file that doesn't exist."""
        backend = StateBackend()

        result = backend.read("/nonexistent.txt")
        assert "Error:" in result
        assert "not found" in result

    def test_edit_file(self):
        """Test editing a file."""
        backend = StateBackend()

        backend.write("/test.txt", "Hello, World!")
        result = backend.edit("/test.txt", "World", "Universe")

        assert result.error is None
        assert result.occurrences == 1

        content = backend.read("/test.txt")
        assert "Universe" in content
        assert "World" not in content

    def test_edit_multiple_occurrences(self):
        """Test editing with multiple occurrences."""
        backend = StateBackend()

        backend.write("/test.txt", "foo bar foo baz foo")

        # Should fail without replace_all
        result = backend.edit("/test.txt", "foo", "qux")
        assert result.error is not None
        assert "3 times" in result.error

        # Should succeed with replace_all
        result = backend.edit("/test.txt", "foo", "qux", replace_all=True)
        assert result.error is None
        assert result.occurrences == 3

    def test_ls_info(self):
        """Test listing directory contents."""
        backend = StateBackend()

        backend.write("/dir/file1.txt", "content1")
        backend.write("/dir/file2.txt", "content2")
        backend.write("/dir/subdir/file3.txt", "content3")

        entries = backend.ls_info("/dir")
        names = [e["name"] for e in entries]

        assert "file1.txt" in names
        assert "file2.txt" in names
        assert "subdir" in names

    def test_glob_info(self):
        """Test glob pattern matching."""
        backend = StateBackend()

        backend.write("/src/main.py", "# main")
        backend.write("/src/utils.py", "# utils")
        backend.write("/src/test.js", "// test")
        backend.write("/lib/helper.py", "# helper")

        # Find all Python files
        results = backend.glob_info("**/*.py")
        paths = [r["path"] for r in results]

        assert "/src/main.py" in paths
        assert "/src/utils.py" in paths
        assert "/lib/helper.py" in paths
        assert "/src/test.js" not in paths

    def test_grep_raw(self):
        """Test grep searching."""
        backend = StateBackend()

        backend.write("/test.py", "def hello():\n    print('Hello')")
        backend.write("/other.py", "def goodbye():\n    print('Goodbye')")

        results = backend.grep_raw("hello")
        assert isinstance(results, list)
        assert len(results) > 0
        assert any(r["path"] == "/test.py" for r in results)

    def test_path_validation(self):
        """Test path validation security."""
        backend = StateBackend()

        # Test .. traversal
        result = backend.write("/../etc/passwd", "hack")
        assert result.error is not None

        # Test ~ expansion
        result = backend.write("~/secret", "hack")
        assert result.error is not None


class TestFilesystemBackend:
    """Tests for FilesystemBackend."""

    def test_write_and_read(self, tmp_path):
        """Test writing and reading a file."""
        backend = FilesystemBackend(tmp_path)

        result = backend.write("/test.txt", "Hello, World!")
        assert result.error is None

        content = backend.read("/test.txt")
        assert "Hello, World!" in content

    def test_virtual_mode(self, tmp_path):
        """Test virtual_mode creates directory."""
        new_dir = tmp_path / "new_virtual_dir"
        assert not new_dir.exists()

        _ = FilesystemBackend(new_dir, virtual_mode=True)
        assert new_dir.exists()

    def test_edit_file(self, tmp_path):
        """Test editing a file."""
        backend = FilesystemBackend(tmp_path)

        backend.write("/test.txt", "Hello, World!")
        result = backend.edit("/test.txt", "World", "Universe")

        assert result.error is None

        content = backend.read("/test.txt")
        assert "Universe" in content

    def test_glob_info(self, tmp_path):
        """Test glob pattern matching."""
        backend = FilesystemBackend(tmp_path)

        backend.write("/src/main.py", "# main")
        backend.write("/src/utils.py", "# utils")

        results = backend.glob_info("**/*.py")
        assert len(results) == 2


class TestCompositeBackend:
    """Tests for CompositeBackend."""

    def test_routing(self):
        """Test that operations are routed to correct backend."""
        memory_backend = StateBackend()
        temp_backend = StateBackend()

        composite = CompositeBackend(
            default=memory_backend,
            routes={"/temp/": temp_backend},
        )

        # Write to default backend
        composite.write("/data.txt", "default data")
        assert "/data.txt" in memory_backend.files
        assert "/data.txt" not in temp_backend.files

        # Write to temp backend
        composite.write("/temp/cache.txt", "temp data")
        assert "/temp/cache.txt" in temp_backend.files
        assert "/temp/cache.txt" not in memory_backend.files

    def test_aggregated_ls(self):
        """Test that root ls aggregates from all backends."""
        backend1 = StateBackend()
        backend2 = StateBackend()

        backend1.write("/file1.txt", "content1")
        backend2.write("/special/file2.txt", "content2")

        composite = CompositeBackend(
            default=backend1,
            routes={"/special/": backend2},
        )

        entries = composite.ls_info("/")
        names = [e["name"] for e in entries]

        assert "file1.txt" in names
        assert "special" in names  # Virtual directory for route
