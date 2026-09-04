# MSI GF63 Auto Profile

[![Tests](https://github.com/4ykutG/fan-driver/actions/workflows/test.yml/badge.svg)](https://github.com/4ykutG/fan-driver/actions/workflows/test.yml)
[![License: GPL-3.0-or-later](https://img.shields.io/badge/License-GPL--3.0--or--later-blue.svg)](LICENSE)
[![Release](https://img.shields.io/github/v/release/4ykutG/fan-driver)](https://github.com/4ykutG/fan-driver/releases)

An open-source MSI Center-style profile controller for the **MSI Thin GF63
12VE** on Linux. It combines Fn+F7 profile selection, an on-screen display,
automatic game detection, maximum cooling during games, and optional
GameMode/NVIDIA PRIME integration.

[Türkçe belge](README.tr.md)

> [!CAUTION]
> Embedded-controller layouts are firmware-specific. Version 0.1.0 writes
> only on `Thin GF63 12VE` with EC firmware `16R8IMS1.107`. It refuses all
> other model/firmware combinations. Do not remove these checks.

## Features

- MSI Center-like **Super Battery → Silent → Balanced → Performance** OSD.
- Captures the real Fn+F7 scancode without opening GNOME Display Settings.
- Detects native Steam and Proton games without per-game fan configuration.
- Locks the laptop to Turbo + Cooler Boost while a game is active.
- Returns to Balanced eight seconds after the last game exits.
- Keeps firmware thermal throttling and emergency shutdown protections intact.
- Optional `gamemoderun` + `prime-run` wrapper for hybrid NVIDIA laptops.
- Systemd sandboxing, strict hardware validation, and no passwordless sudo rule.

This project is a userspace controller for the open-source
[`msi-ec`](https://github.com/BeardOverflow/msi-ec) kernel driver; it is not a
replacement kernel driver.

## Profiles

| Profile | MSI EC shift | Fan | Cooler Boost | Power profile |
| --- | --- | --- | --- | --- |
| Super Battery | `eco` | `silent` | Thermal safety guard | power-saver |
| Silent | `eco` | `silent` | Thermal safety guard | power-saver |
| Balanced | `comfort` | `auto` | Thermal safety guard | balanced |
| Performance/game | `turbo` | `auto` | always on | performance |

During a game, the userspace temperature guard never changes the selected
profile or fan mode. Cooler Boost stays on. Hardware-level thermal protection
continues to operate normally.

## Requirements

- MSI Thin GF63 12VE
- EC firmware `16R8IMS1.107`
- Linux with systemd
- A current `msi-ec` module exposing `/sys/devices/platform/msi-ec`
- Python 3, power-profiles-daemon, GTK 4 and PyGObject
- GNOME Shell 50 for the bundled Shell OSD, or GTK4 on other desktops
- Arch Linux/CachyOS for the optional automatic gaming dependency installer

## Install

Inspect the scripts first, then run:

```bash
git clone https://github.com/4ykutG/fan-driver.git
cd fan-driver
sudo ./install-system.sh
```

On GNOME:

```bash
gnome-extensions enable msi-gf63-profile-osd@4ykutg.github.io
```

Optional GameMode, MangoHud, NVIDIA PRIME and CS2 setup:

```bash
sudo ./gaming-setup.sh --configure-cs2
```

The CS2 editor refuses to run while Steam is open, creates a timestamped
backup, preserves existing launch arguments, and is idempotent. The resulting
launch option is:

```text
msi-game-run %command%
```

## Use

Press Fn+F7 repeatedly, then stop on the desired card. The choice is committed
after 0.9 seconds. While a game is detected, Performance remains locked and
Fn+F7 shows the current locked state.

Manual commands:

```bash
sudo msi-profile-control status
sudo msi-profile-control set balanced
sudo msi-profile-control set performance
journalctl -u msi-profile-hotkeyd.service
msi-profile-doctor
```

`msi-profile-doctor --json` produces a read-only support report without a
username, hostname, serial number, Steam data, process environment or token.

Record a 60-second thermal/GPU session without process names or identity data:

```bash
msi-profile-monitor --duration 60 --output cs2-session.csv
```

The recorder refuses to overwrite an existing file unless `--force` is given.

Native Steam and Proton games are detected automatically. For a non-Steam
game, add its executable basename to `/etc/msi-profile-games.conf`, one name
per line.

Daemon timing can be changed in `/etc/msi-profile-control.conf` and takes
effect after `sudo systemctl restart msi-profile-hotkeyd`. Accepted ranges are
0.5–10 seconds for scanning, 0–60 seconds for exit delay and 5–120 seconds for
the daily thermal guard. Configuration is parsed as data; it is never sourced
as shell code.

## Uninstall

```bash
sudo ./uninstall.sh
```

Use `sudo ./uninstall.sh --purge` to remove the custom game list too. Gaming
packages and Steam launch options are deliberately retained.

## Performance expectations

The tool removes common Linux laptop mistakes such as launching a Vulkan game
on the iGPU or leaving the EC in Eco mode. It cannot guarantee higher FPS than
Windows: game builds, drivers, shader compilation, background services and the
laptop's 45 W GPU firmware limit still matter. It never overclocks the GPU or
changes its VBIOS power limit.

## Development

```bash
make test
```

See [architecture and safety notes](docs/architecture.md) and
[CONTRIBUTING.md](CONTRIBUTING.md). Planned work is tracked in
[ROADMAP.md](ROADMAP.md).

## License

GPL-3.0-or-later. See [LICENSE](LICENSE). MSI and MSI Center are trademarks of
Micro-Star International. This project is independent and not endorsed by MSI.
