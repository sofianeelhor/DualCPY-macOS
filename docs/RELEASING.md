# Releasing

## Versioning

DualCPY macOS uses semantic versioning. Update `__version__` in `main.py` and
add a dated entry to `CHANGELOG.md` before creating a tag.

## Local unsigned build

```zsh
make package
```

This creates an ad-hoc-signed application archive and SHA-256 file in
`release/`. It is suitable for testing, but Gatekeeper may warn other users.

## Signed and notarized build

An Apple Developer Program membership and a `Developer ID Application`
certificate are required for a frictionless public download.

```zsh
export MACOS_SIGNING_IDENTITY="Developer ID Application: Example (TEAMID)"
export APPLE_ID="developer@example.com"
export APPLE_TEAM_ID="TEAMID"
export APPLE_APP_PASSWORD="app-specific-password"
./scripts/sign_and_notarize.sh
```

Never commit those values. The script signs with the hardened runtime, submits
the app to Apple's notary service, staples the ticket, validates it, and creates
the release archive and checksum.

## GitHub release

Pushing a tag matching `v*` builds an arm64 draft release. Configure the signing
secrets described in `.github/workflows/release.yml` to make its artifact signed
and notarized. Review the draft and its checksum before publishing it.
