"""
Eye Contact Detection using Iris Landmarks.

Algorithm Explanation:
====================

MediaPipe FaceMesh provides iris landmarks when refine_landmarks=True:
    Left Iris:  468 (center), 469 (top), 470 (right), 471 (bottom), 472 (left)
    Right Iris: 473 (center), 474 (top), 475 (right), 476 (bottom), 477 (left)

Along with eye corner landmarks:
    Left Eye:  inner=133, outer=33
    Right Eye: inner=362, outer=263

Gaze Calculation:
-----------------
1. For each eye, we compute the iris position relative to the eye corners.

2. LEFT-RIGHT RATIO:
   - Measure the horizontal distance from the outer eye corner to the iris center.
   - Divide by the total eye width (outer to inner corner).
   - Result: 0.0 = looking far left, 0.5 = looking center, 1.0 = looking far right.
   - We average both eyes for stability.

3. UP-DOWN RATIO:
   - Measure the vertical distance from the top of the eye to the iris center.
   - Divide by the total eye height.
   - Result: 0.0 = looking up, 0.5 = center, 1.0 = looking down.

4. EYE CONTACT SCORE:
   - Calculate deviation from center (0.5, 0.5) for both ratios.
   - Score = 100 - (weighted_deviation * 100)
   - Clamp to [0, 100].
   - Eye contact is True when score >= threshold (default 60).

5. TEMPORAL SMOOTHING:
   - Apply exponential moving average (EMA) to reduce jitter.
   - EMA: smoothed = alpha * current + (1 - alpha) * previous
   - alpha=0.3 gives good balance between responsiveness and stability.
"""

import logging
from typing import Optional

from ..models.metrics import EyeContactResult

logger = logging.getLogger(__name__)


class EyeContactDetector:
    """
    Detects whether the user is making eye contact with the camera.
    
    Uses iris position relative to eye corners to determine gaze direction.
    
    Usage:
        detector = EyeContactDetector()
        result = detector.calculate(landmarks)
        print(f"Eye contact: {result.eye_contact}, Score: {result.eye_contact_score}")
    """
    
    # Landmark indices
    LEFT_IRIS_CENTER = 468
    RIGHT_IRIS_CENTER = 473
    LEFT_EYE_INNER = 133
    LEFT_EYE_OUTER = 33
    RIGHT_EYE_INNER = 362
    RIGHT_EYE_OUTER = 263
    
    # Eye contour for vertical measurement
    LEFT_EYE_TOP = 159     # Top of left eye
    LEFT_EYE_BOTTOM = 145  # Bottom of left eye
    RIGHT_EYE_TOP = 386    # Top of right eye
    RIGHT_EYE_BOTTOM = 374 # Bottom of right eye
    
    def __init__(
        self,
        contact_threshold: float = 60.0,
        smoothing_alpha: float = 0.3,
        lr_weight: float = 1.5,
        ud_weight: float = 1.0,
    ):
        """
        Args:
            contact_threshold: Minimum score to consider as eye contact [0-100].
            smoothing_alpha: EMA smoothing factor. Lower = smoother but laggier.
            lr_weight: Weight for left-right deviation in score calculation.
                Higher = more sensitive to horizontal gaze shifts.
            ud_weight: Weight for up-down deviation in score calculation.
        """
        self._threshold = contact_threshold
        self._alpha = smoothing_alpha
        self._lr_weight = lr_weight
        self._ud_weight = ud_weight
        
        # Smoothed values
        self._smoothed_lr: Optional[float] = None
        self._smoothed_ud: Optional[float] = None
        self._smoothed_score: Optional[float] = None
        
        logger.info(
            f"EyeContactDetector initialized: threshold={contact_threshold}, "
            f"alpha={smoothing_alpha}"
        )
    
    def calculate(self, landmarks: list) -> EyeContactResult:
        """
        Calculate eye contact metrics from face landmarks.
        
        Args:
            landmarks: List of 478 NormalizedLandmark objects from FaceMesh.
        
        Returns:
            EyeContactResult with score, boolean contact, and gaze ratios.
        """
        if not landmarks or len(landmarks) < 478:
            return EyeContactResult()
        
        try:
            # --- LEFT-RIGHT RATIO ---
            # For each eye: ratio = (iris_x - outer_x) / (inner_x - outer_x)
            
            # Left eye horizontal
            left_iris_x = landmarks[self.LEFT_IRIS_CENTER].x
            left_outer_x = landmarks[self.LEFT_EYE_OUTER].x
            left_inner_x = landmarks[self.LEFT_EYE_INNER].x
            left_eye_width = left_inner_x - left_outer_x
            
            if abs(left_eye_width) < 1e-6:
                return EyeContactResult()
            
            left_lr_ratio = (left_iris_x - left_outer_x) / left_eye_width
            
            # Right eye horizontal
            right_iris_x = landmarks[self.RIGHT_IRIS_CENTER].x
            right_outer_x = landmarks[self.RIGHT_EYE_OUTER].x
            right_inner_x = landmarks[self.RIGHT_EYE_INNER].x
            right_eye_width = right_inner_x - right_outer_x
            
            if abs(right_eye_width) < 1e-6:
                return EyeContactResult()
            
            right_lr_ratio = (right_iris_x - right_outer_x) / right_eye_width
            
            # Average both eyes for stability
            lr_ratio = (left_lr_ratio + right_lr_ratio) / 2.0
            
            # --- UP-DOWN RATIO ---
            # For each eye: ratio = (iris_y - top_y) / (bottom_y - top_y)
            
            # Left eye vertical
            left_iris_y = landmarks[self.LEFT_IRIS_CENTER].y
            left_top_y = landmarks[self.LEFT_EYE_TOP].y
            left_bottom_y = landmarks[self.LEFT_EYE_BOTTOM].y
            left_eye_height = left_bottom_y - left_top_y
            
            if abs(left_eye_height) < 1e-6:
                return EyeContactResult()
            
            left_ud_ratio = (left_iris_y - left_top_y) / left_eye_height
            
            # Right eye vertical
            right_iris_y = landmarks[self.RIGHT_IRIS_CENTER].y
            right_top_y = landmarks[self.RIGHT_EYE_TOP].y
            right_bottom_y = landmarks[self.RIGHT_EYE_BOTTOM].y
            right_eye_height = right_bottom_y - right_top_y
            
            if abs(right_eye_height) < 1e-6:
                return EyeContactResult()
            
            right_ud_ratio = (right_iris_y - right_top_y) / right_eye_height
            
            ud_ratio = (left_ud_ratio + right_ud_ratio) / 2.0
            
            # --- TEMPORAL SMOOTHING (EMA) ---
            if self._smoothed_lr is None:
                self._smoothed_lr = lr_ratio
                self._smoothed_ud = ud_ratio
            else:
                self._smoothed_lr = (
                    self._alpha * lr_ratio +
                    (1 - self._alpha) * self._smoothed_lr
                )
                self._smoothed_ud = (
                    self._alpha * ud_ratio +
                    (1 - self._alpha) * self._smoothed_ud
                )
            
            # --- EYE CONTACT SCORE ---
            # Deviation from center (0.5, 0.5)
            lr_deviation = abs(self._smoothed_lr - 0.5) * 2  # Normalize to [0, 1]
            ud_deviation = abs(self._smoothed_ud - 0.5) * 2  # Normalize to [0, 1]
            
            # Weighted combined deviation
            total_weight = self._lr_weight + self._ud_weight
            weighted_deviation = (
                self._lr_weight * lr_deviation +
                self._ud_weight * ud_deviation
            ) / total_weight
            
            # Convert to score: 0 deviation = 100, max deviation = 0
            raw_score = max(0.0, min(100.0, (1.0 - weighted_deviation) * 100.0))
            
            # Smooth the score
            if self._smoothed_score is None:
                self._smoothed_score = raw_score
            else:
                self._smoothed_score = (
                    self._alpha * raw_score +
                    (1 - self._alpha) * self._smoothed_score
                )
            
            # Determine eye contact
            is_contact = self._smoothed_score >= self._threshold
            
            # Gaze center (average iris position)
            gaze_x = (
                landmarks[self.LEFT_IRIS_CENTER].x +
                landmarks[self.RIGHT_IRIS_CENTER].x
            ) / 2.0
            gaze_y = (
                landmarks[self.LEFT_IRIS_CENTER].y +
                landmarks[self.RIGHT_IRIS_CENTER].y
            ) / 2.0
            
            return EyeContactResult(
                eye_contact=is_contact,
                eye_contact_score=self._smoothed_score,
                gaze_center=(gaze_x, gaze_y),
                left_right_ratio=self._smoothed_lr,
                up_down_ratio=self._smoothed_ud,
            )
            
        except (IndexError, AttributeError) as e:
            logger.warning(f"Eye contact calculation error: {e}")
            return EyeContactResult()
    
    def reset(self) -> None:
        """Reset smoothing state."""
        self._smoothed_lr = None
        self._smoothed_ud = None
        self._smoothed_score = None
