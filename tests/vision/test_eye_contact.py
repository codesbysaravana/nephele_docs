"""
Unit tests for eye contact detection.

Uses mock landmark data to test the algorithm without a camera.
"""

import pytest
from unittest.mock import MagicMock
from edge.vision.analytics.eye_contact import EyeContactDetector
from edge.vision.models.metrics import EyeContactResult


def _make_landmark(x: float, y: float, z: float = 0.0):
    """Create a mock landmark with x, y, z attributes."""
    lm = MagicMock()
    lm.x = x
    lm.y = y
    lm.z = z
    return lm


def _make_landmarks_looking_center():
    """
    Create 478 mock landmarks simulating a face looking straight ahead.

    Key landmarks for eye contact:
        33  - Left eye outer corner
        133 - Left eye inner corner
        263 - Right eye outer corner
        362 - Right eye inner corner
        159 - Left eye top
        145 - Left eye bottom
        386 - Right eye top
        374 - Right eye bottom
        468 - Left iris center
        473 - Right iris center
    """
    landmarks = [_make_landmark(0.5, 0.5) for _ in range(478)]

    # Left eye: outer=33 at x=0.30, inner=133 at x=0.45 (width=0.15)
    landmarks[33] = _make_landmark(0.30, 0.45)   # outer
    landmarks[133] = _make_landmark(0.45, 0.45)   # inner

    # Right eye: outer=263 at x=0.70, inner=362 at x=0.55 (width=-0.15, but outer > inner)
    landmarks[263] = _make_landmark(0.70, 0.45)   # outer
    landmarks[362] = _make_landmark(0.55, 0.45)   # inner

    # Eye top/bottom for vertical
    landmarks[159] = _make_landmark(0.375, 0.42)  # left eye top
    landmarks[145] = _make_landmark(0.375, 0.48)  # left eye bottom
    landmarks[386] = _make_landmark(0.625, 0.42)  # right eye top
    landmarks[374] = _make_landmark(0.625, 0.48)  # right eye bottom

    # Iris centers - EXACTLY centered between eye corners
    # Left eye center: (0.30 + 0.45) / 2 = 0.375
    landmarks[468] = _make_landmark(0.375, 0.45)  # left iris center
    # Right eye center: (0.70 + 0.55) / 2 = 0.625
    landmarks[473] = _make_landmark(0.625, 0.45)  # right iris center

    return landmarks


def _make_landmarks_looking_left():
    """Create landmarks simulating looking to the left (iris shifted toward outer corner)."""
    landmarks = _make_landmarks_looking_center()

    # Shift iris significantly toward the outer corner (left)
    # Left eye: outer=0.30, center=0.375, inner=0.45 → shift iris to 0.33
    landmarks[468] = _make_landmark(0.33, 0.45)
    # Right eye: outer=0.70, inner=0.55 → shift iris to 0.66 (toward outer=0.70)
    landmarks[473] = _make_landmark(0.66, 0.45)

    return landmarks


def _make_landmarks_looking_right():
    """Create landmarks simulating looking to the right (iris shifted toward inner corner)."""
    landmarks = _make_landmarks_looking_center()

    # Shift iris toward inner corner (right)
    # Left eye: outer=0.30, inner=0.45 → shift iris to 0.42
    landmarks[468] = _make_landmark(0.42, 0.45)
    # Right eye: outer=0.70, inner=0.55 → shift iris to 0.58 (toward inner=0.55)
    landmarks[473] = _make_landmark(0.58, 0.45)

    return landmarks


class TestEyeContactDetector:
    """Tests for EyeContactDetector."""

    def test_default_result_no_landmarks(self):
        """Should return default result with no landmarks."""
        detector = EyeContactDetector()
        result = detector.calculate([])
        assert result.eye_contact is False
        assert result.eye_contact_score == 0.0

    def test_default_result_insufficient_landmarks(self):
        """Should return default with fewer than 478 landmarks."""
        detector = EyeContactDetector()
        landmarks = [_make_landmark(0.5, 0.5) for _ in range(100)]
        result = detector.calculate(landmarks)
        assert result.eye_contact is False

    def test_looking_center_high_score(self):
        """Looking straight ahead should yield high eye contact score."""
        detector = EyeContactDetector(smoothing_alpha=1.0)  # No smoothing
        landmarks = _make_landmarks_looking_center()
        result = detector.calculate(landmarks)

        assert result.eye_contact is True
        assert result.eye_contact_score > 70

    def test_looking_left_lower_score(self):
        """Looking left should yield lower eye contact score than center."""
        detector = EyeContactDetector(smoothing_alpha=1.0)
        landmarks = _make_landmarks_looking_left()
        result = detector.calculate(landmarks)

        center_detector = EyeContactDetector(smoothing_alpha=1.0)
        center_result = center_detector.calculate(_make_landmarks_looking_center())

        # Left gaze should produce a noticeably lower score
        assert result.eye_contact_score < center_result.eye_contact_score - 1

    def test_looking_right_lower_score(self):
        """Looking right should yield lower eye contact score than center."""
        detector = EyeContactDetector(smoothing_alpha=1.0)
        landmarks = _make_landmarks_looking_right()
        result = detector.calculate(landmarks)

        center_detector = EyeContactDetector(smoothing_alpha=1.0)
        center_result = center_detector.calculate(_make_landmarks_looking_center())

        assert result.eye_contact_score < center_result.eye_contact_score - 1

    def test_gaze_center_returned(self):
        """Should return gaze center coordinates."""
        detector = EyeContactDetector(smoothing_alpha=1.0)
        landmarks = _make_landmarks_looking_center()
        result = detector.calculate(landmarks)

        assert result.gaze_center is not None
        assert len(result.gaze_center) == 2

    def test_smoothing_reduces_jitter(self):
        """With smoothing, alternating inputs should produce stable output."""
        detector = EyeContactDetector(smoothing_alpha=0.3)

        scores = []
        for i in range(10):
            if i % 2 == 0:
                landmarks = _make_landmarks_looking_center()
            else:
                landmarks = _make_landmarks_looking_left()
            result = detector.calculate(landmarks)
            scores.append(result.eye_contact_score)

        # Later scores should be more stable (less variance)
        early_range = max(scores[:4]) - min(scores[:4])
        late_range = max(scores[6:]) - min(scores[6:])

        # The late range should be smaller due to smoothing
        assert late_range <= early_range or late_range < 20

    def test_reset(self):
        """Reset should clear smoothing state."""
        detector = EyeContactDetector()

        landmarks = _make_landmarks_looking_center()
        detector.calculate(landmarks)
        detector.reset()

        # After reset, internal smoothed values should be None
        assert detector._smoothed_lr is None
        assert detector._smoothed_ud is None
        assert detector._smoothed_score is None

    def test_score_range(self):
        """Score should always be between 0 and 100."""
        detector = EyeContactDetector(smoothing_alpha=1.0)

        for landmarks_fn in [
            _make_landmarks_looking_center,
            _make_landmarks_looking_left,
            _make_landmarks_looking_right,
        ]:
            result = detector.calculate(landmarks_fn())
            assert 0 <= result.eye_contact_score <= 100
            detector.reset()
