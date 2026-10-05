import unittest
import os
import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QUrl

# Ensure D:\Clipr 2.0 is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from ui.media_player import StudioMediaPlayer, MusicVisualizerWidget, VIDEO_EXTS, AUDIO_EXTS
from ui.main_window import MainWindow

app = QApplication.instance()
if not app:
    app = QApplication(sys.argv)


class TestCliprMediaPlayer(unittest.TestCase):
    def setUp(self):
        self.player = StudioMediaPlayer()

    def tearDown(self):
        if self.player:
            self.player.player.stop()
            self.player.close()

    def test_initialization(self):
        self.assertIsNotNone(self.player.player)
        self.assertIsNotNone(self.player.audio_output)
        self.assertIsNotNone(self.player.video_widget)
        self.assertIsNotNone(self.player.music_widget)
        self.assertEqual(len(self.player.playlist), 0)
        self.assertFalse(self.player.is_looping)

    def test_format_extensions(self):
        self.assertIn(".mp4", VIDEO_EXTS)
        self.assertIn(".mkv", VIDEO_EXTS)
        self.assertIn(".webm", VIDEO_EXTS)
        self.assertIn(".mp3", AUDIO_EXTS)
        self.assertIn(".wav", AUDIO_EXTS)
        self.assertIn(".flac", AUDIO_EXTS)

    def test_volume_and_mute(self):
        self.player.slider_vol.setValue(70)
        self.assertAlmostEqual(self.player.audio_output.volume(), 0.70, delta=0.03)
        
        # Toggle mute
        self.player.toggle_mute()
        self.assertEqual(self.player.audio_output.volume(), 0.0)
        self.assertEqual(self.player.slider_vol.value(), 0)

        # Unmute
        self.player.toggle_mute()
        self.assertAlmostEqual(self.player.audio_output.volume(), 0.70, delta=0.03)

    def test_playback_speed_change(self):
        self.player._on_speed_changed("1.5x")
        self.assertAlmostEqual(self.player.player.playbackRate(), 1.5, places=2)

        self.player._on_speed_changed("0.5x")
        self.assertAlmostEqual(self.player.player.playbackRate(), 0.5, places=2)

    def test_loop_toggle(self):
        self.assertFalse(self.player.is_looping)
        self.player.toggle_loop()
        self.assertTrue(self.player.is_looping)
        self.assertIn("ON", self.player.btn_loop.text())
        self.player.toggle_loop()
        self.assertFalse(self.player.is_looping)
        self.assertIn("OFF", self.player.btn_loop.text())

    def test_playlist_operations(self):
        fake_video = os.path.join(str(BASE_DIR), "sample_video.mp4")
        fake_audio = os.path.join(str(BASE_DIR), "sample_music.mp3")

        # Create dummy files for testing
        with open(fake_video, "w") as f:
            f.write("test video")
        with open(fake_audio, "w") as f:
            f.write("test audio")

        try:
            # Play video -> should set is_video_mode True
            self.player.play_file(fake_video)
            self.assertTrue(self.player.is_video_mode)
            self.assertEqual(self.player.display_stack.currentIndex(), 0)
            self.assertEqual(len(self.player.playlist), 1)

            # Play audio -> should set is_video_mode False
            self.player.play_file(fake_audio)
            self.assertFalse(self.player.is_video_mode)
            self.assertEqual(self.player.display_stack.currentIndex(), 1)
            self.assertEqual(len(self.player.playlist), 2)

            # Next / Prev
            self.assertEqual(self.player.current_index, 1)
            self.player.play_next()
            self.assertEqual(self.player.current_index, 0)
            self.player.play_previous()
            self.assertEqual(self.player.current_index, 1)

            # Clear playlist
            self.player.clear_playlist()
            self.assertEqual(len(self.player.playlist), 0)
            self.assertEqual(self.player.playlist_view.count(), 0)
        finally:
            try:
                self.player.player.stop()
                from PyQt6.QtCore import QUrl
                self.player.player.setSource(QUrl())
            except Exception:
                pass
            for f in (fake_video, fake_audio):
                try:
                    if os.path.exists(f):
                        os.remove(f)
                except Exception:
                    pass

    def test_mainwindow_integration(self):
        win = MainWindow()
        try:
            self.assertTrue(hasattr(win, "_open_media_player"))
            self.assertTrue(hasattr(win, "_open_video_player"))
            self.assertTrue(hasattr(win, "_open_music_player"))
            self.assertTrue(hasattr(win, "btn_player"))

            # Open media player from main window
            win._open_media_player()
            self.assertIsNotNone(win.media_player)
            self.assertTrue(win.media_player.isVisible())

            # Open video player
            win._open_video_player()
            self.assertEqual(win.media_player.display_stack.currentIndex(), 0)

            # Open music player
            win._open_music_player()
            self.assertEqual(win.media_player.display_stack.currentIndex(), 1)
        finally:
            win.close()
            if hasattr(win, "media_player") and win.media_player:
                win.media_player.close()


if __name__ == "__main__":
    unittest.main()
