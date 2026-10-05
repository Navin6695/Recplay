import os
import sys
from pathlib import Path

desktops = [
    Path(r"C:\Users\Sasi\Desktop"),
    Path(r"C:\Users\Sasi\OneDrive\Desktop"),
]

files_to_remove = [
    "Clipr 2.0 Player.lnk",
    "Clipr 2.0.lnk",
    "Clipr_2.0_Keygen_Tool.zip",
    "Clipr_2.0_Setup.exe",
    "Clipr_2.0_Windows_Package.zip",
    "Clipr_PRO_License_Keys_For_Others.txt",
    "Clipr_5_License_Keys.txt",
    "Clipr_Board_20260928_131700.png",
    "Clipr_Shot_20260923_232658.png",
    "Recplay 2.0 Player.lnk",
    "Recplay Media Player.lnk",
    "Recplay.lnk",
    "Recplay Keygen.exe",
    "Recplay_Keygen.exe",
    "Recplay_2.0_Setup.exe",
    "Recplay_2.0_Windows_Package.zip",
    "Recplay_Keygen.bat",
]

for d in desktops:
    if not d.exists():
        continue
    for fname in files_to_remove:
        target = d / fname
        if target.exists():
            try:
                if target.is_dir():
                    import shutil
                    shutil.rmtree(target)
                else:
                    target.unlink()
                print(f"[REMOVED] {target}")
            except Exception as e:
                print(f"[ERROR REMOVING] {target}: {e}")

print("[DONE] Desktop cleanup completed.")
