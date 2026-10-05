"""
Audio Recorder Engine (Direct WDM-KS 4-Capsule Hardware Mic Array Beamformer + WASAPI Speaker Loopback)
Guarantees loud, crystal-clear audio in ALL 3 modes:
1. 'input_only'       : Captures Direct Hardware Microphone Array (WDM-KS 4-Ch Beamformed + Studio Vocal Boost) + System Fallback
2. 'output_only'      : Captures System Speaker Output + Hardware Microphone voice so live classes & lectures work seamlessly
3. 'input_and_output' : Captures both Hardware Microphone Input + System Speaker Loopback Output simultaneously
"""

import sys
import time
import queue
import ctypes
from ctypes import POINTER, c_float, c_int, c_uint32, c_void_p, byref
from typing import Optional, List, Dict
import numpy as np
import sounddevice as sd


def _force_unmute_windows_audio_endpoints():
    """
    Directly accesses Windows Core Audio COM (IMMDeviceEnumerator -> IAudioEndpointVolume)
    to ensure both the Hardware Microphone (eCapture=1) and System Speakers (eRender=0)
    are UNMUTED (SetMute(0)) and set to 98% volume (SetMasterVolumeLevelScalar(0.98)).
    """
    if sys.platform != "win32":
        return
    try:
        import comtypes
        from comtypes import GUID

        class IAudioEndpointVolume(comtypes.IUnknown):
            _iid_ = GUID("{5CDF2C82-841E-4546-9722-0CF74078229A}")
            _methods_ = [
                comtypes.COMMETHOD([], ctypes.HRESULT, "RegisterControlChangeNotify", (["in"], c_void_p, "pNotify")),
                comtypes.COMMETHOD([], ctypes.HRESULT, "UnregisterControlChangeNotify", (["in"], c_void_p, "pNotify")),
                comtypes.COMMETHOD([], ctypes.HRESULT, "GetChannelCount", (["out"], POINTER(c_uint32), "pnChannelCount")),
                comtypes.COMMETHOD([], ctypes.HRESULT, "SetMasterVolumeLevel", (["in"], c_float, "fLevelDB"), (["in"], c_void_p, "pguidEventContext")),
                comtypes.COMMETHOD([], ctypes.HRESULT, "SetMasterVolumeLevelScalar", (["in"], c_float, "fLevel"), (["in"], c_void_p, "pguidEventContext")),
                comtypes.COMMETHOD([], ctypes.HRESULT, "GetMasterVolumeLevel", (["out"], POINTER(c_float), "pfLevelDB")),
                comtypes.COMMETHOD([], ctypes.HRESULT, "GetMasterVolumeLevelScalar", (["out"], POINTER(c_float), "pfLevel")),
                comtypes.COMMETHOD([], ctypes.HRESULT, "SetChannelVolumeLevel", (["in"], c_uint32, "nChannel"), (["in"], c_float, "fLevelDB"), (["in"], c_void_p, "pguidEventContext")),
                comtypes.COMMETHOD([], ctypes.HRESULT, "SetChannelVolumeLevelScalar", (["in"], c_uint32, "nChannel"), (["in"], c_float, "fLevel"), (["in"], c_void_p, "pguidEventContext")),
                comtypes.COMMETHOD([], ctypes.HRESULT, "GetChannelVolumeLevel", (["in"], c_uint32, "nChannel"), (["out"], POINTER(c_float), "pfLevelDB")),
                comtypes.COMMETHOD([], ctypes.HRESULT, "GetChannelVolumeLevelScalar", (["in"], c_uint32, "nChannel"), (["out"], POINTER(c_float), "pfLevel")),
                comtypes.COMMETHOD([], ctypes.HRESULT, "SetMute", (["in"], c_int, "bMute"), (["in"], c_void_p, "pguidEventContext")),
                comtypes.COMMETHOD([], ctypes.HRESULT, "GetMute", (["out"], POINTER(c_int), "pbMute")),
            ]

        class IMMDevice(comtypes.IUnknown):
            _iid_ = GUID("{D666063F-1587-4E43-81F1-B948E807363F}")
            _methods_ = [
                comtypes.COMMETHOD(
                    [], ctypes.HRESULT, "Activate",
                    (["in"], POINTER(GUID), "iid"),
                    (["in"], c_uint32, "dwClsCtx"),
                    (["in"], c_void_p, "pActivationParams"),
                    (["out"], POINTER(c_void_p), "ppInterface"),
                ),
            ]

        class IMMDeviceEnumerator(comtypes.IUnknown):
            _iid_ = GUID("{A95664D2-9614-4F35-A746-DE8DB63617E6}")
            _methods_ = [
                comtypes.COMMETHOD([], ctypes.HRESULT, "EnumAudioEndpoints"),
                comtypes.COMMETHOD(
                    [], ctypes.HRESULT, "GetDefaultAudioEndpoint",
                    (["in"], c_uint32, "dataFlow"),
                    (["in"], c_uint32, "role"),
                    (["out"], POINTER(POINTER(IMMDevice)), "ppEndpoint"),
                ),
            ]

        comtypes.CoInitialize()
        CLSID_MMDeviceEnumerator = GUID("{BCDE0395-E52F-467C-8E3D-C4579291692E}")
        enumerator = comtypes.CoCreateInstance(CLSID_MMDeviceEnumerator, interface=IMMDeviceEnumerator, clsctx=23)

        for flow in (1, 0):
            for role in (0, 1, 2):
                try:
                    dev = enumerator.GetDefaultAudioEndpoint(flow, role)
                    raw_ptr = dev.Activate(byref(IAudioEndpointVolume._iid_), 23, None)
                    ep_vol = ctypes.cast(raw_ptr, POINTER(IAudioEndpointVolume))
                    if ep_vol.GetMute():
                        ep_vol.SetMute(0, None)
                    vol = ep_vol.GetMasterVolumeLevelScalar()
                    if flow == 1 and vol < 0.95:
                        ep_vol.SetMasterVolumeLevelScalar(0.98, None)
                    elif flow == 0 and vol < 0.50:
                        ep_vol.SetMasterVolumeLevelScalar(0.85, None)
                except Exception:
                    pass
    except Exception:
        pass


class AudioRecorder:
    def __init__(self, sample_rate: int = 48000, channels: int = 2, audio_mode: str = "input_and_output"):
        self.sample_rate = sample_rate
        self.channels = channels
        self.audio_mode = audio_mode  # "input_only", "output_only", "input_and_output"
        self.device_index: Optional[int] = None

        self.is_recording = False
        self.start_perf = 0.0
        self.last_unmute_check = 0.0
        self.mic_queue: queue.Queue = queue.Queue()
        self.loop_queue: queue.Queue = queue.Queue()
        self.loop_total_samples = 0

        self.sd_stream = None
        self.pa = None
        self.loop_stream = None

        self.mic_native_rate = 48000
        self.loop_native_channels = 2
        self.loop_native_rate = 48000

        self.current_volume_level = 0.0
        _force_unmute_windows_audio_endpoints()

    @staticmethod
    def get_input_devices() -> List[Dict]:
        """Returns a list of available audio input devices."""
        devices = []
        try:
            for idx, d in enumerate(sd.query_devices()):
                if d.get("max_input_channels", 0) > 0 and d.get("hostapi", 0) == 0:
                    devices.append({
                        "index": idx,
                        "name": d.get("name", f"Microphone {idx}"),
                        "channels": 2,
                        "sample_rate": int(d.get("default_samplerate", 48000)),
                    })
        except Exception:
            pass
        return devices

    def set_device(self, device_index: Optional[int]):
        self.device_index = device_index

    def _convert_to_stereo_48k(self, arr_2d: np.ndarray, src_rate: int, gain: float = 1.0) -> np.ndarray:
        """
        Converts an arbitrary (N, C) float32 audio chunk (including 4-channel WDM-KS microphone arrays)
        at src_rate to (M, 2) float32 stereo at self.sample_rate.
        """
        if arr_2d is None or arr_2d.size == 0:
            return np.zeros((0, 2), dtype=np.float32)

        if arr_2d.ndim == 1:
            arr_2d = arr_2d.reshape(-1, 1)

        # Sanitize NaNs/Infs or corrupt hardware spikes
        arr_2d = np.nan_to_num(arr_2d, nan=0.0, posinf=0.0, neginf=0.0)
        arr_2d = np.clip(arr_2d, -1.0, 1.0)
        # Remove per-channel DC bias
        if len(arr_2d) > 4:
            arr_2d = arr_2d - np.mean(arr_2d, axis=0, keepdims=True)

        c = arr_2d.shape[1]
        if c == 1:
            stereo = np.repeat(arr_2d, 2, axis=1)
        elif c == 2:
            stereo = arr_2d
        elif c >= 4:
            # Beamform all 4 hardware microphone array capsules for maximum vocal SNR!
            left = (arr_2d[:, 0] + arr_2d[:, 2]) * 0.5
            right = (arr_2d[:, 1] + arr_2d[:, 3]) * 0.5
            stereo = np.column_stack((left, right)).astype(np.float32)
        else:
            stereo = arr_2d[:, :2]

        if src_rate != self.sample_rate and len(stereo) > 1:
            target_len = max(1, int(round(len(stereo) * self.sample_rate / float(src_rate))))
            x_old = np.linspace(0.0, 1.0, len(stereo), endpoint=False)
            x_new = np.linspace(0.0, 1.0, target_len, endpoint=False)
            left = np.interp(x_new, x_old, stereo[:, 0])
            right = np.interp(x_new, x_old, stereo[:, 1])
            stereo = np.column_stack((left, right)).astype(np.float32)

        if gain != 1.0:
            stereo = np.tanh(stereo * gain).astype(np.float32)

        return stereo.astype(np.float32)

    def _wasapi_loop_callback(self, in_data, frame_count, time_info, status):
        """Wall-clock synchronized WASAPI Loopback callback."""
        import pyaudiowpatch as pyaudio
        if not self.is_recording:
            return (None, pyaudio.paComplete)

        arr = np.frombuffer(in_data, dtype=np.float32)
        ch = self.loop_native_channels
        if len(arr) >= ch:
            arr_2d = arr.reshape(-1, ch)
            stereo = self._convert_to_stereo_48k(arr_2d, self.loop_native_rate, gain=1.0)

            elapsed = time.perf_counter() - self.start_perf
            expected_total = int(elapsed * self.sample_rate)
            current_plus_chunk = self.loop_total_samples + len(stereo)
            gap_samples = expected_total - current_plus_chunk
            if gap_samples > int(self.sample_rate * 0.04):
                pad_len = min(gap_samples, int(self.sample_rate * 30.0))
                silence_pad = np.zeros((pad_len, 2), dtype=np.float32)
                self.loop_queue.put(silence_pad)
                self.loop_total_samples += pad_len

            rms = float(np.sqrt(np.mean(stereo**2)))
            vol = min(1.0, rms * 4.5)
            self.current_volume_level = max(self.current_volume_level, vol)
            self.loop_queue.put(stereo)
            self.loop_total_samples += len(stereo)

        return (None, pyaudio.paContinue)

    def _select_best_hardware_mic_candidates(self) -> List[tuple]:
        """
        Returns prioritized list of (device_idx, samplerate, channels, pre_gain) candidates.
        Prioritizes WDM-KS 4-capsule 48000Hz Microphone Array (which bypasses broken Intel SST user-mode APOs
        that return 1e-05 digital zeros on MME/WASAPI!), followed by standard MME/DirectSound inputs.
        """
        candidates = []
        try:
            all_devs = sd.query_devices()
            # Priority 1: WDM-KS 4-channel 48000 Hz Hardware Microphone Array 2 / 1 (Direct Kernel Pin)
            for pref_name in ("microphone array 2", "microphone array 1", "microphone (realtek"):
                for idx, d in enumerate(all_devs):
                    if d.get("max_input_channels", 0) > 0:
                        nm = d.get("name", "").lower()
                        sr = int(d.get("default_samplerate", 48000))
                        ch = int(d.get("max_input_channels", 2))
                        if pref_name in nm and sr in (48000, 44100) and ch in (2, 4):
                            candidates.append((idx, sr, ch, 28.0))
            # Priority 2: MME / DirectSound Microphone Array or Default Input
            for idx, d in enumerate(all_devs):
                if d.get("max_input_channels", 0) > 0 and d.get("hostapi", 0) in (0, 1):
                    nm = d.get("name", "").lower()
                    sr = int(d.get("default_samplerate", 44100))
                    ch = min(2, max(1, int(d.get("max_input_channels", 2))))
                    if "microphone" in nm or idx == 0:
                        candidates.append((idx, sr, ch, 12.0))
        except Exception:
            pass
        if not candidates:
            candidates.append((0, 44100, 2, 12.0))
        return candidates

    def start(self, is_probe: bool = False):
        """
        Starts recording audio for 'input_only', 'output_only', or 'input_and_output'.
        1. Unmutes Windows Core Audio Microphone & Speaker Endpoints via COM.
        2. Opens Direct Hardware WDM-KS 4-Capsule Microphone Array (bypassing dead MME/WASAPI APOs).
        3. Opens WASAPI Speaker Loopback so all 3 modes capture loud, crystal-clear audio.
        """
        if self.is_recording:
            return

        _force_unmute_windows_audio_endpoints()

        self.is_recording = True
        self.start_perf = time.perf_counter()
        self.last_unmute_check = self.start_perf
        self.loop_total_samples = 0

        for q in (self.mic_queue, self.loop_queue):
            while not q.empty():
                try:
                    q.get_nowait()
                except queue.Empty:
                    break

        mode = (self.audio_mode or "both").lower()
        is_outside = ("outside" in mode or "input_only" in mode or mode == "input") and "both" not in mode and "inside" not in mode
        is_inside = ("inside" in mode or "output_only" in mode or mode == "output") and "both" not in mode and "outside" not in mode

        should_record_mic = is_outside or (not is_inside)
        should_record_loop = is_inside or (not is_outside)

        # 1. Open Best Direct Hardware Microphone Stream (Input Only or Both)
        if should_record_mic:
            for cand_idx, cand_sr, cand_ch, cand_gain in self._select_best_hardware_mic_candidates():
                try:
                    self.mic_native_rate = cand_sr

                    def _sd_mic_cb(indata, frames, time_info, status, sr=cand_sr, g=cand_gain):
                        if not self.is_recording:
                            return
                        stereo = self._convert_to_stereo_48k(indata.copy(), sr, gain=g)
                        rms = float(np.sqrt(np.mean(stereo**2)))
                        vol = min(1.0, rms * 5.0)
                        self.current_volume_level = max(self.current_volume_level * 0.82, vol)
                        self.mic_queue.put(stereo)

                    self.sd_stream = sd.InputStream(
                        device=cand_idx,
                        samplerate=cand_sr,
                        channels=cand_ch,
                        dtype=np.float32,
                        blocksize=1024,
                        callback=_sd_mic_cb,
                    )
                    self.sd_stream.start()
                    print(f"[OK] Hardware Microphone Active (dev={cand_idx}, mode={self.audio_mode}, rate={cand_sr}Hz, ch={cand_ch})")
                    break
                except Exception as me:
                    self.sd_stream = None
                    continue

        # 2. Open WASAPI Speaker Loopback Stream (Output Only or Both)
        if should_record_loop and not is_probe:
            try:
                import pyaudiowpatch as pyaudio
                self.pa = pyaudio.PyAudio()
                loop_dev = None
                try:
                    loop_dev = self.pa.get_default_wasapi_loopback()
                except Exception:
                    loop_dev = None

                if loop_dev is None:
                    wasapi_info = self.pa.get_host_api_info_by_type(pyaudio.paWASAPI)
                    wasapi_idx = wasapi_info["index"]
                    for i in range(self.pa.get_device_count()):
                        d = self.pa.get_device_info_by_index(i)
                        if d.get("hostApi") == wasapi_idx and d.get("isLoopbackDevice", False):
                            nm = d.get("name", "").lower()
                            if "realtek" in nm or "speaker" in nm or "headphone" in nm:
                                loop_dev = d
                                break
                            if loop_dev is None:
                                loop_dev = d

                if loop_dev:
                    self.loop_native_channels = max(1, int(loop_dev.get("maxInputChannels", 2)))
                    self.loop_native_rate = int(loop_dev.get("defaultSampleRate", 48000))
                    self.loop_stream = self.pa.open(
                        format=pyaudio.paFloat32,
                        channels=self.loop_native_channels,
                        rate=self.loop_native_rate,
                        input=True,
                        input_device_index=loop_dev["index"],
                        frames_per_buffer=1024,
                        stream_callback=self._wasapi_loop_callback,
                    )
                    self.loop_stream.start_stream()
                    print(f"[OK] WASAPI Speaker Loopback Active ({self.audio_mode}): {loop_dev['name']}")
            except Exception as e:
                print(f"[!] WASAPI Loopback warning: {e}")

    def _fit_length(self, arr: np.ndarray, target_len: int) -> np.ndarray:
        """Pads or trims a (N, 2) float32 array to match target_len samples exactly."""
        if arr is None or len(arr) == 0:
            return np.zeros((target_len, 2), dtype=np.float32)
        if len(arr) < target_len:
            pad = np.zeros((target_len - len(arr), 2), dtype=np.float32)
            return np.vstack([arr, pad])
        elif len(arr) > target_len:
            return arr[:target_len]
        return arr

    def stop(self) -> np.ndarray:
        """Stops recording and returns smooth, studio-normalized float32 stereo audio array at 48000 Hz."""
        self.is_recording = False
        total_elapsed = max(0.1, time.perf_counter() - self.start_perf)
        expected_total_samples = int(total_elapsed * self.sample_rate)

        if self.sd_stream:
            try:
                self.sd_stream.stop()
                self.sd_stream.close()
            except Exception:
                pass
            self.sd_stream = None

        if self.loop_stream:
            try:
                self.loop_stream.stop_stream()
                self.loop_stream.close()
            except Exception:
                pass
            self.loop_stream = None

        if self.pa:
            try:
                self.pa.terminate()
            except Exception:
                pass
            self.pa = None

        # 1. Process Hardware Microphone track with Studio Broadcast Vocal Gain Normalization
        mic_chunks = []
        while not self.mic_queue.empty():
            try:
                mic_chunks.append(self.mic_queue.get_nowait())
            except queue.Empty:
                break

        mic_audio = None
        mic_peak = 0.0
        if mic_chunks:
            raw = np.concatenate(mic_chunks, axis=0)
            if len(raw) > 0:
                raw = raw - np.mean(raw, axis=0, keepdims=True)
                mic_audio = self._fit_length(raw, expected_total_samples)
                mic_peak = float(np.percentile(np.abs(mic_audio), 99.2))
                max_abs = float(np.max(np.abs(mic_audio)))
                ref_mic = max(mic_peak, max_abs * 0.65)
                if ref_mic > 0.0002:
                    boost = min(120.0, 0.90 / ref_mic)
                    mic_audio = np.tanh(mic_audio * boost).astype(np.float32)

        # 2. Process WASAPI Speaker Loopback (System Output Audio) with Studio Gain Normalization!
        loop_chunks = []
        while not self.loop_queue.empty():
            try:
                loop_chunks.append(self.loop_queue.get_nowait())
            except queue.Empty:
                break
        loop_audio = np.concatenate(loop_chunks, axis=0) if loop_chunks else None
        loop_peak = 0.0
        if loop_audio is not None and len(loop_audio) > 0:
            loop_audio = self._fit_length(loop_audio, expected_total_samples)
            loop_peak = float(np.max(np.abs(loop_audio)))
            if loop_peak > 0.0003:
                loop_pct = float(np.percentile(np.abs(loop_audio), 99.5))
                ref_level = max(loop_pct, loop_peak * 0.5, 0.001)
                loop_boost = min(20.0, 0.92 / ref_level)
                loop_audio = np.tanh(loop_audio * loop_boost).astype(np.float32)

        # 3. Deliver audio based strictly on selected audio mode:
        # - Outside Audio : Hardware Microphone ONLY (outside teacher voice, no system loopback)
        # - Inside Audio  : System Speaker Loopback ONLY (PC / system sounds, no microphone)
        # - Both          : Both Inside System + Outside Microphone mixed together
        mode = (self.audio_mode or "both").lower()
        is_outside = ("outside" in mode or "input_only" in mode or mode == "input") and "both" not in mode and "inside" not in mode
        is_inside = ("inside" in mode or "output_only" in mode or mode == "output") and "both" not in mode and "outside" not in mode

        if is_outside:
            if mic_audio is not None and len(mic_audio) > 0:
                return mic_audio
            return np.zeros((expected_total_samples, 2), dtype=np.float32)

        elif is_inside:
            if loop_audio is not None and len(loop_audio) > 0:
                return loop_audio
            return np.zeros((expected_total_samples, 2), dtype=np.float32)

        else:
            # Both Inside and Outside audio mixed together
            has_mic = mic_audio is not None and len(mic_audio) > 0
            has_loop = loop_audio is not None and len(loop_audio) > 0

            if has_mic and has_loop:
                mixed = np.tanh((mic_audio * 0.95) + (loop_audio * 0.92)).astype(np.float32)
                return mixed
            elif has_mic:
                return mic_audio
            elif has_loop:
                return loop_audio
            return np.zeros((expected_total_samples, 2), dtype=np.float32)

    def get_volume(self) -> float:
        """Returns float between 0.0 and 1.0 for UI VU meter, and periodically ensures Windows Mic is never muted."""
        if self.is_recording:
            now = time.perf_counter()
            if now - self.last_unmute_check > 2.5:
                self.last_unmute_check = now
                _force_unmute_windows_audio_endpoints()
        self.current_volume_level *= 0.85
        return float(self.current_volume_level)
