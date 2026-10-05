"""
Floating Live Facecam Widget for Recplay 2.0
Displays a borderless, draggable and mouse-wheel resizable webcam preview on the teacher's screen
while recording, with double-click Mirror Flip support and a direct ✕ OFF button.

Modes:
- 'face_only': Seamless body cutout with zero background, zero square and zero round frames.
- 'blur': DSLR bokeh background blur.
- 'standard': Normal framed camera.
"""

from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QImage, QPixmap, QPainter, QPainterPath, QColor, QPen, QFont, QRegion
from PyQt6.QtCore import Qt, QPoint, QRect, QRectF, pyqtSignal
import cv2
import numpy as np
from core.face_processor import FaceCamProcessor


class FloatingFacecamWidget(QWidget):
    close_requested = pyqtSignal()

    def __init__(self, size: int = 220, shape: str = "square", mode: str = "standard", parent=None):
        super().__init__(parent)
        self.face_size = size
        self.shape = shape.lower()  # "square", "circle", "rectangle"
        self.mode = mode.lower()    # "standard", "blur", "face_only"
        self.mirror_flip = True     # Mirror by default for natural presenter view
        self.face_processor = FaceCamProcessor()
        self.setFixedSize(size, size)

        # Frameless, Always on Top, Translucent background support
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setToolTip("Drag to move • Click '✕' to turn Facecam OFF • Scroll wheel to resize • Double-click to Mirror Flip")

        self.current_pixmap = None
        self.drag_position = QPoint()
        self._apply_shape_mask()

    def _apply_shape_mask(self):
        if "face" in self.mode or "cutout" in self.mode:
            # Body cutout uses transparent RGBA pixels - no hard window clipping
            self.clearMask()
        elif "circle" in self.shape:
            self.setMask(QRegion(0, 0, self.face_size, self.face_size, QRegion.RegionType.Ellipse))
        else:
            self.clearMask()

    def set_mode(self, mode: str):
        """Sets webcam mode: 'standard', 'blur', or 'face_only'."""
        self.mode = mode.lower()
        if "face" not in self.mode and "cutout" not in self.mode:
            self.setFixedSize(self.face_size, self.face_size)
        self._apply_shape_mask()
        self.update()

    def _get_close_rect(self) -> QRect:
        return QRect(self.face_size - 30, 6, 24, 24)

    def set_shape(self, shape: str):
        """Changes shape dynamically: 'square', 'circle', or 'rectangle'."""
        self.shape = shape.lower()
        self._apply_shape_mask()
        self.update()

    def set_face_size(self, size_px: int):
        """Dynamically updates the live facecam widget size in pixels."""
        size_px = max(120, min(420, int(size_px)))
        self.face_size = size_px
        self.setFixedSize(self.face_size, self.face_size)
        self._apply_shape_mask()
        self.update()

    def update_frame(self, bgr_frame):
        """Receives a BGR frame from webcam, processes mode (standard, blur, face_only), and updates widget."""
        if bgr_frame is None:
            return

        if self.mirror_flip:
            bgr_frame = cv2.flip(bgr_frame, 1)

        # 1. Body & Face Cutout ("No square and no round frame, zero background, only show body")
        if "face" in self.mode or "cutout" in self.mode or "face" in self.shape or "cutout" in self.shape:
            cutout_target = max(260, self.face_size)
            cutout_body, alpha_3ch = self.face_processor.apply_face_cutout(bgr_frame, target_size=cutout_target)
            ch, cw = cutout_body.shape[:2]
            if self.width() != cw or self.height() != ch:
                self.setFixedSize(cw, ch)
            rgb = cv2.cvtColor(cutout_body, cv2.COLOR_BGR2RGB)
            alpha_1ch = (alpha_3ch[:, :, 0] * 255.0).astype(np.uint8)
            rgba = np.ascontiguousarray(np.dstack([rgb, alpha_1ch]))
            qimg = QImage(rgba.data, cw, ch, int(rgba.strides[0]), QImage.Format.Format_RGBA8888).copy()
            self.current_pixmap = QPixmap.fromImage(qimg)
            self.update()
            return

        # 2. Background Blur (DSLR portrait bokeh, crisp body)
        if "blur" in self.mode or "blur" in self.shape:
            bgr_frame = self.face_processor.apply_background_blur(bgr_frame)

        h, w = bgr_frame.shape[:2]
        min_dim = min(h, w)
        sx = (w - min_dim) // 2
        sy = (h - min_dim) // 2
        cropped = bgr_frame[sy : sy + min_dim, sx : sx + min_dim]
        resized = cv2.resize(cropped, (self.face_size, self.face_size), interpolation=cv2.INTER_LINEAR)
        rgb = np.ascontiguousarray(cv2.cvtColor(resized, cv2.COLOR_BGR2RGB))

        qimg = QImage(rgb.data, self.face_size, self.face_size, int(rgb.strides[0]), QImage.Format.Format_RGB888).copy()
        self.current_pixmap = QPixmap.fromImage(qimg)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Body Only Cutout: Zero background, zero square/round frame, floats naturally
        if "face" in self.mode or "cutout" in self.mode or "face" in self.shape or "cutout" in self.shape:
            if self.current_pixmap:
                pw = self.current_pixmap.width()
                ph = self.current_pixmap.height()
                dx = max(0, (self.width() - pw) // 2)
                dy = max(0, self.height() - ph)
                painter.drawPixmap(dx, dy, self.current_pixmap)
        else:
            # Standard or Blur with chosen shape
            painter.fillRect(self.rect(), QColor(11, 17, 32))
            if self.current_pixmap:
                path = QPainterPath()
                pen = QPen(QColor(56, 189, 248), 4)

                if "circle" in self.shape:
                    path.addEllipse(QRectF(3.0, 3.0, float(self.face_size - 6), float(self.face_size - 6)))
                    painter.setClipPath(path)
                    painter.drawPixmap(0, 0, self.current_pixmap)
                    painter.setClipping(False)
                    painter.setPen(pen)
                    painter.drawEllipse(QRectF(3.0, 3.0, float(self.face_size - 6), float(self.face_size - 6)))
                else:
                    radius = 14.0 if "square" in self.shape else 6.0
                    path.addRoundedRect(QRectF(3.0, 3.0, float(self.face_size - 6), float(self.face_size - 6)), radius, radius)
                    painter.setClipPath(path)
                    painter.drawPixmap(0, 0, self.current_pixmap)
                    painter.setClipping(False)
                    painter.setPen(pen)
                    painter.drawRoundedRect(QRectF(3.0, 3.0, float(self.face_size - 6), float(self.face_size - 6)), radius, radius)

        # Quick close '✕' button
        close_rect = self._get_close_rect()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(220, 38, 38, 215))
        painter.drawEllipse(close_rect)
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        font = QFont("Segoe UI", 9, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(close_rect, Qt.AlignmentFlag.AlignCenter, "✕")

    def mousePressEvent(self, event):
        pos = event.position().toPoint()
        if event.button() == Qt.MouseButton.LeftButton:
            if self._get_close_rect().contains(pos):
                self.hide()
                self.close_requested.emit()
                return
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        elif event.button() == Qt.MouseButton.RightButton:
            modes = ["square", "circle", "rectangle"]
            idx = (modes.index(self.shape) + 1) % len(modes) if self.shape in modes else 0
            self.set_shape(modes[idx])

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if not self._get_close_rect().contains(event.position().toPoint()):
                self.mirror_flip = not self.mirror_flip

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)

    def wheelEvent(self, event):
        delta = 16 if event.angleDelta().y() > 0 else -16
        new_size = max(120, min(400, self.face_size + delta))
        if new_size != self.face_size:
            self.set_face_size(new_size)
