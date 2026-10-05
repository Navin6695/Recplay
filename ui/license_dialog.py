"""
Recplay 2.0 - Customer License Activation Dialog
Clean, high-contrast, professional customer-facing activation window.
- Shows '⚠️ TRIAL MODE (Unlicensed)' when unlicensed.
- Activates and switches to '💎 PRO ACTIVATED' when a valid License Key is entered.
- Displays the customer's Machine Hardware ID with a 1-click Copy button.
"""

from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QTextEdit, QMessageBox, QFrame, QApplication, QWidget
)
from PyQt6.QtCore import Qt, pyqtSignal, QUrl
from PyQt6.QtGui import QDesktopServices, QPixmap, QIcon

from core.hwid import get_hardware_id
from core.license_verifier import LicenseVerifier


class LicenseDialog(QDialog):
    license_changed = pyqtSignal(bool)

    def __init__(self, verifier: LicenseVerifier, parent=None):
        super().__init__(parent)
        self.verifier = verifier
        self.setWindowTitle("Recplay 2.0 - License Manager")
        self.setFixedSize(620, 580)

        icon_path = Path(__file__).resolve().parent.parent / "assets" / "icon.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self.setStyleSheet("""
            QDialog {
                background-color: #060C18;
                color: #FFFFFF;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLabel {
                color: #FFFFFF;
                font-size: 13px;
                font-weight: bold;
                border: none;
                background: transparent;
            }
            QLineEdit, QTextEdit {
                background-color: #0F172A;
                border: 1.5px solid #0284C7;
                border-radius: 8px;
                padding: 10px 12px;
                color: #FFFFFF;
                font-size: 13px;
                font-weight: bold;
                selection-background-color: #0284C7;
                selection-color: #FFFFFF;
            }
            QLineEdit:focus, QTextEdit:focus {
                border: 1.5px solid #00F0FF;
                background-color: #132038;
            }
            QLineEdit:disabled, QTextEdit:disabled {
                background-color: #0B132B;
                color: #64748B;
                border: 1px solid #1E293B;
            }
            QLineEdit:read-only, QTextEdit:read-only {
                background-color: #0F172A;
                color: #00F0FF;
                border: 1.5px solid #0284C7;
            }
            QToolTip {
                background-color: #0F172A;
                color: #00F0FF;
                border: 1.5px solid #0284C7;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 12px;
                font-weight: bold;
            }
            QMessageBox {
                background-color: #060C18;
                border: 2px solid #00F0FF;
            }
            QMessageBox QLabel {
                color: #FFFFFF;
                font-size: 13px;
                font-weight: bold;
                background: transparent;
            }
            QPushButton {
                background-color: #0284C7;
                color: #FFFFFF;
                font-weight: 900;
                font-size: 13px;
                border: 1.5px solid #00F0FF;
                border-radius: 8px;
                padding: 10px 18px;
                min-height: 40px;
            }
            QPushButton:hover {
                background-color: #00F0FF;
                color: #060C18;
            }
            QPushButton:disabled {
                background-color: #1E293B;
                color: #64748B;
                border: 1px solid #334155;
            }
            QPushButton#copyBtn {
                background-color: #0F172A;
                color: #FFFFFF;
                border: 1.5px solid #0284C7;
                min-height: 38px;
                padding: 8px 16px;
            }
            QPushButton#copyBtn:hover {
                background-color: #0284C7;
                border: 1.5px solid #00F0FF;
                color: #FFFFFF;
            }
            QPushButton#deactivateBtn {
                background-color: #DC2626;
                color: #FFFFFF;
                border: 1.5px solid #FCA5A5;
            }
            QPushButton#deactivateBtn:hover {
                background-color: #B91C1C;
                border: 1.5px solid #FFFFFF;
            }
            QPushButton#deactivateBtn:disabled {
                background-color: #1E293B;
                color: #475569;
                border: 1px solid #334155;
            }
        """)

        self._init_ui()
        self.refresh_status()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        # Branded Header
        header_widget = QWidget()
        h_lay = QHBoxLayout(header_widget)
        h_lay.setContentsMargins(0, 0, 0, 0)
        h_lay.setSpacing(12)

        icon_lbl = QLabel()
        png_path = Path(__file__).resolve().parent.parent / "assets" / "icon.png"
        if png_path.exists():
            pix = QPixmap(str(png_path)).scaled(
                40, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
            icon_lbl.setPixmap(pix)
        h_lay.addWidget(icon_lbl)

        col = QVBoxLayout()
        col.setSpacing(2)
        title = QLabel("Recplay 2.0 - License Manager")
        title.setStyleSheet("font-size: 19px; font-weight: 900; color: #00F0FF; border: none;")
        subtitle = QLabel("Activate your lifetime license or manage your workstation binding")
        subtitle.setStyleSheet("font-size: 12px; font-weight: bold; color: #38BDF8; border: none;")
        col.addWidget(title)
        col.addWidget(subtitle)
        h_lay.addLayout(col, 1)
        layout.addWidget(header_widget)

        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet("background-color: #0284C7; max-height: 2px;")
        layout.addWidget(div)

        # Status Banner Frame
        self.status_banner = QFrame()
        b_layout = QVBoxLayout(self.status_banner)
        b_layout.setContentsMargins(14, 12, 14, 12)
        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("border: none; background: transparent; font-size: 13px; font-weight: bold;")
        b_layout.addWidget(self.status_label)
        layout.addWidget(self.status_banner)

        # Machine Hardware ID Section
        hw_title = QLabel("Your Machine Hardware ID (HWID):")
        hw_title.setStyleSheet("font-weight: bold; color: #FFFFFF; font-size: 13px; border: none;")
        layout.addWidget(hw_title)

        hw_row = QHBoxLayout()
        hw_row.setSpacing(10)
        self.hwid_display = QLineEdit(get_hardware_id())
        self.hwid_display.setReadOnly(True)
        self.hwid_display.setStyleSheet(
            "font-family: Consolas, monospace; font-size: 14px; font-weight: bold; color: #00F0FF; "
            "background-color: #0F172A; border: 1.5px solid #0284C7; border-radius: 8px; padding: 10px;"
        )
        copy_btn = QPushButton("📋 Copy ID")
        copy_btn.setObjectName("copyBtn")
        copy_btn.clicked.connect(self._copy_hwid)
        hw_row.addWidget(self.hwid_display, 1)
        hw_row.addWidget(copy_btn)
        layout.addLayout(hw_row)

        hw_hint = QLabel("💡 Send this HWID to the seller to purchase or receive your activation key.")
        hw_hint.setStyleSheet("font-size: 12px; font-weight: bold; color: #38BDF8; border: none;")
        layout.addWidget(hw_hint)

        # License Key Input Section
        key_header_row = QHBoxLayout()
        key_title = QLabel("Enter License Key:")
        key_title.setStyleSheet("font-weight: bold; color: #FFFFFF; font-size: 13px; margin-top: 4px; border: none;")
        key_header_row.addWidget(key_title)
        key_header_row.addStretch()

        paste_btn = QPushButton("📋 Paste from Clipboard")
        paste_btn.setStyleSheet("""
            QPushButton {
                background-color: #0F172A;
                color: #38BDF8;
                border: 1px solid #0284C7;
                border-radius: 4px;
                font-size: 11px;
                font-weight: bold;
                padding: 3px 10px;
            }
            QPushButton:hover {
                background-color: #0284C7;
                color: #FFFFFF;
            }
        """)
        paste_btn.clicked.connect(self._paste_clipboard)
        key_header_row.addWidget(paste_btn)
        layout.addLayout(key_header_row)

        self.key_input = QTextEdit()
        self.key_input.setPlaceholderText("Paste your license key string here (e.g. RECPLAY-XXXX-XXXX...)...")
        self.key_input.setFixedHeight(85)
        layout.addWidget(self.key_input)

        # Action Buttons (Activate & Deactivate)
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        self.activate_btn = QPushButton("🚀 Activate License")
        self.activate_btn.clicked.connect(self._activate_license)

        self.deactivate_btn = QPushButton("🗑️ Deactivate")
        self.deactivate_btn.setObjectName("deactivateBtn")
        self.deactivate_btn.clicked.connect(self._deactivate_license)

        self.privacy_btn = QPushButton("🛡️ Privacy Policy")
        self.privacy_btn.setStyleSheet("""
            QPushButton {
                background-color: #0F172A;
                color: #00F0FF;
                border: 1.5px solid #0284C7;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0284C7;
                color: #FFFFFF;
            }
        """)
        self.privacy_btn.clicked.connect(self._open_privacy_policy)

        btn_row.addWidget(self.activate_btn, 2)
        btn_row.addWidget(self.deactivate_btn, 1)
        btn_row.addWidget(self.privacy_btn, 1)
        layout.addLayout(btn_row)

        layout.addStretch()

    def _copy_hwid(self):
        QApplication.clipboard().setText(self.hwid_display.text())
        QMessageBox.information(
            self,
            "Hardware ID Copied",
            "Copied Hardware ID to clipboard!\n\nProvide this ID to the seller to receive your activation key."
        )

    def _paste_clipboard(self):
        cb = QApplication.clipboard().text().strip()
        if cb:
            self.key_input.setPlainText(cb)

    def refresh_status(self):
        lic = self.verifier.get_active_license()
        if lic.get("valid"):
            user = lic.get("user", "Valued Customer")
            tier = lic.get("tier", "PRO")
            exp = lic.get("expires", "LIFETIME")

            import datetime
            if exp != "LIFETIME":
                try:
                    exp_dt = datetime.datetime.strptime(exp, "%Y-%m-%d").date()
                    days_rem = (exp_dt - datetime.date.today()).days
                    if days_rem > 0:
                        validity_str = f"{exp} ({days_rem} days remaining)"
                    elif days_rem == 0:
                        validity_str = f"{exp} (Expires today)"
                    else:
                        validity_str = f"{exp} (Expired)"
                except Exception:
                    validity_str = exp
            else:
                validity_str = "LIFETIME (Permanent)"

            self.status_banner.setStyleSheet(
                "QFrame { background-color: #064E3B; border: 1.5px solid #10B981; border-radius: 8px; }"
            )
            self.status_label.setStyleSheet("color: #6EE7B7; font-size: 13px; font-weight: bold; border: none; background: transparent;")
            self.status_label.setText(
                f"💎 PRO ACTIVATED\n"
                f"Licensed to: {user}\n"
                f"Tier: {tier}   •   Status: Active   •   Validity: {validity_str}"
            )
            self.activate_btn.setText("🔄 Update / Renew License")
            self.activate_btn.setEnabled(True)
            self.deactivate_btn.setEnabled(True)
            self.key_input.setEnabled(True)
            self.key_input.setPlaceholderText("Enter a new key here to change or renew your license...")
        else:
            self.status_banner.setStyleSheet(
                "QFrame { background-color: #451A03; border: 1.5px solid #F59E0B; border-radius: 8px; }"
            )
            self.status_label.setStyleSheet("color: #FEF08A; font-size: 13px; font-weight: bold; border: none; background: transparent;")
            self.status_label.setText(
                "⚠️ TRIAL MODE (Unlicensed)\n"
                "Watermark enabled and 5-minute recording limit active.\n"
                "Enter a license key below to unlock PRO."
            )
            self.activate_btn.setText("🚀 Activate License")
            self.activate_btn.setEnabled(True)
            self.deactivate_btn.setEnabled(False)
            self.key_input.setEnabled(True)
            self.key_input.setPlaceholderText("Paste your license key string here (e.g. RECPLAY-XXXX-XXXX...)...")

    def _activate_license(self):
        key = self.key_input.toPlainText().strip()
        if not key:
            QMessageBox.warning(self, "Missing Key", "Please paste your license key into the text box.")
            return

        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            res = self.verifier.save_license(key)
        finally:
            QApplication.restoreOverrideCursor()

        if res.get("valid"):
            self.key_input.clear()
            self.refresh_status()
            self.license_changed.emit(True)
            exp_str = res.get("expires", "LIFETIME")
            QMessageBox.information(
                self,
                "Success!",
                f"Recplay 2.0 activated successfully!\n\nValidity: {exp_str}\nAll watermarks and time limits are now removed."
            )
        else:
            err = res.get("error", "Invalid or corrupted license key.")
            QMessageBox.critical(
                self,
                "Activation Failed",
                f"Could not activate license:\n\n{err}"
            )

    def _deactivate_license(self):
        reply = QMessageBox.question(
            self,
            "Deactivate License",
            "Are you sure you want to deactivate the license on this machine?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.verifier.remove_license()
            self.refresh_status()
            self.license_changed.emit(False)
            QMessageBox.information(
                self,
                "Deactivated",
                "License removed. Recplay is now in Trial mode."
            )

    def _open_privacy_policy(self):
        policy_html = Path(__file__).resolve().parent.parent / "privacy_policy.html"
        if policy_html.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(policy_html)))
        else:
            QDesktopServices.openUrl(QUrl("https://recplay.github.io/privacy"))
