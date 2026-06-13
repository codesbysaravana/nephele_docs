"""Debug overlay drawing utilities for vision pipeline visualization."""

import cv2
import numpy as np
from typing import Optional, Tuple, List
from ..models.metrics import (
    VisionMetrics,
    FaceDetectionResult,
    EyeContactResult,
    HeadPoseResult,
)


# Color palette (BGR format for OpenCV)
COLOR_GREEN = (0, 255, 0)
COLOR_RED = (0, 0, 255)
COLOR_YELLOW = (0, 255, 255)
COLOR_CYAN = (255, 255, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_ORANGE = (0, 165, 255)
COLOR_PANEL_BG = (30, 30, 30)


class OverlayDrawer:
    """
    Draws debug overlay information onto camera frames.
    
    Renders a semi-transparent HUD panel showing:
    - FPS counter
    - Face detection status + confidence
    - Eye contact score with visual bar
    - Head pose angles (yaw, pitch, roll)
    - Engagement score with visual bar
    - Face bounding box
    - Landmark visualization
    """
    
    def __init__(self, panel_width: int = 280, font_scale: float = 0.5):
        """
        Args:
            panel_width: Width of the HUD panel in pixels.
            font_scale: Font scale for text rendering.
        """
        self._panel_width = panel_width
        self._font = cv2.FONT_HERSHEY_SIMPLEX
        self._font_scale = font_scale
        self._thickness = 1
        self._line_height = 24
    
    def draw_debug_overlay(
        self,
        frame: np.ndarray,
        metrics: VisionMetrics,
        face_result: Optional[FaceDetectionResult] = None,
        landmarks: Optional[list] = None,
    ) -> np.ndarray:
        """
        Draw the complete debug overlay on a frame.
        
        Args:
            frame: BGR image from camera.
            metrics: Current vision metrics.
            face_result: Face detection result for bounding box.
            landmarks: Optional FaceMesh landmarks for visualization.
        
        Returns:
            Frame with overlay drawn (modified in-place for performance).
        """
        h, w = frame.shape[:2]
        
        # Draw semi-transparent panel background
        self._draw_panel(frame, w)
        
        # Draw metrics text
        y_offset = 20
        
        # FPS
        fps_color = COLOR_GREEN if metrics.fps >= 10 else COLOR_RED
        y_offset = self._draw_text(
            frame, f"FPS: {metrics.fps:.1f}", (10, y_offset), fps_color
        )
        
        # Separator
        y_offset = self._draw_separator(frame, y_offset, w)
        
        # Face visible
        face_color = COLOR_GREEN if metrics.face_visible else COLOR_RED
        face_text = "DETECTED" if metrics.face_visible else "NOT FOUND"
        y_offset = self._draw_text(
            frame, f"Face: {face_text}", (10, y_offset), face_color
        )
        
        # Confidence
        if metrics.face_visible:
            y_offset = self._draw_text(
                frame,
                f"Confidence: {metrics.confidence:.0%}",
                (10, y_offset),
                COLOR_WHITE,
            )
        
        # Separator
        y_offset = self._draw_separator(frame, y_offset, w)
        
        # Eye contact
        ec_color = COLOR_GREEN if metrics.eye_contact else COLOR_ORANGE
        ec_text = "YES" if metrics.eye_contact else "NO"
        y_offset = self._draw_text(
            frame, f"Eye Contact: {ec_text}", (10, y_offset), ec_color
        )
        y_offset = self._draw_progress_bar(
            frame, 10, y_offset, metrics.eye_contact_score, "EC Score"
        )
        
        # Separator
        y_offset = self._draw_separator(frame, y_offset, w)
        
        # Head pose
        y_offset = self._draw_text(
            frame, "Head Pose:", (10, y_offset), COLOR_CYAN
        )
        y_offset = self._draw_text(
            frame,
            f"  Yaw:   {metrics.yaw:+6.1f} deg",
            (10, y_offset),
            COLOR_WHITE,
        )
        y_offset = self._draw_text(
            frame,
            f"  Pitch: {metrics.pitch:+6.1f} deg",
            (10, y_offset),
            COLOR_WHITE,
        )
        y_offset = self._draw_text(
            frame,
            f"  Roll:  {metrics.roll:+6.1f} deg",
            (10, y_offset),
            COLOR_WHITE,
        )
        
        # Separator
        y_offset = self._draw_separator(frame, y_offset, w)
        
        # Engagement
        y_offset = self._draw_progress_bar(
            frame, 10, y_offset, metrics.engagement_score, "Engagement"
        )
        
        # Draw face bounding box
        if face_result and face_result.bounding_box:
            self._draw_bounding_box(frame, face_result)
        
        # Draw landmarks
        if landmarks:
            self._draw_landmarks(frame, landmarks)
        
        return frame
    
    def _draw_panel(self, frame: np.ndarray, frame_width: int) -> None:
        """Draw semi-transparent background panel."""
        overlay = frame.copy()
        cv2.rectangle(
            overlay,
            (0, 0),
            (self._panel_width, 360),
            COLOR_PANEL_BG,
            -1,
        )
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
    
    def _draw_text(
        self,
        frame: np.ndarray,
        text: str,
        pos: Tuple[int, int],
        color: Tuple[int, int, int],
    ) -> int:
        """Draw text and return next Y position."""
        cv2.putText(
            frame, text, pos, self._font,
            self._font_scale, color, self._thickness, cv2.LINE_AA
        )
        return pos[1] + self._line_height
    
    def _draw_separator(
        self, frame: np.ndarray, y: int, frame_width: int
    ) -> int:
        """Draw a horizontal separator line."""
        cv2.line(
            frame,
            (10, y + 2),
            (self._panel_width - 10, y + 2),
            (80, 80, 80),
            1,
        )
        return y + 10
    
    def _draw_progress_bar(
        self,
        frame: np.ndarray,
        x: int,
        y: int,
        value: float,
        label: str,
        max_val: float = 100.0,
    ) -> int:
        """Draw a labeled progress bar."""
        bar_width = self._panel_width - 40
        bar_height = 14
        
        # Label
        cv2.putText(
            frame, f"{label}: {value:.0f}%", (x, y),
            self._font, self._font_scale, COLOR_WHITE,
            self._thickness, cv2.LINE_AA
        )
        y += 18
        
        # Background bar
        cv2.rectangle(
            frame, (x, y), (x + bar_width, y + bar_height),
            (60, 60, 60), -1
        )
        
        # Filled portion
        fill_width = int(bar_width * min(value / max_val, 1.0))
        if value >= 70:
            bar_color = COLOR_GREEN
        elif value >= 40:
            bar_color = COLOR_YELLOW
        else:
            bar_color = COLOR_RED
        
        cv2.rectangle(
            frame, (x, y), (x + fill_width, y + bar_height),
            bar_color, -1
        )
        
        # Border
        cv2.rectangle(
            frame, (x, y), (x + bar_width, y + bar_height),
            (100, 100, 100), 1
        )
        
        return y + bar_height + 8
    
    def _draw_bounding_box(
        self, frame: np.ndarray, face_result: FaceDetectionResult
    ) -> None:
        """Draw face bounding box with confidence label."""
        if not face_result.bounding_box:
            return
        
        x, y, w, h = face_result.bounding_box
        color = COLOR_GREEN if face_result.confidence > 0.7 else COLOR_YELLOW
        
        # Corner-style bounding box (looks more modern than full rectangle)
        corner_len = min(w, h) // 5
        thickness = 2
        
        # Top-left corner
        cv2.line(frame, (x, y), (x + corner_len, y), color, thickness)
        cv2.line(frame, (x, y), (x, y + corner_len), color, thickness)
        
        # Top-right corner
        cv2.line(frame, (x + w, y), (x + w - corner_len, y), color, thickness)
        cv2.line(frame, (x + w, y), (x + w, y + corner_len), color, thickness)
        
        # Bottom-left corner
        cv2.line(frame, (x, y + h), (x + corner_len, y + h), color, thickness)
        cv2.line(frame, (x, y + h), (x, y + h - corner_len), color, thickness)
        
        # Bottom-right corner
        cv2.line(frame, (x + w, y + h), (x + w - corner_len, y + h), color, thickness)
        cv2.line(frame, (x + w, y + h), (x + w, y + h - corner_len), color, thickness)
        
        # Confidence label
        label = f"{face_result.confidence:.0%}"
        cv2.putText(
            frame, label, (x, y - 8),
            self._font, self._font_scale, color,
            self._thickness, cv2.LINE_AA
        )
    
    def _draw_landmarks(
        self,
        frame: np.ndarray,
        landmarks: list,
        radius: int = 1,
        color: Tuple[int, int, int] = COLOR_GREEN,
    ) -> None:
        """Draw FaceMesh landmarks as small dots."""
        h, w = frame.shape[:2]
        for lm in landmarks:
            x = int(lm.x * w)
            y = int(lm.y * h)
            cv2.circle(frame, (x, y), radius, color, -1)
