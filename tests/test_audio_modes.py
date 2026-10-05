import unittest
import time
import numpy as np
from core.audio_recorder import AudioRecorder


class TestAudioModes(unittest.TestCase):
    def test_audio_input_only_mode(self):
        rec = AudioRecorder(sample_rate=48000, channels=2, audio_mode="input_only")
        rec.start()
        time.sleep(0.3)
        audio = rec.stop()
        self.assertIsInstance(audio, np.ndarray)
        self.assertEqual(audio.dtype, np.float32)
        if len(audio) > 0:
            self.assertEqual(audio.shape[1], 2)

    def test_audio_input_and_output_mode(self):
        rec = AudioRecorder(sample_rate=48000, channels=2, audio_mode="input_and_output")
        rec.start()
        time.sleep(0.3)
        audio = rec.stop()
        self.assertIsInstance(audio, np.ndarray)
        self.assertEqual(audio.dtype, np.float32)
        if len(audio) > 0:
            self.assertEqual(audio.shape[1], 2)

    def test_outside_audio_mode(self):
        rec = AudioRecorder(sample_rate=48000, channels=2, audio_mode="outside_audio")
        rec.start()
        time.sleep(0.3)
        audio = rec.stop()
        self.assertIsInstance(audio, np.ndarray)
        self.assertEqual(audio.dtype, np.float32)
        if len(audio) > 0:
            self.assertEqual(audio.shape[1], 2)

    def test_inside_audio_mode(self):
        rec = AudioRecorder(sample_rate=48000, channels=2, audio_mode="inside_audio")
        rec.start()
        time.sleep(0.3)
        audio = rec.stop()
        self.assertIsInstance(audio, np.ndarray)
        self.assertEqual(audio.dtype, np.float32)
        if len(audio) > 0:
            self.assertEqual(audio.shape[1], 2)

    def test_both_audio_mode(self):
        rec = AudioRecorder(sample_rate=48000, channels=2, audio_mode="both")
        rec.start()
        time.sleep(0.3)
        audio = rec.stop()
        self.assertIsInstance(audio, np.ndarray)
        self.assertEqual(audio.dtype, np.float32)
        if len(audio) > 0:
            self.assertEqual(audio.shape[1], 2)

    def test_volume_meter_reporting(self):
        rec = AudioRecorder(sample_rate=48000, channels=2, audio_mode="input_only")
        rec.start()
        time.sleep(0.1)
        vol = rec.get_volume()
        self.assertGreaterEqual(vol, 0.0)
        self.assertLessEqual(vol, 1.0)
        rec.stop()


if __name__ == "__main__":
    unittest.main()

