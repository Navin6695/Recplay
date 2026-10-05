import unittest
import os
import sys
import time
import cv2
from core.screen_recorder import ScreenRecorder


class TestRecordingPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PyQt6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def setUp(self):
        self.output_file = "test_pipeline_run.mp4"
        if os.path.exists(self.output_file):
            os.remove(self.output_file)

    def tearDown(self):
        if os.path.exists(self.output_file):
            try:
                os.remove(self.output_file)
            except Exception:
                pass

    def test_record_and_encode(self):
        rec = ScreenRecorder(
            output_file=self.output_file,
            fps=30,
            crf=23,
            enable_webcam=True,
            enable_mic=True,
        )
        rec.start()
        time.sleep(2.0)
        rec.stop()

        self.assertTrue(os.path.exists(self.output_file), "Output MP4 file was not created")
        file_size = os.path.getsize(self.output_file)
        self.assertGreater(file_size, 1024, "Output MP4 is too small or empty")

        # Verify video stream with OpenCV
        cap = cv2.VideoCapture(self.output_file)
        self.assertTrue(cap.isOpened(), "Could not open created MP4 file with OpenCV")
        ret, frame = cap.read()
        if not ret or frame is None:
            w = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            h = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            self.assertGreater(w, 0)
            self.assertGreater(h, 0)
        else:
            self.assertGreater(frame.shape[1], 0)
            self.assertGreater(frame.shape[0], 0)
        cap.release()


if __name__ == "__main__":
    unittest.main()
