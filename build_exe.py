"""
Recplay 2.0 - Standalone Windows .exe & Multi-PC Installer Package Builder
Builds:
1. Standalone Recplay.exe in dist/Recplay (bundled with PyQt6, OpenCV, ONNX models, sounddevice, FFmpeg).
2. Recplay_2.0_Windows_Package.zip (portable distribution package ready to copy to any PC).
3. Recplay_2.0_Setup.exe (Graphical Windows Setup Wizard with Control Panel uninstaller).
4. Cleans up any legacy Clipr / 1.0 builds from system.
"""

import os
import sys
import shutil
import zipfile
import subprocess
from pathlib import Path
import imageio_ffmpeg


def build():
    base_dir = Path(__file__).resolve().parent
    ffmpeg_bin = imageio_ffmpeg.get_ffmpeg_exe()

    print("==================================================")
    print("     Recplay 2.0 - Standalone Windows Package Builder")
    print("==================================================")
    print(f"[*] Base Directory: {base_dir}")
    print(f"[*] Bundling FFmpeg Binary: {ffmpeg_bin}")

    dist_dir = base_dir / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)

    # Clean legacy artifacts if any
    legacy_clipr_dist = dist_dir / "Clipr"
    if legacy_clipr_dist.exists():
        try:
            shutil.rmtree(legacy_clipr_dist)
            print("[*] Cleaned up legacy dist/Clipr folder.")
        except Exception:
            pass

    pyinst_path = Path(sys.executable).parent / "pyinstaller.exe"
    if not pyinst_path.exists():
        pyinst_path = base_dir.parent / ".venv" / "Scripts" / "pyinstaller.exe"

    # Step 1: Compile main Recplay application into dist/Recplay
    print("\n[*] Step 1: Running PyInstaller for Recplay 2.0...")
    pyinstaller_cmd = [
        str(pyinst_path),
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--noconsole",
        "--name", "Recplay",
        "--icon", str(base_dir / "assets" / "icon.ico"),
        "--add-data", f"{base_dir / 'assets'};assets",
        "--add-data", f"{base_dir / 'keys'};keys",
        "--add-data", f"{base_dir / 'licensing_admin'};licensing_admin",
        "--add-data", f"{base_dir / 'privacy_policy.html'};.",
        "--add-data", f"{base_dir / 'PRIVACY_POLICY.md'};.",
        "--add-binary", f"{ffmpeg_bin};imageio_ffmpeg/binaries",
        "--collect-all", "PyQt6",
        "--collect-all", "sounddevice",
        "--collect-all", "speech_recognition",
        "--hidden-import", "speech_recognition",
        "--hidden-import", "core.subtitle_generator",
        "--hidden-import", "mss",
        "--hidden-import", "pynput",
        "--hidden-import", "cryptography",
        "--hidden-import", "cv2",
        "--hidden-import", "numpy",
        "--hidden-import", "PIL",
        "--hidden-import", "ui.media_player",
        "--hidden-import", "ui.main_window",
        "--hidden-import", "ui.floating_facecam",
        "--hidden-import", "core.face_processor",
        "--hidden-import", "core.screen_recorder",
        "--hidden-import", "core.audio_recorder",
        "--hidden-import", "core.license_verifier",
        "--hidden-import", "licensing_admin.admin_keygen",
        "main.py",
    ]

    subprocess.run(pyinstaller_cmd, cwd=str(base_dir), check=True)
    recplay_dist = dist_dir / "Recplay"

    # Copy privacy policy files into application folder
    shutil.copy2(str(base_dir / "privacy_policy.html"), str(recplay_dist / "privacy_policy.html"))
    shutil.copy2(str(base_dir / "PRIVACY_POLICY.md"), str(recplay_dist / "PRIVACY_POLICY.md"))

    # Silent VBS launcher that runs Recplay.exe with zero console window
    vbs_silent = recplay_dist / "Run_Recplay_Silent.vbs"
    vbs_silent.write_text(
        'Set WshShell = CreateObject("WScript.Shell")\r\n'
        'Set fso = CreateObject("Scripting.FileSystemObject")\r\n'
        'scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)\r\n'
        'WshShell.CurrentDirectory = scriptDir\r\n'
        'WshShell.Run Chr(34) & scriptDir & "\\Recplay.exe" & Chr(34), 0, False\r\n',
        encoding="utf-8",
    )

    # Step 1B: Create Standalone Recplay_Keygen.exe
    print("\n[*] Step 1B: Generating Recplay_Keygen.exe (Standalone Keygen Executable)...")
    recplay_exe = recplay_dist / "Recplay.exe"
    keygen_exe = recplay_dist / "Recplay_Keygen.exe"
    keygen_space_exe = recplay_dist / "Recplay Keygen.exe"
    if recplay_exe.exists():
        shutil.copy2(str(recplay_exe), str(keygen_exe))
        shutil.copy2(str(recplay_exe), str(keygen_space_exe))
        shutil.copy2(str(recplay_exe), str(dist_dir / "Recplay_Keygen.exe"))
        shutil.copy2(str(recplay_exe), str(dist_dir / "Recplay Keygen.exe"))
        shutil.copy2(str(recplay_exe), str(base_dir.parent / "Recplay_Keygen.exe"))
        shutil.copy2(str(recplay_exe), str(base_dir.parent / "Recplay Keygen.exe"))
        print(f"[OK] Standalone Recplay_Keygen.exe created successfully: {keygen_exe}")

    # 1-Click Setup & Launcher scripts inside dist/Recplay for any target PC
    install_bat = recplay_dist / "Install_Recplay_Here.bat"
    install_bat.write_text(
        '@echo off\r\n'
        'title Recplay 2.0 - 1-Click Setup\r\n'
        'powershell -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -Command "$sh = New-Object -ComObject WScript.Shell; '
        '$d = [Environment]::GetFolderPath(\'Desktop\'); '
        '$sm = [Environment]::GetFolderPath(\'Programs\'); '
        '$exe = \'%~dp0Recplay.exe\'; '
        '$ico = \'%~dp0assets\\icon.ico\'; '
        '$s1 = $sh.CreateShortcut($d + \'\\Recplay 2.0.lnk\'); $s1.TargetPath = $exe; $s1.WorkingDirectory = \'%~dp0\'; if (Test-Path $ico) { $s1.IconLocation = $ico + \',0\' }; $s1.Save(); '
        '$s2 = $sh.CreateShortcut($d + \'\\Recplay Keygen.lnk\'); $s2.TargetPath = $exe; $s2.Arguments = \'--keygen\'; $s2.WorkingDirectory = \'%~dp0\'; if (Test-Path $ico) { $s2.IconLocation = $ico + \',0\' }; $s2.Save(); '
        '$s3 = $sh.CreateShortcut($sm + \'\\Recplay 2.0.lnk\'); $s3.TargetPath = $exe; $s3.WorkingDirectory = \'%~dp0\'; if (Test-Path $ico) { $s3.IconLocation = $ico + \',0\' }; $s3.Save(); '
        '$s4 = $sh.CreateShortcut($sm + \'\\Recplay Keygen.lnk\'); $s4.TargetPath = $exe; $s4.Arguments = \'--keygen\'; $s4.WorkingDirectory = \'%~dp0\'; if (Test-Path $ico) { $s4.IconLocation = $ico + \',0\' }; $s4.Save(); '
        'Write-Output \'[OK] Clean Desktop and Start Menu shortcuts created!\'"\r\n'
        'start "" "%~dp0Recplay.exe"\r\n'
        'exit\r\n',
        encoding="utf-8",
    )

    player_bat = recplay_dist / "Run_Player.bat"
    player_bat.write_text(
        '@echo off\r\nstart "" "%~dp0Recplay.exe" --player %*\r\nexit\r\n',
        encoding="utf-8",
    )

    keygen_bat = recplay_dist / "Run_Keygen.bat"
    keygen_bat.write_text(
        '@echo off\r\n'
        'if exist "%~dp0Recplay_Keygen.exe" (\r\n'
        '    start "" "%~dp0Recplay_Keygen.exe" %*\r\n'
        ') else (\r\n'
        '    start "" "%~dp0Recplay.exe" --keygen %*\r\n'
        ')\r\n'
        'exit\r\n',
        encoding="utf-8",
    )

    keygen_direct_bat = recplay_dist / "Recplay_Keygen.bat"
    keygen_direct_bat.write_text(
        '@echo off\r\n'
        'if exist "%~dp0Recplay_Keygen.exe" (\r\n'
        '    start "" "%~dp0Recplay_Keygen.exe" %*\r\n'
        ') else (\r\n'
        '    start "" "%~dp0Recplay.exe" --keygen %*\r\n'
        ')\r\n'
        'exit\r\n',
        encoding="utf-8",
    )

    keygen_vbs = recplay_dist / "Run_Recplay_Keygen.vbs"
    keygen_vbs.write_text(
        'Set WshShell = CreateObject("WScript.Shell")\r\n'
        'Set fso = CreateObject("Scripting.FileSystemObject")\r\n'
        'scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)\r\n'
        'WshShell.CurrentDirectory = scriptDir\r\n'
        'If fso.FileExists(scriptDir & "\\Recplay_Keygen.exe") Then\r\n'
        '    WshShell.Run Chr(34) & scriptDir & "\\Recplay_Keygen.exe" & Chr(34), 0, False\r\n'
        'Else\r\n'
        '    WshShell.Run Chr(34) & scriptDir & "\\Recplay.exe" & Chr(34) & " --keygen", 0, False\r\n'
        'End If\r\n',
        encoding="utf-8",
    )

    recplay_bat = recplay_dist / "Run_Recplay.bat"
    recplay_bat.write_text(
        '@echo off\r\nstart "" "%~dp0Recplay.exe" %*\r\nexit\r\n',
        encoding="utf-8",
    )

    # Step 2: Package dist/Recplay into a clean zip archive for distribution
    print("\n[*] Step 2: Creating distribution archive (Recplay_2.0_Windows_Package.zip)...")
    zip_output_base = str(base_dir.parent / "Recplay_2.0_Windows_Package")
    zip_path = shutil.make_archive(zip_output_base, "zip", str(dist_dir), "Recplay")
    print(f"[OK] Distribution zip package created: {zip_path}")

    # Copy zip to dist directory as well
    shutil.copy2(zip_path, str(dist_dir / "Recplay_2.0_Windows_Package.zip"))

    # Step 3: Compile Recplay_2.0_Setup.exe (Graphical Windows Setup Wizard)
    print("\n[*] Step 3: Compiling Recplay_2.0_Setup.exe (Windows Installer Wizard)...")
    setup_py = base_dir / "installer" / "setup_wizard.py"
    if setup_py.exists():
        setup_cmd = [
            str(pyinst_path),
            "--noconfirm",
            "--onefile",
            "--windowed",
            "--noconsole",
            "--name", "Recplay_2.0_Setup",
            "--icon", str(base_dir / "assets" / "icon.ico"),
            "--add-data", f"{base_dir / 'assets'};assets",
            "--add-data", f"{base_dir / 'privacy_policy.html'};.",
            "--add-data", f"{base_dir / 'PRIVACY_POLICY.md'};.",
            "--add-data", f"{zip_path};.",
            "--collect-all", "PyQt6",
            str(setup_py),
        ]
        try:
            subprocess.run(setup_cmd, cwd=str(base_dir), check=True)
            setup_exe = dist_dir / "Recplay_2.0_Setup.exe"
            if setup_exe.exists():
                print(f"[OK] Standalone installer wizard created: {setup_exe}")
                # Copy installer to D:\Clipr root and to User Desktop
                shutil.copy2(str(setup_exe), str(base_dir.parent / "Recplay_2.0_Setup.exe"))
        except Exception as e:
            print(f"[!] Note on installer wizard compilation: {e}")

    # Step 4: Copy distribution files to User Desktop and Project Root for instant access
    keygen_bat_path = recplay_dist / "Recplay_Keygen.bat"
    keygen_exe_src = dist_dir / "Recplay_Keygen.exe"
    if not keygen_exe_src.exists():
        keygen_exe_src = recplay_dist / "Recplay_Keygen.exe"

    if keygen_exe_src.exists():
        shutil.copy2(str(keygen_exe_src), str(base_dir.parent / "Recplay_Keygen.exe"))
        shutil.copy2(str(keygen_exe_src), str(base_dir.parent / "Recplay Keygen.exe"))
        print(f"[OK] Copied Recplay_Keygen.exe to {base_dir.parent}")

    if keygen_bat_path.exists():
        shutil.copy2(str(keygen_bat_path), str(base_dir.parent / "Recplay_Keygen.bat"))
        print(f"[OK] Copied Recplay_Keygen.bat to {base_dir.parent}")

    # Step 4: Ensure clean Desktop shortcuts (Recplay 2.0 and Recplay Keygen)
    print("\n[*] Step 4: Configuring clean Desktop and Start Menu shortcuts...")
    desktop = Path.home() / "Desktop"
    onedrive_desktop = Path.home() / "OneDrive" / "Desktop"
    installed_app_dir = Path.home() / "AppData" / "Local" / "Programs" / "Recplay"
    target_exe = installed_app_dir / "Recplay.exe" if installed_app_dir.exists() else (recplay_dist / "Recplay.exe")
    icon_ico = base_dir / "assets" / "icon.ico"

    venv_pythonw = base_dir.parent / ".venv" / "Scripts" / "pythonw.exe"
    main_py = base_dir / "main.py"
    if venv_pythonw.exists() and main_py.exists():
        target_app = str(venv_pythonw)
        app_args = f'"{main_py}"'
        app_workdir = str(base_dir)
        keygen_app = str(venv_pythonw)
        keygen_args = f'"{main_py}" --keygen'
        keygen_workdir = str(base_dir)
    else:
        target_app = str(target_exe)
        app_args = ""
        app_workdir = str(target_exe.parent)
        keygen_app = str(target_exe)
        keygen_args = "--keygen"
        keygen_workdir = str(target_exe.parent)

    for d in [desktop, onedrive_desktop]:
        if d.exists():
            try:
                # Remove loose/legacy clutter if present
                for loose in ["Recplay.lnk", "Recplay 2.0 Player.lnk", "Recplay Media Player.lnk", "Recplay Keygen.exe", "Recplay_Keygen.exe", "Recplay_Keygen.bat", "Recplay_2.0_Setup.exe", "Recplay_2.0_Windows_Package.zip", "Clipr 2.0.lnk", "Clipr 2.0 Player.lnk"]:
                    p = d / loose
                    if p.exists():
                        try:
                            p.unlink()
                        except Exception:
                            pass
                # Create clean shortcuts pointing to Recplay.exe and Recplay.exe --keygen
                ps_shortcuts = f"""
                $sh = New-Object -ComObject WScript.Shell
                $s1 = $sh.CreateShortcut('{d}\\Recplay 2.0.lnk')
                $s1.TargetPath = '{target_app}'
                $s1.Arguments = '{app_args}'
                $s1.WorkingDirectory = '{app_workdir}'
                if (Test-Path '{icon_ico}') {{ $s1.IconLocation = '{icon_ico},0' }}
                $s1.Description = 'Recplay 2.0 - Studio Video Recorder & Media Player'
                $s1.Save()

                $s2 = $sh.CreateShortcut('{d}\\Recplay Keygen.lnk')
                $s2.TargetPath = '{keygen_app}'
                $s2.Arguments = '{keygen_args}'
                $s2.WorkingDirectory = '{keygen_workdir}'
                if (Test-Path '{icon_ico}') {{ $s2.IconLocation = '{icon_ico},0' }}
                $s2.Description = 'Recplay 2.0 - License Key Generator'
                $s2.Save()
                """
                subprocess.run(["powershell", "-NoProfile", "-Command", ps_shortcuts], check=False)
                print(f"[OK] Clean desktop shortcuts configured for: {d}")
            except Exception as e:
                print(f"[!] Desktop shortcut notice: {e}")

    # Step 5: Clean up old legacy executables and packages from parent directory & Desktop
    legacy_files_to_clean = [
        base_dir.parent / "Clipr_2.0_Setup.exe",
        base_dir.parent / "Clipr_2.0_Windows_Package.zip",
        base_dir.parent / "Clipr.exe",
    ]
    for lf in legacy_files_to_clean:
        if lf.exists():
            try:
                lf.unlink()
                print(f"[*] Cleaned up legacy file: {lf.name}")
            except Exception:
                pass

    # Step 6: Update currently installed Recplay application so existing shortcuts work immediately
    installed_app_dir = Path.home() / "AppData" / "Local" / "Programs" / "Recplay"
    if installed_app_dir.exists():
        try:
            for item in recplay_dist.iterdir():
                dest_item = installed_app_dir / item.name
                if item.is_dir():
                    shutil.copytree(str(item), str(dest_item), dirs_exist_ok=True)
                else:
                    shutil.copy2(str(item), str(dest_item))
            print(f"[OK] Automatically updated installed Recplay application in {installed_app_dir}")
        except Exception as e:
            print(f"[!] Note on updating installed Recplay app: {e}")

    print("\n==================================================")
    print("      ALL PACKAGING COMPLETED SUCCESSFULLY!       ")
    print("==================================================")
    print(f"1. Standalone Application Folder: {recplay_dist}")
    print(f"2. Portable ZIP Package:         {base_dir.parent / 'Recplay_2.0_Windows_Package.zip'}")
    if (base_dir.parent / "Recplay_2.0_Setup.exe").exists():
        print(f"3. 1-Click Installer Setup:      {base_dir.parent / 'Recplay_2.0_Setup.exe'}")


if __name__ == "__main__":
    build()
