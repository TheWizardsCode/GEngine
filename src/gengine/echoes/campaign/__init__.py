"""Campaign management for Echoes of Emergence.

This module provides campaign session management including:
- Campaign creation and metadata tracking
- Autosave functionality at configurable intervals
- Campaign listing and resumption
- End-of-campaign flow with post-mortem integration
"""

from .manager import (
    Campaign,
    CampaignManager,
    CampaignSettings,
)

__all__ = [
    "Campaign",
    "CampaignManager",
    "CampaignSettings",
]
