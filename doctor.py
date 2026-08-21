#!/usr/bin/env python3
"""Read-only setup and device diagnostic for DualCPY on macOS."""

import platform
import shutil
import subprocess


def command_output(command, timeout=15):
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
        return result.returncode, (result.stdout + result.stderr).strip()
    except Exception as exc:
        return 1, str(exc)


def main():
    print(f"macOS: {platform.mac_ver()[0] or 'not macOS'}")
    print(f"Python: {platform.python_version()}")

    missing = []
    binaries = {}
    for name in ("adb", "scrcpy"):
        path = shutil.which(name)
        binaries[name] = path
        print(f"{name}: {path or 'MISSING'}")
        if not path:
            missing.append(name)

    for module in ("tkinter", "customtkinter", "Quartz", "ApplicationServices", "mss", "PIL"):
        try:
            __import__(module)
            print(f"Python module {module}: OK")
        except Exception as exc:
            print(f"Python module {module}: MISSING ({exc})")
            missing.append(module)

    if binaries.get("scrcpy"):
        _, version = command_output([binaries["scrcpy"], "--version"])
        print(version.splitlines()[0] if version else "scrcpy version unavailable")

    authorized = []
    if binaries.get("adb"):
        _, devices = command_output([binaries["adb"], "devices", "-l"])
        print("\nADB devices:")
        print(devices or "none")
        for line in devices.splitlines()[1:]:
            parts = line.split()
            if len(parts) >= 2 and parts[1] == "device":
                authorized.append(parts[0])

    for serial in authorized:
        _, displays = command_output(
            [binaries["scrcpy"], "-s", serial, "--list-displays"], timeout=30
        )
        print(f"\nDisplays for {serial}:")
        print(displays or "No displays reported")

    if missing:
        print("\nResult: INCOMPLETE — run ./install.command")
        return 1
    if not authorized:
        print("\nResult: SOFTWARE OK — connect and authorize the Thor")
        return 2
    print("\nResult: READY")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
