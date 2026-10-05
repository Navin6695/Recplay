"""
Hardware Identification (HWID) Module
Extracts stable, unique hardware identifiers from Windows systems
to bind licenses to a specific physical machine without opening any console window.
"""

import sys
import hashlib
import platform
import subprocess
import winreg
import uuid

_CACHED_HWID = None
_CREATE_NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0


def _get_registry_machine_guid() -> str:
    """Reads the machine GUID from Windows registry."""
    try:
        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Cryptography",
            0,
            winreg.KEY_READ | winreg.KEY_WOW64_64KEY,
        ) as key:
            val, _ = winreg.QueryValueEx(key, "MachineGuid")
            return str(val).strip()
    except Exception:
        return ""


def _get_wmi_value(command: str) -> str:
    """Executes a hidden PowerShell CIM query to get hardware IDs."""
    try:
        sinfo = None
        if sys.platform == "win32":
            sinfo = subprocess.STARTUPINFO()
            sinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            sinfo.wShowWindow = subprocess.SW_HIDE
        out = subprocess.check_output(
            ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", command],
            stderr=subprocess.DEVNULL,
            creationflags=_CREATE_NO_WINDOW,
            startupinfo=sinfo,
            timeout=2,
        ).decode("utf-8", errors="ignore").strip()
        return out
    except Exception:
        return ""


def get_hardware_id() -> str:
    """
    Computes a unique, tamper-resistant Hardware ID (HWID) for this computer.
    Format: VREC-XXXX-XXXX-XXXX
    Cached in memory so it only computes once per session.
    """
    global _CACHED_HWID
    if _CACHED_HWID:
        return _CACHED_HWID

    parts = []

    # 1. Computer System UUID
    uuid_str = _get_wmi_value("(Get-CimInstance -ClassName Win32_ComputerSystemProduct).UUID")
    if uuid_str:
        parts.append(uuid_str)

    # 2. CPU Processor ID
    cpu_id = _get_wmi_value("(Get-CimInstance -ClassName Win32_Processor | Select-Object -First 1).ProcessorId")
    if cpu_id:
        parts.append(cpu_id)

    # 3. Registry Machine GUID
    reg_guid = _get_registry_machine_guid()
    if reg_guid:
        parts.append(reg_guid)

    # 4. Fallback MAC Address if queries fail
    if not parts:
        mac = uuid.getnode()
        parts.append(str(mac))

    combined = "|".join(parts) + f"|{platform.machine()}"
    digest = hashlib.sha256(combined.encode("utf-8")).hexdigest().upper()

    _CACHED_HWID = f"VREC-{digest[0:4]}-{digest[4:8]}-{digest[8:12]}"
    return _CACHED_HWID


if __name__ == "__main__":
    print("Machine HWID:", get_hardware_id())
