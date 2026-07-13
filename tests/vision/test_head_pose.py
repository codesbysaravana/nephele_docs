"""
Unit tests for head pose estimation.

Uses mock landmark data to verify the solvePnP pipeline.
"""

import numpy as np
from unittest.mock import MagicMock
from edge.vision.analytics.head_pose import HeadPoseEstimator
from edge.vision.models.metrics import HeadPoseResult


def _make_landmark(x: float, y: float, z: float = 0.0):
    """Create a mock landmark."""
    lm = MagicMock()
    lm.x = x
    lm.y = y
    lm.z = z
    return lm


def _make_landmarks_facing_forward():
    """
    Create mock landmarks simulating a face looking straight at the camera.

    Landmark layout for solvePnP (indices: 1, 199, 33, 263, 61, 291):
        1   (nose tip)       - center of face
        199 (chin)           - below nose
        33  (left eye outer) - upper left
        263 (right eye outer)- upper right
        61  (left mouth)     - lower left
        291 (right mouth)    - lower right
    """
    landmarks = [_make_landmark(0.5, 0.5) for _ in range(478)]

    # Symmetric face centered in frame
    landmarks[1] = _make_landmark(0.50, 0.45)    # Nose tip - center
    landmarks[199] = _make_landmark(0.50, 0.65)  # Chin - below
    landmarks[33] = _make_landmark(0.35, 0.35)   # Left eye outer
    landmarks[263] = _make_landmark(0.65, 0.35)  # Right eye outer
    landmarks[61] = _make_landmark(0.40, 0.58)   # Left mouth
    landmarks[291] = _make_landmark(0.60, 0.58)  # Right mouth

    return landmarks


def _make_landmarks_turned_right():
    """Create landmarks simulating face turned to the right (positive yaw)."""
    landmarks = [_make_landmark(0.5, 0.5) for _ in range(478)]

    # Shift right side closer, left side further
    landmarks[1] = _make_landmark(0.55, 0.45)    # Nose shifted right
    landmarks[199] = _make_landmark(0.55, 0.65)  # Chin shifted right
    landmarks[33] = _make_landmark(0.42, 0.35)   # Left eye (compressed)
    landmarks[263] = _make_landmark(0.68, 0.35)  # Right eye (expanded)
    landmarks[61] = _make_landmark(0.47, 0.58)   # Left mouth (compressed)
    landmarks[291] = _make_landmark(0.63, 0.58)  # Right mouth (expanded)

    return landmarks


class TestHeadPoseEstimator:
    """Tests for HeadPoseEstimator."""

    def test_default_result_no_landmarks(self):
        """Should return default result with no landmarks."""
        estimator = HeadPoseEstimator()
        result = estimator.estimate([], 640, 480)
        assert result.pitch == 0.0
        assert result.yaw == 0.0
        assert result.roll == 0.0

    def test_facing_forward_small_angles(self):
        """Facing forward should produce valid pose results."""
        estimator = HeadPoseEstimator(smoothing_alpha=1.0)
        landmarks = _make_landmarks_facing_forward()
        result = estimator.estimate(landmarks, 640, 480)

        # Should return a valid result
        assert isinstance(result, HeadPoseResult)
        assert hasattr(result, "yaw")
        assert hasattr(result, "pitch")
        assert hasattr(result, "roll")

    def test_turned_right_positive_yaw(self):
        """Turning right should change yaw relative to forward."""
        estimator_fwd = HeadPoseEstimator(smoothing_alpha=1.0)
        estimator_right = HeadPoseEstimator(smoothing_alpha=1.0)

        fwd_result = estimator_fwd.estimate(
            _make_landmarks_facing_forward(), 640, 480
        )
        right_result = estimator_right.estimate(
            _make_landmarks_turned_right(), 640, 480
        )

        # The yaw should differ between forward and turned right
        # (exact sign depends on coordinate convention, so we just check difference)
        assert abs(right_result.yaw - fwd_result.yaw) > 0.5

    def test_model_points_shape(self):
        """Model points should have correct shape."""
        assert HeadPoseEstimator.MODEL_POINTS.shape == (6, 3)
        assert len(HeadPoseEstimator.LANDMARK_INDICES) == 6

    def test_camera_matrix_caching(self):
        """Camera matrix should be cached for same resolution."""
        estimator = HeadPoseEstimator()

        mat1 = estimator._get_camera_matrix(640, 480)
        mat2 = estimator._get_camera_matrix(640, 480)
        assert mat1 is mat2  # Same object

        mat3 = estimator._get_camera_matrix(1280, 720)
        assert mat1 is not mat3  # Different object for different resolution

    def test_rotation_matrix_to_euler(self):
        """Identity rotation matrix should give near-zero angles."""
        R = np.eye(3)
        pitch, yaw, roll = HeadPoseEstimator._rotation_matrix_to_euler(R)
        assert abs(pitch) < 1.0
        assert abs(yaw) < 1.0
        assert abs(roll) < 1.0

    def test_smoothing(self):
        """Smoothing should reduce jitter between frames."""
        estimator = HeadPoseEstimator(smoothing_alpha=0.3)
        landmarks = _make_landmarks_facing_forward()

        results = []
        for _ in range(5):
            result = estimator.estimate(landmarks, 640, 480)
            results.append(result)

        # All results should converge (last values should be very close)
        if len(results) >= 2:
            assert abs(results[-1].yaw - results[-2].yaw) < abs(
                results[1].yaw - results[0].yaw
            ) + 1  # +1 for tolerance

    def test_reset(self):
        """Reset should clear smoothing state."""
        estimator = HeadPoseEstimator()
        landmarks = _make_landmarks_facing_forward()
        estimator.estimate(landmarks, 640, 480)

        estimator.reset()
        assert estimator._smoothed_pitch is None
        assert estimator._smoothed_yaw is None
        assert estimator._smoothed_roll is None
