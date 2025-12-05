"""Tests for the environment trajectories plotting script."""

from __future__ import annotations

import json
import sys
from importlib import util
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_MODULE_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "plot_environment_trajectories.py"
)


def _load_plot_module():
    spec = util.spec_from_file_location("plot_environment_trajectories", _MODULE_PATH)
    module = util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules.setdefault("plot_environment_trajectories", module)
    spec.loader.exec_module(module)
    return module


_mod = _load_plot_module()
parse_args = _mod.parse_args
main = _mod.main
_collect_runs = _mod._collect_runs
_parse_run_spec = _mod._parse_run_spec
_extract_series = _mod._extract_series
DEFAULT_RUNS = _mod.DEFAULT_RUNS


class TestParseArgs:
    """Tests for the parse_args function."""

    def test_default_values(self) -> None:
        """Test that parse_args returns expected defaults."""
        args = parse_args([])
        assert args.run is None
        assert args.output is None
        assert args.title == "Environment trajectories"

    def test_single_run_argument(self) -> None:
        """Test parsing a single --run argument."""
        args = parse_args(["--run", "test=path/to/file.json"])
        assert args.run == ["test=path/to/file.json"]

    def test_multiple_run_arguments(self) -> None:
        """Test parsing multiple --run arguments."""
        args = parse_args([
            "--run", "run1=path1.json",
            "--run", "run2=path2.json",
            "--run", "run3=path3.json",
        ])
        assert args.run == ["run1=path1.json", "run2=path2.json", "run3=path3.json"]

    def test_output_argument(self) -> None:
        """Test parsing --output argument."""
        args = parse_args(["--output", "/tmp/plot.png"])
        assert args.output == Path("/tmp/plot.png")

    def test_title_argument(self) -> None:
        """Test parsing --title argument."""
        args = parse_args(["--title", "Custom Title"])
        assert args.title == "Custom Title"

    def test_combined_arguments(self) -> None:
        """Test parsing multiple arguments together."""
        args = parse_args([
            "--run", "test=file.json",
            "--output", "out.png",
            "--title", "My Plot",
        ])
        assert args.run == ["test=file.json"]
        assert args.output == Path("out.png")
        assert args.title == "My Plot"


class TestParseRunSpec:
    """Tests for the _parse_run_spec helper function."""

    def test_label_equals_path_format(self) -> None:
        """Test parsing 'label=path' format."""
        label, path = _parse_run_spec("cushioned=build/test.json")
        assert label == "cushioned"
        assert path == Path("build/test.json")

    def test_path_only_format(self) -> None:
        """Test parsing path-only format (uses stem as label)."""
        label, path = _parse_run_spec("build/test-results.json")
        assert label == "test-results"
        assert path == Path("build/test-results.json")

    def test_label_with_spaces(self) -> None:
        """Test parsing label with spaces around equals sign."""
        label, path = _parse_run_spec(" my-label = path/to/file.json ")
        assert label == "my-label"
        assert path == Path("path/to/file.json")

    def test_path_with_multiple_equals(self) -> None:
        """Test parsing spec with multiple equals signs."""
        label, path = _parse_run_spec("label=path/with=equals.json")
        assert label == "label"
        assert path == Path("path/with=equals.json")


class TestCollectRuns:
    """Tests for the _collect_runs function."""

    def test_collect_from_run_args(self, tmp_path: Path) -> None:
        """Test collecting runs from explicit run arguments."""
        runs = _collect_runs(["label1=path1.json", "label2=path2.json"])
        assert "label1" in runs
        assert "label2" in runs
        assert runs["label1"] == Path("path1.json")
        assert runs["label2"] == Path("path2.json")

    def test_collect_empty_when_no_args_and_no_defaults(self) -> None:
        """Test that empty dict returned when no args and defaults don't exist."""
        with patch.dict(_mod.__dict__, {"DEFAULT_RUNS": {}}):
            runs = _collect_runs(None)
            assert runs == {}

    def test_collect_defaults_when_exist(self, tmp_path: Path) -> None:
        """Test that defaults are collected when they exist."""
        test_file = tmp_path / "test.json"
        test_file.write_text("{}")

        # Temporarily modify DEFAULT_RUNS for this test
        original_defaults = dict(DEFAULT_RUNS)
        DEFAULT_RUNS.clear()
        DEFAULT_RUNS["test"] = test_file

        try:
            runs = _collect_runs(None)
            assert "test" in runs
            assert runs["test"] == test_file
        finally:
            DEFAULT_RUNS.clear()
            DEFAULT_RUNS.update(original_defaults)

    def test_collect_skips_nonexistent_defaults(self) -> None:
        """Test that nonexistent default files are skipped."""
        original_defaults = dict(DEFAULT_RUNS)
        DEFAULT_RUNS.clear()
        DEFAULT_RUNS["nonexistent"] = Path("/nonexistent/path.json")

        try:
            runs = _collect_runs(None)
            assert "nonexistent" not in runs
        finally:
            DEFAULT_RUNS.clear()
            DEFAULT_RUNS.update(original_defaults)


class TestExtractSeries:
    """Tests for the _extract_series function."""

    def test_extract_from_director_history(self, tmp_path: Path) -> None:
        """Test extracting series from director_history format."""
        data = {
            "director_history": [
                {"tick": 0, "environment": {"pollution": 0.1, "unrest": 0.2}},
                {"tick": 10, "environment": {"pollution": 0.15, "unrest": 0.25}},
                {"tick": 20, "environment": {"pollution": 0.2, "unrest": 0.3}},
            ]
        }
        test_file = tmp_path / "test.json"
        test_file.write_text(json.dumps(data))

        ticks, pollution, unrest = _extract_series(test_file)

        assert ticks == [0, 10, 20]
        assert pollution == [0.1, 0.15, 0.2]
        assert unrest == [0.2, 0.25, 0.3]

    def test_extract_fallback_to_last_environment(self, tmp_path: Path) -> None:
        """Test fallback to last_environment when no director_history."""
        data = {
            "end_tick": 100,
            "last_environment": {
                "pollution": 0.5,
                "unrest": 0.6,
            },
        }
        test_file = tmp_path / "test.json"
        test_file.write_text(json.dumps(data))

        ticks, pollution, unrest = _extract_series(test_file)

        assert ticks == [100]
        assert pollution == [0.5]
        assert unrest == [0.6]

    def test_extract_empty_when_no_data(self, tmp_path: Path) -> None:
        """Test that empty lists returned when no relevant data."""
        data = {"other_field": "value"}
        test_file = tmp_path / "test.json"
        test_file.write_text(json.dumps(data))

        ticks, pollution, unrest = _extract_series(test_file)

        assert ticks == []
        assert pollution == []
        assert unrest == []

    def test_extract_handles_missing_environment(self, tmp_path: Path) -> None:
        """Test handling entries missing environment data."""
        data = {
            "director_history": [
                {"tick": 0, "environment": {"pollution": 0.1, "unrest": 0.2}},
                {"tick": 10},  # Missing environment
                {"tick": 20, "environment": {"pollution": 0.3, "unrest": 0.4}},
            ]
        }
        test_file = tmp_path / "test.json"
        test_file.write_text(json.dumps(data))

        ticks, pollution, unrest = _extract_series(test_file)

        # Should skip entries without environment
        assert ticks == [0, 20]
        assert pollution == [0.1, 0.3]
        assert unrest == [0.2, 0.4]

    def test_extract_sorts_by_tick(self, tmp_path: Path) -> None:
        """Test that entries are sorted by tick."""
        data = {
            "director_history": [
                {"tick": 20, "environment": {"pollution": 0.3, "unrest": 0.4}},
                {"tick": 0, "environment": {"pollution": 0.1, "unrest": 0.2}},
                {"tick": 10, "environment": {"pollution": 0.2, "unrest": 0.3}},
            ]
        }
        test_file = tmp_path / "test.json"
        test_file.write_text(json.dumps(data))

        ticks, pollution, unrest = _extract_series(test_file)

        assert ticks == [0, 10, 20]
        assert pollution == [0.1, 0.2, 0.3]
        assert unrest == [0.2, 0.3, 0.4]

    def test_extract_default_values(self, tmp_path: Path) -> None:
        """Test that missing pollution/unrest default to 0.0."""
        data = {
            "director_history": [
                {"tick": 0, "environment": {"pollution": 0.0}},  # Missing unrest
            ]
        }
        test_file = tmp_path / "test.json"
        test_file.write_text(json.dumps(data))

        ticks, pollution, unrest = _extract_series(test_file)

        assert ticks == [0]
        assert pollution == [0.0]
        assert unrest == [0.0]  # Should default to 0.0


class TestMainFunction:
    """Tests for the main function."""

    def test_main_exits_when_no_files_found(self) -> None:
        """Test that main exits with error when no files found."""
        with patch.dict(_mod.__dict__, {"DEFAULT_RUNS": {}}):
            with pytest.raises(SystemExit) as exc_info:
                main([])
            assert exc_info.value.code is not None

    @patch("matplotlib.pyplot.show")
    @patch("matplotlib.pyplot.subplots")
    def test_main_creates_plot_with_run_args(
        self, mock_subplots: MagicMock, mock_show: MagicMock, tmp_path: Path
    ) -> None:
        """Test that main creates a plot when run arguments provided."""
        # Create test data file
        data = {
            "director_history": [
                {"tick": 0, "environment": {"pollution": 0.1, "unrest": 0.2}},
                {"tick": 10, "environment": {"pollution": 0.2, "unrest": 0.3}},
            ]
        }
        test_file = tmp_path / "test.json"
        test_file.write_text(json.dumps(data))

        # Set up mocks
        mock_fig = MagicMock()
        mock_ax_pollution = MagicMock()
        mock_ax_unrest = MagicMock()
        mock_subplots.return_value = (mock_fig, (mock_ax_pollution, mock_ax_unrest))

        result = main(["--run", f"test={test_file}"])

        assert result == 0
        mock_subplots.assert_called_once()
        mock_show.assert_called_once()

    @patch("matplotlib.pyplot.subplots")
    def test_main_saves_to_output_file(
        self, mock_subplots: MagicMock, tmp_path: Path
    ) -> None:
        """Test that main saves plot to output file when specified."""
        # Create test data file
        data = {
            "director_history": [
                {"tick": 0, "environment": {"pollution": 0.1, "unrest": 0.2}},
                {"tick": 10, "environment": {"pollution": 0.2, "unrest": 0.3}},
            ]
        }
        test_file = tmp_path / "test.json"
        test_file.write_text(json.dumps(data))

        output_file = tmp_path / "output" / "plot.png"

        # Set up mocks
        mock_fig = MagicMock()
        mock_ax_pollution = MagicMock()
        mock_ax_unrest = MagicMock()
        mock_subplots.return_value = (mock_fig, (mock_ax_pollution, mock_ax_unrest))

        result = main([
            "--run", f"test={test_file}",
            "--output", str(output_file),
        ])

        assert result == 0
        mock_fig.savefig.assert_called_once()
        # Verify parent directory was created
        assert output_file.parent.exists()

    @patch("matplotlib.pyplot.show")
    @patch("matplotlib.pyplot.subplots")
    def test_main_uses_custom_title(
        self, mock_subplots: MagicMock, mock_show: MagicMock, tmp_path: Path
    ) -> None:
        """Test that main uses custom title when specified."""
        # Create test data file
        data = {
            "director_history": [
                {"tick": 0, "environment": {"pollution": 0.1, "unrest": 0.2}},
            ]
        }
        test_file = tmp_path / "test.json"
        test_file.write_text(json.dumps(data))

        # Set up mocks
        mock_fig = MagicMock()
        mock_ax_pollution = MagicMock()
        mock_ax_unrest = MagicMock()
        mock_subplots.return_value = (mock_fig, (mock_ax_pollution, mock_ax_unrest))

        result = main([
            "--run", f"test={test_file}",
            "--title", "Custom Plot Title",
        ])

        assert result == 0
        mock_fig.suptitle.assert_called_with("Custom Plot Title")

    @patch("matplotlib.pyplot.show")
    @patch("matplotlib.pyplot.subplots")
    def test_main_prints_warning_for_few_samples(
        self, mock_subplots: MagicMock, mock_show: MagicMock, tmp_path: Path, capsys
    ) -> None:
        """Test that main prints warning when few samples available."""
        # Create test data file with only one sample
        data = {
            "director_history": [
                {"tick": 0, "environment": {"pollution": 0.1, "unrest": 0.2}},
            ]
        }
        test_file = tmp_path / "test.json"
        test_file.write_text(json.dumps(data))

        # Set up mocks
        mock_fig = MagicMock()
        mock_ax_pollution = MagicMock()
        mock_ax_unrest = MagicMock()
        mock_subplots.return_value = (mock_fig, (mock_ax_pollution, mock_ax_unrest))

        result = main(["--run", f"test={test_file}"])

        assert result == 0
        captured = capsys.readouterr()
        assert "Warning" in captured.out
        assert "1 sample" in captured.out

    @patch("matplotlib.pyplot.show")
    @patch("matplotlib.pyplot.subplots")
    def test_main_multiple_runs(
        self, mock_subplots: MagicMock, mock_show: MagicMock, tmp_path: Path
    ) -> None:
        """Test that main handles multiple run files."""
        # Create multiple test data files
        for i, name in enumerate(["run1", "run2", "run3"]):
            data = {
                "director_history": [
                    {
                        "tick": 0,
                        "environment": {"pollution": 0.1 * (i + 1), "unrest": 0.2},
                    },
                    {
                        "tick": 10,
                        "environment": {"pollution": 0.2 * (i + 1), "unrest": 0.3},
                    },
                ]
            }
            test_file = tmp_path / f"{name}.json"
            test_file.write_text(json.dumps(data))

        # Set up mocks
        mock_fig = MagicMock()
        mock_ax_pollution = MagicMock()
        mock_ax_unrest = MagicMock()
        mock_subplots.return_value = (mock_fig, (mock_ax_pollution, mock_ax_unrest))

        result = main([
            "--run", f"run1={tmp_path / 'run1.json'}",
            "--run", f"run2={tmp_path / 'run2.json'}",
            "--run", f"run3={tmp_path / 'run3.json'}",
        ])

        assert result == 0
        # Verify plot was called for each run
        assert mock_ax_pollution.plot.call_count == 3
        assert mock_ax_unrest.plot.call_count == 3


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_extract_series_handles_invalid_json(self, tmp_path: Path) -> None:
        """Test that extract_series raises on invalid JSON."""
        test_file = tmp_path / "invalid.json"
        test_file.write_text("not valid json")

        with pytest.raises(json.JSONDecodeError):
            _extract_series(test_file)

    def test_extract_series_handles_missing_tick(self, tmp_path: Path) -> None:
        """Test handling entries with missing tick field."""
        data = {
            "director_history": [
                {"environment": {"pollution": 0.1, "unrest": 0.2}},  # Missing tick
                {"tick": 10, "environment": {"pollution": 0.2, "unrest": 0.3}},
            ]
        }
        test_file = tmp_path / "test.json"
        test_file.write_text(json.dumps(data))

        ticks, pollution, unrest = _extract_series(test_file)

        # Entry with missing tick should be skipped
        assert ticks == [10]
        assert pollution == [0.2]
        assert unrest == [0.3]

    def test_parse_run_spec_empty_label(self) -> None:
        """Test parsing spec with empty label."""
        label, path = _parse_run_spec("=path/file.json")
        assert label == ""
        assert path == Path("path/file.json")

    def test_help_displays_description(self, capsys) -> None:
        """Test that --help displays script description."""
        with pytest.raises(SystemExit) as exc_info:
            parse_args(["--help"])
        assert exc_info.value.code == 0

        captured = capsys.readouterr()
        assert (
            "pollution" in captured.out.lower()
            or "trajectories" in captured.out.lower()
        )
