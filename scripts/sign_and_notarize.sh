#!/bin/zsh
set -euo pipefail

project_dir="${0:A:h:h}"
cd "$project_dir"

: "${MACOS_SIGNING_IDENTITY:?Set MACOS_SIGNING_IDENTITY to a Developer ID Application identity}"
: "${APPLE_ID:?Set APPLE_ID}"
: "${APPLE_TEAM_ID:?Set APPLE_TEAM_ID}"
: "${APPLE_APP_PASSWORD:?Set APPLE_APP_PASSWORD to an app-specific password}"

app_path="dist/DualCPY macOS.app"
submission_zip="$(mktemp /tmp/dualcpy-notary.XXXXXX.zip)"
trap 'rm -f "$submission_zip"' EXIT

codesign --force --deep --options runtime --timestamp \
  --sign "$MACOS_SIGNING_IDENTITY" "$app_path"
codesign --verify --deep --strict --verbose=2 "$app_path"

ditto -c -k --sequesterRsrc --keepParent "$app_path" "$submission_zip"
xcrun notarytool submit "$submission_zip" \
  --apple-id "$APPLE_ID" \
  --team-id "$APPLE_TEAM_ID" \
  --password "$APPLE_APP_PASSWORD" \
  --wait
xcrun stapler staple "$app_path"
xcrun stapler validate "$app_path"

scripts/package_release.sh signed-notarized
