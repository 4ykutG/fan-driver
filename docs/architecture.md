# Architecture and safety

1. `msi-profile-hotkeyd` runs as a sandboxed root system service.
2. It reads the Fn+F7 evdev event and scans process metadata for games.
3. It invokes `msi-profile-control`, the only component that writes `msi-ec`
   sysfs attributes.
4. The backend validates DMI model, vendor and EC firmware before every write.
5. The daemon publishes a mode-0644 JSON snapshot in `/run`.
6. The unprivileged GTK OSD or GNOME Shell extension only reads that snapshot.

The daemon reads executable paths, command lines and the two Steam app-id
environment entries needed to identify Proton games. It does not store or log
process environments.

## Game lock

`game-start` applies Turbo, automatic EC fan control, Cooler Boost and the
performance power profile. A runtime marker prevents manual or thermal-guard
changes from selecting a lower mode while a game is active. The guard only
repairs drift from that fixed state. `game-stop` removes the marker and applies
Balanced; Cooler Boost remains active during heat soak until the CPU cools.

## Trust boundary

Only root can write the EC sysfs files. There is no NOPASSWD sudo rule, D-Bus
write API, socket or writable root command file. `/etc/msi-profile-games.conf`
contains executable basenames only and cannot inject commands.

The exact firmware allowlist is intentional. Supporting a new firmware requires
upstream `msi-ec` support and real-hardware validation; never infer EC register
compatibility from a similar marketing name.
