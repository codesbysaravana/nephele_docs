from dataclasses import dataclass
from typing import Optional, Tuple
from datetime import datetime
import json


@dataclass
class FaceDetectionResult:
    """Result from face detection pipeline."""
    face_visible: bool = False
    confidence: float = 0.0
    bounding_box: Optional[Tuple[int, int, int, int]] = None  # x, y, w, h
    
    def to_dict(self) -> dict:
        return {
            "face_visible": self.face_visible,
            "confidence": round(self.confidence, 2),
            "bounding_box": list(self.bounding_box) if self.bounding_box else None
        }


@dataclass
class EyeContactResult:
    """Result from eye contact detection."""
    eye_contact: bool = False
    eye_contact_score: float = 0.0  # 0-100 normalized
    gaze_center: Optional[Tuple[float, float]] = None
    left_right_ratio: float = 0.5  # 0=far left, 0.5=center, 1=far right
    up_down_ratio: float = 0.5    # 0=far up, 0.5=center, 1=far down
    
    def to_dict(self) -> dict:
        return {
            "eye_contact": self.eye_contact,
            "eye_contact_score": round(self.eye_contact_score, 1),
            "gaze_center": list(self.gaze_center) if self.gaze_center else None,
            "left_right_ratio": round(self.left_right_ratio, 3),
            "up_down_ratio": round(self.up_down_ratio, 3)
        }


@dataclass
class HeadPoseResult:
    """Result from head pose estimation."""
    pitch: float = 0.0  # Up/down rotation in degrees
    yaw: float = 0.0    # Left/right rotation in degrees
    roll: float = 0.0   # Tilt rotation in degrees
    
    def to_dict(self) -> dict:
        return {
            "pitch": round(self.pitch, 1),
            "yaw": round(self.yaw, 1),
            "roll": round(self.roll, 1)
        }


@dataclass
class VisionMetrics:
    """Complete vision metrics packet sent over WebSocket."""
    timestamp: str = ""
    face_visible: bool = False
    confidence: float = 0.0
    eye_contact: bool = False
    eye_contact_score: float = 0.0
    pitch: float = 0.0
    yaw: float = 0.0
    roll: float = 0.0
    engagement_score: float = 0.0
    fps: float = 0.0
    
    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp or datetime.utcnow().isoformat(),
            "face_visible": self.face_visible,
            "confidence": round(self.confidence, 2),
            "eye_contact": self.eye_contact,
            "eye_contact_score": round(self.eye_contact_score, 1),
            "pitch": round(self.pitch, 1),
            "yaw": round(self.yaw, 1),
            "roll": round(self.roll, 1),
            "engagement_score": round(self.engagement_score, 1),
            "fps": round(self.fps, 1)
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_results(
        cls,
        face: 'FaceDetectionResult',
        eye: 'EyeContactResult',
        pose: 'HeadPoseResult',
        engagement: float,
        fps: float
    ) -> 'VisionMetrics':
        return cls(
            timestamp=datetime.utcnow().isoformat(),
            face_visible=face.face_visible,
            confidence=face.confidence,
            eye_contact=eye.eye_contact,
            eye_contact_score=eye.eye_contact_score,
            pitch=pose.pitch,
            yaw=pose.yaw,
            roll=pose.roll,
            engagement_score=engagement,
            fps=fps
        )
