import unittest
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QPoint, QPointF, QRect, QEvent
from PyQt6.QtGui import QMouseEvent

app = QApplication.instance() or QApplication(sys.argv)

from ui.main_window import MainWindow, LiveRegionFrame
from ui.screen_annotator import AnnotatorOverlay


class TestSelectAreaAndFontSize(unittest.TestCase):
    def setUp(self):
        self.main_win = MainWindow()
        self.frame = self.main_win.live_region_frame
        self.annotator = self.main_win.annotator

    def tearDown(self):
        self.frame.hide()
        self.annotator.close_board()
        self.main_win.close()

    def test_live_region_frame_clean_text(self):
        self.frame.open_centered()
        dim_text = self.frame.lbl_dims.text()
        self.assertNotIn("CLIPR AREA MODE", dim_text)
        self.assertNotIn("Area Mode", dim_text)
        self.assertIn("SELECT AREA", dim_text)
        self.assertTrue(self.frame.btn_redraw.isVisible())
        self.assertEqual(self.frame.btn_redraw.text(), "🖱️ Drag New")

    def test_live_region_frame_locked_text(self):
        self.frame.open_centered()
        self.frame.confirm_current_area()
        dim_text = self.frame.lbl_dims.text()
        self.assertNotIn("CLIPR AREA MODE", dim_text)
        self.assertNotIn("Area Mode", dim_text)
        self.assertIn("LOCKED", dim_text)

    def test_live_region_frame_event_filter_drag(self):
        self.frame.open_centered()
        start_pos = self.frame.pos()
        p1 = QPointF(50.0, 10.0)
        gp1 = QPointF(float(start_pos.x() + 50), float(start_pos.y() + 10))
        press_ev = QMouseEvent(QEvent.Type.MouseButtonPress, p1, gp1, Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
        self.frame.eventFilter(self.frame.top_bar, press_ev)

        p2 = QPointF(110.0, 45.0)
        gp2 = QPointF(float(start_pos.x() + 110), float(start_pos.y() + 45))
        move_ev = QMouseEvent(QEvent.Type.MouseMove, p2, gp2, Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
        self.frame.eventFilter(self.frame.top_bar, move_ev)

        new_pos = self.frame.pos()
        self.assertEqual(new_pos.x(), start_pos.x() + 60)
        self.assertEqual(new_pos.y(), start_pos.y() + 35)

        rel_ev = QMouseEvent(QEvent.Type.MouseButtonRelease, p2, gp2, Qt.MouseButton.LeftButton, Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier)
        self.frame.eventFilter(self.frame.top_bar, rel_ev)
        self.assertIsNone(self.frame._drag_offset)

    def test_set_from_dragged_rect(self):
        rect = QRect(100, 100, 600, 400)
        self.frame.set_from_dragged_rect(rect)
        self.assertFalse(self.frame.is_locked_mode)
        # User requirement: After selection, do not show any toolbar on screen
        self.assertFalse(self.frame.isVisible())
        self.assertFalse(self.frame.btn_redraw.isHidden())
        self.assertFalse(self.frame.btn_lock.isHidden())
        rx, ry, rw, rh = self.frame.get_physical_crop_region()
        self.assertGreaterEqual(rw, 590)
        self.assertGreaterEqual(rh, 390)

    def test_screen_mode_dropdown_clean(self):
        combo = self.main_win.combo_screen_mode
        self.assertEqual(combo.itemText(0), "🖥️ Full Screen")
        self.assertEqual(combo.itemText(1), "🎯 Select Area")
        self.assertNotIn("Area Mode", [combo.itemText(i) for i in range(combo.count())])

    def test_drawboard_font_size(self):
        self.assertTrue(hasattr(self.annotator, "btn_font_size"))
        self.assertIn("24px", self.annotator.btn_font_size.text())

        self.annotator._set_font_size(32)
        self.assertEqual(self.annotator.text_font_size, 32)
        self.assertIn("32px", self.annotator.btn_font_size.text())

        self.annotator._set_font_size(18)
        self.assertEqual(self.annotator.text_font_size, 18)
        self.assertIn("18px", self.annotator.btn_font_size.text())

        # Test pen size does not overwrite font size
        self.annotator._cycle_pen_size()
        self.assertEqual(self.annotator.text_font_size, 18)

    def test_area_mode_records_exact_selected_region(self):
        # 1. User selects an area
        dragged_rect = QRect(200, 150, 500, 350)
        self.main_win._on_freehand_area_dragged(dragged_rect)

        # Verify crop region is stored
        self.assertIsNotNone(self.main_win.custom_crop_region)
        rx, ry, rw, rh = self.main_win.custom_crop_region
        self.assertGreaterEqual(rw, 490)
        self.assertGreaterEqual(rh, 340)
        self.assertEqual(self.main_win.combo_screen_mode.currentIndex(), 1)
        self.assertIn(f"{rw}×{rh}", self.main_win.combo_screen_mode.currentText())

        # 2. Check marking border is visible on screen
        self.assertTrue(self.main_win.area_marking_border.isVisible())

        # 3. Verify start recording assigns exact crop_region to ScreenRecorder
        self.main_win.chk_mic.setChecked(False)
        self.main_win._start_recording()
        self.main_win._execute_start_recording()

        self.assertTrue(self.main_win.is_recording)
        self.assertIsNotNone(self.main_win.recorder)
        self.assertEqual(self.main_win.recorder.crop_region, (rx, ry, rw, rh))

        # 4. Stop recorder
        if self.main_win.recorder:
            self.main_win.recorder.is_recording = False
            if hasattr(self.main_win.recorder, "_gui_grab_timer") and self.main_win.recorder._gui_grab_timer:
                self.main_win.recorder._gui_grab_timer.stop()
        self.main_win.is_recording = False
        self.main_win._close_all_highlight_areas()

        # Verify custom_crop_region and mode are preserved for subsequent recordings
        self.assertEqual(self.main_win.combo_screen_mode.currentIndex(), 1)
        self.assertEqual(self.main_win.custom_crop_region, (rx, ry, rw, rh))

    def test_area_mode_no_toolbar_and_no_minimizing(self):
        """User requirement: After area selection, do not show any toolbar on screen and do not minimize app."""
        self.main_win.show()
        dragged_rect = QRect(150, 120, 640, 480)
        self.main_win._on_freehand_area_dragged(dragged_rect)

        # 1. LiveRegionFrame toolbar MUST NOT be visible on screen
        self.assertFalse(self.main_win.live_region_frame.isVisible())

        # 2. Main window must remain visible and NOT minimized
        self.assertFalse(self.main_win.isMinimized())
        self.assertTrue(self.main_win.isVisible())

        # 3. Area marking line must be visible
        self.assertTrue(self.main_win.area_marking_border.isVisible())

    def test_camera_option_enabled_on_app_open(self):
        """User requirement: When open the app camera option needs on if i want i will on."""
        # Camera checkbox must be enabled (clickable) on app open
        self.assertTrue(self.main_win.chk_webcam.isEnabled())
        self.assertIn("Webcam", self.main_win.chk_webcam.text())

        # Turning camera on should work without trial blocking dialog
        self.main_win.chk_webcam.setChecked(True)
        self.assertTrue(self.main_win.chk_webcam.isChecked())
        self.assertIn("(ON)", self.main_win.chk_webcam.text())

        # Turning camera off
        self.main_win.chk_webcam.setChecked(False)
        self.assertFalse(self.main_win.chk_webcam.isChecked())

    def test_drawboard_paint_tools_and_palette(self):
        """User requirement: In drawboard add features like paint tool."""
        # 1. Verify paint tool buttons exist
        self.assertTrue(hasattr(self.annotator, "btn_brush"))
        self.assertTrue(hasattr(self.annotator, "btn_circle"))
        self.assertTrue(hasattr(self.annotator, "btn_fill_circle"))
        self.assertTrue(hasattr(self.annotator, "btn_fill_rect"))

        # 2. Verify quick paint palette swatches exist
        self.assertTrue(hasattr(self.annotator, "swatch_buttons"))
        self.assertGreaterEqual(len(self.annotator.swatch_buttons), 8)

        # 3. Test quick color selection
        self.annotator._set_quick_color("#00F0FF")
        self.assertEqual(self.annotator.current_color.name().upper(), "#00F0FF")

        # 4. Test tool switching to brush
        self.annotator._set_tool("brush")
        self.assertEqual(self.annotator.current_tool, "brush")

        # 5. Test tool switching to circle
        self.annotator._set_tool("circle")
        self.assertEqual(self.annotator.current_tool, "circle")

        # 6. Test tool switching to fill_rect
        self.annotator._set_tool("fill_rect")
        self.assertEqual(self.annotator.current_tool, "fill_rect")

        # 7. Test tool switching to fill_circle
        self.annotator._set_tool("fill_circle")
        self.assertEqual(self.annotator.current_tool, "fill_circle")

    def test_area_marking_border_hidden_after_recording_stops(self):
        """User requirement: Select area is showing after stop the recording also please stop that."""
        # 1. Select an area and verify border is visible
        dragged_rect = QRect(200, 150, 500, 350)
        self.main_win._on_freehand_area_dragged(dragged_rect)
        self.assertTrue(self.main_win.area_marking_border.isVisible())

        # 2. Simulate recorder finished
        self.main_win._close_all_highlight_areas()
        self.main_win._on_recorder_finished("")

        # 3. Verify area marking border is completely hidden on screen!
        self.assertFalse(self.main_win.area_marking_border.isVisible())

    def test_clicking_drawboard_automatically_goes_to_whiteboard(self):
        """User requirement: When clicking the drawboard it needs go to white board automatically set that."""
        self.main_win.verifier.is_licensed = lambda: True
        # 1. Verify default board mode on annotator
        self.assertEqual(self.annotator.board_mode, "whiteboard")

        # 2. Simulate clicking drawboard button (_toggle_annotator)
        self.annotator.close_board()
        self.main_win._toggle_annotator()

        # 3. Verify it is visible and in whiteboard mode automatically
        self.assertTrue(self.annotator.isVisible())
        self.assertEqual(self.annotator.board_mode, "whiteboard")
        self.assertIn("Live Screen", self.annotator.btn_whiteboard.text())
        self.assertEqual(self.annotator.btn_whiteboard.property("active"), "true")

        # 4. Toggle whiteboard button to switch to live screen and back
        self.annotator._toggle_whiteboard_mode()
        self.assertEqual(self.annotator.board_mode, "screen")
        self.assertIn("White Board", self.annotator.btn_whiteboard.text())

        # 5. Close and reopen via _toggle_annotator -> must automatically go to whiteboard again!
        self.annotator.close_board()
        self.main_win._toggle_annotator()
        self.assertEqual(self.annotator.board_mode, "whiteboard")
        self.annotator.close_board()


if __name__ == "__main__":
    unittest.main()

