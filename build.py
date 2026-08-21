# DualCPY for macOS application bundle build
# Copyright (C) 2026 the_swest
# Contact: Github issues
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

# build.py

import os
import plistlib
import re
import subprocess
from pathlib import Path

import PyInstaller.__main__

ROOT = Path(__file__).resolve().parent
MAIN = ROOT / "main.py"
ICON = ROOT / "assets" / "icon.icns"


def app_version():
    match = re.search(r'^__version__\s*=\s*"([^"]+)"', MAIN.read_text(), re.MULTILINE)
    if not match:
        raise RuntimeError("Could not read __version__ from main.py")
    return match.group(1)


if not ICON.exists():
    subprocess.run([str(ROOT / "scripts" / "make_icns.sh")], check=True)

version = app_version()

PyInstaller.__main__.run(
    [
        "main.py",
        "--windowed",
        "--clean",
        "--name=DualCPY macOS",
        f"--add-data=config{os.pathsep}config",
        f"--add-data=bin{os.pathsep}bin",
        f"--add-data=logs{os.pathsep}logs",
        f"--add-data=assets/fonts{os.pathsep}assets/fonts",
        f"--add-data=assets/icons{os.pathsep}assets/icons",
        f"--add-data=assets/icon.png{os.pathsep}assets",
        f"--icon={ICON}",
        "--osx-bundle-identifier=io.dualcpy.macos",
        "-y",
    ]
)

# PyInstaller does not expose bundle-version flags. Update the generated plist,
# then restore the ad-hoc signature invalidated by that metadata edit.
app_path = ROOT / "dist" / "DualCPY macOS.app"
plist_path = app_path / "Contents" / "Info.plist"
with plist_path.open("rb") as plist_file:
    plist = plistlib.load(plist_file)
plist["CFBundleShortVersionString"] = version
plist["CFBundleVersion"] = version
with plist_path.open("wb") as plist_file:
    plistlib.dump(plist, plist_file)
subprocess.run(
    ["codesign", "--force", "--deep", "--sign", "-", str(app_path)],
    check=True,
)
