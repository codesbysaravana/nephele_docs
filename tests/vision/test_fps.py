"""
Unit tests for FPS counter utility.
"""

import time
import pytest
from edge.vision.utils.fps import FPSCounter


class TestFPSCounter:
    """Tests for FPSCounter."""

    def test_initial_state(self):
        """FPS should start at 0."""
        counter = FPSCounter()
        assert counter.fps == 0.0
        assert counter.total_frames == 0

    def test_tick_increments_frame_count(self):
        """Each tick should increment the frame count."""
        counter = FPSCounter()
        counter.tick()
        assert counter.total_frames == 1
        counter.tick()
        assert counter.total_frames == 2

    def test_fps_calculation(self):
        """FPS should be calculated from timestamps."""
        counter = FPSCounter(window_size=5)

        # Simulate 10 frames at ~100 FPS
        for _ in range(10):
            counter.tick()
            time.sleep(0.01)  # 10ms per frame = ~100 FPS

        # FPS should be roughly 100 (with some tolerance for timing jitter)
        assert counter.fps > 50  # Very loose check due to timing
        assert counter.fps < 200

    def test_reset(self):
        """Reset should clear all state."""
        counter = FPSCounter()
        for _ in range(5):
            counter.tick()

        counter.reset()
        assert counter.fps == 0.0
        assert counter.total_frames == 0

    def test_window_size(self):
        """Counter should respect window size."""
        counter = FPSCounter(window_size=3)
        for _ in range(10):
            counter.tick()
            time.sleep(0.001)  # Ensure timestamps differ on Windows

        # Should still work with more frames than window size
        assert counter.total_frames == 10
        assert counter.fps > 0

    def test_elapsed(self):
        """Elapsed time should increase."""
        counter = FPSCounter()
        assert counter.elapsed >= 0
        time.sleep(0.05)
        assert counter.elapsed >= 0.04  # Allow some timing slack

    def test_average_fps(self):
        """Average FPS should be calculated over total lifetime."""
        counter = FPSCounter()
        for _ in range(5):
            counter.tick()
            time.sleep(0.01)

        avg = counter.average_fps
        assert avg > 0
