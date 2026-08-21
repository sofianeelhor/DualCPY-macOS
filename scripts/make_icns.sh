#!/bin/zsh
set -euo pipefail

project_dir="${0:A:h:h}"
source_png="$project_dir/assets/icon.png"
output_icns="$project_dir/assets/icon.icns"
iconset_dir="$(mktemp -d /tmp/dualcpy-iconset.XXXXXX)/DualCPY.iconset"
mkdir -p "$iconset_dir"
trap 'rm -rf "${iconset_dir:h}"' EXIT

for size in 16 32 128 256 512; do
  sips -s format png -z "$size" "$size" "$source_png" \
    --out "$iconset_dir/icon_${size}x${size}.png" >/dev/null
  doubled=$((size * 2))
  sips -s format png -z "$doubled" "$doubled" "$source_png" \
    --out "$iconset_dir/icon_${size}x${size}@2x.png" >/dev/null
done

iconutil --convert icns --output "$output_icns" "$iconset_dir"
print "Created $output_icns"
