"""
Recplay Keygen - Standalone Seller License Key Generator (Admin Keygen)
Runs strictly as a separate desktop application for the seller.
Generates cryptographically signed License Keys (3 Months, 6 Months, 1 Year, Lifetime)
that unlock '💎 PRO' when activated in Recplay -> Manage License.
Features:
- Cryptographic expiration date embedding for Compact Recplay Keys, 20-Digit Keys, and Classic RSA Tokens.
- Full Key Generation Tracker & History Database (tracks total keys generated, batch counts, and validity breakdowns).
- Interactive Key History viewer dialog with search, filtering, and bulk export.
"""

import sys
import os
import json
import uuid
import base64
import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization

# Master Keypair (matches EMBEDDED_PUBLIC_KEY_PEM in core/license_verifier.py)
MASTER_PRIVATE_KEY_PEM = b"""-----BEGIN PRIVATE KEY-----
MIIEvwIBADANBgkqhkiG9w0BAQEFAASCBKkwggSlAgEAAoIBAQDM/uL0+5kOnZNE
JQ7sZle4jqH/tyoaDM7olC6eDl81RILrMaYq9/LHugXgNxV/l4nomJQxlpnWzCiz
WGiw9z+ip+rkLljl5J2s0GNpaLCWrhGUq9O02C15RT06rEwrcGJVqo1yzi9ngf0D
hjHMyxamthYf2ntg96jrcnzupOzUU1SCjy/5U3+zMidVFxaKgv9E1m982JtYRRSA
4TIEztwBIH+JLmouPQFOQolDn4WZwg0AMrucPCStTGmlocPZsmerrZjoeoPCYoAr
l1b0eveZfvfdT0GxD630I0dhOts31QLw6v/J9mw42QfATnm8fMcprTtAfzziBywX
jJ2ikuLrAgMBAAECggEAJnunAZSF3C+KqN1IGurvhs8H7GhnN/K1mQXQZo2OJALT
jPGKH0Diy8nJNplAqO46znZuQ4zhHmi/L0Pmi2ovAQsC1ok42Rd83idUskIb/H17
AWzsVmPKzZxI7U3REsqLO0fEPAwm7AiEBfhYOvjZLLy8FIjAZqi3hlO8zlQZvZX8
9KC1LbK2x2MPTUhsWLggizrj0Wua+XtZCk5XgRXUgTlnDeXazFihxRmh83ZYZWEv
E+RIoS219NdiSQGE66xsaLoljgaOgqyjWCB36Yy/f/JlM5e1V/a0Fb+JhRojvbYn
17vzaN/OGQSuPIe7aUklMEfSXTdhDVHOwv0caG7cmQKBgQD0NaSXoZByR0OZPSev
GdlDH43cbtbt3xpfDdb/vN5EiyWYFkb2aRarw2Q3T+v0/AiVPcXOepWvmHihdKxs
7g5HZPnSCkDOv9a1CXbxpDgTGot19y2I18bC/QLt0N4uiTAXYeDof++btHsBR4FO
pvaw+uyu+7EWv8j4tYfFM3cG/QKBgQDW5JJU9VJjay+mE/Id5uJDvlZud8kHvH6d
xvNFH8YG8tm1q4Y+b2l/7wzdzNN3ZxIe8xvJCnaN/238qSYoDpdefR/ORajKGrjH
pHiphYQP3bEghKCsLv3iJ3iXOa7pJzUg3veMUQ4jtfpe7AlTQ4oSaFPVeGS6+qtQ
2eVleswaBwKBgQDOYGbwHYFMkhz2a1AWEeohZ5EjMChCbcCDg9al2J6dnlnu5SSj
KLwX+8+9TrVBG5zFQqbfj4jgFCIdj9QHWkaG3zaf4jpSfpyb8ZurKfSZcF1bG8BH
XNKEBf1rrI+XFCioGfdPhI6hLyykMCF+rmrbtbI/TkShzQGx7PcIGC4GoQKBgQCH
JTjiNWabH83XpLOgGpQyBoJU9wB23RTEJVrZHiJsPE6u8jB7E5ZF3xE4bJiRf0Dm
Nf5DcVEd/IYvYDGe/44y3n4iO6zrbeLHq6g29MEZOVMsIDzsDKGemTQ95wkZmI7R
HWiR1mgODWRoTgmPU+qBqRsQJacz8HHNZzvdllzGAQKBgQDrGA4jakyU1kKTVrHE
WY2hXYxRduUMIF2+bmogKvcYyoD1F+K2VdwTVFZIaZDLUNKIEF99tS1ktmF/zypZ
TZO4TYXT5/8mn6tcvG5ckHgZvBQGBjg2htih2ffcw9nIMUP5a84y9AwzS/a7EQpF
KqWR6xFMxc3hfZHzCRX8Kdyjbw==
-----END PRIVATE KEY-----"""

MASTER_PUBLIC_KEY_PEM = b"""-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAzP7i9PuZDp2TRCUO7GZX
uI6h/7cqGgzO6JQung5fNUSC6zGmKvfyx7oF4DcVf5eJ6JiUMZaZ1swos1hosPc/
oqfq5C5Y5eSdrNBjaWiwlq4RlKvTtNgteUU9OqxMK3BiVaqNcs4vZ4H9A4YxzMsW
prYWH9p7YPeo63J87qTs1FNUgo8v+VN/szInVRcWioL/RNZvfNibWEUUgOEyBM7c
ASB/iS5qLj0BTkKJQ5+FmcINADK7nDwkrUxppaHD2bJnq62Y6HqDwmKAK5dW9Hr3
mX733U9BsQ+t9CNHYTrbN9UC8Or/yfZsONkHwE55vHzHKa07QH884gcsF4ydopLi
6wIDAQAB
-----END PUBLIC KEY-----"""

KEY_DIR = ROOT_DIR / "keys"
PRIVATE_KEY_PATH = KEY_DIR / "private_key.pem"
PUBLIC_KEY_PATH = KEY_DIR / "public_key.pem"
HISTORY_FILE = KEY_DIR / "generated_keys_history.json"
FALLBACK_HISTORY_FILE = Path(os.getenv("LOCALAPPDATA") or str(Path.home())) / "Recplay" / "keygen_history.json"


def ensure_keypair():
    """Ensures RSA-2048 master keypair is available and written to disk."""
    KEY_DIR.mkdir(parents=True, exist_ok=True)
    if not PRIVATE_KEY_PATH.exists():
        try:
            with open(PRIVATE_KEY_PATH, "wb") as f:
                f.write(MASTER_PRIVATE_KEY_PEM)
        except Exception:
            pass
    if not PUBLIC_KEY_PATH.exists():
        try:
            with open(PUBLIC_KEY_PATH, "wb") as f:
                f.write(MASTER_PUBLIC_KEY_PEM)
        except Exception:
            pass


def get_private_key_bytes() -> bytes:
    if PRIVATE_KEY_PATH.exists():
        try:
            return PRIVATE_KEY_PATH.read_bytes().strip()
        except Exception:
            pass
    return MASTER_PRIVATE_KEY_PEM.strip()


def get_public_key_bytes() -> bytes:
    if PUBLIC_KEY_PATH.exists():
        try:
            return PUBLIC_KEY_PATH.read_bytes().strip()
        except Exception:
            pass
    return MASTER_PUBLIC_KEY_PEM.strip()


def _update_embedded_public_key(public_pem: bytes):
    """Embeds the generated public key into core/license_verifier.py."""
    verifier_file = ROOT_DIR / "core" / "license_verifier.py"
    if verifier_file.exists():
        with open(verifier_file, "r", encoding="utf-8") as f:
            content = f.read()

        import re
        pattern = r"EMBEDDED_PUBLIC_KEY_PEM\s*=\s*b\"\"\"[\s\S]*?\"\"\""
        replacement = f'EMBEDDED_PUBLIC_KEY_PEM = b"""{public_pem.decode("utf-8").strip()}"""'
        updated = re.sub(pattern, replacement, content)

        with open(verifier_file, "w", encoding="utf-8") as f:
            f.write(updated)


def _get_history_file() -> Path:
    if KEY_DIR.exists():
        return HISTORY_FILE
    FALLBACK_HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    return FALLBACK_HISTORY_FILE


def load_keygen_history() -> dict:
    for hf in [HISTORY_FILE, FALLBACK_HISTORY_FILE]:
        if hf.exists():
            try:
                with open(hf, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        data.setdefault("total_generated", len(data.get("keys", [])))
                        data.setdefault("by_validity", {})
                        data.setdefault("keys", [])
                        return data
            except Exception:
                pass
    return {"total_generated": 0, "by_validity": {}, "keys": []}


def save_keygen_history(history: dict):
    for hf in [HISTORY_FILE, FALLBACK_HISTORY_FILE]:
        try:
            hf.parent.mkdir(parents=True, exist_ok=True)
            with open(hf, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2)
        except Exception:
            pass


def record_generated_batch(items: list[tuple[str, str]], validity_code: str, exp_date: str, tier: str = "PRO"):
    hist = load_keygen_history()
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for serial, key_token in items:
        hist["total_generated"] = hist.get("total_generated", 0) + 1
        by_val = hist.setdefault("by_validity", {})
        by_val[validity_code] = by_val.get(validity_code, 0) + 1
        hist.setdefault("keys", []).append({
            "serial": serial,
            "validity": validity_code,
            "expires": exp_date,
            "tier": tier,
            "created_at": now_str,
            "key": key_token,
        })
    save_keygen_history(hist)
    return hist


def generate_20digit_license_key(public_pem_norm: bytes, expiry_date_str: str = "LIFETIME") -> tuple[str, str]:
    """Generates a 20-digit cryptographically verified Product Key (XXXX-XXXX-XXXX-XXXX-XXXX) with embedded expiry."""
    import random
    import hashlib

    # 4 digits prefix (1000..9999)
    prefix_val = random.randint(1000, 9999)
    # 4 digits entropy (1000..9999)
    entropy_val = random.randint(1000, 9999)

    # 4 digits expiry
    exp_str = str(expiry_date_str).strip()
    if exp_str.upper() in ("LIFETIME", "PERMANENT", "LIFE", ""):
        exp_digits = "9999"
    else:
        try:
            exp_dt = datetime.datetime.strptime(exp_str, "%Y-%m-%d").date()
            epoch = datetime.date(2024, 1, 1)
            days = (exp_dt - epoch).days
            days = max(0, min(9998, days))
            exp_digits = f"{days:04d}"
        except Exception:
            exp_digits = "9999"

    payload = f"{prefix_val:04d}{entropy_val:04d}{exp_digits}"
    h = hashlib.sha256(b"RECPLAY_20DIGIT_EXP_V2::" + public_pem_norm + b"::" + payload.encode("utf-8")).digest()
    val = int.from_bytes(h[:6], "big") % 100000000
    sig = f"{val:08d}"
    key_id = f"{payload[:4]}-{payload[4:8]}-{payload[8:12]}"
    formatted_key = f"{payload[:4]}-{payload[4:8]}-{payload[8:12]}-{sig[:4]}-{sig[4:]}"
    return key_id, formatted_key


def generate_5block_compact_key(public_pem_norm: bytes, expiry_date_str: str = "LIFETIME") -> tuple[str, str]:
    """
    Generates a 5-block cryptographic key: RECPLAY-B1-B2-EXP-SIG1-SIG2
    where EXP encodes the exact expiration date or 'FFFF' for LIFETIME.
    """
    import hashlib

    raw_hex = uuid.uuid4().hex.upper()
    b1 = raw_hex[0:4]
    b2 = raw_hex[4:8]

    # Calculate expiration code
    exp_str = str(expiry_date_str).strip()
    if exp_str.upper() in ("LIFETIME", "PERMANENT", "LIFE", ""):
        exp_code = "FFFF"
    else:
        try:
            exp_dt = datetime.datetime.strptime(exp_str, "%Y-%m-%d").date()
            epoch = datetime.date(2024, 1, 1)
            days = (exp_dt - epoch).days
            days = max(0, min(0xFFFE, days))
            exp_code = f"{days:04X}"
        except Exception:
            exp_code = "FFFF"

    serial_prefix = f"RECPLAY-{b1}-{b2}-{exp_code}"
    expected_hash = hashlib.sha256(
        b"RECPLAY_EXP_V2::" + public_pem_norm + b"::" + serial_prefix.encode("utf-8")
    ).hexdigest().upper()
    expected_sig = f"{expected_hash[0:4]}-{expected_hash[4:8]}"
    full_key = f"{serial_prefix}-{expected_sig}"
    return serial_prefix, full_key


def generate_compact_license_key(public_pem_norm: bytes, index_num: int = 1, expiry_date_str: str = "LIFETIME") -> tuple[str, str]:
    """Generates a 20-digit cryptographically signed Product Key (XXXX-XXXX-XXXX-XXXX-XXXX)."""
    return generate_20digit_license_key(public_pem_norm, expiry_date_str=expiry_date_str)


class KeyResult(str):
    """String subclass that also behaves as a (key_id, license_key) 2-tuple."""
    def __new__(cls, key_id: str, license_key: str):
        obj = super().__new__(cls, license_key)
        obj.key_id = key_id
        obj.license_key = license_key
        return obj

    def __iter__(self):
        return iter((self.key_id, self.license_key))

    def __getitem__(self, item):
        if item in (0, 1):
            return (self.key_id, self.license_key)[item]
        return super().__getitem__(item)


def generate_license_key(
    customer_name: str = "PRO",
    hwid: str = "AUTO_ONLINE_BIND",
    tier: str = "PRO",
    expiry_date_str: str = "LIFETIME",
    index_num: int = 1,
    use_compact: bool = False,
    use_5block: bool = False,
) -> KeyResult:
    """Signs license details using Seller's Keypair (supports Compact 20-digit, 5-block RECPLAY, and RSA-2048 formats)."""
    ensure_keypair()

    # Handle case where hwid is omitted in keyword call
    if isinstance(hwid, int) and tier == "PRO":
        index_num = hwid
        hwid = "AUTO_ONLINE_BIND"

    try:
        idx_val = int(index_num)
    except (ValueError, TypeError):
        idx_val = 1

    if use_5block and hwid in ("AUTO_ONLINE_BIND", "ANY", ""):
        pub_norm = b"".join(get_public_key_bytes().splitlines())
        kid, full_key = generate_5block_compact_key(pub_norm, expiry_date_str=expiry_date_str)
        return KeyResult(kid, full_key)

    if use_compact and hwid in ("AUTO_ONLINE_BIND", "ANY", ""):
        pub_norm = b"".join(get_public_key_bytes().splitlines())
        kid, full_key = generate_20digit_license_key(pub_norm, expiry_date_str=expiry_date_str)
        return KeyResult(kid, full_key)

    private_key = serialization.load_pem_private_key(get_private_key_bytes(), password=None)

    raw_hex = uuid.uuid4().hex.upper()
    key_id = f"RECPLAY-{raw_hex[0:4]}-{raw_hex[4:8]}-{raw_hex[8:12]}"

    user_label = str(customer_name).strip() or "PRO"
    if idx_val > 1 and "#" not in user_label:
        user_label = f"{user_label} #{idx_val}"

    payload = {
        "key_id": key_id,
        "user": user_label,
        "hwid": str(hwid).strip(),
        "tier": str(tier).strip(),
        "expires": str(expiry_date_str).strip(),
        "issued_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    payload_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")

    signature = private_key.sign(
        payload_bytes,
        padding.PKCS1v15(),
        hashes.SHA256(),
    )

    payload_b64 = base64.urlsafe_b64encode(payload_bytes).decode("utf-8")
    signature_b64 = base64.urlsafe_b64encode(signature).decode("utf-8")

    license_key = f"{payload_b64}.{signature_b64}"
    return KeyResult(key_id, license_key)


def generate_bulk_license_keys(
    count: int = 5,
    customer_name: str = "PRO",
    tier: str = "PRO",
    expiry_date_str: str = "LIFETIME",
    format_type: str = "clipr_compact",
) -> list[tuple[str, str]]:
    """High-speed bulk generator producing unique signed license keys in Classic or Compact format."""
    ensure_keypair()
    pub_norm = b"".join(get_public_key_bytes().splitlines())

    results = []
    if format_type == "clipr_compact":
        for _ in range(max(1, count)):
            results.append(generate_5block_compact_key(pub_norm, expiry_date_str=expiry_date_str))
        return results
    elif format_type == "compact":
        for _ in range(max(1, count)):
            results.append(generate_20digit_license_key(pub_norm, expiry_date_str=expiry_date_str))
        return results

    # Classic RSA-2048 token
    for i in range(1, max(1, count) + 1):
        key_id, token = generate_license_key(
            customer_name=customer_name,
            tier=tier,
            expiry_date_str=expiry_date_str,
            index_num=i if count > 1 else 1,
            use_compact=False,
        )
        results.append((key_id, token))
    return results


def show_history_dialog(parent_widget=None):
    """Opens the Key Generation Statistics & History dialog."""
    from PyQt6.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
        QPushButton, QListWidget, QListWidgetItem, QComboBox, QMessageBox, QFileDialog, QFrame, QApplication
    )

    dlg = QDialog(parent_widget)
    dlg.setWindowTitle("Recplay Keygen - Generated Keys History & Statistics")
    dlg.resize(880, 560)
    dlg.setStyleSheet("""
        QDialog {
            background-color: #060C18;
            color: #FFFFFF;
            font-family: 'Segoe UI', Arial, sans-serif;
        }
        QLabel {
            color: #FFFFFF;
            font-size: 13px;
            font-weight: bold;
        }
        QLineEdit, QComboBox {
            background-color: #0F172A;
            border: 1.5px solid #0284C7;
            border-radius: 6px;
            padding: 7px 12px;
            color: #FFFFFF;
            font-size: 13px;
            font-weight: bold;
        }
        QListWidget {
            background-color: #0F172A;
            border: 1.5px solid #0284C7;
            border-radius: 8px;
            font-family: Consolas, monospace;
            font-size: 12px;
            color: #FFFFFF;
            padding: 4px;
        }
        QListWidget::item {
            padding: 6px 10px;
            border-radius: 4px;
            color: #FFFFFF;
        }
        QListWidget::item:selected {
            background-color: #0284C7;
            color: #FFFFFF;
            font-weight: 900;
        }
        QPushButton {
            background-color: #0F172A;
            color: #FFFFFF;
            border: 1.5px solid #0284C7;
            border-radius: 6px;
            padding: 8px 16px;
            font-weight: bold;
            font-size: 12px;
        }
        QPushButton:hover {
            background-color: #0284C7;
            border-color: #00F0FF;
        }
    """)

    lay = QVBoxLayout(dlg)
    lay.setContentsMargins(20, 16, 20, 16)
    lay.setSpacing(12)

    # Title & Stats Summary
    hist = load_keygen_history()
    all_keys = hist.get("keys", [])
    total_count = len(all_keys)

    header_lbl = QLabel(f"📜 Generated Keys History ({total_count:,} Total Keys Created)")
    header_lbl.setStyleSheet("font-size: 18px; font-weight: 900; color: #00F0FF;")
    lay.addWidget(header_lbl)

    # Summary Badges Frame
    stat_frame = QFrame()
    stat_frame.setStyleSheet("background-color: #0F172A; border: 1.5px solid #0284C7; border-radius: 8px;")
    stat_lay = QHBoxLayout(stat_frame)
    stat_lay.setContentsMargins(14, 8, 14, 8)

    by_val = hist.get("by_validity", {})
    cnt_life = by_val.get("LIFETIME", 0)
    cnt_1y = by_val.get("1YEAR", 0)
    cnt_6m = by_val.get("6MONTHS", 0)
    cnt_3m = by_val.get("3MONTHS", 0)

    stats_str = (
        f"<b>All-Time Created:</b> <font color='#00F0FF'>{total_count:,}</font>   |   "
        f"<b>Lifetime:</b> <font color='#34D399'>{cnt_life:,}</font>   |   "
        f"<b>1 Year:</b> <font color='#38BDF8'>{cnt_1y:,}</font>   |   "
        f"<b>6 Months:</b> <font color='#FBBF24'>{cnt_6m:,}</font>   |   "
        f"<b>3 Months:</b> <font color='#F472B6'>{cnt_3m:,}</font>"
    )
    lbl_summary = QLabel(stats_str)
    lbl_summary.setStyleSheet("font-size: 13px;")
    stat_lay.addWidget(lbl_summary)
    lay.addWidget(stat_frame)

    # Filter / Search Row
    filter_row = QHBoxLayout()
    filter_row.setSpacing(10)
    search_edit = QLineEdit()
    search_edit.setPlaceholderText("🔍 Search by serial, date, or key content...")

    combo_filter = QComboBox()
    combo_filter.addItems(["All Validities", "LIFETIME", "1YEAR", "6MONTHS", "3MONTHS"])

    filter_row.addWidget(search_edit, 2)
    filter_row.addWidget(combo_filter, 1)
    lay.addLayout(filter_row)

    # History List Widget
    history_list = QListWidget()
    lay.addWidget(history_list)

    filtered_items: list[dict] = []

    def refresh_display():
        nonlocal filtered_items
        history_list.clear()
        query = search_edit.text().strip().lower()
        val_filter = combo_filter.currentText()

        filtered_items = []
        # Show newest keys first
        for item in reversed(all_keys):
            v_code = item.get("validity", "LIFETIME")
            if val_filter != "All Validities" and v_code != val_filter:
                continue
            serial = item.get("serial", "")
            key_str = item.get("key", "")
            exp = item.get("expires", "")
            created = item.get("created_at", "")
            searchable = f"{serial} {key_str} {exp} {created} {v_code}".lower()
            if query and query not in searchable:
                continue

            filtered_items.append(item)
            list_text = f"Key: {key_str}   •   {v_code} (Exp: {exp})   •   {created}"
            history_list.addItem(QListWidgetItem(list_text))

        header_lbl.setText(f"📜 Generated Keys History ({len(filtered_items):,} shown of {total_count:,} total)")

    search_edit.textChanged.connect(refresh_display)
    combo_filter.currentIndexChanged.connect(refresh_display)
    refresh_display()

    # Action Buttons
    btn_row = QHBoxLayout()
    btn_row.setSpacing(10)

    btn_copy = QPushButton("📋 Copy Selected Key")
    btn_copy.setStyleSheet("background-color: #059669; color: #FFFFFF; border: 1.5px solid #34D399; font-weight: 900;")

    btn_export = QPushButton("💾 Export Filtered (.txt)")
    btn_export.setStyleSheet("background-color: #0284C7; color: #FFFFFF; border: 1.5px solid #00F0FF; font-weight: 900;")

    btn_clear = QPushButton("🗑️ Clear History")
    btn_clear.setStyleSheet("background-color: #DC2626; color: #FFFFFF; border: 1.5px solid #FCA5A5;")

    btn_close = QPushButton("✕ Close")

    btn_row.addWidget(btn_copy, 2)
    btn_row.addWidget(btn_export, 2)
    btn_row.addWidget(btn_clear, 1)
    btn_row.addWidget(btn_close, 1)
    lay.addLayout(btn_row)

    def on_copy():
        idx = history_list.currentRow()
        if 0 <= idx < len(filtered_items):
            item = filtered_items[idx]
            QApplication.clipboard().setText(item.get("key", ""))
            QMessageBox.information(dlg, "Copied", f"Copied License Key ({item.get('serial')}) to clipboard!")
        elif filtered_items:
            QApplication.clipboard().setText(filtered_items[0].get("key", ""))
            QMessageBox.information(dlg, "Copied", "Copied first License Key to clipboard!")

    def on_export():
        if not filtered_items:
            QMessageBox.warning(dlg, "No Keys", "No keys to export.")
            return
        path, _ = QFileDialog.getSaveFileName(dlg, "Export Keys History", "Recplay_Generated_Keys_History.txt", "Text Files (*.txt);;CSV Files (*.csv)")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                if path.lower().endswith(".csv"):
                    f.write("Index,Created_At,Validity,Expires,Serial,License_Key\n")
                    for i, itm in enumerate(filtered_items, 1):
                        f.write(f'{i},"{itm.get("created_at")}","{itm.get("validity")}","{itm.get("expires")}","{itm.get("serial")}","{itm.get("key")}"\n')
                else:
                    f.write(f"=== RECPLAY KEYGEN - GENERATED KEYS HISTORY ({len(filtered_items)} Keys) ===\n\n")
                    for i, itm in enumerate(filtered_items, 1):
                        f.write(f"--- Key #{i} | {itm.get('validity')} | Created: {itm.get('created_at')} | Expires: {itm.get('expires')} ---\n")
                        f.write(f"Serial: {itm.get('serial')}\nKey: {itm.get('key')}\n\n")
            QMessageBox.information(dlg, "Exported", f"Successfully exported {len(filtered_items)} keys to:\n{path}")

    def on_clear():
        reply = QMessageBox.question(
            dlg, "Clear Key History",
            "Are you sure you want to clear your generated keys history?\n\n(Existing keys will still remain valid for customers.)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            save_keygen_history({"total_generated": 0, "by_validity": {}, "keys": []})
            all_keys.clear()
            refresh_display()
            QMessageBox.information(dlg, "History Cleared", "Generated keys history has been cleared.")

    btn_copy.clicked.connect(on_copy)
    btn_export.clicked.connect(on_export)
    btn_clear.clicked.connect(on_clear)
    btn_close.clicked.connect(dlg.accept)

    dlg.exec()


def create_keygen_window():
    from PyQt6.QtWidgets import (
        QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
        QLineEdit, QPushButton, QTextEdit, QMessageBox,
        QFileDialog, QSpinBox, QListWidget, QListWidgetItem, QFrame
    )
    from PyQt6.QtGui import QIcon

    ensure_keypair()

    win = QWidget()
    win.setWindowTitle("Recplay Keygen")
    win.setMinimumSize(960, 750)
    win.resize(1000, 780)

    ico_path = ROOT_DIR / "assets" / "icon.ico"
    png_path = ROOT_DIR / "assets" / "icon.png"
    if ico_path.exists():
        win.setWindowIcon(QIcon(str(ico_path)))
    elif png_path.exists():
        win.setWindowIcon(QIcon(str(png_path)))

    win.setStyleSheet("""
        QWidget {
            background-color: #060C18;
            color: #FFFFFF;
            font-family: 'Segoe UI', Arial, sans-serif;
        }
        QLabel {
            font-size: 13px;
            font-weight: bold;
            color: #FFFFFF;
            border: none;
            background: transparent;
        }
        QLineEdit, QSpinBox {
            background-color: #0F172A;
            border: 1.5px solid #0284C7;
            border-radius: 6px;
            padding: 7px 12px;
            font-size: 13px;
            font-weight: bold;
            color: #FFFFFF;
        }
        QLineEdit:focus, QSpinBox:focus {
            border: 1.5px solid #00F0FF;
            background-color: #132038;
        }
        QListWidget {
            background-color: #0F172A;
            border: 1.5px solid #0284C7;
            border-radius: 8px;
            font-family: Consolas, monospace;
            font-size: 12px;
            font-weight: bold;
            color: #FFFFFF;
            padding: 4px;
        }
        QListWidget::item {
            padding: 6px 10px;
            border-radius: 4px;
            color: #FFFFFF;
        }
        QListWidget::item:selected {
            background-color: #0284C7;
            color: #FFFFFF;
            font-weight: 900;
        }
        QTextEdit {
            background-color: #0F172A;
            border: 1.5px solid #0284C7;
            border-radius: 8px;
            font-family: Consolas, monospace;
            font-size: 13px;
            font-weight: bold;
            color: #00F0FF;
            padding: 8px;
        }
        QPushButton {
            background-color: #0F172A;
            color: #FFFFFF;
            font-size: 13px;
            font-weight: bold;
            border: 1.5px solid #0284C7;
            border-radius: 6px;
            padding: 8px 14px;
        }
        QPushButton:hover {
            background-color: #0284C7;
            border: 1.5px solid #00F0FF;
            color: #FFFFFF;
        }
        QPushButton#genBtn {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #DC2626, stop:1 #EF4444);
            color: #FFFFFF;
            font-size: 15px;
            font-weight: 900;
            border: 1.5px solid #FCA5A5;
            border-radius: 8px;
            padding: 11px 20px;
        }
        QPushButton#genBtn:hover {
            background: #B91C1C;
            border: 1.5px solid #FFFFFF;
        }
        QPushButton#copyOneBtn {
            background-color: #059669;
            color: #FFFFFF;
            font-size: 13px;
            font-weight: 900;
            border: 1.5px solid #34D399;
            border-radius: 8px;
            padding: 10px 16px;
        }
        QPushButton#copyOneBtn:hover {
            background-color: #047857;
            border: 1.5px solid #FFFFFF;
        }
        QPushButton#copyAllBtn {
            background-color: #0284C7;
            color: #FFFFFF;
            font-size: 13px;
            font-weight: 900;
            border: 1.5px solid #00F0FF;
            border-radius: 8px;
            padding: 10px 16px;
        }
        QPushButton#copyAllBtn:hover {
            background-color: #00F0FF;
            color: #060C18;
        }
        QPushButton#saveBtn {
            background-color: #4338CA;
            color: #FFFFFF;
            font-size: 13px;
            font-weight: 900;
            border: 1.5px solid #818CF8;
            border-radius: 8px;
            padding: 10px 16px;
        }
        QPushButton#saveBtn:hover {
            background-color: #3730A3;
            border: 1.5px solid #FFFFFF;
        }
        QPushButton#histBtn {
            background-color: #0F172A;
            color: #00F0FF;
            font-size: 12px;
            font-weight: bold;
            border: 1.5px solid #0284C7;
            border-radius: 6px;
            padding: 5px 12px;
        }
        QPushButton#histBtn:hover {
            background-color: #0284C7;
            color: #FFFFFF;
        }
    """)

    layout = QVBoxLayout()
    layout.setContentsMargins(24, 18, 24, 18)
    layout.setSpacing(10)

    # Branded Header with History Button
    top_bar = QHBoxLayout()
    header = QLabel("🔑 Recplay Keygen")
    header.setStyleSheet("font-size: 20px; font-weight: 900; color: #00F0FF; letter-spacing: 0.5px;")
    top_bar.addWidget(header)
    top_bar.addStretch()

    hist = load_keygen_history()
    all_time_total = hist.get("total_generated", 0)

    btn_view_history = QPushButton(f"📜 View All Keys History ({all_time_total:,})")
    btn_view_history.setObjectName("histBtn")
    btn_view_history.clicked.connect(lambda: (show_history_dialog(win), update_stats_banner()))
    top_bar.addWidget(btn_view_history)
    layout.addLayout(top_bar)

    # Instructions Card
    info_box = QFrame()
    info_box.setStyleSheet("QFrame { background-color: #0F172A; border-left: 4px solid #10B981; border: 1.5px solid #0284C7; border-radius: 8px; }")
    info_lay = QVBoxLayout(info_box)
    info_lay.setContentsMargins(14, 8, 14, 8)
    info_lay.setSpacing(3)
    info_lbl = QLabel(
        "1️⃣  Choose validity (3 Months, 6 Months, 1 Year, or Lifetime) and number of keys, then click 'Generate'.\n"
        "2️⃣  Copy selected key and paste into Recplay -> '🛡️ Manage License' -> '🚀 Activate License'.\n"
        "3️⃣  The exact validity period is cryptographically embedded and unlocks 💎 PRO until the expiration date!"
    )
    info_lbl.setWordWrap(True)
    info_lbl.setStyleSheet("color: #34D399; font-size: 12px; font-weight: bold; border: none; background: transparent; line-height: 1.4;")
    info_lay.addWidget(info_lbl)
    layout.addWidget(info_box)

    # Stats Banner (Tracks how many keys generated)
    stats_box = QFrame()
    stats_box.setStyleSheet("QFrame { background-color: #0F172A; border: 1.5px solid #0284C7; border-radius: 8px; }")
    stats_box_lay = QHBoxLayout(stats_box)
    stats_box_lay.setContentsMargins(14, 8, 14, 8)

    lbl_stats_live = QLabel()
    lbl_stats_live.setStyleSheet("font-size: 12px; font-weight: bold; color: #FFFFFF;")
    stats_box_lay.addWidget(lbl_stats_live, 1)

    def update_stats_banner(current_batch_count: int = 0):
        h = load_keygen_history()
        total_g = h.get("total_generated", 0)
        bv = h.get("by_validity", {})
        lbl_stats_live.setText(
            f"📊 <b>Total Keys Generated All-Time:</b> <font color='#00F0FF'>{total_g:,}</font>   |   "
            f"<b>Current Batch:</b> <font color='#34D399'>{current_batch_count:,}</font>   |   "
            f"<b>Lifetime:</b> {bv.get('LIFETIME', 0):,}   |   "
            f"<b>1 Year:</b> {bv.get('1YEAR', 0):,}   |   "
            f"<b>6 Mos:</b> {bv.get('6MONTHS', 0):,}   |   "
            f"<b>3 Mos:</b> {bv.get('3MONTHS', 0):,}"
        )
        btn_view_history.setText(f"📜 View All Keys History ({total_g:,})")

    update_stats_banner(0)
    layout.addWidget(stats_box)

    # Row 1: Batch Label + Number of Keys
    row1 = QHBoxLayout()
    row1.setSpacing(12)

    col_name = QVBoxLayout()
    col_name.addWidget(QLabel("License Tier Label:"))
    name_input = QLineEdit("PRO")
    col_name.addWidget(name_input)
    row1.addLayout(col_name, 2)

    col_qty = QVBoxLayout()
    col_qty.addWidget(QLabel("🔢 Number of Keys to Create (Supports up to 5,00,000+ / 5 Lakhs+):"))
    qty_row = QHBoxLayout()
    qty_spin = QSpinBox()
    qty_spin.setRange(1, 600000)
    qty_spin.setValue(5)
    qty_spin.setStyleSheet("font-size: 15px; font-weight: bold; color: #00F0FF; min-width: 110px;")
    qty_row.addWidget(qty_spin)

    for preset_lbl, preset_n in [("5", 5), ("100", 100), ("10K", 10000), ("1 Lakh", 100000), ("5 Lakhs", 500000)]:
        btn_n = QPushButton(preset_lbl)
        btn_n.setMinimumWidth(74)
        btn_n.clicked.connect(lambda checked=False, n=preset_n: qty_spin.setValue(n))
        qty_row.addWidget(btn_n)

    col_qty.addLayout(qty_row)
    row1.addLayout(col_qty, 3)
    layout.addLayout(row1)

    # Row 2: 1-Click Validity Selector Buttons (3 Months, 6 Months, 1 Year, Lifetime)
    selected_validity = ["LIFETIME"]
    val_row = QHBoxLayout()
    val_row.addWidget(QLabel("License Validity:"))
    val_btns = {}
    for label_txt, code_val in [
        ("♾️ LIFETIME PRO", "LIFETIME"),
        ("📅 1 Year (365 Days)", "1YEAR"),
        ("📅 6 Months (180 Days)", "6MONTHS"),
        ("📅 3 Months (90 Days)", "3MONTHS"),
    ]:
        b = QPushButton(label_txt)
        val_btns[code_val] = b
        val_row.addWidget(b, 1)

    def select_val(code_v):
        selected_validity[0] = code_v
        for k, btn_w in val_btns.items():
            if k == code_v:
                btn_w.setStyleSheet("background-color: #059669; color: #FFFFFF; border: 2px solid #34D399; font-weight: 900;")
            else:
                btn_w.setStyleSheet("background-color: #0F172A; color: #FFFFFF; border: 1.5px solid #0284C7; font-weight: bold;")

    for code_v, btn_w in val_btns.items():
        btn_w.clicked.connect(lambda checked=False, c=code_v: select_val(c))
    select_val("LIFETIME")
    layout.addLayout(val_row)

    # Row 3: Key Format Selector
    selected_format = ["clipr_compact"]
    fmt_row = QHBoxLayout()
    fmt_row.addWidget(QLabel("License Format:"))
    fmt_btns = {}
    for label_txt, code_fmt in [
        ("🏷️ Compact Recplay Key (RECPLAY-XXXX...)", "clipr_compact"),
        ("🔢 20-Digit Product Key", "compact"),
        ("🔑 Classic Token (RSA-2048)", "classic"),
    ]:
        b = QPushButton(label_txt)
        fmt_btns[code_fmt] = b
        fmt_row.addWidget(b, 1)

    def select_fmt(code_f):
        selected_format[0] = code_f
        for k, btn_w in fmt_btns.items():
            if k == code_f:
                btn_w.setStyleSheet("background-color: #0284C7; color: #FFFFFF; border: 2px solid #00F0FF; font-weight: 900;")
            else:
                btn_w.setStyleSheet("background-color: #0F172A; color: #FFFFFF; border: 1.5px solid #0284C7; font-weight: bold;")

    for code_f, btn_w in fmt_btns.items():
        btn_w.clicked.connect(lambda checked=False, c=code_f: select_fmt(c))
    select_fmt("clipr_compact")
    layout.addLayout(fmt_row)

    # Generate Button
    gen_btn = QPushButton("🔑 Generate 5 License Keys Now")
    gen_btn.setObjectName("genBtn")
    qty_spin.valueChanged.connect(lambda v: gen_btn.setText(f"🔑 Generate {v:,} License Key{'s' if v > 1 else ''} Now"))
    layout.addWidget(gen_btn)

    lbl_list = QLabel("Generated License Keys (Select any key below and click '📋 Copy Selected Key' or '💾 Export Keys'):")
    lbl_list.setStyleSheet("color: #FFFFFF; font-weight: bold; font-size: 13px;")
    layout.addWidget(lbl_list)

    key_list = QListWidget()
    key_list.setFixedHeight(125)
    layout.addWidget(key_list)

    key_output = QTextEdit()
    key_output.setReadOnly(True)
    key_output.setFixedHeight(80)
    layout.addWidget(key_output)

    generated_items: list[tuple[str, str]] = []

    def on_list_row_changed(idx: int):
        if 0 <= idx < len(generated_items):
            serial, token = generated_items[idx]
            key_output.setPlainText(token)

    key_list.currentRowChanged.connect(on_list_row_changed)

    def on_generate():
        nonlocal generated_items
        name = name_input.text().strip() or "PRO"
        count = qty_spin.value()

        v_code = selected_validity[0]
        if v_code == "LIFETIME":
            exp_date = "LIFETIME"
            val_label = "LIFETIME"
        elif v_code == "1YEAR":
            exp_date = (datetime.date.today() + datetime.timedelta(days=365)).strftime("%Y-%m-%d")
            val_label = f"1 Year (Expires {exp_date})"
        elif v_code == "6MONTHS":
            exp_date = (datetime.date.today() + datetime.timedelta(days=180)).strftime("%Y-%m-%d")
            val_label = f"6 Months (Expires {exp_date})"
        elif v_code == "3MONTHS":
            exp_date = (datetime.date.today() + datetime.timedelta(days=90)).strftime("%Y-%m-%d")
            val_label = f"3 Months (Expires {exp_date})"
        else:
            exp_date = (datetime.date.today() + datetime.timedelta(days=90)).strftime("%Y-%m-%d")
            val_label = f"Expires {exp_date}"

        f_code = selected_format[0]
        generated_items = generate_bulk_license_keys(
            count=count,
            customer_name=name,
            tier="PRO",
            expiry_date_str=exp_date,
            format_type=f_code,
        )

        # Record generated keys in persistent history tracker
        record_generated_batch(generated_items, validity_code=v_code, exp_date=exp_date, tier="PRO")
        update_stats_banner(current_batch_count=len(generated_items))

        key_list.clear()
        preview_limit = min(200, len(generated_items))
        for idx in range(preview_limit):
            serial, token = generated_items[idx]
            item = QListWidgetItem(f"Key #{idx + 1:02d}:   {token}   [{val_label}]")
            key_list.addItem(item)

        if generated_items:
            key_list.setCurrentRow(0)
            key_output.setPlainText(generated_items[0][1])

        extra_note = f" (Showing first {preview_limit} in preview — click '💾 Export Keys' to save all {len(generated_items):,})" if len(generated_items) > preview_limit else ""
        lbl_list.setText(f"✅ Generated {len(generated_items):,} Unique PRO License Key(s) for {val_label}!{extra_note}")

    def on_copy_selected():
        idx = key_list.currentRow()
        if 0 <= idx < len(generated_items):
            serial, token = generated_items[idx]
        elif generated_items:
            serial, token = generated_items[0]
        else:
            return
        QApplication.clipboard().setText(token)
        QMessageBox.information(
            win,
            "License Key Copied!",
            f"Copied License Key:\n\n{token}\n\nNow open Recplay -> '🛡️ Manage License', click '📋 Paste from Clipboard' (or paste the key), and click '🚀 Activate License' to unlock 💎 PRO!"
        )

    def on_copy_all():
        if not generated_items:
            return
        lines = [token for _, token in generated_items]
        QApplication.clipboard().setText("\n\n".join(lines))
        QMessageBox.information(win, "All Keys Copied!", f"Copied all {len(generated_items)} license keys to clipboard!")

    def on_save():
        if not generated_items:
            return
        default_name = f"Recplay_{len(generated_items)}_License_Keys.txt"
        file_path, _ = QFileDialog.getSaveFileName(
            win,
            "Save Generated License Keys",
            default_name,
            "Text Files (*.txt);;License Files (*.lic)",
        )
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"=== RECPLAY 2.0 - GENERATED PRO LICENSE KEYS ({len(generated_items)} KEYS) ===\n")
                f.write(f"Generated At: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                for idx, (serial, token) in enumerate(generated_items, start=1):
                    f.write(f"=== KEY #{idx} | SERIAL: {serial} ===\n{token}\n\n")
            QMessageBox.information(win, "Saved", f"Saved {len(generated_items)} license key(s) to:\n{file_path}")

    b_row = QHBoxLayout()
    b_row.setSpacing(12)
    copy_one_btn = QPushButton("📋 Copy Selected Key (Paste in Recplay)")
    copy_one_btn.setObjectName("copyOneBtn")
    copy_all_btn = QPushButton("📋 Copy All Keys")
    copy_all_btn.setObjectName("copyAllBtn")
    save_btn = QPushButton("💾 Export Keys (.txt)")
    save_btn.setObjectName("saveBtn")

    b_row.addWidget(copy_one_btn, 2)
    b_row.addWidget(copy_all_btn, 1)
    b_row.addWidget(save_btn, 1)
    layout.addLayout(b_row)

    gen_btn.clicked.connect(on_generate)
    copy_one_btn.clicked.connect(on_copy_selected)
    copy_all_btn.clicked.connect(on_copy_all)
    save_btn.clicked.connect(on_save)

    on_generate()
    win.setLayout(layout)
    return win


def launch_admin_gui():
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance()
    owns_app = False
    if app is None:
        app = QApplication(sys.argv)
        app.setStyle("Fusion")
        owns_app = True

    win = create_keygen_window()
    win.show()
    win.raise_()
    win.activateWindow()
    if owns_app:
        sys.exit(app.exec())
    return win


if __name__ == "__main__":
    ensure_keypair()
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        count = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 5
        keys = generate_bulk_license_keys(count=count)
        for idx, (serial, tok) in enumerate(keys, start=1):
            print(f"--- KEY #{idx} ({serial}) ---")
            print(tok)
    else:
        launch_admin_gui()
