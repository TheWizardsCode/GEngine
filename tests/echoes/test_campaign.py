"""Tests for campaign management module."""

from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from gengine.echoes.campaign import (
    Campaign,
    CampaignManager,
    CampaignSettings,
)


class TestCampaignSettings:
    """Tests for CampaignSettings."""

    def test_default_settings(self):
        settings = CampaignSettings()
        assert settings.campaigns_dir == Path("campaigns")
        assert settings.autosave_interval == 50
        assert settings.max_autosaves == 3
        assert settings.generate_postmortem_on_end is True

    def test_from_dict(self):
        data = {
            "campaigns_dir": "saves",
            "autosave_interval": 100,
            "max_autosaves": 5,
            "generate_postmortem_on_end": False,
        }
        settings = CampaignSettings.from_dict(data)
        assert settings.campaigns_dir == Path("saves")
        assert settings.autosave_interval == 100
        assert settings.max_autosaves == 5
        assert settings.generate_postmortem_on_end is False


class TestCampaign:
    """Tests for Campaign model."""

    def test_campaign_to_dict(self):
        now = datetime.now(timezone.utc)
        campaign = Campaign(
            id="test123",
            name="Test Campaign",
            world="default",
            created_at=now,
            last_saved=now,
            last_tick=42,
            ended=False,
            description="A test campaign",
        )
        result = campaign.to_dict()
        assert result["id"] == "test123"
        assert result["name"] == "Test Campaign"
        assert result["world"] == "default"
        assert result["last_tick"] == 42
        assert result["ended"] is False
        assert result["description"] == "A test campaign"

    def test_campaign_from_dict(self):
        data = {
            "id": "abc123",
            "name": "My Campaign",
            "world": "test-world",
            "created_at": "2024-01-01T12:00:00+00:00",
            "last_saved": "2024-01-01T12:30:00+00:00",
            "last_tick": 100,
            "ended": True,
            "description": "Finished campaign",
        }
        campaign = Campaign.from_dict(data)
        assert campaign.id == "abc123"
        assert campaign.name == "My Campaign"
        assert campaign.world == "test-world"
        assert campaign.last_tick == 100
        assert campaign.ended is True
        assert campaign.description == "Finished campaign"

    def test_campaign_from_dict_minimal(self):
        """Test with minimal data."""
        data = {"id": "min", "name": "Minimal"}
        campaign = Campaign.from_dict(data)
        assert campaign.id == "min"
        assert campaign.name == "Minimal"
        assert campaign.world == "default"
        assert campaign.last_tick == 0
        assert campaign.ended is False


class TestCampaignManager:
    """Tests for CampaignManager."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for campaign saves."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def manager(self, temp_dir):
        """Create a campaign manager with temporary directory."""
        settings = CampaignSettings(
            campaigns_dir=temp_dir,
            autosave_interval=10,
            max_autosaves=2,
        )
        return CampaignManager(settings)

    def test_create_campaign(self, manager):
        campaign = manager.create_campaign("Test Campaign", "default", "Test desc")
        assert campaign.name == "Test Campaign"
        assert campaign.world == "default"
        assert campaign.description == "Test desc"
        assert campaign.ended is False
        assert manager.active_campaign == campaign

    def test_list_campaigns_empty(self, manager):
        campaigns = manager.list_campaigns()
        assert campaigns == []

    def test_list_campaigns(self, manager):
        manager.create_campaign("First", "default")
        manager.create_campaign("Second", "default")
        campaigns = manager.list_campaigns()
        assert len(campaigns) == 2
        # Most recent first
        assert campaigns[0].name == "Second"
        assert campaigns[1].name == "First"

    def test_load_campaign(self, manager):
        created = manager.create_campaign("Test", "default")
        campaign_id = created.id
        # Clear active campaign
        manager._active_campaign = None

        loaded = manager.load_campaign(campaign_id)
        assert loaded.id == campaign_id
        assert loaded.name == "Test"
        assert manager.active_campaign == loaded

    def test_load_campaign_not_found(self, manager):
        with pytest.raises(FileNotFoundError):
            manager.load_campaign("nonexistent")

    def test_save_campaign(self, manager):
        manager.create_campaign("Test", "default")
        snapshot = {"tick": 10, "city": {"name": "Test City"}}

        path = manager.save_campaign(snapshot, 10)
        assert path.exists()
        assert manager.active_campaign.last_tick == 10

    def test_save_campaign_no_active(self, manager):
        with pytest.raises(ValueError, match="No active campaign"):
            manager.save_campaign({}, 0)

    def test_autosave_triggered(self, manager):
        manager.create_campaign("Test", "default")
        snapshot = {"tick": 15}

        # First autosave at tick 10+
        path = manager.check_autosave(snapshot, 15)
        assert path is not None
        assert "autosave" in path.name

    def test_autosave_not_triggered(self, manager):
        manager.create_campaign("Test", "default")
        snapshot = {"tick": 5}

        # Should not trigger - only 5 ticks since start (interval is 10)
        path = manager.check_autosave(snapshot, 5)
        assert path is None

    def test_autosave_cleanup(self, manager):
        manager.create_campaign("Test", "default")

        # Create multiple autosaves
        for i in range(5):
            tick = (i + 1) * 10
            manager._last_autosave_tick = tick - 10
            manager.check_autosave({"tick": tick}, tick)

        # Should only keep 2 autosaves (max_autosaves=2)
        autosaves = manager.list_autosaves()
        assert len(autosaves) <= 2

    def test_end_campaign(self, manager):
        manager.create_campaign("Test", "default")
        post_mortem = {"notes": ["Game ended well"]}
        snapshot = {"tick": 100}

        ended = manager.end_campaign(snapshot, 100, post_mortem)
        assert ended.name == "Test"
        assert ended.ended is True
        assert ended.last_tick == 100
        assert manager.active_campaign is None

        # Check post-mortem was saved
        pm_path = manager.get_postmortem_path(ended.id)
        assert pm_path.exists()

    def test_end_campaign_no_active(self, manager):
        with pytest.raises(ValueError, match="No active campaign"):
            manager.end_campaign({}, 0)

    def test_delete_campaign(self, manager):
        campaign = manager.create_campaign("ToDelete", "default")
        campaign_id = campaign.id

        assert manager.delete_campaign(campaign_id) is True
        assert manager.active_campaign is None

        # Should not be in list
        campaigns = manager.list_campaigns()
        assert all(c.id != campaign_id for c in campaigns)

    def test_delete_campaign_not_found(self, manager):
        assert manager.delete_campaign("nonexistent") is False

    def test_summary(self, manager):
        summary = manager.summary()
        assert "campaigns_dir" in summary
        assert "autosave_interval" in summary
        assert summary["active_campaign"] is None
        assert summary["total_campaigns"] == 0

    def test_summary_with_active(self, manager):
        manager.create_campaign("Active", "default")
        summary = manager.summary()
        assert summary["active_campaign"] is not None
        assert summary["active_campaign"]["name"] == "Active"


class TestCampaignIntegration:
    """Integration tests for campaign with shell backend."""

    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_campaign_workflow(self, temp_dir):
        """Test complete campaign workflow."""
        from gengine.echoes.sim import SimEngine
        from gengine.echoes.cli.shell import LocalBackend

        settings = CampaignSettings(
            campaigns_dir=temp_dir,
            autosave_interval=10,
        )
        manager = CampaignManager(settings)
        engine = SimEngine()
        engine.initialize_state(world="default")
        backend = LocalBackend(engine, manager)

        # Create new campaign
        result = backend.campaign_new("Integration Test", "default")
        assert "error" not in result
        campaign_id = result["id"]

        # Advance simulation
        backend.advance_ticks(15)

        # Check status
        status = backend.campaign_status()
        assert status["active_campaign"]["id"] == campaign_id

        # List campaigns
        campaigns = backend.campaign_list()
        assert len(campaigns) == 1
        assert campaigns[0]["id"] == campaign_id

        # End campaign
        end_result = backend.campaign_end()
        assert "ended" in end_result
        assert end_result["ended"]["id"] == campaign_id

        # Resume ended campaign
        resume_result = backend.campaign_resume(campaign_id)
        assert "error" not in resume_result

    def test_campaign_autosave_on_advance(self, temp_dir):
        """Test that autosave happens when advancing ticks."""
        from gengine.echoes.sim import SimEngine
        from gengine.echoes.cli.shell import LocalBackend

        settings = CampaignSettings(
            campaigns_dir=temp_dir,
            autosave_interval=5,
        )
        manager = CampaignManager(settings)
        engine = SimEngine()
        engine.initialize_state(world="default")
        backend = LocalBackend(engine, manager)

        # Create campaign
        backend.campaign_new("Autosave Test", "default")

        # Advance past autosave interval
        backend.advance_ticks(10)

        # Check autosaves were created
        autosaves = manager.list_autosaves()
        assert len(autosaves) >= 1
