from unittest.mock import MagicMock, patch

import pytest

from gengine.balance_studio.cli import main


@pytest.fixture
def mock_script_path(tmp_path):
    """Create a dummy script file to simulate echoes_balance_studio.py."""
    script_dir = tmp_path / "scripts"
    script_dir.mkdir()
    script_path = script_dir / "echoes_balance_studio.py"
    script_path.touch()
    return script_path


def test_main_success(mock_script_path):
    """Test that main successfully loads and runs the script."""
    # Mock the module and its main function
    mock_module = MagicMock()
    mock_module.main.return_value = 0

    # Mock importlib.util.spec_from_file_location
    with patch("importlib.util.spec_from_file_location") as mock_spec_from_file:
        # Setup the mock spec and loader
        mock_spec = MagicMock()
        mock_loader = MagicMock()
        mock_spec.loader = mock_loader
        mock_spec_from_file.return_value = mock_spec

        # Mock importlib.util.module_from_spec
        with patch("importlib.util.module_from_spec") as mock_module_from_spec:
            mock_module_from_spec.return_value = mock_module

            # We also need to patch Path to return our temp path structure
            # specifically when resolving the script path
            with patch("gengine.balance_studio.cli.Path") as mock_path_cls:
                # Configure the mock path to point to our temp script
                # The logic in cli.py is:
                # Path(__file__).resolve().parents[3] / "scripts"
                # We'll just mock the final result of that chain
                mock_resolved_path = MagicMock()
                mock_resolved_path.parents = [
                    MagicMock(),
                    MagicMock(),
                    MagicMock(),
                    MagicMock(),
                ]
                # The 4th parent (index 3) is the root
                mock_root = mock_resolved_path.parents[3]
                mock_root.__truediv__.return_value = mock_script_path.parent
                
                # Mock Path(__file__).resolve()
                mock_path_instance = MagicMock()
                mock_path_instance.resolve.return_value = mock_resolved_path
                mock_path_cls.return_value = mock_path_instance
                
                # Run main
                result = main(["arg1", "arg2"])

                # Verify results
                assert result == 0
                mock_module.main.assert_called_once_with(["arg1", "arg2"])
                mock_spec.loader.exec_module.assert_called_once_with(mock_module)


def test_main_script_not_found():
    """Test that main handles failure to load the script."""
    with patch("importlib.util.spec_from_file_location") as mock_spec_from_file:
        mock_spec_from_file.return_value = None

        # Capture stderr
        with patch("sys.stderr") as mock_stderr:
            result = main()

            assert result == 1
            mock_stderr.write.assert_called_once()
            assert (
                "Failed to load Balance Studio script"
                in mock_stderr.write.call_args[0][0]
            )
