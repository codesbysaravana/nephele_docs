"""
Integration tests for the vision pipeline.

Tests the full pipeline with mock camera data.
Does not require a real camera.
"""

import numpy as np

from edge.vision.models.metrics import (
    VisionMetrics,
    FaceDetectionResult,
    EyeContactResult,
    HeadPoseResult,
)
from edge.vision.utils.fps import FPSCounter
from edge.vision.analytics.engagement import EngagementAnalyzer


class TestPipelineIntegration:
    """Integration tests for the vision pipeline flow."""

    def test_metrics_serialization_roundtrip(self):
        """Metrics should serialize to JSON and maintain structure."""
        import json

        face = FaceDetectionResult(
            face_visible=True, confidence=0.94, bounding_box=(100, 50, 200, 250)
        )
        eye = EyeContactResult(
            eye_contact=True,
            eye_contact_score=87.0,
            gaze_center=(0.5, 0.48),
            left_right_ratio=0.52,
            up_down_ratio=0.49,
        )
        pose = HeadPoseResult(pitch=4.2, yaw=-3.1, roll=1.8)

        metrics = VisionMetrics.from_results(
            face=face, eye=eye, pose=pose, engagement=82.0, fps=14.5
        )

        # Serialize and deserialize
        json_str = metrics.to_json()
        parsed = json.loads(json_str)

        assert parsed["face_visible"] is True
        assert parsed["confidence"] == 0.94
        assert parsed["eye_contact"] is True
        assert parsed["eye_contact_score"] == 87.0
        assert parsed["pitch"] == 4.2
        assert parsed["yaw"] == -3.1
        assert parsed["roll"] == 1.8
        assert parsed["engagement_score"] == 82.0
        assert parsed["fps"] == 14.5
        assert "timestamp" in parsed

    def test_fps_counter_with_processing(self):
        """FPS counter should track processing rate."""
        import time

        counter = FPSCounter(window_size=10)

        for _ in range(20):
            counter.tick()
            time.sleep(0.01)  # Simulate processing

        assert counter.fps > 0
        assert counter.total_frames == 20

    def test_engagement_pipeline(self):
        """Test the engagement calculation pipeline end-to-end."""
        analyzer = EngagementAnalyzer(smoothing_alpha=1.0)

        # Simulate a sequence of detections
        scenarios = [
            # (face_visible, confidence, eye_score, yaw, expected_range)
            (True, 0.95, 90.0, 0.0, (70, 100)),    # Fully engaged
            (True, 0.90, 50.0, 10.0, (40, 80)),     # Moderate
            (True, 0.85, 20.0, 25.0, (15, 55)),     # Low engagement
            (False, 0.0, 0.0, 0.0, (0, 20)),        # No face
        ]

        for face_vis, conf, eye_score, yaw, (min_exp, max_exp) in scenarios:
            analyzer.reset()

            face = FaceDetectionResult(face_visible=face_vis, confidence=conf)
            eye = EyeContactResult(
                eye_contact=eye_score > 60, eye_contact_score=eye_score
            )
            pose = HeadPoseResult(yaw=yaw)

            score = analyzer.calculate(face, eye, pose)
            assert min_exp <= score <= max_exp, (
                f"Expected {min_exp}-{max_exp}, got {score:.1f} for "
                f"face={face_vis}, eye={eye_score}, yaw={yaw}"
            )

    def test_websocket_payload_format(self):
        """WebSocket payload should match expected format."""

        metrics = VisionMetrics(
            face_visible=True,
            confidence=0.94,
            eye_contact=True,
            eye_contact_score=87.0,
            pitch=4.2,
            yaw=-3.1,
            roll=1.8,
            engagement_score=82.0,
            fps=14.5,
        )

        payload = metrics.to_dict()

        # Verify all required fields
        required_fields = [
            "timestamp",
            "face_visible",
            "eye_contact_score",
            "engagement_score",
            "yaw",
            "pitch",
            "roll",
        ]
        for field in required_fields:
            assert field in payload, f"Missing required field: {field}"

    def test_drawing_overlay_no_crash(self):
        """Overlay drawing should not crash with various inputs."""
        from edge.vision.utils.drawing import OverlayDrawer

        drawer = OverlayDrawer()

        # Create a dummy frame
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # Test with default metrics (no face)
        metrics = VisionMetrics(fps=14.5)
        result = drawer.draw_debug_overlay(frame, metrics)
        assert result is not None
        assert result.shape == (480, 640, 3)

        # Test with full metrics
        metrics = VisionMetrics(
            face_visible=True,
            confidence=0.94,
            eye_contact=True,
            eye_contact_score=87.0,
            pitch=4.2,
            yaw=-3.1,
            roll=1.8,
            engagement_score=82.0,
            fps=14.5,
        )
        face = FaceDetectionResult(
            face_visible=True,
            confidence=0.94,
            bounding_box=(100, 50, 200, 250),
        )
        result = drawer.draw_debug_overlay(frame, metrics, face)
        assert result is not None

    def test_all_components_instantiate(self):
        """All pipeline components should instantiate without errors."""
        from edge.vision.detection.face_detector import FaceDetector
        from edge.vision.detection.facemesh_detector import FaceMeshDetector
        from edge.vision.analytics.eye_contact import EyeContactDetector
        from edge.vision.analytics.head_pose import HeadPoseEstimator
        from edge.vision.analytics.engagement import EngagementAnalyzer

        face_detector = FaceDetector()
        facemesh = FaceMeshDetector()
        EyeContactDetector()
        HeadPoseEstimator()
        EngagementAnalyzer()

        # Cleanup
        face_detector.release()
        facemesh.release()
