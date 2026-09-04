# Initial issue plan

Create these issues immediately before the public launch so contributors see a
small, honest and actionable backlog.

## 1. Real-hardware CS2 benchmark and thermal validation

Labels: `testing`, `hardware`, `help wanted`

Validate automatic game start/exit, RTX 4050 selection, CPU temperature, fan
RPM and frametime on Thin GF63 12VE / EC 16R8IMS1.107. Publish only the output
of `msi-profile-doctor --json` and redacted benchmark results.

## 2. AUR package

Labels: `packaging`, `help wanted`

Create a reproducible PKGBUILD after `v0.1.0` is tagged. Keep `msi-ec` as an
explicit dependency and do not bypass the firmware allowlist.

## 3. Test GTK OSD on non-GNOME desktops

Labels: `testing`, `ui`, `help wanted`

Test KDE Plasma, Hyprland and Sway with gtk4-layer-shell. Report compositor,
desktop version and a screenshot containing no private content.

## 4. Translation infrastructure

Labels: `enhancement`, `localization`, `good first issue`

Move Turkish daemon/OSD messages into a small translation layer and provide
English as the fallback language.

## 5. Safe settings UI

Labels: `enhancement`, `ui`

Design an unprivileged editor for the bounded timing options and executable
list. Applying changes must use a narrowly scoped privileged operation; never
introduce a general passwordless command or shell-sourced configuration.
