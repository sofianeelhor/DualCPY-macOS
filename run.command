#!/bin/zsh
set -euo pipefail

cd "${0:A:h}"

if [[ ! -x .venv/bin/python ]]; then
  print -u2 "DualCPY is not installed yet. Double-click install.command first."
  exit 1
fi

export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
exec .venv/bin/python main.py
