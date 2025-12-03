"""Performance and tick-limit regression tests for Echoes of Emergence.

This module ensures that:
- Configured tick limits (engine, CLI, service) are enforced via existing APIs.
- Basic timing benchmarks for multi-tick runs stay under generous thresholds.

Tests marked with @pytest.mark.slow can be skipped via `pytest -m "not slow"`.
"""

from __future__ import annotations

import time

import pytest
from fastapi.testclient import TestClient

from gengine.echoes.cli.shell import EchoesShell, LocalBackend
from gengine.echoes.service import create_app
from gengine.echoes.settings import SimulationConfig, SimulationLimits
from gengine.echoes.sim import SimEngine


# --------------------------------------------------------------------------
# Engine tick-limit enforcement tests
# --------------------------------------------------------------------------


class TestEngineTickLimits:
    """Tests verifying engine_max_ticks limit enforcement."""

    def test_advance_ticks_within_limit_succeeds(self) -> None:
        """Advancing ticks within the configured limit should succeed."""
        limits = SimulationLimits(
            engine_max_ticks=10,
            cli_run_cap=10,
            cli_script_command_cap=20,
            service_tick_cap=10,
        )
        config = SimulationConfig(limits=limits)
        engine = SimEngine(config=config)
        engine.initialize_state(world="default")

        # This should succeed without raising
        reports = engine.advance_ticks(10)

        assert len(reports) == 10
        assert engine.state.tick == 10

    def test_advance_ticks_exceeds_limit_raises_valueerror(self) -> None:
        """Exceeding engine_max_ticks should raise ValueError."""
        limits = SimulationLimits(
            engine_max_ticks=5,
            cli_run_cap=10,
            cli_script_command_cap=20,
            service_tick_cap=10,
        )
        config = SimulationConfig(limits=limits)
        engine = SimEngine(config=config)
        engine.initialize_state(world="default")

        with pytest.raises(ValueError, match="exceeds engine limit"):
            engine.advance_ticks(10)

    def test_engine_limit_exact_boundary(self) -> None:
        """Requesting exactly the limit should succeed."""
        limits = SimulationLimits(
            engine_max_ticks=3,
            cli_run_cap=5,
            cli_script_command_cap=10,
            service_tick_cap=5,
        )
        config = SimulationConfig(limits=limits)
        engine = SimEngine(config=config)
        engine.initialize_state(world="default")

        reports = engine.advance_ticks(3)

        assert len(reports) == 3

    def test_engine_limit_one_over_boundary_fails(self) -> None:
        """Requesting one more than the limit should fail."""
        limits = SimulationLimits(
            engine_max_ticks=3,
            cli_run_cap=5,
            cli_script_command_cap=10,
            service_tick_cap=5,
        )
        config = SimulationConfig(limits=limits)
        engine = SimEngine(config=config)
        engine.initialize_state(world="default")

        with pytest.raises(ValueError, match="exceeds engine limit"):
            engine.advance_ticks(4)


# --------------------------------------------------------------------------
# CLI tick-limit enforcement tests
# --------------------------------------------------------------------------


class TestCLITickLimits:
    """Tests verifying cli_run_cap limit enforcement via the shell."""

    def test_cli_run_command_within_limit_succeeds(self) -> None:
        """Running ticks within cli_run_cap should succeed."""
        limits = SimulationLimits(
            engine_max_ticks=20,
            cli_run_cap=5,
            cli_script_command_cap=20,
            service_tick_cap=20,
        )
        engine = SimEngine()
        engine.initialize_state(world="default")
        shell = EchoesShell(LocalBackend(engine), limits=limits)

        result = shell.execute("run 3")

        # Should complete without safeguard clamping
        assert "Safeguard" not in result.output
        # Should have run 3 ticks
        assert result.output.count("Tick") == 3

    def test_cli_run_command_exceeds_limit_is_clamped(self) -> None:
        """Running ticks exceeding cli_run_cap should be clamped with safeguard message."""
        limits = SimulationLimits(
            engine_max_ticks=20,
            cli_run_cap=3,
            cli_script_command_cap=20,
            service_tick_cap=20,
        )
        engine = SimEngine()
        engine.initialize_state(world="default")
        shell = EchoesShell(LocalBackend(engine), limits=limits)

        result = shell.execute("run 10")

        # Should show safeguard message
        assert "Safeguard" in result.output
        # Should have run only 3 ticks (clamped to limit)
        assert result.output.count("Tick") == 3

    def test_cli_run_at_boundary(self) -> None:
        """Running ticks at exactly cli_run_cap should succeed without safeguard."""
        limits = SimulationLimits(
            engine_max_ticks=20,
            cli_run_cap=4,
            cli_script_command_cap=20,
            service_tick_cap=20,
        )
        engine = SimEngine()
        engine.initialize_state(world="default")
        shell = EchoesShell(LocalBackend(engine), limits=limits)

        result = shell.execute("run 4")

        assert "Safeguard" not in result.output
        assert result.output.count("Tick") == 4


# --------------------------------------------------------------------------
# Service tick-limit enforcement tests
# --------------------------------------------------------------------------


class TestServiceTickLimits:
    """Tests verifying service_tick_cap limit enforcement via the HTTP API."""

    def _create_client(
        self, service_tick_cap: int = 10
    ) -> tuple[TestClient, SimEngine]:
        """Create a test client with specified service tick cap."""
        limits = SimulationLimits(
            engine_max_ticks=100,
            cli_run_cap=50,
            cli_script_command_cap=200,
            service_tick_cap=service_tick_cap,
        )
        config = SimulationConfig(limits=limits)
        engine = SimEngine(config=config)
        engine.initialize_state(world="default")
        app = create_app(engine=engine, config=config)
        return TestClient(app), engine

    def test_service_tick_within_limit_succeeds(self) -> None:
        """Tick request within service_tick_cap should return 200."""
        client, _ = self._create_client(service_tick_cap=10)

        response = client.post("/tick", json={"ticks": 5})

        assert response.status_code == 200
        body = response.json()
        assert body["ticks_advanced"] == 5

    def test_service_tick_exceeds_limit_returns_400(self) -> None:
        """Tick request exceeding service_tick_cap should return 400."""
        client, _ = self._create_client(service_tick_cap=5)

        response = client.post("/tick", json={"ticks": 10})

        assert response.status_code == 400
        assert "limit" in response.json()["detail"].lower()

    def test_service_tick_at_boundary_succeeds(self) -> None:
        """Tick request at exactly service_tick_cap should succeed."""
        client, _ = self._create_client(service_tick_cap=7)

        response = client.post("/tick", json={"ticks": 7})

        assert response.status_code == 200
        body = response.json()
        assert body["ticks_advanced"] == 7

    def test_service_tick_one_over_boundary_fails(self) -> None:
        """Tick request one over service_tick_cap should fail."""
        client, _ = self._create_client(service_tick_cap=7)

        response = client.post("/tick", json={"ticks": 8})

        assert response.status_code == 400
        assert "limit" in response.json()["detail"].lower()


# --------------------------------------------------------------------------
# Performance timing tests (marked slow)
# --------------------------------------------------------------------------


@pytest.mark.slow
class TestPerformanceTiming:
    """Basic performance regression tests with generous thresholds.

    These tests ensure multi-tick runs complete in a reasonable time.
    Thresholds are intentionally generous to avoid CI flakiness.
    """

    def test_multi_tick_run_completes_within_threshold(self) -> None:
        """100 ticks should complete within 10 seconds on CI hardware.

        This is a basic performance regression test. The threshold is
        intentionally generous to avoid flakiness on varying CI hardware.
        Adjust the threshold if CI consistently passes with time to spare.
        """
        threshold_seconds = 10.0
        tick_count = 100

        engine = SimEngine()
        engine.initialize_state(world="default")

        start_time = time.perf_counter()
        reports = engine.advance_ticks(tick_count, seed=42)
        elapsed_time = time.perf_counter() - start_time

        assert len(reports) == tick_count
        assert elapsed_time < threshold_seconds, (
            f"Multi-tick run took {elapsed_time:.2f}s, "
            f"exceeding threshold of {threshold_seconds}s"
        )

    def test_repeated_tick_batches_consistent_timing(self) -> None:
        """Repeated tick batches should have consistent timing.

        This test ensures that performance doesn't degrade significantly
        over multiple tick batches (e.g., due to memory leaks or
        unbounded data structures).
        """
        batch_size = 20
        num_batches = 5
        max_per_batch_seconds = 3.0

        engine = SimEngine()
        engine.initialize_state(world="default")

        batch_times = []
        for i in range(num_batches):
            start_time = time.perf_counter()
            engine.advance_ticks(batch_size, seed=42 + i)
            elapsed = time.perf_counter() - start_time
            batch_times.append(elapsed)

        # Each batch should complete within the threshold
        for i, batch_time in enumerate(batch_times):
            assert batch_time < max_per_batch_seconds, (
                f"Batch {i + 1} took {batch_time:.2f}s, "
                f"exceeding threshold of {max_per_batch_seconds}s"
            )

        # Ensure total ticks were advanced
        assert engine.state.tick == batch_size * num_batches

    def test_average_tick_time_within_bounds(self) -> None:
        """Average per-tick time should remain under threshold.

        This test provides a more granular view of tick performance.
        """
        tick_count = 50
        max_avg_ms_per_tick = 100.0  # 100ms average per tick is generous

        engine = SimEngine()
        engine.initialize_state(world="default")

        start_time = time.perf_counter()
        reports = engine.advance_ticks(tick_count, seed=42)
        elapsed_time = time.perf_counter() - start_time

        avg_ms_per_tick = (elapsed_time / tick_count) * 1000

        assert len(reports) == tick_count
        assert avg_ms_per_tick < max_avg_ms_per_tick, (
            f"Average tick time {avg_ms_per_tick:.2f}ms "
            f"exceeds threshold of {max_avg_ms_per_tick}ms"
        )
