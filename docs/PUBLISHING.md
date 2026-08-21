# Publishing the repository

The workspace is intentionally prepared but not automatically published. This
avoids exposing the local Git author e-mail or choosing the wrong GitHub owner.

## 1. Protect your commit e-mail

In GitHub, enable **Keep my email addresses private**, then configure the
repository with the no-reply address shown by GitHub:

```zsh
git config user.name "YOUR DISPLAY NAME"
git config user.email "YOUR_GITHUB_NOREPLY_ADDRESS"
```

## 2. Create the first commit

Review `git add --dry-run .`, then:

```zsh
git add .
git commit -m "Initial open-source macOS release"
git branch -M main
```

## 3. Create the public repository

With the GitHub CLI authenticated:

```zsh
gh repo create DualCPY-macOS \
  --public \
  --source=. \
  --remote=origin \
  --push \
  --description="Dual-screen Android handheld mirroring for macOS"
```

Afterward, enable private vulnerability reporting, branch protection for
`main`, required CI checks, Dependabot security updates, Discussions, and the
GPL-3.0 license indicator in the repository settings.

## 4. First release

Follow [RELEASING.md](RELEASING.md). Prefer signing and notarization before
publishing `v1.0.0`; unsigned tag builds remain drafts by design.
