"""
Checkpoint and Versioning Service for Project Greenlight.

Manages project checkpoints, frame versioning, and state archival.
Enables restoring to any previous pipeline state.
"""

import hashlib
import json
import logging
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import (
    Checkpoint,
    CheckpointIndex,
    CheckpointType,
    FrameVersion,
    StorageStats,
)

logger = logging.getLogger(__name__)


# Files to archive for a full checkpoint
CHECKPOINT_FILES = [
    "world_bible/world_config.json",
    "outlines/outline_variants.json",
    "outlines/confirmed_outline.json",
    "storyboard/visual_script.json",
    "storyboard/prompts.json",
]


class CheckpointService:
    """Manages project checkpoints and frame versioning."""

    def __init__(self, project_path: Path):
        self.project_path = Path(project_path)
        self.checkpoints_dir = self.project_path / "checkpoints"
        self.index_path = self.checkpoints_dir / "checkpoint_index.json"
        self.thumbnails_dir = self.checkpoints_dir / "thumbnails"

    def _ensure_dirs(self):
        """Ensure checkpoint directories exist."""
        self.checkpoints_dir.mkdir(parents=True, exist_ok=True)
        self.thumbnails_dir.mkdir(parents=True, exist_ok=True)

    def _load_index(self) -> CheckpointIndex:
        """Load or create the checkpoint index."""
        if self.index_path.exists():
            try:
                data = json.loads(self.index_path.read_text(encoding="utf-8"))
                return CheckpointIndex(**data)
            except Exception as e:
                logger.error(f"Failed to load checkpoint index: {e}")

        return CheckpointIndex(project_path=str(self.project_path))

    def _save_index(self, index: CheckpointIndex):
        """Save the checkpoint index."""
        self._ensure_dirs()
        index.last_updated = datetime.now()
        self.index_path.write_text(
            index.model_dump_json(indent=2),
            encoding="utf-8"
        )

    def create_checkpoint(
        self,
        name: str,
        description: str = "",
        checkpoint_type: CheckpointType = CheckpointType.MANUAL,
        include_images: bool = True,
    ) -> Checkpoint:
        """
        Create a new checkpoint of current project state.

        Args:
            name: Human-readable name for the checkpoint
            description: Optional description
            checkpoint_type: MANUAL or AUTO
            include_images: Whether to archive generated frame images

        Returns:
            The created Checkpoint
        """
        self._ensure_dirs()

        checkpoint_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        checkpoint_folder = f"cp_{timestamp}_{checkpoint_id}"
        checkpoint_dir = self.checkpoints_dir / checkpoint_folder

        checkpoint_dir.mkdir(parents=True, exist_ok=True)

        files_archived = []
        total_size = 0

        # Archive JSON files
        for rel_path in CHECKPOINT_FILES:
            src = self.project_path / rel_path
            if src.exists():
                dst = checkpoint_dir / Path(rel_path).name
                shutil.copy2(src, dst)
                files_archived.append(rel_path)
                total_size += dst.stat().st_size

        # Archive frame images
        frames_archived = 0
        total_frames = 0
        total_scenes = set()

        if include_images:
            frames_dir = checkpoint_dir / "frames"
            frames_dir.mkdir(exist_ok=True)

            generated_dir = self.project_path / "storyboard_output" / "generated"
            if generated_dir.exists():
                for img_path in generated_dir.glob("*.png"):
                    if img_path.name.startswith("backups"):
                        continue
                    dst = frames_dir / img_path.name
                    shutil.copy2(img_path, dst)
                    frames_archived += 1
                    total_size += dst.stat().st_size

                    # Extract scene number from frame_id (e.g., "1.2.cA" -> scene 1)
                    frame_id = img_path.stem
                    try:
                        scene_num = int(frame_id.split(".")[0])
                        total_scenes.add(scene_num)
                    except (ValueError, IndexError):
                        pass

        # Count total frames from prompts.json
        prompts_path = self.project_path / "storyboard" / "prompts.json"
        if prompts_path.exists():
            try:
                prompts = json.loads(prompts_path.read_text(encoding="utf-8"))
                total_frames = len(prompts)
            except Exception:
                total_frames = frames_archived

        # Create checkpoint record
        checkpoint = Checkpoint(
            checkpoint_id=checkpoint_id,
            name=name,
            description=description,
            created_at=datetime.now(),
            checkpoint_type=checkpoint_type,
            files_archived=files_archived,
            frames_archived=frames_archived,
            total_frames=total_frames,
            total_scenes=len(total_scenes),
            file_size_bytes=total_size,
        )

        # Save manifest
        manifest_path = checkpoint_dir / "manifest.json"
        manifest_path.write_text(
            checkpoint.model_dump_json(indent=2),
            encoding="utf-8"
        )

        # Update index
        index = self._load_index()
        index.checkpoints.append(checkpoint)
        self._save_index(index)

        logger.info(f"Created checkpoint: {name} ({checkpoint_id})")
        return checkpoint

    def restore_checkpoint(
        self,
        checkpoint_id: str,
        archive_current: bool = True,
    ) -> dict:
        """
        Restore project to a checkpoint's state.

        Args:
            checkpoint_id: ID of checkpoint to restore
            archive_current: Whether to create a checkpoint of current state first

        Returns:
            dict with success status and message
        """
        index = self._load_index()

        # Find the checkpoint
        checkpoint = None
        for cp in index.checkpoints:
            if cp.checkpoint_id == checkpoint_id:
                checkpoint = cp
                break

        if not checkpoint:
            return {"success": False, "error": f"Checkpoint {checkpoint_id} not found"}

        # Find checkpoint directory
        checkpoint_dir = None
        for d in self.checkpoints_dir.iterdir():
            if d.is_dir() and checkpoint_id in d.name:
                checkpoint_dir = d
                break

        if not checkpoint_dir or not checkpoint_dir.exists():
            return {"success": False, "error": "Checkpoint directory not found"}

        # Archive current state first
        if archive_current:
            self.create_checkpoint(
                name=f"Before restore to '{checkpoint.name}'",
                description="Auto-created before restore",
                checkpoint_type=CheckpointType.AUTO,
            )

        # Restore JSON files
        for filename in ["world_config.json", "outline_variants.json",
                         "confirmed_outline.json", "visual_script.json", "prompts.json"]:
            src = checkpoint_dir / filename
            if src.exists():
                # Determine destination
                if filename == "world_config.json":
                    dst = self.project_path / "world_bible" / filename
                elif filename in ["outline_variants.json", "confirmed_outline.json"]:
                    dst = self.project_path / "outlines" / filename
                else:
                    dst = self.project_path / "storyboard" / filename

                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)

        # Restore frame images
        frames_dir = checkpoint_dir / "frames"
        if frames_dir.exists():
            generated_dir = self.project_path / "storyboard_output" / "generated"
            generated_dir.mkdir(parents=True, exist_ok=True)

            # Clear current frames (move to backups)
            backup_dir = generated_dir / "backups"
            backup_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            for img in generated_dir.glob("*.png"):
                backup_path = backup_dir / f"{img.stem}_prerestore_{timestamp}{img.suffix}"
                shutil.move(str(img), str(backup_path))

            # Copy archived frames
            for img in frames_dir.glob("*.png"):
                shutil.copy2(img, generated_dir / img.name)

        logger.info(f"Restored checkpoint: {checkpoint.name}")
        return {
            "success": True,
            "message": f"Restored to checkpoint '{checkpoint.name}'",
            "checkpoint": checkpoint.model_dump(),
        }

    def delete_checkpoint(self, checkpoint_id: str) -> dict:
        """Delete a checkpoint."""
        index = self._load_index()

        # Find and remove from index
        checkpoint = None
        for i, cp in enumerate(index.checkpoints):
            if cp.checkpoint_id == checkpoint_id:
                checkpoint = index.checkpoints.pop(i)
                break

        if not checkpoint:
            return {"success": False, "error": f"Checkpoint {checkpoint_id} not found"}

        # Delete checkpoint directory
        for d in self.checkpoints_dir.iterdir():
            if d.is_dir() and checkpoint_id in d.name:
                shutil.rmtree(d)
                break

        self._save_index(index)

        logger.info(f"Deleted checkpoint: {checkpoint.name}")
        return {"success": True, "message": f"Deleted checkpoint '{checkpoint.name}'"}

    def archive_frame(
        self,
        frame_id: str,
        healing_notes: str = "",
        continuity_score: float = 0.0,
        prompt: str = "",
    ) -> Optional[FrameVersion]:
        """
        Archive current frame before regeneration.

        Args:
            frame_id: The frame identifier (e.g., "1.1.cA")
            healing_notes: Why this frame is being regenerated
            continuity_score: Score from continuity check
            prompt: The prompt used for this version

        Returns:
            The created FrameVersion or None if frame doesn't exist
        """
        self._ensure_dirs()

        # Find the current frame image
        generated_dir = self.project_path / "storyboard_output" / "generated"
        current_frame = generated_dir / f"{frame_id}.png"

        if not current_frame.exists():
            return None

        index = self._load_index()

        # Get current versions for this frame
        versions = index.frame_versions.get(frame_id, [])
        iteration = len(versions) + 1

        # Create version record
        version_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Archive to versions directory
        versions_dir = self.checkpoints_dir / "frame_versions" / frame_id
        versions_dir.mkdir(parents=True, exist_ok=True)

        archived_name = f"{frame_id}_v{iteration}_{timestamp}.png"
        archived_path = versions_dir / archived_name
        shutil.copy2(current_frame, archived_path)

        # Generate thumbnail
        thumbnail_path = None
        try:
            thumbnail_path = self._generate_thumbnail(archived_path, version_id)
        except Exception as e:
            logger.warning(f"Failed to generate thumbnail: {e}")

        version = FrameVersion(
            version_id=version_id,
            frame_id=frame_id,
            iteration=iteration,
            created_at=datetime.now(),
            image_path=str(archived_path.relative_to(self.project_path)),
            thumbnail_path=str(thumbnail_path.relative_to(self.project_path)) if thumbnail_path else None,
            healing_notes=healing_notes,
            continuity_score=continuity_score,
            file_size_bytes=archived_path.stat().st_size,
            prompt_snapshot=prompt,
        )

        # Update index
        if frame_id not in index.frame_versions:
            index.frame_versions[frame_id] = []
        index.frame_versions[frame_id].append(version)
        self._save_index(index)

        logger.info(f"Archived frame {frame_id} v{iteration}")
        return version

    def restore_frame_version(
        self,
        frame_id: str,
        version_id: str,
    ) -> dict:
        """
        Restore a frame to a previous version.

        Args:
            frame_id: The frame identifier
            version_id: The version to restore

        Returns:
            dict with success status
        """
        index = self._load_index()

        versions = index.frame_versions.get(frame_id, [])
        version = None
        for v in versions:
            if v.version_id == version_id:
                version = v
                break

        if not version:
            return {"success": False, "error": f"Version {version_id} not found"}

        archived_path = self.project_path / version.image_path
        if not archived_path.exists():
            return {"success": False, "error": "Archived image not found"}

        # Archive current before restoring
        self.archive_frame(
            frame_id=frame_id,
            healing_notes=f"Before restore to v{version.iteration}",
        )

        # Restore the version
        generated_dir = self.project_path / "storyboard_output" / "generated"
        target_path = generated_dir / f"{frame_id}.png"
        shutil.copy2(archived_path, target_path)

        logger.info(f"Restored frame {frame_id} to v{version.iteration}")
        return {
            "success": True,
            "message": f"Restored {frame_id} to version {version.iteration}",
            "version": version.model_dump(),
        }

    def get_frame_versions(self, frame_id: str) -> list[FrameVersion]:
        """Get all versions of a specific frame."""
        index = self._load_index()
        return index.frame_versions.get(frame_id, [])

    def get_all_frame_versions(self) -> dict[str, list[FrameVersion]]:
        """Get all frame versions for the project."""
        index = self._load_index()
        return index.frame_versions

    def get_all_checkpoints(self) -> list[Checkpoint]:
        """Get all checkpoints for the project."""
        index = self._load_index()
        return index.checkpoints

    def get_storage_stats(self) -> StorageStats:
        """Calculate storage usage for checkpoints."""
        index = self._load_index()

        total_size = 0
        oldest = None
        newest = None

        # Calculate checkpoint sizes
        for cp in index.checkpoints:
            total_size += cp.file_size_bytes
            if oldest is None or cp.created_at < oldest:
                oldest = cp.created_at
            if newest is None or cp.created_at > newest:
                newest = cp.created_at

        # Calculate version sizes
        total_versions = 0
        for frame_id, versions in index.frame_versions.items():
            for v in versions:
                total_versions += 1
                total_size += v.file_size_bytes

        return StorageStats(
            total_checkpoints=len(index.checkpoints),
            total_versions=total_versions,
            total_size_bytes=total_size,
            total_size_mb=round(total_size / (1024 * 1024), 2),
            oldest_checkpoint=oldest,
            newest_checkpoint=newest,
        )

    def _generate_thumbnail(self, image_path: Path, version_id: str) -> Optional[Path]:
        """Generate a thumbnail for quick preview."""
        try:
            from PIL import Image

            img = Image.open(image_path)

            # Resize to 256px width, maintaining aspect ratio
            width = 256
            ratio = width / img.width
            height = int(img.height * ratio)
            img = img.resize((width, height), Image.Resampling.LANCZOS)

            # Save as JPEG for smaller size
            thumbnail_path = self.thumbnails_dir / f"{version_id}.jpg"
            img.convert("RGB").save(thumbnail_path, "JPEG", quality=85)

            return thumbnail_path
        except ImportError:
            logger.warning("PIL not available for thumbnail generation")
            return None
        except Exception as e:
            logger.error(f"Thumbnail generation failed: {e}")
            return None

    def get_version_image_path(self, version_id: str, thumbnail: bool = False) -> Optional[Path]:
        """Get the path to a version's image or thumbnail."""
        index = self._load_index()

        for frame_id, versions in index.frame_versions.items():
            for v in versions:
                if v.version_id == version_id:
                    if thumbnail and v.thumbnail_path:
                        return self.project_path / v.thumbnail_path
                    return self.project_path / v.image_path

        return None
