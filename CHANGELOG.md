# Changelog

## Unreleased

- Made Silent an absolute lock with Cooler Boost always off; thermal boost now
  applies only to Automatic, while Maximum Fan remains explicitly selected.
- Restart the hotkey daemon during upgrades so the newly installed code is
  loaded even when the service was already active.
- Prevented the GTK fallback OSD from running in GNOME sessions.
- Added automatic migration from the retired four-profile GNOME extension so
  Fn+F7 opens exactly one three-mode fan panel after upgrades.

## 0.2.1 - 2026-09-12

- `install-system.sh` now releases the MSI Shift and `super_battery` values a
  0.1.x install left behind before overwriting it. 0.2.0 removed that scope
  without a migration, so upgrading stranded the EC in `turbo` with nothing
  left able to reset it. The controller itself still writes neither.
- Stopped inferring Maximum Fan from `cooler_boost` when no valid mode is
  recorded. The guard sets that bit itself above 90°C, so reading it back as a
  user choice latched the fan on: `max` forces boost on, and boost on was read
  as `max` again at the next tick. The state file lives on tmpfs, so this
  fallback runs on every boot and a warm boot could latch the fan for good.

## 0.2.0 - 2026-09-07

- Refactored the controller to three fan-only modes: Automatic, Silent and
  Maximum Fan.
- Removed all power-profile, MSI Shift, battery, game-detection, GameMode and
  Steam integration.
- Added a mandatory Cooler Boost override at 90°C with release at 75°C.
- Updated Fn+F7 OSDs, diagnostics, telemetry and tests for the narrow scope.
- Added regression assertions proving Shift and desktop power state are not
  changed by fan operations.

## 0.1.0 - 2026-09-04

- Initial public release for MSI Thin GF63 12VE / EC 16R8IMS1.107.
- Fn+F7 four-profile OSD for GNOME and GTK4 desktops.
- Native Steam, Proton and configurable non-Steam game detection.
- Fixed Turbo + Cooler Boost game lock and delayed Balanced restore.
- Optional GameMode, MangoHud, NVIDIA PRIME and CS2 integration.
- Strict DMI/firmware checks, systemd sandboxing and automated tests.
