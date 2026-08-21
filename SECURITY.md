# Security policy

## Supported versions

Security fixes are applied to the latest release and the default branch.

## Reporting a vulnerability

Please use GitHub's private **Report a vulnerability** form in the repository's
Security tab. Do not open a public issue for an unpatched vulnerability.

Include affected versions, reproduction steps, impact, and any suggested fix.
Device serials, wireless-debugging addresses, pairing codes, certificates, and
logs containing personal paths should be redacted.

DualCPY executes `adb` and `scrcpy` and can transfer or delete files when the
user explicitly requests those operations. Reports about expected, documented
ADB capabilities without an application-level bypass are not vulnerabilities.
