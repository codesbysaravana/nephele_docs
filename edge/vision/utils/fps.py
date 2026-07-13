"""FPS counter with sliding window for smooth measurement."""

import time
from collections import deque


class FPSCounter:
    """
    Tracks frames per second using a sliding window approach.
    
    Instead of measuring instantaneous FPS (which fluctuates wildly),
    we maintain a deque of timestamps for the last N frames and
    calculate FPS as: count / (newest_timestamp - oldest_timestamp).
    
    This gives a smooth, rolling average that's useful for display.
    """
    
    def __init__(self, window_size: int = 30):
        """
        Args:
            window_size: Number of frames to average over.
                         Larger = smoother but slower to respond.
                         30 frames ≈ 2 seconds at 15 FPS.
        """
        self._window_size = window_size
        self._timestamps: deque = deque(maxlen=window_size)
        self._fps: float = 0.0
        self._frame_count: int = 0
        self._start_time: float = time.monotonic()
    
    def tick(self) -> float:
        """
        Call once per frame to record a timestamp.
        
        Returns:
            Current smoothed FPS value.
        """
        now = time.monotonic()
        self._timestamps.append(now)
        self._frame_count += 1
        
        if len(self._timestamps) >= 2:
            elapsed = self._timestamps[-1] - self._timestamps[0]
            if elapsed > 0:
                self._fps = (len(self._timestamps) - 1) / elapsed
        
        return self._fps
    
    @property
    def fps(self) -> float:
        """Current smoothed FPS."""
        return self._fps
    
    @property
    def total_frames(self) -> int:
        """Total frames counted since creation."""
        return self._frame_count
    
    @property
    def elapsed(self) -> float:
        """Total seconds since counter was created."""
        return time.monotonic() - self._start_time
    
    @property
    def average_fps(self) -> float:
        """Overall average FPS since creation."""
        elapsed = self.elapsed
        return self._frame_count / elapsed if elapsed > 0 else 0.0
    
    def reset(self) -> None:
        """Reset all counters."""
        self._timestamps.clear()
        self._fps = 0.0
        self._frame_count = 0
        self._start_time = time.monotonic()
