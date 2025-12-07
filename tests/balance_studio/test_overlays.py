import pytest
import yaml
from pathlib import Path
from gengine.balance_studio.overlays import (
    ConfigOverlay,
    create_tuning_overlay,
    deep_merge,
    load_overlay_directory,
    merge_overlays,
)


def test_config_overlay_from_yaml(tmp_path):
    """Test loading overlay from YAML."""
    overlay_path = tmp_path / "test.yml"
    data = {
        "name": "test",
        "description": "desc",
        "overrides": {"a": 1},
        "metadata": {"m": 2}
    }
    with open(overlay_path, "w") as f:
        yaml.dump(data, f)
        
    overlay = ConfigOverlay.from_yaml(overlay_path)
    
    assert overlay.name == "test"
    assert overlay.description == "desc"
    assert overlay.overrides == {"a": 1}
    assert overlay.metadata == {"m": 2}
    assert overlay.source_path == overlay_path


def test_config_overlay_from_yaml_not_found(tmp_path):
    """Test loading non-existent overlay."""
    with pytest.raises(FileNotFoundError):
        ConfigOverlay.from_yaml(tmp_path / "non_existent.yml")


def test_config_overlay_from_yaml_invalid(tmp_path):
    """Test loading invalid overlay."""
    overlay_path = tmp_path / "invalid.yml"
    with open(overlay_path, "w") as f:
        f.write("not a dict")
        
    with pytest.raises(ValueError):
        ConfigOverlay.from_yaml(overlay_path)


def test_config_overlay_from_dict():
    """Test creating overlay from dict."""
    data = {"overrides": {"a": 1}, "name": "test"}
    overlay = ConfigOverlay.from_dict(data)
    
    assert overlay.name == "test"
    assert overlay.overrides == data["overrides"]
    
    data2 = {"a": 1}
    overlay2 = ConfigOverlay.from_dict(data2, name="custom")
    assert overlay2.name == "custom"
    assert overlay2.overrides == data2


def test_apply_overlay():
    """Test applying overlay to config."""
    base = {"a": 1, "b": {"c": 2}}
    overlay = ConfigOverlay(name="test", overrides={"a": 2, "b": {"d": 3}})
    
    merged = overlay.apply(base)
    
    assert merged["a"] == 2
    assert merged["b"]["c"] == 2
    assert merged["b"]["d"] == 3


def test_to_dict():
    """Test serializing overlay to dict."""
    overlay = ConfigOverlay(name="test", overrides={"a": 1})
    data = overlay.to_dict()
    
    assert data["name"] == "test"
    assert data["overrides"] == {"a": 1}


def test_to_yaml(tmp_path):
    """Test writing overlay to YAML."""
    overlay = ConfigOverlay(name="test", overrides={"a": 1})
    path = tmp_path / "out.yml"
    
    overlay.to_yaml(path)
    
    with open(path) as f:
        data = yaml.safe_load(f)
        
    assert data["name"] == "test"
    assert data["overrides"] == {"a": 1}


def test_deep_merge():
    """Test deep merge utility."""
    base = {"a": 1, "b": {"c": 2}}
    override = {"b": {"c": 3, "d": 4}, "e": 5}
    
    merged = deep_merge(base, override)
    
    assert merged["a"] == 1
    assert merged["b"]["c"] == 3
    assert merged["b"]["d"] == 4
    assert merged["e"] == 5


def test_load_overlay_directory(tmp_path):
    """Test loading overlays from directory."""
    d = tmp_path / "overlays"
    d.mkdir()
    
    # Valid yaml
    with open(d / "1.yml", "w") as f:
        yaml.dump({"name": "1"}, f)
        
    # Valid yaml extension
    with open(d / "2.yaml", "w") as f:
        yaml.dump({"name": "2"}, f)
        
    # Invalid yaml
    with open(d / "3.yml", "w") as f:
        f.write(":")
        
    overlays = load_overlay_directory(d)
    
    assert len(overlays) == 2
    names = sorted([o.name for o in overlays])
    assert names == ["1", "2"]


def test_load_overlay_directory_not_exists(tmp_path):
    """Test loading from non-existent directory."""
    assert load_overlay_directory(tmp_path / "non_existent") == []


def test_merge_overlays():
    """Test merging multiple overlays."""
    o1 = ConfigOverlay(name="o1", overrides={"a": 1, "b": 1})
    o2 = ConfigOverlay(name="o2", overrides={"b": 2, "c": 3})
    
    merged = merge_overlays([o1, o2])
    
    assert merged.name == "o1 + o2"
    assert merged.overrides["a"] == 1
    assert merged.overrides["b"] == 2
    assert merged.overrides["c"] == 3


def test_merge_overlays_empty():
    """Test merging empty list of overlays."""
    merged = merge_overlays([])
    assert merged.name == "empty"
    assert merged.overrides == {}
