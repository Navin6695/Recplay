r"""
Recplay 2.0 Windows Setup Wizard
Provides a seamless, graphical Windows installation experience for Recplay 2.0 on ANY Windows computer.
Installs application files to %LOCALAPPDATA%\Programs\Recplay, creates Desktop and Start Menu shortcuts,
registers in Windows Control Panel (Programs and Features / Installed Apps) with complete uninstaller,
and provides direct Privacy Policy links for Microsoft Store certification.
"""

import os
import sys
import shutil
import zipfile
import subprocess
import ctypes
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QWizard, QWizardPage, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QCheckBox, QProgressBar,
    QFileDialog, QMessageBox, QWidget, QFrame
)
from PyQt6.QtGui import QPixmap, QIcon, QFont, QColor, QDesktopServices
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QUrl


def get_default_install_dir() -> Path:
    local_appdata = os.getenv("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    return Path(local_appdata) / "Programs" / "Recplay"


def open_privacy_policy():
    """Opens local or online Privacy Policy."""
    policy_html = Path(__file__).resolve().parent.parent / "privacy_policy.html"
    if policy_html.exists():
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(policy_html)))
    else:
        QDesktopServices.openUrl(QUrl("https://recplay.github.io/privacy"))


def create_windows_shortcut(target_exe: Path, shortcut_path: Path, args: str = "", icon_path: Path = None, description: str = ""):
    """Creates a Windows .lnk shortcut silently using WScript.Shell via PowerShell."""
    shortcut_path.parent.mkdir(parents=True, exist_ok=True)
    icon_arg = f'$Shortcut.IconLocation = "{icon_path},0";' if icon_path and icon_path.exists() else ''
    args_arg = f'$Shortcut.Arguments = "{args}";' if args else ''
    desc_arg = f'$Shortcut.Description = "{description}";' if description else ''
    ps_script = f"""
    $WshShell = New-Object -comObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
    $Shortcut.TargetPath = "{target_exe}"
    $Shortcut.WorkingDirectory = "{target_exe.parent}"
    {args_arg}
    {desc_arg}
    {icon_arg}
    $Shortcut.Save()
    """
    try:
        no_win_flag = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        sinfo = None
        if sys.platform == "win32":
            sinfo = subprocess.STARTUPINFO()
            sinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            sinfo.wShowWindow = subprocess.SW_HIDE
        subprocess.run(
            ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps_script],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=no_win_flag,
            startupinfo=sinfo,
            check=True,
        )
    except Exception as e:
        print(f"[!] Shortcut creation error: {e}")


def register_control_panel_uninstaller(target_dir: Path, target_exe: Path):
    """
    Registers Recplay 2.0 in the Windows Control Panel (Programs and Features / Installed Apps)
    so users can cleanly uninstall it directly from Windows Settings or Control Panel.
    """
    if sys.platform != "win32":
        return
    try:
        import winreg

        # Calculate estimated installed size in KB
        total_size_bytes = 0
        try:
            for f in target_dir.rglob('*'):
                if f.is_file():
                    total_size_bytes += f.stat().st_size
        except Exception:
            total_size_bytes = 180 * 1024 * 1024
        size_kb = int(total_size_bytes / 1024)

        uninstaller_bat = target_dir / "Uninstall.bat"
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\Recplay"

        with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE) as key:
            winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, "Recplay 2.0 - Studio Suite & Media Player")
            winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, "2.0.0")
            winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, "Recplay Studio")
            winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, str(target_dir))
            winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, f"{target_exe},0")
            winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, f'"{uninstaller_bat}"')
            winreg.SetValueEx(key, "QuietUninstallString", 0, winreg.REG_SZ, f'"{uninstaller_bat}" /quiet')
            winreg.SetValueEx(key, "HelpLink", 0, winreg.REG_SZ, "https://recplay.github.io/privacy")
            winreg.SetValueEx(key, "URLInfoAbout", 0, winreg.REG_SZ, "https://recplay.github.io/privacy")
            winreg.SetValueEx(key, "NoModify", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "NoRepair", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "EstimatedSize", 0, winreg.REG_DWORD, size_kb)
    except Exception as e:
        print(f"[!] Windows Registry uninstallation registration error: {e}")


def create_page_header(title_text: str, subtitle_text: str) -> QWidget:
    """Creates a high-contrast branded header banner with the Recplay icon and crisp cyan typography."""
    container = QWidget()
    c_lay = QVBoxLayout(container)
    c_lay.setContentsMargins(0, 0, 0, 8)
    c_lay.setSpacing(6)

    h_widget = QWidget()
    h_lay = QHBoxLayout(h_widget)
    h_lay.setContentsMargins(0, 0, 0, 0)
    h_lay.setSpacing(12)

    icon_lbl = QLabel()
    icon_candidates = [
        Path(__file__).resolve().parent.parent / "assets" / "icon.png",
        Path(__file__).resolve().parent / "assets" / "icon.png",
        Path(r"D:\Clipr\2.0\assets\icon.png"),
    ]
    icon_pix = None
    for icp in icon_candidates:
        if icp.exists():
            icon_pix = QPixmap(str(icp)).scaled(
                44, 44, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
            break
    if icon_pix and not icon_pix.isNull():
        icon_lbl.setPixmap(icon_pix)
    h_lay.addWidget(icon_lbl)

    col = QVBoxLayout()
    col.setSpacing(2)
    t = QLabel(title_text)
    t.setStyleSheet("font-size: 18px; font-weight: 900; color: #00F0FF; letter-spacing: 0.5px; background: transparent;")
    st = QLabel(subtitle_text)
    st.setStyleSheet("font-size: 12px; font-weight: bold; color: #38BDF8; background: transparent;")
    col.addWidget(t)
    col.addWidget(st)
    h_lay.addLayout(col, 1)
    c_lay.addWidget(h_widget)

    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setStyleSheet("background-color: #0284C7; max-height: 2px;")
    c_lay.addWidget(line)
    return container


class WelcomePage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 12, 18, 12)
        layout.setSpacing(12)

        layout.addWidget(create_page_header("Welcome to Recplay 2.0 Setup", "Studio Screen Recorder • AI Facecam • Media Player"))

        card = QFrame()
        card.setObjectName("welcomeCard")
        card.setStyleSheet("""
            QFrame#welcomeCard {
                background-color: #0F172A;
                border: 1.5px solid #0284C7;
                border-radius: 10px;
            }
        """)
        c_lay = QVBoxLayout(card)
        c_lay.setContentsMargins(16, 14, 16, 14)
        c_lay.setSpacing(8)

        intro = QLabel("This wizard will install <b>Recplay 2.0 Studio Suite</b> on your computer.")
        intro.setStyleSheet("color: #FFFFFF; font-size: 13px; font-weight: 600; background: transparent;")
        c_lay.addWidget(intro)

        feats_title = QLabel("Included Studio Features:")
        feats_title.setStyleSheet("color: #00F0FF; font-weight: bold; font-size: 13px; margin-top: 4px; background: transparent;")
        c_lay.addWidget(feats_title)

        bullets = [
            "●  Ultra-Low CPU Studio Screen Recording (CRF 22-26, 30 FPS, H.264)",
            "●  AI Webcam Facecam: No-Frame Body Cutout & DSLR Studio Bokeh Blur",
            "●  Live Subtitles & Closed Captions (.SRT export & embedded captions)",
            "●  Inside Audio (WASAPI System Audio) & Outside Audio (Microphone)",
            "●  Integrated Studio Media Player with Animated Audio Deck & Equalizer",
            "●  Live Draw & Annotate, Snipping Screenshot Tool & YouTube Chapters",
        ]
        for b in bullets:
            lbl = QLabel(b)
            lbl.setStyleSheet("color: #F8FAFC; font-size: 12px; font-weight: 600; margin-left: 6px; background: transparent;")
            c_lay.addWidget(lbl)

        outro = QLabel("Click <b>Next</b> to choose the destination folder and proceed.")
        outro.setStyleSheet("color: #38BDF8; font-weight: bold; font-size: 13px; margin-top: 6px; background: transparent;")
        c_lay.addWidget(outro)

        layout.addWidget(card)

        # Privacy link
        priv_row = QHBoxLayout()
        btn_priv = QPushButton("🛡️ View Privacy Policy")
        btn_priv.setStyleSheet("""
            QPushButton {
                background-color: #0F172A;
                color: #00F0FF;
                border: 1.5px solid #0284C7;
                border-radius: 6px;
                font-size: 11px;
                font-weight: bold;
                padding: 6px 14px;
            }
            QPushButton:hover {
                background-color: #0284C7;
                color: #FFFFFF;
            }
        """)
        btn_priv.clicked.connect(open_privacy_policy)
        priv_row.addWidget(btn_priv)
        priv_row.addStretch()
        layout.addLayout(priv_row)
        layout.addStretch()


class DirectoryPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 12, 18, 12)
        layout.setSpacing(14)

        layout.addWidget(create_page_header("Select Destination Location", "Where should Recplay 2.0 be installed?"))

        card = QFrame()
        card.setObjectName("dirCard")
        card.setStyleSheet("""
            QFrame#dirCard {
                background-color: #0F172A;
                border: 1.5px solid #0284C7;
                border-radius: 10px;
            }
        """)
        c_lay = QVBoxLayout(card)
        c_lay.setContentsMargins(16, 16, 16, 16)
        c_lay.setSpacing(12)

        info = QLabel("Setup will install Recplay 2.0 into the following folder on your computer:")
        info.setStyleSheet("color: #FFFFFF; font-size: 13px; font-weight: bold; background: transparent;")
        c_lay.addWidget(info)

        h_row = QHBoxLayout()
        h_row.setSpacing(10)
        self.path_edit = QLineEdit(str(get_default_install_dir()))
        self.path_edit.setStyleSheet(
            "background-color: #1E293B; color: #FFFFFF; padding: 10px 12px; "
            "border: 1.5px solid #0284C7; border-radius: 6px; font-size: 13px; font-weight: bold;"
        )
        btn_browse = QPushButton("📁 Browse...")
        btn_browse.setStyleSheet("""
            QPushButton {
                background-color: #0284C7;
                color: #FFFFFF;
                border: 1.5px solid #00F0FF;
                border-radius: 6px;
                padding: 9px 16px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #00F0FF;
                color: #060C18;
            }
        """)
        btn_browse.clicked.connect(self._browse)
        h_row.addWidget(self.path_edit, 1)
        h_row.addWidget(btn_browse)
        c_lay.addLayout(h_row)

        space_lbl = QLabel("💾 Space Required: At least 180 MB of free disk space is required.")
        space_lbl.setStyleSheet("color: #38BDF8; font-size: 12px; font-weight: bold; margin-top: 4px; background: transparent;")
        c_lay.addWidget(space_lbl)

        layout.addWidget(card)
        layout.addStretch()

    def _browse(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Install Directory", self.path_edit.text())
        if folder:
            self.path_edit.setText(str(Path(folder) / "Recplay"))

    def get_install_dir(self) -> Path:
        return Path(self.path_edit.text().strip())


class ComponentSelectionPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 12, 18, 12)
        layout.setSpacing(12)

        layout.addWidget(create_page_header("Select Applications to Install", "Choose which Recplay components to install on your computer:"))

        # 1. Video Recorder Component Box
        rec_box = QFrame()
        rec_box.setObjectName("recBox")
        rec_box.setStyleSheet("""
            QFrame#recBox {
                background-color: #0F172A;
                border: 1.5px solid #0284C7;
                border-radius: 8px;
            }
        """)
        rec_lay = QVBoxLayout(rec_box)
        rec_lay.setContentsMargins(14, 12, 14, 12)
        rec_lay.setSpacing(6)

        self.chk_recorder = QCheckBox("🎥  Recplay 2.0 Studio Video Recorder")
        self.chk_recorder.setChecked(True)
        self.chk_recorder.setStyleSheet("""
            QCheckBox {
                font-size: 14px;
                font-weight: 900;
                color: #00F0FF;
                border: none;
                background: transparent;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                background-color: #1E293B;
                border: 1.5px solid #00F0FF;
                border-radius: 4px;
            }
            QCheckBox::indicator:checked {
                background-color: #00F0FF;
            }
        """)
        self.chk_recorder.stateChanged.connect(self._on_component_toggled)
        rec_lay.addWidget(self.chk_recorder)

        lbl_rec_desc = QLabel(
            "Ultra-low CPU 1080p/4K recording, AI Webcam Facecam (No-Frame cutout & Studio bokeh blur), "
            "Dual Inside/Outside Audio, Annotations & Auto-Hiding Floating Bar."
        )
        lbl_rec_desc.setWordWrap(True)
        lbl_rec_desc.setStyleSheet("color: #FFFFFF; font-size: 12px; font-weight: 500; border: none; background: transparent; margin-left: 26px;")
        rec_lay.addWidget(lbl_rec_desc)
        layout.addWidget(rec_box)

        # 2. Media Player Component Box
        player_box = QFrame()
        player_box.setObjectName("playerBox")
        player_box.setStyleSheet("""
            QFrame#playerBox {
                background-color: #0F172A;
                border: 1.5px solid #0284C7;
                border-radius: 8px;
            }
        """)
        player_lay = QVBoxLayout(player_box)
        player_lay.setContentsMargins(14, 12, 14, 12)
        player_lay.setSpacing(6)

        self.chk_player = QCheckBox("🎬  Recplay 2.0 Studio Media Player")
        self.chk_player.setChecked(True)
        self.chk_player.setStyleSheet("""
            QCheckBox {
                font-size: 14px;
                font-weight: 900;
                color: #38BDF8;
                border: none;
                background: transparent;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                background-color: #1E293B;
                border: 1.5px solid #38BDF8;
                border-radius: 4px;
            }
            QCheckBox::indicator:checked {
                background-color: #38BDF8;
            }
        """)
        self.chk_player.stateChanged.connect(self._on_component_toggled)
        player_lay.addWidget(self.chk_player)

        lbl_player_desc = QLabel(
            "Full-featured Video & Audio Player with animated Arc Reactor theme, 48-band equalizer, "
            "fullscreen mode, video frame capture, and instant sound cutoff on window close."
        )
        lbl_player_desc.setWordWrap(True)
        lbl_player_desc.setStyleSheet("color: #FFFFFF; font-size: 12px; font-weight: 500; border: none; background: transparent; margin-left: 26px;")
        player_lay.addWidget(lbl_player_desc)
        layout.addWidget(player_box)

        # Shortcut preferences card
        sc_card = QFrame()
        sc_card.setObjectName("scCard")
        sc_card.setStyleSheet("""
            QFrame#scCard {
                background-color: #0F172A;
                border: 1.5px solid #0284C7;
                border-radius: 8px;
            }
        """)
        sc_lay = QVBoxLayout(sc_card)
        sc_lay.setContentsMargins(14, 10, 14, 10)
        sc_lay.setSpacing(6)

        self.chk_desktop = QCheckBox("Create Desktop shortcut(s) for selected applications")
        self.chk_desktop.setChecked(True)
        self.chk_desktop.setStyleSheet("""
            QCheckBox {
                color: #FFFFFF;
                font-size: 12px;
                font-weight: bold;
                background: transparent;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                background-color: #1E293B;
                border: 1.5px solid #0284C7;
                border-radius: 4px;
            }
            QCheckBox::indicator:checked {
                background-color: #00F0FF;
            }
        """)
        sc_lay.addWidget(self.chk_desktop)

        self.chk_startmenu = QCheckBox("Create Start Menu shortcut(s) for selected applications")
        self.chk_startmenu.setChecked(True)
        self.chk_startmenu.setStyleSheet("""
            QCheckBox {
                color: #FFFFFF;
                font-size: 12px;
                font-weight: bold;
                background: transparent;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                background-color: #1E293B;
                border: 1.5px solid #0284C7;
                border-radius: 4px;
            }
            QCheckBox::indicator:checked {
                background-color: #00F0FF;
            }
        """)
        sc_lay.addWidget(self.chk_startmenu)
        layout.addWidget(sc_card)

        layout.addStretch()

    def _on_component_toggled(self):
        self.completeChanged.emit()

    def isComplete(self) -> bool:
        return self.chk_recorder.isChecked() or self.chk_player.isChecked()


class InstallWorker(QThread):
    progress_changed = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str)

    def __init__(
        self,
        source_dir: Path,
        target_dir: Path,
        install_recorder: bool,
        install_player: bool,
        create_desktop: bool,
        create_start: bool,
    ):
        super().__init__()
        self.source_dir = source_dir
        self.target_dir = target_dir
        self.install_recorder = install_recorder
        self.install_player = install_player
        self.create_desktop = create_desktop
        self.create_start = create_start

    def run(self):
        try:
            self.progress_changed.emit(10, "Preparing installation folder...")
            self.target_dir.mkdir(parents=True, exist_ok=True)

            self.progress_changed.emit(25, "Extracting and copying application files...")

            # 1. Locate bundled zip or source files across MEIPASS, executable dir, and source dirs
            zip_candidate = None
            meipass = getattr(sys, '_MEIPASS', None)

            search_paths = []
            if meipass:
                search_paths.append(Path(meipass))
            search_paths.append(Path(sys.executable).parent)
            search_paths.append(Path(__file__).resolve().parent)
            search_paths.append(Path(__file__).resolve().parent.parent)
            search_paths.append(Path(__file__).resolve().parent.parent / "dist")
            search_paths.append(self.source_dir)
            search_paths.append(Path("D:/Clipr/2.0"))
            search_paths.append(Path("D:/Clipr"))

            for sp in search_paths:
                if not sp or not sp.exists():
                    continue
                for name in [
                    "Recplay_2.0_Windows_Package.zip",
                    "Recplay_Windows_Package.zip",
                    "Clipr_2.0_Windows_Package.zip",
                    "Clipr_Windows_Package.zip",
                ]:
                    p = sp / name
                    if p.is_file():
                        zip_candidate = p
                        break
                if zip_candidate:
                    break
                for p in sp.glob("*Recplay*.zip"):
                    if p.is_file():
                        zip_candidate = p
                        break
                if zip_candidate:
                    break
                for p in sp.glob("*Clipr*.zip"):
                    if p.is_file():
                        zip_candidate = p
                        break
                if zip_candidate:
                    break

            if zip_candidate and zip_candidate.exists():
                with zipfile.ZipFile(str(zip_candidate), "r") as z:
                    total_items = len(z.infolist())
                    for i, item in enumerate(z.infolist()):
                        z.extract(item, str(self.target_dir))
                        if i % max(1, total_items // 20) == 0:
                            pct = 25 + int((i / total_items) * 45)
                            self.progress_changed.emit(pct, f"Installing {item.filename[:40]}...")
            elif self.source_dir.exists():
                all_items = list(self.source_dir.glob("*"))
                for i, item in enumerate(all_items):
                    dest = self.target_dir / item.name
                    if item.is_dir():
                        if dest.exists():
                            shutil.rmtree(dest)
                        shutil.copytree(item, dest)
                    else:
                        shutil.copy2(item, dest)
                    pct = 25 + int((i / max(1, len(all_items))) * 45)
                    self.progress_changed.emit(pct, f"Installing {item.name}...")

            # Flatten nested Recplay/Clipr folder if extracted as subfolder
            for sub_name in ["Recplay", "Clipr"]:
                nested = self.target_dir / sub_name
                if nested.exists() and (nested / f"{sub_name}.exe").exists():
                    for child in nested.iterdir():
                        dest_child = self.target_dir / child.name
                        if dest_child.exists():
                            if dest_child.is_dir():
                                shutil.rmtree(dest_child)
                            else:
                                dest_child.unlink()
                        shutil.move(str(child), str(self.target_dir))
                    try:
                        nested.rmdir()
                    except Exception:
                        pass

            self.progress_changed.emit(75, "Configuring executable and creating Windows shortcuts...")

            # Identify or normalize target executable
            target_exe = self.target_dir / "Recplay.exe"
            if not target_exe.exists():
                legacy_exe = self.target_dir / "Clipr.exe"
                if legacy_exe.exists():
                    try:
                        shutil.copy2(legacy_exe, target_exe)
                    except Exception:
                        target_exe = legacy_exe

            icon_ico = target_exe.parent / "assets" / "icon.ico"

            target_keygen = self.target_dir / "Recplay_Keygen.exe"
            keygen_target_exe = target_keygen if target_keygen.exists() else target_exe
            keygen_args = "" if target_keygen.exists() else "--keygen"

            # Desktop shortcuts (strictly ONE main app shortcut + ONE keygen shortcut)
            desktop = Path.home() / "Desktop"
            onedrive_desktop = Path.home() / "OneDrive" / "Desktop"
            for d in [desktop, onedrive_desktop]:
                if d.exists() and self.create_desktop:
                    if self.install_recorder:
                        create_windows_shortcut(target_exe, d / "Recplay 2.0.lnk", "", icon_ico, "Recplay 2.0 - Studio Video Recorder & Media Player")
                    # Recplay Keygen shortcut pointing reliably to target_exe --keygen
                    create_windows_shortcut(target_exe, d / "Recplay Keygen.lnk", "--keygen", icon_ico, "Recplay 2.0 - License Key Generator")

            # Start Menu shortcuts
            if self.create_start:
                start_programs = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
                if self.install_recorder:
                    create_windows_shortcut(target_exe, start_programs / "Recplay 2.0.lnk", "", icon_ico, "Recplay 2.0 - Studio Video Recorder & Media Player")
                if self.install_player:
                    create_windows_shortcut(target_exe, start_programs / "Recplay Media Player.lnk", "--player", icon_ico, "Recplay 2.0 - Studio Media Player")
                create_windows_shortcut(target_exe, start_programs / "Recplay Keygen.lnk", "--keygen", icon_ico, "Recplay 2.0 - License Key Generator")

            self.progress_changed.emit(88, "Writing uninstaller and registering in Windows Control Panel...")
            self._write_uninstaller(target_exe)
            register_control_panel_uninstaller(self.target_dir, target_exe)

            self.progress_changed.emit(100, "Installation completed successfully!")
            self.finished.emit(True, str(target_exe))

        except Exception as e:
            self.finished.emit(False, str(e))

    def _write_uninstaller(self, target_exe: Path):
        uninstaller_bat = target_exe.parent / "Uninstall.bat"
        uninstaller_bat.write_text(f"""@echo off
title Recplay 2.0 - Uninstaller
echo ==========================================================
echo   Uninstalling Recplay 2.0 Studio Suite...
echo ==========================================================
taskkill /f /im Recplay.exe >nul 2>&1
taskkill /f /im Clipr.exe >nul 2>&1

rem Remove Windows Control Panel / Settings uninstaller registry entry
reg delete "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\Recplay" /f >nul 2>&1
reg delete "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\Clipr" /f >nul 2>&1

rem Clean up Desktop shortcuts
del "%USERPROFILE%\\Desktop\\Recplay 2.0.lnk" 2>nul
del "%USERPROFILE%\\Desktop\\Recplay.lnk" 2>nul
del "%USERPROFILE%\\Desktop\\Recplay 2.0 Player.lnk" 2>nul
del "%USERPROFILE%\\Desktop\\Recplay Media Player.lnk" 2>nul
del "%USERPROFILE%\\Desktop\\Recplay Keygen.lnk" 2>nul
del "%USERPROFILE%\\OneDrive\\Desktop\\Recplay 2.0.lnk" 2>nul
del "%USERPROFILE%\\OneDrive\\Desktop\\Recplay.lnk" 2>nul
del "%USERPROFILE%\\OneDrive\\Desktop\\Recplay 2.0 Player.lnk" 2>nul
del "%USERPROFILE%\\OneDrive\\Desktop\\Recplay Media Player.lnk" 2>nul
del "%USERPROFILE%\\OneDrive\\Desktop\\Recplay Keygen.lnk" 2>nul
del "%USERPROFILE%\\Desktop\\Clipr*.lnk" 2>nul
del "%USERPROFILE%\\OneDrive\\Desktop\\Clipr*.lnk" 2>nul

rem Clean up Start Menu shortcuts
del "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Recplay 2.0.lnk" 2>nul
del "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Recplay.lnk" 2>nul
del "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Recplay Media Player.lnk" 2>nul
del "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Recplay 2.0 Player.lnk" 2>nul
del "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Recplay Keygen.lnk" 2>nul
del "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Clipr*.lnk" 2>nul
del "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Recplay Media Player.lnk" 2>nul
del "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Recplay 2.0 Player.lnk" 2>nul
del "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Clipr*.lnk" 2>nul

echo [OK] Shortcuts and Control Panel registration removed.
set "INSTALL_DIR=%~dp0"
cd /d "%TEMP%"
start /b cmd /c "timeout /t 2 /nobreak >nul & rmdir /s /q \"%INSTALL_DIR%\""
echo [OK] Recplay 2.0 has been cleanly uninstalled from your computer.

if not "%1"=="/quiet" (
    powershell -NoProfile -Command "[System.Windows.Forms.MessageBox]::Show('Recplay 2.0 has been successfully uninstalled from your computer.', 'Recplay 2.0 Uninstaller', [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Information)" 2>nul
)
""", encoding="utf-8")


class InstallPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 12, 18, 12)
        layout.setSpacing(14)

        layout.addWidget(create_page_header("Installing Recplay 2.0", "Please wait while Setup installs Recplay 2.0 on your computer..."))

        card = QFrame()
        card.setObjectName("installCard")
        card.setStyleSheet("""
            QFrame#installCard {
                background-color: #0F172A;
                border: 1.5px solid #0284C7;
                border-radius: 10px;
            }
        """)
        c_lay = QVBoxLayout(card)
        c_lay.setContentsMargins(16, 18, 16, 18)
        c_lay.setSpacing(14)

        self.lbl_status = QLabel("Extracting and installing files...")
        self.lbl_status.setStyleSheet("color: #FFFFFF; font-size: 13px; font-weight: bold; background: transparent;")
        c_lay.addWidget(self.lbl_status)

        self.pbar = QProgressBar()
        self.pbar.setRange(0, 100)
        self.pbar.setValue(0)
        self.pbar.setStyleSheet("""
            QProgressBar {
                background-color: #1E293B;
                border: 1.5px solid #00F0FF;
                border-radius: 6px;
                height: 22px;
                text-align: center;
                color: #FFFFFF;
                font-weight: bold;
                font-size: 12px;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284C7, stop:1 #00F0FF);
                border-radius: 4px;
            }
        """)
        c_lay.addWidget(self.pbar)

        sub_info = QLabel("Configuring studio codecs, DirectX display capture, and hardware acceleration...")
        sub_info.setStyleSheet("color: #38BDF8; font-size: 12px; font-weight: 600; background: transparent;")
        c_lay.addWidget(sub_info)

        layout.addWidget(card)
        layout.addStretch()

        self.is_done = False
        self.installed_exe = ""

    def initializePage(self):
        wizard = self.wizard()
        target_dir = wizard.dir_page.get_install_dir()
        install_rec = wizard.component_page.chk_recorder.isChecked()
        install_player = wizard.component_page.chk_player.isChecked()
        create_desktop = wizard.component_page.chk_desktop.isChecked()
        create_start = wizard.component_page.chk_startmenu.isChecked()

        base_dir = Path(__file__).resolve().parent.parent
        source_dir = base_dir / "dist" / "Recplay"
        if not source_dir.exists():
            source_dir = base_dir / "dist" / "Clipr"
        if not source_dir.exists():
            source_dir = base_dir

        self.worker = InstallWorker(
            source_dir,
            target_dir,
            install_recorder=install_rec,
            install_player=install_player,
            create_desktop=create_desktop,
            create_start=create_start,
        )
        self.worker.progress_changed.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()

    def _on_progress(self, val: int, msg: str):
        self.pbar.setValue(val)
        self.lbl_status.setText(msg)

    def _on_finished(self, success: bool, res: str):
        if success:
            self.is_done = True
            self.installed_exe = res
            self.completeChanged.emit()
            self.wizard().next()
        else:
            QMessageBox.critical(self, "Installation Failed", f"Setup encountered an error:\n\n{res}")

    def isComplete(self):
        return self.is_done


class FinishedPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 12, 18, 12)
        layout.setSpacing(12)

        layout.addWidget(create_page_header("Completing Recplay 2.0 Setup", "Installation completed successfully!"))

        card = QFrame()
        card.setObjectName("finishedCard")
        card.setStyleSheet("""
            QFrame#finishedCard {
                background-color: #0F172A;
                border: 1.5px solid #0284C7;
                border-radius: 10px;
            }
        """)
        c_lay = QVBoxLayout(card)
        c_lay.setContentsMargins(16, 14, 16, 14)
        c_lay.setSpacing(10)

        self.done_lbl = QLabel(
            "Setup has finished installing your selected <b>Recplay 2.0</b> application(s) on your computer.<br><br>"
            "Windows Control Panel uninstallation entry and desktop shortcuts have been registered.<br>"
            "You can launch the application now or anytime using the desktop shortcuts."
        )
        self.done_lbl.setStyleSheet("color: #FFFFFF; font-size: 13px; font-weight: 600; line-height: 1.5; background: transparent;")
        c_lay.addWidget(self.done_lbl)

        self.chk_launch_rec = QCheckBox("🚀  Launch Recplay 2.0 Video Recorder now")
        self.chk_launch_rec.setChecked(True)
        self.chk_launch_rec.setStyleSheet("""
            QCheckBox {
                font-weight: 900;
                color: #00F0FF;
                font-size: 13px;
                background: transparent;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                background-color: #1E293B;
                border: 1.5px solid #00F0FF;
                border-radius: 4px;
            }
            QCheckBox::indicator:checked {
                background-color: #00F0FF;
            }
        """)
        c_lay.addWidget(self.chk_launch_rec)

        self.chk_launch_player = QCheckBox("🎬  Launch Recplay 2.0 Media Player now")
        self.chk_launch_player.setChecked(False)
        self.chk_launch_player.setStyleSheet("""
            QCheckBox {
                font-weight: 900;
                color: #38BDF8;
                font-size: 13px;
                background: transparent;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                background-color: #1E293B;
                border: 1.5px solid #38BDF8;
                border-radius: 4px;
            }
            QCheckBox::indicator:checked {
                background-color: #38BDF8;
            }
        """)
        c_lay.addWidget(self.chk_launch_player)

        note_lbl = QLabel("✅ All shortcuts are installed on your Desktop and Start Menu.")
        note_lbl.setStyleSheet("color: #34D399; font-size: 12px; font-weight: bold; margin-top: 4px; background: transparent;")
        c_lay.addWidget(note_lbl)

        layout.addWidget(card)
        layout.addStretch()

    def initializePage(self):
        wizard = self.wizard()
        install_rec = wizard.component_page.chk_recorder.isChecked()
        install_player = wizard.component_page.chk_player.isChecked()

        self.chk_launch_rec.setVisible(install_rec)
        self.chk_launch_rec.setChecked(install_rec)

        self.chk_launch_player.setVisible(install_player)
        self.chk_launch_player.setChecked(install_player and not install_rec)


class RecplaySetupWizard(QWizard):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Recplay 2.0 Setup Wizard")
        self.setFixedSize(660, 520)
        # CRITICAL: ClassicStyle forces full Qt stylesheet control and prevents Windows Aero white background override
        self.setWizardStyle(QWizard.WizardStyle.ClassicStyle)

        icon_path = Path(__file__).resolve().parent.parent / "assets" / "icon.ico"
        if not icon_path.exists():
            icon_path = Path(__file__).resolve().parent / "assets" / "icon.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self.setStyleSheet("""
            QWizard, QWizardPage {
                background-color: #060C18;
                color: #FFFFFF;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLabel {
                color: #FFFFFF;
            }
            QPushButton {
                background-color: #0284C7;
                color: #FFFFFF;
                border: 1.5px solid #00F0FF;
                border-radius: 6px;
                padding: 7px 22px;
                font-weight: bold;
                font-size: 13px;
                min-width: 85px;
            }
            QPushButton:hover {
                background-color: #00F0FF;
                color: #060C18;
                font-weight: 900;
            }
            QPushButton:disabled {
                background-color: #1E293B;
                color: #64748B;
                border: 1px solid #334155;
            }
            QCheckBox {
                color: #FFFFFF;
                font-size: 13px;
                font-weight: 600;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                background-color: #1E293B;
                border: 1.5px solid #0284C7;
                border-radius: 4px;
            }
            QCheckBox::indicator:checked {
                background-color: #00F0FF;
                border: 1.5px solid #00F0FF;
            }
        """)

        self.welcome_page = WelcomePage(self)
        self.dir_page = DirectoryPage(self)
        self.component_page = ComponentSelectionPage(self)
        self.install_page = InstallPage(self)
        self.finish_page = FinishedPage(self)

        self.addPage(self.welcome_page)
        self.addPage(self.dir_page)
        self.addPage(self.component_page)
        self.addPage(self.install_page)
        self.addPage(self.finish_page)

    def accept(self):
        super().accept()
        exe = self.install_page.installed_exe
        if not exe or not os.path.exists(exe):
            return
        no_win_flag = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        sinfo = None
        if sys.platform == "win32":
            sinfo = subprocess.STARTUPINFO()
            sinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            sinfo.wShowWindow = subprocess.SW_HIDE
        try:
            if self.finish_page.chk_launch_rec.isVisible() and self.finish_page.chk_launch_rec.isChecked():
                subprocess.Popen([exe], creationflags=no_win_flag, startupinfo=sinfo)
            if self.finish_page.chk_launch_player.isVisible() and self.finish_page.chk_launch_player.isChecked():
                subprocess.Popen([exe, "--player"], creationflags=no_win_flag, startupinfo=sinfo)
        except Exception as e:
            print(f"[!] Launch error: {e}")


def main():
    if sys.platform == "win32":
        try:
            kernel32 = ctypes.windll.kernel32
            hwnd = kernel32.GetConsoleWindow()
            if hwnd:
                user32 = ctypes.windll.user32
                user32.ShowWindow(hwnd, 0)  # SW_HIDE
                kernel32.FreeConsole()
        except Exception:
            pass

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    wizard = RecplaySetupWizard()
    wizard.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
