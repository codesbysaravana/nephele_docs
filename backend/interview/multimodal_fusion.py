"""
Nephele Interview Engine — Multi-Modal Fusion Engine.

Processes high-frequency vision and audio signals, maintaining rolling
windows to detect behavioral trends (e.g., sustained loss of engagement,
nervousness markers) that the orchestrator should react to.
"""

import collections
import logging
from typing import List, Optional

from backend.models.domain import MultiModalSignals, VisionSnapshot

logger = logging.getLogger(__name__)


class MultiModalFusionEngine:
    """
    Analyzes live multi-modal metrics to detect behavioral patterns.
    """

    def __init__(self, history_capacity: int = 100):
        """
        Args:
            history_capacity: How many recent vision frames to buffer for 
                              trend analysis.
        """
        self.engagement_buffer = collections.deque(maxlen=history_capacity)
        self.eye_contact_buffer = collections.deque(maxlen=history_capacity)
        self.face_visible_buffer = collections.deque(maxlen=history_capacity)

    def process_vision_frame(
        self, 
        signals: MultiModalSignals, 
        eye_contact: float, 
        engagement: float, 
        yaw: float, 
        pitch: float, 
        roll: float, 
        face_visible: bool
    ) -> None:
        """
        Updates the current answer's snapshot AND the engine's trend buffers.
        """
        # 1. Update the current answer window snapshot (online mean)
        signals.vision.update_from_frame(
            eye_contact=eye_contact,
            engagement=engagement,
            yaw=yaw,
            pitch=pitch,
            roll=roll,
            face_visible=face_visible
        )

        # 2. Update the trend buffers
        self.engagement_buffer.append(engagement)
        self.eye_contact_buffer.append(eye_contact)
        self.face_visible_buffer.append(face_visible)

    def analyze_behavioral_trends(self) -> dict:
        """
        Analyze the buffered history for concerning or notable trends.
        
        Returns a dictionary of boolean flags representing detected behaviors.
        """
        trends = {
            "sustained_engagement_drop": False,
            "poor_eye_contact": False,
            "face_lost": False,
            "nervous_movement": False,
        }

        if len(self.engagement_buffer) < 10:
            return trends  # Not enough data yet

        # Face Lost detection
        # If the face was visible less than 50% of the time in the recent buffer
        visible_ratio = sum(self.face_visible_buffer) / len(self.face_visible_buffer)
        if visible_ratio < 0.5:
            trends["face_lost"] = True

        # Sustained Engagement Drop
        # If the average engagement over the buffer is below 40
        avg_eng = sum(self.engagement_buffer) / len(self.engagement_buffer)
        if avg_eng < 40.0:
            trends["sustained_engagement_drop"] = True

        # Poor Eye Contact
        avg_eye = sum(self.eye_contact_buffer) / len(self.eye_contact_buffer)
        if avg_eye < 30.0:
            trends["poor_eye_contact"] = True

        return trends

    def compute_audio_confidence(self, wpm: float, silence_ratio: float, filler_ratio: float) -> float:
        """
        Compute an audio-only confidence score based on speech pace and hesitations.
        """
        # WPM scoring: peak at 150 WPM
        if wpm <= 0:
            wpm_score = 0.0
        else:
            deviation = abs(wpm - 150) / 100.0
            wpm_score = max(0.0, 1.0 - deviation) * 100.0

        silence_score = max(0.0, (1.0 - silence_ratio)) * 100.0
        filler_score = max(0.0, (1.0 - filler_ratio * 5.0)) * 100.0

        return 0.40 * wpm_score + 0.30 * silence_score + 0.30 * filler_score

    def clear_buffers(self) -> None:
        """Clear historical buffers (useful between rounds)."""
        self.engagement_buffer.clear()
        self.eye_contact_buffer.clear()
        self.face_visible_buffer.clear()
