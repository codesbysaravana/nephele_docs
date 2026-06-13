"""
FaceMesh Detection using MediaPipe Tasks API (FaceLandmarker).

MediaPipe FaceLandmarker provides 478 3D face landmarks including
iris landmarks. This gives us:

- Full face geometry for head pose estimation via solvePnP
- Iris landmarks for gaze/eye contact detection
- Lip landmarks for speech detection (future use)
- Eyebrow landmarks for expression analysis (future use)

Key Landmark Groups:
    Face Oval: 10, 338, 297, 332, 284, 251, 389, 356, 454, 323, ...
    Left Eye:  33, 7, 163, 144, 145, 153, 154, 155, 133, 173, ...
    Right Eye: 362, 382, 381, 380, 374, 373, 390, 249, 263, 466, ...
    Left Iris: 468, 469, 470, 471, 472
    Right Iris: 473, 474, 475, 476, 477
    Nose Tip:  1
    Chin:      199

Performance on Pi 4:
    - ~15ms per frame with iris refinement
    - ~10ms per frame without
    - Memory: ~50MB

Note: MediaPipe 0.10.35+ uses the Tasks API (FaceLandmarker).
Model files are downloaded automatically on first use.
"""

import cv2
import os
import logging
import urllib.request
import numpy as np
import mediapipe as mp
from typing import Optional, List, NamedTuple

logger = logging.getLogger(__name__)

# Model download URL and cache location
_MODEL_URL = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/latest/face_landmarker.task"
_MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models_cache")
_MODEL_PATH = os.path.join(_MODELS_DIR, "face_landmarker.task")


def _ensure_model() -> str:
    """Download face landmarker model if not cached. Returns path to model file."""
    if os.path.exists(_MODEL_PATH):
        return _MODEL_PATH
    os.makedirs(_MODELS_DIR, exist_ok=True)
    logger.info(f"Downloading face landmarker model to {_MODEL_PATH}...")
    urllib.request.urlretrieve(_MODEL_URL, _MODEL_PATH)
    logger.info("Face landmarker model downloaded successfully")
    return _MODEL_PATH


class _LandmarkProxy:
    """
    Lightweight proxy for MediaPipe NormalizedLandmark.
    
    The Tasks API returns landmarks as NormalizedLandmark objects.
    This proxy ensures a consistent interface across API versions
    and allows mock creation in tests.
    """
    __slots__ = ('x', 'y', 'z')
    
    def __init__(self, x: float, y: float, z: float = 0.0):
        self.x = x
        self.y = y
        self.z = z


class FaceMeshDetector:
    """
    MediaPipe FaceLandmarker detector for landmark extraction.
    
    Extracts 478 landmarks with 3D coordinates.
    
    Usage:
        mesh = FaceMeshDetector()
        landmarks = mesh.detect(frame)
        if landmarks:
            # landmarks is a list of objects with .x, .y, .z
            nose_tip = landmarks[1]
            print(f"Nose at: ({nose_tip.x}, {nose_tip.y}, {nose_tip.z})")
    """
    
    # Key landmark indices for reuse across the pipeline
    NOSE_TIP = 1
    CHIN = 199
    LEFT_EYE_OUTER = 33
    RIGHT_EYE_OUTER = 263
    LEFT_MOUTH = 61
    RIGHT_MOUTH = 291
    FOREHEAD = 10
    
    # Iris landmark indices
    LEFT_IRIS = [468, 469, 470, 471, 472]   # Center, top, right, bottom, left
    RIGHT_IRIS = [473, 474, 475, 476, 477]  # Center, top, right, bottom, left
    
    # Eye corner landmarks for gaze calculation
    LEFT_EYE_INNER = 133
    LEFT_EYE_OUTER_CORNER = 33
    RIGHT_EYE_INNER = 362
    RIGHT_EYE_OUTER_CORNER = 263
    
    # Eye contour for eye aspect ratio
    LEFT_EYE_CONTOUR = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
    RIGHT_EYE_CONTOUR = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
    
    def __init__(
        self,
        max_faces: int = 1,
        refine_landmarks: bool = True,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
    ):
        """
        Args:
            max_faces: Maximum number of faces to detect.
                For interview robot, 1 is optimal for performance.
            refine_landmarks: If True, includes iris landmarks (478 total).
                Required for eye contact detection.
            min_detection_confidence: Threshold for initial face detection.
            min_tracking_confidence: Threshold for landmark tracking between frames.
                Higher = more accurate but may lose tracking more often.
        """
        self._max_faces = max_faces
        self._refine_landmarks = refine_landmarks
        self._landmarker = None
        
        # Initialize MediaPipe FaceLandmarker (Tasks API)
        model_path = _ensure_model()
        
        from mediapipe.tasks.python import BaseOptions
        from mediapipe.tasks.python.vision import (
            FaceLandmarker,
            FaceLandmarkerOptions,
        )
        
        base_options = BaseOptions(model_asset_path=model_path)
        options = FaceLandmarkerOptions(
            base_options=base_options,
            num_faces=max_faces,
            min_face_detection_confidence=min_detection_confidence,
            min_face_presence_confidence=min_tracking_confidence,
            min_tracking_confidence=min_tracking_confidence,
            output_face_blendshapes=False,
            output_facial_transformation_matrixes=False,
        )
        self._landmarker = FaceLandmarker.create_from_options(options)
        
        logger.info(
            f"FaceMeshDetector initialized: max_faces={max_faces}, "
            f"refine_landmarks={refine_landmarks}"
        )
    
    def detect(self, frame: np.ndarray) -> Optional[list]:
        """
        Detect face landmarks in the given frame.
        
        Args:
            frame: BGR image from camera.
        
        Returns:
            List of landmark proxy objects with .x, .y, .z attributes,
            or None if no face detected.
            
            Each landmark has:
                .x: horizontal position [0, 1] (left to right)
                .y: vertical position [0, 1] (top to bottom)
                .z: depth (roughly proportional to x, negative = closer)
        """
        if self._landmarker is None:
            return None
        
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Create MediaPipe Image
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        
        # Run FaceLandmarker
        results = self._landmarker.detect(mp_image)
        
        if not results.face_landmarks:
            return None
        
        # Convert to proxy objects for consistent interface
        landmarks = [
            _LandmarkProxy(lm.x, lm.y, lm.z)
            for lm in results.face_landmarks[0]
        ]
        
        return landmarks
    
    def get_landmark_pixel_coords(
        self,
        landmarks: list,
        index: int,
        frame_width: int,
        frame_height: int,
    ) -> tuple:
        """
        Convert a normalized landmark to pixel coordinates.
        
        Args:
            landmarks: List of landmark objects.
            index: Landmark index.
            frame_width: Frame width in pixels.
            frame_height: Frame height in pixels.
        
        Returns:
            (x, y) tuple in pixel coordinates.
        """
        lm = landmarks[index]
        return (
            int(lm.x * frame_width),
            int(lm.y * frame_height),
        )
    
    def get_iris_landmarks(
        self, landmarks: list
    ) -> Optional[dict]:
        """
        Extract iris landmark data from the full landmark set.
        
        Returns:
            Dictionary with left and right iris data, or None if
            fewer than 478 landmarks available.
            
            {
                'left_iris_center': landmark,
                'right_iris_center': landmark,
                'left_iris_points': [5 landmarks],
                'right_iris_points': [5 landmarks],
                'left_eye_inner': landmark,
                'left_eye_outer': landmark,
                'right_eye_inner': landmark,
                'right_eye_outer': landmark,
            }
        """
        if not self._refine_landmarks or len(landmarks) < 478:
            return None
        
        return {
            'left_iris_center': landmarks[self.LEFT_IRIS[0]],
            'right_iris_center': landmarks[self.RIGHT_IRIS[0]],
            'left_iris_points': [landmarks[i] for i in self.LEFT_IRIS],
            'right_iris_points': [landmarks[i] for i in self.RIGHT_IRIS],
            'left_eye_inner': landmarks[self.LEFT_EYE_INNER],
            'left_eye_outer': landmarks[self.LEFT_EYE_OUTER_CORNER],
            'right_eye_inner': landmarks[self.RIGHT_EYE_INNER],
            'right_eye_outer': landmarks[self.RIGHT_EYE_OUTER_CORNER],
        }
    
    def release(self) -> None:
        """Release MediaPipe resources."""
        if hasattr(self, '_landmarker') and self._landmarker is not None:
            self._landmarker.close()
            self._landmarker = None
            logger.info("FaceMeshDetector released")
    
    def __enter__(self) -> 'FaceMeshDetector':
        return self
    
    def __exit__(self, *args) -> None:
        self.release()
    
    def __del__(self) -> None:
        self.release()
