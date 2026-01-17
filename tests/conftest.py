"""Pytest configuration for Project Greenlight tests."""

import os
import sys
from pathlib import Path

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def test_project_path():
    """Return path to test project directory."""
    return project_root / "test_project"


@pytest.fixture
def projects_path():
    """Return path to projects directory."""
    return project_root / "projects"
