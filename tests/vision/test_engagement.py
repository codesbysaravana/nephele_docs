"""
Unit tests for engagement scoring.
"""

import pytest
from edge.vision.analytics.engagement import EngagementAnalyzer
from edge.vision.models.metrics import (
    FaceDetectionResult,
    EyeContactResult,
    HeadPoseResult,
)


class TestEngagementAnalyzer:
    """Tests for EngagementAnalyzer."""

    def test_fully_engaged(self):
        """Maximum engagement: face visible, eye contact, facing camera."""
        analyzer = EngagementAnalyzer(smoothing_alpha=1.0)

        face = FaceDetectionResult(face_visible=True, confidence=0.95)
        eye = EyeContactResult(eye_contact=True, eye_contact_score=95.0)
        pose = HeadPoseResult(pitch=0.0, yaw=0.0, roll=0.0)

        score = analyzer.calculate(face, eye, pose)
        assert score > 80  # Should be high engagement

    def test_no_face(self):
        """No face visible should yield very low engagement."""
        analyzer = EngagementAnalyzer(smoothing_alpha=1.0)

        face = FaceDetectionResult(face_visible=False, confidence=0.0)
        eye = EyeContactResult()
        pose = HeadPoseResult()

        score = analyzer.calculate(face, eye, pose)
        assert score <= 20  # Very low engagement

    def test_face_visible_no_eye_contact(self):
        """Face visible but no eye contact should be moderate."""
        analyzer = EngagementAnalyzer(smoothing_alpha=1.0)

        face = FaceDetectionResult(face_visible=True, confidence=0.90)
        eye = EyeContactResult(eye_contact=False, eye_contact_score=20.0)
        pose = HeadPoseResult(pitch=0.0, yaw=0.0, roll=0.0)

        score = analyzer.calculate(face, eye, pose)
        assert 20 < score < 80  # Moderate engagement

    def test_head_turned_away(self):
        """Head turned far away should reduce engagement."""
        analyzer = EngagementAnalyzer(smoothing_alpha=1.0)

        face = FaceDetectionResult(face_visible=True, confidence=0.85)
        eye = EyeContactResult(eye_contact=False, eye_contact_score=30.0)
        pose = HeadPoseResult(pitch=0.0, yaw=40.0, roll=0.0)  # Turned 40°

        score = analyzer.calculate(face, eye, pose)

        # Compare with facing camera
        analyzer2 = EngagementAnalyzer(smoothing_alpha=1.0)
        face2 = FaceDetectionResult(face_visible=True, confidence=0.85)
        eye2 = EyeContactResult(eye_contact=False, eye_contact_score=30.0)
        pose2 = HeadPoseResult(pitch=0.0, yaw=0.0, roll=0.0)

        score2 = analyzer2.calculate(face2, eye2, pose2)

        assert score < score2  # Turned away = lower engagement

    def test_score_clamping(self):
        """Score should always be in [0, 100]."""
        analyzer = EngagementAnalyzer(smoothing_alpha=1.0)

        # Test with extreme values
        face = FaceDetectionResult(face_visible=True, confidence=1.0)
        eye = EyeContactResult(eye_contact=True, eye_contact_score=100.0)
        pose = HeadPoseResult(pitch=0.0, yaw=0.0, roll=0.0)

        score = analyzer.calculate(face, eye, pose)
        assert 0 <= score <= 100

    def test_weight_normalization_warning(self):
        """Non-unit weights should be normalized."""
        weights = {
            'face_visible': 0.5,
            'eye_contact': 0.5,
            'head_pose': 0.5,
            'confidence': 0.5,
        }
        analyzer = EngagementAnalyzer(weights=weights, smoothing_alpha=1.0)

        # Should still produce valid results after normalization
        face = FaceDetectionResult(face_visible=True, confidence=0.90)
        eye = EyeContactResult(eye_contact=True, eye_contact_score=80.0)
        pose = HeadPoseResult()

        score = analyzer.calculate(face, eye, pose)
        assert 0 <= score <= 100

    def test_head_pose_score_quadratic(self):
        """Head pose penalty should follow quadratic curve."""
        analyzer = EngagementAnalyzer()

        # Small angle - small penalty
        small = HeadPoseResult(yaw=5.0)
        small_score = analyzer._calculate_head_pose_score(small)

        # Large angle - large penalty
        large = HeadPoseResult(yaw=25.0)
        large_score = analyzer._calculate_head_pose_score(large)

        assert small_score > large_score
        assert small_score > 80  # Small angle should have high score

    def test_smoothing(self):
        """Smoothing should prevent jumps."""
        analyzer = EngagementAnalyzer(smoothing_alpha=0.2)

        face = FaceDetectionResult(face_visible=True, confidence=0.90)
        eye_high = EyeContactResult(eye_contact=True, eye_contact_score=90.0)
        eye_low = EyeContactResult(eye_contact=False, eye_contact_score=10.0)
        pose = HeadPoseResult()

        # Start with high engagement
        score1 = analyzer.calculate(face, eye_high, pose)

        # Sudden drop to low
        score2 = analyzer.calculate(face, eye_low, pose)

        # Score should not drop all the way to low (smoothing)
        assert score2 > 20  # Smoothed, not fully dropped

    def test_reset(self):
        """Reset should clear smoothing."""
        analyzer = EngagementAnalyzer()

        face = FaceDetectionResult(face_visible=True, confidence=0.90)
        eye = EyeContactResult(eye_contact=True, eye_contact_score=80.0)
        pose = HeadPoseResult()

        analyzer.calculate(face, eye, pose)
        analyzer.reset()
        assert analyzer._smoothed_score is None
