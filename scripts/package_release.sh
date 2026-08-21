#!/bin/zsh
set -euo pipefail

project_dir="${0:A:h:h}"
cd "$project_dir"

app_path="dist/DualCPY macOS.app"
if [[ ! -d "$app_path" ]]; then
  print -u2 "Missing $app_path; run .venv/bin/python build.py first."
  exit 1
fi

if [[ -x .venv/bin/python ]]; then
  python_bin=.venv/bin/python
else
  python_bin="$(command -v python3)"
fi
version="$("$python_bin" -c 'import ast; tree=ast.parse(open("main.py").read()); print(next(n.value.value for n in tree.body if isinstance(n, ast.Assign) and any(getattr(t, "id", "") == "__version__" for t in n.targets)))')"
arch="$(uname -m)"
suffix="${1:-unsigned}"
release_dir="release"
archive="$release_dir/DualCPY-macOS-${version}-${arch}-${suffix}.zip"

mkdir -p "$release_dir"
ditto -c -k --sequesterRsrc --keepParent "$app_path" "$archive"
shasum -a 256 "$archive" > "$archive.sha256"
print "Created $archive"
print "Created $archive.sha256"
