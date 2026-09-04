# Roadmap

## Before v0.1.0 public launch

- Verify installation, Fn+F7, OSD and automatic game lock on real hardware.
- Capture a CS2 session: GPU selection, fan RPM, CPU/GPU temperature and
  frametime before/after, without publishing personal data.
- Confirm both GitHub Actions workflows are green.
- Choose the final project and repository name.
- Add one OSD screenshot and tag `v0.1.0`.
- Make the repository public and publish the community announcement.

## Proposed v0.2 work

- Package for the AUR after the first stable tag exists.
- Add a small settings UI for timing and non-Steam executable entries.
- Test the GTK overlay on KDE Plasma, Hyprland and Sway.
- Add English UI strings and translation infrastructure.
- Add opt-in MangoHud benchmark capture with automatic redaction.
- Investigate game detection through GameMode's public API as an alternative
  to process scanning.

## Model support policy

Additional models or firmware versions are never enabled by similarity alone.
They require upstream `msi-ec` support, a dedicated allowlist entry, synthetic
tests and validation by an owner of that exact model/firmware combination.
