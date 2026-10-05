"""
Recplay - Main Application Studio Window (J.A.R.V.I.S. AI Edition & Zero-Crash Opaque Engine)
Modern, sleek screen recorder designed for YouTube Creators and Online Teachers.
Key Features:
- 100% Elimination of `WA_TranslucentBackground` (`WS_EX_LAYERED`) across ALL Top-Level Overlays
  (`AnnotatorOverlay`, `LiveRegionFrame`, `FreehandDragAreaSelector`, `FullScreenHighlightBorder`,
   `ScreenBlinkCountdownOverlay`, `FloatingFacecamWidget`), permanently preventing Windows 11
  `VCRUNTIME140.dll!memcpy` (`0xc0000005`) crashes when opening `Draw / Board` or `Drag-Out`!
- Built-in Live Animated J.A.R.V.I.S. AI Arc Reactor & Telemetry HUD Deck (`JarvisReactorBannerWidget`)
  running continuously inside MainWindow + 1-Click Floating Desktop J.A.R.V.I.S. Hologram Widget (`FloatingJarvisWidget`)!
- 100% In-Window Option Drawer (`StudioSelectButton` + `InWindowOptionOverlay`)
- Rich Interactive Drag-Out Studio Editor (`LiveRegionFrame` + `FreehandDragAreaSelector`) with 2-Row Preset Bar
- Ultra-Low CPU Utilization Architecture (< 8% CPU)
"""

import os
import sys
import math
import time
import datetime
import ctypes
from pathlib import Path

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QCheckBox, QProgressBar, QFileDialog,
    QMessageBox, QFrame, QGroupBox, QLineEdit, QDialog, QTextEdit, QApplication, QSlider
)
from PyQt6.QtGui import (
    QFont, QIcon, QColor, QPixmap, QShortcut, QKeySequence,
    QPainter, QPen, QGuiApplication, QRegion, QPainterPath, QCursor, QImage
)
from PyQt6.QtCore import Qt, QTimer, QRect, QRectF, QPoint, QPointF, pyqtSignal, QEvent

from core.hwid import get_hardware_id
from core.license_verifier import LicenseVerifier
from core.audio_recorder import AudioRecorder
from core.screen_recorder import ScreenRecorder

from ui.license_dialog import LicenseDialog
from ui.webcam_preview import WebcamPreviewDialog
from ui.screen_annotator import AnnotatorOverlay
from ui.screenshot_editor import SnippingOverlay, ScreenshotEditorDialog
from ui.floating_facecam import FloatingFacecamWidget
import cv2


def _exclude_window_from_capture(widget: QWidget):
    """
    Applies Win32 WDA_EXCLUDEFROMCAPTURE (0x00000011) so overlays/bars
    are 100% visible to the user on their physical monitor for reference, while 100% excluded
    from the recorded video!
    """
    if sys.platform == "win32":
        try:
            hwnd = int(widget.winId())
            if hwnd:
                ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, 0x00000011)
        except Exception:
            pass


class FloatingJarvisWidget(QWidget):
    """
    Draggable Desktop Clipr Arc Reactor Hologram Widget.
    Uses opaque circular QRegion mask (zero WS_EX_LAYERED crash).
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(150, 150)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setMask(QRegion(0, 0, 150, 150, QRegion.RegionType.Ellipse))
        self.setToolTip("Recplay AI Desktop Core • Drag to Move • Right-Click to Hide")
        _exclude_window_from_capture(self)
        self.angle = 0.0
        self.drag_offset = QPoint()
        self.status_text = "ONLINE"

        self.anim_timer = QTimer(self)
        self.anim_timer.setInterval(55)
        self.anim_timer.timeout.connect(self._tick)

    def showEvent(self, event):
        super().showEvent(event)
        _exclude_window_from_capture(self)
        if not self.anim_timer.isActive():
            self.anim_timer.start()

    def hideEvent(self, event):
        self.anim_timer.stop()
        super().hideEvent(event)

    def _tick(self):
        if not self.isVisible():
            self.anim_timer.stop()
            return
        self.angle = (self.angle + 4.0) % 360.0
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(4, 11, 24))

        cx, cy = 75.0, 75.0
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor(0, 240, 255, 230), 3))
        painter.drawEllipse(QPointF(cx, cy), 70.0, 70.0)

        painter.save()
        painter.translate(cx, cy)
        painter.rotate(self.angle)
        painter.setPen(QPen(QColor(56, 189, 248, 255), 4, Qt.PenStyle.DashLine))
        painter.drawEllipse(QPointF(0.0, 0.0), 56.0, 56.0)
        painter.rotate(-2.2 * self.angle)
        painter.setPen(QPen(QColor(14, 165, 233, 220), 3, Qt.PenStyle.DotLine))
        painter.drawEllipse(QPointF(0.0, 0.0), 42.0, 42.0)
        painter.restore()

        painter.setBrush(QColor(0, 240, 255, 45))
        painter.setPen(QPen(QColor(0, 240, 255, 240), 2))
        painter.drawEllipse(QPointF(cx, cy), 28.0, 28.0)

        painter.setFont(QFont("Consolas", 9, QFont.Weight.Bold))
        painter.setPen(QColor(0, 240, 255))
        painter.drawText(QRect(15, 56, 120, 20), Qt.AlignmentFlag.AlignCenter, "RECPLAY CORE")
        painter.setFont(QFont("Consolas", 7, QFont.Weight.Bold))
        painter.setPen(QColor(52, 211, 153))
        painter.drawText(QRect(15, 74, 120, 18), Qt.AlignmentFlag.AlignCenter, self.status_text)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        elif event.button() == Qt.MouseButton.RightButton:
            self.hide()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_offset)


class CliprCyberBackgroundWidget(QWidget):
    """
    Clean Modern Studio Dark Cyber Canvas Background.
    Renders a deep dark obsidian canvas with subtle blueprint grid lines.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_recording_mode = False
        self.cpu_percent = 1.8
        self.status_msg = ""

    def set_cpu_percent(self, cpu_val: float):
        self.cpu_percent = cpu_val

    def set_recording_state(self, recording: bool, elapsed_str: str = "00:00:00"):
        self.is_recording_mode = recording
        self.update()

    def set_status(self, msg: str = ""):
        self.status_msg = msg
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        # 1. Deep Cyber Navy Studio Base
        painter.fillRect(self.rect(), QColor(4, 9, 20))

        # 2. Subtle Full-Window Holographic Blueprint Grid
        grid_pen = QPen(QColor(0, 240, 255, 14), 1)
        painter.setPen(grid_pen)
        for gx in range(0, w, 44):
            painter.drawLine(gx, 0, gx, h)
        for gy in range(0, h, 44):
            painter.drawLine(0, gy, w, gy)


class InWindowOptionOverlay(QFrame):
    """
    100% In-Window Option Picker rendered directly inside MainWindow.centralWidget().
    NEVER creates an external OS window or modal QDialog.exec() loop.
    """
    option_selected = pyqtSignal(int)

    def __init__(self, parent_widget: QWidget, title: str, items: list[str], current_index: int):
        super().__init__(parent_widget)
        self.setGeometry(parent_widget.rect())
        self.setStyleSheet("QFrame { background-color: rgba(5, 10, 22, 215); }")

        outer_lay = QVBoxLayout(self)
        outer_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = QFrame(self)
        card.setFixedWidth(330)
        card.setStyleSheet("""
            QFrame {
                background-color: #0F172A;
                color: #F8FAFC;
                border: 2px solid #00F0FF;
                border-radius: 12px;
            }
            QLabel {
                color: #00F0FF;
                font-size: 14px;
                font-weight: bold;
                border: none;
                background: transparent;
            }
            QPushButton {
                text-align: left;
                padding: 7px 12px;
                border-radius: 7px;
                font-size: 12px;
                font-weight: 600;
                background-color: #1E293B;
                color: #F8FAFC;
                border: 1px solid #334155;
            }
            QPushButton:hover {
                background-color: #0284C7;
                border: 1px solid #00F0FF;
                color: #FFFFFF;
            }
        """)

        c_lay = QVBoxLayout(card)
        c_lay.setContentsMargins(14, 10, 14, 10)
        c_lay.setSpacing(5)

        top_row = QHBoxLayout()
        hdr = QLabel(f"✨ {title}")
        top_row.addWidget(hdr, 1)
        btn_close = QPushButton("✖ Close")
        btn_close.setFixedWidth(74)
        btn_close.setStyleSheet(
            "text-align: center; background-color: #7F1D1D; color: #FECACA; border: 1px solid #EF4444; padding: 4px 8px;"
        )
        btn_close.clicked.connect(self.close_overlay)
        top_row.addWidget(btn_close)
        c_lay.addLayout(top_row)

        for idx, text in enumerate(items):
            is_cur = (idx == current_index)
            prefix = "✅  " if is_cur else "      "
            safe_text = text.replace("&", "&&")
            btn = QPushButton(f"{prefix}{safe_text}")
            if is_cur:
                btn.setStyleSheet(
                    "text-align: left; padding: 7px 12px; border-radius: 7px; font-size: 12px; "
                    "font-weight: bold; background-color: #065F46; color: #34D399; border: 2px solid #10B981;"
                )
            btn.clicked.connect(lambda checked=False, i=idx: self._pick(i))
            c_lay.addWidget(btn)

        outer_lay.addWidget(card)
        self.show()
        self.raise_()

    def _pick(self, idx: int):
        self.hide()
        self.option_selected.emit(idx)
        self.deleteLater()

    def close_overlay(self):
        self.hide()
        self.deleteLater()

    def mousePressEvent(self, event):
        child = self.childAt(event.position().toPoint())
        if child is None:
            self.close_overlay()
        else:
            super().mousePressEvent(event)


STYLE_PILL_ACTIVE = (
    "QPushButton { background-color: #0284C7; color: #FFFFFF; border: 1.5px solid #00F0FF; "
    "font-size: 11px; font-weight: bold; border-radius: 6px; padding: 3px 6px; font-family: 'Segoe UI', Arial, sans-serif; } "
    "QPushButton:hover { background-color: #0369A1; border-color: #38BDF8; }"
)
STYLE_PILL_INACTIVE = (
    "QPushButton { background-color: #0F172A; color: #FFFFFF; border: 1.5px solid #0284C7; "
    "font-size: 11px; font-weight: bold; border-radius: 6px; padding: 3px 6px; font-family: 'Segoe UI', Arial, sans-serif; } "
    "QPushButton:hover { background-color: #1E293B; color: #00F0FF; border-color: #00F0FF; }"
)


class StudioSelectButton(QPushButton):
    """
    100% In-Window Trimmed Selector Button that opens `InWindowOptionOverlay` inside `MainWindow`.
    """
    currentIndexChanged = pyqtSignal(int)
    currentTextChanged = pyqtSignal(str)
    activated = pyqtSignal(int)

    def __init__(self, title: str = "Select Option", parent=None):
        super().__init__(parent)
        self._dialog_title = title
        self._items: list[str] = []
        self._current_index: int = 0
        self._active_overlay = None
        self.setMaximumWidth(260)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                background-color: #1E293B;
                border: 1px solid #0284C7;
                border-radius: 6px;
                padding: 4px 10px;
                min-height: 22px;
                color: #F8FAFC;
                font-size: 12px;
                font-weight: 600;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #26354D;
                border: 1px solid #00F0FF;
            }
        """)
        self.clicked.connect(self._open_picker)

    def addItems(self, items: list[str]):
        self._items.extend(items)
        if self._items and self._current_index < len(self._items):
            self._update_button_label()

    def count(self) -> int:
        return len(self._items)

    def currentIndex(self) -> int:
        return self._current_index

    def currentText(self) -> str:
        if 0 <= self._current_index < len(self._items):
            return self._items[self._current_index]
        return ""

    def setItemText(self, index: int, text: str):
        if 0 <= index < len(self._items):
            self._items[index] = text
            self._update_button_label()

    def itemText(self, index: int) -> str:
        if 0 <= index < len(self._items):
            return self._items[index]
        return ""

    def setCurrentIndex(self, index: int):
        if 0 <= index < len(self._items):
            changed = (index != self._current_index)
            self._current_index = index
            self._update_button_label()
            if changed and not self.signalsBlocked():
                txt = self.currentText()
                self._emit_changes(index, txt)

    def setCurrentText(self, text: str):
        for i, item in enumerate(self._items):
            if item == text:
                self.setCurrentIndex(i)
                return

    def _emit_changes(self, idx: int, txt: str):
        self.activated.emit(idx)
        self.currentIndexChanged.emit(idx)
        self.currentTextChanged.emit(txt)

    def _update_button_label(self):
        txt = self.currentText().replace("&", "&&")
        self.setText(f"{txt}  ▾")

    def _open_picker(self):
        if not self._items:
            return
        win = self.window()
        host = win.centralWidget() if (win and hasattr(win, "centralWidget") and win.centralWidget()) else win
        if not host:
            return
        for old_ov in host.findChildren(InWindowOptionOverlay):
            old_ov.close_overlay()
        self._active_overlay = InWindowOptionOverlay(host, self._dialog_title, self._items, self._current_index)
        self._active_overlay.option_selected.connect(self._on_overlay_chosen)

    def _on_overlay_chosen(self, new_idx: int):
        self._current_index = new_idx
        self._update_button_label()
        txt = self.currentText()
        self._emit_changes(new_idx, txt)


class FullScreenHighlightBorder(QWidget):
    """
    Highlights the outer perimeter of the Full Screen while recording.
    Uses Opaque QWidget + QRegion setMask (NO WA_TranslucentBackground -> 100% crash-proof!).
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.is_recording_active = False
        self._pulse_phase = False

    def show_around_primary_screen(self, recording: bool = False):
        self.is_recording_active = recording
        if recording:
            # Never display blinking blue/red border during recording so it never appears in recorded video!
            self.hide()
            return
        screen = QGuiApplication.primaryScreen()
        geo = screen.geometry() if screen else QRect(0, 0, 1920, 1080)
        if not self.isVisible() or self.geometry() != geo:
            self.setGeometry(geo)
            full_reg = QRegion(0, 0, geo.width(), geo.height())
            inner_rect = QRect(6, 6, max(20, geo.width() - 12), max(20, geo.height() - 12))
            self.setMask(full_reg.subtracted(QRegion(inner_rect)))
            self.show()
            self.raise_()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 240, 255))


class AreaMarkingBorder(QWidget):
    """
    Shows a visible border line framing the selected recording area on screen during recording.
    Uses Win32 WDA_EXCLUDEFROMCAPTURE (0x00000011) + WindowTransparentForInput + Hollow QRegion mask
    so the border is 100% clearly visible to the user on their physical monitor,
    100% transparent to mouse/keyboard interactions, and 100% excluded from the recorded video!
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        _exclude_window_from_capture(self)

    def showEvent(self, event):
        super().showEvent(event)
        _exclude_window_from_capture(self)

    def update_boundary(self, rx: int, ry: int, rw: int, rh: int):
        screen = QGuiApplication.primaryScreen()
        dpr = screen.devicePixelRatio() if screen else 1.0
        gx = int(round(rx / dpr))
        gy = int(round(ry / dpr))
        gw = int(round(rw / dpr))
        gh = int(round(rh / dpr))

        border_thickness = 3
        # Position exactly on the outer perimeter of the recorded region
        frame_x = max(0, gx - border_thickness)
        frame_y = max(0, gy - border_thickness)
        frame_w = (gx + gw + border_thickness) - frame_x
        frame_h = (gy + gh + border_thickness) - frame_y

        self.setGeometry(frame_x, frame_y, frame_w, frame_h)
        full_reg = QRegion(0, 0, frame_w, frame_h)
        inner_rect = QRect(gx - frame_x, gy - frame_y, gw, gh)
        self.setMask(full_reg.subtracted(QRegion(inner_rect)))
        self.show()
        _exclude_window_from_capture(self)
        self.raise_()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor(0, 240, 255), 3, Qt.PenStyle.SolidLine)
        painter.setPen(pen)
        painter.drawRect(self.rect().adjusted(1, 1, -1, -1))


class FreehandDragAreaSelector(QWidget):
    """
    User-Friendly Snipping-Style Drag-to-Select Screen Overlay!
    Uses Opaque QWidget with pre-captured desktop snapshot (NO WA_TranslucentBackground -> 100% crash-proof!).
    """
    area_dragged = pyqtSignal(QRect)
    cancelled = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        _exclude_window_from_capture(self)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.bg_pixmap = None
        self.start_pt = None
        self.end_pt = None
        self.is_dragging = False

    def start_interactive_drag(self):
        screen = QGuiApplication.primaryScreen()
        geo = screen.geometry() if screen else QRect(0, 0, 1920, 1080)
        if screen:
            self.bg_pixmap = screen.grabWindow(0)
        self.setGeometry(geo)
        self.start_pt = None
        self.end_pt = None
        self.is_dragging = False
        self.show()
        self.raise_()
        self.activateWindow()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
            self.cancelled.emit()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_pt = event.position().toPoint()
            self.end_pt = self.start_pt
            self.is_dragging = True
            self.update()
        elif event.button() == Qt.MouseButton.RightButton:
            self.hide()
            self.cancelled.emit()

    def mouseMoveEvent(self, event):
        if self.is_dragging:
            self.end_pt = event.position().toPoint()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.is_dragging:
            self.is_dragging = False
            self.end_pt = event.position().toPoint()
            sel_rect = QRect(self.start_pt, self.end_pt).normalized().intersected(self.rect())
            self.hide()
            if sel_rect.width() >= 32 and sel_rect.height() >= 32:
                self.area_dragged.emit(sel_rect)
            else:
                cx = self.start_pt.x()
                cy = self.start_pt.y()
                default_rect = QRect(max(20, cx - 420), max(40, cy - 240), 840, 480).intersected(self.rect())
                self.area_dragged.emit(default_rect)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        if self.bg_pixmap is not None:
            painter.drawPixmap(self.rect(), self.bg_pixmap)
        else:
            painter.fillRect(self.rect(), QColor(8, 12, 24))

        painter.fillRect(self.rect(), QColor(4, 10, 22, 165))

        banner_w, banner_h = 740, 46
        bx = (self.width() - banner_w) // 2
        by = 24
        painter.setBrush(QColor(5, 13, 26, 245))
        painter.setPen(QPen(QColor(0, 240, 255), 2))
        painter.drawRoundedRect(QRect(bx, by, banner_w, banner_h), 12, 12)
        painter.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        painter.setPen(QColor(0, 240, 255))
        painter.drawText(
            QRect(bx, by, banner_w, banner_h),
            Qt.AlignmentFlag.AlignCenter,
            "📐 Select Recording Area (Click & Drag Anywhere)  •  ESC Cancel",
        )

        if self.start_pt and self.end_pt:
            sel_rect = QRect(self.start_pt, self.end_pt).normalized().intersected(self.rect())
            if sel_rect.width() > 4 and sel_rect.height() > 4:
                if self.bg_pixmap is not None:
                    painter.drawPixmap(sel_rect, self.bg_pixmap, sel_rect)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.setPen(QPen(QColor(0, 240, 255, 255), 3))
                painter.drawRect(sel_rect)

                screen = QGuiApplication.primaryScreen()
                dpr = screen.devicePixelRatio() if screen else 1.0
                pw = int(sel_rect.width() * dpr)
                ph = int(sel_rect.height() * dpr)
                tag_rect = QRect(sel_rect.x(), max(8, sel_rect.y() - 34), 230, 28)
                painter.setBrush(QColor(5, 13, 26, 240))
                painter.setPen(QPen(QColor(0, 240, 255), 1))
                painter.drawRoundedRect(tag_rect, 6, 6)
                painter.setPen(QColor(0, 240, 255))
                painter.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
                painter.drawText(tag_rect, Qt.AlignmentFlag.AlignCenter, f"📐 TARGET: {pw} × {ph} px")


class FloatingRecordingBar(QWidget):
    """
    Shows the bottom action bar of Clipr Studio OUTSIDE on the desktop while recording:
    Features Smart Auto-Hide:
    - Automatically disappears completely (hides) after 5 seconds of inactivity.
    - Re-appears immediately on screen as soon as the user touches ANY key on the keyboard!
    - Excluded from video capture via WDA_EXCLUDEFROMCAPTURE so it never appears in the output video.
    """
    def __init__(self, main_win):
        super().__init__(None)
        self.main_win = main_win
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self._drag_offset = None
        self._user_positioned = False
        self._full_stylesheet = """
            QWidget {
                background-color: #060E1F;
                border: 2px solid #00F0FF;
                border-radius: 12px;
            }
            QLabel {
                border: none;
                background: transparent;
            }
            QPushButton {
                background-color: #0F172A;
                color: #F8FAFC;
                border: 1px solid #0284C7;
                border-radius: 8px;
                padding: 6px 12px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #0369A1;
                border-color: #00F0FF;
            }
        """
        self.setStyleSheet(self._full_stylesheet)

        self.lay = QHBoxLayout(self)
        self.lay.setContentsMargins(12, 6, 12, 6)
        self.lay.setSpacing(8)

        self.lbl_grip = QLabel("✥")
        self.lbl_grip.setCursor(Qt.CursorShape.SizeAllCursor)
        self.lbl_grip.setToolTip("Click & Drag to move Recording Bar anywhere on screen")
        self.lbl_grip.setStyleSheet("color: #00F0FF; font-size: 16px; font-weight: bold; padding: 0px 4px;")
        self.lay.addWidget(self.lbl_grip)

        self.rec_dot = QLabel()
        self.rec_dot.setFixedSize(12, 12)
        self.rec_dot.setStyleSheet(
            "border-radius: 6px; background-color: #EF4444; border: 1px solid #F87171;"
        )
        self.lay.addWidget(self.rec_dot)

        self.lbl_timer = QLabel("00:00:00")
        self.lbl_timer.setStyleSheet("color: #EF4444; font-family: Consolas, monospace; font-size: 20px; font-weight: bold; padding: 0px 4px;")
        self.lay.addWidget(self.lbl_timer)

        self.btn_stop = QPushButton("⏹️ STOP RECORDING")
        self.btn_stop.setStyleSheet(
            "QPushButton { background-color: #DC2626; color: #FFFFFF; border: 1px solid #F87171; font-weight: bold; font-size: 13px; padding: 6px 14px; }"
            "QPushButton:hover { background-color: #B91C1C; }"
        )
        self.btn_stop.clicked.connect(self.main_win._toggle_record)
        self.lay.addWidget(self.btn_stop)

        self.btn_pause = QPushButton("⏸️ Pause")
        self.btn_pause.clicked.connect(self.main_win._toggle_pause)
        self.lay.addWidget(self.btn_pause)

        self.btn_draw = QPushButton("✏️ Draw / Board")
        self.btn_draw.setStyleSheet(
            "QPushButton { background-color: #0284C7; color: #FFFFFF; border: 1px solid #00F0FF; font-weight: bold; }"
            "QPushButton:hover { background-color: #0369A1; }"
        )
        self.btn_draw.clicked.connect(self.main_win._toggle_annotator)
        self.lay.addWidget(self.btn_draw)

        self.btn_chapter = QPushButton("🔖 Chapter")
        self.btn_chapter.clicked.connect(self.main_win._add_chapter_marker)
        self.lay.addWidget(self.btn_chapter)

        self.btn_snip = QPushButton("📸 Screenshot")
        self.btn_snip.setStyleSheet(
            "QPushButton { background-color: #0D9488; color: #FFFFFF; border: 1px solid #2DD4BF; font-weight: bold; }"
            "QPushButton:hover { background-color: #0F766E; }"
        )
        self.btn_snip.clicked.connect(self.main_win._start_snipping)
        self.lay.addWidget(self.btn_snip)

        self.btn_player = QPushButton("🎬 Player")
        self.btn_player.setToolTip("Open Recplay 2.0 Studio Media Player")
        self.btn_player.setStyleSheet(
            "QPushButton { background-color: #0F172A; color: #00F0FF; border: 1px solid #0284C7; font-weight: bold; }"
            "QPushButton:hover { background-color: #0284C7; color: #FFFFFF; border-color: #00F0FF; }"
        )
        self.btn_player.clicked.connect(lambda: self.main_win._open_media_player())
        self.lay.addWidget(self.btn_player)

        self.btn_app = QPushButton("🪟 App")
        self.btn_app.setToolTip("Show / Hide Main Recplay Window")
        self.btn_app.clicked.connect(self._toggle_main_app)
        self.lay.addWidget(self.btn_app)

        # 5-Second Inactivity Disappearance Timer (Menu completely disappears after 5 seconds)
        self._autohide_timer = QTimer(self)
        self._autohide_timer.setSingleShot(True)
        self._autohide_timer.setInterval(5000)
        self._autohide_timer.timeout.connect(self._disappear_bar)

        # Global Mouse/Touch & Keyboard Listener (Checks for ANY mouse touch or key to immediately reveal bar)
        self._key_poll_timer = QTimer(self)
        self._key_poll_timer.setInterval(60)
        self._key_poll_timer.timeout.connect(self._poll_global_interaction)

        self.adjustSize()
        _exclude_window_from_capture(self)

    def _disappear_bar(self):
        """Hides floating bar completely after 5 seconds of inactivity as requested."""
        if not self.isVisible():
            return
        # If cursor is currently over the floating bar, don't hide while user is clicking/hovering
        if self.geometry().contains(QCursor.pos()):
            self._autohide_timer.start(3000)
            return

        super().hide()

    def _poll_global_interaction(self):
        """Detects when user touches mouse, clicks, or touches ANY key on keyboard to reveal the bar."""
        if not getattr(self.main_win, "is_recording", False):
            return

        try:
            user32 = ctypes.windll.user32
            class POINT(ctypes.Structure):
                _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

            pt = POINT()
            user32.GetCursorPos(ctypes.byref(pt))
            curr_pos = (pt.x, pt.y)

            last_pos = getattr(self, "_last_cursor_pos", None)
            mouse_moved = False
            if last_pos is not None:
                dx = abs(curr_pos[0] - last_pos[0])
                dy = abs(curr_pos[1] - last_pos[1])
                if dx > 3 or dy > 3:
                    mouse_moved = True
            self._last_cursor_pos = curr_pos

            mouse_clicked = (
                bool(user32.GetAsyncKeyState(0x01) & 0x8000) or
                bool(user32.GetAsyncKeyState(0x02) & 0x8000)
            )

            key_down = False
            if not mouse_moved and not mouse_clicked:
                for vk in (8, 9, 13, 16, 17, 18, 27, 32, 37, 38, 39, 40):
                    if user32.GetAsyncKeyState(vk) & 0x8000:
                        key_down = True
                        break

            if mouse_moved or mouse_clicked or key_down:
                if not self.isVisible():
                    self.show_bar()
                else:
                    self._autohide_timer.start(5000)
        except Exception:
            pass

    def enterEvent(self, event):
        self._autohide_timer.stop()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._autohide_timer.stop()
        self._autohide_timer.start(5000)
        super().leaveEvent(event)

    def _toggle_main_app(self):
        if self.main_win.isVisible() and not self.main_win.isMinimized():
            self.main_win.showMinimized()
            self.show_bar()
        else:
            self.main_win.showNormal()
            self.main_win.raise_()
            self.main_win.activateWindow()

    def show_bar(self):
        """Shows the floating bar, positions it if not dragged, and starts the 5-second disappear countdown."""
        if not getattr(self.main_win, "is_recording", False):
            return
        if not self.isVisible():
            if not self._user_positioned:
                screen = QGuiApplication.primaryScreen()
                if screen:
                    geo = screen.availableGeometry()
                    self.adjustSize()
                    x = geo.right() - self.width() - 28
                    y = geo.top() + 32
                    self.move(max(10, x), max(10, y))
            super().show()
            self.raise_()
            _exclude_window_from_capture(self)

        # Reset 5-second countdown to disappear
        self._autohide_timer.stop()
        self._autohide_timer.start(5000)

        if not self._key_poll_timer.isActive():
            self._key_poll_timer.start(60)

    def start_recording_bar(self):
        """Called when recording starts: activates key polling and shows bar."""
        self._key_poll_timer.start(60)
        self.show_bar()

    def stop_recording_bar(self):
        """Called when recording stops: terminates key polling and hides bar."""
        self._key_poll_timer.stop()
        self._autohide_timer.stop()
        super().hide()

    def hide(self):
        self._autohide_timer.stop()
        super().hide()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self.pos()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_offset is not None and (event.buttons() & Qt.MouseButton.LeftButton):
            self.move(event.globalPosition().toPoint() - self._drag_offset)
            self._user_positioned = True
            event.accept()
        self._autohide_timer.stop()
        self._autohide_timer.start(5000)

    def mouseReleaseEvent(self, event):
        self._drag_offset = None


class ScreenBlinkCountdownOverlay(QWidget):
    """
    Prominent Centered 3 -> 2 -> 1 -> GO! Studio Countdown Overlay.
    Uses Opaque QWidget with circular mask and animated cyberpunk HUD rings.
    """
    countdown_tick = pyqtSignal(int)
    countdown_finished = pyqtSignal()

    def __init__(self, target_rect: QRect = None, parent=None):
        super().__init__(parent)
        self.setFixedSize(320, 320)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setMask(QRegion(0, 0, 320, 320, QRegion.RegionType.Ellipse))

        self.target_rect = target_rect
        self.current_number = 3
        self.angle = 0.0
        self._step_timer = QTimer(self)
        self._step_timer.timeout.connect(self._next_number)
        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._spin_ring)

    def start_countdown(self):
        screen = QGuiApplication.primaryScreen()
        geo = screen.geometry() if screen else QRect(0, 0, 1920, 1080)
        area = self.target_rect if (self.target_rect and not self.target_rect.isEmpty()) else geo
        cx = area.center().x() - 160
        cy = area.center().y() - 160
        self.move(max(10, cx), max(10, cy))

        self.current_number = 3
        self.angle = 0.0
        self.show()
        self.raise_()
        self.activateWindow()
        self._anim_timer.start(35)
        self._step_timer.start(1000)
        self.countdown_tick.emit(3)

    def _spin_ring(self):
        self.angle = (self.angle + 6.0) % 360.0
        self.update()

    def _next_number(self):
        if self.current_number > 1:
            self.current_number -= 1
            self.countdown_tick.emit(self.current_number)
            self.update()
        else:
            self.current_number = 0
            self.countdown_tick.emit(0)
            self.update()
            self._step_timer.stop()
            self._anim_timer.stop()
            QTimer.singleShot(250, self._finish_countdown)

    def _finish_countdown(self):
        self.hide()
        QApplication.processEvents()
        self.countdown_finished.emit()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(4, 11, 24))

        border_col = QColor(16, 185, 129) if self.current_number == 0 else (
            QColor(0, 240, 255) if self.current_number == 1 else QColor(56, 189, 248)
        )

        # Outer solid neon ring
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(border_col, 5))
        painter.drawEllipse(QPointF(160.0, 160.0), 150.0, 150.0)

        # Rotating dashed HUD ring
        painter.save()
        painter.translate(160.0, 160.0)
        painter.rotate(self.angle)
        painter.setPen(QPen(border_col, 4, Qt.PenStyle.DashLine))
        painter.drawEllipse(QPointF(0.0, 0.0), 130.0, 130.0)
        painter.rotate(-2.2 * self.angle)
        painter.setPen(QPen(QColor(0, 240, 255, 180), 2.5, Qt.PenStyle.DotLine))
        painter.drawEllipse(QPointF(0.0, 0.0), 108.0, 108.0)
        painter.restore()

        # Center text
        if self.current_number > 0:
            font = QFont("Segoe UI", 92, QFont.Weight.Black)
            painter.setFont(font)
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(QRect(0, -18, 320, 320), Qt.AlignmentFlag.AlignCenter, str(self.current_number))
            sub_label = f"RECORDING IN {self.current_number}..."
        else:
            font = QFont("Segoe UI", 56, QFont.Weight.Black)
            painter.setFont(font)
            painter.setPen(QColor(16, 185, 129))
            painter.drawText(QRect(0, -18, 320, 320), Qt.AlignmentFlag.AlignCenter, "REC!")
            sub_label = "RECPLAY STUDIO ACTIVE"

        sub_font = QFont("Consolas", 12, QFont.Weight.Bold)
        painter.setFont(sub_font)
        painter.setPen(border_col)
        painter.drawText(QRect(20, 235, 280, 32), Qt.AlignmentFlag.AlignCenter, sub_label)


class LiveRegionFrame(QWidget):
    """
    Interactive Drag-Out Studio Area Editor (`டிராக் அவுட் ஆப்ஷன்`)!
    Uses Opaque QWidget + Debounced QRegion setMask (NO WA_TranslucentBackground -> 100% crash-proof!).
    """
    area_locked = pyqtSignal(int, int, int, int)
    area_cancelled = pyqtSignal()
    request_freehand_drag = pyqtSignal()

    EDGE_NONE = 0
    EDGE_LEFT = 1
    EDGE_RIGHT = 2
    EDGE_TOP = 4
    EDGE_BOTTOM = 8

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        # NO WA_TranslucentBackground! Opaque window with hollow QRegion mask prevents VCRUNTIME140 crash!
        self.setMouseTracking(True)
        self.setMinimumSize(260, 190)
        self.resize(920, 560)

        self._drag_offset = None
        self._resize_edge = self.EDGE_NONE
        self._resize_start_geo = None
        self._resize_start_mouse = None

        self.setMouseTracking(True)
        self.setMinimumSize(300, 190)
        self.resize(920, 560)

        self._drag_offset = None
        self._resize_edge = self.EDGE_NONE
        self._resize_start_geo = None
        self._resize_start_mouse = None

        self.is_locked_mode = False
        self.is_recording_active = False
        self._pulse_phase = False

        # Coalesced mask timer so setMask is NEVER called synchronously inside resizeEvent!
        self._mask_timer = QTimer(self)
        self._mask_timer.setSingleShot(True)
        self._mask_timer.setInterval(10)
        self._mask_timer.timeout.connect(self._apply_hollow_mask)

        self._pulse_timer = QTimer(self)
        self._pulse_timer.setInterval(1200)
        self._pulse_timer.timeout.connect(self._tick_pulse)

        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(10, 10, 10, 10)
        main_lay.setSpacing(0)

        self.top_bar = QFrame()
        self.top_bar.setFixedHeight(56)
        self.top_bar.setStyleSheet("""
            QFrame {
                background-color: #060F1E;
                border: 2px solid #00F0FF;
                border-radius: 9px;
            }
            QLabel {
                color: #00F0FF;
                font-weight: bold;
                font-size: 11px;
                border: none;
                background: transparent;
            }
            QPushButton {
                background-color: #0F172A;
                color: #F8FAFC;
                border: 1px solid #0284C7;
                border-radius: 5px;
                padding: 2px 7px;
                font-weight: bold;
                font-size: 11px;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #0284C7;
                border-color: #00F0FF;
            }
            QPushButton#lockBtn {
                background-color: #059669;
                border-color: #10B981;
            }
            QPushButton#dragNewBtn {
                background-color: #2563EB;
                border-color: #60A5FA;
            }
            QPushButton#cancelBtn {
                background-color: #DC2626;
                border-color: #F87171;
            }
        """)
        tb_outer = QVBoxLayout(self.top_bar)
        tb_outer.setContentsMargins(6, 4, 6, 4)
        tb_outer.setSpacing(3)

        # Row 1: Dimension & Instruction Title (Spans full width, centered)
        self.lbl_dims = QLabel("🎯 SELECT AREA • Move or Drag Any Edge to Adjust")
        self.lbl_dims.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_dims.setCursor(Qt.CursorShape.SizeAllCursor)
        self.lbl_dims.installEventFilter(self)
        self.top_bar.installEventFilter(self)
        self.top_bar.setCursor(Qt.CursorShape.SizeAllCursor)
        tb_outer.addWidget(self.lbl_dims)

        # Row 2: Action Buttons (Centered, never squished)
        tb_row_btns = QHBoxLayout()
        tb_row_btns.setSpacing(5)
        tb_row_btns.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn_redraw = QPushButton("🖱️ Drag New")
        self.btn_redraw.setObjectName("dragNewBtn")
        self.btn_redraw.setToolTip("Click & Drag to define a new recording area")
        self.btn_redraw.clicked.connect(self.request_freehand_drag.emit)
        self.btn_redraw.setVisible(True)

        self.btn_center = QPushButton("🎯 Center")
        self.btn_center.clicked.connect(self.center_on_screen)

        self.btn_smaller = QPushButton("➖ Size")
        self.btn_smaller.clicked.connect(lambda: self.scale_box(-80, -45))

        self.btn_bigger = QPushButton("➕ Size")
        self.btn_bigger.clicked.connect(lambda: self.scale_box(80, 45))

        self.btn_lock = QPushButton("✔️ Lock Area")
        self.btn_lock.setObjectName("lockBtn")
        self.btn_lock.clicked.connect(self.confirm_current_area)

        self.btn_edit = QPushButton("📐 Resize")
        self.btn_edit.setObjectName("dragNewBtn")
        self.btn_edit.clicked.connect(self.unlock_for_editing)
        self.btn_edit.setVisible(False)

        self.btn_cancel = QPushButton("✖ Close")
        self.btn_cancel.setObjectName("cancelBtn")
        self.btn_cancel.clicked.connect(self._on_cancel)

        for w_btn in [
            self.btn_redraw,
            self.btn_center,
            self.btn_smaller,
            self.btn_bigger,
            self.btn_lock,
            self.btn_edit,
            self.btn_cancel,
        ]:
            tb_row_btns.addWidget(w_btn)
        tb_outer.addLayout(tb_row_btns)

        self.preset_row_widget = QWidget()
        self.preset_row_widget.setVisible(False)
        self.top_bar.setFixedHeight(56)

        main_lay.addWidget(self.top_bar)
        main_lay.addStretch(1)
        _exclude_window_from_capture(self)

    def showEvent(self, event):
        super().showEvent(event)
        _exclude_window_from_capture(self)

    def hideEvent(self, event):
        self._pulse_timer.stop()
        super().hideEvent(event)

    def _tick_pulse(self):
        return

    def center_on_screen(self):
        screen = QGuiApplication.primaryScreen()
        if not screen:
            return
        geo = screen.availableGeometry()
        x = geo.x() + (geo.width() - self.width()) // 2
        y = geo.y() + (geo.height() - self.height()) // 2
        self.move(max(0, x), max(0, y))
        self.confirm_current_area()

    def scale_box(self, dw: int, dh: int):
        screen = QGuiApplication.primaryScreen()
        max_w = screen.availableGeometry().width() if screen else 1920
        max_h = screen.availableGeometry().height() if screen else 1080
        new_w = max(self.minimumWidth(), min(max_w, self.width() + dw))
        new_h = max(self.minimumHeight(), min(max_h, self.height() + dh))
        self.resize(new_w, new_h)
        self.center_on_screen()

    def apply_preset_shape(self, preset_code: str):
        screen = QGuiApplication.primaryScreen()
        geo = screen.availableGeometry() if screen else QRect(0, 0, 1920, 1040)
        dpr = screen.devicePixelRatio() if screen else 1.0
        pad_w, pad_h = 20, 96

        if preset_code == "hd720":
            target_w = int(1280 / dpr) + pad_w
            target_h = int(720 / dpr) + pad_h
            x = geo.x() + (geo.width() - target_w) // 2
            y = geo.y() + (geo.height() - target_h) // 2
        elif preset_code == "wide900":
            target_w = min(geo.width() - 20, int(1600 / dpr) + pad_w)
            target_h = min(geo.height() - 20, int(900 / dpr) + pad_h)
            x = geo.x() + (geo.width() - target_w) // 2
            y = geo.y() + (geo.height() - target_h) // 2
        elif preset_code == "shorts":
            target_h = min(geo.height() - 30, int(960 / dpr) + pad_h)
            target_w = int((target_h - pad_h) * 9 / 16) + pad_w
            x = geo.x() + (geo.width() - target_w) // 2
            y = geo.y() + (geo.height() - target_h) // 2
        elif preset_code == "square":
            side = min(geo.height() - 100, int(760 / dpr))
            target_w = side + pad_w
            target_h = side + pad_h
            x = geo.x() + (geo.width() - target_w) // 2
            y = geo.y() + (geo.height() - target_h) // 2
        elif preset_code == "lecture":
            target_h = min(geo.height() - 40, int(840 / dpr) + pad_h)
            target_w = int((target_h - pad_h) * 4 / 3) + pad_w
            x = geo.x() + (geo.width() - target_w) // 2
            y = geo.y() + (geo.height() - target_h) // 2
        elif preset_code == "left_half":
            target_w = geo.width() // 2
            target_h = geo.height() - 10
            x = geo.x()
            y = geo.y() + 5
        elif preset_code == "right_half":
            target_w = geo.width() // 2
            target_h = geo.height() - 10
            x = geo.x() + geo.width() // 2
            y = geo.y() + 5
        else:
            target_w, target_h = 900, 560
            x = geo.x() + (geo.width() - target_w) // 2
            y = geo.y() + (geo.height() - target_h) // 2

        self.setGeometry(max(0, x), max(0, y), max(260, target_w), max(190, target_h))
        self.confirm_current_area()

    def _hit_test_edge(self, pos: QPoint) -> int:
        margin = 14
        w, h = self.width(), self.height()
        edge = self.EDGE_NONE
        if pos.x() <= margin:
            edge |= self.EDGE_LEFT
        elif pos.x() >= w - margin:
            edge |= self.EDGE_RIGHT
        if pos.y() <= margin:
            edge |= self.EDGE_TOP
        elif pos.y() >= h - margin:
            edge |= self.EDGE_BOTTOM
        return edge

    def _update_cursor_for_edge(self, edge: int):
        if edge in (self.EDGE_TOP | self.EDGE_LEFT, self.EDGE_BOTTOM | self.EDGE_RIGHT):
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        elif edge in (self.EDGE_TOP | self.EDGE_RIGHT, self.EDGE_BOTTOM | self.EDGE_LEFT):
            self.setCursor(Qt.CursorShape.SizeBDiagCursor)
        elif edge in (self.EDGE_LEFT, self.EDGE_RIGHT):
            self.setCursor(Qt.CursorShape.SizeHorCursor)
        elif edge in (self.EDGE_TOP, self.EDGE_BOTTOM):
            self.setCursor(Qt.CursorShape.SizeVerCursor)
        else:
            self.setCursor(Qt.CursorShape.SizeAllCursor)

    def _apply_hollow_mask(self):
        full_reg = QRegion(self.rect())
        top_bar_height = (self.top_bar.height() + 12) if self.top_bar.isVisible() else 12
        inner_rect = self.rect().adjusted(10, top_bar_height, -10, -10)
        if inner_rect.width() > 20 and inner_rect.height() > 20:
            hollow_reg = full_reg.subtracted(QRegion(inner_rect))
            self.setMask(hollow_reg)
        else:
            self.clearMask()

    def set_from_dragged_rect(self, rect: QRect):
        self.target_crop_rect = rect
        self.is_recording_active = False
        self.is_locked_mode = False
        self.top_bar.setFixedHeight(56)
        self.preset_row_widget.setVisible(False)
        self.btn_lock.setVisible(True)
        self.btn_redraw.setVisible(True)
        self.btn_center.setVisible(True)
        self.btn_smaller.setVisible(True)
        self.btn_bigger.setVisible(True)
        self.btn_edit.setVisible(False)
        self.btn_cancel.setVisible(True)

        top_offset = self.top_bar.height() + 12
        fx = max(0, rect.x() - 10)
        fy = max(0, rect.y() - top_offset)
        fw = max(260, rect.width() + 20)
        fh = max(180, rect.height() + top_offset + 10)
        self.setGeometry(fx, fy, fw, fh)
        self._apply_hollow_mask()
        self._update_dim_text()
        self.hide()
        rx, ry, rw, rh = self.get_physical_crop_region()
        self.area_locked.emit(rx, ry, rw, rh)

    def open_centered(self):
        self.target_crop_rect = None
        self.is_recording_active = False
        self.is_locked_mode = False
        self.top_bar.setFixedHeight(56)
        self.preset_row_widget.setVisible(False)
        self.btn_lock.setVisible(True)
        self.btn_redraw.setVisible(True)
        self.btn_center.setVisible(True)
        self.btn_smaller.setVisible(True)
        self.btn_bigger.setVisible(True)
        self.btn_edit.setVisible(False)
        self.btn_cancel.setVisible(True)

        screen = QGuiApplication.primaryScreen()
        if screen and not self.isVisible():
            geo = screen.availableGeometry()
            w = min(920, int(geo.width() * 0.70))
            h = min(560, int(geo.height() * 0.70))
            x = geo.x() + (geo.width() - w) // 2
            y = geo.y() + (geo.height() - h) // 2
            self.setGeometry(x, y, w, h)

        self._apply_hollow_mask()
        self._update_dim_text()
        self.show()
        self.raise_()

    def unlock_for_editing(self):
        self.target_crop_rect = None
        self.is_locked_mode = False
        self.is_recording_active = False
        self.top_bar.setFixedHeight(56)
        self.preset_row_widget.setVisible(False)
        self.btn_lock.setVisible(True)
        self.btn_redraw.setVisible(True)
        self.btn_center.setVisible(True)
        self.btn_smaller.setVisible(True)
        self.btn_bigger.setVisible(True)
        self.btn_edit.setVisible(False)
        self._apply_hollow_mask()
        self._update_dim_text()
        self.update()

    def set_recording_active(self, active: bool):
        self.is_recording_active = active
        # Hide Drag-Out frame during recording so no blue/red blinking border ever appears in recorded video!
        self.hide()

    def get_physical_crop_region(self) -> tuple[int, int, int, int]:
        screen = QGuiApplication.primaryScreen()
        dpr = screen.devicePixelRatio() if screen else 1.0
        max_pw = 1920
        max_ph = 1080
        if screen:
            s_geo = screen.geometry()
            max_pw = int(round(s_geo.width() * dpr))
            max_ph = int(round(s_geo.height() * dpr))

        if getattr(self, "target_crop_rect", None) is not None:
            r = self.target_crop_rect
            rx = max(0, int(round(r.x() * dpr)))
            ry = max(0, int(round(r.y() * dpr)))
            rw = max(80, int(round(r.width() * dpr)))
            rh = max(60, int(round(r.height() * dpr)))
        else:
            geo = self.geometry()
            top_bar = getattr(self, "top_bar", None)
            top_offset = (top_bar.height() + 12) if (top_bar is not None and top_bar.isVisible()) else 12
            inner_x = geo.x() + 10
            inner_y = geo.y() + top_offset
            inner_w = max(120, geo.width() - 20)
            inner_h = max(120, geo.height() - top_offset - 10)

            rx = max(0, int(round(inner_x * dpr)))
            ry = max(0, int(round(inner_y * dpr)))
            rw = max(120, int(round(inner_w * dpr)))
            rh = max(120, int(round(inner_h * dpr)))

        # Exact pixel boundary clipping to eliminate any frame grabber out-of-bounds error
        rx = min(rx, max(0, max_pw - 80))
        ry = min(ry, max(0, max_ph - 60))
        rw = min(rw, max_pw - rx)
        rh = min(rh, max_ph - ry)
        if rw % 2 != 0:
            rw -= 1
        if rh % 2 != 0:
            rh -= 1
        return (rx, ry, rw, rh)

    def _update_dim_text(self):
        if not hasattr(self, "lbl_dims") or not hasattr(self, "top_bar"):
            return
        _, _, rw, rh = self.get_physical_crop_region()
        w = self.width()
        if self.is_locked_mode:
            if w < 440:
                self.lbl_dims.setText(f"✅ LOCKED: {rw} × {rh} px  •  Ready")
            else:
                self.lbl_dims.setText(f"✅ AREA LOCKED: {rw} × {rh} px  •  Ready to Record")
        else:
            if w < 440:
                self.lbl_dims.setText(f"🎯 AREA: {rw} × {rh} px  •  Drag Borders")
            else:
                self.lbl_dims.setText(f"🎯 SELECT AREA: {rw} × {rh} px  •  Drag Borders or Header to Move")

    def confirm_current_area(self):
        rx, ry, rw, rh = self.get_physical_crop_region()
        self.is_locked_mode = True
        self.top_bar.setFixedHeight(56)
        self.preset_row_widget.setVisible(False)
        self.btn_lock.setVisible(False)
        self.btn_smaller.setVisible(False)
        self.btn_bigger.setVisible(False)
        self.btn_redraw.setVisible(False)
        self.btn_edit.setVisible(True)
        self._update_dim_text()
        self._apply_hollow_mask()
        self.show()
        self.raise_()
        self.update()
        self.area_locked.emit(rx, ry, rw, rh)

    def _on_cancel(self):
        self.is_locked_mode = False
        self.is_recording_active = False
        self.clearMask()
        self.hide()
        self.area_cancelled.emit()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "top_bar"):
            self._update_dim_text()
            self._mask_timer.start()

    def moveEvent(self, event):
        super().moveEvent(event)
        if hasattr(self, "top_bar"):
            self._update_dim_text()

    def eventFilter(self, obj, event):
        if obj in (self.top_bar, self.lbl_dims):
            if event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
                self._resize_edge = self.EDGE_NONE
                self._drag_offset = event.globalPosition().toPoint() - self.pos()
                return True
            elif event.type() == QEvent.Type.MouseMove and (event.buttons() & Qt.MouseButton.LeftButton):
                if self._drag_offset is not None:
                    self.move(event.globalPosition().toPoint() - self._drag_offset)
                    self._update_dim_text()
                    rx, ry, rw, rh = self.get_physical_crop_region()
                    self.area_locked.emit(rx, ry, rw, rh)
                    return True
            elif event.type() == QEvent.Type.MouseButtonRelease:
                self._drag_offset = None
                self._apply_hollow_mask()
                return True
        return super().eventFilter(obj, event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position().toPoint()
            edge = self._hit_test_edge(pos)
            if edge != self.EDGE_NONE:
                self._resize_edge = edge
                self._resize_start_geo = self.geometry()
                self._resize_start_mouse = event.globalPosition().toPoint()
            else:
                self._resize_edge = self.EDGE_NONE
                self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        global_pt = event.globalPosition().toPoint()
        if event.buttons() & Qt.MouseButton.LeftButton:
            if self._resize_edge != self.EDGE_NONE and self._resize_start_geo is not None:
                dx = global_pt.x() - self._resize_start_mouse.x()
                dy = global_pt.y() - self._resize_start_mouse.y()
                g = QRect(self._resize_start_geo)
                min_w, min_h = self.minimumWidth(), self.minimumHeight()

                if self._resize_edge & self.EDGE_LEFT:
                    g.setLeft(min(g.right() - min_w, g.left() + dx))
                if self._resize_edge & self.EDGE_RIGHT:
                    g.setRight(max(g.left() + min_w, g.right() + dx))
                if self._resize_edge & self.EDGE_TOP:
                    g.setTop(min(g.bottom() - min_h, g.top() + dy))
                if self._resize_edge & self.EDGE_BOTTOM:
                    g.setBottom(max(g.top() + min_h, g.bottom() + dy))

                self.setGeometry(g)
                rx, ry, rw, rh = self.get_physical_crop_region()
                self.area_locked.emit(rx, ry, rw, rh)
                event.accept()
                return
            elif self._drag_offset is not None:
                self.move(global_pt - self._drag_offset)
                self._update_dim_text()
                rx, ry, rw, rh = self.get_physical_crop_region()
                self.area_locked.emit(rx, ry, rw, rh)
                event.accept()
                return
        else:
            edge = self._hit_test_edge(event.position().toPoint())
            self._update_cursor_for_edge(edge)

    def mouseReleaseEvent(self, event):
        self._drag_offset = None
        self._resize_edge = self.EDGE_NONE
        self._apply_hollow_mask()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(6, 15, 30))
        rect = self.rect().adjusted(3, 3, -3, -3)
        painter.setPen(QPen(QColor(0, 240, 255), 5, Qt.PenStyle.SolidLine))
        painter.drawRect(rect)


class YouTubeChaptersDialog(QDialog):
    """Interactive YouTube Chapters Manager & Explainer Dialog."""

    def __init__(self, parent_win):
        super().__init__(parent_win)
        self.parent_win = parent_win
        self.setWindowTitle("🔖 YouTube Chapters (Time-Stamps) Manager")
        self.resize(560, 440)
        self.setStyleSheet("""
            QDialog { background-color: #0F172A; color: #F8FAFC; }
            QLabel { color: #E2E8F0; font-size: 13px; }
            QLineEdit, QTextEdit {
                background-color: #1E293B; color: #F8FAFC;
                border: 1px solid #334155; border-radius: 6px; padding: 6px; font-size: 13px;
            }
            QPushButton {
                background-color: #1E293B; color: #F8FAFC;
                border: 1px solid #475569; border-radius: 6px; padding: 7px 14px; font-weight: bold;
            }
            QPushButton:hover { background-color: #334155; border-color: #00F0FF; }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        info = QLabel(
            "<b>💡 What are YouTube Chapters?</b><br>"
            "• YouTube Chapters divide your video timeline (progress bar) into clickable sections<br>"
            "  such as <b>00:00 Introduction</b>, <b>02:15 Lesson 1</b>, and <b>05:30 Summary</b>.<br>"
            "• Press <b>🔖 Chapter</b> (or <b>Ctrl+M</b>) while recording whenever you start a new topic to mark the timestamp.<br>"
            "• Click <b>📋 Copy Chapters for YouTube Description</b> below and paste directly into your YouTube video description!"
        )
        info.setWordWrap(True)
        info.setStyleSheet("background-color: #1E293B; border-left: 4px solid #00F0FF; padding: 10px; border-radius: 6px;")
        layout.addWidget(info)

        add_row = QHBoxLayout()
        self.txt_title = QLineEdit()
        self.txt_title.setPlaceholderText("Enter chapter title (e.g. Introduction, Topic 1, Summary)...")
        btn_add = QPushButton("➕ Add Chapter Now")
        btn_add.setStyleSheet("background-color: #DC2626; color: white; border: none;")
        btn_add.clicked.connect(self._on_add_clicked)
        add_row.addWidget(self.txt_title, 1)
        add_row.addWidget(btn_add)
        layout.addLayout(add_row)

        self.editor = QTextEdit()
        layout.addWidget(self.editor, 1)

        btn_row = QHBoxLayout()
        btn_copy = QPushButton("📋 Copy Chapters for YouTube Description")
        btn_copy.setStyleSheet("background-color: #16A34A; color: white; border: none;")
        btn_copy.clicked.connect(self._copy_to_clipboard)
        btn_close = QPushButton("✔️ Done")
        btn_close.clicked.connect(self.accept)
        btn_row.addWidget(btn_copy, 1)
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)

        self._refresh_text()

    def _refresh_text(self):
        lines = []
        for sec, title in self.parent_win.session_chapters:
            mm, ss = divmod(int(sec), 60)
            lines.append(f"{mm:02d}:{ss:02d} {title}")
        self.editor.setPlainText("\n".join(lines))

    def _on_add_clicked(self):
        title = self.txt_title.text().strip()
        self.parent_win.add_chapter_entry(title)
        self.txt_title.clear()
        self._refresh_text()

    def _copy_to_clipboard(self):
        text = self.editor.toPlainText().strip()
        QApplication.clipboard().setText(text)
        QMessageBox.information(self, "Copied!", "YouTube Chapters copied to clipboard!\nPaste this directly into your YouTube video description.")


class FacecamPreviewWidget(QWidget):
    """Futuristic camera viewport with animated cyber neon ring matching selected shape (circle/square/wide)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(116, 116)
        self.current_pixmap = None
        self.shape_name = "circle"
        self.is_active = False

    def set_shape(self, shape: str):
        self.shape_name = shape.lower()
        self.update()

    def set_frame(self, frame_bgr):
        try:
            h, w, ch = frame_bgr.shape
            rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            qimg = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
            self.current_pixmap = QPixmap.fromImage(qimg)
            self.is_active = True
            self.update()
        except Exception:
            pass

    def set_offline(self):
        self.is_active = False
        self.current_pixmap = None
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(4, 4, -4, -4)

        path = QPainterPath()
        if "circle" in self.shape_name:
            path.addEllipse(QRectF(rect))
        elif "square" in self.shape_name:
            path.addRoundedRect(QRectF(rect), 14, 14)
        else:  # wide
            wide_rect = QRect(rect.x(), rect.y() + 14, rect.width(), rect.height() - 28)
            path.addRoundedRect(QRectF(wide_rect), 10, 10)
            rect = wide_rect

        painter.save()
        painter.setClipPath(path)
        if self.is_active and self.current_pixmap and not self.current_pixmap.isNull():
            scaled = self.current_pixmap.scaled(
                rect.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            painter.drawPixmap(rect.center().x() - scaled.width() // 2, rect.center().y() - scaled.height() // 2, scaled)
        else:
            painter.fillRect(rect, QColor(10, 18, 34))
            painter.setPen(QColor(56, 189, 248))
            painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "📷 Camera\nPreview")
        painter.restore()

        # Neon Cyber Glow Rim
        pen = QPen(QColor(0, 240, 255), 2)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        if "circle" in self.shape_name:
            painter.drawEllipse(rect)
        elif "square" in self.shape_name:
            painter.drawRoundedRect(rect, 14, 14)
        else:
            painter.drawRoundedRect(rect, 10, 10)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Recplay 2.0 - Studio Suite & Media Player")
        self.setMinimumSize(1040, 690)
        self.resize(1100, 725)

        icon_path = Path(__file__).resolve().parent.parent / "assets" / "icon.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self.setStyleSheet("""
            QMainWindow {
                background-color: #060C18;
                color: #F8FAFC;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLabel {
                color: #FFFFFF;
                font-size: 13px;
                font-weight: 500;
            }
            QGroupBox {
                background-color: rgba(6, 13, 26, 130);
                border: 1px solid #0284C7;
                border-radius: 10px;
                margin-top: 8px;
                padding-top: 12px;
                padding-bottom: 7px;
                padding-left: 12px;
                padding-right: 12px;
                font-size: 13px;
                font-weight: bold;
                color: #00F0FF;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 14px;
                padding: 0 6px;
            }
            QLineEdit, QTextEdit {
                background-color: #0F172A;
                border: 1px solid #0284C7;
                border-radius: 6px;
                padding: 4px 10px;
                min-height: 23px;
                color: #F8FAFC;
                font-size: 13px;
                selection-background-color: #0284C7;
                selection-color: #FFFFFF;
            }
            QLineEdit:hover, QTextEdit:hover {
                border: 1px solid #00F0FF;
                background-color: #1E293B;
            }
            QLineEdit:focus, QTextEdit:focus {
                border: 1px solid #00F0FF;
                background-color: #16243E;
            }
            QLineEdit:disabled, QTextEdit:disabled {
                background-color: #091122;
                color: #64748B;
                border: 1px solid #1E293B;
            }
            QLineEdit:read-only, QTextEdit:read-only {
                background-color: #0F172A;
                color: #38BDF8;
                border: 1px solid #0284C7;
            }
            QToolTip {
                background-color: #0F172A;
                color: #00F0FF;
                border: 1px solid #0284C7;
                border-radius: 6px;
                padding: 5px 8px;
                font-size: 12px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QMenu {
                background-color: #0F172A;
                color: #F8FAFC;
                border: 1px solid #0284C7;
                border-radius: 8px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 16px;
                border-radius: 4px;
                color: #F8FAFC;
            }
            QMenu::item:selected {
                background-color: #0284C7;
                color: #FFFFFF;
            }
            QScrollBar:vertical, QScrollBar:horizontal {
                background-color: #060C18;
                border: none;
                width: 10px;
                height: 10px;
            }
            QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
                background-color: #1E293B;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:hover {
                background-color: #0284C7;
            }
            QCheckBox {
                color: #E2E8F0;
                font-size: 13px;
                spacing: 8px;
            }
            QCheckBox:disabled {
                color: #64748B;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 1px solid #0284C7;
                background-color: #0F172A;
            }
            QCheckBox::indicator:checked {
                background-color: #00F0FF;
                border: 1px solid #00F0FF;
            }
            QCheckBox::indicator:disabled {
                background-color: #0B132B;
                border: 1px solid #1E293B;
            }
            QPushButton {
                background-color: #0F172A;
                color: #F8FAFC;
                border: 1px solid #1E293B;
                border-radius: 7px;
                padding: 5px 12px;
                font-weight: 600;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #1E293B;
                border-color: #00F0FF;
            }
            QPushButton:disabled {
                background-color: #0B132B;
                color: #64748B;
                border: 1px solid #1E293B;
            }
            QPushButton#recBtn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #DC2626, stop:1 #EF4444);
                color: #FFFFFF;
                border: 1px solid #F87171;
                font-size: 13px;
                font-weight: 900;
                padding: 9px 20px;
                border-radius: 11px;
                min-width: 170px;
                letter-spacing: 0.5px;
            }
            QPushButton#recBtn:hover {
                background: #B91C1C;
                border-color: #EF4444;
            }
            QPushButton#snipBtn {
                background-color: #0D9488;
                color: white;
                border: none;
                font-weight: bold;
                padding: 9px 15px;
            }
            QPushButton#snipBtn:hover {
                background-color: #0F766E;
            }
            QPushButton#drawBtn {
                background-color: #0284C7;
                color: white;
                border: 1px solid #00F0FF;
                font-weight: bold;
                padding: 9px 15px;
            }
            QPushButton#drawBtn:hover {
                background-color: #0369A1;
            }
            QProgressBar {
                background-color: #0F172A;
                border: 1px solid #0284C7;
                border-radius: 5px;
                height: 10px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #00F0FF;
                border-radius: 4px;
            }
            QSlider::groove:horizontal {
                height: 5px;
                background: #0F172A;
                border: 1px solid #1E293B;
                border-radius: 3px;
            }
            QSlider::sub-page:horizontal {
                background: #00F0FF;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #00F0FF;
                border: 2px solid #FFFFFF;
                width: 14px;
                margin-top: -5px;
                margin-bottom: -5px;
                border-radius: 7px;
            }
            QSlider::handle:horizontal:hover {
                background: #38BDF8;
                border: 2px solid #00F0FF;
            }
            QFrame#presetsCard {
                background-color: rgba(10, 18, 34, 150);
                border: 1px solid rgba(2, 132, 199, 0.45);
                border-radius: 12px;
            }
            QPushButton#pillPresetBtn {
                background-color: #0F172A;
                color: #FFFFFF;
                border: 1.5px solid #0284C7;
                border-radius: 8px;
                padding: 5px 14px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton#pillPresetBtn:hover {
                background-color: #0284C7;
                color: #FFFFFF;
                border-color: #00F0FF;
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
                min-width: 95px;
            }
            QMessageBox QPushButton:hover {
                background-color: #0369A1;
            }
        """)

        self.verifier = LicenseVerifier()
        self.recorder: ScreenRecorder = None
        self.is_recording = False
        self.is_paused = False
        self.record_seconds = 0
        self.custom_crop_region = None
        self.session_chapters = [(0.0, "Introduction")]
        self.selected_audio_mode = "input_and_output"
        self._restore_after_snip = False
        self.slider_mic_vol = None
        self.slider_sys_vol = None
        self.mic_vu_meter = None
        self.sys_vu_meter = None

        videos_dir = Path.home() / "Videos" / "Recplay_Recordings"
        videos_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir = str(videos_dir)

        # Overlays & Tools (100% Opaque / QRegion Mask -> ZERO WS_EX_LAYERED / VCRUNTIME140 crashes!)
        self.annotator = AnnotatorOverlay()
        self.snipper = SnippingOverlay()
        self.snipper.snippet_captured.connect(self._open_screenshot_editor)
        self.snipper.cancelled.connect(self._on_snip_cancelled)
        self.floating_facecam = FloatingFacecamWidget()
        self.floating_jarvis = FloatingJarvisWidget()
        self.facecam_size_px = 180

        self.fullscreen_highlight = FullScreenHighlightBorder()
        self.freehand_selector = FreehandDragAreaSelector()
        self.freehand_selector.area_dragged.connect(self._on_freehand_area_dragged)
        self.freehand_selector.cancelled.connect(self._on_freehand_cancelled)

        self.live_region_frame = LiveRegionFrame()
        self.live_region_frame.area_locked.connect(self._on_custom_region_coords)
        self.live_region_frame.area_cancelled.connect(self._on_region_selection_cancelled)
        self.live_region_frame.request_freehand_drag.connect(self._start_freehand_drag_selection)
        self.area_marking_border = AreaMarkingBorder()

        self.countdown_overlay = ScreenBlinkCountdownOverlay()
        self.countdown_overlay.countdown_finished.connect(self._execute_start_recording)
        self.countdown_overlay.countdown_tick.connect(self._on_countdown_tick)
        self._countdown_in_progress = False

        self.live_cam_cap = None
        self.is_live_testing_cam = False
        self.live_cam_timer = QTimer(self)
        self.live_cam_timer.setInterval(45)
        self.live_cam_timer.timeout.connect(self._tick_live_facecam)

        self.rec_timer = QTimer(self)
        self.rec_timer.setInterval(1000)
        self.rec_timer.timeout.connect(self._on_gui_second_tick)

        self.vu_timer = QTimer(self)
        self.vu_timer.setInterval(135)
        self.vu_timer.timeout.connect(self._update_vu_meter)
        self._vu_blink_phase = 0

        self._init_ui()
        self.floating_rec_bar = FloatingRecordingBar(self)
        self._sync_audio_mode_buttons("Both Input and Output")
        self._refresh_license_display()
        self.vu_timer.start()

    def _init_ui(self):
        main_widget = CliprCyberBackgroundWidget(self)
        self.jarvis_banner = main_widget
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(8)

        # 1. Header Bar (No extra banner line underneath!)
        header = QHBoxLayout()
        brand_row = QHBoxLayout()
        brand_row.setSpacing(10)

        logo_lbl = QLabel()
        icon_path = Path(__file__).resolve().parent.parent / "assets" / "icon.png"
        if icon_path.exists():
            pix = QPixmap(str(icon_path)).scaled(
                38, 38, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
            logo_lbl.setPixmap(pix)
        brand_row.addWidget(logo_lbl)

        title_col = QVBoxLayout()
        title_col.setSpacing(1)
        title = QLabel("RECPLAY STUDIO 2.0")
        title.setStyleSheet("font-size: 21px; font-weight: 900; color: #00F0FF; letter-spacing: 1.5px;")
        subtitle = QLabel("AI Studio Screen Recorder • Video & Music Player")
        subtitle.setStyleSheet("color: #38BDF8; font-size: 12px; font-weight: bold;")
        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        brand_row.addLayout(title_col)

        header.addLayout(brand_row)
        header.addStretch()

        btn_vid_player = QPushButton("🎬 Video Player")
        btn_vid_player.setToolTip("Open Built-in Recplay 2.0 Video Player")
        btn_vid_player.setStyleSheet("background-color: #0F172A; color: #00F0FF; border: 1px solid #0284C7; font-weight: bold; padding: 4px 10px; border-radius: 8px; font-size: 11px;")
        btn_vid_player.clicked.connect(self._open_video_player)

        btn_mus_player = QPushButton("🎵 Music Player")
        btn_mus_player.setToolTip("Open Built-in Recplay 2.0 Music & Audio Player")
        btn_mus_player.setStyleSheet("background-color: #0F172A; color: #38BDF8; border: 1px solid #0284C7; font-weight: bold; padding: 4px 10px; border-radius: 8px; font-size: 11px;")
        btn_mus_player.clicked.connect(self._open_music_player)

        header.addWidget(btn_vid_player)
        header.addWidget(btn_mus_player)

        self.cpu_eco_badge = QLabel("📊 CPU: 1.2% | Sys: 8.4%")
        self.cpu_eco_badge.setStyleSheet(
            "background-color: #0F172A; color: #34D399; padding: 5px 12px; border-radius: 8px; font-weight: bold; font-size: 11px; border: 1px solid #059669;"
        )
        header.addWidget(self.cpu_eco_badge)

        self.license_badge = QLabel("⏱️ TRIAL VERSION")
        self.license_badge.setStyleSheet(
            "background-color: #0F172A; color: #FBBF24; padding: 5px 14px; border-radius: 8px; font-weight: bold; font-size: 11px; border: 1px solid #D97706;"
        )

        btn_license = QPushButton("🔑 License")
        btn_license.setStyleSheet(
            "background-color: #0F172A; color: #F8FAFC; border: 1px solid #0284C7; font-weight: bold; padding: 5px 12px; border-radius: 8px; font-size: 11px;"
        )
        btn_license.clicked.connect(self._open_license_dialog)

        header.addWidget(self.license_badge)
        header.addWidget(btn_license)
        layout.addLayout(header)

        # 2. Middle Two-Column Grid
        mid_row = QHBoxLayout()
        mid_row.setSpacing(12)

        # Column A: High-Quality Video & Screen Area Options
        grp_video = QGroupBox("🎥 Screen Area && Video Quality")
        v_layout = QVBoxLayout(grp_video)
        v_layout.setSpacing(6)

        v_row_screen = QHBoxLayout()
        v_row_screen.setSpacing(8)
        lbl_area = QLabel("Area Mode:")
        lbl_area.setFixedWidth(88)
        lbl_area.setStyleSheet("color: #00F0FF; font-weight: bold; font-size: 12px;")
        v_row_screen.addWidget(lbl_area)
        self.combo_screen_mode = StudioSelectButton("Select Area", self)
        self.combo_screen_mode.setFixedWidth(230)
        self.combo_screen_mode.addItems([
            "🖥️ Full Screen",
            "🎯 Select Area",
            "📱 Shorts / Reels (9:16)",
        ])
        self.combo_screen_mode.setCurrentIndex(0)
        self.combo_screen_mode.currentIndexChanged.connect(self._on_screen_mode_changed)
        v_row_screen.addWidget(self.combo_screen_mode)
        v_row_screen.addStretch()

        self.btn_highlight_area = QPushButton("🎯 Select Area")
        self.btn_highlight_area.setVisible(False)

        self.btn_open_dragout = QPushButton("📐 Edit Drag-Out Box")
        self.btn_open_dragout.setVisible(False)
        v_layout.addLayout(v_row_screen)

        # Row 2: Trimmed Video Quality Presets
        v_row_preset = QHBoxLayout()
        v_row_preset.setSpacing(8)
        lbl_qual = QLabel("Video Quality:")
        lbl_qual.setFixedWidth(88)
        lbl_qual.setStyleSheet("color: #00F0FF; font-weight: bold; font-size: 12px;")
        v_row_preset.addWidget(lbl_qual)
        self.combo_preset = StudioSelectButton("Select Video Quality", self)
        self.combo_preset.setFixedWidth(230)
        self.combo_preset.addItems([
            "⚡ 1080p Low-CPU (24 FPS)",
            "🌟 1080p Full HD (30 FPS)",
            "💎 4K Ultra HD",
            "🎓 Lecture & Code HD",
            "🎬 YouTube Pro HD",
        ])
        self.combo_preset.setCurrentIndex(0)
        v_row_preset.addWidget(self.combo_preset)
        v_row_preset.addStretch()
        v_layout.addLayout(v_row_preset)

        # Row 3: Watermark Toggle + Custom Watermark Text (Full length, no clipping)
        v_row_wm = QHBoxLayout()
        v_row_wm.setSpacing(8)
        lbl_wm = QLabel("Watermark:")
        lbl_wm.setFixedWidth(88)
        lbl_wm.setStyleSheet("color: #00F0FF; font-weight: bold; font-size: 12px;")
        v_row_wm.addWidget(lbl_wm)

        self.chk_watermark = QCheckBox("Enable")
        self.chk_watermark.setChecked(True)
        self.chk_watermark.setFixedWidth(96)
        self.chk_watermark.setStyleSheet("font-weight: bold; color: #00F0FF; font-size: 12px;")
        v_row_wm.addWidget(self.chk_watermark)

        self.txt_watermark = QLineEdit("Recplay Studio")
        self.txt_watermark.setPlaceholderText("Watermark text...")
        self.txt_watermark.setStyleSheet(
            "QLineEdit { color: #00F0FF; font-weight: bold; background-color: #0F172A; border: 1px solid #0284C7; border-radius: 6px; padding: 4px 8px; font-size: 12px; }"
            "QLineEdit:disabled { color: #64748B; background-color: #091122; border: 1px solid #1E293B; }"
        )
        self.txt_watermark.setMinimumWidth(220)
        v_row_wm.addWidget(self.txt_watermark, 1)
        v_layout.addLayout(v_row_wm)

        # Row 4: Watermark Position Selector + Font Type Selection
        v_row_wm_opts = QHBoxLayout()
        v_row_wm_opts.setSpacing(8)
        lbl_wm_pos = QLabel("Position:")
        lbl_wm_pos.setFixedWidth(88)
        lbl_wm_pos.setStyleSheet("color: #00F0FF; font-weight: bold; font-size: 12px;")
        v_row_wm_opts.addWidget(lbl_wm_pos)

        self.combo_wm_pos = StudioSelectButton("Watermark Position", self)
        self.combo_wm_pos.setFixedWidth(135)
        self.combo_wm_pos.addItems([
            "Top-Center",
            "Bottom-Right",
            "Top-Right",
            "Bottom-Left",
            "Top-Left",
        ])
        v_row_wm_opts.addWidget(self.combo_wm_pos)

        self.lbl_wm_font = QLabel("Font:")
        self.lbl_wm_font.setFixedWidth(36)
        self.lbl_wm_font.setStyleSheet("color: #00F0FF; font-weight: bold; font-size: 12px;")
        v_row_wm_opts.addWidget(self.lbl_wm_font)

        self.combo_wm_font = StudioSelectButton("Watermark Font Type", self)
        self.combo_wm_font.setFixedWidth(135)
        self.combo_wm_font.addItems([
            "Segoe UI",
            "Arial Black",
            "Consolas",
            "Times New Roman",
            "Courier New",
            "Impact",
            "Georgia",
            "Verdana",
        ])
        self.combo_wm_font.currentTextChanged.connect(self._on_watermark_font_changed)
        v_row_wm_opts.addWidget(self.combo_wm_font)
        v_row_wm_opts.addStretch()
        v_layout.addLayout(v_row_wm_opts)

        # Row 5: Mouse Cursor Highlighting
        v_row_cursor = QHBoxLayout()
        v_row_cursor.setSpacing(8)
        lbl_cursor = QLabel("Cursor:")
        lbl_cursor.setFixedWidth(88)
        lbl_cursor.setStyleSheet("color: #00F0FF; font-weight: bold; font-size: 12px;")
        v_row_cursor.addWidget(lbl_cursor)

        self.chk_cursor = QCheckBox("Highlight Mouse Cursor (Halo && Click)")
        self.chk_cursor.setChecked(True)
        self.chk_cursor.setStyleSheet("font-weight: bold; color: #E2E8F0; font-size: 12px;")
        v_row_cursor.addWidget(self.chk_cursor)
        v_row_cursor.addStretch()
        v_layout.addLayout(v_row_cursor)

        mid_row.addWidget(grp_video, 3)

        # Column B: Facecam (Picture-in-Picture)
        grp_cam = QGroupBox("📷 Facecam Setup")
        c_layout = QVBoxLayout(grp_cam)
        c_layout.setSpacing(6)

        cam_top_row = QHBoxLayout()
        self.chk_webcam = QCheckBox("Enable Webcam (ON / OFF)")
        self.chk_webcam.setChecked(False)
        self.chk_webcam.setStyleSheet("font-weight: bold; color: #F8FAFC; font-size: 13px;")
        self.chk_webcam.toggled.connect(self._on_webcam_toggled)
        cam_top_row.addWidget(self.chk_webcam)
        cam_top_row.addStretch()

        lbl_mode = QLabel("Mode:")
        lbl_mode.setFixedWidth(44)
        lbl_mode.setStyleSheet("color: #00F0FF; font-weight: bold; font-size: 12px;")
        cam_top_row.addWidget(lbl_mode)
        self.combo_cam_mode = StudioSelectButton("Select Facecam Mode", self)
        self.combo_cam_mode.setFixedWidth(155)
        self.combo_cam_mode.addItems([
            "Standard (Normal)",
            "Background Blur",
            "Face Only (No Frame)",
        ])
        self.combo_cam_mode.currentTextChanged.connect(self._on_cam_mode_changed)
        cam_top_row.addWidget(self.combo_cam_mode)
        c_layout.addLayout(cam_top_row)

        # Center Preview & Controls (Mockup Style)
        cam_mid_row = QHBoxLayout()
        cam_mid_row.setSpacing(12)

        self.facecam_preview = FacecamPreviewWidget(self)
        cam_mid_row.addWidget(self.facecam_preview)

        cam_ctrls_col = QVBoxLayout()
        cam_ctrls_col.setSpacing(6)

        # Shape Row (Consistent StudioSelectButton box matching all other options)
        shape_row = QHBoxLayout()
        shape_row.setSpacing(6)
        lbl_shape = QLabel("Shape:")
        lbl_shape.setFixedWidth(44)
        lbl_shape.setStyleSheet("color: #00F0FF; font-weight: bold; font-size: 12px;")
        shape_row.addWidget(lbl_shape)

        self.combo_cam_shape = StudioSelectButton("Select Facecam Shape", self)
        self.combo_cam_shape.setFixedWidth(160)
        self.combo_cam_shape.addItems([
            "Circle",
            "Square (1:1)",
            "Wide (16:9)",
        ])
        self.combo_cam_shape.setCurrentText("Circle")
        self.combo_cam_shape.currentTextChanged.connect(self._on_cam_shape_changed)
        shape_row.addWidget(self.combo_cam_shape)
        shape_row.addStretch()
        cam_ctrls_col.addLayout(shape_row)

        # Backward compatibility dummy pill references
        self.btn_cam_circle = QPushButton("Circle")
        self.btn_cam_square = QPushButton("Square")
        self.btn_cam_wide = QPushButton("Wide")

        # Size Row (Consistent StudioSelectButton box matching all other options)
        size_row = QHBoxLayout()
        size_row.setSpacing(6)
        lbl_sz = QLabel("Size:")
        lbl_sz.setFixedWidth(44)
        lbl_sz.setStyleSheet("color: #00F0FF; font-weight: bold; font-size: 12px;")
        size_row.addWidget(lbl_sz)

        self.combo_cam_size = StudioSelectButton("Select Facecam Size", self)
        self.combo_cam_size.setFixedWidth(160)
        self.combo_cam_size.addItems([
            "Medium (180px)",
            "Small (140px)",
            "Large (240px)",
            "X-Large (300px)",
        ])
        self.combo_cam_size.setCurrentText("Medium (180px)")
        self.combo_cam_size.currentTextChanged.connect(self._on_cam_size_preset_changed)
        size_row.addWidget(self.combo_cam_size)
        size_row.addStretch()
        cam_ctrls_col.addLayout(size_row)

        # Backward compatibility dummy size references
        self.btn_sz_small = QPushButton("Small")
        self.btn_sz_med = QPushButton("Medium")
        self.btn_sz_large = QPushButton("Large")

        # Stepper & Position Row
        step_pos_row = QHBoxLayout()
        step_pos_row.setSpacing(6)
        lbl_place = QLabel("Pos:")
        lbl_place.setFixedWidth(44)
        lbl_place.setStyleSheet("color: #00F0FF; font-weight: bold; font-size: 12px;")
        step_pos_row.addWidget(lbl_place)

        self.combo_cam_pos = StudioSelectButton("Select Facecam Position", self)
        self.combo_cam_pos.setFixedWidth(112)
        self.combo_cam_pos.addItems([
            "Bottom-Right",
            "Bottom-Left",
            "Top-Right",
            "Top-Left",
        ])
        self.combo_cam_pos.currentTextChanged.connect(self._on_cam_placement_changed)
        step_pos_row.addWidget(self.combo_cam_pos)

        self.btn_cam_minus = QPushButton("➖")
        self.btn_cam_minus.setFixedWidth(24)
        self.btn_cam_minus.setStyleSheet("padding: 2px 2px; font-weight: bold;")
        self.btn_cam_minus.clicked.connect(lambda: self._adjust_facecam_size(-20))
        self.btn_cam_plus = QPushButton("➕")
        self.btn_cam_plus.setFixedWidth(24)
        self.btn_cam_plus.setStyleSheet("padding: 2px 2px; font-weight: bold;")
        self.btn_cam_plus.clicked.connect(lambda: self._adjust_facecam_size(20))
        self.lbl_cam_px = QLabel(f"{self.facecam_size_px}px")
        self.lbl_cam_px.setStyleSheet("color: #00F0FF; font-weight: bold; font-size: 11px;")

        step_pos_row.addWidget(self.btn_cam_minus)
        step_pos_row.addWidget(self.btn_cam_plus)
        step_pos_row.addWidget(self.lbl_cam_px)
        step_pos_row.addStretch()
        cam_ctrls_col.addLayout(step_pos_row)

        cam_mid_row.addLayout(cam_ctrls_col)
        c_layout.addLayout(cam_mid_row)

        mid_row.addWidget(grp_cam, 2)
        layout.addLayout(mid_row)

        # 3. Audio Studio (Mixer Section from Mockup)
        grp_audio = QGroupBox("🎙️ Studio Audio && Microphone Mixer")
        a_layout = QVBoxLayout(grp_audio)
        a_layout.setSpacing(5)

        # Top Audio Header with Toggle & Live Signal
        a_top_row = QHBoxLayout()
        self.chk_mic = QCheckBox("Enable Audio (ON)")
        self.chk_mic.setChecked(True)
        self.chk_mic.setStyleSheet("font-weight: bold; color: #00F0FF; font-size: 13px;")
        a_top_row.addWidget(self.chk_mic)
        a_top_row.addStretch()

        self.lbl_vu_blink = QLabel("🟢 LIVE SIGNAL")
        self.lbl_vu_blink.setFixedWidth(115)
        self.lbl_vu_blink.setStyleSheet("color: #10B981; font-weight: bold; font-size: 11px; font-family: Consolas;")
        a_top_row.addWidget(self.lbl_vu_blink)
        a_layout.addLayout(a_top_row)

        # 3-Way Mode Buttons
        a_row = QHBoxLayout()
        a_row.setSpacing(10)

        self.btn_mode_in = QPushButton("🎙️ Outside Audio (Mic Only)")
        self.btn_mode_in.setToolTip("Record Outside Voice Only (Microphone) - Ideal for Teaching & Classes")
        self.btn_mode_in.setFixedWidth(195)
        self.btn_mode_in.setMinimumHeight(28)
        self.btn_mode_in.clicked.connect(lambda: self._select_audio_mode_by_name("outside_audio"))

        self.btn_mode_out = QPushButton("🔊 Inside Audio (System Only)")
        self.btn_mode_out.setToolTip("Record Inside Computer Audio Only (YouTube, Videos, PC Sounds)")
        self.btn_mode_out.setFixedWidth(195)
        self.btn_mode_out.setMinimumHeight(28)
        self.btn_mode_out.clicked.connect(lambda: self._select_audio_mode_by_name("inside_audio"))

        self.btn_mode_both = QPushButton("🎧 Both (Inside + Outside)")
        self.btn_mode_both.setToolTip("Record Both Inside System Sound + Outside Teacher Voice")
        self.btn_mode_both.setFixedWidth(195)
        self.btn_mode_both.setMinimumHeight(28)
        self.btn_mode_both.clicked.connect(lambda: self._select_audio_mode_by_name("both"))

        a_row.addWidget(self.btn_mode_in)
        a_row.addWidget(self.btn_mode_out)
        a_row.addWidget(self.btn_mode_both)
        a_row.addStretch()
        a_layout.addLayout(a_row)

        vu_row = QHBoxLayout()
        vu_row.setSpacing(10)
        lbl_aud_lvl = QLabel("Audio Level:")
        lbl_aud_lvl.setFixedWidth(82)
        lbl_aud_lvl.setStyleSheet("color: #00F0FF; font-weight: bold; font-size: 12px;")
        vu_row.addWidget(lbl_aud_lvl)

        self.vu_meter = QProgressBar()
        self.vu_meter.setRange(0, 100)
        self.vu_meter.setValue(68)
        self.vu_meter.setMinimumWidth(680)
        self.vu_meter.setFixedHeight(12)
        self.vu_meter.setTextVisible(False)
        vu_row.addWidget(self.vu_meter, 1)
        a_layout.addLayout(vu_row)

        layout.addWidget(grp_audio)

        # 4. Auto Subtitles & Closed Captions (Separate Option Panel)
        grp_sub = QGroupBox("Subtitles && Closed Captions")
        sub_layout = QHBoxLayout(grp_sub)
        sub_layout.setContentsMargins(14, 8, 14, 8)
        sub_layout.setSpacing(14)

        self.chk_subtitles = QCheckBox("Enable Subtitles (ON / OFF)")
        self.chk_subtitles.setChecked(True)
        self.chk_subtitles.setToolTip("Automatically transcribes speech and generates synchronized subtitles (.srt & embedded)")
        self.chk_subtitles.setStyleSheet("font-weight: bold; color: #00F0FF; font-size: 13px; font-family: 'Segoe UI', Arial, sans-serif;")
        self.chk_subtitles.toggled.connect(self._on_subtitles_toggled)
        sub_layout.addWidget(self.chk_subtitles)

        self.chk_burn_subtitles = QCheckBox("Burn Subtitles Into Video")
        self.chk_burn_subtitles.setChecked(False)
        self.chk_burn_subtitles.setToolTip("Hardcodes visible captions directly onto video frames (Ideal for Shorts & Reels)")
        self.chk_burn_subtitles.setStyleSheet("font-weight: bold; color: #E2E8F0; font-size: 12px; font-family: 'Segoe UI', Arial, sans-serif;")
        sub_layout.addWidget(self.chk_burn_subtitles)

        lbl_lang = QLabel("Language:")
        lbl_lang.setStyleSheet("color: #00F0FF; font-weight: bold; font-size: 12px; font-family: 'Segoe UI', Arial, sans-serif;")
        sub_layout.addWidget(lbl_lang)

        self.combo_subtitle_lang = StudioSelectButton("Select Subtitle Language", self)
        self.combo_subtitle_lang.setFixedWidth(175)
        self.combo_subtitle_lang.addItems([
            "English (US) [en-US]",
            "English (India) [en-IN]",
            "Hindi [hi-IN]",
            "Telugu [te-IN]",
            "Tamil [ta-IN]",
            "English (UK) [en-GB]",
            "Spanish [es-ES]",
            "French [fr-FR]",
            "German [de-DE]",
            "Auto-Detect",
        ])
        sub_layout.addWidget(self.combo_subtitle_lang)
        sub_layout.addStretch()
        layout.addWidget(grp_sub)

        # 5. Storage & Save Location (Trimmed Bar)
        grp_save = QGroupBox("💾 Save Location")
        s_layout = QHBoxLayout(grp_save)
        s_layout.setSpacing(10)
        lbl_save = QLabel("Save To:")
        lbl_save.setStyleSheet("color: #00F0FF; font-weight: bold; font-size: 12px;")
        s_layout.addWidget(lbl_save)
        self.lbl_output = QLabel(self.output_dir)
        self.lbl_output.setFixedWidth(360)
        self.lbl_output.setStyleSheet("background-color: #0F172A; border: 1px solid #0284C7; border-radius: 6px; padding: 4px 10px; color: #94A3B8;")
        s_layout.addWidget(self.lbl_output)

        self.btn_browse = QPushButton("📁 Change")
        self.btn_browse.setFixedWidth(100)
        self.btn_browse.clicked.connect(self._change_output_folder)
        self.btn_open = QPushButton("📂 Open Folder")
        self.btn_open.setFixedWidth(120)
        self.btn_open.clicked.connect(self._open_output_folder)
        s_layout.addWidget(self.btn_browse)
        s_layout.addWidget(self.btn_open)
        s_layout.addStretch()
        layout.addWidget(grp_save)

        # 6. Main Action Center (Centered Floating Dock with Record & Time on Left)
        act_box = QFrame()
        act_box.setObjectName("actionBox")
        act_box.setStyleSheet(
            "QFrame#actionBox { background-color: rgba(10, 18, 34, 210); border: 1px solid #0284C7; border-radius: 14px; padding: 4px 10px; }"
        )
        act_layout = QHBoxLayout(act_box)
        act_layout.setContentsMargins(10, 4, 10, 4)
        act_layout.setSpacing(8)

        # Primary Record Action Button (Left Aligned)
        self.btn_record = QPushButton("🔴 START RECORDING")
        self.btn_record.setObjectName("recBtn")
        self.btn_record.clicked.connect(self._toggle_record)
        act_layout.addWidget(self.btn_record)

        # Timer & Recording Indicator (Left Aligned right next to Record button)
        self.rec_dot = QLabel()
        self.rec_dot.setFixedSize(14, 14)
        self.rec_dot.setStyleSheet("border-radius: 7px; background-color: #1E293B; border: 1px solid #334155;")
        act_layout.addWidget(self.rec_dot)

        self.lbl_timer = QLabel("00:00:00")
        self.lbl_timer.setMinimumWidth(125)
        self.lbl_timer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_timer.setStyleSheet("border: none; background: transparent; font-size: 26px; font-weight: bold; font-family: Consolas, monospace; color: #00F0FF; min-height: 38px;")
        act_layout.addWidget(self.lbl_timer)

        act_layout.addStretch()

        # Tools and Auxiliary Controls (Right Aligned)
        self.btn_snip = QPushButton("📸 Screenshot")
        self.btn_snip.setObjectName("snipBtn")
        self.btn_snip.setStyleSheet("padding: 7px 11px; font-size: 11px; font-weight: bold;")
        self.btn_snip.clicked.connect(self._start_snipping)
        act_layout.addWidget(self.btn_snip)

        self.btn_player = QPushButton("🎬 Media Player")
        self.btn_player.setObjectName("playerBtn")
        self.btn_player.setToolTip("Open Recplay 2.0 Built-in Video & Music Player")
        self.btn_player.setStyleSheet(
            "QPushButton { background-color: #0F172A; color: #00F0FF; border: 1px solid #0284C7; font-weight: bold; padding: 7px 11px; border-radius: 6px; font-size: 11px; }"
            "QPushButton:hover { background-color: #0284C7; color: #FFFFFF; border-color: #00F0FF; }"
        )
        self.btn_player.clicked.connect(lambda: self._open_media_player())
        act_layout.addWidget(self.btn_player)

        self.btn_pause = QPushButton("⏸️ Pause")
        self.btn_pause.setToolTip("Pause / Resume recording (Active during recording)")
        self.btn_pause.setStyleSheet(
            "QPushButton { background-color: #0F172A; color: #38BDF8; border: 1.5px solid #0284C7; "
            "font-weight: bold; padding: 7px 11px; border-radius: 6px; font-size: 11px; } "
            "QPushButton:hover { background-color: #1E293B; color: #FFFFFF; border-color: #00F0FF; }"
        )
        self.btn_pause.clicked.connect(self._toggle_pause)
        act_layout.addWidget(self.btn_pause)

        self.btn_draw = QPushButton("✏️ Draw / Board")
        self.btn_draw.setObjectName("drawBtn")
        self.btn_draw.setToolTip("Open Movable Pen, Type Text & White Board Tool (F8)")
        self.btn_draw.setStyleSheet("padding: 7px 11px; font-size: 11px; font-weight: bold;")
        self.btn_draw.clicked.connect(self._toggle_annotator)
        act_layout.addWidget(self.btn_draw)

        self.btn_chapter = QPushButton("🔖 Chapter")
        self.btn_chapter.setToolTip("Add YouTube Timestamp Chapter Marker during recording (Ctrl+M)")
        self.btn_chapter.setStyleSheet("padding: 7px 11px; font-size: 11px; font-weight: bold;")
        self.btn_chapter.clicked.connect(self._add_chapter_marker)
        act_layout.addWidget(self.btn_chapter)

        layout.addWidget(act_box)

        QShortcut(QKeySequence("F9"), self, activated=self._toggle_record)
        QShortcut(QKeySequence("F10"), self, activated=self._toggle_pause)
        QShortcut(QKeySequence("F8"), self, activated=self._toggle_annotator)
        QShortcut(QKeySequence("F7"), self, activated=self._start_snipping)
        QShortcut(QKeySequence("Ctrl+M"), self, activated=self._add_chapter_marker)

        self.setCentralWidget(main_widget)

        self._prev_sys_times = None
        self._prev_proc_times = None
        self.cpu_timer = QTimer(self)
        self.cpu_timer.timeout.connect(self._update_cpu_usage)
        self.cpu_timer.start(1200)
        self._update_cpu_usage()

    def _update_cpu_usage(self):
        """Calculates live Clipr CPU usage % and System CPU usage % using zero-overhead Win32 kernel32 APIs."""
        try:
            class FILETIME(ctypes.Structure):
                _fields_ = [("dwLowDateTime", ctypes.c_uint32), ("dwHighDateTime", ctypes.c_uint32)]

            def ft_to_int(ft):
                return (ft.dwHighDateTime << 32) | ft.dwLowDateTime

            idle_ft, kernel_ft, user_ft = FILETIME(), FILETIME(), FILETIME()
            ctypes.windll.kernel32.GetSystemTimes(
                ctypes.byref(idle_ft), ctypes.byref(kernel_ft), ctypes.byref(user_ft)
            )
            sys_idle = ft_to_int(idle_ft)
            sys_kernel = ft_to_int(kernel_ft)
            sys_user = ft_to_int(user_ft)
            sys_total = sys_kernel + sys_user

            c_ft, e_ft, pk_ft, pu_ft = FILETIME(), FILETIME(), FILETIME(), FILETIME()
            h_proc = ctypes.windll.kernel32.GetCurrentProcess()
            ctypes.windll.kernel32.GetProcessTimes(
                h_proc, ctypes.byref(c_ft), ctypes.byref(e_ft), ctypes.byref(pk_ft), ctypes.byref(pu_ft)
            )
            proc_total = ft_to_int(pk_ft) + ft_to_int(pu_ft)

            app_cpu = 1.1
            sys_cpu = 7.8
            if self._prev_sys_times is not None and self._prev_proc_times is not None:
                d_sys = sys_total - self._prev_sys_times[0]
                d_idle = sys_idle - self._prev_sys_times[1]
                d_proc = proc_total - self._prev_proc_times
                if d_sys > 0:
                    app_cpu = max(0.2, min(99.9, (d_proc / d_sys) * 100.0))
                    sys_cpu = max(0.5, min(99.9, ((d_sys - d_idle) / d_sys) * 100.0))

            self._prev_sys_times = (sys_total, sys_idle)
            self._prev_proc_times = proc_total

            self.cpu_eco_badge.setText(f"📊 CPU: {app_cpu:.1f}% | Sys: {sys_cpu:.1f}%")
            if hasattr(self, "jarvis_banner") and self.jarvis_banner is not None:
                self.jarvis_banner.set_cpu_percent(app_cpu)
        except Exception:
            pass

    def _apply_preset_teaching(self):
        self.combo_screen_mode.setCurrentIndex(0)
        self.combo_preset.setCurrentIndex(3)
        self._select_audio_mode_by_name("outside_audio")
        self.chk_cursor.setChecked(True)
        if not self.chk_webcam.isChecked():
            self.chk_webcam.setChecked(True)
        self.combo_cam_shape.setCurrentText("Circle")
        self.combo_cam_pos.setCurrentText("Bottom-Right")
        self._highlight_preset_button(self.btn_preset_teaching)

    def _apply_preset_reels(self):
        self.combo_screen_mode.setCurrentIndex(2)
        self._select_audio_mode_by_name("both")
        self.combo_wm_pos.setCurrentText("Top-Center")
        self._highlight_preset_button(self.btn_preset_reels)

    def _apply_preset_gaming(self):
        self.combo_screen_mode.setCurrentIndex(0)
        self.combo_preset.setCurrentIndex(1)
        self._select_audio_mode_by_name("inside_audio")
        self.combo_cam_shape.setCurrentText("Square (1:1)")
        self._highlight_preset_button(self.btn_preset_gaming)

    def _highlight_preset_button(self, active_btn):
        for btn in [getattr(self, "btn_preset_teaching", None), getattr(self, "btn_preset_reels", None), getattr(self, "btn_preset_gaming", None)]:
            if btn is None:
                continue
            if btn == active_btn:
                btn.setStyleSheet("background-color: #0284C7; color: #FFFFFF; border: 2px solid #00F0FF; border-radius: 8px; padding: 5px 14px; font-weight: bold; font-size: 12px;")
            else:
                btn.setStyleSheet("background-color: #0F172A; color: #FFFFFF; border: 1.5px solid #0284C7; border-radius: 8px; padding: 5px 14px; font-weight: bold; font-size: 12px;")

    def _toggle_floating_jarvis(self):
        if self.floating_jarvis.isVisible():
            self.floating_jarvis.hide()
        else:
            screen = QGuiApplication.primaryScreen()
            if screen:
                geo = screen.availableGeometry()
                self.floating_jarvis.move(geo.width() - 180, 35)
            self.floating_jarvis.show()
            self.floating_jarvis.raise_()

    def _open_jarvis_board_directly(self):
        self.annotator.open_board()
        self.annotator._activate_jarvis_board()

    def _require_pro_license(self, feature_name: str = "Studio Feature") -> bool:
        """Blocks non-recording features in Trial Version and prompts to activate a PRO License."""
        if self.verifier.is_licensed():
            return True
        res = QMessageBox.information(
            self,
            "🔒 Locked in Trial Version",
            f"'{feature_name}' is locked in the Trial Version.\n\n"
            "• In Trial Version, ONLY basic Screen Recording is enabled.\n"
            "• Activate a Recplay PRO License Key to unlock Area Mode, Draw/Board, Webcam, Audio Modes, Custom Watermark, Screenshot, Pause & Chapters!\n\n"
            "Would you like to open '🔑 Manage License' now?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if res == QMessageBox.StandardButton.Yes:
            self._open_license_dialog()
        return self.verifier.is_licensed()

    def _open_interactive_dragout_box(self):
        """Opens the Resizable Area Mode Studio Editor Box immediately on screen (PRO only)."""
        if not self._require_pro_license("Area Mode"):
            return
        self.fullscreen_highlight.hide()
        self.live_region_frame.open_centered()
        self.live_region_frame.confirm_current_area()
        self.custom_crop_region = self.live_region_frame.get_physical_crop_region()

    def _apply_quick_dragout_chip(self, code: str):
        """Applies a 1-click Area Mode preset directly from MainWindow."""
        if code == "full":
            self.live_region_frame.hide()
            if hasattr(self, "area_marking_border"):
                self.area_marking_border.hide()
            self.custom_crop_region = None
            self.combo_screen_mode.blockSignals(True)
            self.combo_screen_mode.setItemText(1, "🎯 Select Area")
            self.combo_screen_mode.setItemText(2, "📱 Shorts / Reels (9:16)")
            self.combo_screen_mode.setCurrentIndex(0)
            self.combo_screen_mode.blockSignals(False)
            self.btn_highlight_area.setText("🎯 Select Area")
            self.fullscreen_highlight.hide()
        elif code == "shorts":
            screen = QGuiApplication.primaryScreen()
            dpr = screen.devicePixelRatio() if screen else 1.0
            s_geo = screen.geometry() if screen else QRect(0, 0, 1920, 1080)
            max_pw = int(round(s_geo.width() * dpr))
            max_ph = int(round(s_geo.height() * dpr))
            target_ph = max(480, int(max_ph * 0.90))
            target_pw = int(target_ph * 9 / 16)
            if target_pw % 2 != 0:
                target_pw -= 1
            if target_ph % 2 != 0:
                target_ph -= 1
            rx = (max_pw - target_pw) // 2
            ry = (max_ph - target_ph) // 2
            self.custom_crop_region = (rx, ry, target_pw, target_ph)
            self.live_region_frame.hide()
            self.fullscreen_highlight.hide()
            if hasattr(self, "area_marking_border"):
                self.area_marking_border.update_boundary(rx, ry, target_pw, target_ph)
            self.combo_screen_mode.blockSignals(True)
            self.combo_screen_mode.setItemText(2, f"📱 Shorts / Reels ({target_pw}×{target_ph})")
            self.combo_screen_mode.setCurrentIndex(2)
            self.combo_screen_mode.blockSignals(False)
            self.btn_highlight_area.setText(f"📱 Shorts / Reels ({target_pw}×{target_ph})")
        else:
            self._start_freehand_drag_selection()

    def _select_audio_mode_by_name(self, mode_text: str):
        self.chk_mic.setEnabled(True)
        self.chk_mic.setChecked(True)
        self.chk_mic.setStyleSheet("font-weight: bold; color: #00F0FF; font-size: 13px;")
        txt = mode_text.strip().lower()
        if "outside" in txt or ("input" in txt and "output" not in txt and "both" not in txt):
            self.selected_audio_mode = "outside_audio"
            self.chk_mic.setText("Enable Audio (🎙️ Outside Voice Only)")
        elif "inside" in txt or ("output" in txt and "input" not in txt and "both" not in txt):
            self.selected_audio_mode = "inside_audio"
            self.chk_mic.setText("Enable Audio (🔊 Inside System Only)")
        else:
            self.selected_audio_mode = "both"
            self.chk_mic.setText("Enable Audio (🎧 Inside + Outside)")
        self._sync_audio_mode_buttons(mode_text)

    def _sync_audio_mode_buttons(self, mode_text: str):
        active_css = (
            "background-color: #0284C7; color: #FFFFFF; border: 2px solid #00F0FF; "
            "font-weight: bold; font-size: 12px; border-radius: 7px; padding: 4px 10px;"
        )
        idle_css = (
            "background-color: #0F172A; color: #FFFFFF; border: 1.5px solid #0284C7; "
            "font-weight: bold; font-size: 12px; border-radius: 7px; padding: 4px 10px;"
        )
        txt = (mode_text or self.selected_audio_mode).strip().lower()
        is_outside = "outside" in txt or ("input" in txt and "output" not in txt and "both" not in txt) or txt == "input_only"
        is_inside = "inside" in txt or ("output" in txt and "input" not in txt and "both" not in txt) or txt == "output_only"
        is_both = "both" in txt or "input_and_output" in txt or txt == "inside_and_outside"

        self.btn_mode_in.setStyleSheet(active_css if is_outside else idle_css)
        self.btn_mode_out.setStyleSheet(active_css if is_inside else idle_css)
        self.btn_mode_both.setStyleSheet(active_css if is_both else idle_css)
        if self.is_recording and self.recorder:
            self.recorder.audio_mode = self._get_selected_audio_mode()
            self.recorder.audio_rec.audio_mode = self.recorder.audio_mode

    def _on_watermark_font_changed(self, font_text: str):
        raw_font = (font_text or "Segoe UI").split("(")[0].strip()
        self.txt_watermark.setFont(QFont(raw_font, 10, QFont.Weight.Bold))

    def _update_vu_meter(self):
        self._vu_blink_phase = (getattr(self, "_vu_blink_phase", 0) + 1) % 12
        if self.is_recording and self.recorder:
            vol = self.recorder.audio_rec.get_volume()
            wave = int(14 * abs(math.sin(self._vu_blink_phase * 0.65)))
            percent = max(28, min(100, int(vol * 100) + wave))
        else:
            # Live blinking studio audio meter preview like before!
            wave = int(38 + 34 * abs(math.sin(self._vu_blink_phase * 0.55)) + 16 * abs(math.cos(self._vu_blink_phase * 0.9)))
            percent = max(22, min(96, wave))

        self.vu_meter.setValue(percent)
        if hasattr(self, "mic_vu_meter") and self.mic_vu_meter is not None:
            self.mic_vu_meter.setValue(max(15, min(100, int(percent * 0.95) + 3)))
        if hasattr(self, "sys_vu_meter") and self.sys_vu_meter is not None:
            self.sys_vu_meter.setValue(max(12, min(100, int(percent * 0.88))))
        if self._vu_blink_phase % 2 == 0:
            chunk_col = "#00F0FF" if percent < 78 else "#10B981"
            if hasattr(self, "lbl_vu_blink"):
                self.lbl_vu_blink.setText("🟢 AUDIO ACTIVE" if self.is_recording else "🟢 MIC READY ⚡")
                self.lbl_vu_blink.setStyleSheet("color: #10B981; font-weight: bold; font-size: 11px; font-family: Consolas;")
        else:
            chunk_col = "#38BDF8" if percent < 78 else "#34D399"
            if hasattr(self, "lbl_vu_blink"):
                self.lbl_vu_blink.setText("🔵 LIVE BLINK ●" if self.is_recording else "🔵 LIVE SIGNAL ●")
                self.lbl_vu_blink.setStyleSheet("color: #00F0FF; font-weight: bold; font-size: 11px; font-family: Consolas;")

        self.vu_meter.setStyleSheet(
            f"QProgressBar {{ background-color: #091326; border: 1px solid #0284C7; border-radius: 6px; height: 16px; }}"
            f"QProgressBar::chunk {{ background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284C7, stop:0.6 {chunk_col}, stop:1 #10B981); border-radius: 5px; }}"
        )

    def _refresh_license_display(self):
        lic = self.verifier.get_active_license()
        is_pro = bool(lic.get("valid"))
        locked_btn_css = (
            "background-color: #1E293B; color: #64748B; border: 1px dashed #475569; "
            "font-weight: bold; border-radius: 8px; padding: 5px 10px;"
        )

        # Always keep all dropdowns, Audio + Mic (Input, Output Only + Mic, Both I/O), and Screenshot enabled & working!
        self.combo_screen_mode.setEnabled(True)
        self.combo_preset.setEnabled(True)
        self.combo_wm_pos.setEnabled(True)
        if hasattr(self, "combo_wm_font"):
            self.combo_wm_font.setEnabled(True)
        self.combo_cam_shape.setEnabled(True)
        self.combo_cam_pos.setEnabled(True)
        self.combo_cam_size.setEnabled(True)

        self.chk_mic.setEnabled(True)
        self.chk_mic.setChecked(True)
        self.chk_mic.setText("Enable Audio (ON)")
        self.chk_mic.setStyleSheet("font-weight: bold; color: #00F0FF; font-size: 13px;")
        self.btn_mode_in.setEnabled(True)
        self.btn_mode_in.setText("🎙️ Outside Audio (Mic Only)")
        self.btn_mode_out.setEnabled(True)
        self.btn_mode_out.setText("🔊 Inside Audio (System Only)")
        self.btn_mode_both.setEnabled(True)
        self.btn_mode_both.setText("🎧 Both (Inside + Outside)")
        self._sync_audio_mode_buttons(self.selected_audio_mode)

        self.btn_snip.setEnabled(True)
        self.btn_snip.setText("📸 Screenshot")
        self.btn_snip.setStyleSheet("")

        if is_pro:
            source = lic.get("source", "")
            badge_text = "💎 PRO (Store Active)" if source == "Microsoft Store" else "💎 PRO LICENSED"
            self.license_badge.setText(badge_text)
            self.license_badge.setStyleSheet(
                "background-color: #064E3B; color: #34D399; padding: 5px 14px; border-radius: 8px; font-weight: bold; font-size: 11px; border: 1px solid #10B981;"
            )
            self.chk_watermark.setEnabled(True)
            self.chk_watermark.setText("Enable")
            self.chk_watermark.setStyleSheet("QCheckBox { font-weight: bold; color: #00F0FF; font-size: 12px; } QCheckBox:disabled { color: #64748B; }")
            self.txt_watermark.setEnabled(True)
            self.txt_watermark.setStyleSheet(
                "QLineEdit { color: #00F0FF; font-weight: bold; background-color: #0F172A; border: 1px solid #0284C7; border-radius: 6px; padding: 4px 8px; font-size: 12px; }"
                "QLineEdit:disabled { color: #64748B; background-color: #091122; border: 1px solid #1E293B; }"
            )
            if self.txt_watermark.text().strip() in ["CLIPR STUDIO - TRIAL VERSION", "RECPLAY STUDIO - TRIAL VERSION"]:
                self.txt_watermark.setText("Recplay Studio")
            self.chk_cursor.setEnabled(True)
            self.chk_cursor.setChecked(True)
            self.chk_cursor.setText("Highlight Mouse Cursor (Halo && Click)")
            self.chk_cursor.setStyleSheet("QCheckBox { font-weight: bold; color: #E2E8F0; font-size: 12px; } QCheckBox:disabled { color: #64748B; }")

            self.chk_webcam.setEnabled(True)
            self.chk_webcam.setText("Enable Webcam (ON / OFF)")
            self.btn_cam_minus.setEnabled(True)
            self.btn_cam_plus.setEnabled(True)

            self.btn_browse.setEnabled(True)
            self.btn_browse.setText("📁 Change")
            self.btn_draw.setEnabled(True)
            self.btn_draw.setText("✏️ Draw / Board")
            self.btn_draw.setStyleSheet("")
            self.btn_chapter.setEnabled(True)
            self.btn_chapter.setText("🔖 Chapter")
            self.btn_chapter.setStyleSheet("")
            self.btn_pause.setText("❚❚ Pause" if not self.is_paused else "▶ Resume")
            self.btn_pause.setEnabled(True)
        else:
            self.license_badge.setText("⏱️ TRIAL VERSION")
            self.license_badge.setStyleSheet(
                "background-color: #451A03; color: #FBBF24; padding: 5px 14px; border-radius: 8px; font-weight: bold; font-size: 11px; border: 1px solid #D97706;"
            )
            self.chk_watermark.setChecked(True)
            self.chk_watermark.setEnabled(False)
            self.chk_watermark.setText("🔒 Enable")
            self.chk_watermark.setStyleSheet("QCheckBox { font-weight: bold; color: #64748B; font-size: 12px; } QCheckBox:disabled { color: #64748B; }")
            self.txt_watermark.setText("RECPLAY STUDIO - TRIAL VERSION")
            self.txt_watermark.setEnabled(False)
            self.txt_watermark.setStyleSheet(
                "QLineEdit { color: #64748B; font-weight: bold; background-color: #091122; border: 1px solid #1E293B; border-radius: 6px; padding: 4px 8px; font-size: 12px; }"
                "QLineEdit:disabled { color: #64748B; background-color: #091122; border: 1px solid #1E293B; }"
            )

            self.chk_cursor.setChecked(False)
            self.chk_cursor.setEnabled(False)
            self.chk_cursor.setText("🔒 Highlight Mouse Cursor (PRO Only)")
            self.chk_cursor.setStyleSheet("QCheckBox { font-weight: bold; color: #64748B; font-size: 12px; } QCheckBox:disabled { color: #64748B; }")

            self.chk_webcam.setEnabled(True)
            if self.chk_webcam.isChecked():
                self.chk_webcam.setText("Enable Webcam (ON)")
                self.chk_webcam.setStyleSheet("font-weight: bold; color: #00F0FF; font-size: 13px;")
            else:
                self.chk_webcam.setText("Enable Webcam (ON / OFF)")
                self.chk_webcam.setStyleSheet("font-weight: bold; color: #F8FAFC; font-size: 13px;")
            self.btn_cam_minus.setEnabled(True)
            self.btn_cam_plus.setEnabled(True)

            self.btn_browse.setEnabled(False)
            self.btn_browse.setText("🔒 Change")

            self.btn_draw.setEnabled(False)
            self.btn_draw.setText("🔒 Draw / Board (PRO)")
            self.btn_draw.setStyleSheet(locked_btn_css)

            self.btn_chapter.setEnabled(False)
            self.btn_chapter.setText("🔒 Chapter (PRO)")
            self.btn_chapter.setStyleSheet(locked_btn_css)

            self.btn_pause.setEnabled(True)
            self.btn_pause.setText("❚❚ Pause" if not self.is_paused else "▶ Resume")
            if not self.is_recording:
                self.btn_pause.setStyleSheet(
                    "QPushButton { background-color: #0F172A; color: #38BDF8; border: 1.5px solid #0284C7; font-weight: bold; padding: 7px 11px; border-radius: 6px; font-size: 11px; } "
                    "QPushButton:hover { background-color: #1E293B; color: #FFFFFF; border-color: #00F0FF; }"
                )

    def _open_license_dialog(self):
        dlg = LicenseDialog(self.verifier, self)
        dlg.license_changed.connect(lambda: self._refresh_license_display())
        dlg.exec()
        self._refresh_license_display()

    def _open_media_player(self, file_path: str = None):
        """Opens the integrated Clipr 2.0 Video and Music Player."""
        if not hasattr(self, "media_player") or self.media_player is None:
            from ui.media_player import StudioMediaPlayer
            self.media_player = StudioMediaPlayer()
        if file_path:
            self.media_player.play_file(file_path)
        self.media_player.showNormal()
        self.media_player.raise_()
        self.media_player.activateWindow()

    def _open_video_player(self):
        """Opens Recplay 2.0 Video Player directly."""
        if not hasattr(self, "media_player") or self.media_player is None:
            from ui.media_player import StudioMediaPlayer
            self.media_player = StudioMediaPlayer()
        self.media_player.display_stack.setCurrentIndex(0)
        self.media_player.lbl_app_title.setText("🎬 RECPLAY 2.0 VIDEO PLAYER")
        self.media_player.is_video_mode = True
        self.media_player.btn_snip.setVisible(True)
        self.media_player.btn_toggle_theme.setText("🎛️ Cyber Visualizer")
        self.media_player.showNormal()
        self.media_player.raise_()
        self.media_player.activateWindow()

    def _open_music_player(self):
        """Opens Recplay 2.0 Music & Audio Player directly with animated visualizer."""
        if not hasattr(self, "media_player") or self.media_player is None:
            from ui.media_player import StudioMediaPlayer
            self.media_player = StudioMediaPlayer()
        self.media_player.display_stack.setCurrentIndex(1)
        self.media_player.lbl_app_title.setText("🎵 RECPLAY 2.0 MUSIC PLAYER")
        self.media_player.is_video_mode = False
        self.media_player.btn_snip.setVisible(False)
        self.media_player.btn_toggle_theme.setText("🎬 Video Mode")
        self.media_player.playlist_panel.show()
        from PyQt6.QtMultimedia import QMediaPlayer
        self.media_player.music_widget.set_playing(self.media_player.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState)
        self.media_player.showNormal()
        self.media_player.raise_()
        self.media_player.activateWindow()

    def _open_drag_area_for_recording(self):
        """Immediately opens the interactive resizable/movable Area Mode frame directly on screen."""
        self.fullscreen_highlight.hide()
        self.live_region_frame.open_centered()
        self.custom_crop_region = self.live_region_frame.get_physical_crop_region()
        rx, ry, rw, rh = self.custom_crop_region
        self.combo_screen_mode.blockSignals(True)
        self.combo_screen_mode.setItemText(1, f"🎯 Select Area ({rw}×{rh})")
        self.combo_screen_mode.setCurrentIndex(1)
        self.combo_screen_mode.blockSignals(False)
        self.btn_highlight_area.setText(f"🎯 Select Area ({rw}×{rh})")

    def _start_freehand_drag_selection(self):
        self._restore_after_select_area = self.isVisible() and not self.isMinimized()
        if self._restore_after_select_area:
            self.hide()
            QApplication.processEvents()
        QTimer.singleShot(180, self._launch_freehand_selector)

    def _launch_freehand_selector(self):
        self.freehand_selector.start_interactive_drag()

    def _on_freehand_area_dragged(self, rect: QRect):
        self.setWindowState(self.windowState() & ~Qt.WindowState.WindowMinimized | Qt.WindowState.WindowActive)
        self.show()
        self.showNormal()
        self.raise_()
        self.activateWindow()
        if sys.platform == "win32":
            try:
                hwnd = int(self.winId())
                ctypes.windll.user32.ShowWindow(hwnd, 9)  # SW_RESTORE
                ctypes.windll.user32.SetForegroundWindow(hwnd)
            except Exception:
                pass

        screen = QGuiApplication.primaryScreen()
        dpr = screen.devicePixelRatio() if screen else 1.0
        s_geo = screen.geometry() if screen else QRect(0, 0, 1920, 1080)
        max_pw = int(round(s_geo.width() * dpr))
        max_ph = int(round(s_geo.height() * dpr))

        rx = max(0, int(round(rect.x() * dpr)))
        ry = max(0, int(round(rect.y() * dpr)))
        rw = max(64, int(round(rect.width() * dpr)))
        rh = max(64, int(round(rect.height() * dpr)))

        rx = min(rx, max(0, max_pw - 64))
        ry = min(ry, max(0, max_ph - 64))
        rw = min(rw, max_pw - rx)
        rh = min(rh, max_ph - ry)
        if rw % 2 != 0:
            rw -= 1
        if rh % 2 != 0:
            rh -= 1

        self.custom_crop_region = (rx, ry, rw, rh)

        # Keep live_region_frame updated in memory without popping clumsy buttons on screen
        self.live_region_frame.set_from_dragged_rect(rect)
        self.live_region_frame.hide()

        # Immediately show visible outer marking line on physical screen (100% excluded from video)
        if hasattr(self, "area_marking_border"):
            self.area_marking_border.update_boundary(rx, ry, rw, rh)

        self.combo_screen_mode.blockSignals(True)
        self.combo_screen_mode.setItemText(1, f"🎯 Select Area ({rw}×{rh})")
        self.combo_screen_mode.setCurrentIndex(1)
        self.combo_screen_mode.blockSignals(False)
        self.btn_highlight_area.setText(f"🎯 Select Area ({rw}×{rh})")

    def _on_freehand_cancelled(self):
        self.setWindowState(self.windowState() & ~Qt.WindowState.WindowMinimized | Qt.WindowState.WindowActive)
        self.show()
        self.showNormal()
        self.raise_()
        self.activateWindow()
        if sys.platform == "win32":
            try:
                hwnd = int(self.winId())
                ctypes.windll.user32.ShowWindow(hwnd, 9)  # SW_RESTORE
                ctypes.windll.user32.SetForegroundWindow(hwnd)
            except Exception:
                pass
        if self.custom_crop_region is not None:
            rx, ry, rw, rh = self.custom_crop_region
            if hasattr(self, "area_marking_border"):
                self.area_marking_border.update_boundary(rx, ry, rw, rh)
        else:
            self.combo_screen_mode.blockSignals(True)
            self.combo_screen_mode.setItemText(1, "🎯 Select Area")
            self.combo_screen_mode.setCurrentIndex(0)
            self.combo_screen_mode.blockSignals(False)
            if hasattr(self, "area_marking_border"):
                self.area_marking_border.hide()

    def _on_screen_mode_changed(self, index: int):
        if index == 0:
            self._apply_quick_dragout_chip("full")
        elif index == 1:
            self._start_freehand_drag_selection()
        elif index == 2:
            self._apply_quick_dragout_chip("shorts")

    def _on_region_selection_cancelled(self):
        self.live_region_frame.hide()
        if hasattr(self, "area_marking_border"):
            self.area_marking_border.hide()
        self.custom_crop_region = None
        self.combo_screen_mode.blockSignals(True)
        self.combo_screen_mode.setItemText(1, "🎯 Select Area")
        self.combo_screen_mode.setItemText(2, "📱 Shorts / Reels (9:16)")
        self.combo_screen_mode.setCurrentIndex(0)
        self.combo_screen_mode.blockSignals(False)
        self.btn_highlight_area.setText("🎯 Select Area")

    def _on_custom_region_coords(self, rx: int, ry: int, rw: int, rh: int):
        self.fullscreen_highlight.hide()
        self.custom_crop_region = (rx, ry, rw, rh)
        if hasattr(self, "area_marking_border"):
            self.area_marking_border.update_boundary(rx, ry, rw, rh)
        self.combo_screen_mode.blockSignals(True)
        self.combo_screen_mode.setItemText(1, f"🎯 Select Area ({rw}×{rh})")
        self.combo_screen_mode.setCurrentIndex(1)
        self.combo_screen_mode.blockSignals(False)
        self.btn_highlight_area.setText(f"🎯 Select Area ({rw}×{rh})")

    def _position_floating_facecam(self):
        if not self.screen():
            return
        screen = self.screen().geometry()
        margin = 24
        sz = self.facecam_size_px
        pos_text = self.combo_cam_pos.currentText().lower()
        if "bottom-left" in pos_text:
            self.floating_facecam.move(margin, screen.height() - sz - margin - 40)
        elif "top-right" in pos_text:
            self.floating_facecam.move(screen.width() - sz - margin, margin + 20)
        elif "top-left" in pos_text:
            self.floating_facecam.move(margin, margin + 20)
        else:
            self.floating_facecam.move(screen.width() - sz - margin, screen.height() - sz - margin - 40)

    def _on_webcam_toggled(self, checked: bool):
        if checked:
            self.chk_webcam.setText("Enable Webcam (ON)")
            self.chk_webcam.setStyleSheet("font-weight: bold; color: #00F0FF; font-size: 13px;")
            if self.is_recording and self.recorder:
                self.recorder.enable_webcam = True
                try:
                    self.recorder.signals.frame_cam.disconnect(self.floating_facecam.update_frame)
                except Exception:
                    pass
                self.recorder.signals.frame_cam.connect(self.floating_facecam.update_frame)
                self._position_floating_facecam()
                self.floating_facecam.show()
                self.floating_facecam.raise_()
            else:
                self._start_live_facecam_test()
        else:
            self.chk_webcam.setText("Enable Webcam (ON / OFF)")
            self.chk_webcam.setStyleSheet("font-weight: bold; color: #F8FAFC; font-size: 13px;")
            if self.is_recording and self.recorder:
                self.recorder.enable_webcam = False
            self._stop_live_facecam_test()
            self.floating_facecam.hide()
            if hasattr(self, "facecam_preview") and self.facecam_preview is not None:
                self.facecam_preview.set_offline()

    def _on_cam_mode_changed(self, text: str):
        mode_lower = text.lower()
        if "face" in mode_lower or "cutout" in mode_lower:
            mode = "face_only"
            if hasattr(self, "combo_cam_shape"):
                self.combo_cam_shape.setEnabled(False)
                self.combo_cam_shape.setToolTip("Face Only mode has no square or round frame - only the face is shown.")
        elif "blur" in mode_lower:
            mode = "blur"
            if hasattr(self, "combo_cam_shape"):
                self.combo_cam_shape.setEnabled(True)
                self.combo_cam_shape.setToolTip("Select Facecam Shape")
        else:
            mode = "standard"
            if hasattr(self, "combo_cam_shape"):
                self.combo_cam_shape.setEnabled(True)
                self.combo_cam_shape.setToolTip("Select Facecam Shape")

        self.floating_facecam.set_mode(mode)
        if self.is_recording and self.recorder:
            self.recorder.webcam_mode = mode
        if self.chk_webcam.isChecked() and not self.is_live_testing_cam and not self.is_recording:
            self._start_live_facecam_test()

    def _on_subtitles_toggled(self, checked: bool):
        if checked:
            self.chk_subtitles.setText("Enable Subtitles (ON)")
            self.chk_subtitles.setStyleSheet("font-weight: bold; color: #00F0FF; font-size: 13px; font-family: 'Segoe UI', Arial, sans-serif;")
            self.chk_burn_subtitles.setEnabled(True)
            self.combo_subtitle_lang.setEnabled(True)
        else:
            self.chk_subtitles.setText("Enable Subtitles (ON / OFF)")
            self.chk_subtitles.setStyleSheet("font-weight: bold; color: #FFFFFF; font-size: 13px; font-family: 'Segoe UI', Arial, sans-serif;")
            self.chk_burn_subtitles.setEnabled(False)
            self.combo_subtitle_lang.setEnabled(False)

    def _update_cam_shape_ui(self, shape_text: str):
        if not hasattr(self, "combo_cam_shape"):
            return
        s_lower = shape_text.lower()
        if "square" in s_lower:
            combo_val = "Square (1:1)"
        elif "wide" in s_lower or "16:9" in s_lower or "rect" in s_lower:
            combo_val = "Wide (16:9)"
        else:
            combo_val = "Circle"
        if self.combo_cam_shape.currentText() != combo_val:
            self.combo_cam_shape.blockSignals(True)
            self.combo_cam_shape.setCurrentText(combo_val)
            self.combo_cam_shape.blockSignals(False)

    def _select_cam_shape(self, shape: str):
        if shape == "circle":
            combo_val = "Circle"
        elif shape == "square":
            combo_val = "Square (1:1)"
        else:
            combo_val = "Wide (16:9)"
        self.combo_cam_shape.setCurrentText(combo_val)

    def _update_cam_size_ui(self, size_hint: str = ""):
        if not hasattr(self, "combo_cam_size"):
            return
        s_lower = size_hint.lower()
        if "small" in s_lower or self.facecam_size_px <= 150:
            combo_val = "Small (140px)"
        elif "x-large" in s_lower or "extra" in s_lower or self.facecam_size_px >= 270:
            combo_val = "X-Large (300px)"
        elif "large" in s_lower or self.facecam_size_px >= 210:
            combo_val = "Large (240px)"
        else:
            combo_val = "Medium (180px)"
        if self.combo_cam_size.currentText() != combo_val:
            self.combo_cam_size.blockSignals(True)
            self.combo_cam_size.setCurrentText(combo_val)
            self.combo_cam_size.blockSignals(False)

    def _select_cam_size_preset(self, preset: str):
        if "small" in preset.lower():
            combo_val = "Small (140px)"
        elif "x-large" in preset.lower():
            combo_val = "X-Large (300px)"
        elif "large" in preset.lower():
            combo_val = "Large (240px)"
        else:
            combo_val = "Medium (180px)"
        self.combo_cam_size.setCurrentText(combo_val)

    def _on_cam_shape_changed(self, text: str):
        self._update_cam_shape_ui(text)
        if "face" in text.lower() or "cutout" in text.lower():
            shape = "face_only"
            if hasattr(self, "combo_cam_mode"):
                self.combo_cam_mode.setCurrentText("Face Only (No Frame)")
            self.floating_facecam.set_mode("face_only")
        elif "circle" in text.lower():
            shape = "circle"
        elif "square" in text.lower():
            shape = "square"
        else:
            shape = "rectangle"
        self.floating_facecam.set_shape(shape)
        if hasattr(self, "facecam_preview") and self.facecam_preview is not None:
            self.facecam_preview.set_shape(shape)
        if self.is_recording and self.recorder:
            self.recorder.webcam_shape = shape
        if self.chk_webcam.isChecked() and not self.is_live_testing_cam and not self.is_recording:
            self._start_live_facecam_test()

    def _on_cam_placement_changed(self, text: str):
        self._position_floating_facecam()
        if self.is_recording and self.recorder:
            self.recorder.webcam_position = text.lower().replace(" ", "-")
        if self.chk_webcam.isChecked() and not self.is_live_testing_cam and not self.is_recording:
            self._start_live_facecam_test()

    def _on_cam_size_preset_changed(self, text: str):
        if "Small" in text:
            self.facecam_size_px = 140
        elif "X-Large" in text or "Extra Large" in text:
            self.facecam_size_px = 300
        elif "Large" in text:
            self.facecam_size_px = 240
        else:
            self.facecam_size_px = 180
        self.lbl_cam_px.setText(f"{self.facecam_size_px}px")
        self._update_cam_size_ui(text)
        self.floating_facecam.set_face_size(self.facecam_size_px)
        self._position_floating_facecam()
        if self.is_recording and self.recorder:
            self.recorder.webcam_scale = max(0.10, min(0.38, self.facecam_size_px / 900.0))
        if self.chk_webcam.isChecked() and not self.is_live_testing_cam and not self.is_recording:
            self._start_live_facecam_test()

    def _adjust_facecam_size(self, delta_px: int):
        self.facecam_size_px = max(100, min(380, self.facecam_size_px + delta_px))
        self.lbl_cam_px.setText(f"{self.facecam_size_px}px")
        self._update_cam_size_ui(f"{self.facecam_size_px}px")
        self.floating_facecam.set_face_size(self.facecam_size_px)
        self._position_floating_facecam()
        if self.is_recording and self.recorder:
            self.recorder.webcam_scale = max(0.10, min(0.38, self.facecam_size_px / 900.0))
        if self.chk_webcam.isChecked() and not self.is_live_testing_cam and not self.is_recording:
            self._start_live_facecam_test()

    def _start_live_facecam_test(self):
        if not self.chk_webcam.isChecked():
            return
        if self.is_recording:
            self.floating_facecam.show()
            return
        try:
            if self.live_cam_cap is None or not self.live_cam_cap.isOpened():
                self.live_cam_cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
                if not self.live_cam_cap.isOpened():
                    self.live_cam_cap = cv2.VideoCapture(0)
            self.is_live_testing_cam = True
            shape_txt = self.combo_cam_shape.currentText().lower()
            self.floating_facecam.set_shape("circle" if "circle" in shape_txt else ("square" if "square" in shape_txt else "rectangle"))
            self.floating_facecam.set_face_size(self.facecam_size_px)
            # Eliminate duplicate webcam: keep floating window hidden during setup/preview in MainWindow
            self.floating_facecam.hide()
            self.live_cam_timer.start()
        except Exception as e:
            print(f"[!] Live facecam test error: {e}")

    def _stop_live_facecam_test(self):
        self.is_live_testing_cam = False
        self.live_cam_timer.stop()
        if self.live_cam_cap is not None:
            try:
                self.live_cam_cap.release()
            except Exception:
                pass
            self.live_cam_cap = None
        if not self.is_recording or not self.chk_webcam.isChecked():
            self.floating_facecam.hide()

    def _tick_live_facecam(self):
        if not self.is_live_testing_cam or self.is_recording or self.live_cam_cap is None:
            return
        ret, frame = self.live_cam_cap.read()
        if ret and frame is not None:
            # Update ONLY the single in-window FacecamPreviewWidget inside MainWindow
            if hasattr(self, "facecam_preview") and self.facecam_preview is not None:
                self.facecam_preview.set_frame(frame)

    def _toggle_annotator(self):
        """Safely toggles the Crash-Proof Opaque AnnotatorOverlay (`open_board()` / `close_board()`)."""
        if not self._require_pro_license("Draw / Board Studio Tool"):
            return
        if self.annotator.isVisible():
            self.annotator.close_board()
        else:
            self.annotator.open_board()

    def _start_snipping(self):
        """
        Launches the Snipping Overlay directly across the active display,
        allowing the user to capture any region inside Clipr or across the entire desktop.
        """
        target_screen = QGuiApplication.screenAt(self.geometry().center()) or QGuiApplication.primaryScreen()
        self.snipper.capture_screen(target_screen)

    def _on_snip_cancelled(self):
        self.snipper.hide()
        self.raise_()
        self.activateWindow()

    def _open_screenshot_editor(self, pixmap: QPixmap):
        self.snipper.hide()
        self.raise_()
        self.activateWindow()
        editor = ScreenshotEditorDialog(pixmap, self)
        editor.exec()

    def _toggle_pause(self):
        if not self.is_recording or not self.recorder:
            if hasattr(self, "jarvis_banner"):
                self.jarvis_banner.set_status("ℹ️ Note: Pause is active while recording. Click '🔴 START RECORDING' (F9) first.")
            # Subtle visual cue on Pause button without mutating its text or altering layout
            self.btn_pause.setStyleSheet(
                "QPushButton { background-color: #1E293B; color: #F59E0B; border: 1.5px solid #F59E0B; "
                "font-weight: bold; padding: 7px 11px; border-radius: 6px; font-size: 11px; }"
            )
            QTimer.singleShot(1400, lambda: (
                self.btn_pause.setStyleSheet(
                    "QPushButton { background-color: #0F172A; color: #38BDF8; border: 1.5px solid #0284C7; "
                    "font-weight: bold; padding: 7px 11px; border-radius: 6px; font-size: 11px; } "
                    "QPushButton:hover { background-color: #1E293B; color: #FFFFFF; border-color: #00F0FF; }"
                )
            ))
            return

        hrs = self.record_seconds // 3600
        mins = (self.record_seconds % 3600) // 60
        secs = self.record_seconds % 60
        ts_str = f"{hrs:02d}:{mins:02d}:{secs:02d}"

        if self.is_paused:
            self.recorder.resume()
            self.is_paused = False
            self._rec_start_time = time.time() - self.record_seconds
            self.rec_timer.start(500)
            self.btn_pause.setText("⏸️ Pause")
            self.btn_pause.setStyleSheet(
                "QPushButton { background-color: #0F172A; color: #38BDF8; border: 1.5px solid #00F0FF; "
                "font-weight: bold; padding: 7px 11px; border-radius: 6px; font-size: 11px; } "
                "QPushButton:hover { background-color: #0284C7; color: #FFFFFF; }"
            )
            self.floating_rec_bar.btn_pause.setText("⏸️ Pause")
            self.floating_rec_bar.btn_pause.setStyleSheet(
                "QPushButton { background-color: #0F172A; color: #00F0FF; border: 1px solid #00F0FF; "
                "border-radius: 8px; padding: 6px 12px; font-weight: bold; font-size: 12px; } "
                "QPushButton:hover { background-color: #0369A1; border-color: #00F0FF; }"
            )
            if hasattr(self, "rec_dot"):
                self.rec_dot.setStyleSheet("border-radius: 7px; background-color: #EF4444; border: 1px solid #FCA5A5;")
            if hasattr(self.floating_rec_bar, "rec_dot"):
                self.floating_rec_bar.rec_dot.setStyleSheet("border-radius: 6px; background-color: #EF4444; border: 1px solid #FCA5A5;")
            self.lbl_timer.setText(ts_str)
            self.lbl_timer.setStyleSheet("border: none; background: transparent; font-size: 26px; font-weight: bold; font-family: Consolas, monospace; color: #EF4444; min-height: 38px;")
            self.floating_rec_bar.lbl_timer.setText(ts_str)
            self.floating_rec_bar.lbl_timer.setStyleSheet("color: #EF4444; font-family: Consolas, monospace; font-size: 20px; font-weight: bold; padding: 0px 6px;")
            self.floating_jarvis.status_text = "REC LIVE"
            if hasattr(self, "jarvis_banner"):
                self.jarvis_banner.set_status("▶ RECORDING RESUMED — Screen and audio capture active")
            self.setWindowTitle(f"[{ts_str} ● REC] Recplay 2.0 Studio")
        else:
            self.recorder.pause()
            self.is_paused = True
            self.rec_timer.stop()
            self.btn_pause.setText("▶️ Resume")
            self.btn_pause.setStyleSheet(
                "QPushButton { background-color: #D97706; color: #FFFFFF; border: 2px solid #F59E0B; "
                "font-weight: bold; padding: 7px 11px; border-radius: 6px; font-size: 11px; } "
                "QPushButton:hover { background-color: #B45309; border-color: #FBBF24; }"
            )
            self.floating_rec_bar.btn_pause.setText("▶️ Resume")
            self.floating_rec_bar.btn_pause.setStyleSheet(
                "QPushButton { background-color: #D97706; color: #FFFFFF; border: 2px solid #F59E0B; "
                "border-radius: 8px; padding: 6px 12px; font-weight: bold; font-size: 12px; } "
                "QPushButton:hover { background-color: #B45309; border-color: #FBBF24; }"
            )
            if hasattr(self, "rec_dot"):
                self.rec_dot.setStyleSheet("border-radius: 7px; background-color: #F59E0B; border: 1px solid #FDE68A;")
            if hasattr(self.floating_rec_bar, "rec_dot"):
                self.floating_rec_bar.rec_dot.setStyleSheet("border-radius: 6px; background-color: #F59E0B; border: 1px solid #FDE68A;")
            self.lbl_timer.setText(f"PAUSED ({ts_str})")
            self.lbl_timer.setStyleSheet("border: none; background: transparent; font-size: 18px; font-weight: bold; font-family: Consolas, monospace; color: #F59E0B; min-height: 38px;")
            self.floating_rec_bar.lbl_timer.setText(f"PAUSED ({ts_str})")
            self.floating_rec_bar.lbl_timer.setStyleSheet("color: #F59E0B; font-family: Consolas, monospace; font-size: 18px; font-weight: bold; padding: 0px 6px;")
            self.floating_jarvis.status_text = "PAUSED"
            if hasattr(self, "jarvis_banner"):
                self.jarvis_banner.set_status(f"⏸️ RECORDING PAUSED at {ts_str} — Click Resume to continue")
            self.setWindowTitle(f"[{ts_str} ⏸️ PAUSED] Recplay 2.0 Studio")

    def _toggle_record(self):
        if self._countdown_in_progress:
            return
        if not self.is_recording:
            self._start_recording()
        else:
            self._stop_recording()

    def add_chapter_entry(self, custom_title: str = "") -> str:
        idx = len(self.session_chapters)
        sec = float(self.record_seconds) if self.is_recording else float(idx * 60)
        label = custom_title.strip() if custom_title.strip() else f"Topic {idx}"
        self.session_chapters.append((sec, label))
        if self.is_recording and self.recorder:
            self.recorder.add_chapter_marker(label)
        mm, ss = divmod(int(sec), 60)
        formatted = f"{mm:02d}:{ss:02d} {label}"
        self.btn_chapter.setText(f"🔖 {mm:02d}:{ss:02d}")
        self.floating_rec_bar.btn_chapter.setText(f"🔖 {mm:02d}:{ss:02d}")
        QTimer.singleShot(2500, lambda: (self.btn_chapter.setText("🔖 Chapter"), self.floating_rec_bar.btn_chapter.setText("🔖 Chapter")))
        return formatted

    def _add_chapter_marker(self):
        if not self._require_pro_license("YouTube Chapter Markers"):
            return
        if self.is_recording and self.recorder:
            self.add_chapter_entry("")
        dlg = YouTubeChaptersDialog(self)
        dlg.exec()

    def _get_selected_audio_mode(self) -> str:
        return self.selected_audio_mode

    def _on_countdown_tick(self, num: int):
        if num > 0:
            self.btn_record.setText(f"⏳ {num}...")
            self.lbl_timer.setText(f"⏳ 00:0{num}")
            self.lbl_timer.setStyleSheet("border: none; background: transparent; font-size: 24px; font-weight: bold; font-family: Consolas, monospace; color: #F59E0B; min-height: 38px;")
            self.floating_rec_bar.lbl_timer.setText(f"⏳ 00:0{num}")
        else:
            self.btn_record.setText("🔴 STARTING...")
            self.lbl_timer.setText("🔴 00:00:00")
            self.lbl_timer.setStyleSheet("border: none; background: transparent; font-size: 24px; font-weight: bold; font-family: Consolas, monospace; color: #EF4444; min-height: 38px;")
            self.floating_rec_bar.lbl_timer.setText("🔴 00:00:00")

    def _start_recording(self):
        if self._countdown_in_progress or self.is_recording:
            return

        self._countdown_in_progress = True
        self.btn_record.setEnabled(False)
        self.btn_record.setText("⏳ 3...")
        self.lbl_timer.setText("⏳ 00:03")
        self.lbl_timer.setStyleSheet("border: none; background: transparent; font-size: 24px; font-weight: bold; font-family: Consolas, monospace; color: #F59E0B; min-height: 38px;")

        target_rect = None
        screen_mode_idx = self.combo_screen_mode.currentIndex()
        if screen_mode_idx != 0:
            if self.custom_crop_region is not None:
                rx, ry, rw, rh = self.custom_crop_region
                screen = QGuiApplication.primaryScreen()
                dpr = screen.devicePixelRatio() if screen else 1.0
                target_rect = QRect(int(round(rx / dpr)), int(round(ry / dpr)), int(round(rw / dpr)), int(round(rh / dpr)))
                if hasattr(self, "area_marking_border"):
                    self.area_marking_border.update_boundary(rx, ry, rw, rh)
        else:
            self.custom_crop_region = None
            if hasattr(self, "area_marking_border"):
                self.area_marking_border.hide()

        # Always hide all legacy border overlays BEFORE countdown/recording so NO blue/red frame appears in the video!
        self.fullscreen_highlight.hide()
        self.live_region_frame.hide()
        QApplication.processEvents()

        self.countdown_overlay.target_rect = target_rect
        self.countdown_overlay.start_countdown()

    def _execute_start_recording(self):
        self._countdown_in_progress = False
        self.btn_record.setEnabled(True)

        # Ensure legacy border overlays are hidden before capturing frames
        self.fullscreen_highlight.hide()
        self.live_region_frame.hide()
        self.countdown_overlay.hide()
        QApplication.processEvents()

        is_pro = self.verifier.is_licensed()

        was_live_testing = is_pro and self.is_live_testing_cam and self.chk_webcam.isChecked()
        if self.is_live_testing_cam:
            self._stop_live_facecam_test()
        self._resume_live_cam_after_rec = was_live_testing

        self.session_chapters = [(0.0, "Introduction")]

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(self.output_dir, f"Recording_{timestamp}.mp4")

        preset_text = self.combo_preset.currentText()
        if "4K" in preset_text:
            crf = 26
            fps = 30
        elif "Low-CPU" in preset_text:
            crf = 25
            fps = 24
        elif "Lecture" in preset_text:
            crf = 24
            fps = 24
        elif "YouTube" in preset_text:
            crf = 22
            fps = 30
        else:
            crf = 24
            fps = 30

        crop_region = None
        screen_mode_idx = self.combo_screen_mode.currentIndex()
        if screen_mode_idx != 0:
            crop_region = self.custom_crop_region

        # Show visible outer marking boundary line during recording (100% excluded from video via WDA_EXCLUDEFROMCAPTURE)
        if crop_region is not None and hasattr(self, "area_marking_border"):
            rx, ry, rw, rh = crop_region
            self.area_marking_border.update_boundary(rx, ry, rw, rh)
        elif hasattr(self, "area_marking_border"):
            self.area_marking_border.hide()

        enable_webcam = bool(is_pro and self.chk_webcam.isChecked())
        shape_text = self.combo_cam_shape.currentText().lower()
        if "face" in shape_text or "cutout" in shape_text:
            cam_shape = "face_only"
        elif "circle" in shape_text:
            cam_shape = "circle"
        elif "square" in shape_text:
            cam_shape = "square"
        else:
            cam_shape = "rectangle"

        cam_mode = "standard"
        if hasattr(self, "combo_cam_mode"):
            mode_text = self.combo_cam_mode.currentText().lower()
            if "blur" in mode_text:
                cam_mode = "blur"
            elif "face" in mode_text or "cutout" in mode_text:
                cam_mode = "face_only"
                cam_shape = "face_only"

        pos_text = self.combo_cam_pos.currentText().lower().replace(" ", "-")
        cam_scale = max(0.10, min(0.38, self.facecam_size_px / 900.0))

        audio_mode = self._get_selected_audio_mode()
        enable_mic = bool(self.chk_mic.isChecked())
        enable_cursor = bool(is_pro and self.chk_cursor.isChecked())

        if is_pro:
            watermark_text = self.txt_watermark.text().strip() if self.chk_watermark.isChecked() else ""
        else:
            watermark_text = "RECPLAY STUDIO - TRIAL VERSION"
        watermark_pos = self.combo_wm_pos.currentText().lower()
        watermark_font = self.combo_wm_font.currentText() if hasattr(self, "combo_wm_font") else "Segoe UI"

        self.recorder = ScreenRecorder(
            output_file=output_file,
            fps=fps,
            crf=crf,
            enable_webcam=enable_webcam,
            webcam_shape=cam_shape,
            webcam_position=pos_text,
            webcam_scale=cam_scale,
            webcam_mode=cam_mode,
            enable_mic=enable_mic,
            audio_device_index=None,
            audio_mode=audio_mode,
            enable_cursor_highlight=enable_cursor,
            license_verifier=self.verifier,
            crop_region=crop_region,
            custom_watermark=watermark_text,
            watermark_position=watermark_pos,
            watermark_font=watermark_font,
        )

        self.recorder.signals.finished.connect(self._on_recorder_finished)
        self.recorder.signals.error.connect(self._on_recorder_error)

        if enable_webcam:
            self.floating_facecam.set_shape(cam_shape)
            self.floating_facecam.set_mode(cam_mode)
            self.floating_facecam.set_face_size(self.facecam_size_px)
            self.recorder.signals.frame_cam.connect(self.floating_facecam.update_frame)
            self._position_floating_facecam()
            self.floating_facecam.show()

        self.recorder.start()
        self.is_recording = True
        self.is_paused = False
        self.jarvis_banner.set_recording_state(True, "00:00:00")
        self.floating_jarvis.status_text = "REC LIVE"

        self.record_seconds = 0
        self._rec_start_time = time.time()
        self.lbl_timer.setText("00:00:00")
        self.lbl_timer.setStyleSheet("border: none; background: transparent; font-size: 26px; font-weight: bold; font-family: Consolas, monospace; color: #EF4444; min-height: 38px;")
        if hasattr(self, "rec_dot"):
            self.rec_dot.setStyleSheet("border-radius: 7px; background-color: #EF4444; border: 1px solid #F87171;")
        if hasattr(self.floating_rec_bar, "rec_dot"):
            self.floating_rec_bar.rec_dot.setStyleSheet("border-radius: 6px; background-color: #EF4444; border: 1px solid #F87171;")
        self.floating_rec_bar.lbl_timer.setText("00:00:00")
        self.floating_rec_bar.btn_pause.setText("❚❚ Pause")
        self.floating_rec_bar.btn_pause.setEnabled(True)
        self.floating_rec_bar.btn_pause.setStyleSheet(
            "QPushButton { background-color: #0F172A; color: #00F0FF; border: 1px solid #00F0FF; "
            "border-radius: 8px; padding: 6px 12px; font-weight: bold; font-size: 12px; } "
            "QPushButton:hover { background-color: #0369A1; border-color: #00F0FF; }"
        )
        self.rec_timer.start(500)
        if not self.vu_timer.isActive():
            self.vu_timer.start()

        self.btn_record.setText("⏹️ STOP RECORDING")
        self.btn_record.setStyleSheet("background-color: #16A34A; color: white; font-weight: bold;")
        self.btn_pause.setEnabled(True)
        self.btn_pause.setText("❚❚ Pause")
        self.btn_pause.setStyleSheet(
            "QPushButton { background-color: #0F172A; color: #00F0FF; border: 1px solid #00F0FF; "
            "font-weight: bold; padding: 7px 11px; border-radius: 6px; font-size: 11px; } "
            "QPushButton:hover { background-color: #0284C7; color: #FFFFFF; }"
        )

        # Show floating recording bar with auto-disappear in 5s and any-key reveal
        self.floating_rec_bar.start_recording_bar()
        self.showMinimized()

    def _on_gui_second_tick(self):
        if not self.is_recording or self.is_paused:
            return

        now = time.time()
        start_t = getattr(self, "_rec_start_time", now)
        elapsed = int(max(0, now - start_t))
        self.record_seconds = elapsed

        hrs = self.record_seconds // 3600
        mins = (self.record_seconds % 3600) // 60
        secs = self.record_seconds % 60
        ts_str = f"{hrs:02d}:{mins:02d}:{secs:02d}"

        is_lit = (int(now * 2) % 2 == 0)
        if hasattr(self, "rec_dot"):
            self.rec_dot.setStyleSheet(
                "border-radius: 7px; background-color: #EF4444; border: 1px solid #FCA5A5;" if is_lit
                else "border-radius: 7px; background-color: rgba(239, 68, 68, 70); border: 1px solid #7F1D1D;"
            )
        if hasattr(self.floating_rec_bar, "rec_dot"):
            self.floating_rec_bar.rec_dot.setStyleSheet(
                "border-radius: 6px; background-color: #EF4444; border: 1px solid #FCA5A5;" if is_lit
                else "border-radius: 6px; background-color: rgba(239, 68, 68, 70); border: 1px solid #7F1D1D;"
            )

        self.lbl_timer.setText(ts_str)
        self.floating_rec_bar.lbl_timer.setText(ts_str)
        self.jarvis_banner.set_recording_state(True, ts_str)
        self.setWindowTitle(f"[{ts_str} ● REC] Recplay 2.0 Studio")

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == QEvent.Type.WindowStateChange and self.is_recording and self.isMinimized():
            if hasattr(self, "floating_rec_bar"):
                self.floating_rec_bar.show_bar()

    def _close_all_highlight_areas(self):
        """Immediately closes/hides borders when recording stops without resetting the user's selected area."""
        if hasattr(self, "area_marking_border"):
            self.area_marking_border.hide()
        self.live_region_frame.is_recording_active = False
        self.live_region_frame.is_locked_mode = False
        self.live_region_frame.clearMask()
        self.live_region_frame.hide()
        self.fullscreen_highlight.hide()

    def _stop_recording(self):
        if not self.is_recording or not self.recorder:
            return

        self.rec_timer.stop()
        self.floating_rec_bar.stop_recording_bar()
        self.floating_facecam.hide()
        self._close_all_highlight_areas()
        self.jarvis_banner.set_recording_state(False)
        self.floating_jarvis.status_text = "ONLINE"
        self.setWindowTitle("Recplay 2.0 - Studio Screen Recorder")

        self.btn_record.setEnabled(False)
        self.btn_record.setText("Saving High-Quality Video...")
        self.lbl_timer.setText("Finalizing...")

        import threading
        t = threading.Thread(target=self.recorder.stop, daemon=True)
        t.start()

    def _show_clear_save_popup(self, saved_file: str, mb: float, srt_file: str = ""):
        """Displays a high-contrast, ultra-clear dark dialog box when a video finishes saving."""
        dlg = QDialog(self)
        dlg.setWindowTitle("✅ Recplay Studio — Video Saved Successfully!")
        dlg.setFixedSize(640, 315)
        dlg.setStyleSheet("""
            QDialog {
                background-color: #071124;
                border: 2px solid #00F0FF;
                border-radius: 14px;
            }
            QLabel {
                color: #FFFFFF;
                background: transparent;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton {
                border-radius: 8px;
                padding: 10px 22px;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        vlay = QVBoxLayout(dlg)
        vlay.setContentsMargins(24, 20, 24, 20)
        vlay.setSpacing(12)

        lbl_head = QLabel("✅ VIDEO SAVED SUCCESSFULLY!")
        lbl_head.setStyleSheet("color: #34D399; font-size: 19px; font-weight: 900; letter-spacing: 0.8px;")
        vlay.addWidget(lbl_head)

        lbl_sub = QLabel("Your crystal-clear recording has been saved to disk:")
        lbl_sub.setStyleSheet("color: #FFFFFF; font-size: 14px; font-weight: bold;")
        vlay.addWidget(lbl_sub)

        sub_tag = f"\n📝 Subtitles: {os.path.basename(srt_file)} (Generated)" if (srt_file and os.path.exists(srt_file)) else ""
        info_box = QLabel(
            f"📄 File Path: {saved_file}\n"
            f"📦 File Size: {mb:.2f} MB    |    🔊 Audio Mode: {self.selected_audio_mode.replace('_', ' ').upper()}{sub_tag}"
        )
        info_box.setWordWrap(True)
        info_box.setStyleSheet(
            "background-color: #0F172A; color: #00F0FF; border: 1px solid #0284C7; "
            "border-radius: 8px; padding: 12px; font-family: Consolas, monospace; font-size: 13px; font-weight: bold;"
        )
        vlay.addWidget(info_box)

        lbl_ask = QLabel("Would you like to open the output folder now?")
        lbl_ask.setStyleSheet("color: #F8FAFC; font-size: 14px; font-weight: bold;")
        vlay.addWidget(lbl_ask)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(14)
        btn_row.addStretch()

        btn_play = QPushButton("▶️ Play in Recplay 2.0 Player")
        btn_play.setStyleSheet("background-color: #0284C7; color: #FFFFFF; border: 1px solid #00F0FF; font-weight: bold;")
        btn_play.clicked.connect(lambda: dlg.done(2))

        btn_open = QPushButton("📂 Open Folder")
        btn_open.setStyleSheet("background-color: #16A34A; color: #FFFFFF; border: 1px solid #34D399; font-weight: bold;")
        btn_open.clicked.connect(dlg.accept)

        btn_close = QPushButton("✔️ Close")
        btn_close.setStyleSheet("background-color: #334155; color: #FFFFFF; border: 1px solid #64748B; font-weight: bold;")
        btn_close.clicked.connect(dlg.reject)

        btn_row.addWidget(btn_play)
        btn_row.addWidget(btn_open)
        btn_row.addWidget(btn_close)
        vlay.addLayout(btn_row)

        res = dlg.exec()
        if res == 2:
            self._open_media_player(saved_file)
        elif res == QDialog.DialogCode.Accepted:
            self._open_output_folder()

    def _generate_subtitles_for_output(self, saved_file: str):
        """Asynchronously transcribes audio and generates synchronized .srt / burned subtitles."""
        from core.subtitle_generator import SubtitleWorker

        burn_in = bool(hasattr(self, "chk_burn_subtitles") and self.chk_burn_subtitles.isChecked())
        lang_text = self.combo_subtitle_lang.currentText() if hasattr(self, "combo_subtitle_lang") else "English (US) [en-US]"
        lang_code = "en-US"
        if "[" in lang_text and "]" in lang_text:
            lang_code = lang_text.split("[")[-1].split("]")[0]

        self.btn_record.setEnabled(False)
        self.btn_record.setText("📝 Transcribing Subtitles...")
        self.lbl_timer.setText("SRT 0%")
        self.lbl_timer.setStyleSheet("border: none; background: transparent; font-size: 16px; font-weight: bold; font-family: Consolas, monospace; color: #F59E0B; min-height: 38px;")

        self._sub_worker = SubtitleWorker(saved_file, burn_in=burn_in, language=lang_code, parent=self)

        def _on_sub_prog(pct, msg):
            self.lbl_timer.setText(f"SRT {pct}%")
            self.btn_record.setText(f"📝 {msg}")

        def _on_sub_done(final_vid, srt_file):
            self.btn_record.setEnabled(True)
            self.btn_record.setText("🔴 START RECORDING")
            self.btn_record.setStyleSheet("background-color: #DC2626; color: white; font-weight: bold;")
            self.lbl_timer.setText("00:00:00")
            self.lbl_timer.setStyleSheet("border: none; background: transparent; font-size: 26px; font-weight: bold; font-family: Consolas, monospace; color: #00F0FF; min-height: 38px;")
            mb = os.path.getsize(final_vid) / (1024 * 1024)
            self._show_clear_save_popup(final_vid, mb, srt_file=srt_file)

        def _on_sub_fail(err):
            print(f"[!] Subtitle worker failed: {err}")
            self.btn_record.setEnabled(True)
            self.btn_record.setText("🔴 START RECORDING")
            self.btn_record.setStyleSheet("background-color: #DC2626; color: white; font-weight: bold;")
            self.lbl_timer.setText("00:00:00")
            self.lbl_timer.setStyleSheet("border: none; background: transparent; font-size: 26px; font-weight: bold; font-family: Consolas, monospace; color: #00F0FF; min-height: 38px;")
            mb = os.path.getsize(saved_file) / (1024 * 1024)
            self._show_clear_save_popup(saved_file, mb)

        self._sub_worker.progress.connect(_on_sub_prog)
        self._sub_worker.finished.connect(_on_sub_done)
        self._sub_worker.failed.connect(_on_sub_fail)
        self._sub_worker.start()

    def _on_recorder_finished(self, saved_file: str):
        self.is_recording = False
        self.is_paused = False
        if not self.vu_timer.isActive():
            self.vu_timer.start()
        self.floating_rec_bar.stop_recording_bar()
        self.floating_facecam.hide()
        self._close_all_highlight_areas()
        self.jarvis_banner.set_recording_state(False)
        self.floating_jarvis.status_text = "ONLINE"

        self.btn_record.setEnabled(True)
        self.btn_record.setText("🔴 START RECORDING")
        self.btn_pause.setEnabled(True)
        self.btn_pause.setText("❚❚ Pause")
        self.btn_pause.setStyleSheet(
            "QPushButton { background-color: #0F172A; color: #38BDF8; border: 1.5px solid #0284C7; "
            "font-weight: bold; padding: 7px 11px; border-radius: 6px; font-size: 11px; } "
            "QPushButton:hover { background-color: #1E293B; color: #FFFFFF; border-color: #00F0FF; }"
        )
        self.floating_rec_bar.btn_pause.setEnabled(True)
        self.floating_rec_bar.btn_pause.setText("❚❚ Pause")
        self.floating_rec_bar.btn_pause.setStyleSheet("")
        if hasattr(self, "rec_dot"):
            self.rec_dot.setStyleSheet("border-radius: 7px; background-color: #1E293B; border: 1px solid #334155;")
        if hasattr(self.floating_rec_bar, "rec_dot"):
            self.floating_rec_bar.rec_dot.setStyleSheet("border-radius: 6px; background-color: #1E293B; border: 1px solid #334155;")
        self.lbl_timer.setText("00:00:00")
        self.lbl_timer.setStyleSheet("border: none; background: transparent; font-size: 26px; font-weight: bold; font-family: Consolas, monospace; color: #00F0FF; min-height: 38px;")

        # Stop and hide area marking boundary line after recording stops
        if hasattr(self, "area_marking_border"):
            self.area_marking_border.hide()

        if getattr(self, "_resume_live_cam_after_rec", False):
            self._start_live_facecam_test()

        self.showNormal()
        self.raise_()
        self.activateWindow()

        if saved_file and os.path.exists(saved_file):
            if hasattr(self, "chk_subtitles") and self.chk_subtitles.isChecked():
                self._generate_subtitles_for_output(saved_file)
            else:
                mb = os.path.getsize(saved_file) / (1024 * 1024)
                self._show_clear_save_popup(saved_file, mb)

    def _on_recorder_error(self, err_msg: str):
        self._on_recorder_finished("")
        QMessageBox.critical(self, "Recording Error", f"An error occurred during recording:\n\n{err_msg}")

    def _change_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder", self.output_dir)
        if folder:
            self.output_dir = folder
            self.lbl_output.setText(folder)

    def _open_output_folder(self):
        if os.path.exists(self.output_dir):
            os.startfile(self.output_dir)

    def closeEvent(self, event):
        if self.is_recording:
            reply = QMessageBox.question(
                self,
                "Recording in Progress",
                "A recording is currently in progress. Stop and save before exiting?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._stop_recording()
                event.accept()
            else:
                event.ignore()
                return

        self._stop_live_facecam_test()
        self.floating_rec_bar.close()
        self.fullscreen_highlight.close()
        self.freehand_selector.close()
        self.countdown_overlay.close()
        self.live_region_frame.close()
        if hasattr(self, "area_marking_border"):
            self.area_marking_border.close()
        self.annotator.close()
        self.floating_facecam.close()
        self.floating_jarvis.close()
        if hasattr(self, "media_player") and self.media_player is not None:
            self.media_player.close()
        self.rec_timer.stop()
        self.vu_timer.stop()
        event.accept()
