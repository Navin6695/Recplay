import sys
import unittest
import numpy as np
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from ui.screen_annotator import AnnotatorOverlay
from ui.main_window import MainWindow
from core.audio_recorder import AudioRecorder
from core.license_verifier import LicenseVerifier

class TestNewFeatures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def test_screen_annotator_text_no_placeholder(self):
        annotator = AnnotatorOverlay()
        # Verify text placeholder is empty
        self.assertEqual(annotator.text_input.placeholderText(), "")
        # Verify single Color button exists instead of line of swatch buttons
        self.assertTrue(hasattr(annotator, "btn_color"))
        self.assertIn("Color", annotator.btn_color.text())
        annotator.close_board()

    def test_main_window_area_mode_dropdown(self):
        win = MainWindow()
        # Verify combo_screen_mode has 3 items and NO redundant "Area Mode" inside
        items = [win.combo_screen_mode.itemText(i) for i in range(win.combo_screen_mode.count())]
        self.assertEqual(len(items), 3)
        self.assertIn("Full Screen", items[0])
        self.assertIn("Select Area", items[1])
        self.assertIn("Shorts / Reels", items[2])
        for it in items:
            self.assertNotEqual(it, "📐 Area Mode")

        # Verify Audio buttons
        self.assertIn("Outside Audio", win.btn_mode_in.text())
        self.assertIn("Inside Audio", win.btn_mode_out.text())
        self.assertNotIn("(+Mic ON)", win.btn_mode_out.text())
        self.assertIn("Both", win.btn_mode_both.text())

        # Verify auto-minimize behavior on stop
        self.assertTrue(hasattr(win, "_stop_recording"))
        win.close()

    def test_audio_mode_stream_isolation(self):
        # 1. Output only mode
        rec_out = AudioRecorder(sample_rate=48000, channels=2, audio_mode="output_only")
        rec_out.start()
        # In output_only, mic stream must NOT be opened
        self.assertIsNone(rec_out.sd_stream)
        audio_out = rec_out.stop()
        self.assertIsInstance(audio_out, np.ndarray)

        # 2. Input only mode
        rec_in = AudioRecorder(sample_rate=48000, channels=2, audio_mode="input_only")
        rec_in.start()
        # In input_only, loop stream must NOT be opened
        self.assertIsNone(rec_in.loop_stream)
        audio_in = rec_in.stop()
        self.assertIsInstance(audio_in, np.ndarray)

    def test_microsoft_store_license_detection(self):
        verifier = LicenseVerifier()
        # Default environment: checks cleanly without crash
        store_res = verifier.check_microsoft_store_license()
        self.assertIsInstance(store_res, dict)
        self.assertIn("valid", store_res)

        # Active Store entitlement check
        store_lic = verifier.activate_microsoft_store_license()
        self.assertTrue(store_lic["valid"])
        self.assertEqual(store_lic["tier"], "PRO")
        self.assertEqual(store_lic["source"], "Microsoft Store")

        active = verifier.get_active_license()
        self.assertTrue(active["valid"])
        self.assertEqual(active["source"], "Microsoft Store")

        # Clean up
        verifier.remove_license()

    def test_area_marking_border_attributes(self):
        from ui.main_window import AreaMarkingBorder
        border = AreaMarkingBorder()
        self.assertTrue(border.testAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents))
        self.assertTrue(border.testAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating))
        # Test boundary update
        border.update_boundary(100, 150, 800, 600)
        self.assertTrue(border.isVisible())
        self.assertFalse(border.mask().isEmpty())
        border.hide()
        border.close()

    def test_license_dialog_button_grid_layout(self):
        from ui.license_dialog import LicenseDialog
        verifier = LicenseVerifier()
        dlg = LicenseDialog(verifier)
        self.assertGreaterEqual(dlg.width(), 540)
        self.assertGreaterEqual(dlg.height(), 500)
        self.assertTrue(any(w in dlg.activate_btn.text() for w in ["Activate", "Update", "Renew"]))
        self.assertIn("Deactivate", dlg.deactivate_btn.text())
        self.assertTrue(len(dlg.hwid_display.text()) > 5)
        dlg.close()

    def test_screen_recorder_compact_file_size_settings(self):
        from core.screen_recorder import ScreenRecorder
        rec = ScreenRecorder(output_file="dummy.mp4")
        self.assertEqual(rec.crf, 24)


if __name__ == "__main__":
    unittest.main()
