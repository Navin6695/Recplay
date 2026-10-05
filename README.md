# Clipr Studio 2.0 - Complete Screen Recorder, Video & Music Player Suite

**Clipr Studio 2.0** is an all-in-one commercial-grade desktop production suite for Windows. It combines high-performance **1080p/4K screen recording**, **facecam overlay**, **3-way audio routing**, **interactive whiteboard with Paint tools**, and a **built-in high-fidelity Video & Music Player** in the same unified package.

---

## 🚀 What's New in Clipr 2.0

### 🎬 Built-in Video Player (Integrated in the Same Package)
- **Zero External Dependencies**: Powered by native `PyQt6.QtMultimedia` with hardware-accelerated video decoding.
- **Universal Video Format Support**: Plays `.mp4`, `.mkv`, `.avi`, `.mov`, `.webm`, `.flv`, `.wmv`, and `.m4v`.
- **Pro Playback Controls**:
  - Precision scrubber bar with instant click-to-seek and millisecond timestamp display.
  - Step jump controls: `⏪ 5s` backward and `5s ⏩` forward.
  - Variable speed playback: `0.5x`, `0.75x`, `1.0x`, `1.25x`, `1.5x`, and `2.0x`.
  - Master volume slider with mute toggle and smart volume restoration.
  - Single-track loop toggle (`🔁 Loop: ON / OFF`).
  - Seamless borderless **Fullscreen mode** (`⛶ Fullscreen` or press `F` / `Double-Click` / `ESC`).
  - **📸 1-Click Frame Snip**: Instantly capture and save full-resolution PNG stills from any video frame directly to your Pictures folder.
- **Collapsible Playlist Queue**:
  - Drag-and-drop video/audio files or folders directly into the player window.
  - Add files via file picker (`➕`) or clear playlist (`🗑️`).
  - Double-click any track or use `⏮️` and `⏭️` for playlist navigation.

### 🎵 Built-in Music & Audio Player
- **Universal Audio Format Support**: Plays `.mp3`, `.wav`, `.aac`, `.m4a`, `.flac`, `.ogg`, and `.wma`.
- **Animated Cyberpunk Frequency Visualizer**:
  - Dynamic 36-band frequency equalizer bars rendering in real-time with gradient peaks.
  - High-energy pulsing response to audio rhythms.
- **Spinning Vinyl Disc Core**:
  - Smooth rotating vinyl record turntable with glowing concentric rings.
  - Prominent track title, subtitle, bitrate, and file format metadata.

### 🔗 Deep Recorder Integration
- **Header Quick Launch**: Direct `🎬 Video Player` and `🎵 Music Player` launcher buttons in the main header bar.
- **Action Bar Access**: One-click `🎬 Media Player` in the bottom dashboard.
- **Floating Recording Bar**: Dedicated `🎬 Player` button on the floating widget.
- **Post-Recording Instant Play**: When a screen recording finishes, the save notification includes a **"▶️ Play in Clipr 2.0 Player"** button to immediately review the recorded video.
- **Standalone CLI & Bat Launch**: Launch directly into the media player via `Run_Player.bat` or `python main.py --player [media_file]`.

---

## 🎯 Screen Recording Features

1. **Smart Low-Storage Compression (CRF 23 H.264)**:
   - High visual quality with ultra-compact file size (up to 70% smaller than standard recorders).
2. **3 Professional Studio Audio Modes**:
   - 🎤 **Outside Audio (Mic Only)**: Captures only your voice / external microphone (ideal for classroom lectures).
   - 🔊 **Inside Audio (System Only)**: Captures internal PC audio / video audio without picking up background room noise.
   - 🎧 **Both (Inside + Outside)**: Concurrently captures microphone narration + internal computer audio.
3. **Select Area Mode with Invisible Outer Guide**:
   - Freehand drag selection tool.
   - Neon blue outer marking border indicates the active recording boundaries without being captured in the recorded video.
4. **DrawBoard with Full Paint Tools Suite (F8)**:
   - Freehand Pen with smooth anti-aliased curves.
   - Highlighter with semi-transparent tint.
   - Vector shapes: Rectangle, Circle/Ellipse, Vector Arrow, Straight Line.
   - Text tool for typing notes directly onto the screen.
   - Eraser with adjustable radius.
   - Fill Tool / Color Bucket for board background coloring.
   - EyeDropper / Color Picker.
   - Complete 10-swatch quick palette + custom QColorDialog picker.
   - 5 stroke thickness presets (2px to 24px) + Font size controls.
5. **Webcam Facecam with AI Body & Portrait Segmentation**:
   - **Mode Selection**:
     - 🎯 **Standard (Normal)**: Classical webcam with Square (1:1), Circular (Loom-style), or Rounded Rectangle overlay with custom border color.
     - 🌫️ **Background Blur (DSLR Studio Bokeh)**: Neural pixel-level person segmentation that keeps 100% of the presenter's body (hair, face, neck, shoulders, clothes, hands) razor-sharp while deeply blurring the room background with creamy bokeh.
     - 👤 **Face & Body Only (No Frame / Zero Background)**: Complete background removal — extracts the presenter's upper body with **zero room background, zero square borders, and zero circular borders**. The presenter's body floats seamlessly and organically directly over the recorded screen.
   - Powered by real-time MediaPipe Neural Selfie Segmentation ONNX + OpenCV YuNet face detection running at 150+ FPS on CPU.
   - Customizable corner placements: Bottom-Right, Bottom-Left, Top-Right, Top-Left.
   - Live camera preview, framing test, and optional camera auto-start toggle on app launch.
6. **Hardware-Locked Commercial RSA-2048 Licensing**:
   - Cryptographically signed 20-character formatted license keys (`XXXXX-XXXXX-XXXXX-XXXXX`).
   - Built-in Seller Key Generator GUI (`licensing_admin/admin_keygen.py`).

---

## 📁 Project Structure

```
d:\Clipr 2.0\
├── assets\                     # Application icons and branding
│   └── models\                # Pre-trained ONNX models (YuNet face detection)
├── core\
│   ├── audio_recorder.py      # Multi-mode sounddevice audio capture (Mic, System WASAPI, Both)
│   ├── face_processor.py      # AI face detection, background blur & borderless face cutout
│   ├── hwid.py                # Hardware ID generator for PC locking
│   ├── license_verifier.py    # RSA-2048 verification & 20-digit license parsing
│   └── screen_recorder.py     # FFmpeg CRF low-filesize video recorder pipeline
├── keys\
│   ├── private_key.pem        # MASTER PRIVATE KEY (Keep secret!)
│   └── public_key.pem         # Embedded client public key
├── licensing_admin\
│   └── admin_keygen.py        # Admin key generation tool for selling licenses
├── tests\
│   ├── test_facecam_modes.py  # Tests for FaceCamProcessor, blur, cutout & rendering
│   ├── test_media_player.py   # Comprehensive unit tests for Video & Music player
│   └── test_*.py              # 55 automated unit and integration tests
├── ui\
│   ├── floating_facecam.py    # Live borderless floating webcam preview widget
│   ├── main_window.py         # Main studio dashboard UI & player integration
│   ├── media_player.py        # StudioMediaPlayer (Video & Music Player + Visualizer)
│   ├── screen_annotator.py    # DrawBoard with Paint tools & whiteboard
│   ├── license_dialog.py      # Customer activation dialog
│   └── webcam_preview.py      # Live camera preview dialog
├── build_exe.py               # Standalone PyInstaller .exe compiler
├── Clipr.spec                 # PyInstaller specification file
├── main.py                    # Application entry point with --player CLI support
├── Run_Clipr.bat              # 1-click launcher for Clipr Studio 2.0
├── Run_Player.bat             # 1-click launcher for Clipr 2.0 Media Player
└── Run_Keygen.bat             # 1-click launcher for Key Generator
```

---

## 🚀 How to Run

### Launch Clipr Studio 2.0
Double-click `Run_Clipr.bat` or run:
```powershell
d:\ScreenRecorderPro\.venv\Scripts\python.exe main.py
```

### Launch Media Player Directly
Double-click `Run_Player.bat` or run:
```powershell
d:\ScreenRecorderPro\.venv\Scripts\python.exe main.py --player
```
Or open any media file directly:
```powershell
d:\ScreenRecorderPro\.venv\Scripts\python.exe main.py "C:\Path\To\Video.mp4"
```

### Run All Automated Unit Tests
```powershell
d:\ScreenRecorderPro\.venv\Scripts\python.exe -m unittest discover -s tests
```
*Current test suite: **55 / 55 tests passing**.*
