"""
Recplay Studio - Main Entry Point
Launches the Studio Screen Recorder with Red & Black theme, custom Windows Taskbar AppUserModelID,
crash-proof exception & window-lifecycle guards (`setQuitOnLastWindowClosed(False)`),
and ultra-low CPU hardware-friendly Qt GUI.
"""

import sys
import os
import ctypes
import tempfile
import traceback
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Under pythonw.exe on Windows, sys.stdout / sys.stderr can be None or invalid console handles,
# which causes print() or Qt slot exceptions to terminate the process. Redirect safely to a log file.
try:
    _log_path = os.path.join(tempfile.gettempdir(), "recplay_studio_runtime.log")
    if sys.stdout is None or not hasattr(sys.stdout, "write"):
        sys.stdout = open(_log_path, "a", encoding="utf-8", buffering=1)
    if sys.stderr is None or not hasattr(sys.stderr, "write"):
        sys.stderr = open(_log_path, "a", encoding="utf-8", buffering=1)
except Exception:
    pass


def _global_exception_guard(exc_type, exc_value, exc_tb):
    """Prevents PyQt6 from calling abort()/qFatal() on non-fatal UI slot exceptions."""
    try:
        err_text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        if sys.stderr and hasattr(sys.stderr, "write"):
            sys.stderr.write(f"[Recplay Guarded Exception]\n{err_text}\n")
            sys.stderr.flush()
    except Exception:
        pass


sys.excepthook = _global_exception_guard

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon, QPalette, QColor

from ui.main_window import MainWindow


def _set_windows_app_id():
    """Ensures Windows Taskbar & Explorer display the Recplay Poster Icon instead of a generic file icon."""
    if sys.platform == "win32":
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Recplay.Studio.2.0")
        except Exception:
            pass


def _close_stale_instance_if_any():
    """Closes any stale/hidden previous Recplay 2.0 window so a fresh launch NEVER exits early or stays invisible."""
    if sys.platform != "win32":
        return
    try:
        user32 = ctypes.windll.user32
        hwnd = user32.FindWindowW(None, "Recplay 2.0 - Studio Suite & Media Player")
        if hwnd:
            WM_CLOSE = 0x0010
            user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)
    except Exception:
        pass


def main():
    # 1. Silently detach and hide any console window so CMD NEVER shows to user
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

    _close_stale_instance_if_any()
    _set_windows_app_id()

    app = QApplication(sys.argv)
    # CRITICAL FIX: Prevent Qt from ever auto-closing the application when any dropdown,
    # drag-out overlay, annotator board, or modal dialog is opened/closed!
    app.setQuitOnLastWindowClosed(False)

    app.setApplicationName("Recplay 2.0")
    app.setOrganizationName("Recplay 2.0")
    app.setStyle("Fusion")

    # Global Dark Palette ensuring NO widget or subdialog can ever inherit Windows white palette
    dark_palette = QPalette()
    dark_palette.setColor(QPalette.ColorRole.Window, QColor(6, 12, 24))
    dark_palette.setColor(QPalette.ColorRole.WindowText, QColor(248, 250, 252))
    dark_palette.setColor(QPalette.ColorRole.Base, QColor(15, 23, 42))
    dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(30, 41, 59))
    dark_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(15, 23, 42))
    dark_palette.setColor(QPalette.ColorRole.ToolTipText, QColor(0, 240, 255))
    dark_palette.setColor(QPalette.ColorRole.Text, QColor(248, 250, 252))
    dark_palette.setColor(QPalette.ColorRole.Button, QColor(15, 23, 42))
    dark_palette.setColor(QPalette.ColorRole.ButtonText, QColor(248, 250, 252))
    dark_palette.setColor(QPalette.ColorRole.BrightText, QColor(0, 240, 255))
    dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(2, 132, 199))
    dark_palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(100, 116, 139))
    dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(100, 116, 139))
    dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor(100, 116, 139))
    dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Base, QColor(11, 19, 43))
    app.setPalette(dark_palette)

    app.setStyleSheet("""
        QToolTip {
            background-color: #0F172A;
            color: #00F0FF;
            border: 1px solid #0284C7;
            border-radius: 6px;
            padding: 5px 8px;
            font-size: 12px;
            font-family: 'Segoe UI', Arial, sans-serif;
        }
        QMenu {
            background-color: #0F172A;
            color: #F8FAFC;
            border: 1px solid #0284C7;
            border-radius: 8px;
            padding: 4px;
        }
        QMenu::item:selected {
            background-color: #0284C7;
            color: #FFFFFF;
        }
        QLineEdit, QTextEdit {
            background-color: #0F172A;
            color: #F8FAFC;
            border: 1px solid #0284C7;
            border-radius: 6px;
            selection-background-color: #0284C7;
            selection-color: #FFFFFF;
        }
        QLineEdit:disabled, QTextEdit:disabled {
            background-color: #091122;
            color: #64748B;
            border: 1px solid #1E293B;
        }
        QLineEdit:read-only, QTextEdit:read-only {
            background-color: #0F172A;
            color: #38BDF8;
            border: 1px solid #0284C7;
        }
        QDialog, QMessageBox {
            background-color: #060C18;
            color: #F8FAFC;
        }
        QMessageBox QLabel {
            color: #F8FAFC;
            font-size: 13px;
            background: transparent;
        }
    """)

    ico_path = BASE_DIR / "assets" / "icon.ico"
    png_path = BASE_DIR / "assets" / "icon.png"

    if ico_path.exists():
        app.setWindowIcon(QIcon(str(ico_path)))
    elif png_path.exists():
        app.setWindowIcon(QIcon(str(png_path)))

    exe_name = Path(sys.executable).stem.lower()
    is_keygen_exe = "keygen" in exe_name or any("keygen" in str(arg).lower() for arg in sys.argv)
    is_player_exe = "player" in exe_name or "--player" in sys.argv

    # Mode A: Direct launch of License Keygen Tool
    if is_keygen_exe:
        from licensing_admin.admin_keygen import create_keygen_window, ensure_keypair
        ensure_keypair()
        win = create_keygen_window()
        if ico_path.exists():
            win.setWindowIcon(QIcon(str(ico_path)))
        win.show()
        win.raise_()
        win.activateWindow()
        sys.exit(app.exec())

    # Mode B: Direct launch of Studio Media Player
    elif is_player_exe or (len(sys.argv) > 1 and any(sys.argv[1].lower().endswith(ext) for ext in (".mp4", ".mkv", ".avi", ".mov", ".webm", ".wmv", ".mp3", ".wav", ".aac", ".m4a", ".flac", ".ogg"))):
        from ui.media_player import StudioMediaPlayer
        player = StudioMediaPlayer()
        if ico_path.exists():
            player.setWindowIcon(QIcon(str(ico_path)))
        media_file = sys.argv[1] if (len(sys.argv) > 1 and sys.argv[1] != "--player" and os.path.exists(sys.argv[1])) else None
        if media_file:
            player.play_file(media_file)
        player.showNormal()
        player.raise_()
        player.activateWindow()
        sys.exit(app.exec())

    # Mode C: Standard Recplay 2.0 Studio Video Recorder
    else:
        window = MainWindow()
        if ico_path.exists():
            window.setWindowIcon(QIcon(str(ico_path)))
        window.showNormal()
        window.raise_()
        window.activateWindow()
        sys.exit(app.exec())


if __name__ == "__main__":
    main()
