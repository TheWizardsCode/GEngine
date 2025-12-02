"""Campaign manager for tracking and persisting campaign sessions.

Provides campaign lifecycle management:
- Create new campaigns with unique IDs
- Track campaign metadata (name, world, created_at, last_saved)
- Autosave at configurable tick intervals
- List and resume existing campaigns
- End campaigns with post-mortem generation
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def _json_default(value: Any) -> Any:
    """JSON encoder for datetime objects."""
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


@dataclass
class CampaignSettings:
    """Configuration for campaign management."""

    # Directory to store campaign saves
    campaigns_dir: Path = field(default_factory=lambda: Path("campaigns"))

    # Autosave interval in ticks (0 = disabled)
    autosave_interval: int = 50

    # Maximum number of autosaves to keep per campaign
    max_autosaves: int = 3

    # Whether to auto-generate post-mortem on campaign end
    generate_postmortem_on_end: bool = True

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CampaignSettings":
        """Create settings from a dictionary (e.g., from config file)."""
        return cls(
            campaigns_dir=Path(data.get("campaigns_dir", "campaigns")),
            autosave_interval=int(data.get("autosave_interval", 50)),
            max_autosaves=int(data.get("max_autosaves", 3)),
            generate_postmortem_on_end=bool(
                data.get("generate_postmortem_on_end", True)
            ),
        )


@dataclass
class Campaign:
    """Represents a campaign session with its metadata."""

    # Unique campaign identifier
    id: str

    # Human-readable campaign name
    name: str

    # World name used for this campaign
    world: str

    # When the campaign was created
    created_at: datetime

    # When the campaign was last saved
    last_saved: Optional[datetime] = None

    # Last tick count at save time
    last_tick: int = 0

    # Whether this campaign has ended
    ended: bool = False

    # Optional description or notes
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize campaign metadata to a dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "world": self.world,
            "created_at": self.created_at.isoformat(),
            "last_saved": self.last_saved.isoformat() if self.last_saved else None,
            "last_tick": self.last_tick,
            "ended": self.ended,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Campaign":
        """Deserialize campaign metadata from a dictionary."""
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif created_at is None:
            created_at = datetime.now(timezone.utc)

        last_saved = data.get("last_saved")
        if isinstance(last_saved, str):
            last_saved = datetime.fromisoformat(last_saved)

        return cls(
            id=str(data.get("id", "")),
            name=str(data.get("name", "Untitled")),
            world=str(data.get("world", "default")),
            created_at=created_at,
            last_saved=last_saved,
            last_tick=int(data.get("last_tick", 0)),
            ended=bool(data.get("ended", False)),
            description=str(data.get("description", "")),
        )


class CampaignManager:
    """Manages campaign lifecycle and persistence."""

    METADATA_FILENAME = "campaign.json"
    SNAPSHOT_FILENAME = "snapshot.json"
    AUTOSAVE_PREFIX = "autosave_"
    POSTMORTEM_FILENAME = "postmortem.json"

    def __init__(self, settings: Optional[CampaignSettings] = None) -> None:
        self._settings = settings or CampaignSettings()
        self._active_campaign: Optional[Campaign] = None
        self._last_autosave_tick: int = 0

    @property
    def settings(self) -> CampaignSettings:
        return self._settings

    @property
    def active_campaign(self) -> Optional[Campaign]:
        return self._active_campaign

    @property
    def campaigns_dir(self) -> Path:
        return self._settings.campaigns_dir

    def _ensure_campaigns_dir(self) -> None:
        """Create campaigns directory if it doesn't exist."""
        self._settings.campaigns_dir.mkdir(parents=True, exist_ok=True)

    def _campaign_dir(self, campaign_id: str) -> Path:
        """Get the directory for a specific campaign."""
        return self._settings.campaigns_dir / campaign_id

    def create_campaign(
        self,
        name: str,
        world: str = "default",
        description: str = "",
    ) -> Campaign:
        """Create a new campaign session.

        Args:
            name: Human-readable campaign name
            world: World name to load
            description: Optional campaign description

        Returns:
            The newly created Campaign
        """
        self._ensure_campaigns_dir()

        campaign_id = str(uuid.uuid4())[:12]  # Use 12 chars for reduced collision risk
        now = datetime.now(timezone.utc)

        campaign = Campaign(
            id=campaign_id,
            name=name,
            world=world,
            created_at=now,
            last_saved=now,
            last_tick=0,
            ended=False,
            description=description,
        )

        # Create campaign directory and save metadata
        campaign_dir = self._campaign_dir(campaign_id)
        campaign_dir.mkdir(parents=True, exist_ok=True)

        metadata_path = campaign_dir / self.METADATA_FILENAME
        metadata_path.write_text(
            json.dumps(campaign.to_dict(), indent=2, default=_json_default),
            encoding="utf-8",
        )

        self._active_campaign = campaign
        self._last_autosave_tick = 0
        return campaign

    def list_campaigns(self) -> List[Campaign]:
        """List all saved campaigns.

        Returns:
            List of Campaign objects sorted by last_saved (most recent first)
        """
        campaigns: List[Campaign] = []

        if not self._settings.campaigns_dir.exists():
            return campaigns

        for entry in self._settings.campaigns_dir.iterdir():
            if not entry.is_dir():
                continue
            metadata_path = entry / self.METADATA_FILENAME
            if not metadata_path.exists():
                continue
            try:
                data = json.loads(metadata_path.read_text(encoding="utf-8"))
                campaign = Campaign.from_dict(data)
                campaigns.append(campaign)
            except (json.JSONDecodeError, KeyError, ValueError):
                # Skip malformed campaign data
                continue

        # Sort by last_saved, most recent first
        campaigns.sort(
            key=lambda c: c.last_saved or c.created_at,
            reverse=True,
        )
        return campaigns

    def load_campaign(self, campaign_id: str) -> Campaign:
        """Load an existing campaign by ID.

        Args:
            campaign_id: The campaign ID to load

        Returns:
            The loaded Campaign

        Raises:
            FileNotFoundError: If campaign doesn't exist
            ValueError: If campaign data is invalid
        """
        campaign_dir = self._campaign_dir(campaign_id)
        metadata_path = campaign_dir / self.METADATA_FILENAME

        if not metadata_path.exists():
            raise FileNotFoundError(f"Campaign '{campaign_id}' not found")

        try:
            data = json.loads(metadata_path.read_text(encoding="utf-8"))
            campaign = Campaign.from_dict(data)
        except (json.JSONDecodeError, KeyError) as exc:
            raise ValueError(f"Invalid campaign data: {exc}") from exc

        self._active_campaign = campaign
        self._last_autosave_tick = campaign.last_tick
        return campaign

    def get_snapshot_path(self, campaign_id: Optional[str] = None) -> Path:
        """Get the path to the main snapshot for a campaign.

        Args:
            campaign_id: Campaign ID, or None for active campaign

        Returns:
            Path to the snapshot file

        Raises:
            ValueError: If no campaign is active and no ID provided
        """
        if campaign_id is None:
            if self._active_campaign is None:
                raise ValueError("No active campaign")
            campaign_id = self._active_campaign.id

        return self._campaign_dir(campaign_id) / self.SNAPSHOT_FILENAME

    def save_campaign(
        self,
        state_snapshot: Dict[str, Any],
        tick: int,
    ) -> Path:
        """Save the current campaign state.

        Args:
            state_snapshot: GameState.snapshot() output
            tick: Current tick count

        Returns:
            Path to the saved snapshot

        Raises:
            ValueError: If no campaign is active
        """
        if self._active_campaign is None:
            raise ValueError("No active campaign")

        campaign_dir = self._campaign_dir(self._active_campaign.id)
        campaign_dir.mkdir(parents=True, exist_ok=True)

        # Update campaign metadata
        now = datetime.now(timezone.utc)
        self._active_campaign.last_saved = now
        self._active_campaign.last_tick = tick

        # Save metadata
        metadata_path = campaign_dir / self.METADATA_FILENAME
        metadata_path.write_text(
            json.dumps(
                self._active_campaign.to_dict(), indent=2, default=_json_default
            ),
            encoding="utf-8",
        )

        # Save snapshot
        snapshot_path = campaign_dir / self.SNAPSHOT_FILENAME
        snapshot_path.write_text(
            json.dumps(state_snapshot, indent=2, default=_json_default),
            encoding="utf-8",
        )

        return snapshot_path

    def check_autosave(
        self,
        state_snapshot: Dict[str, Any],
        tick: int,
    ) -> Optional[Path]:
        """Check if autosave is due and save if needed.

        Args:
            state_snapshot: GameState.snapshot() output
            tick: Current tick count

        Returns:
            Path to autosave if one was created, None otherwise
        """
        if self._active_campaign is None:
            return None

        if self._settings.autosave_interval <= 0:
            return None

        ticks_since_save = tick - self._last_autosave_tick
        if ticks_since_save < self._settings.autosave_interval:
            return None

        # Time for autosave
        campaign_dir = self._campaign_dir(self._active_campaign.id)
        campaign_dir.mkdir(parents=True, exist_ok=True)

        # Create autosave with timestamp including microseconds to avoid collisions
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
        autosave_name = f"{self.AUTOSAVE_PREFIX}{timestamp}_tick{tick}.json"
        autosave_path = campaign_dir / autosave_name

        autosave_path.write_text(
            json.dumps(state_snapshot, indent=2, default=_json_default),
            encoding="utf-8",
        )

        self._last_autosave_tick = tick

        # Also update main snapshot
        self.save_campaign(state_snapshot, tick)

        # Cleanup old autosaves
        self._cleanup_autosaves(campaign_dir)

        return autosave_path

    def _cleanup_autosaves(self, campaign_dir: Path) -> None:
        """Remove old autosaves beyond the max limit."""
        autosaves = sorted(
            [
                f
                for f in campaign_dir.iterdir()
                if f.name.startswith(self.AUTOSAVE_PREFIX)
            ],
            key=lambda f: f.stat().st_mtime,
            reverse=True,
        )

        # Keep only the most recent autosaves
        for old_save in autosaves[self._settings.max_autosaves :]:
            old_save.unlink()

    def list_autosaves(self, campaign_id: Optional[str] = None) -> List[Path]:
        """List autosave files for a campaign.

        Args:
            campaign_id: Campaign ID, or None for active campaign

        Returns:
            List of autosave paths, most recent first
        """
        if campaign_id is None:
            if self._active_campaign is None:
                return []
            campaign_id = self._active_campaign.id

        campaign_dir = self._campaign_dir(campaign_id)
        if not campaign_dir.exists():
            return []

        autosaves = sorted(
            [
                f
                for f in campaign_dir.iterdir()
                if f.name.startswith(self.AUTOSAVE_PREFIX)
            ],
            key=lambda f: f.stat().st_mtime,
            reverse=True,
        )
        return autosaves

    def end_campaign(
        self,
        state_snapshot: Dict[str, Any],
        tick: int,
        post_mortem: Optional[Dict[str, Any]] = None,
    ) -> Campaign:
        """End the active campaign and generate final saves.

        Args:
            state_snapshot: Final GameState.snapshot() output
            tick: Final tick count
            post_mortem: Optional post-mortem data to save

        Returns:
            The ended Campaign

        Raises:
            ValueError: If no campaign is active
        """
        if self._active_campaign is None:
            raise ValueError("No active campaign")

        campaign_dir = self._campaign_dir(self._active_campaign.id)
        campaign_dir.mkdir(parents=True, exist_ok=True)

        # Mark campaign as ended
        self._active_campaign.ended = True
        self._active_campaign.last_tick = tick
        self._active_campaign.last_saved = datetime.now(timezone.utc)

        # Save final snapshot
        self.save_campaign(state_snapshot, tick)

        # Save post-mortem if provided and setting enabled
        if post_mortem and self._settings.generate_postmortem_on_end:
            postmortem_path = campaign_dir / self.POSTMORTEM_FILENAME
            postmortem_path.write_text(
                json.dumps(post_mortem, indent=2, default=_json_default),
                encoding="utf-8",
            )

        # Update metadata
        metadata_path = campaign_dir / self.METADATA_FILENAME
        metadata_path.write_text(
            json.dumps(
                self._active_campaign.to_dict(), indent=2, default=_json_default
            ),
            encoding="utf-8",
        )

        ended_campaign = self._active_campaign
        self._active_campaign = None
        self._last_autosave_tick = 0

        return ended_campaign

    def delete_campaign(self, campaign_id: str) -> bool:
        """Delete a campaign and all its saves.

        Args:
            campaign_id: The campaign ID to delete

        Returns:
            True if deleted, False if not found
        """
        campaign_dir = self._campaign_dir(campaign_id)
        if not campaign_dir.exists():
            return False

        # Remove all files in campaign directory
        for f in campaign_dir.iterdir():
            f.unlink()
        campaign_dir.rmdir()

        # Clear active campaign if it was deleted
        if self._active_campaign and self._active_campaign.id == campaign_id:
            self._active_campaign = None
            self._last_autosave_tick = 0

        return True

    def get_postmortem_path(self, campaign_id: Optional[str] = None) -> Path:
        """Get the path to the post-mortem file for a campaign.

        Args:
            campaign_id: Campaign ID, or None for active campaign

        Returns:
            Path to the post-mortem file
        """
        if campaign_id is None:
            if self._active_campaign is None:
                raise ValueError("No active campaign")
            campaign_id = self._active_campaign.id

        return self._campaign_dir(campaign_id) / self.POSTMORTEM_FILENAME

    def summary(self) -> Dict[str, Any]:
        """Return a summary of campaign manager state."""
        active = None
        if self._active_campaign:
            active = {
                "id": self._active_campaign.id,
                "name": self._active_campaign.name,
                "world": self._active_campaign.world,
                "tick": self._active_campaign.last_tick,
            }

        return {
            "campaigns_dir": str(self._settings.campaigns_dir),
            "autosave_interval": self._settings.autosave_interval,
            "active_campaign": active,
            "total_campaigns": len(self.list_campaigns()),
        }
