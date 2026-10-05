import sys
import os
import unittest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPixmap, QColor, QPainter
from PyQt6.QtCore import QRect, QPoint

from ui.screenshot_editor import ScreenshotCanvas


class TestScreenshotEditor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def setUp(self):
        # Create a test 800x600 pixmap
        self.pixmap = QPixmap(800, 600)
        self.pixmap.fill(QColor(255, 255, 255))
        painter = QPainter(self.pixmap)
        painter.fillRect(50, 50, 200, 100, QColor(220, 38, 38))
        painter.end()

        self.canvas = ScreenshotCanvas(self.pixmap)

    def test_initial_size(self):
        self.assertEqual(self.canvas.current_pixmap.width(), 800)
        self.assertEqual(self.canvas.current_pixmap.height(), 600)

    def test_crop_tool(self):
        # Set crop rect and apply
        self.canvas.crop_rect = QRect(50, 50, 300, 200)
        self.canvas.apply_crop()
        self.assertEqual(self.canvas.current_pixmap.width(), 300)
        self.assertEqual(self.canvas.current_pixmap.height(), 200)

        # Test Undo
        self.canvas.undo()
        self.assertEqual(self.canvas.current_pixmap.width(), 800)
        self.assertEqual(self.canvas.current_pixmap.height(), 600)

    def test_blur_redact(self):
        # Apply blur on a region
        rect = QRect(50, 50, 100, 100)
        self.canvas._apply_blur_rect(rect)
        self.assertEqual(self.canvas.current_pixmap.width(), 800)

    def test_save_screenshot(self):
        test_file = "test_shot_out.png"
        if os.path.exists(test_file):
            os.remove(test_file)

        self.canvas.current_pixmap.save(test_file)
        self.assertTrue(os.path.exists(test_file))
        self.assertGreater(os.path.getsize(test_file), 500)
        os.remove(test_file)


if __name__ == "__main__":
    unittest.main()
