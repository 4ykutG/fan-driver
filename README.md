# MSI GF63 Fan Control

A small GPL-3.0 fan-only controller for the MSI Thin GF63 12VE on Linux.
Fn+F7 opens an MSI Center-style OSD and cycles through Automatic, Silent and
Maximum Fan. At 90°C, Cooler Boost is forced on regardless of the selected
mode and remains on until the CPU cools to 75°C.

## Scope guarantee

This controller writes only these two `msi-ec` interfaces:

- `/sys/devices/platform/msi-ec/fan_mode`
- `/sys/devices/platform/msi-ec/cooler_boost`

It does not call `powerprofilesctl`, change GNOME/KDE power modes, write MSI
`shift_mode` or `super_battery`, alter CPU/GPU limits, detect games, or run
GameMode. Desktop power settings remain entirely under the user's control.

One exception lives in the installer, never in the controller. Version 0.1.x
did drive `shift_mode` and `super_battery`. 0.2.0 dropped that scope and can no
longer undo it, so an upgrade would strand the EC on whatever 0.1.x last wrote
-- `turbo` above all, with nothing left able to reset it. When
`install-system.sh` finds a 0.1.x backend already in place it releases that
leftover once (`turbo` or `eco` to `comfort`, `super_battery` to `off`) and
never touches either again.

## Fan modes

| Fn+F7 mode | EC fan mode | Cooler Boost |
|---|---|---|
| Automatic | `auto` | off normally; forced on at 90°C |
| Silent | `silent` | off normally; forced on at 90°C |
| Maximum Fan | `auto` | always on |

The 90°C override does not forget the selected mode. After cooling to 75°C,
Automatic or Silent is restored. Firmware throttling and shutdown protections
are never disabled.

## Supported hardware

- MSI Thin GF63 12VE
- EC firmware `16R8IMS1.107`
- Linux with a compatible `msi-ec` driver exposing `fan_mode` and
  `cooler_boost`
- Python 3; GTK 4/PyGObject for the fallback OSD

The strict hardware allowlist prevents writes on unknown EC firmware.

## Install

```bash
git clone git@github.com:4ykutG/fan-driver.git
cd fan-driver
make test
sudo ./install-system.sh
```

On GNOME, enable the extension once if necessary:

```bash
gnome-extensions enable msi-gf63-profile-osd@4ykutg.github.io
```

Log out and back in if the Fn+F7 mapping or OSD is not picked up immediately.
On GNOME the Shell extension is the only OSD; the GTK fallback exits without
opening a second panel. Upgrades disable the retired `msi-profile-osd@local`
four-profile extension automatically when a user session is available.

## Commands

```bash
sudo msi-profile-control set auto
sudo msi-profile-control set silent
sudo msi-profile-control set max
sudo msi-profile-control status
msi-profile-doctor
```

The system service checks temperature every 15 seconds. This can be adjusted
between 5 and 120 seconds in `/etc/msi-profile-control.conf`.

## Development and safety

Run `make test` before submitting a change. The fake-sysfs integration test
includes sentinel power and Shift values and fails if fan operations alter
them. New laptop/firmware support requires upstream `msi-ec` support and
validation on that exact hardware.

See [README.tr.md](README.tr.md), [SECURITY.md](SECURITY.md), and
[CONTRIBUTING.md](CONTRIBUTING.md).
