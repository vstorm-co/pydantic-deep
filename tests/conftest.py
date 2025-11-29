"""Pytest configuration and fixtures."""

import tempfile
from pathlib import Path

import pytest

from pydantic_deep.backends.filesystem import FilesystemBackend
from pydantic_deep.backends.state import StateBackend
from pydantic_deep.deps import DeepAgentDeps


@pytest.fixture
def state_backend():
    """Create a fresh StateBackend."""
    return StateBackend()


@pytest.fixture
def deps(state_backend):
    """Create default DeepAgentDeps with StateBackend."""
    return DeepAgentDeps(backend=state_backend)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def filesystem_backend(temp_dir):
    """Create a FilesystemBackend with temporary directory."""
    return FilesystemBackend(temp_dir)
