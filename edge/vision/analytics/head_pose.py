"""
Head Pose Estimation using OpenCV solvePnP.

Algorithm Explanation:
====================

Head pose estimation solves the Perspective-n-Point (PnP) problem:
Given known 3D points on a face model and their corresponding 2D projections
in the camera image, compute the rotation and translation of the head
relative to the camera.

Landmark Selection:
-------------------
We use 6 key landmarks from MediaPipe FaceMesh that are:
1. Well-distributed across the face (not clustered)
2. Anatomically stable (don't move with expressions)
3. Reliable to detect (high confidence)

Selected landmarks:
    Index 1   - Nose tip          (most protruding point)
    Index 199 - Chin               (bottom of face)
    Index 33  - Left eye outer     (stable corner)
    Index 263 - Right eye outer    (stable corner)
    Index 61  - Left mouth corner  (relatively stable)
    Index 291 - Right mouth corner (relatively stable)

3D Model Points:
--------------
We define a canonical 3D face model based on an average human face.
Coordinates are in an arbitrary unit system centered at the nose tip.
The specific values come from anthropometric face measurements:
    - Average face width: ~14cm
    - Average face height: ~18cm
    - Nose protrusion: ~3cm

Camera Matrix:
--------------
We approximate the camera intrinsic matrix using:
    - Focal length ≈ frame width (reasonable for most webcams/Pi cameras)
    - Principal point = image center
This is an approximation, but works well in practice for relative
pose estimation (we care about changes, not absolute angles).

solvePnP:
---------
OpenCV's solvePnP uses the Levenberg-Marquardt iterative method to
find the rotation vector (Rodrigues form) and translation vector that
minimize the reprojection error.

We convert the rotation vector to Euler angles (pitch, yaw, roll):
    - Pitch: Up/down head rotation (positive = looking up)
    - Yaw:   Left/right head rotation (positive = looking right)
    - Roll:  Head tilt (positive = tilting right)
"""

import cv2
import logging
import numpy as np
from typing import Optional, Tuple

from ..models.metrics import HeadPoseResult

logger = logging.getLogger(__name__)


class HeadPoseEstimator:
    """
    Estimates head orientation (pitch, yaw, roll) from face landmarks.
    
    Usage:
        estimator = HeadPoseEstimator()
        result = estimator.estimate(landmarks, frame_width=640, frame_height=480)
        print(f"Yaw: {result.yaw:.1f}, Pitch: {result.pitch:.1f}, Roll: {result.roll:.1f}")
    """
    
    # 3D model points for a canonical face (centered at nose tip)
    # Units are arbitrary but proportional to real face dimensions
    MODEL_POINTS = np.array([
        (0.0, 0.0, 0.0),          # Nose tip (index 1)
        (0.0, -63.6, -12.5),      # Chin (index 199)
        (-43.3, 32.7, -26.0),     # Left eye outer (index 33)
        (43.3, 32.7, -26.0),      # Right eye outer (index 263)
        (-28.9, -28.9, -24.1),    # Left mouth corner (index 61)
        (28.9, -28.9, -24.1),     # Right mouth corner (index 291)
    ], dtype=np.float64)
    
    # Corresponding MediaPipe landmark indices
    LANDMARK_INDICES = [1, 199, 33, 263, 61, 291]
    
    def __init__(self, smoothing_alpha: float = 0.4):
        """
        Args:
            smoothing_alpha: EMA smoothing factor for pose angles.
                Higher = more responsive, Lower = smoother.
        """
        self._alpha = smoothing_alpha
        self._smoothed_pitch: Optional[float] = None
        self._smoothed_yaw: Optional[float] = None
        self._smoothed_roll: Optional[float] = None
        
        # Cache camera matrix (recomputed only when resolution changes)
        self._cached_camera_matrix: Optional[np.ndarray] = None
        self._cached_resolution: Optional[Tuple[int, int]] = None
        
        logger.info(f"HeadPoseEstimator initialized: alpha={smoothing_alpha}")
    
    def estimate(
        self,
        landmarks: list,
        frame_width: int,
        frame_height: int,
    ) -> HeadPoseResult:
        """
        Estimate head pose from face landmarks.
        
        Args:
            landmarks: List of NormalizedLandmark objects from FaceMesh.
            frame_width: Frame width in pixels.
            frame_height: Frame height in pixels.
        
        Returns:
            HeadPoseResult with pitch, yaw, roll in degrees.
        """
        if not landmarks:
            return HeadPoseResult()
        
        try:
            # Get 2D image points from landmarks
            image_points = np.array([
                (
                    landmarks[idx].x * frame_width,
                    landmarks[idx].y * frame_height,
                )
                for idx in self.LANDMARK_INDICES
            ], dtype=np.float64)
            
            # Get or compute camera matrix
            camera_matrix = self._get_camera_matrix(frame_width, frame_height)
            
            # Assume no lens distortion (reasonable for Pi Camera)
            dist_coeffs = np.zeros((4, 1), dtype=np.float64)
            
            # Solve PnP
            success, rotation_vec, translation_vec = cv2.solvePnP(
                self.MODEL_POINTS,
                image_points,
                camera_matrix,
                dist_coeffs,
                flags=cv2.SOLVEPNP_ITERATIVE,
            )
            
            if not success:
                logger.warning("solvePnP failed")
                return HeadPoseResult()
            
            # Convert rotation vector to rotation matrix
            rotation_mat, _ = cv2.Rodrigues(rotation_vec)
            
            # Extract Euler angles from rotation matrix
            pitch, yaw, roll = self._rotation_matrix_to_euler(rotation_mat)
            
            # Apply temporal smoothing
            pitch, yaw, roll = self._smooth_angles(pitch, yaw, roll)
            
            return HeadPoseResult(
                pitch=pitch,
                yaw=yaw,
                roll=roll,
            )
            
        except Exception as e:
            logger.warning(f"Head pose estimation error: {e}")
            return HeadPoseResult()
    
    def _get_camera_matrix(self, width: int, height: int) -> np.ndarray:
        """
        Get or compute the camera intrinsic matrix.
        
        We approximate:
            focal_length ≈ width (typical for webcams/Pi Camera)
            cx, cy = image center
        
        This is cached and only recomputed when resolution changes.
        """
        resolution = (width, height)
        if self._cached_resolution == resolution and self._cached_camera_matrix is not None:
            return self._cached_camera_matrix
        
        focal_length = width
        cx = width / 2.0
        cy = height / 2.0
        
        self._cached_camera_matrix = np.array([
            [focal_length, 0, cx],
            [0, focal_length, cy],
            [0, 0, 1],
        ], dtype=np.float64)
        
        self._cached_resolution = resolution
        return self._cached_camera_matrix
    
    @staticmethod
    def _rotation_matrix_to_euler(R: np.ndarray) -> Tuple[float, float, float]:
        """
        Convert 3x3 rotation matrix to Euler angles (pitch, yaw, roll).
        
        Uses the ZYX (Tait-Bryan) convention:
            1. Roll  (rotation around Z axis)
            2. Yaw   (rotation around Y axis) 
            3. Pitch (rotation around X axis)
        
        Returns:
            (pitch, yaw, roll) in degrees.
        """
        sy = np.sqrt(R[0, 0] ** 2 + R[1, 0] ** 2)
        
        singular = sy < 1e-6
        
        if not singular:
            pitch = np.degrees(np.arctan2(R[2, 1], R[2, 2]))
            yaw = np.degrees(np.arctan2(-R[2, 0], sy))
            roll = np.degrees(np.arctan2(R[1, 0], R[0, 0]))
        else:
            pitch = np.degrees(np.arctan2(-R[1, 2], R[1, 1]))
            yaw = np.degrees(np.arctan2(-R[2, 0], sy))
            roll = 0.0
        
        return (pitch, yaw, roll)
    
    def _smooth_angles(
        self, pitch: float, yaw: float, roll: float
    ) -> Tuple[float, float, float]:
        """
        Apply EMA smoothing to reduce jitter in pose angles.
        """
        if self._smoothed_pitch is None:
            self._smoothed_pitch = pitch
            self._smoothed_yaw = yaw
            self._smoothed_roll = roll
        else:
            self._smoothed_pitch = (
                self._alpha * pitch + (1 - self._alpha) * self._smoothed_pitch
            )
            self._smoothed_yaw = (
                self._alpha * yaw + (1 - self._alpha) * self._smoothed_yaw
            )
            self._smoothed_roll = (
                self._alpha * roll + (1 - self._alpha) * self._smoothed_roll
            )
        
        return (self._smoothed_pitch, self._smoothed_yaw, self._smoothed_roll)
    
    def reset(self) -> None:
        """Reset smoothing state."""
        self._smoothed_pitch = None
        self._smoothed_yaw = None
        self._smoothed_roll = None
