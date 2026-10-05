"""
Live Webcam Test & Preview Dialog
Allows teachers and creators to check lighting, camera alignment, and facecam position
before starting their online class or tutorial recording.
"""

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import QTimer, Qt
import cv2


class WebcamPreviewDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Webcam Live Preview & Test")
        self.setFixedSize(440, 480)
        self.setStyleSheet("""
            QDialog {
                background-color: #0F172A;
                color: #F8FAFC;
            }
            QLabel {
                color: #94A3B8;
                font-size: 13px;
            }
            QPushButton {
                background-color: #2563EB;
                color: white;
                font-weight: bold;
                border-radius: 8px;
                padding: 10px 20px;
                border: none;
            }
            QPushButton:hover {
                background-color: #1D4ED8;
            }
        """)

        self.cap = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_frame)

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        header = QLabel("Camera Live Preview")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #60A5FA;")
        layout.addWidget(header)

        self.video_label = QLabel("Initializing camera...")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setFixedSize(400, 320)
        self.video_label.setStyleSheet("background-color: #1E293B; border-radius: 12px; border: 2px solid #334155;")
        layout.addWidget(self.video_label)

        sub = QLabel("Check your lighting, framing, and background before recording.")
        sub.setStyleSheet("font-size: 11px; color: #64748B;")
        layout.addWidget(sub)

        btn_row = QHBoxLayout()
        close_btn = QPushButton("Done")
        close_btn.clicked.connect(self.accept)
        btn_row.addStretch()
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

    def showEvent(self, event):
        super().showEvent(event)
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not self.cap.isOpened():
            self.cap = cv2.VideoCapture(0)
        self.timer.start(33)  # ~30 fps

    def hideEvent(self, event):
        super().hideEvent(event)
        self.timer.stop()
        if self.cap:
            self.cap.release()
            self.cap = None

    def _update_frame(self):
        if not self.cap or not self.cap.isOpened():
            self.video_label.setText("Camera not found or in use by another app.")
            return

        ret, frame = self.cap.read()
        if ret and frame is not None:
            # Resize to preview box
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            bytes_per_line = ch * w
            qimg = QImage(rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            pix = QPixmap.fromImage(qimg).scaled(
                self.video_label.width(),
                self.video_label.height(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.video_label.setPixmap(pix)
