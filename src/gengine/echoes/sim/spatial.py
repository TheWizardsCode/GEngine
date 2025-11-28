"""Shared spatial helper utilities for Echoes simulation features."""

from __future__ import annotations

from ..core.models import DistrictCoordinates


def euclidean_distance(
    point_a: DistrictCoordinates | None,
    point_b: DistrictCoordinates | None,
) -> float | None:
    """Return the Euclidean distance between two coordinate triplets.

    Returns ``None`` when either coordinate is missing so callers can decide on a
    fallback distance (for example, a tuned constant in settings).
    """

    if point_a is None or point_b is None:
        return None
    ax, ay, az = point_a.x, point_a.y, point_a.z or 0.0
    bx, by, bz = point_b.x, point_b.y, point_b.z or 0.0
    dx = ax - bx
    dy = ay - by
    dz = az - bz
    return (dx * dx + dy * dy + dz * dz) ** 0.5


__all__ = ["euclidean_distance"]
