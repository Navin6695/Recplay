# Privacy Policy - Recplay 2.0 Studio

**Last Updated:** October 2026  
**Application:** Recplay 2.0 - Studio Suite & Media Player  
**Publisher:** Recplay Studio  
**Official URL:** https://recplay.github.io/privacy  

---

### Core Privacy Commitment
> **Recplay 2.0 Studio is an offline-first desktop application.**  
> We do **NOT** collect, upload, monitor, sell, or transmit your screen recordings, camera feeds, microphone audio, keystrokes, or media files. All data processing occurs 100% on your local computer.

---

### 1. Data Collection and Usage Practices

- **Screen & Display Capture:**  
  Frames are captured strictly in system memory on your local GPU/CPU only when you actively trigger recording. Compressed output files (.mp4/.mkv) are written directly to your chosen local disk path (`Videos/Recplay_Recordings`).
- **Microphone & Desktop Audio:**  
  Audio capture (WASAPI loopback & microphone) operates only during user-initiated recording sessions. No voice or audio samples are ever stored in cloud memory or transmitted externally.
- **Webcam / Facecam Feeds:**  
  Processed in real-time through local computer vision algorithms (e.g. OpenCV background blur & body cutout). No biometric templates or images leave your machine.
- **Subtitles & Transcriptions:**  
  When live subtitles are enabled, speech-to-text operates locally or via standard operating system speech synthesis solely to produce local `.srt` tracks or burned-in captions.
- **Keystroke Visualizer:**  
  Tutorial keyboard shortcut badges (e.g. `Ctrl+C`) are evaluated locally on the active frame and never logged to disk or transmitted.

---

### 2. Network and Cloud Operations

Recplay contains **zero advertising SDKs, zero telemetry collectors, and zero background analytics** (no Google Analytics, no telemetry beacons).  
The only network operations:
1. **Cryptographic License Verification:** An optional one-way SHA-256 hash of the machine hardware identifier to ensure 1-PC-per-key activation. No personal identities, email addresses, or files are sent.
2. **Microsoft Store Entitlement:** If acquired via Microsoft Store, licensing is managed through native Windows Store WinRT services.

---

### 3. Microsoft Store Certification Compliance

Recplay 2.0 strictly follows Microsoft Store Application Certification Policies:
- **Policy 10.5.1 / 10.5.2 (Privacy & Permissions):** Clear, prominent disclosure and user consent for camera, microphone, and screen access.
- **Policy 10.2.1 (Full Control & Clean Uninstallation):** Registers cleanly in Windows Control Panel (`Programs and Features`) and Windows Settings (`Installed Apps`). Uninstallation removes all program files, shortcuts, and registry keys without residual services.

---

### 4. Contact Information

- **Developer:** Recplay Studio  
- **Website:** https://recplay.github.io/privacy  
- **Email:** support@recplay.studio  
