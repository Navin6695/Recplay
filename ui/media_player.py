"""
Recplay Studio 2.0 - Integrated Studio Media Player (Video & Music Player)
Engineered for Windows 11 with PyQt6.QtMultimedia + QVideoWidget.

Features:
- Dual-Mode Player: Video Player (MP4, MKV, AVI, MOV, WebM) + Music Player (MP3, WAV, AAC, M4A, FLAC, OGG)
- Dynamic Audio Visualizer: Vibrant multi-color animated spectrum bars, rotating Arc Reactor, glowing core emblem
- Video Controls: Scrubber slider, time elapsed/remaining, volume, playback speed (0.5x - 2.0x), full screen
- Frame Snip Tool: 📸 1-click crystal-clear video frame capture saved to disk
- Interactive Playlist: Create playlists, save/load .m3u playlists, add folders, filter search, drag-and-drop
- Seamless Screen Recorder Integration: Instant 1-click playback of finished recordings
"""

import os
import sys
import math
import json
import random
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSlider,
    QStackedWidget, QListWidget, QListWidgetItem, QFileDialog, QMessageBox,
    QFrame, QComboBox, QMenu, QApplication, QSplitter, QInputDialog, QLineEdit
)
from PyQt6.QtCore import Qt, QUrl, QTimer, QPoint, QPointF, QRect, QSize, pyqtSignal, QEvent
from PyQt6.QtGui import (
    QPainter, QPen, QColor, QFont, QIcon, QPixmap, QImage,
    QLinearGradient, QRadialGradient, QBrush, QKeySequence, QShortcut, QCursor
)
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget


VIDEO_EXTS = {".mp4", ".mkv", ".avi", ".mov", ".webm", ".wmv", ".flv", ".ts", ".m4v"}
AUDIO_EXTS = {".mp3", ".wav", ".aac", ".m4a", ".flac", ".ogg", ".wma", ".opus"}
ALL_MEDIA_EXTS = VIDEO_EXTS | AUDIO_EXTS


class VideoDisplayWidget(QVideoWidget):
    """
    QVideoWidget subclass that emits a double_clicked signal to toggle full screen on double-click.
    """
    double_clicked = pyqtSignal()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit()
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)


class MusicVisualizerWidget(QWidget):
    """
    Iconic Recplay Cyber Visualizer matching the main application HUD background:
    - Deep Cyber Navy Studio Base (QColor(4, 9, 20))
    - Subtle Full-Widget Holographic Blueprint Grid
    - Animated rotating Arc Reactor & concentric radar rings with dashed and dotted rings
    - Inner glowing core emblem with "RECPLAY AUDIO"
    - Flanking lateral energy wave bars with multi-hue spectrum animation
    - Dynamic 48-band frequency spectrum equalizer with vibrant shifting aurora color shades
    - High-contrast cyber typography for track title and metadata
    - Fully responsive scaling for windowed and full screen display modes
    """
    double_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(280)
        self.is_playing = False
        self.track_title = "No Track Loaded"
        self.track_info = "Load audio or create a playlist"
        self.bar_count = 48
        self.bar_heights = [12.0] * self.bar_count
        self.target_heights = [12.0] * self.bar_count
        self.reactor_angle = 0.0
        self.wave_phase = 0.0
        self.color_hue = 0.0

        self.anim_timer = QTimer(self)
        self.anim_timer.setInterval(40)  # 25 FPS animation
        self.anim_timer.timeout.connect(self._animate_visualizer)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit()
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)

    def set_track(self, title: str, info: str = ""):
        self.track_title = title
        self.track_info = info
        self.update()

    def set_playing(self, playing: bool):
        self.is_playing = playing
        if not self.anim_timer.isActive():
            self.anim_timer.start()
        self.update()

    def _animate_visualizer(self):
        if self.is_playing:
            self.reactor_angle = (self.reactor_angle + 2.4) % 360.0
            self.wave_phase += 0.22
            self.color_hue = (self.color_hue + 1.4) % 360.0
            for i in range(self.bar_count):
                w1 = math.sin(i * 0.26 + self.wave_phase * 1.6) ** 2
                w2 = math.cos(i * 0.42 - self.wave_phase * 2.0) ** 2
                w3 = math.sin(i * 0.14 + self.reactor_angle * 0.04) ** 2
                bass = 1.35 if i < 16 else (1.15 if i < 32 else 0.95)
                amp = (w1 * 0.5 + w2 * 0.32 + w3 * 0.18) * 115.0 * bass
                jitter = random.uniform(0.78, 1.22)
                self.target_heights[i] = max(8.0, min(140.0, amp * jitter))
        else:
            # Idle gentle drift and smooth bar decay
            self.reactor_angle = (self.reactor_angle + 0.6) % 360.0
            self.wave_phase += 0.05
            self.color_hue = (self.color_hue + 0.2) % 360.0
            for i in range(self.bar_count):
                self.target_heights[i] = 6.0
            if all(h <= 7.0 for h in self.bar_heights) and not self.is_playing:
                self.anim_timer.stop()

        for i in range(self.bar_count):
            self.bar_heights[i] += (self.target_heights[i] - self.bar_heights[i]) * 0.35

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()

        # 1. Deep Cyber Navy Studio Base
        painter.fillRect(self.rect(), QColor(4, 9, 20))

        # 2. Subtle Full-Window Holographic Blueprint Grid
        grid_pen = QPen(QColor(0, 240, 255, 22), 1)
        painter.setPen(grid_pen)
        for gx in range(0, w, 44):
            painter.drawLine(gx, 0, gx, h)
        for gy in range(0, h, 44):
            painter.drawLine(0, gy, w, gy)

        # Responsive scale factor based on window/screen size
        scale = min(2.2, max(0.85, min(w / 880.0, h / 540.0)))

        # Center coordinates for Arc Reactor HUD
        cx = w / 2.0
        cy = max(110.0 * scale, (h / 2.0) - 25.0 * scale)

        r_outer = 135.0 * scale
        r_mid = 115.0 * scale
        r_dash = 92.0 * scale
        r_dot = 68.0 * scale
        r_dashdot = 46.0 * scale
        r_core = 32.0 * scale

        # Ambient breathing radial glow with dynamic color shade
        if self.is_playing:
            ambient_rad = QRadialGradient(cx, cy, r_outer * 1.55)
            c_core = QColor.fromHsv(int(self.color_hue) % 360, 230, 255, 48)
            c_mid = QColor.fromHsv(int((self.color_hue + 70) % 360), 220, 255, 24)
            c_edge = QColor.fromHsv(int((self.color_hue + 140) % 360), 200, 255, 0)
            ambient_rad.setColorAt(0.0, c_core)
            ambient_rad.setColorAt(0.5, c_mid)
            ambient_rad.setColorAt(1.0, c_edge)
            painter.setBrush(ambient_rad)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPointF(cx, cy), r_outer * 1.55, r_outer * 1.55)

        # 3. Rotating Center Arc Reactor & Radar Rings
        if self.is_playing:
            col_outer = QColor.fromHsv(int((self.color_hue + 20) % 360), 220, 255, 190)
            col_mid = QColor.fromHsv(int((self.color_hue + 80) % 360), 210, 255, 160)
            col_dash = QColor.fromHsv(int((self.color_hue + 160) % 360), 230, 255, 230)
            col_dot = QColor.fromHsv(int((self.color_hue + 240) % 360), 220, 255, 210)
            glow_fill = QColor.fromHsv(int(self.color_hue) % 360, 200, 255, 32)
        else:
            col_outer = QColor(0, 240, 255, 80)
            col_mid = QColor(56, 189, 248, 70)
            col_dash = QColor(0, 240, 255, 100)
            col_dot = QColor(56, 189, 248, 80)
            glow_fill = QColor(0, 240, 255, 12)

        # Outer radar glow circle
        painter.setBrush(glow_fill)
        painter.setPen(QPen(col_outer, 2.2 * scale))
        painter.drawEllipse(QPointF(cx, cy), r_outer, r_outer)

        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(col_mid, 1.4 * scale))
        painter.drawEllipse(QPointF(cx, cy), r_mid, r_mid)

        # Rotating concentric detail rings
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(self.reactor_angle)
        painter.setPen(QPen(col_dash, 3.5 * scale, Qt.PenStyle.DashLine))
        painter.drawEllipse(QPointF(0.0, 0.0), r_dash, r_dash)

        painter.rotate(-2.1 * self.reactor_angle)
        painter.setPen(QPen(col_dot, 2.5 * scale, Qt.PenStyle.DotLine))
        painter.drawEllipse(QPointF(0.0, 0.0), r_dot, r_dot)

        painter.rotate(3.0 * self.reactor_angle)
        painter.setPen(QPen(col_outer, 2.0 * scale, Qt.PenStyle.DashDotLine))
        painter.drawEllipse(QPointF(0.0, 0.0), r_dashdot, r_dashdot)
        painter.restore()

        # 4. Inner Glowing Core Emblem ("RECPLAY AUDIO")
        core_radial = QRadialGradient(cx, cy, r_core)
        if self.is_playing:
            core_radial.setColorAt(0.0, QColor.fromHsv(int((self.color_hue + 300) % 360), 200, 255, 200))
            core_radial.setColorAt(0.7, QColor.fromHsv(int(self.color_hue % 360), 220, 255, 80))
            core_radial.setColorAt(1.0, QColor.fromHsv(int((self.color_hue + 60) % 360), 240, 255, 20))
        else:
            core_radial.setColorAt(0.0, QColor(0, 240, 255, 60))
            core_radial.setColorAt(1.0, QColor(0, 240, 255, 10))

        painter.setBrush(core_radial)
        painter.setPen(QPen(col_outer, 2 * scale))
        painter.drawEllipse(QPointF(cx, cy), r_core, r_core)

        painter.setFont(QFont("Consolas", int(10 * scale), QFont.Weight.Bold))
        painter.setPen(QColor(255, 255, 255, 245) if self.is_playing else QColor(148, 163, 184, 180))
        painter.drawText(
            QRect(int(cx - 100 * scale), int(cy - 9 * scale), int(200 * scale), int(18 * scale)),
            Qt.AlignmentFlag.AlignCenter,
            "RECPLAY AUDIO"
        )

        # 5. Symmetric Lateral Energy Wave Bars with Vibrant Multi-Color Hues
        for side in (-1, 1):
            for i in range(12):
                val = math.sin(self.wave_phase + i * 0.45) * 0.5 + 0.5
                bh = int(10 + val * (58 if self.is_playing else 22) * scale)
                bx = int(cx + side * ((r_outer + 18 * scale) + i * (13 * scale)))
                by = int(cy - bh // 2)
                if self.is_playing:
                    bar_hue = int(self.color_hue + i * 16) % 360
                    col_bar = QColor.fromHsv(bar_hue, 220, 255, 180)
                else:
                    col_bar = QColor(0, 240, 255, 30)
                painter.fillRect(QRect(bx, by, max(3, int(5 * scale)), bh), col_bar)

        # 6. HUD Header Telemetry Badges
        painter.setFont(QFont("Consolas", int(9 * scale), QFont.Weight.Bold))
        painter.setPen(QColor(0, 240, 255, 160))
        painter.drawText(QRect(24, 20, 300, 24), Qt.AlignmentFlag.AlignLeft, "⬡ RECPLAY 2.0 STUDIO AUDIO DECK")
        painter.setPen(QColor(56, 189, 248, 160))
        painter.drawText(QRect(int(w - 324), 20, 300, 24), Qt.AlignmentFlag.AlignRight, "HI-FI 48 kHz STEREO ⬡")

        # 7. Track title & metadata banner
        painter.setPen(QColor(248, 250, 252))
        font_title = QFont("Segoe UI", int(14 * scale), QFont.Weight.Bold)
        painter.setFont(font_title)
        title_rect = QRect(20, int(cy + r_outer + 16 * scale), int(w - 40), int(26 * scale))
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignCenter, self.track_title)

        painter.setPen(QColor(56, 189, 248))
        font_info = QFont("Consolas", int(10 * scale))
        painter.setFont(font_info)
        info_rect = QRect(20, int(cy + r_outer + 44 * scale), int(w - 40), int(22 * scale))
        status_prefix = "● PLAYING" if self.is_playing else "○ PAUSED"
        painter.drawText(info_rect, Qt.AlignmentFlag.AlignCenter, f"{status_prefix}  |  {self.track_info}")

        # 8. Frequency spectrum equalizer bars at bottom with dynamic shifting aurora colors
        baseline_y = h - 14
        bar_w = max(4, (int(w) - 70) // self.bar_count - 3)
        total_w = self.bar_count * (bar_w + 3)
        start_x = max(16, (int(w) - total_w) // 2)

        for i in range(self.bar_count):
            bx = start_x + i * (bar_w + 3)
            bh = int(self.bar_heights[i] * scale)
            by = baseline_y - bh

            bar_grad = QLinearGradient(bx, by, bx, baseline_y)
            if self.is_playing:
                top_hue = (int(self.color_hue) + i * 6) % 360
                mid_hue = (top_hue + 45) % 360
                bot_hue = (top_hue + 110) % 360
                bar_grad.setColorAt(0.0, QColor.fromHsv(top_hue, 240, 255, 255))
                bar_grad.setColorAt(0.4, QColor.fromHsv(mid_hue, 220, 255, 220))
                bar_grad.setColorAt(1.0, QColor.fromHsv(bot_hue, 230, 210, 160))
            else:
                bar_grad.setColorAt(0.0, QColor(0, 240, 255, 110))
                bar_grad.setColorAt(0.5, QColor(16, 185, 129, 80))
                bar_grad.setColorAt(1.0, QColor(59, 130, 246, 50))

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(bar_grad)
            painter.drawRoundedRect(QRect(bx, by, bar_w, bh), 2, 2)

            # Bright glowing neon peak cap atop active equalizer bars
            if self.is_playing and bh > 14:
                cap_hue = (int(self.color_hue) + i * 6) % 360
                cap_col = QColor.fromHsv(cap_hue, 100, 255, 255)
                painter.fillRect(QRect(bx, by - 3, bar_w, 2), cap_col)


class ClickableSlider(QSlider):
    """QSlider that immediately seeks to the clicked mouse position."""
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            val = self.minimum() + ((self.maximum() - self.minimum()) * event.position().x()) / max(1, self.width())
            self.setValue(int(round(val)))
            self.sliderMoved.emit(int(round(val)))
            event.accept()
        super().mousePressEvent(event)


class StudioMediaPlayer(QWidget):
    """
    All-in-One Cyberpunk Studio Media Player for Recplay 2.0.
    Directly plays Video & Music recordings or external media files.
    """
    snapshot_captured = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🎬 Recplay Studio 2.0 - Media Player (Video & Music)")
        self.resize(1040, 650)
        self.setMinimumSize(640, 440)
        self.setAcceptDrops(True)

        self.current_file: str | None = None
        self.playlist: list[str] = []
        self.playlist_name: str = "Default Playlist"
        self.current_index: int = -1
        self.is_looping: bool = False
        self.is_video_mode: bool = True
        self.last_volume: float = 0.85
        self._user_seeking: bool = False

        # QtMultimedia Player & Audio Output
        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(self.last_volume)

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #0B1120;
                color: #F8FAFC;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLabel {
                color: #FFFFFF;
                font-size: 12px;
                font-weight: 500;
            }
            QPushButton {
                background-color: #1E293B;
                color: #F8FAFC;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #0284C7;
                border-color: #00F0FF;
                color: #FFFFFF;
            }
            QPushButton[active="true"] {
                background-color: #0284C7;
                border: 2px solid #00F0FF;
                color: #FFFFFF;
            }
            QSlider::groove:horizontal {
                height: 6px;
                background: #1E293B;
                border-radius: 3px;
            }
            QSlider::sub-page:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00F0FF, stop:1 #3B82F6);
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #00F0FF;
                border: 2px solid #FFFFFF;
                width: 14px;
                margin-top: -4px;
                margin-bottom: -4px;
                border-radius: 7px;
            }
            QSlider::handle:horizontal:hover {
                background: #FFFFFF;
                border-color: #00F0FF;
            }
            QListWidget {
                background-color: #0F172A;
                border: 1px solid #1E293B;
                border-radius: 8px;
                padding: 4px;
                color: #F8FAFC;
                font-size: 12px;
            }
            QListWidget::item {
                padding: 8px 10px;
                border-radius: 6px;
            }
            QListWidget::item:hover {
                background-color: #1E293B;
                color: #00F0FF;
            }
            QListWidget::item:selected {
                background-color: #0284C7;
                color: #FFFFFF;
                font-weight: bold;
            }
            QComboBox {
                background-color: #1E293B;
                color: #F8FAFC;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 4px 8px;
                font-weight: bold;
                font-size: 12px;
            }
            QComboBox QAbstractItemView {
                background-color: #0F172A;
                color: #F8FAFC;
                selection-background-color: #0284C7;
                border: 1px solid #334155;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(8)

        # Top Header Bar
        self.header_panel = QFrame()
        header_bar = QHBoxLayout(self.header_panel)
        header_bar.setContentsMargins(0, 0, 0, 0)
        self.lbl_app_title = QLabel("🎬 RECPLAY 2.0 STUDIO MEDIA PLAYER")
        self.lbl_app_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #00F0FF; letter-spacing: 1px;")
        header_bar.addWidget(self.lbl_app_title)

        self.lbl_media_badge = QLabel("READY")
        self.lbl_media_badge.setStyleSheet(
            "background-color: #065F46; color: #34D399; padding: 3px 10px; border-radius: 10px; font-weight: bold; font-size: 11px;"
        )
        header_bar.addWidget(self.lbl_media_badge)
        header_bar.addStretch()

        self.btn_open_file = QPushButton("📂 Open Media")
        self.btn_open_file.setToolTip("Open any video or audio file")
        self.btn_open_file.clicked.connect(self._browse_and_open_file)
        header_bar.addWidget(self.btn_open_file)

        self.btn_toggle_playlist = QPushButton("📑 Playlist")
        self.btn_toggle_playlist.setToolTip("Show / Hide Playlist Drawer")
        self.btn_toggle_playlist.clicked.connect(self._toggle_playlist_drawer)
        header_bar.addWidget(self.btn_toggle_playlist)
        main_layout.addWidget(self.header_panel)

        # Center Area: Splitter containing Media Display + Collapsible Playlist
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setStyleSheet("QSplitter::handle { background-color: #1E293B; width: 3px; }")

        # Media Display Stack (Index 0: VideoWidget, Index 1: MusicVisualizerWidget)
        self.display_stack = QStackedWidget()
        self.display_stack.setStyleSheet("background-color: #030712; border-radius: 10px; border: 1px solid #1E293B;")

        # Video Widget (with Double-Click to Fullscreen!)
        self.video_widget = VideoDisplayWidget()
        self.video_widget.setStyleSheet("background-color: #000000; border-radius: 10px;")
        self.video_widget.double_clicked.connect(self.toggle_fullscreen)
        self.player.setVideoOutput(self.video_widget)
        self.display_stack.addWidget(self.video_widget)

        # Music Visualizer Widget (with Double-Click to Fullscreen!)
        self.music_widget = MusicVisualizerWidget()
        self.music_widget.double_clicked.connect(self.toggle_fullscreen)
        self.display_stack.addWidget(self.music_widget)
        self.splitter.addWidget(self.display_stack)

        # Playlist Drawer Panel
        self.playlist_panel = QFrame()
        self.playlist_panel.setMinimumWidth(280)
        self.playlist_panel.setMaximumWidth(400)
        self.playlist_panel.setStyleSheet("QFrame { background-color: #0A0F1D; border-radius: 8px; border: 1px solid #1E293B; }")
        pl_layout = QVBoxLayout(self.playlist_panel)
        pl_layout.setContentsMargins(8, 8, 8, 8)
        pl_layout.setSpacing(6)

        # 1. Header Title with Track Count & Quick Action Buttons
        pl_header = QHBoxLayout()
        self.lbl_pl_title = QLabel("📋 Playlist (0 tracks)")
        self.lbl_pl_title.setStyleSheet("font-weight: bold; font-size: 13px; color: #00F0FF; background: transparent; border: none;")
        pl_header.addWidget(self.lbl_pl_title)
        pl_header.addStretch()

        self.btn_create_pl = QPushButton("✨ New")
        self.btn_create_pl.setToolTip("Create a New Named Playlist")
        self.btn_create_pl.setStyleSheet(
            "QPushButton { background-color: #0284C7; color: #FFFFFF; font-weight: bold; padding: 4px 8px; border-radius: 6px; font-size: 11px; border: 1px solid #00F0FF; }"
            "QPushButton:hover { background-color: #0369A1; }"
        )
        self.btn_create_pl.clicked.connect(self.create_new_playlist)
        pl_header.addWidget(self.btn_create_pl)

        self.btn_load_pl = QPushButton("📂 Open")
        self.btn_load_pl.setToolTip("Open Existing Playlist (.m3u, .json) or Folder")
        self.btn_load_pl.setStyleSheet(
            "QPushButton { background-color: #1E293B; color: #38BDF8; font-weight: bold; padding: 4px 8px; border-radius: 6px; font-size: 11px; border: 1px solid #334155; }"
            "QPushButton:hover { background-color: #0284C7; color: #FFFFFF; }"
        )
        self.btn_load_pl.clicked.connect(lambda: self.load_playlist())
        pl_header.addWidget(self.btn_load_pl)

        self.btn_save_pl = QPushButton("💾 Save")
        self.btn_save_pl.setToolTip("Save Current Playlist to Disk (.m3u)")
        self.btn_save_pl.setStyleSheet(
            "QPushButton { background-color: #1E293B; color: #34D399; font-weight: bold; padding: 4px 8px; border-radius: 6px; font-size: 11px; border: 1px solid #334155; }"
            "QPushButton:hover { background-color: #059669; color: #FFFFFF; }"
        )
        self.btn_save_pl.clicked.connect(self.save_playlist)
        pl_header.addWidget(self.btn_save_pl)
        pl_layout.addLayout(pl_header)

        # 2. Add / Remove Secondary Action Row
        act_row = QHBoxLayout()
        act_row.setSpacing(4)

        btn_add = QPushButton("➕ Tracks")
        btn_add.setToolTip("Add Audio / Video Files to Playlist")
        btn_add.setStyleSheet(
            "QPushButton { background-color: #1E293B; color: #F8FAFC; font-size: 11px; font-weight: bold; padding: 4px 6px; border-radius: 5px; border: 1px solid #334155; }"
            "QPushButton:hover { background-color: #0284C7; }"
        )
        btn_add.clicked.connect(self.add_media_files)
        act_row.addWidget(btn_add)

        btn_folder = QPushButton("📁 Folder")
        btn_folder.setToolTip("Scan & Add All Media from a Music Folder")
        btn_folder.setStyleSheet(
            "QPushButton { background-color: #1E293B; color: #F8FAFC; font-size: 11px; font-weight: bold; padding: 4px 6px; border-radius: 5px; border: 1px solid #334155; }"
            "QPushButton:hover { background-color: #0284C7; }"
        )
        btn_folder.clicked.connect(self.add_media_folder)
        act_row.addWidget(btn_folder)

        btn_del = QPushButton("❌ Remove")
        btn_del.setToolTip("Remove Selected Track from Queue")
        btn_del.setStyleSheet(
            "QPushButton { background-color: #1E293B; color: #F87171; font-size: 11px; font-weight: bold; padding: 4px 6px; border-radius: 5px; border: 1px solid #334155; }"
            "QPushButton:hover { background-color: #991B1B; color: #FFFFFF; }"
        )
        btn_del.clicked.connect(self.remove_selected_track)
        act_row.addWidget(btn_del)

        btn_clear = QPushButton("🗑️")
        btn_clear.setToolTip("Clear Entire Playlist")
        btn_clear.setFixedWidth(28)
        btn_clear.setStyleSheet(
            "QPushButton { background-color: #1E293B; color: #94A3B8; font-size: 11px; font-weight: bold; padding: 4px; border-radius: 5px; border: 1px solid #334155; }"
            "QPushButton:hover { background-color: #EF4444; color: #FFFFFF; }"
        )
        btn_clear.clicked.connect(self.clear_playlist)
        act_row.addWidget(btn_clear)
        pl_layout.addLayout(act_row)

        # 3. Quick Filter Box
        self.txt_pl_search = QLineEdit()
        self.txt_pl_search.setPlaceholderText("🔍 Filter tracks in playlist...")
        self.txt_pl_search.setStyleSheet(
            "QLineEdit { background-color: #0F172A; color: #F8FAFC; border: 1px solid #1E293B; border-radius: 6px; padding: 4px 8px; font-size: 11px; }"
            "QLineEdit:focus { border: 1px solid #00F0FF; }"
        )
        self.txt_pl_search.textChanged.connect(self._filter_playlist_items)
        pl_layout.addWidget(self.txt_pl_search)

        # 4. Playlist Items ListWidget
        self.playlist_view = QListWidget()
        self.playlist_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.playlist_view.customContextMenuRequested.connect(self._show_playlist_context_menu)
        self.playlist_view.itemDoubleClicked.connect(self._on_playlist_item_double_clicked)
        pl_layout.addWidget(self.playlist_view)

        self.splitter.addWidget(self.playlist_panel)
        self.splitter.setStretchFactor(0, 4)
        self.splitter.setStretchFactor(1, 1)
        main_layout.addWidget(self.splitter, 1)

        # Bottom Controls Panel (Seek Bar + Playback Toolbar)
        self.bottom_controls_panel = QFrame()
        b_layout = QVBoxLayout(self.bottom_controls_panel)
        b_layout.setContentsMargins(0, 4, 0, 0)
        b_layout.setSpacing(6)

        # Progress / Seek Bar
        seek_box = QHBoxLayout()
        seek_box.setSpacing(8)
        self.lbl_time_cur = QLabel("00:00")
        self.lbl_time_cur.setFixedWidth(52)
        self.lbl_time_cur.setStyleSheet("color: #00F0FF; font-family: Consolas, monospace; font-weight: bold;")
        seek_box.addWidget(self.lbl_time_cur)

        self.slider_seek = ClickableSlider(Qt.Orientation.Horizontal)
        self.slider_seek.setRange(0, 1000)
        self.slider_seek.setValue(0)
        self.slider_seek.sliderPressed.connect(self._on_seek_pressed)
        self.slider_seek.sliderMoved.connect(self._on_seek_moved)
        self.slider_seek.sliderReleased.connect(self._on_seek_released)
        seek_box.addWidget(self.slider_seek)

        self.lbl_time_total = QLabel("00:00")
        self.lbl_time_total.setFixedWidth(52)
        self.lbl_time_total.setStyleSheet("color: #38BDF8; font-family: Consolas, monospace; font-weight: bold;")
        seek_box.addWidget(self.lbl_time_total)
        b_layout.addLayout(seek_box)

        # Control Bar: Play/Pause, Navigation, Volume, Speed, Tools
        ctrl_bar = QHBoxLayout()
        ctrl_bar.setSpacing(8)

        # Prev / Next
        self.btn_prev = QPushButton("⏮️")
        self.btn_prev.setToolTip("Previous Track / Video")
        self.btn_prev.setFixedWidth(40)
        self.btn_prev.clicked.connect(self.play_previous)
        ctrl_bar.addWidget(self.btn_prev)

        self.btn_back5 = QPushButton("⏪ 5s")
        self.btn_back5.setToolTip("Jump Backward 5 Seconds")
        self.btn_back5.clicked.connect(lambda: self.seek_relative(-5000))
        ctrl_bar.addWidget(self.btn_back5)

        # Play / Pause Main Button
        self.btn_play = QPushButton("▶️ Play")
        self.btn_play.setFixedWidth(100)
        self.btn_play.setStyleSheet(
            "QPushButton { background-color: #0284C7; color: #FFFFFF; font-size: 13px; font-weight: bold; border: 1px solid #00F0FF; padding: 7px 16px; }"
            "QPushButton:hover { background-color: #0369A1; }"
        )
        self.btn_play.clicked.connect(self.toggle_play_pause)
        ctrl_bar.addWidget(self.btn_play)

        self.btn_fwd5 = QPushButton("5s ⏩")
        self.btn_fwd5.setToolTip("Jump Forward 5 Seconds")
        self.btn_fwd5.clicked.connect(lambda: self.seek_relative(5000))
        ctrl_bar.addWidget(self.btn_fwd5)

        self.btn_next = QPushButton("⏭️")
        self.btn_next.setToolTip("Next Track / Video")
        self.btn_next.setFixedWidth(40)
        self.btn_next.clicked.connect(self.play_next)
        ctrl_bar.addWidget(self.btn_next)

        self.btn_stop = QPushButton("⏹️")
        self.btn_stop.setToolTip("Stop Playback")
        self.btn_stop.setFixedWidth(38)
        self.btn_stop.clicked.connect(self.stop)
        ctrl_bar.addWidget(self.btn_stop)

        ctrl_bar.addSpacing(10)

        # Volume Controls
        self.btn_mute = QPushButton("🔊")
        self.btn_mute.setToolTip("Mute / Unmute Audio")
        self.btn_mute.setFixedWidth(38)
        self.btn_mute.clicked.connect(self.toggle_mute)
        ctrl_bar.addWidget(self.btn_mute)

        self.slider_vol = QSlider(Qt.Orientation.Horizontal)
        self.slider_vol.setRange(0, 100)
        self.slider_vol.setValue(85)
        self.slider_vol.setFixedWidth(90)
        self.slider_vol.setToolTip("Volume: 85%")
        self.slider_vol.valueChanged.connect(self._on_volume_changed)
        ctrl_bar.addWidget(self.slider_vol)

        ctrl_bar.addSpacing(10)

        # Speed Dropdown
        lbl_spd = QLabel("Speed:")
        ctrl_bar.addWidget(lbl_spd)
        self.combo_speed = QComboBox()
        self.combo_speed.setFixedWidth(80)
        self.combo_speed.addItems(["0.5x", "0.75x", "1.0x", "1.25x", "1.5x", "2.0x"])
        self.combo_speed.setCurrentText("1.0x")
        self.combo_speed.currentTextChanged.connect(self._on_speed_changed)
        ctrl_bar.addWidget(self.combo_speed)

        ctrl_bar.addStretch()

        # Tools: Loop, Frame Snip, Cyber Visualizer, Fullscreen
        tool_btn_style = (
            "QPushButton { padding: 6px 10px; font-size: 11px; font-weight: bold; } "
            "QPushButton:hover { background-color: #0284C7; border-color: #00F0FF; }"
        )
        self.btn_loop = QPushButton("🔁 Loop: OFF")
        self.btn_loop.setToolTip("Toggle Single Track / Video Repeat")
        self.btn_loop.setStyleSheet(tool_btn_style)
        self.btn_loop.clicked.connect(self.toggle_loop)
        ctrl_bar.addWidget(self.btn_loop)

        self.btn_snip = QPushButton("📸 Snip Frame")
        self.btn_snip.setToolTip("Capture full resolution PNG screenshot from video")
        self.btn_snip.setStyleSheet(tool_btn_style)
        self.btn_snip.clicked.connect(self.capture_video_snapshot)
        ctrl_bar.addWidget(self.btn_snip)

        self.btn_toggle_theme = QPushButton("🎛️ Visualizer")
        self.btn_toggle_theme.setToolTip("Toggle between Video and Recplay Cyber Background Theme")
        self.btn_toggle_theme.setStyleSheet(tool_btn_style)
        self.btn_toggle_theme.clicked.connect(self.toggle_visualizer_mode)
        ctrl_bar.addWidget(self.btn_toggle_theme)

        self.btn_fullscreen = QPushButton("⛶ Fullscreen")
        self.btn_fullscreen.setToolTip("Toggle Fullscreen Video / Music View (Double-click or ESC to exit)")
        self.btn_fullscreen.setStyleSheet(tool_btn_style)
        self.btn_fullscreen.clicked.connect(self.toggle_fullscreen)
        ctrl_bar.addWidget(self.btn_fullscreen)

        b_layout.addLayout(ctrl_bar)
        main_layout.addWidget(self.bottom_controls_panel)

        # Floating Fullscreen Exit Button
        self.btn_fs_exit = QPushButton("✖ Exit Fullscreen (Esc)", self)
        self.btn_fs_exit.setStyleSheet("""
            QPushButton {
                background-color: rgba(15, 23, 42, 220);
                color: #00F0FF;
                border: 1px solid #00F0FF;
                border-radius: 16px;
                padding: 7px 18px;
                font-weight: bold;
                font-size: 12px;
                letter-spacing: 0.5px;
            }
            QPushButton:hover {
                background-color: #DC2626;
                color: #FFFFFF;
                border-color: #EF4444;
            }
        """)
        self.btn_fs_exit.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_fs_exit.clicked.connect(self.toggle_fullscreen)
        self.btn_fs_exit.hide()

        # 5-Second Inactivity Disappearance Timer for Fullscreen Mode
        self._fs_autohide_timer = QTimer(self)
        self._fs_autohide_timer.setSingleShot(True)
        self._fs_autohide_timer.setInterval(5000)
        self._fs_autohide_timer.timeout.connect(self._hide_fs_controls)

        self.setMouseTracking(True)
        self.display_stack.setMouseTracking(True)
        self.video_widget.setMouseTracking(True)
        self.music_widget.setMouseTracking(True)

        self.video_widget.installEventFilter(self)
        self.music_widget.installEventFilter(self)
        self.display_stack.installEventFilter(self)

    def _connect_signals(self):
        self.player.positionChanged.connect(self._on_position_changed)
        self.player.durationChanged.connect(self._on_duration_changed)
        self.player.playbackStateChanged.connect(self._on_playback_state_changed)
        self.player.mediaStatusChanged.connect(self._on_media_status_changed)
        self.player.errorOccurred.connect(self._on_player_error)

    def _on_player_error(self, error: QMediaPlayer.Error, error_string: str = ""):
        print(f"[!] MediaPlayer Error: {error} - {error_string}")
        err_msg = error_string or f"Playback error ({error})"
        self.lbl_media_badge.setText("⚠️ PLAYBACK ERROR")
        self.lbl_media_badge.setStyleSheet(
            "background-color: #7F1D1D; color: #FCA5A5; padding: 3px 10px; border-radius: 10px; font-weight: bold; font-size: 11px;"
        )
        self.lbl_app_title.setText(f"⚠️ Error playing media: {err_msg}")

    def _format_time(self, ms: int) -> str:
        total_sec = max(0, ms // 1000)
        hours = total_sec // 3600
        mins = (total_sec % 3600) // 60
        secs = total_sec % 60
        if hours > 0:
            return f"{hours:02d}:{mins:02d}:{secs:02d}"
        return f"{mins:02d}:{secs:02d}"

    def _on_position_changed(self, pos: int):
        if not self._user_seeking:
            dur = self.player.duration()
            if dur > 0:
                self.slider_seek.setValue(int((pos / dur) * 1000))
            self.lbl_time_cur.setText(self._format_time(pos))

    def _on_duration_changed(self, dur: int):
        self.lbl_time_total.setText(self._format_time(dur))

    def _on_seek_pressed(self):
        self._user_seeking = True

    def _on_seek_moved(self, val: int):
        dur = self.player.duration()
        if dur > 0:
            seek_ms = int((val / 1000) * dur)
            self.lbl_time_cur.setText(self._format_time(seek_ms))

    def _on_seek_released(self):
        self._user_seeking = False
        val = self.slider_seek.value()
        dur = self.player.duration()
        if dur > 0:
            seek_ms = int((val / 1000) * dur)
            self.player.setPosition(seek_ms)

    def _on_playback_state_changed(self, state: QMediaPlayer.PlaybackState):
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.btn_play.setText("⏸️ Pause")
            self.lbl_media_badge.setText("▶ PLAYING")
            self.lbl_media_badge.setStyleSheet(
                "background-color: #065F46; color: #34D399; padding: 3px 10px; border-radius: 10px; font-weight: bold; font-size: 11px;"
            )
            self.music_widget.set_playing(True)
        else:
            self.btn_play.setText("▶️ Play")
            self.lbl_media_badge.setText("⏸ PAUSED" if state == QMediaPlayer.PlaybackState.PausedState else "⏹ STOPPED")
            self.lbl_media_badge.setStyleSheet(
                "background-color: #0F172A; color: #FFFFFF; border: 1.5px solid #0284C7; padding: 3px 10px; border-radius: 10px; font-weight: bold; font-size: 11px;"
            )
            self.music_widget.set_playing(False)

    def _on_media_status_changed(self, status: QMediaPlayer.MediaStatus):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            if self.is_looping:
                self.player.setPosition(0)
                self.player.play()
            else:
                self.play_next()

    def _on_volume_changed(self, val: int):
        vol = val / 100.0
        self.audio_output.setVolume(vol)
        self.slider_vol.setToolTip(f"Volume: {val}%")
        if val == 0:
            self.btn_mute.setText("🔇")
        elif val < 50:
            self.btn_mute.setText("🔉")
        else:
            self.btn_mute.setText("🔊")
        if val > 0:
            self.last_volume = vol

    def toggle_mute(self):
        if self.audio_output.volume() > 0:
            self.last_volume = self.audio_output.volume()
            self.audio_output.setVolume(0.0)
            self.slider_vol.setValue(0)
            self.btn_mute.setText("🔇")
        else:
            restore_vol = self.last_volume if self.last_volume > 0.05 else 0.8
            self.audio_output.setVolume(restore_vol)
            self.slider_vol.setValue(int(restore_vol * 100))
            self.btn_mute.setText("🔊")

    def _on_speed_changed(self, text: str):
        try:
            rate = float(text.replace("x", ""))
            self.player.setPlaybackRate(rate)
        except Exception:
            pass

    def toggle_loop(self):
        self.is_looping = not self.is_looping
        if self.is_looping:
            self.btn_loop.setText("🔁 Loop: ON")
            self.btn_loop.setStyleSheet("background-color: #0284C7; color: #FFFFFF; border: 1px solid #00F0FF; font-weight: bold; padding: 6px 10px; font-size: 11px;")
        else:
            self.btn_loop.setText("🔁 Loop: OFF")
            self.btn_loop.setStyleSheet("QPushButton { padding: 6px 10px; font-size: 11px; font-weight: bold; } QPushButton:hover { background-color: #0284C7; border-color: #00F0FF; }")

    def toggle_play_pause(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        else:
            if not self.current_file:
                if self.playlist:
                    self.play_index(0)
                else:
                    self.add_media_files()
            else:
                self.player.play()

    def stop(self):
        self.player.stop()
        self.slider_seek.setValue(0)
        self.lbl_time_cur.setText("00:00")
        self.music_widget.set_playing(False)

    def seek_relative(self, ms: int):
        new_pos = max(0, min(self.player.duration(), self.player.position() + ms))
        self.player.setPosition(new_pos)

    def _update_playlist_badge(self):
        self.lbl_pl_title.setText(f"📋 {self.playlist_name} ({len(self.playlist)} tracks)")

    def _filter_playlist_items(self, query: str):
        q = query.strip().lower()
        for i in range(self.playlist_view.count()):
            item = self.playlist_view.item(i)
            item.setHidden(bool(q and q not in item.text().lower()))

    def _show_playlist_context_menu(self, pos: QPoint):
        item = self.playlist_view.itemAt(pos)
        menu = QMenu(self)
        menu.setStyleSheet(
            "QMenu { background-color: #0F172A; color: #F8FAFC; border: 1px solid #0284C7; padding: 4px; border-radius: 6px; } "
            "QMenu::item:selected { background-color: #0284C7; color: #FFFFFF; }"
        )
        act_play = menu.addAction("▶️ Play Track")
        act_remove = menu.addAction("❌ Remove from Playlist")
        act_open_folder = menu.addAction("📂 Open File Location")
        menu.addSeparator()
        act_clear = menu.addAction("🗑️ Clear Entire Playlist")

        action = menu.exec(self.playlist_view.mapToGlobal(pos))
        if action == act_play and item:
            idx = self.playlist_view.row(item)
            self.play_index(idx)
        elif action == act_remove and item:
            self.remove_selected_track()
        elif action == act_open_folder and item:
            fp = item.toolTip()
            if os.path.exists(fp) and sys.platform == "win32":
                os.system(f'explorer /select,"{fp}"')
        elif action == act_clear:
            self.clear_playlist()

    def create_new_playlist(self):
        """Prompts for a new playlist name and immediately allows adding audio/video tracks."""
        name, ok = QInputDialog.getText(
            self, "Create New Playlist", "Enter Playlist Name:", text=f"Playlist {len(self.playlist) + 1}"
        )
        if ok and name.strip():
            self.playlist_name = name.strip()
            self.clear_playlist()
            self.playlist_name = name.strip()
            self._update_playlist_badge()
            self.add_media_files()

    def load_playlist(self, file_path: str = None):
        """Loads an existing .m3u, .pls, or .json playlist file from disk."""
        if not file_path:
            filter_str = "Playlist Files (*.m3u *.m3u8 *.pls *.json);;All Files (*.*)"
            file_path, _ = QFileDialog.getOpenFileName(self, "Open Playlist File", "", filter_str)
        if not file_path or not os.path.exists(file_path):
            return

        self.clear_playlist()
        p = Path(file_path)
        self.playlist_name = p.stem
        loaded_files = []
        try:
            if p.suffix.lower() == ".json":
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.playlist_name = data.get("name", p.stem)
                    loaded_files = data.get("tracks", [])
            else:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            loaded_files.append(line)
        except Exception as e:
            QMessageBox.warning(self, "Playlist Error", f"Failed to parse playlist file:\n{e}")
            return

        for fp in loaded_files:
            clean_fp = os.path.abspath(os.path.normpath(fp))
            if os.path.exists(clean_fp) and clean_fp not in self.playlist:
                self.playlist.append(clean_fp)
                ext = Path(clean_fp).suffix.lower()
                icon = "🎬 " if ext in VIDEO_EXTS else "🎵 "
                item = QListWidgetItem(f"{len(self.playlist):02d}. {icon}{Path(clean_fp).name}")
                item.setToolTip(clean_fp)
                self.playlist_view.addItem(item)

        self._update_playlist_badge()
        if self.playlist:
            self.play_index(0)

    def save_playlist(self):
        """Exports current playlist to standard .m3u or .json format."""
        if not self.playlist:
            QMessageBox.information(self, "Save Playlist", "The playlist queue is currently empty! Add tracks first.")
            return

        save_dir = Path.home() / "Music" / "Recplay_Playlists"
        save_dir.mkdir(parents=True, exist_ok=True)
        def_path = str(save_dir / f"{self.playlist_name}.m3u")

        file_path, sel_filter = QFileDialog.getSaveFileName(
            self, "Save Playlist As", def_path, "M3U Playlist (*.m3u);;JSON Playlist (*.json)"
        )
        if not file_path:
            return

        try:
            if file_path.endswith(".json"):
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump({"name": self.playlist_name, "tracks": self.playlist, "version": "2.0"}, f, indent=2)
            else:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write("#EXTM3U\n")
                    f.write(f"#PLAYLIST:{self.playlist_name}\n")
                    for t in self.playlist:
                        f.write(f"{t}\n")
            QMessageBox.information(
                self, "Playlist Saved", f"Playlist successfully saved to:\n\n📁 {file_path}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save playlist file:\n{e}")

    def add_media_files(self):
        """Opens multi-file chooser for all supported media files and appends them to queue."""
        filter_str = (
            "All Media (*.mp4 *.mkv *.avi *.mov *.webm *.wmv *.mp3 *.wav *.aac *.m4a *.flac *.ogg);;"
            "Audio Files (*.mp3 *.wav *.aac *.m4a *.flac *.ogg);;"
            "Video Files (*.mp4 *.mkv *.avi *.mov *.webm *.wmv);;"
            "All Files (*.*)"
        )
        files, _ = QFileDialog.getOpenFileNames(self, "Select Media Track(s)", "", filter_str)
        if files:
            first_added = None
            for f in files:
                clean_f = os.path.abspath(os.path.normpath(f))
                if clean_f not in self.playlist:
                    if first_added is None:
                        first_added = clean_f
                    self.playlist.append(clean_f)
                    ext = Path(clean_f).suffix.lower()
                    icon = "🎬 " if ext in VIDEO_EXTS else "🎵 "
                    item = QListWidgetItem(f"{len(self.playlist):02d}. {icon}{Path(clean_f).name}")
                    item.setToolTip(clean_f)
                    self.playlist_view.addItem(item)
            self._update_playlist_badge()
            if self.player.playbackState() != QMediaPlayer.PlaybackState.PlayingState and first_added:
                self.play_file(first_added)

    def add_media_folder(self):
        """Recursively scans a directory and adds all audio and video tracks to playlist."""
        folder = QFileDialog.getExistingDirectory(self, "Select Music / Media Folder", str(Path.home() / "Music" or Path.home()))
        if not folder:
            return
        added_count = 0
        first_added = None
        for root, _, files in os.walk(folder):
            for fn in sorted(files):
                if Path(fn).suffix.lower() in ALL_MEDIA_EXTS:
                    clean_f = os.path.abspath(os.path.normpath(os.path.join(root, fn)))
                    if clean_f not in self.playlist:
                        if first_added is None:
                            first_added = clean_f
                        self.playlist.append(clean_f)
                        ext = Path(clean_f).suffix.lower()
                        icon = "🎬 " if ext in VIDEO_EXTS else "🎵 "
                        item = QListWidgetItem(f"{len(self.playlist):02d}. {icon}{Path(clean_f).name}")
                        item.setToolTip(clean_f)
                        self.playlist_view.addItem(item)
                        added_count += 1
        self._update_playlist_badge()
        if self.player.playbackState() != QMediaPlayer.PlaybackState.PlayingState and first_added:
            self.play_file(first_added)
        if added_count == 0:
            QMessageBox.information(self, "No Media Found", f"No supported media files found in:\n{folder}")

    def remove_selected_track(self):
        """Removes the selected track from playlist."""
        row = self.playlist_view.currentRow()
        if 0 <= row < len(self.playlist):
            removed_file = self.playlist.pop(row)
            self.playlist_view.takeItem(row)
            # Refresh numbers
            for i in range(self.playlist_view.count()):
                t_path = self.playlist[i]
                ext = Path(t_path).suffix.lower()
                icon = "🎬 " if ext in VIDEO_EXTS else "🎵 "
                self.playlist_view.item(i).setText(f"{i+1:02d}. {icon}{Path(t_path).name}")
            self._update_playlist_badge()
            if removed_file == self.current_file:
                if self.playlist:
                    next_idx = min(row, len(self.playlist) - 1)
                    self.play_index(next_idx)
                else:
                    self.stop()
                    self.current_file = None
                    self.current_index = -1

    def play_file(self, file_path: str):
        if not file_path:
            return
        clean_path = os.path.abspath(os.path.normpath(str(file_path)))
        if not os.path.exists(clean_path):
            QMessageBox.warning(self, "Media File Not Found", f"Cannot find media file:\n{clean_path}")
            return

        # Stop previous playback cleanly before changing source
        self.player.stop()

        self.current_file = clean_path
        ext = Path(clean_path).suffix.lower()
        self.is_video_mode = ext in VIDEO_EXTS

        # Add to playlist if not already present
        if clean_path not in self.playlist:
            self.playlist.append(clean_path)
            icon = "🎬 " if self.is_video_mode else "🎵 "
            item = QListWidgetItem(f"{len(self.playlist):02d}. {icon}{Path(clean_path).name}")
            item.setToolTip(clean_path)
            self.playlist_view.addItem(item)
        self.current_index = self.playlist.index(clean_path)
        self.playlist_view.setCurrentRow(self.current_index)
        self._update_playlist_badge()

        # Switch display stack: Index 0 for Video, Index 1 for Music
        if self.is_video_mode:
            self.display_stack.setCurrentIndex(0)
            self.player.setVideoOutput(self.video_widget)
            self.btn_snip.setVisible(True)
            self.btn_toggle_theme.setText("🎛️ Visualizer")
            self.lbl_app_title.setText(f"🎬 VIDEO: {Path(clean_path).name}")
            self.music_widget.set_playing(False)
        else:
            self.display_stack.setCurrentIndex(1)
            self.player.setVideoOutput(None)
            self.btn_snip.setVisible(False)
            self.btn_toggle_theme.setText("🎬 Video")
            self.lbl_app_title.setText(f"🎵 MUSIC: {Path(clean_path).name}")
            try:
                filesize_mb = os.path.getsize(clean_path) / (1024 * 1024)
            except Exception:
                filesize_mb = 0.0
            self.music_widget.set_track(
                Path(clean_path).stem,
                f"Audio Track  •  {ext.upper().lstrip('.')}  •  {filesize_mb:.1f} MB"
            )
            self.music_widget.set_playing(True)

        self.btn_fullscreen.setVisible(True)
        if self.audio_output.volume() < 0.05:
            self.audio_output.setVolume(self.last_volume or 0.85)
        self.player.setSource(QUrl.fromLocalFile(clean_path))
        self.player.play()

    def play_index(self, index: int):
        if 0 <= index < len(self.playlist):
            self.current_index = index
            self.play_file(self.playlist[index])

    def play_next(self):
        if self.playlist:
            next_idx = (self.current_index + 1) % len(self.playlist)
            self.play_index(next_idx)

    def play_previous(self):
        if self.playlist:
            prev_idx = (self.current_index - 1 + len(self.playlist)) % len(self.playlist)
            self.play_index(prev_idx)

    def clear_playlist(self):
        self.player.stop()
        self.playlist.clear()
        self.playlist_view.clear()
        self.current_index = -1
        self.current_file = None
        self.playlist_name = "Default Playlist"
        self._update_playlist_badge()
        self.lbl_app_title.setText("🎬 RECPLAY 2.0 STUDIO MEDIA PLAYER")
        self.lbl_media_badge.setText("READY")
        self.lbl_time_cur.setText("00:00")
        self.lbl_time_total.setText("00:00")
        self.slider_seek.setValue(0)
        self.music_widget.set_track("No Track Loaded", "Load audio or create a playlist")

    def _browse_and_open_file(self):
        self.add_media_files()

    def _on_playlist_item_double_clicked(self, item: QListWidgetItem):
        idx = self.playlist_view.row(item)
        self.play_index(idx)

    def _toggle_playlist_drawer(self):
        self.playlist_panel.setVisible(not self.playlist_panel.isVisible())

    def capture_video_snapshot(self):
        """Grabs the current video display frame and saves it directly to Pictures."""
        if not self.is_video_mode or not self.current_file:
            QMessageBox.information(self, "Snap Frame", "Please play a video file to capture a frame snapshot.")
            return

        import datetime
        snap_dir = Path.home() / "Pictures" / "Recplay_Snapshots"
        snap_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        out_file = str(snap_dir / f"Snapshot_{ts}.png")

        pixmap = self.video_widget.grab()
        if not pixmap.isNull():
            pixmap.save(out_file)
            self.snapshot_captured.emit(out_file)
            QMessageBox.information(
                self,
                "📸 Frame Snip Saved",
                f"Video frame snapshot saved successfully!\n\n📁 {out_file}",
            )

    def toggle_visualizer_mode(self):
        """Toggles between Video Output and Recplay Cyber Background Theme."""
        if self.display_stack.currentIndex() == 0:
            self.display_stack.setCurrentIndex(1)
            self.btn_toggle_theme.setText("🎬 Video")
            self.music_widget.set_playing(self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState)
        else:
            self.display_stack.setCurrentIndex(0)
            self.btn_toggle_theme.setText("🎛️ Visualizer")

    def _hide_fs_controls(self):
        """Hides floating buttons and bottom controls in fullscreen after 5 seconds of inactivity."""
        if not self.isFullScreen():
            return
        # If cursor is directly over bottom controls or exit button, keep showing
        try:
            cur_pos = self.mapFromGlobal(QCursor.pos())
            if hasattr(self, "bottom_controls_panel") and self.bottom_controls_panel.geometry().contains(cur_pos):
                self._fs_autohide_timer.start(3000)
                return
            if hasattr(self, "btn_fs_exit") and self.btn_fs_exit.geometry().contains(cur_pos):
                self._fs_autohide_timer.start(3000)
                return
        except Exception:
            pass

        self.bottom_controls_panel.hide()
        self.btn_fs_exit.hide()
        self.setCursor(Qt.CursorShape.BlankCursor)

    def _show_fs_controls(self):
        """Reveals floating buttons and bottom controls when user touches screen or moves mouse."""
        self.setCursor(Qt.CursorShape.ArrowCursor)
        if self.isFullScreen():
            if hasattr(self, "bottom_controls_panel"):
                self.bottom_controls_panel.show()
                self.bottom_controls_panel.raise_()
            if hasattr(self, "btn_fs_exit"):
                self.btn_fs_exit.show()
                self.btn_fs_exit.raise_()
            self._fs_autohide_timer.start(5000)

    def eventFilter(self, watched, event):
        if event.type() in (
            QEvent.Type.MouseMove,
            QEvent.Type.MouseButtonPress,
            QEvent.Type.MouseButtonRelease,
            QEvent.Type.TouchBegin,
            QEvent.Type.TouchUpdate,
        ):
            if self.isFullScreen():
                self._show_fs_controls()
        return super().eventFilter(watched, event)

    def mouseMoveEvent(self, event):
        if self.isFullScreen():
            self._show_fs_controls()
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        if self.isFullScreen():
            self._show_fs_controls()
        super().mousePressEvent(event)

    def toggle_fullscreen(self):
        """Toggles Fullscreen for Video and Music with immersive full-display expansion."""
        if self.isFullScreen():
            self._fs_autohide_timer.stop()
            self.showNormal()
            self.header_panel.show()
            self.bottom_controls_panel.show()
            if getattr(self, "_playlist_was_visible_before_fs", False):
                self.playlist_panel.show()
            self.btn_fullscreen.setText("⛶ Fullscreen")
            self.btn_fs_exit.hide()
            self.setCursor(Qt.CursorShape.ArrowCursor)
            self.layout().setContentsMargins(12, 12, 12, 12)
            self.display_stack.setStyleSheet("background-color: #030712; border-radius: 10px; border: 1px solid #1E293B;")
        else:
            self._playlist_was_visible_before_fs = self.playlist_panel.isVisible()
            self.header_panel.hide()
            self.playlist_panel.hide()
            self.layout().setContentsMargins(0, 0, 0, 0)
            self.display_stack.setStyleSheet("background-color: #030712; border: none; border-radius: 0px;")
            self.showFullScreen()
            self.btn_fullscreen.setText("✖ Exit Full")
            self.btn_fs_exit.adjustSize()
            self.btn_fs_exit.move(self.width() - self.btn_fs_exit.width() - 24, 20)
            self.btn_fs_exit.show()
            self.btn_fs_exit.raise_()
            self.bottom_controls_panel.show()
            self.setCursor(Qt.CursorShape.ArrowCursor)
            self._fs_autohide_timer.start(5000)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.isFullScreen() and hasattr(self, "btn_fs_exit"):
            self.btn_fs_exit.move(self.width() - self.btn_fs_exit.width() - 24, 20)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Space:
            self.toggle_play_pause()
        elif event.key() in (Qt.Key.Key_F, Qt.Key.Key_F11):
            self.toggle_fullscreen()
        elif event.key() == Qt.Key.Key_Escape and self.isFullScreen():
            self.toggle_fullscreen()
        elif event.key() == Qt.Key.Key_Left:
            self.seek_relative(-5000)
        elif event.key() == Qt.Key.Key_Right:
            self.seek_relative(5000)
        elif event.key() == Qt.Key.Key_Up:
            self.slider_vol.setValue(min(100, self.slider_vol.value() + 5))
        elif event.key() == Qt.Key.Key_Down:
            self.slider_vol.setValue(max(0, self.slider_vol.value() - 5))
        elif event.key() == Qt.Key.Key_M:
            self.toggle_mute()
        super().keyPressEvent(event)

    def closeEvent(self, event):
        """Immediately silences and halts all audio and video playback when window is closed."""
        try:
            if hasattr(self, "audio_output") and self.audio_output is not None:
                self.audio_output.setMuted(True)
                self.audio_output.setVolume(0.0)
            if hasattr(self, "player") and self.player is not None:
                self.player.stop()
                self.player.setSource(QUrl())
            if hasattr(self, "visualizer") and self.visualizer is not None:
                if hasattr(self.visualizer, "anim_timer") and self.visualizer.anim_timer.isActive():
                    self.visualizer.anim_timer.stop()
            self.is_playing = False
        except Exception as e:
            print(f"[!] MediaPlayer close warning: {e}")
        finally:
            super().closeEvent(event)
            event.accept()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        added_files = []
        for u in urls:
            fp = u.toLocalFile()
            if os.path.isfile(fp) and Path(fp).suffix.lower() in ALL_MEDIA_EXTS:
                added_files.append(fp)
            elif os.path.isdir(fp):
                for root, _, files in os.walk(fp):
                    for fn in files:
                        if Path(fn).suffix.lower() in ALL_MEDIA_EXTS:
                            added_files.append(os.path.join(root, fn))

        if added_files:
            first_to_play = os.path.abspath(os.path.normpath(added_files[0]))
            for f in added_files:
                clean_f = os.path.abspath(os.path.normpath(f))
                if clean_f not in self.playlist:
                    self.playlist.append(clean_f)
                    ext = Path(clean_f).suffix.lower()
                    icon = "🎬 " if ext in VIDEO_EXTS else "🎵 "
                    item = QListWidgetItem(f"{icon}{Path(clean_f).name}")
                    item.setToolTip(clean_f)
                    self.playlist_view.addItem(item)
            self.play_file(first_to_play)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    player = StudioMediaPlayer()
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        player.play_file(sys.argv[1])
    player.show()
    sys.exit(app.exec())
