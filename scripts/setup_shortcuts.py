import os
import subprocess
from pathlib import Path

# Create script to configure Windows shortcuts via PowerShell com object
ps_script = r"""
$sh = New-Object -ComObject WScript.Shell
$pythonw = "D:\Clipr\.venv\Scripts\pythonw.exe"
$mainPy = "D:\Clipr\2.0\main.py"
$workDir = "D:\Clipr\2.0"
$iconPath = "D:\Clipr\2.0\assets\icon.ico"
$desktops = @("C:\Users\Sasi\Desktop", "C:\Users\Sasi\OneDrive\Desktop")

foreach ($d in $desktops) {
    if (Test-Path $d) {
        # 1. Main App Shortcut: Recplay 2.0.lnk
        $mainLnk = Join-Path $d "Recplay 2.0.lnk"
        $s1 = $sh.CreateShortcut($mainLnk)
        $s1.TargetPath = $pythonw
        $s1.Arguments = "`"$mainPy`""
        $s1.WorkingDirectory = $workDir
        $s1.IconLocation = "$iconPath,0"
        $s1.Description = "Recplay 2.0 - Studio Video Recorder & Media Player"
        $s1.Save()
        Write-Host "Created: $mainLnk"

        # 2. Keygen Shortcut: Recplay Keygen.lnk
        $keygenLnk = Join-Path $d "Recplay Keygen.lnk"
        $s2 = $sh.CreateShortcut($keygenLnk)
        $s2.TargetPath = $pythonw
        $s2.Arguments = "`"$mainPy`" --keygen"
        $s2.WorkingDirectory = $workDir
        $s2.IconLocation = "$iconPath,0"
        $s2.Description = "Recplay 2.0 - License Key Generator"
        $s2.Save()
        Write-Host "Created: $keygenLnk"
    }
}
"""

ps_file = Path("D:/Clipr/2.0/scripts/make_shortcuts.ps1")
ps_file.write_text(ps_script, encoding="utf-8")
res = subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", str(ps_file)], capture_output=True, text=True)
print("STDOUT:", res.stdout)
print("STDERR:", res.stderr)
