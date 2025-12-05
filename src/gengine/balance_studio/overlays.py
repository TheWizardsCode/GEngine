"""YAML overlay system for configuration testing.

Allows designers to create configuration overlays that are merged with base
configs, enabling testing of tuning changes without modifying base files.

Examples
--------
Create and apply an overlay::

    overlay = ConfigOverlay.from_yaml(Path("my_overlay.yml"))
    merged_config = overlay.apply(base_config)

Load overlay directory::

    overlays = load_overlay_directory(Path("content/config/overlays"))
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class ConfigOverlay:
    """A configuration overlay that can be merged with base configs.

    Attributes
    ----------
    name
        Name of the overlay for display purposes.
    description
        Human-readable description of what this overlay changes.
    source_path
        Path to the source YAML file.
    overrides
        Dictionary of config keys to override values.
    metadata
        Additional metadata about the overlay.
    """

    name: str
    description: str = ""
    source_path: Path | None = None
    overrides: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_yaml(cls, path: Path) -> ConfigOverlay:
        """Load an overlay from a YAML file.

        Parameters
        ----------
        path
            Path to the YAML overlay file.

        Returns
        -------
        ConfigOverlay
            Loaded overlay.

        Raises
        ------
        FileNotFoundError
            If the file does not exist.
        ValueError
            If the file is not valid YAML or missing required fields.
        """
        if not path.exists():
            raise FileNotFoundError(f"Overlay file not found: {path}")

        with open(path) as f:
            data = yaml.safe_load(f) or {}

        if not isinstance(data, dict):
            raise ValueError(f"Invalid overlay format in {path}: expected dict")

        return cls(
            name=data.get("name", path.stem),
            description=data.get("description", ""),
            source_path=path,
            overrides=data.get("overrides", {}),
            metadata=data.get("metadata", {}),
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any], name: str = "inline") -> ConfigOverlay:
        """Create an overlay from a dictionary.

        Parameters
        ----------
        data
            Dictionary with overlay structure.
        name
            Name for the overlay.

        Returns
        -------
        ConfigOverlay
            Created overlay.
        """
        return cls(
            name=data.get("name", name),
            description=data.get("description", ""),
            overrides=data.get("overrides", data),
            metadata=data.get("metadata", {}),
        )

    def apply(self, base_config: dict[str, Any]) -> dict[str, Any]:
        """Apply this overlay to a base configuration.

        Performs a deep merge where overlay values override base values.

        Parameters
        ----------
        base_config
            Base configuration dictionary.

        Returns
        -------
        dict[str, Any]
            Merged configuration with overlays applied.
        """
        return deep_merge(base_config, self.overrides)

    def to_dict(self) -> dict[str, Any]:
        """Serialize overlay to dictionary.

        Returns
        -------
        dict[str, Any]
            Serialized overlay.
        """
        return {
            "name": self.name,
            "description": self.description,
            "source_path": str(self.source_path) if self.source_path else None,
            "overrides": self.overrides,
            "metadata": self.metadata,
        }

    def to_yaml(self, path: Path) -> None:
        """Write overlay to a YAML file.

        Parameters
        ----------
        path
            Path to write the overlay file.
        """
        data = {
            "name": self.name,
            "description": self.description,
            "overrides": self.overrides,
            "metadata": self.metadata,
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Deep merge two dictionaries, with override taking precedence.

    Parameters
    ----------
    base
        Base dictionary.
    override
        Override dictionary with values to merge.

    Returns
    -------
    dict[str, Any]
        Merged dictionary.
    """
    result = copy.deepcopy(base)

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)

    return result


def load_overlay_directory(directory: Path) -> list[ConfigOverlay]:
    """Load all overlays from a directory.

    Parameters
    ----------
    directory
        Directory containing overlay YAML files.

    Returns
    -------
    list[ConfigOverlay]
        List of loaded overlays.
    """
    if not directory.exists():
        return []

    overlays: list[ConfigOverlay] = []

    for path in sorted(directory.glob("*.yml")):
        try:
            overlays.append(ConfigOverlay.from_yaml(path))
        except (ValueError, yaml.YAMLError):
            continue

    for path in sorted(directory.glob("*.yaml")):
        try:
            overlays.append(ConfigOverlay.from_yaml(path))
        except (ValueError, yaml.YAMLError):
            continue

    return overlays


def create_tuning_overlay(
    name: str,
    changes: dict[str, Any],
    description: str = "",
) -> ConfigOverlay:
    """Create a tuning overlay from a dictionary of changes.

    This is a convenience function for quick experimentation.

    Parameters
    ----------
    name
        Name for the overlay.
    changes
        Dictionary of configuration changes to apply.
    description
        Optional description of the changes.

    Returns
    -------
    ConfigOverlay
        Created overlay.

    Examples
    --------
    >>> overlay = create_tuning_overlay(
    ...     "aggressive_economy",
    ...     {"economy": {"regen_scale": 1.2}},
    ...     "Test higher resource regeneration"
    ... )
    """
    return ConfigOverlay(
        name=name,
        description=description,
        overrides=changes,
        metadata={"type": "tuning_experiment"},
    )


def merge_overlays(overlays: list[ConfigOverlay]) -> ConfigOverlay:
    """Merge multiple overlays into a single overlay.

    Overlays are applied in order, with later overlays taking precedence.

    Parameters
    ----------
    overlays
        List of overlays to merge.

    Returns
    -------
    ConfigOverlay
        Merged overlay.
    """
    if not overlays:
        return ConfigOverlay(name="empty")

    merged_overrides: dict[str, Any] = {}
    names: list[str] = []

    for overlay in overlays:
        merged_overrides = deep_merge(merged_overrides, overlay.overrides)
        names.append(overlay.name)

    return ConfigOverlay(
        name=" + ".join(names),
        description=f"Merged from: {', '.join(names)}",
        overrides=merged_overrides,
        metadata={"merged_from": names},
    )
