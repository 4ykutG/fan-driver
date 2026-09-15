# Architecture

The project has three deliberately narrow layers:

1. `msi-profile-control` validates the exact laptop and EC firmware, serializes
   access, and writes only `fan_mode` and `cooler_boost`.
2. `msi-profile-hotkeyd` reads kernel `KEY_PROG3` events for Fn+F7, cycles the
   three fan modes, and runs the thermal guard every 15 seconds.
3. The GNOME extension or GTK application renders the read-only OSD state from
   `/run/msi-profile-control/osd-state`.

Only while Automatic is selected, the guard enables Cooler Boost at 90°C and
keeps it enabled until 75°C. Silent always writes `silent` plus boost off;
Maximum Fan always writes `auto` plus boost on. No component imports a
power-management API or writes MSI Shift, battery, CPU or GPU settings.
