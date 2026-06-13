"""
Face Detection using MediaPipe Tasks API.

Uses MediaPipe's Face Detection solution which is a lightweight model
optimized for mobile/edge devices. It provides:
- Ultra-fast detection (~2ms on Pi 4 at 128x128 input)
- 6 facial keypoints (for rough pose estimation)
- Bounding box with confidence score

We use the short-range model which is optimized for
faces within 2 meters of the camera — perfect for an interview setting.

Performance on Pi 4:
- ~5ms per detection at min_detection_confidence=0.5
- Very low memory footprint (~20MB)

Note: MediaPipe 0.10.35+ uses the Tasks API. Model files (.task) are
downloaded automatically on first use and cached in the vision/models_cache/ dir.
"""

import cv2
import os
import logging
import urllib.request
import numpy as np
import mediapipe as mp
from typing import Optional, Tuple

from ..models.metrics import FaceDetectionResult

logger = logging.getLogger(__name__)

# Model download URL and cache location
_MODEL_URL = "https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/latest/blaze_face_short_range.tflite"
_MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models_cache")
_MODEL_PATH = os.path.join(_MODELS_DIR, "blaze_face_short_range.tflite")


def _ensure_model() -> str:
    """Download face detection model if not cached. Returns path to model file."""
    if os.path.exists(_MODEL_PATH):
        return _MODEL_PATH
    os.makedirs(_MODELS_DIR, exist_ok=True)
    logger.info(f"Downloading face detection model to {_MODEL_PATH}...")
    urllib.request.urlretrieve(_MODEL_URL, _MODEL_PATH)
    logger.info("Face detection model downloaded successfully")
    return _MODEL_PATH


class FaceDetector:
    """
    MediaPipe-based face detector optimized for Raspberry Pi.
    
    Usage:
        detector = FaceDetector(min_confidence=0.5)
        result = detector.detect(frame)
        if result.face_visible:
            print(f"Face found with {result.confidence:.0%} confidence")
    """
    
    def __init__(
        self,
        min_confidence: float = 0.5,
    ):
        """
        Args:
            min_confidence: Minimum detection confidence threshold [0.0, 1.0].
                Lower values catch more faces but increase false positives.
        """
        self._min_confidence = min_confidence
        self._detector = None
        
        # Initialize MediaPipe Face Detection (Tasks API)
        model_path = _ensure_model()
        
        from mediapipe.tasks.python import BaseOptions
        from mediapipe.tasks.python.vision import (
            FaceDetector as MPFaceDetector,
            FaceDetectorOptions,
        )
        
        base_options = BaseOptions(model_asset_path=model_path)
        options = FaceDetectorOptions(
            base_options=base_options,
            min_detection_confidence=self._min_confidence,
        )
        self._detector = MPFaceDetector.create_from_options(options)
        
        logger.info(
            f"FaceDetector initialized: confidence={min_confidence}"
        )
    
    def detect(self, frame: np.ndarray) -> FaceDetectionResult:
        """
        Detect a face in the given frame.
        
        Args:
            frame: BGR image from camera.
        
        Returns:
            FaceDetectionResult with face_visible, confidence, and bounding_box.
            If multiple faces are detected, returns the one with highest confidence.
        """
        if self._detector is None:
            return FaceDetectionResult(face_visible=False)
        
        # Convert BGR to RGB (MediaPipe expects RGB)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Create MediaPipe Image
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        
        # Run detection
        results = self._detector.detect(mp_image)
        
        if not results.detections:
            return FaceDetectionResult(face_visible=False)
        
        # Get the detection with highest confidence
        best_detection = max(
            results.detections,
            key=lambda d: d.categories[0].score
        )
        
        confidence = best_detection.categories[0].score
        
        # Extract bounding box in pixel coordinates
        h, w = frame.shape[:2]
        bbox = best_detection.bounding_box
        
        x = max(0, bbox.origin_x)
        y = max(0, bbox.origin_y)
        box_w = min(bbox.width, w - x)
        box_h = min(bbox.height, h - y)
        
        return FaceDetectionResult(
            face_visible=True,
            confidence=float(confidence),
            bounding_box=(x, y, box_w, box_h),
        )
    
    def release(self) -> None:
        """Release MediaPipe resources."""
        if hasattr(self, '_detector') and self._detector is not None:
            self._detector.close()
            self._detector = None
            logger.info("FaceDetector released")
    
    def __enter__(self) -> 'FaceDetector':
        return self
    
    def __exit__(self, *args) -> None:
        self.release()
    
    def __del__(self) -> None:
        self.release()
