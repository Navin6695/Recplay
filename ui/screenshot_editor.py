"""
Clipr Shot Studio - Screenshot Capture & Annotation Suite
Supports interactive cropping, buttery-smooth live pen & highlighters,
arrows, bounding boxes, text annotations, blur/redact, and instant clipboard copy.
"""

import os
import sys
import datetime
from pathlib import Path
from typing import Optional, List

from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QColorDialog, QFileDialog, QMessageBox, QScrollArea,
    QInputDialog, QFrame, QSizePolicy
)
from PyQt6.QtGui import (
    QImage, QPixmap, QPainter, QPen, QColor, QPainterPath,
    QFont, QCursor, QGuiApplication, QBrush
)
from PyQt6.QtCore import Qt, QPoint, QRect, pyqtSignal
import cv2
import numpy as np


class SnippingOverlay(QWidget):
    """Full-screen translucent overlay allowing user to drag a box to capture an area or select recording region."""
    snippet_captured = pyqtSignal(QPixmap)
    region_selected = pyqtSignal(int, int, int, int)
    cancelled = pyqtSignal()

    def __init__(self, parent=None, is_region_selector: bool = False):
        super().__init__(parent)
        self.is_region_selector = is_region_selector
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setStyleSheet("background-color: transparent;")
        self.setCursor(Qt.CursorShape.CrossCursor)

        self.full_pixmap = None
        self.raw_physical_pixmap = None
        self.display_pixmap = None
        self.start_pos = None
        self.current_pos = None
        self.is_snipping = False
        self._dpr = 1.0

    def capture_screen(self, target_screen=None):
        screen = target_screen or QGuiApplication.screenAt(QCursor.pos()) or QGuiApplication.primaryScreen()
        if not screen:
            screen = QGuiApplication.primaryScreen()
        if screen:
            geo = screen.geometry()
            self._dpr = screen.devicePixelRatio()
            raw_pix = None
            try:
                # 1. Native Qt hardware screen capture (instantaneous, captures full screen including Clipr)
                raw_pix = screen.grabWindow(0)
            except Exception:
                pass

            if not raw_pix or raw_pix.isNull():
                try:
                    # 2. MSS fallback
                    import mss
                    with mss.mss() as sct:
                        mon = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
                        shot = sct.grab(mon)
                        img_bgra = np.array(shot, dtype=np.uint8)
                        img_rgba = cv2.cvtColor(img_bgra, cv2.COLOR_BGRA2RGBA)
                        h, w, ch = img_rgba.shape
                        qimg = QImage(img_rgba.data, w, h, ch * w, QImage.Format.Format_RGBA8888).copy()
                        raw_pix = QPixmap.fromImage(qimg)
                except Exception:
                    pass

            if not raw_pix or raw_pix.isNull():
                return

            raw_pix.setDevicePixelRatio(1.0)
            self.raw_physical_pixmap = raw_pix
            self.display_pixmap = raw_pix.scaled(
                geo.width(),
                geo.height(),
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.display_pixmap.setDevicePixelRatio(1.0)
            self.full_pixmap = self.display_pixmap

            self.start_pos = None
            self.current_pos = None
            self.is_snipping = False
            self.setGeometry(geo)
            self.show()
            self.raise_()
            self.activateWindow()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_pos = event.position().toPoint()
            self.current_pos = event.position().toPoint()
            self.is_snipping = True
            self.update()
        elif event.button() == Qt.MouseButton.RightButton:
            self.is_snipping = False
            self.hide()
            self.cancelled.emit()

    def mouseMoveEvent(self, event):
        if self.is_snipping:
            self.current_pos = event.position().toPoint()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.is_snipping:
            self.is_snipping = False
            rect = QRect(self.start_pos, self.current_pos).normalized()
            rect = rect.intersected(self.rect())
            if rect.width() > 24 and rect.height() > 24 and self.raw_physical_pixmap:
                self.hide()
                sx = self.raw_physical_pixmap.width() / float(max(1, self.width()))
                sy = self.raw_physical_pixmap.height() / float(max(1, self.height()))
                rx = max(0, int(round(rect.x() * sx)))
                ry = max(0, int(round(rect.y() * sy)))
                rw = max(64, int(round(rect.width() * sx)))
                rh = max(64, int(round(rect.height() * sy)))
                if rw % 2 != 0:
                    rw -= 1
                if rh % 2 != 0:
                    rh -= 1
                self.region_selected.emit(rx, ry, rw, rh)
                phys_rect = QRect(rx, ry, rw, rh).intersected(self.raw_physical_pixmap.rect())
                cropped = self.raw_physical_pixmap.copy(phys_rect)
                cropped.setDevicePixelRatio(1.0)
                self.snippet_captured.emit(cropped)
            elif self.is_region_selector:
                self.start_pos = None
                self.current_pos = None
                self.update()
            elif self.raw_physical_pixmap:
                self.hide()
                full_copy = QPixmap(self.raw_physical_pixmap)
                full_copy.setDevicePixelRatio(1.0)
                self.snippet_captured.emit(full_copy)

    def paintEvent(self, event):
        if not self.display_pixmap:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.drawPixmap(self.rect(), self.display_pixmap)

        dim_brush = QBrush(QColor(0, 0, 0, 135))
        painter.fillRect(self.rect(), dim_brush)

        banner_rect = QRect((self.width() - 560) // 2, 18, 560, 42)
        painter.setBrush(QColor(15, 23, 42, 235))
        painter.setPen(QPen(QColor(16, 185, 129) if self.is_region_selector else QColor(0, 240, 255), 2))
        painter.drawRoundedRect(banner_rect, 8, 8)
        painter.setPen(QColor(248, 250, 252))
        painter.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        banner_txt = "📐 Click & DRAG Mouse to Select Recording Area (ESC / Right-Click to Cancel)" if self.is_region_selector else "📸 Click & DRAG Mouse to Capture Screenshot (Full Screen 1:1 - ESC to Cancel)"
        painter.drawText(banner_rect, Qt.AlignmentFlag.AlignCenter, banner_txt)

        if self.start_pos and self.current_pos:
            r = QRect(self.start_pos, self.current_pos).normalized().intersected(self.rect())
            if r.width() > 2 and r.height() > 2:
                painter.drawPixmap(r, self.display_pixmap, r)
                border_color = QColor(16, 185, 129) if self.is_region_selector else QColor(0, 240, 255)
                border_pen = QPen(border_color, 3, Qt.PenStyle.SolidLine)
                painter.setPen(border_pen)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawRect(r)

                sx = self.raw_physical_pixmap.width() / float(max(1, self.width())) if self.raw_physical_pixmap else self._dpr
                sy = self.raw_physical_pixmap.height() / float(max(1, self.height())) if self.raw_physical_pixmap else self._dpr
                pw = int(round(r.width() * sx))
                ph = int(round(r.height() * sy))
                lbl_rect = QRect(r.x(), max(4, r.y() - 30), 185, 26)
                painter.setBrush(border_color)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRoundedRect(lbl_rect, 5, 5)
                painter.setPen(QColor(5, 13, 26))
                painter.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
                painter.drawText(lbl_rect, Qt.AlignmentFlag.AlignCenter, f"📐 {pw} × {ph} px")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.is_snipping = False
            self.hide()
            self.cancelled.emit()


class ScreenshotCanvas(QWidget):
    """Interactive canvas with real-time freehand drawing, cropping, and annotations."""
    image_modified = pyqtSignal()

    def __init__(self, pixmap: QPixmap, parent=None):
        super().__init__(parent)
        clean_pix = QPixmap(pixmap)
        clean_pix.setDevicePixelRatio(1.0)
        # Fit large high-DPI captures smoothly within the editor view so the entire captured area is visible without zoom
        screen = QGuiApplication.primaryScreen()
        avail = screen.availableGeometry() if screen else QRect(0, 0, 1536, 864)
        max_w = max(1200, int(avail.width() * 0.88))
        max_h = max(900, int(avail.height() * 0.85))
        if clean_pix.width() > max_w or clean_pix.height() > max_h:
            clean_pix = clean_pix.scaled(
                max_w, max_h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
            clean_pix.setDevicePixelRatio(1.0)

        self.base_pixmap = QPixmap(clean_pix)
        self.current_pixmap = QPixmap(clean_pix)
        self.undo_stack: List[QPixmap] = [QPixmap(clean_pix)]

        # Tools: 'pen', 'highlighter', 'arrow', 'rect', 'text', 'blur', 'crop'
        self.tool = "pen"
        self.pen_color = QColor(239, 68, 68)  # Default Clipr Red
        self.pen_width = 4
        self.is_action_active = False

        self.start_point = None
        self.last_point = None
        self.current_point = None

        self.crop_rect = None

        self.setFixedSize(self.current_pixmap.size())
        self.setCursor(Qt.CursorShape.CrossCursor)

    def set_image(self, pixmap: QPixmap):
        clean_pix = QPixmap(pixmap)
        clean_pix.setDevicePixelRatio(1.0)
        self.base_pixmap = QPixmap(clean_pix)
        self.current_pixmap = QPixmap(clean_pix)
        self.undo_stack = [QPixmap(clean_pix)]
        self.setFixedSize(self.current_pixmap.size())
        self.update()

    def push_undo(self):
        self.undo_stack.append(QPixmap(self.current_pixmap))
        if len(self.undo_stack) > 30:
            self.undo_stack.pop(0)

    def undo(self):
        if len(self.undo_stack) > 1:
            self.undo_stack.pop()
            self.current_pixmap = QPixmap(self.undo_stack[-1])
            self.crop_rect = None
            self.setFixedSize(self.current_pixmap.size())
            self.update()
            self.image_modified.emit()

    def set_tool(self, tool_name: str):
        self.tool = tool_name
        if tool_name == "crop":
            self.setCursor(Qt.CursorShape.CrossCursor)
        elif tool_name in ("pen", "highlighter"):
            self.setCursor(Qt.CursorShape.CrossCursor)
        elif tool_name == "text":
            self.setCursor(Qt.CursorShape.IBeamCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def apply_crop(self):
        """Crops image to current selected crop box."""
        if self.crop_rect and self.crop_rect.width() > 10 and self.crop_rect.height() > 10:
            self.push_undo()
            self.current_pixmap = self.current_pixmap.copy(self.crop_rect)
            self.crop_rect = None
            self.setFixedSize(self.current_pixmap.size())
            self.update()
            self.image_modified.emit()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_action_active = True
            self.start_point = event.pos()
            self.last_point = event.pos()
            self.current_point = event.pos()

            if self.tool in ("pen", "highlighter"):
                # Save undo state at beginning of stroke
                self.push_undo()

            elif self.tool == "text":
                self._handle_text_tool(event.pos())
                self.is_action_active = False

    def mouseMoveEvent(self, event):
        if not self.is_action_active:
            return

        self.current_point = event.pos()

        if self.tool in ("pen", "highlighter"):
            # Paint directly onto pixmap immediately for butter-smooth freehand drawing!
            painter = QPainter(self.current_pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            if self.tool == "highlighter":
                # Semi-transparent highlighter
                hl_color = QColor(self.pen_color)
                hl_color.setAlpha(65)
                pen = QPen(hl_color, 24, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
            else:
                pen = QPen(self.pen_color, self.pen_width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)

            painter.setPen(pen)
            painter.drawLine(self.last_point, self.current_point)
            painter.end()

            self.last_point = self.current_point
            self.update()
            self.image_modified.emit()

        elif self.tool == "crop":
            self.crop_rect = QRect(self.start_point, self.current_point).normalized()
            self.update()

        else:
            # Shapes (box, arrow, blur): preview during drag
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.is_action_active:
            self.is_action_active = False
            self.current_point = event.pos()

            if self.tool in ("rect", "arrow", "blur"):
                self.push_undo()
                self._bake_shape_action()
                self.update()
                self.image_modified.emit()

    def _bake_shape_action(self):
        """Bakes geometric shapes onto permanent pixmap."""
        painter = QPainter(self.current_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        pen = QPen(self.pen_color, self.pen_width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)

        if self.tool == "rect":
            r = QRect(self.start_point, self.current_point).normalized()
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(r)

        elif self.tool == "arrow":
            self._draw_arrow(painter, self.start_point, self.current_point, self.pen_color, self.pen_width)

        elif self.tool == "blur":
            r = QRect(self.start_point, self.current_point).normalized()
            painter.end()
            self._apply_blur_rect(r)
            return

        painter.end()

    def _draw_arrow(self, painter: QPainter, start: QPoint, end: QPoint, color: QColor, width: int):
        import math
        painter.drawLine(start, end)
        dx = end.x() - start.x()
        dy = end.y() - start.y()
        angle = math.atan2(dy, dx)
        arrow_len = 16
        arrow_angle = math.pi / 6

        p1 = QPoint(int(end.x() - arrow_len * math.cos(angle - arrow_angle)), int(end.y() - arrow_len * math.sin(angle - arrow_angle)))
        p2 = QPoint(int(end.x() - arrow_len * math.cos(angle + arrow_angle)), int(end.y() - arrow_len * math.sin(angle + arrow_angle)))
        painter.drawLine(end, p1)
        painter.drawLine(end, p2)

    def _apply_blur_rect(self, rect: QRect):
        """Gaussian blurs the rectangle region for redaction."""
        qimg = self.current_pixmap.toImage()
        sub_img = qimg.copy(rect)
        if sub_img.width() <= 2 or sub_img.height() <= 2:
            return

        sub_img = sub_img.convertToFormat(QImage.Format.Format_RGBA8888)
        w, h = sub_img.width(), sub_img.height()
        ptr = sub_img.bits()
        ptr.setsize(sub_img.sizeInBytes())
        arr = np.frombuffer(ptr, np.uint8).reshape((h, w, 4))

        ksize = max(15, (min(w, h) // 10) * 2 + 1)
        if ksize % 2 == 0:
            ksize += 1
        blurred = cv2.GaussianBlur(arr[:, :, :3], (ksize, ksize), 0)
        arr[:, :, :3] = blurred

        new_qimg = QImage(arr.data, w, h, w * 4, QImage.Format.Format_RGBA8888)
        painter = QPainter(self.current_pixmap)
        painter.drawImage(rect.topLeft(), new_qimg)
        painter.end()

    def _handle_text_tool(self, pos: QPoint):
        text, ok = QInputDialog.getText(self, "Add Text Label", "Enter annotation text:")
        if ok and text.strip():
            self.push_undo()
            painter = QPainter(self.current_pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
            painter.setPen(self.pen_color)
            painter.drawText(pos, text.strip())
            painter.end()
            self.update()
            self.image_modified.emit()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.current_pixmap)

        # Draw drag previews for shapes
        if self.is_action_active and self.start_point and self.current_point:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            if self.tool == "rect":
                painter.setPen(QPen(self.pen_color, self.pen_width, Qt.PenStyle.SolidLine))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawRect(QRect(self.start_point, self.current_point).normalized())

            elif self.tool == "arrow":
                painter.setPen(QPen(self.pen_color, self.pen_width, Qt.PenStyle.SolidLine))
                self._draw_arrow(painter, self.start_point, self.current_point, self.pen_color, self.pen_width)

            elif self.tool == "crop":
                r = QRect(self.start_point, self.current_point).normalized()
                painter.setPen(QPen(QColor(239, 68, 68), 2, Qt.PenStyle.DashLine))
                painter.setBrush(QBrush(QColor(239, 68, 68, 35)))
                painter.drawRect(r)

            elif self.tool == "blur":
                r = QRect(self.start_point, self.current_point).normalized()
                painter.setPen(QPen(QColor(148, 163, 184), 1, Qt.PenStyle.DashLine))
                painter.setBrush(QBrush(QColor(0, 0, 0, 80)))
                painter.drawRect(r)


class ScreenshotEditorDialog(QDialog):
    """Studio window for cropping, editing, highlighting, and exporting screenshots."""

    def __init__(self, pixmap: QPixmap, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Recplay Shot Studio - Screenshot Editor")
        self.setMinimumSize(1020, 720)
        self.setStyleSheet("""
            QDialog {
                background-color: #0B1120;
                color: #F8FAFC;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton {
                background-color: #1E293B;
                color: #F8FAFC;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 9px 14px;
                font-weight: 600;
                font-size: 13px;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #334155;
                border: 1px solid #475569;
            }
            QPushButton[active="true"] {
                background-color: #DC2626;
                color: white;
                border: 1px solid #EF4444;
            }
            QPushButton#saveBtn {
                background-color: #16A34A;
                color: white;
                font-weight: bold;
            }
            QPushButton#saveBtn:hover {
                background-color: #15803D;
            }
            QPushButton#copyBtn {
                background-color: #2563EB;
                color: white;
                font-weight: bold;
            }
            QPushButton#copyBtn:hover {
                background-color: #1D4ED8;
            }
            QMessageBox {
                background-color: #071124;
                border: 2px solid #00F0FF;
            }
            QMessageBox QLabel {
                color: #FFFFFF;
                font-size: 14px;
                font-weight: bold;
                background: transparent;
            }
            QMessageBox QPushButton {
                background-color: #0284C7;
                color: #FFFFFF;
                border: 1px solid #00F0FF;
                border-radius: 8px;
                padding: 8px 18px;
                font-weight: bold;
                min-width: 90px;
            }
        """)

        self.canvas = ScreenshotCanvas(pixmap, self)
        self.canvas.image_modified.connect(self._update_status)

        self.output_dir = str(Path.home() / "Videos" / "Recplay_Recordings" / "Screenshots")
        os.makedirs(self.output_dir, exist_ok=True)

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(12)

        # 1. Top Modern Responsive Toolbar
        toolbar = QFrame()
        toolbar.setStyleSheet("background-color: #1E293B; border-radius: 12px; padding: 6px;")
        t_layout = QHBoxLayout(toolbar)
        t_layout.setContentsMargins(10, 6, 10, 6)
        t_layout.setSpacing(8)

        # Drawing Tools
        self.btn_pen = QPushButton("✏️ Pen")
        self.btn_highlighter = QPushButton("🖍️ Highlight")
        self.btn_arrow = QPushButton("➡️ Arrow")
        self.btn_box = QPushButton("🔲 Box")
        self.btn_text = QPushButton("🔤 Text")
        self.btn_blur = QPushButton("🌫️ Blur")
        self.btn_crop = QPushButton("✂️ Crop")
        self.btn_apply_crop = QPushButton("✓ Apply Crop")
        self.btn_apply_crop.setStyleSheet("background-color: #EF4444; color: white; font-weight: bold;")
        self.btn_apply_crop.setVisible(False)

        self.tool_buttons = [
            (self.btn_pen, "pen"),
            (self.btn_highlighter, "highlighter"),
            (self.btn_arrow, "arrow"),
            (self.btn_box, "rect"),
            (self.btn_text, "text"),
            (self.btn_blur, "blur"),
            (self.btn_crop, "crop"),
        ]

        for btn, name in self.tool_buttons:
            t_layout.addWidget(btn)
            btn.clicked.connect(lambda checked, n=name: self._select_tool(n))

        t_layout.addWidget(self.btn_apply_crop)
        self.btn_apply_crop.clicked.connect(self._apply_crop)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet("color: #475569;")
        t_layout.addWidget(sep)

        # Color & Undo
        self.btn_color = QPushButton("🎨 Color")
        self.btn_color.setStyleSheet("background-color: #EF4444; color: white;")
        self.btn_undo = QPushButton("↩️ Undo")
        t_layout.addWidget(self.btn_color)
        t_layout.addWidget(self.btn_undo)
        self.btn_color.clicked.connect(self._choose_color)
        self.btn_undo.clicked.connect(self.canvas.undo)

        t_layout.addStretch()

        # Copy & Save
        self.btn_copy = QPushButton("📋 Copy")
        self.btn_copy.setObjectName("copyBtn")
        self.btn_copy.clicked.connect(self._copy_to_clipboard)
        t_layout.addWidget(self.btn_copy)

        self.btn_save = QPushButton("💾 Save Image")
        self.btn_save.setObjectName("saveBtn")
        self.btn_save.clicked.connect(self._save_image)
        t_layout.addWidget(self.btn_save)

        layout.addWidget(toolbar)

        # 2. Scrollable Canvas Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(False)
        scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scroll.setStyleSheet("background-color: #0A0E1A; border: 1px solid #1E293B; border-radius: 8px;")
        scroll.setWidget(self.canvas)
        layout.addWidget(scroll, 1)

        # 3. Status Bar
        self.lbl_status = QLabel(f"Dimensions: {self.canvas.current_pixmap.width()} x {self.canvas.current_pixmap.height()} px | Tool: Pen")
        self.lbl_status.setStyleSheet("color: #64748B; font-size: 12px;")
        layout.addWidget(self.lbl_status)

        self._select_tool("pen")

    def _select_tool(self, tool_name: str):
        self.canvas.set_tool(tool_name)
        for btn, name in self.tool_buttons:
            btn.setProperty("active", "true" if name == tool_name else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        self.btn_apply_crop.setVisible(tool_name == "crop")
        self._update_status()

    def _apply_crop(self):
        self.canvas.apply_crop()
        self._select_tool("pen")

    def _update_status(self):
        w = self.canvas.current_pixmap.width()
        h = self.canvas.current_pixmap.height()
        t = self.canvas.tool.capitalize()
        self.lbl_status.setText(f"Dimensions: {w} x {h} px | Active Tool: {t}")

    def _choose_color(self):
        col = QColorDialog.getColor(self.canvas.pen_color, self, "Select Color")
        if col.isValid():
            self.canvas.pen_color = col
            self.btn_color.setStyleSheet(f"background-color: {col.name()}; color: {'#000' if col.lightness() > 128 else '#fff'};")

    def _copy_to_clipboard(self):
        clipboard = QGuiApplication.clipboard()
        clipboard.setPixmap(self.canvas.current_pixmap)
        QMessageBox.information(self, "Copied!", "Screenshot copied to clipboard!\nYou can paste it directly with Ctrl+V into WhatsApp, Telegram, Slack, or Word.")

    def _save_image(self):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = os.path.join(self.output_dir, f"Recplay_Shot_{timestamp}.png")
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Screenshot",
            default_name,
            "PNG Image (*.png);;JPEG Image (*.jpg)",
        )
        if file_path:
            self.canvas.current_pixmap.save(file_path)
            QMessageBox.information(self, "Saved!", f"Screenshot saved successfully:\n\n{file_path}")
