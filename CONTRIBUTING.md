# Contributing

Thanks for helping improve DualCPY macOS. Small, focused pull requests are the
easiest to review.

## Setup

1. Use macOS 13 or newer with Homebrew.
2. Run `./install.command`.
3. Run `make test` before opening a pull request.

Hardware changes should be tested on an authorized Android device. If you do
not own the relevant handheld, clearly mark the change as untested and include
the `adb`/`scrcpy` output used to validate it.

## Pull requests

- Explain the user-visible problem and the chosen solution.
- Add or update tests for behavior that can run without hardware.
- Never commit device serials, local configuration, logs, signing certificates,
  Apple credentials, build output, or screenshots containing private data.
- Preserve upstream GPL notices and update `NOTICE.md` when incorporating code
  from another project.
- Keep platform-specific behavior behind a small compatibility layer where
  practical.

Bug reports should include the output of `.venv/bin/python doctor.py`, with any
device serial or network address redacted.
