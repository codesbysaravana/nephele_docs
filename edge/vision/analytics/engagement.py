"""
Engagement Score Calculator.

Scoring System:
==============

The engagement score is a weighted combination of multiple signals:

1. FACE VISIBILITY (weight: 0.25)
   - Binary: 100 if face is visible, 0 if not.
   - Rationale: Can't be engaged if you're not facing the camera.

2. EYE CONTACT SCORE (weight: 0.40)
   - Direct passthrough of the eye contact score [0-100].
   - Highest weight because eye contact is the strongest signal
     of engagement in an interview context.

3. HEAD POSE PENALTY (weight: 0.20)
   - Based on how much the head deviates from facing the camera.
   - Score = 100 - penalty, where penalty increases with deviation.
   - Yaw > 30° or Pitch > 25° → significant disengagement.

4. FACE CONFIDENCE (weight: 0.15)
   - Scales with detection confidence.
   - Low confidence often means partially occluded face.

Final Score Calculation:
    engagement = Σ(weight_i * score_i) for each component
    Clamped to [0, 100]

Temporal Smoothing:
    EMA with alpha=0.2 for smooth transitions.
    This prevents the score from jumping erratically.
"""

import logging
from typing import Optional

from ..models.metrics import (
    EyeContactResult,
    HeadPoseResult,
    FaceDetectionResult,
)

logger = logging.getLogger(__name__)


class EngagementAnalyzer:
    """
    Calculates a composite engagement score from vision signals.
    
    Usage:
        analyzer = EngagementAnalyzer()
        score = analyzer.calculate(
            face_result=face_detection_result,
            eye_result=eye_contact_result,
            pose_result=head_pose_result,
        )
        print(f"Engagement: {score:.0f}%")
    """
    
    # Default weights (must sum to 1.0)
    DEFAULT_WEIGHTS = {
        'face_visible': 0.25,
        'eye_contact': 0.40,
        'head_pose': 0.20,
        'confidence': 0.15,
    }
    
    def __init__(
        self,
        weights: Optional[dict] = None,
        smoothing_alpha: float = 0.2,
        yaw_threshold: float = 30.0,
        pitch_threshold: float = 25.0,
    ):
        """
        Args:
            weights: Custom weight dict (keys: face_visible, eye_contact,
                head_pose, confidence). Must sum to 1.0.
            smoothing_alpha: EMA smoothing factor.
            yaw_threshold: Yaw angle (degrees) at which head pose penalty
                reaches maximum.
            pitch_threshold: Pitch angle (degrees) at which head pose penalty
                reaches maximum.
        """
        self._weights = weights or self.DEFAULT_WEIGHTS.copy()
        self._alpha = smoothing_alpha
        self._yaw_threshold = yaw_threshold
        self._pitch_threshold = pitch_threshold
        self._smoothed_score: Optional[float] = None
        
        # Validate weights
        total = sum(self._weights.values())
        if abs(total - 1.0) > 0.01:
            logger.warning(
                f"Engagement weights sum to {total}, expected 1.0. Normalizing."
            )
            for key in self._weights:
                self._weights[key] /= total
        
        logger.info(
            f"EngagementAnalyzer initialized: weights={self._weights}, "
            f"alpha={smoothing_alpha}"
        )
    
    def calculate(
        self,
        face_result: FaceDetectionResult,
        eye_result: EyeContactResult,
        pose_result: HeadPoseResult,
    ) -> float:
        """
        Calculate the engagement score.
        
        Args:
            face_result: Face detection result.
            eye_result: Eye contact result.
            pose_result: Head pose result.
        
        Returns:
            Engagement score [0-100].
        """
        # Component 1: Face visibility (binary)
        face_score = 100.0 if face_result.face_visible else 0.0
        
        # Component 2: Eye contact (direct passthrough)
        eye_score = eye_result.eye_contact_score
        
        # Component 3: Head pose penalty
        head_score = self._calculate_head_pose_score(pose_result)
        
        # Component 4: Detection confidence
        confidence_score = face_result.confidence * 100.0
        
        # Weighted combination
        raw_score = (
            self._weights['face_visible'] * face_score +
            self._weights['eye_contact'] * eye_score +
            self._weights['head_pose'] * head_score +
            self._weights['confidence'] * confidence_score
        )
        
        # Clamp to [0, 100]
        raw_score = max(0.0, min(100.0, raw_score))
        
        # Temporal smoothing
        if self._smoothed_score is None:
            self._smoothed_score = raw_score
        else:
            self._smoothed_score = (
                self._alpha * raw_score +
                (1 - self._alpha) * self._smoothed_score
            )
        
        return self._smoothed_score
    
    def _calculate_head_pose_score(self, pose: HeadPoseResult) -> float:
        """
        Calculate head pose component score.
        
        The score decreases as the head rotates away from facing the camera.
        Uses a quadratic penalty for smooth falloff:
            penalty = (angle / threshold)^2
        
        This means small head movements are tolerated, but large rotations
        are penalized heavily.
        
        Returns:
            Score [0-100] where 100 = facing camera directly.
        """
        # Yaw penalty (left-right)
        yaw_ratio = min(abs(pose.yaw) / self._yaw_threshold, 1.0)
        yaw_penalty = yaw_ratio ** 2  # Quadratic falloff
        
        # Pitch penalty (up-down)
        pitch_ratio = min(abs(pose.pitch) / self._pitch_threshold, 1.0)
        pitch_penalty = pitch_ratio ** 2
        
        # Combined penalty (take the worse of the two, with some averaging)
        combined_penalty = 0.6 * max(yaw_penalty, pitch_penalty) + \
                          0.4 * (yaw_penalty + pitch_penalty) / 2
        
        return max(0.0, (1.0 - combined_penalty) * 100.0)
    
    def reset(self) -> None:
        """Reset smoothing state."""
        self._smoothed_score = None
