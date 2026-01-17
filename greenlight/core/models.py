"""
Pydantic models for Project Greenlight.

All data models in one place - no scattered definitions.
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, Any
from pydantic import BaseModel, Field


# =============================================================================
# ENUMS
# =============================================================================

class PipelineStage(str, Enum):
    """Pipeline execution stages."""
    IDLE = "idle"
    INITIALIZING = "initializing"
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    ERROR = "error"
    CANCELLED = "cancelled"


class VisualStyle(str, Enum):
    """Visual style options for storyboards."""
    LIVE_ACTION = "live_action"
    ANIMATION = "animation"
    ANIME = "anime"
    COMIC = "comic"
    NOIR = "noir"
    VINTAGE = "vintage"


class MediaType(str, Enum):
    """Content length/type."""
    SHORT = "short"  # 1-5 scenes
    STANDARD = "standard"  # 5-15 scenes
    FEATURE = "feature"  # 15+ scenes


# =============================================================================
# PROJECT MODELS
# =============================================================================

class Project(BaseModel):
    """A greenlight project."""
    name: str
    path: str
    created_at: datetime = Field(default_factory=datetime.now)
    last_modified: datetime = Field(default_factory=datetime.now)
    visual_style: VisualStyle = VisualStyle.LIVE_ACTION
    media_type: MediaType = MediaType.STANDARD


# =============================================================================
# WORLD CONTEXT - Generated first, rolls over to all entities
# =============================================================================

class WorldContext(BaseModel):
    """
    World context extracted from pitch FIRST.
    This rolls over to inform all entity extraction and enrichment.
    """
    # Setting
    time_period: str = ""  # e.g., "Tang Dynasty China, 8th century"
    technology_level: str = ""  # e.g., "Pre-industrial, paper/ink, no electricity"

    # Culture
    cultural_context: str = ""  # e.g., "Confucian hierarchy, courtesans as artists"
    social_structure: str = ""  # e.g., "Rigid class system, merchant class rising"

    # Visual
    clothing_norms: str = ""  # e.g., "Hanfu, silk robes, jade ornaments, hair pins"
    architecture_style: str = ""  # e.g., "Traditional Chinese pavilions, paper screens"
    color_palette: str = ""  # e.g., "Warm earth tones, red accents, jade green"

    # Atmosphere
    lighting_style: str = ""  # e.g., "Candlelight, lanterns, natural sunlight"
    mood: str = ""  # e.g., "Romantic tension, forbidden desire"

    # Rules/Constraints
    setting_rules: list[str] = Field(default_factory=list)  # e.g., ["No modern items", "Formal speech"]


# =============================================================================
# ENTITY MODELS - Enriched with world context
# =============================================================================

class Character(BaseModel):
    """
    A character in the story.

    Simplified schema focused on visual storytelling:
    - appearance: Physical look (inferred from world_context)
    - clothing: Period-appropriate attire (MUST match world_context.clothing_norms)
    - personality: Key traits and behavior
    - summary: Brief overview
    """
    tag: str  # e.g., "CHAR_MEI" - canonical format
    name: str
    role: str = ""  # protagonist, antagonist, supporting, love_interest, mentor
    appearance: str = ""  # Physical appearance (world-context aware)
    clothing: str = ""  # Period-appropriate attire (from world_context.clothing_norms)
    personality: str = ""  # Key traits and behavior
    summary: str = ""  # Brief character overview


class Location(BaseModel):
    """
    A location in the story.

    Includes directional views for camera reference image selection.
    """
    tag: str  # e.g., "LOC_PALACE"
    name: str
    description: str = ""
    time_of_day: str = ""  # day, night, dawn, dusk
    # Directional views for camera positioning
    view_north: str = ""
    view_east: str = ""
    view_south: str = ""
    view_west: str = ""


class Prop(BaseModel):
    """A significant prop in the story."""
    tag: str  # e.g., "PROP_SWORD"
    name: str
    description: str = ""  # Period-appropriate description


# =============================================================================
# WORLD CONFIG - Complete world bible
# =============================================================================

class WorldConfig(BaseModel):
    """
    Complete world configuration.

    Generated in phases:
    1. world_context - Setting, culture, visual rules (FIRST)
    2. Entity extraction - Characters, locations, props (with consensus)
    3. Entity enrichment - Details inferred from world_context
    """
    title: str
    genre: str = "Drama"
    visual_style: str = "live_action"
    logline: str = ""
    synopsis: str = ""
    themes: list[str] = Field(default_factory=list)

    # World context (extracted first, rolls over to entities)
    world_context: WorldContext = Field(default_factory=WorldContext)

    # Entities (enriched with world context)
    characters: list[Character] = Field(default_factory=list)
    locations: list[Location] = Field(default_factory=list)
    props: list[Prop] = Field(default_factory=list)

    # All tags for quick reference
    all_tags: list[str] = Field(default_factory=list)

    # Status
    status: str = "draft"  # draft, pending_approval, approved


# =============================================================================
# STORY OUTLINE - Light, editable planning phase
# =============================================================================

class SceneBeat(BaseModel):
    """A single beat within a scene."""
    description: str  # Short description of what happens
    characters: list[str] = Field(default_factory=list)  # Character tags involved


class SceneOutline(BaseModel):
    """
    A scene in the story outline.

    Light and editable - user can modify before Director phase.
    """
    scene_number: int
    title: str = ""  # e.g., "Dawn at the Brothel"
    location_tag: str = ""  # e.g., "LOC_MEI_BEDROOM"
    location_name: str = ""
    time_of_day: str = "day"  # day, night, dawn, dusk
    characters: list[str] = Field(default_factory=list)  # Character tags present
    summary: str = ""  # 1-2 sentence description
    beats: list[SceneBeat] = Field(default_factory=list)  # Key moments


class StoryOutline(BaseModel):
    """
    Complete story outline - the editable planning document.

    User reviews and edits this before proceeding to Director phase.
    """
    title: str
    total_scenes: int = 0
    scenes: list[SceneOutline] = Field(default_factory=list)
    status: str = "draft"  # draft, confirmed


# =============================================================================
# VISUAL SCRIPT MODELS - Generated by Director
# =============================================================================

class Frame(BaseModel):
    """A single frame/shot in the visual script."""
    frame_id: str  # e.g., "1.1.cA" (scene.frame.camera)
    scene_number: int
    prompt: str  # Image generation prompt
    visual_description: str = ""
    camera_notation: str = ""  # e.g., "MS" (medium shot), "WS", "CU", "ECU"
    tags: dict[str, list[str]] = Field(default_factory=dict)  # characters, locations, props
    location_direction: str = "NORTH"  # For location reference image selection


class VisualScript(BaseModel):
    """Complete visual script with all frames."""
    title: str
    total_frames: int = 0
    scenes: list[dict] = Field(default_factory=list)  # Scene metadata
    frames: list[Frame] = Field(default_factory=list)


# =============================================================================
# PIPELINE STATUS MODELS
# =============================================================================

class StageInfo(BaseModel):
    """Information about a pipeline stage."""
    name: str
    status: PipelineStage = PipelineStage.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    message: Optional[str] = None


class PipelineStatus(BaseModel):
    """Status of a running pipeline."""
    pipeline_id: str
    name: str  # writer, director, references, storyboard
    status: PipelineStage = PipelineStage.IDLE
    progress: float = 0.0  # 0.0 to 1.0
    message: str = ""
    logs: list[str] = Field(default_factory=list)
    stages: list[StageInfo] = Field(default_factory=list)
    current_stage: Optional[str] = None
    total_items: int = 0
    completed_items: int = 0
    current_item: Optional[str] = None
    error: Optional[str] = None


# =============================================================================
# API REQUEST/RESPONSE MODELS
# =============================================================================

class PipelineRequest(BaseModel):
    """Request to start a pipeline."""
    project_path: str
    image_model: str = "seedream"
    max_frames: Optional[int] = None
    media_type: str = "standard"
    visual_style: str = "live_action"


class PipelineResponse(BaseModel):
    """Response from starting a pipeline."""
    success: bool
    message: str
    pipeline_id: Optional[str] = None


class ProjectCreateRequest(BaseModel):
    """Request to create a new project."""
    name: str
    path: Optional[str] = None
    visual_style: str = "live_action"
    media_type: str = "standard"
    pitch: str = ""  # Initial pitch text


class ProjectResponse(BaseModel):
    """Response with project information."""
    name: str
    path: str
    created_at: str
    last_modified: str
    has_pitch: bool = False
    has_world_config: bool = False
    has_story_outline: bool = False
    has_visual_script: bool = False
    has_storyboard: bool = False


# =============================================================================
# INGESTION MODELS - Document/Image Processing
# =============================================================================

class EntityType(str, Enum):
    """Entity type for classification."""
    CHARACTER = "character"
    LOCATION = "location"
    PROP = "prop"


class ExtractedEntity(BaseModel):
    """
    An entity extracted during ingestion, before user confirmation.

    Users will review these and:
    - Assign canonical tags (CHAR_, LOC_, PROP_)
    - Confirm or reject each entity
    - Add missing entities manually
    """
    name: str  # Extracted or suggested name
    type: Optional[EntityType] = None  # User assigns this in modal
    type_suggestion: Optional[EntityType] = None  # LLM's suggestion
    role_hint: str = ""  # For characters: protagonist, antagonist, etc.
    description: str = ""  # Brief description from extraction
    contexts: list[str] = Field(default_factory=list)  # Source contexts
    mentions: int = 1  # How many times entity was found
    source: str = "text"  # text, image, or both
    confirmed: bool = False  # User has confirmed this entity


class IngestionResult(BaseModel):
    """Result of the ingestion pipeline."""
    created_at: datetime = Field(default_factory=datetime.now)
    status: str = "pending_confirmation"  # pending_confirmation, confirmed, processing
    source_files: dict = Field(default_factory=dict)  # {documents: [], images: []}

    # Extracted entities (pre-confirmation)
    characters: list[ExtractedEntity] = Field(default_factory=list)
    locations: list[ExtractedEntity] = Field(default_factory=list)
    props: list[ExtractedEntity] = Field(default_factory=list)

    # World hints from images
    world_hints: dict = Field(default_factory=dict)

    # Stats
    total_chunks: int = 0
    documents_processed: int = 0
    images_processed: int = 0


class EntityConfirmation(BaseModel):
    """User confirmation of an extracted entity."""
    name: str
    type: EntityType
    tag: str  # Canonical tag (CHAR_NAME, LOC_NAME, PROP_NAME)
    confirmed: bool = True
    role_hint: Optional[str] = None  # For characters: protagonist, antagonist, supporting, etc.


class ConfirmEntitiesRequest(BaseModel):
    """Request to confirm entities after ingestion."""
    project_path: str
    entities: list[EntityConfirmation]


class ConfirmEntitiesResponse(BaseModel):
    """Response from entity confirmation."""
    success: bool
    message: str
    characters_confirmed: int = 0
    locations_confirmed: int = 0
    props_confirmed: int = 0


# =============================================================================
# WORLD BUILDER MODELS - Progressive Field Population
# =============================================================================

class FieldStatus(str, Enum):
    """Status of a world bible field."""
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETE = "complete"
    ERROR = "error"
    USER_EDITED = "user_edited"


class WorldBibleField(BaseModel):
    """A single field in the world bible with status tracking."""
    field_name: str
    value: str = ""
    status: FieldStatus = FieldStatus.PENDING
    word_count: int = 0
    last_updated: Optional[datetime] = None


class EntityField(BaseModel):
    """A field on an entity (character, location, prop)."""
    field_name: str
    value: str = ""
    status: FieldStatus = FieldStatus.PENDING
    word_count: int = 0


class WorldBibleProgress(BaseModel):
    """Progress tracking for world bible generation."""
    total_fields: int = 0
    completed_fields: int = 0
    generating_fields: list[str] = Field(default_factory=list)
    error_fields: list[str] = Field(default_factory=list)

    # Core world fields
    world_fields: list[WorldBibleField] = Field(default_factory=list)

    # Entity-specific progress
    characters_progress: dict[str, list[EntityField]] = Field(default_factory=dict)
    locations_progress: dict[str, list[EntityField]] = Field(default_factory=dict)
    props_progress: dict[str, list[EntityField]] = Field(default_factory=dict)


# =============================================================================
# REFERENCE IMAGE MODELS
# =============================================================================

class ReferenceImage(BaseModel):
    """A reference image for an entity."""
    entity_tag: str  # e.g., CHAR_MEI, LOC_PALACE
    entity_type: EntityType
    image_path: str
    source: str = "generated"  # generated, uploaded
    prompt_used: str = ""  # For generated images
    created_at: datetime = Field(default_factory=datetime.now)
    is_active: bool = True  # False if replaced by upload


class GenerateReferenceRequest(BaseModel):
    """Request to generate a reference image."""
    project_path: str
    entity_tag: str
    entity_type: str  # character, location, prop


class UploadReferenceRequest(BaseModel):
    """Request to upload a reference image replacement."""
    project_path: str
    entity_tag: str
    entity_type: str


# =============================================================================
# CHECKPOINT/VERSIONING MODELS
# =============================================================================

class CheckpointType(str, Enum):
    """Type of checkpoint."""
    AUTO = "auto"        # Created automatically before regeneration
    MANUAL = "manual"    # Created by user request


class Checkpoint(BaseModel):
    """A project checkpoint capturing pipeline state."""
    checkpoint_id: str  # UUID
    name: str
    description: str = ""
    created_at: datetime = Field(default_factory=datetime.now)
    checkpoint_type: CheckpointType = CheckpointType.MANUAL

    # File manifest - what was archived
    files_archived: list[str] = Field(default_factory=list)  # Relative paths
    frames_archived: int = 0

    # Stats
    total_frames: int = 0
    total_scenes: int = 0
    file_size_bytes: int = 0


class FrameVersion(BaseModel):
    """A single version of a frame image."""
    version_id: str  # UUID
    frame_id: str  # e.g., "1.1.cA"
    iteration: int  # 1, 2, 3...
    created_at: datetime = Field(default_factory=datetime.now)
    image_path: str  # Path in archive
    thumbnail_path: Optional[str] = None
    healing_notes: str = ""  # Why was this regenerated?
    continuity_score: float = 0.0  # From continuity check
    file_size_bytes: int = 0
    prompt_snapshot: str = ""  # The prompt used


class CheckpointIndex(BaseModel):
    """Index of all checkpoints for a project."""
    project_path: str
    checkpoints: list[Checkpoint] = Field(default_factory=list)
    frame_versions: dict[str, list[FrameVersion]] = Field(default_factory=dict)  # frame_id -> versions
    last_updated: datetime = Field(default_factory=datetime.now)


class StorageStats(BaseModel):
    """Storage usage statistics for checkpoints."""
    total_checkpoints: int = 0
    total_versions: int = 0
    total_size_bytes: int = 0
    total_size_mb: float = 0.0
    oldest_checkpoint: Optional[datetime] = None
    newest_checkpoint: Optional[datetime] = None
