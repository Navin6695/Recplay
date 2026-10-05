"""
Unit tests for Webcam Background Blur and Face Only Cutout modes in Clipr Studio 2.0.
"""

import unittest
import numpy as np
import cv2

from core.face_processor import FaceCamProcessor
from core.screen_recorder import ScreenRecorder
from ui.floating_facecam import FloatingFacecamWidget
from PyQt6.QtWidgets import QApplication
import sys

app = QApplication.instance()
if not app:
    app = QApplication(sys.argv)


class TestFaceCamModes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.processor = FaceCamProcessor()

    def test_face_processor_init(self):
        self.assertIsNotNone(self.processor)

    def test_segment_person(self):
        frame = np.full((240, 320, 3), 120, dtype=np.uint8)
        cv2.circle(frame, (160, 120), 50, (180, 210, 235), -1)
        mask = self.processor.segment_person(frame)
        self.assertIsNotNone(mask)
        self.assertEqual(mask.shape, (240, 320))
        self.assertGreaterEqual(np.min(mask), 0.0)
        self.assertLessEqual(np.max(mask), 1.0)

    def test_detect_face_on_frame(self):
        # Create a test frame with a synthetic face
        frame = np.full((320, 320, 3), 100, dtype=np.uint8)
        cv2.circle(frame, (160, 160), 60, (180, 210, 235), -1)
        face = self.processor.detect_face(frame)
        self.assertIsNotNone(face)
        self.assertEqual(len(face), 4)
        fx, fy, fw, fh = face
        self.assertGreater(fw, 0)
        self.assertGreater(fh, 0)

    def test_apply_background_blur(self):
        frame = np.full((240, 320, 3), 120, dtype=np.uint8)
        cv2.circle(frame, (160, 120), 50, (180, 210, 235), -1)
        blurred_composite = self.processor.apply_background_blur(frame)
        self.assertIsNotNone(blurred_composite)
        self.assertEqual(blurred_composite.shape, frame.shape)
        self.assertEqual(blurred_composite.dtype, np.uint8)

    def test_apply_face_cutout(self):
        frame = np.full((240, 320, 3), 120, dtype=np.uint8)
        cv2.circle(frame, (160, 120), 50, (180, 210, 235), -1)
        cutout, alpha = self.processor.apply_face_cutout(frame, target_size=180)
        self.assertIsNotNone(cutout)
        self.assertIsNotNone(alpha)
        self.assertEqual(cutout.shape, alpha.shape)
        self.assertGreaterEqual(np.min(alpha), 0.0)
        self.assertLessEqual(np.max(alpha), 1.0)
        self.assertEqual(cutout.dtype, np.uint8)

    def test_screen_recorder_webcam_mode_init(self):
        rec_blur = ScreenRecorder(output_file="dummy.mp4", webcam_mode="blur")
        self.assertEqual(rec_blur.webcam_mode, "blur")

        rec_cutout = ScreenRecorder(output_file="dummy.mp4", webcam_mode="face_only")
        self.assertEqual(rec_cutout.webcam_mode, "face_only")

    def test_screen_recorder_overlay_cutout(self):
        rec = ScreenRecorder(output_file="dummy.mp4", webcam_mode="face_only")
        screen = np.full((720, 1280, 3), 30, dtype=np.uint8)
        cam = np.full((480, 640, 3), 150, dtype=np.uint8)
        out = rec._overlay_webcam(screen.copy(), cam, 1280, 720)
        self.assertEqual(out.shape, screen.shape)

    def test_screen_recorder_overlay_blur(self):
        rec = ScreenRecorder(output_file="dummy.mp4", webcam_mode="blur", webcam_shape="square")
        screen = np.full((720, 1280, 3), 30, dtype=np.uint8)
        cam = np.full((480, 640, 3), 150, dtype=np.uint8)
        out = rec._overlay_webcam(screen.copy(), cam, 1280, 720)
        self.assertEqual(out.shape, screen.shape)

    def test_floating_facecam_modes(self):
        widget = FloatingFacecamWidget(size=180, mode="face_only")
        self.assertEqual(widget.mode, "face_only")

        cam = np.full((480, 640, 3), 150, dtype=np.uint8)
        widget.update_frame(cam)
        self.assertIsNotNone(widget.current_pixmap)

        widget.set_mode("blur")
        self.assertEqual(widget.mode, "blur")
        widget.update_frame(cam)
        self.assertIsNotNone(widget.current_pixmap)


if __name__ == "__main__":
    unittest.main()
