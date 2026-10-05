"""
Clipr Studio - Clean Movable Draw / Board & White Board Suite
Engineered specifically for Windows 11 with ZERO WA_TranslucentBackground (`WS_EX_LAYERED`)
and ZERO `setGeometry` inside `showEvent`, completely eliminating `VCRUNTIME140.dll` (`0xc0000005`) crashes!

Features:
- Movable Floating Toolbar (`✥ Move` anywhere on screen)
- 🔤 Type Text tool: Click anywhere on the screen or White Board to type letters/words directly on canvas
- ⬜ White Board button: 1-click switch between Full-Screen White Board and Live Screen Overlay
- Essential Tools Only: Pen, Highlighter, Type Text, White Board, Arrow, Box, Line, Eraser, Colors, Size, Undo, Clear, Exit
"""

import time
import math
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QApplication, QLabel, QLineEdit, QTextEdit, QColorDialog, QMenu
)
from PyQt6.QtGui import QPainter, QPen, QColor, QPainterPath, QPixmap, QImage, QFont, QGuiApplication
from PyQt6.QtCore import Qt, QPoint, QPointF, QRect, QRectF, QTimer, pyqtSignal
import cv2
import numpy as np


class DraggableToolbarWidget(QWidget):
    """Draggable floating toolbar container that can be moved anywhere on the screen."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._dragging = False
        self._drag_offset = QPoint(0, 0)
        self.setCursor(Qt.CursorShape.OpenHandCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._drag_offset = event.globalPosition().toPoint() - self.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._dragging and (event.buttons() & Qt.MouseButton.LeftButton):
            new_pos = event.globalPosition().toPoint() - self._drag_offset
            parent_w = self.parentWidget().width() if self.parentWidget() else 1920
            parent_h = self.parentWidget().height() if self.parentWidget() else 1080
            nx = max(4, min(parent_w - self.width() - 4, new_pos.x()))
            ny = max(4, min(parent_h - self.height() - 4, new_pos.y()))
            self.move(nx, ny)
            if self.parentWidget():
                self.parentWidget()._saved_toolbar_pos = QPoint(nx, ny)
                self.parentWidget().update()
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._dragging:
            self._dragging = False
            self.setCursor(Qt.CursorShape.OpenHandCursor)
            event.accept()
            return
        super().mouseReleaseEvent(event)


class DragHandleLabel(QLabel):
    """Dedicated grip badge allowing the user to click & drag the toolbar from the grip label itself."""
    def __init__(self, text: str, toolbar: DraggableToolbarWidget):
        super().__init__(text, toolbar)
        self._toolbar = toolbar
        self.setCursor(Qt.CursorShape.SizeAllCursor)
        self.setStyleSheet(
            "background-color: #0284C7; color: #FFFFFF; border: 1px solid #00F0FF; "
            "border-radius: 6px; padding: 5px 10px; font-weight: bold; font-size: 12px;"
        )
        self.setToolTip("Click & Drag here to move the Draw / Board Toolbar anywhere on the screen!")

    def mousePressEvent(self, event):
        self._toolbar.mousePressEvent(event)

    def mouseMoveEvent(self, event):
        self._toolbar.mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._toolbar.mouseReleaseEvent(event)


class ColorSwatchButton(QPushButton):
    """Compact color chip button for instant MS Paint-style palette selection."""
    def __init__(self, color_hex: str, label_name: str = "", parent=None):
        super().__init__(parent)
        self.color_hex = color_hex
        self.label_name = label_name or color_hex
        self.setFixedSize(20, 20)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(f"Paint Color: {self.label_name} ({color_hex})")
        self.update_appearance(False)

    def update_appearance(self, is_active: bool):
        border = "2px solid #00F0FF" if is_active else "1px solid #475569"
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.color_hex};
                border: {border};
                border-radius: 10px;
                padding: 0px;
                margin: 0px;
            }}
            QPushButton:hover {{
                border: 2px solid #FFFFFF;
            }}
        """)


class AnnotatorOverlay(QWidget):
    request_outside_screenshot = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.shapes = []
        self.current_tool = "pen"
        self.current_color = QColor("#EF4444")  # High-visibility Red default
        self.pen_width = 4
        self.text_font_size = 24
        self.mouse_pos = QPoint(960, 540)
        self._saved_toolbar_pos: QPoint | None = None

        self.is_drawing = False
        self.start_point = None
        self.current_point = None
        self.current_path = []

        # Board Mode: "whiteboard" (Full-Screen Crisp White Board) or "screen" (Live Screen Overlay)
        self.board_mode = "whiteboard"
        self.bg_pixmap: QPixmap | None = None

        # Seamless borderless text typing (no boxes!) starting from the starting of the page
        self.text_input = QLineEdit(self)
        self.text_input.setVisible(False)
        self.text_input.setPlaceholderText("")
        self.text_input.returnPressed.connect(lambda: self._commit_typed_text(advance_next_line=True))
        self._text_anchor_pos = QPoint(60, 60)

        self._setup_floating_toolbar()

    def _setup_floating_toolbar(self):
        """Streamlined, clutter-free movable Clipr Draw & White Board toolbar."""
        self.toolbar = DraggableToolbarWidget(self)
        self.toolbar.setStyleSheet("""
            QWidget {
                background-color: #060D1A;
                border-radius: 12px;
                border: 2px solid #00F0FF;
            }
            QLabel {
                color: #38BDF8;
                font-size: 11px;
                font-weight: bold;
                border: none;
                background: transparent;
            }
            QPushButton {
                background-color: #0F172A;
                color: #F8FAFC;
                border: 1px solid #0284C7;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #0369A1;
                border-color: #00F0FF;
                color: #FFFFFF;
            }
            QPushButton[active="true"] {
                background-color: #0284C7;
                color: #FFFFFF;
                border: 2px solid #00F0FF;
            }
        """)

        main_lay = QVBoxLayout(self.toolbar)
        main_lay.setContentsMargins(8, 6, 8, 6)
        main_lay.setSpacing(5)

        # Row 1: Essential Drawing, Paint Tools, Typing Letters & White Board
        row1 = QHBoxLayout()
        row1.setSpacing(4)

        self.drag_grip = DragHandleLabel("✥ Move", self.toolbar)
        row1.addWidget(self.drag_grip)

        self.btn_pen = QPushButton("✏️ Pen")
        self.btn_brush = QPushButton("🖌️ Brush")
        self.btn_highlighter = QPushButton("🖍️ Highlight")
        self.btn_text = QPushButton("🔤 Type Text")
        self.btn_whiteboard = QPushButton("🖥️ Live Screen")
        self.btn_whiteboard.setProperty("active", "true")
        self.btn_eraser = QPushButton("🧽 Eraser")
        self.btn_line = QPushButton("📏 Line")
        self.btn_arrow = QPushButton("➡️ Arrow")
        self.btn_rect = QPushButton("🔲 Box")
        self.btn_fill_rect = QPushButton("⬛ Fill Box")
        self.btn_circle = QPushButton("⭕ Circle")
        self.btn_fill_circle = QPushButton("🔴 Fill Circle")

        for b in [
            self.btn_pen,
            self.btn_brush,
            self.btn_highlighter,
            self.btn_text,
            self.btn_whiteboard,
            self.btn_eraser,
            self.btn_line,
            self.btn_arrow,
            self.btn_rect,
            self.btn_fill_rect,
            self.btn_circle,
            self.btn_fill_circle,
        ]:
            row1.addWidget(b)
        main_lay.addLayout(row1)

        # Row 2: Color Picker + Quick Paint Palette + Size + Font + Undo / Clear / Save / Exit
        row2 = QHBoxLayout()
        row2.setSpacing(5)

        self.btn_color = QPushButton("🎨 Color")
        self.btn_color.setToolTip("Custom Color Dialog")
        self.btn_color.clicked.connect(self._choose_color)
        self._update_color_button()
        row2.addWidget(self.btn_color)

        # Quick Paint Palette Swatches
        palette_colors = [
            ("#EF4444", "Red"),
            ("#F97316", "Orange"),
            ("#EAB308", "Yellow"),
            ("#10B981", "Green"),
            ("#00F0FF", "Cyan"),
            ("#3B82F6", "Blue"),
            ("#A855F7", "Purple"),
            ("#FFFFFF", "White"),
            ("#0F172A", "Black"),
        ]
        self.swatch_buttons = []
        for hex_code, col_name in palette_colors:
            btn_swatch = ColorSwatchButton(hex_code, col_name, self.toolbar)
            btn_swatch.clicked.connect(lambda checked, h=hex_code: self._set_quick_color(h))
            self.swatch_buttons.append(btn_swatch)
            row2.addWidget(btn_swatch)

        self._update_swatch_selection()

        row2.addSpacing(4)
        self.btn_size = QPushButton("✏️ Size: Med")
        self.btn_size.setToolTip("Line & Brush Stroke Size (Thin / Med / Thick)")

        self.btn_font_size = QPushButton("🔤 Font: 24px")
        self.btn_font_size.setToolTip("Select Font Size for Text on Board / Screen")
        self.btn_font_size.clicked.connect(self._open_font_size_menu)

        self.btn_undo = QPushButton("↩️ Undo")
        self.btn_clear = QPushButton("🗑️ Clear")
        self.btn_save = QPushButton("💾 Save")
        self.btn_save.setToolTip("Save Whiteboard / Drawing as Image (PNG/JPG)")
        self.btn_save.setStyleSheet(
            "background-color: #065F46; color: #34D399; border: 1px solid #10B981; font-weight: bold; padding: 4px 10px;"
        )
        self.btn_close = QPushButton("✖ Exit (ESC)")
        self.btn_close.setStyleSheet(
            "background-color: #DC2626; color: white; border: 1px solid #F87171; font-weight: bold; padding: 4px 10px;"
        )

        row2.addWidget(self.btn_size)
        row2.addWidget(self.btn_font_size)
        row2.addSpacing(4)
        row2.addWidget(self.btn_undo)
        row2.addWidget(self.btn_clear)
        row2.addWidget(self.btn_save)
        row2.addWidget(self.btn_close)
        main_lay.addLayout(row2)

        self.btn_pen.setProperty("active", "true")

        self.btn_pen.clicked.connect(lambda: self._set_tool("pen"))
        self.btn_brush.clicked.connect(lambda: self._set_tool("brush"))
        self.btn_highlighter.clicked.connect(lambda: self._set_tool("highlighter"))
        self.btn_text.clicked.connect(lambda: self._set_tool("text"))
        self.btn_whiteboard.clicked.connect(self._toggle_whiteboard_mode)
        self.btn_eraser.clicked.connect(lambda: self._set_tool("eraser"))
        self.btn_line.clicked.connect(lambda: self._set_tool("line"))
        self.btn_arrow.clicked.connect(lambda: self._set_tool("arrow"))
        self.btn_rect.clicked.connect(lambda: self._set_tool("rect"))
        self.btn_fill_rect.clicked.connect(lambda: self._set_tool("fill_rect"))
        self.btn_circle.clicked.connect(lambda: self._set_tool("circle"))
        self.btn_fill_circle.clicked.connect(lambda: self._set_tool("fill_circle"))

        self.btn_size.clicked.connect(self._cycle_pen_size)
        self.btn_undo.clicked.connect(self.undo)
        self.btn_clear.clicked.connect(self.clear_all)
        self.btn_save.clicked.connect(self.save_board_image)
        self.btn_close.clicked.connect(self.close_board)

        self.toolbar.adjustSize()

    def set_whiteboard_mode(self, active: bool = True):
        """Sets board mode to 'whiteboard' (pure crisp white canvas) or 'screen' (live screen overlay)."""
        if self.text_input.isVisible():
            self._commit_typed_text()
        if active:
            self.board_mode = "whiteboard"
            self.btn_whiteboard.setText("🖥️ Live Screen")
            self.btn_whiteboard.setProperty("active", "true")
            if self.current_color in (QColor("#FFFFFF"), QColor("#00F0FF")):
                self.current_color = QColor("#0F172A")
        else:
            self.board_mode = "screen"
            self.btn_whiteboard.setText("⬜ White Board")
            self.btn_whiteboard.setProperty("active", "false")
            if self.current_color == QColor("#0F172A"):
                self.current_color = QColor("#00F0FF")
        self.btn_whiteboard.style().unpolish(self.btn_whiteboard)
        self.btn_whiteboard.style().polish(self.btn_whiteboard)
        self._update_color_button()
        self.update()

    def open_board(self, mode: str = "whiteboard"):
        """Captures full 1:1 desktop screen without High-DPI zooming and opens directly in White Board mode."""
        self.set_whiteboard_mode(mode == "whiteboard")
        screen = QGuiApplication.primaryScreen()
        screen_geo = screen.geometry() if screen else QRect(0, 0, 1920, 1080)
        if screen:
            raw_pix = None
            try:
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
                raw_pix = screen.grabWindow(0)

            raw_pix.setDevicePixelRatio(1.0)
            self.bg_pixmap = raw_pix.scaled(
                screen_geo.width(),
                screen_geo.height(),
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.bg_pixmap.setDevicePixelRatio(1.0)

        self.setGeometry(screen_geo)
        self.toolbar.adjustSize()
        tb_w = self.toolbar.width()
        tb_h = self.toolbar.height()
        if self._saved_toolbar_pos is not None:
            self.toolbar.move(self._saved_toolbar_pos)
        else:
            self.toolbar.move(max(10, (screen_geo.width() - tb_w) // 2), screen_geo.height() - tb_h - 42)
        self._update_cursor()
        self.show()
        self.raise_()
        self.activateWindow()

    def close_board(self):
        if self.text_input.isVisible():
            self._commit_typed_text()
        self.hide()

    def hideEvent(self, event):
        super().hideEvent(event)

    def _update_cursor(self):
        if self.current_tool == "text":
            self.setCursor(Qt.CursorShape.IBeamCursor)
        else:
            self.setCursor(Qt.CursorShape.CrossCursor)

    def _toggle_whiteboard_mode(self):
        """1-Click toggle between Full-Screen White Board and Live Screen Overlay."""
        self.set_whiteboard_mode(self.board_mode != "whiteboard")

    def _choose_color(self):
        col = QColorDialog.getColor(self.current_color, self, "Select Drawing Color")
        if col.isValid():
            self.current_color = col
            self._update_color_button()
            if self.text_input.isVisible():
                self._style_text_input()
            self.update()

    def _update_color_button(self):
        if not hasattr(self, "btn_color"):
            return
        hex_c = self.current_color.name()
        text_c = "#FFFFFF" if self.current_color.lightness() < 130 else "#000000"
        self.btn_color.setText("🎨 Color")
        self.btn_color.setStyleSheet(
            f"background-color: {hex_c}; color: {text_c}; border: 2px solid #00F0FF; "
            f"font-weight: bold; font-size: 11px; padding: 4px 10px; border-radius: 6px;"
        )
        self._update_swatch_selection()

    def _update_swatch_selection(self):
        cur_hex = self.current_color.name().upper()
        for btn in getattr(self, "swatch_buttons", []):
            is_active = (btn.color_hex.upper() == cur_hex)
            btn.update_appearance(is_active)

    def _set_quick_color(self, hex_str: str):
        self.current_color = QColor(hex_str)
        self._update_color_button()
        if self.text_input.isVisible():
            self._style_text_input()
        self.update()

    def _cycle_pen_size(self):
        if self.pen_width == 4:
            self.pen_width = 8
            self.btn_size.setText("✏️ Size: Thick")
        elif self.pen_width == 8:
            self.pen_width = 2
            self.btn_size.setText("✏️ Size: Thin")
        else:
            self.pen_width = 4
            self.btn_size.setText("✏️ Size: Med")

    def _open_font_size_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #0F172A;
                color: #F8FAFC;
                border: 1px solid #00F0FF;
                border-radius: 6px;
                padding: 4px;
                font-size: 13px;
                font-weight: bold;
            }
            QMenu::item {
                padding: 6px 24px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #0284C7;
                color: #FFFFFF;
            }
        """)
        for sz, label in [
            (18, "18px (Small)"),
            (24, "24px (Normal)"),
            (32, "32px (Medium)"),
            (40, "40px (Large)"),
            (48, "48px (Huge)"),
        ]:
            prefix = "✓ " if self.text_font_size == sz else "   "
            action = menu.addAction(f"{prefix}{label}")
            action.triggered.connect(lambda checked, s=sz: self._set_font_size(s))
        menu.exec(self.btn_font_size.mapToGlobal(QPoint(0, self.btn_font_size.height() + 2)))

    def _set_font_size(self, size: int):
        self.text_font_size = size
        self.btn_font_size.setText(f"🔤 Font: {size}px")
        if self.text_input.isVisible():
            self._style_text_input()
            box_h = max(30, self.text_font_size + 14)
            self.text_input.setFixedHeight(box_h)

    def _set_tool(self, tool_name: str):
        if self.text_input.isVisible():
            self._commit_typed_text(advance_next_line=False)
        self.current_tool = tool_name
        for btn, name in [
            (getattr(self, "btn_pen", None), "pen"),
            (getattr(self, "btn_brush", None), "brush"),
            (getattr(self, "btn_highlighter", None), "highlighter"),
            (getattr(self, "btn_text", None), "text"),
            (getattr(self, "btn_eraser", None), "eraser"),
            (getattr(self, "btn_line", None), "line"),
            (getattr(self, "btn_arrow", None), "arrow"),
            (getattr(self, "btn_rect", None), "rect"),
            (getattr(self, "btn_fill_rect", None), "fill_rect"),
            (getattr(self, "btn_circle", None), "circle"),
            (getattr(self, "btn_fill_circle", None), "fill_circle"),
        ]:
            if btn is not None:
                btn.setProperty("active", "true" if name == tool_name else "false")
                btn.style().unpolish(btn)
                btn.style().polish(btn)
        self._update_cursor()
        if tool_name == "text":
            # Immediately start typing from the starting of the page (top-left margin)
            self._open_text_input_at(QPoint(60, 60))

    def _style_text_input(self):
        col = QColor(self.current_color)
        hex_c = col.name()
        if self.board_mode == "whiteboard":
            if hex_c.lower() in ("#ffffff", "#f8fafc", "#e2e8f0"):
                hex_c = "#0F172A"
        # 100% Seamless & Borderless: NO BOX, NO OUTLINE!
        self.text_input.setStyleSheet(
            f"QLineEdit {{ background: transparent; border: none; outline: none; "
            f"color: {hex_c}; font-family: 'Segoe UI', Arial, sans-serif; "
            f"font-size: {self.text_font_size}px; font-weight: bold; "
            f"padding: 0px; margin: 0px; selection-background-color: #0284C7; }}"
        )

    def _open_text_input_at(self, pos: QPoint):
        if self.text_input.isVisible() and self.text_input.text().strip():
            self._commit_typed_text(advance_next_line=False)
        self._text_anchor_pos = QPoint(pos.x(), pos.y())
        self._style_text_input()
        self.text_input.clear()

        # Span across the page without any box
        max_w = max(280, self.width() - pos.x() - 40)
        box_h = max(30, self.text_font_size + 14)
        self.text_input.setGeometry(pos.x(), pos.y(), max_w, box_h)
        self.text_input.setVisible(True)
        self.text_input.raise_()
        self.text_input.setFocus()

    def _commit_typed_text(self, advance_next_line: bool = False):
        if not self.text_input.isVisible():
            return
        txt = self.text_input.text()
        self.text_input.clear()
        if txt.strip():
            col = QColor(self.current_color)
            if self.board_mode == "whiteboard" and col.name().lower() in ("#ffffff", "#f8fafc", "#e2e8f0"):
                col = QColor("#0F172A")
            self.shapes.append({
                "type": "text",
                "pos": QPoint(self._text_anchor_pos.x(), self._text_anchor_pos.y() + self.text_font_size),
                "text": txt,
                "color": col,
                "font_size": self.text_font_size,
            })
            self.update()

        if advance_next_line and txt.strip():
            # Automatically advance to next line starting from the starting of the page (left margin: 60)
            next_y = self._text_anchor_pos.y() + self.text_font_size + 14
            if next_y < self.height() - 100:
                self._open_text_input_at(QPoint(60, next_y))
                return

        self.text_input.setVisible(False)
        self.setFocus()

    def save_board_image(self):
        """Saves current Whiteboard or screen annotations cleanly without toolbar."""
        if hasattr(self, "text_input") and self.text_input.isVisible():
            self._commit_typed_text(advance_next_line=False)

        # Temporarily hide toolbar for clean capture
        self.toolbar.hide()
        QApplication.processEvents()

        clean_pixmap = self.grab()
        self.toolbar.show()

        import datetime
        from pathlib import Path
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        save_dir = Path.home() / "Pictures" / "Recplay_Whiteboards"
        save_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        default_file = str(save_dir / f"Recplay_Board_{ts}.png")

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "💾 Save Whiteboard / Drawing",
            default_file,
            "PNG Image (*.png);;JPEG Image (*.jpg);;BMP Image (*.bmp)",
        )
        if file_path:
            clean_pixmap.save(file_path)
            QMessageBox.information(
                self,
                "✅ Board Saved",
                f"Whiteboard / Drawing saved successfully!\n\n📁 {file_path}",
            )

    def undo(self):
        if self.text_input.isVisible():
            self.text_input.clear()
            self.text_input.setVisible(False)
            return
        if self.shapes:
            self.shapes.pop()
            self.update()

    def clear_all(self):
        if self.text_input.isVisible():
            self.text_input.clear()
            self.text_input.setVisible(False)
        self.shapes.clear()
        self.update()

    def mousePressEvent(self, event):
        pos = event.position().toPoint()
        self.mouse_pos = pos
        if event.button() == Qt.MouseButton.LeftButton:
            if self.toolbar.geometry().contains(pos):
                return

            if self.current_tool == "text":
                self._open_text_input_at(pos)
                return

            if self.text_input.isVisible():
                self._commit_typed_text()

            self.is_drawing = True
            self.start_point = pos
            self.current_point = pos
            self.current_path = [pos]

    def mouseMoveEvent(self, event):
        pos = event.position().toPoint()
        self.mouse_pos = pos
        if self.is_drawing:
            self.current_point = pos
            if self.current_tool in ("pen", "brush", "highlighter", "eraser"):
                self.current_path.append(pos)
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.is_drawing:
            self.is_drawing = False
            self.current_point = event.position().toPoint()

            color = QColor(self.current_color)
            if self.current_tool == "highlighter":
                color.setAlpha(95)
                width = 24
            elif self.current_tool == "brush":
                width = max(10, self.pen_width * 3)
            elif self.current_tool == "eraser":
                color = QColor(255, 255, 255) if self.board_mode == "whiteboard" else QColor(15, 23, 42)
                width = 32
            else:
                if self.board_mode == "whiteboard" and color == QColor("#FFFFFF"):
                    color = QColor("#0F172A")
                width = self.pen_width

            if self.current_tool in ("pen", "brush", "highlighter", "eraser"):
                self.shapes.append({
                    "type": "path",
                    "points": list(self.current_path),
                    "color": color,
                    "width": width,
                    "is_brush": (self.current_tool == "brush"),
                    "is_eraser": (self.current_tool == "eraser"),
                })
            elif self.current_tool == "arrow":
                self.shapes.append({
                    "type": "arrow",
                    "start": self.start_point,
                    "end": self.current_point,
                    "color": color,
                    "width": width + 1,
                })
            elif self.current_tool == "rect":
                self.shapes.append({
                    "type": "rect",
                    "start": self.start_point,
                    "end": self.current_point,
                    "color": color,
                    "width": width,
                    "filled": False,
                })
            elif self.current_tool == "fill_rect":
                self.shapes.append({
                    "type": "rect",
                    "start": self.start_point,
                    "end": self.current_point,
                    "color": color,
                    "width": 1,
                    "filled": True,
                })
            elif self.current_tool == "circle":
                self.shapes.append({
                    "type": "circle",
                    "start": self.start_point,
                    "end": self.current_point,
                    "color": color,
                    "width": width,
                    "filled": False,
                })
            elif self.current_tool == "fill_circle":
                self.shapes.append({
                    "type": "circle",
                    "start": self.start_point,
                    "end": self.current_point,
                    "color": color,
                    "width": 1,
                    "filled": True,
                })
            elif self.current_tool == "line":
                self.shapes.append({
                    "type": "line",
                    "start": self.start_point,
                    "end": self.current_point,
                    "color": color,
                    "width": width,
                })

            self.current_path = []
            self.update()

    def paintEvent(self, event):
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # 1. Draw Selected Board Canvas (Live Screen vs Clear White Board with No Lines)
            if self.board_mode == "whiteboard":
                painter.fillRect(self.rect(), QColor(255, 255, 255))
            else:
                if self.bg_pixmap is not None:
                    painter.drawPixmap(self.rect(), self.bg_pixmap)
                else:
                    painter.fillRect(self.rect(), QColor(11, 17, 32))

            # 2. Draw existing persistent shapes & typed text
            for s in self.shapes:
                if s["type"] == "text":
                    font = QFont("Segoe UI", int(s.get("font_size", 24)), QFont.Weight.Bold)
                    painter.setFont(font)
                    painter.setPen(s["color"])
                    painter.drawText(s["pos"], s["text"])
                    continue

                pen_col = QColor(255, 255, 255) if (s.get("is_eraser") and self.board_mode == "whiteboard") else s["color"]
                pen = QPen(
                    pen_col,
                    s["width"],
                    Qt.PenStyle.SolidLine,
                    Qt.PenCapStyle.RoundCap,
                    Qt.PenJoinStyle.RoundJoin,
                )
                painter.setPen(pen)
                painter.setBrush(Qt.BrushStyle.NoBrush)

                if s["type"] == "path":
                    pts = s["points"]
                    if len(pts) > 1:
                        path = QPainterPath(QPointF(pts[0]))
                        for p in pts[1:]:
                            path.lineTo(QPointF(p))
                        painter.drawPath(path)
                elif s["type"] == "rect":
                    r = QRect(s["start"], s["end"]).normalized()
                    if s.get("filled", False):
                        painter.setPen(Qt.PenStyle.NoPen)
                        painter.setBrush(s["color"])
                        painter.drawRect(r)
                    else:
                        painter.drawRect(r)
                elif s["type"] == "circle":
                    r = QRect(s["start"], s["end"]).normalized()
                    if s.get("filled", False):
                        painter.setPen(Qt.PenStyle.NoPen)
                        painter.setBrush(s["color"])
                        painter.drawEllipse(r)
                    else:
                        painter.drawEllipse(r)
                elif s["type"] == "line":
                    painter.drawLine(s["start"], s["end"])
                elif s["type"] == "arrow":
                    self._draw_arrow(painter, s["start"], s["end"], s["color"], s["width"])

            # 3. Draw current live shape being dragged
            if self.is_drawing and self.start_point and self.current_point:
                color = QColor(self.current_color)
                if self.current_tool == "highlighter":
                    color.setAlpha(95)
                    width = 24
                elif self.current_tool == "brush":
                    width = max(10, self.pen_width * 3)
                elif self.current_tool == "eraser":
                    color = QColor(255, 255, 255) if self.board_mode == "whiteboard" else QColor(15, 23, 42)
                    width = 32
                else:
                    if self.board_mode == "whiteboard" and color == QColor("#FFFFFF"):
                        color = QColor("#0F172A")
                    width = self.pen_width

                pen = QPen(color, width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
                painter.setPen(pen)
                painter.setBrush(Qt.BrushStyle.NoBrush)

                if self.current_tool in ("pen", "brush", "highlighter", "eraser") and len(self.current_path) > 1:
                    path = QPainterPath(QPointF(self.current_path[0]))
                    for p in self.current_path[1:]:
                        path.lineTo(QPointF(p))
                    painter.drawPath(path)
                elif self.current_tool == "rect":
                    painter.drawRect(QRect(self.start_point, self.current_point).normalized())
                elif self.current_tool == "fill_rect":
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.setBrush(color)
                    painter.drawRect(QRect(self.start_point, self.current_point).normalized())
                elif self.current_tool == "circle":
                    painter.drawEllipse(QRect(self.start_point, self.current_point).normalized())
                elif self.current_tool == "fill_circle":
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.setBrush(color)
                    painter.drawEllipse(QRect(self.start_point, self.current_point).normalized())
                elif self.current_tool == "line":
                    painter.drawLine(self.start_point, self.current_point)
                elif self.current_tool == "arrow":
                    self._draw_arrow(painter, self.start_point, self.current_point, color, width + 1)
        except Exception:
            pass

    def _draw_arrow(self, painter: QPainter, start: QPoint, end: QPoint, color: QColor, width: int):
        painter.drawLine(start, end)
        dx = end.x() - start.x()
        dy = end.y() - start.y()
        angle = math.atan2(dy, dx)
        arrow_len = 16
        arrow_angle = math.pi / 6
        p_left = QPoint(
            int(end.x() - arrow_len * math.cos(angle - arrow_angle)),
            int(end.y() - arrow_len * math.sin(angle - arrow_angle)),
        )
        p_right = QPoint(
            int(end.x() - arrow_len * math.cos(angle + arrow_angle)),
            int(end.y() - arrow_len * math.sin(angle + arrow_angle)),
        )
        painter.drawLine(end, p_left)
        painter.drawLine(end, p_right)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            if self.text_input.isVisible():
                self.text_input.clear()
                self.text_input.setVisible(False)
            else:
                self.close_board()
        elif event.key() == Qt.Key.Key_S and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.save_board_image()
        elif event.key() == Qt.Key.Key_Z and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.undo()
        elif event.key() == Qt.Key.Key_C and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.clear_all()
        elif not self.text_input.isVisible() and event.text() and event.text().isprintable():
            # If user starts typing letters directly anywhere on the board, open the text box at mouse_pos!
            self._set_tool("text")
            self._open_text_input_at(self.mouse_pos)
            self.text_input.setText(event.text())
