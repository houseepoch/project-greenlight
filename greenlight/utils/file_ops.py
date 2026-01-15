"""
File operations utility.

Simple helpers for project file management.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional


def ensure_project_structure(project_path: Path) -> None:
    """
    Ensure a project has the required directory structure.

    Creates:
    - world_bible/
    - scripts/
    - storyboard/
    - references/
    - storyboard_output/generated/
    """
    project_path = Path(project_path)

    directories = [
        project_path / "world_bible",
        project_path / "scripts",
        project_path / "storyboard",
        project_path / "references",
        project_path / "storyboard_output" / "generated",
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def load_json(path: Path) -> Optional[dict]:
    """Load JSON file, return None if not exists or invalid."""
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, IOError):
        pass
    return None


def save_json(path: Path, data: dict) -> bool:
    """Save data as JSON file."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return True
    except IOError:
        return False


def get_project_files(project_path: Path) -> dict[str, bool]:
    """
    Check which files exist in a project.

    Returns dict with file existence status.
    """
    project_path = Path(project_path)

    return {
        "pitch": (project_path / "world_bible" / "pitch.md").exists(),
        "world_config": (project_path / "world_bible" / "world_config.json").exists(),
        "script": (project_path / "scripts" / "script.md").exists(),
        "visual_script": (project_path / "storyboard" / "visual_script.json").exists(),
        "prompts": (project_path / "storyboard" / "prompts.json").exists(),
    }


def update_project_timestamp(project_path: Path) -> None:
    """Update the last_modified timestamp in project.json."""
    config_path = Path(project_path) / "project.json"
    if config_path.exists():
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
            config["last_modified"] = datetime.now().isoformat()
            config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
        except (json.JSONDecodeError, IOError):
            pass
