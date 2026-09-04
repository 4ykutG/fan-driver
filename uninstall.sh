#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
set -Eeuo pipefail

readonly EXTENSION_UUID="msi-gf63-profile-osd@4ykutg.github.io"
purge=false
[[ ${1:-} == --purge ]] && purge=true
[[ ${EUID} -eq 0 ]] || { printf 'error: run as root\n' >&2; exit 1; }

if [[ -x /usr/local/sbin/msi-profile-control &&
      -e /sys/devices/platform/msi-ec/shift_mode ]]; then
	/usr/local/sbin/msi-profile-control game-stop >/dev/null 2>&1 || true
fi
systemctl disable --now msi-profile-hotkeyd.service 2>/dev/null || true
systemctl --global disable msi-profile-osd.service 2>/dev/null || true

rm -f /usr/local/sbin/msi-profile-control \
	/usr/local/sbin/msi-profile-hotkeyd \
	/usr/local/bin/msi-profile-osd \
	/usr/local/bin/msi-game-run \
	/etc/systemd/system/msi-profile-hotkeyd.service \
	/etc/systemd/user/msi-profile-osd.service \
	/etc/udev/hwdb.d/90-msi-gf63-hotkeys.hwdb
rm -rf "/usr/share/gnome-shell/extensions/${EXTENSION_UUID}"
$purge && rm -f /etc/msi-profile-games.conf

systemd-hwdb update
udevadm trigger --subsystem-match=input --action=change
systemctl daemon-reload
printf 'Uninstalled. GameMode/MangoHud packages and Steam options were left intact.\n'
