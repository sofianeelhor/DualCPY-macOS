#!/bin/zsh
set -euo pipefail

cd "${0:A:h}"

if [[ "$(uname -s)" != "Darwin" ]]; then
  print -u2 "DualCPY macOS can only be installed on macOS."
  exit 1
fi

if ! command -v brew >/dev/null 2>&1; then
  print -u2 "Homebrew is required: https://brew.sh"
  exit 1
fi

mac_major="$(sw_vers -productVersion | cut -d. -f1)"
if (( mac_major < 13 )); then
  print -u2 "DualCPY macOS requires macOS 13 or newer."
  exit 1
fi

print "Installing ADB, scrcpy, Python, and Tk with Homebrew…"
HOMEBREW_NO_INSTALL_CLEANUP=1 brew install android-platform-tools scrcpy python@3.14 python-tk@3.14

python_bin="$(brew --prefix python@3.14)/bin/python3.14"
"$python_bin" -m venv .venv
.venv/bin/python -m pip install --upgrade "pip==26.2.1"
.venv/bin/python -m pip install -r requirements.txt

mkdir -p config logs screenshots

print ""
print "Installation complete."
print "1. Enable USB debugging on the Thor and accept its RSA prompt."
print "2. Double-click run.command, or run: ./run.command"
print "3. Grant Accessibility for live layout controls and Screen Recording for screenshots when macOS asks."
