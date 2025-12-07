from unittest.mock import MagicMock, patch

import pytest

from gengine.balance_studio.report_viewer import (
    ReportViewerConfig,
    generate_interactive_html,
    write_html_report,
)


@pytest.fixture
def sample_data():
    return {
        "metadata": {"timestamp": "20230101_120000", "git_commit": "abc1234"},
        "total_sweeps": 2,
        "completed_sweeps": 2,
        "failed_sweeps": 0,
        "total_duration_seconds": 10.5,
        "strategy_stats": {
            "balanced": {
                "count": 1,
                "completed": 1,
                "avg_stability": 0.8,
                "min_stability": 0.8,
                "max_stability": 0.8,
            }
        },
        "difficulty_stats": {
            "normal": {
                "count": 1,
                "completed": 1,
                "avg_stability": 0.8,
                "min_stability": 0.8,
                "max_stability": 0.8,
            }
        },
        "sweeps": [
            {
                "sweep_id": "1",
                "parameters": {
                    "strategy": "balanced",
                    "difficulty": "normal",
                    "seed": 42,
                },
                "results": {"final_stability": 0.8, "actions_taken": 10},
            },
            {
                "sweep_id": "2",
                "parameters": {
                    "strategy": "aggressive",
                    "difficulty": "hard",
                    "seed": 123,
                },
                "results": {"final_stability": 0.2, "actions_taken": 20},
                "error": "Some error",
            },
        ]
    }


def test_generate_interactive_html(sample_data):
    """Test generating HTML report."""
    # Mock matplotlib to avoid actual plotting
    with patch("gengine.balance_studio.report_viewer.HAS_MATPLOTLIB", False):
        html = generate_interactive_html(sample_data)
        
        assert "<!DOCTYPE html>" in html
        assert "Balance Studio Report" in html
        assert "balanced" in html
        assert "0.800" in html
        assert "Some error" in html # Error status should be visible?
        # Actually error message is not directly in the table, but "Error" status is.
        assert "Error" in html


def test_generate_interactive_html_with_charts(sample_data):
    """Test generating HTML report with charts enabled."""
    # Mock matplotlib
    with patch("gengine.balance_studio.report_viewer.HAS_MATPLOTLIB", True), \
         patch("gengine.balance_studio.report_viewer.plt") as mock_plt, \
         patch("gengine.balance_studio.report_viewer.io.BytesIO") as mock_io:
        
        # Configure mock_plt.subplots to return (fig, ax)
        mock_fig = MagicMock()
        mock_ax = MagicMock()
        mock_plt.subplots.return_value = (mock_fig, mock_ax)
        
        # Mock ax.bar to return a list of mocks (bars)
        # We have 1 strategy in sample_data, so 1 bar
        mock_bar = MagicMock()
        mock_bar.get_x.return_value = 0
        mock_bar.get_width.return_value = 1
        mock_ax.bar.return_value = [mock_bar]
        
        # Also need to mock cm.RdYlGn for difficulty chart
        mock_plt.cm.RdYlGn.return_value = ["red", "green"]
        
        mock_io.return_value.read.return_value = b"fake_image_data"
        
        html = generate_interactive_html(sample_data)
        
        assert "data:image/png;base64" in html
        mock_plt.subplots.assert_called()


def test_write_html_report(sample_data, tmp_path):
    """Test writing HTML report to file."""
    output_path = tmp_path / "report.html"
    
    with patch("gengine.balance_studio.report_viewer.HAS_MATPLOTLIB", False):
        write_html_report(sample_data, output_path)
        
    assert output_path.exists()
    content = output_path.read_text()
    assert "<!DOCTYPE html>" in content


def test_report_viewer_config():
    """Test configuration options."""
    config = ReportViewerConfig(
        title="Custom Title",
        include_charts=False,
        include_raw_data=True,
        theme="dark"
    )
    
    assert config.title == "Custom Title"
    assert not config.include_charts
    assert config.include_raw_data
    assert config.theme == "dark"
