"""
Camera Service for Nephele Vision Pipeline.

Provides threaded frame capture from USB webcams and Raspberry Pi cameras.
Designed for continuous operation with automatic reconnection on failure.

Architecture:
    A dedicated capture thread reads frames from OpenCV's VideoCapture
    as fast as possible, storing the latest frame in a shared buffer.
    Consumer threads call get_frame() which returns the most recent
    frame without blocking the capture loop.

    This decouples capture rate from processing rate — the camera
    captures at its native rate while CV processing runs at whatever
    speed it can manage.

Optimizations for Raspberry Pi 4:
    - Uses V4L2 backend for Pi Camera (lower overhead than GStreamer)
    - Configurable resolution (640x480 default, can downscale further)
    - Frame buffer reuse to minimize memory allocation
    - MJPEG format preferred for lower CPU decode overhead
"""

import cv2
import time
import logging
import threading
import numpy as np
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class CameraService:
    """
    Threaded camera capture service with automatic reconnection.
    
    Usage:
        camera = CameraService(camera_id=0, width=640, height=480)
        camera.start()
        
        while True:
            frame = camera.get_frame()
            if frame is not None:
                # process frame
                pass
        
        camera.stop()
    """
    
    def __init__(
        self,
        camera_id: int = 0,
        width: int = 640,
        height: int = 480,
        target_fps: int = 15,
        reconnect_delay: float = 2.0,
        max_reconnect_attempts: int = 10,
        use_pi_camera: bool = False,
    ):
        """
        Args:
            camera_id: Camera device index (0 for default/Pi Camera).
            width: Capture width in pixels.
            height: Capture height in pixels.
            target_fps: Target capture framerate.
            reconnect_delay: Seconds between reconnection attempts.
            max_reconnect_attempts: Max consecutive reconnection attempts
                before giving up (resets on successful capture).
            use_pi_camera: If True, uses V4L2 backend optimized for Pi Camera.
        """
        self._camera_id = camera_id
        self._width = width
        self._height = height
        self._target_fps = target_fps
        self._reconnect_delay = reconnect_delay
        self._max_reconnect_attempts = max_reconnect_attempts
        self._use_pi_camera = use_pi_camera
        
        # State
        self._capture: Optional[cv2.VideoCapture] = None
        self._frame: Optional[np.ndarray] = None
        self._frame_lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._connected = False
        self._frame_count = 0
        self._last_frame_time = 0.0
    
    def start(self) -> bool:
        """
        Start the camera capture thread.
        
        Returns:
            True if camera was opened successfully.
        """
        if self._running:
            logger.warning("Camera service already running")
            return True
        
        if not self._open_camera():
            logger.error("Failed to open camera on startup")
            return False
        
        self._running = True
        self._thread = threading.Thread(
            target=self._capture_loop,
            name="CameraCapture",
            daemon=True,
        )
        self._thread.start()
        logger.info(
            f"Camera started: {self._width}x{self._height} @ {self._target_fps}fps"
        )
        return True
    
    def stop(self) -> None:
        """Stop the camera capture thread and release resources."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5.0)
        self._release_camera()
        logger.info("Camera service stopped")
    
    def get_frame(self) -> Optional[np.ndarray]:
        """
        Get the most recent captured frame.
        
        Returns:
            BGR numpy array of the latest frame, or None if no frame available.
            The returned frame is a reference to the internal buffer —
            do NOT modify it. Call .copy() if you need a mutable copy.
        """
        with self._frame_lock:
            return self._frame
    
    @property
    def is_connected(self) -> bool:
        """Whether the camera is currently connected and capturing."""
        return self._connected
    
    @property
    def is_running(self) -> bool:
        """Whether the capture thread is running."""
        return self._running
    
    @property
    def frame_count(self) -> int:
        """Total frames captured."""
        return self._frame_count
    
    @property
    def resolution(self) -> Tuple[int, int]:
        """Current capture resolution (width, height)."""
        return (self._width, self._height)
    
    def _open_camera(self) -> bool:
        """
        Open the camera device with optimal settings.
        
        For Pi Camera: Uses V4L2 backend which has lower overhead.
        For USB webcam: Uses default backend (usually V4L2 on Linux).
        """
        try:
            self._release_camera()
            
            # Select backend
            if self._use_pi_camera:
                self._capture = cv2.VideoCapture(
                    self._camera_id, cv2.CAP_V4L2
                )
            else:
                self._capture = cv2.VideoCapture(self._camera_id)
            
            if not self._capture.isOpened():
                logger.error(f"Cannot open camera {self._camera_id}")
                return False
            
            # Configure capture properties
            self._capture.set(cv2.CAP_PROP_FRAME_WIDTH, self._width)
            self._capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self._height)
            self._capture.set(cv2.CAP_PROP_FPS, self._target_fps)
            
            # Use MJPEG format if available (lower CPU for decode)
            self._capture.set(
                cv2.CAP_PROP_FOURCC,
                cv2.VideoWriter_fourcc(*'MJPG')
            )
            
            # Minimize internal buffer to reduce latency
            self._capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            # Verify
            actual_w = self._capture.get(cv2.CAP_PROP_FRAME_WIDTH)
            actual_h = self._capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
            actual_fps = self._capture.get(cv2.CAP_PROP_FPS)
            
            logger.info(
                f"Camera opened: {actual_w:.0f}x{actual_h:.0f} "
                f"@ {actual_fps:.0f}fps"
            )
            
            self._connected = True
            return True
            
        except Exception as e:
            logger.error(f"Error opening camera: {e}")
            return False
    
    def _release_camera(self) -> None:
        """Release the camera device."""
        if self._capture is not None:
            try:
                self._capture.release()
            except Exception:
                pass
            self._capture = None
        self._connected = False
    
    def _capture_loop(self) -> None:
        """
        Main capture loop running in dedicated thread.
        
        Reads frames continuously and stores them in the shared buffer.
        Handles camera disconnection with automatic reconnection.
        """
        reconnect_attempts = 0
        1.0 / self._target_fps
        
        while self._running:
            if not self._connected:
                # Attempt reconnection
                if reconnect_attempts >= self._max_reconnect_attempts:
                    logger.error(
                        f"Max reconnection attempts ({self._max_reconnect_attempts}) "
                        f"reached. Stopping camera service."
                    )
                    self._running = False
                    break
                
                logger.info(
                    f"Reconnecting camera (attempt {reconnect_attempts + 1}/"
                    f"{self._max_reconnect_attempts})..."
                )
                time.sleep(self._reconnect_delay)
                
                if self._open_camera():
                    reconnect_attempts = 0
                    logger.info("Camera reconnected successfully")
                else:
                    reconnect_attempts += 1
                    continue
            
            try:
                ret, frame = self._capture.read()
                
                if not ret or frame is None:
                    logger.warning("Failed to read frame")
                    self._connected = False
                    continue
                
                # Store frame in shared buffer
                with self._frame_lock:
                    self._frame = frame
                
                self._frame_count += 1
                self._last_frame_time = time.monotonic()
                
                # Reset reconnect counter on successful read
                reconnect_attempts = 0
                
            except Exception as e:
                logger.error(f"Capture error: {e}")
                self._connected = False
        
        self._release_camera()
    
    def __enter__(self) -> 'CameraService':
        self.start()
        return self
    
    def __exit__(self, *args) -> None:
        self.stop()
    
    def __del__(self) -> None:
        self.stop()
