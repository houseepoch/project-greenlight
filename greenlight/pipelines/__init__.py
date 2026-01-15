"""Pipeline modules for Project Greenlight."""

from .writer import WriterPipeline
from .director import DirectorPipeline
from .references import ReferencesPipeline, generate_references
from .storyboard import (
    StoryboardPipeline,
    generate_storyboard,
    generate_scene,
    generate_frame,
)
from .outline_generator import OutlineGeneratorPipeline, generate_outlines
from .world_builder import WorldBuilderPipeline, build_world

__all__ = [
    # Pipelines
    "WriterPipeline",
    "DirectorPipeline",
    "ReferencesPipeline",
    "StoryboardPipeline",
    "OutlineGeneratorPipeline",
    "WorldBuilderPipeline",
    # Convenience functions
    "generate_storyboard",
    "generate_scene",
    "generate_frame",
    "generate_outlines",
    "generate_references",
    "build_world",
]
