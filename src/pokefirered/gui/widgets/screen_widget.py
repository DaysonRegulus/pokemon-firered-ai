"""
High-Performance Pixel-Art Canvas Widget for PySide6.
Renders authentic GBA display and Kanto World Map crops with nearest-neighbor scaling.
"""
from typing import Optional, Tuple
import numpy as np
from PIL import Image
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QImage, QPixmap, QPainter, QColor, QPen
from PySide6.QtWidgets import QWidget, QSizePolicy


class PixelScreenWidget(QWidget):
    """
    Renders 2D numpy / PIL frame buffers with strict aspect ratio preservation
    and crisp nearest-neighbor integer scaling (no blur).
    """

    def __init__(self, title: str = "", default_size: Tuple[int, int] = (480, 320), parent=None):
        super().__init__(parent)
        self.title = title
        self.default_w, self.default_h = default_size
        self._pixmap: Optional[QPixmap] = None
        self._highlight_rect: Optional[Tuple[int, int, int, int]] = None
        self._overlay_text: str = ""

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(QSize(240, 160))
        self.setStyleSheet("background-color: #06090E; border: 1px solid #1E293B; border-radius: 6px;")

    def set_frame_numpy(self, frame: np.ndarray, bgr: bool = True):
        """Updates display from a numpy array (H, W, 3)."""
        if frame is None or frame.size == 0:
            return
        h, w, c = frame.shape
        if bgr:
            # Convert BGR to RGB for Qt
            frame_rgb = np.ascontiguousarray(frame[:, :, ::-1])
        else:
            frame_rgb = np.ascontiguousarray(frame)

        bytes_per_line = 3 * w
        qimg = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        self._pixmap = QPixmap.fromImage(qimg)
        self.update()

    def update_frame(self, frame: np.ndarray, bgr: bool = True):
        """Convenience alias for set_frame_numpy."""
        self.set_frame_numpy(frame, bgr=bgr)

    def set_overlay_text(self, text: str = ""):
        """Convenience alias for set_overlay."""
        self.set_overlay(text=text, highlight_rect=self._highlight_rect)

    def set_frame_pil(self, pil_img: Image.Image):
        """Updates display from a PIL image."""
        if pil_img is None:
            return
        if pil_img.mode != "RGB":
            pil_img = pil_img.convert("RGB")
        arr = np.array(pil_img)
        self.set_frame_numpy(arr, bgr=False)

    def set_overlay(self, text: str = "", highlight_rect: Optional[Tuple[int, int, int, int]] = None):
        """Sets subtitle text overlay and optional highlight rectangle (x, y, w, h)."""
        self._overlay_text = text
        self._highlight_rect = highlight_rect
        self.update()

    def clear(self):
        self._pixmap = None
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#06090E"))

        if self._pixmap is None or self._pixmap.isNull():
            # Draw placeholder
            painter.setPen(QColor("#475569"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, f"{self.title}\n[Standby / No Signal]")
            return

        # Scaled maintaining aspect ratio
        widget_w = self.width()
        widget_h = self.height()
        pix_w = self._pixmap.width()
        pix_h = self._pixmap.height()

        scale = min(widget_w / pix_w, widget_h / pix_h)
        target_w = int(pix_w * scale)
        target_h = int(pix_h * scale)
        target_x = (widget_w - target_w) // 2
        target_y = (widget_h - target_h) // 2

        # FastTransformation ensures crisp retro pixel art
        scaled_pixmap = self._pixmap.scaled(
            target_w, target_h,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.FastTransformation
        )
        painter.drawPixmap(target_x, target_y, scaled_pixmap)

        # Draw highlight rect if set
        if self._highlight_rect:
            rx, ry, rw, rh = self._highlight_rect
            scaled_rx = int(target_x + rx * scale)
            scaled_ry = int(target_y + ry * scale)
            scaled_rw = int(rw * scale)
            scaled_rh = int(rh * scale)
            pen = QPen(QColor("#FFD700"), 2)
            painter.setPen(pen)
            painter.drawRect(scaled_rx, scaled_ry, scaled_rw, scaled_rh)

        # Draw Title badge in top-left
        if self.title:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(15, 22, 34, 200))
            painter.drawRoundedRect(target_x + 8, target_y + 8, len(self.title) * 8 + 16, 24, 4, 4)
            painter.setPen(QColor("#00E5FF"))
            painter.drawText(target_x + 16, target_y + 24, self.title)

        # Draw overlay text in bottom-left
        if self._overlay_text:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(15, 22, 34, 210))
            painter.drawRoundedRect(target_x + 8, target_y + target_h - 32, len(self._overlay_text) * 7 + 16, 24, 4, 4)
            painter.setPen(QColor("#F8FAFC"))
            painter.drawText(target_x + 16, target_y + target_h - 16, self._overlay_text)


ScreenWidget = PixelScreenWidget

