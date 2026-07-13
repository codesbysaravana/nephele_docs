"""
Unit tests for the metrics data models.
"""

import json
from edge.vision.models.metrics import (
    FaceDetectionResult,
    EyeContactResult,
    HeadPoseResult,
    VisionMetrics,
)


class TestFaceDetectionResult:
    """Tests for FaceDetectionResult dataclass."""

    def test_default_values(self):
        """Default should indicate no face detected."""
        result = FaceDetectionResult()
        assert result.face_visible is False
        assert result.confidence == 0.0
        assert result.bounding_box is None

    def test_face_detected(self):
        """Should store face detection data correctly."""
        result = FaceDetectionResult(
            face_visible=True,
            confidence=0.94,
            bounding_box=(100, 50, 200, 250),
        )
        assert result.face_visible is True
        assert result.confidence == 0.94
        assert result.bounding_box == (100, 50, 200, 250)

    def test_to_dict(self):
        """to_dict should produce a serializable dict."""
        result = FaceDetectionResult(
            face_visible=True,
            confidence=0.9456,
            bounding_box=(10, 20, 30, 40),
        )
        d = result.to_dict()
        assert d["face_visible"] is True
        assert d["confidence"] == 0.95  # Rounded to 2 decimal places
        assert d["bounding_box"] == [10, 20, 30, 40]

    def test_to_dict_no_bbox(self):
        """to_dict with no bounding box should have None."""
        result = FaceDetectionResult(face_visible=False)
        d = result.to_dict()
        assert d["bounding_box"] is None


class TestEyeContactResult:
    """Tests for EyeContactResult dataclass."""

    def test_default_values(self):
        result = EyeContactResult()
        assert result.eye_contact is False
        assert result.eye_contact_score == 0.0
        assert result.left_right_ratio == 0.5
        assert result.up_down_ratio == 0.5

    def test_eye_contact_detected(self):
        result = EyeContactResult(
            eye_contact=True,
            eye_contact_score=87.3,
            gaze_center=(0.5, 0.48),
            left_right_ratio=0.52,
            up_down_ratio=0.49,
        )
        assert result.eye_contact is True
        assert result.eye_contact_score == 87.3

    def test_to_dict_rounding(self):
        result = EyeContactResult(
            eye_contact=True,
            eye_contact_score=87.3456,
            left_right_ratio=0.51234,
            up_down_ratio=0.48765,
        )
        d = result.to_dict()
        assert d["eye_contact_score"] == 87.3
        assert d["left_right_ratio"] == 0.512
        assert d["up_down_ratio"] == 0.488


class TestHeadPoseResult:
    """Tests for HeadPoseResult dataclass."""

    def test_default_values(self):
        result = HeadPoseResult()
        assert result.pitch == 0.0
        assert result.yaw == 0.0
        assert result.roll == 0.0

    def test_pose_values(self):
        result = HeadPoseResult(pitch=4.2, yaw=-3.1, roll=1.8)
        d = result.to_dict()
        assert d["pitch"] == 4.2
        assert d["yaw"] == -3.1
        assert d["roll"] == 1.8


class TestVisionMetrics:
    """Tests for VisionMetrics dataclass."""

    def test_default_values(self):
        metrics = VisionMetrics()
        assert metrics.face_visible is False
        assert metrics.engagement_score == 0.0

    def test_to_json(self):
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
        json_str = metrics.to_json()
        parsed = json.loads(json_str)
        assert parsed["face_visible"] is True
        assert parsed["engagement_score"] == 82.0
        assert "timestamp" in parsed

    def test_from_results(self):
        face = FaceDetectionResult(face_visible=True, confidence=0.94)
        eye = EyeContactResult(eye_contact=True, eye_contact_score=87.0)
        pose = HeadPoseResult(pitch=4.2, yaw=-3.1, roll=1.8)

        metrics = VisionMetrics.from_results(
            face=face, eye=eye, pose=pose, engagement=82.0, fps=14.5
        )
        assert metrics.face_visible is True
        assert metrics.eye_contact_score == 87.0
        assert metrics.pitch == 4.2
        assert metrics.engagement_score == 82.0
        assert metrics.fps == 14.5
        assert len(metrics.timestamp) > 0

    def test_to_dict_timestamp(self):
        """to_dict should auto-generate timestamp if not set."""
        metrics = VisionMetrics()
        d = metrics.to_dict()
        assert "timestamp" in d
        assert len(d["timestamp"]) > 0
