"""
Nephele Vision Pipeline - Main Entry Point.

Orchestrates the complete computer vision pipeline:
    Camera Capture → Face Detection → FaceMesh → Eye Contact →
    Head Pose → Engagement → WebSocket Output

Optimized for Raspberry Pi 4:
    - Camera runs in a separate thread (decoupled from processing)
    - Processing runs in the main thread at whatever FPS it can achieve
    - Optional debug overlay window (disable in production)
    - WebSocket client runs in its own thread with async I/O

Usage:
    python -m edge.vision.main
    python -m edge.vision.main --no-display  # headless mode
    python -m edge.vision.main --ws-url ws://backend:8000/ws/vision
"""

import sys
import cv2
import time
import signal
import logging
import argparse
from typing import Optional

from .camera.camera_service import CameraService
from .detection.face_detector import FaceDetector
from .detection.facemesh_detector import FaceMeshDetector
from .analytics.eye_contact import EyeContactDetector
from .analytics.head_pose import HeadPoseEstimator
from .analytics.engagement import EngagementAnalyzer
from .networking.websocket_client import WebSocketClient
from .models.metrics import (
    VisionMetrics,
    FaceDetectionResult,
    EyeContactResult,
    HeadPoseResult,
)
from .utils.fps import FPSCounter
from .utils.drawing import OverlayDrawer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


class VisionPipeline:
    """
    Main vision pipeline orchestrator.
    
    Coordinates all vision components and manages the processing loop.
    """
    
    def __init__(
        self,
        camera_id: int = 0,
        width: int = 640,
        height: int = 480,
        target_fps: int = 15,
        use_pi_camera: bool = False,
        show_display: bool = True,
        ws_url: str = "ws://localhost:8000/ws/vision",
        enable_websocket: bool = True,
        on_metrics: Optional[callable] = None,
    ):
        """
        Args:
            camera_id: Camera device index.
            width: Capture width.
            height: Capture height.
            target_fps: Target FPS for camera capture.
            use_pi_camera: Whether to use Pi Camera backend.
            show_display: Whether to show debug overlay window.
            ws_url: WebSocket server URL.
            enable_websocket: Whether to enable WebSocket streaming.
            on_metrics: Callback function for direct metrics injection.
        """
        self._show_display = show_display
        self._enable_ws = enable_websocket
        self._on_metrics = on_metrics
        self._running = False
        self._width = width
        self._height = height
        
        # Initialize components
        logger.info("Initializing vision pipeline components...")
        
        # Camera
        self._camera = CameraService(
            camera_id=camera_id,
            width=width,
            height=height,
            target_fps=target_fps,
            use_pi_camera=use_pi_camera,
        )
        
        # Detection
        self._face_detector = FaceDetector(min_confidence=0.5)
        self._facemesh = FaceMeshDetector(
            max_faces=1,
            refine_landmarks=True,
        )
        
        # Analytics
        self._eye_contact = EyeContactDetector()
        self._head_pose = HeadPoseEstimator()
        self._engagement = EngagementAnalyzer()
        
        # Networking
        self._ws_client: Optional[WebSocketClient] = None
        if self._enable_ws:
            self._ws_client = WebSocketClient(url=ws_url)
        
        # Utilities
        self._fps_counter = FPSCounter(window_size=30)
        self._overlay = OverlayDrawer()
        
        # Signal handling for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("Vision pipeline initialized successfully")
    
    def start(self) -> None:
        """Start the vision pipeline."""
        logger.info("Starting vision pipeline...")
        
        # Start camera
        if not self._camera.start():
            logger.error("Failed to start camera. Exiting.")
            return
        
        # Start WebSocket client
        if self._ws_client:
            self._ws_client.start()
        
        # Wait for camera to warm up
        time.sleep(1.0)
        
        self._running = True
        logger.info("Vision pipeline running. Press 'q' to quit.")
        
        try:
            self._processing_loop()
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        finally:
            self.stop()
    
    def stop(self) -> None:
        """Stop all pipeline components."""
        self._running = False
        
        logger.info("Stopping vision pipeline...")
        
        # Stop components
        self._camera.stop()
        
        if self._ws_client:
            self._ws_client.stop()
        
        # Release detectors
        self._face_detector.release()
        self._facemesh.release()
        
        # Close display
        if self._show_display:
            cv2.destroyAllWindows()
        
        # Print summary
        logger.info(
            f"Pipeline stopped. Total frames: {self._camera.frame_count}, "
            f"Average FPS: {self._fps_counter.average_fps:.1f}"
        )
    
    def _processing_loop(self) -> None:
        """
        Main processing loop.
        
        Runs until self._running is False or 'q' is pressed.
        """
        while self._running:
            # Get frame from camera
            frame = self._camera.get_frame()
            if frame is None:
                time.sleep(0.01)  # Brief sleep if no frame available
                continue
            
            # Tick FPS counter
            current_fps = self._fps_counter.tick()
            
            # --- DETECTION PHASE ---
            # Face detection
            face_result = self._face_detector.detect(frame)
            
            # Initialize defaults
            eye_result = EyeContactResult()
            pose_result = HeadPoseResult()
            engagement_score = 0.0
            landmarks = None
            
            if face_result.face_visible:
                # --- LANDMARK PHASE ---
                landmarks = self._facemesh.detect(frame)
                
                if landmarks:
                    # --- ANALYTICS PHASE ---
                    # Eye contact detection
                    eye_result = self._eye_contact.calculate(landmarks)
                    
                    # Head pose estimation
                    pose_result = self._head_pose.estimate(
                        landmarks, self._width, self._height
                    )
                    
                    # Engagement scoring
                    engagement_score = self._engagement.calculate(
                        face_result, eye_result, pose_result
                    )
            
            # --- BUILD METRICS ---
            metrics = VisionMetrics.from_results(
                face=face_result,
                eye=eye_result,
                pose=pose_result,
                engagement=engagement_score,
                fps=current_fps,
            )
            
            # --- SEND OVER WEBSOCKET ---
            if self._ws_client:
                self._ws_client.send_metrics(metrics.to_dict())
                
            # --- LOCAL CALLBACK ---
            if self._on_metrics:
                self._on_metrics(metrics.to_dict())
            
            # --- DEBUG OVERLAY ---
            if self._show_display:
                display_frame = frame.copy()
                self._overlay.draw_debug_overlay(
                    display_frame,
                    metrics,
                    face_result,
                    landmarks,
                )
                
                cv2.imshow("Nephele Vision", display_frame)
                
                # Check for quit key
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    logger.info("Quit key pressed")
                    self._running = False
    
    def _signal_handler(self, signum, frame) -> None:
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        self._running = False


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Nephele Vision Pipeline - AI Interview Robot CV System"
    )
    parser.add_argument(
        "--camera-id", type=int, default=0,
        help="Camera device index (default: 0)"
    )
    parser.add_argument(
        "--width", type=int, default=640,
        help="Capture width (default: 640)"
    )
    parser.add_argument(
        "--height", type=int, default=480,
        help="Capture height (default: 480)"
    )
    parser.add_argument(
        "--fps", type=int, default=15,
        help="Target FPS (default: 15)"
    )
    parser.add_argument(
        "--pi-camera", action="store_true",
        help="Use Pi Camera backend (V4L2)"
    )
    parser.add_argument(
        "--no-display", action="store_true",
        help="Run headless without debug overlay window"
    )
    parser.add_argument(
        "--ws-url", type=str, default="ws://localhost:8000/ws/vision",
        help="WebSocket server URL"
    )
    parser.add_argument(
        "--no-websocket", action="store_true",
        help="Disable WebSocket streaming"
    )
    return parser.parse_args()


def main() -> None:
    """Entry point."""
    args = parse_args()
    
    pipeline = VisionPipeline(
        camera_id=args.camera_id,
        width=args.width,
        height=args.height,
        target_fps=args.fps,
        use_pi_camera=args.pi_camera,
        show_display=not args.no_display,
        ws_url=args.ws_url,
        enable_websocket=not args.no_websocket,
    )
    
    pipeline.start()


if __name__ == "__main__":
    main()
