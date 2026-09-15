#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
set -Eeuo pipefail

readonly SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SYSFS_BASE="/sys/devices/platform/msi-ec"
readonly EXTENSION_UUID="msi-gf63-profile-osd@4ykutg.github.io"
readonly LEGACY_EXTENSION_UUID="msi-profile-osd@local"
readonly EXTENSION_DIR="/usr/share/gnome-shell/extensions/${EXTENSION_UUID}"
readonly INSTALLED_BACKEND="/usr/local/sbin/msi-profile-control"
readonly SHIFT_FILE="${SYSFS_BASE}/shift_mode"
readonly BATTERY_FILE="${SYSFS_BASE}/super_battery"

die() { printf 'error: %s\n' "$*" >&2; exit 1; }

# 0.1.x drove MSI Shift and super_battery alongside the fan. 0.2.0 narrowed the
# scope to fan_mode and cooler_boost, so an upgrade leaves whatever the old
# release last wrote with nothing in the project able to undo it. Turbo is the
# damaging case: it lifts the CPU package power limit, so the machine keeps
# running unrestricted long after the code that asked for it is gone. Release
# the leftover once, here, while the old backend is still on disk to prove an
# upgrade is what is happening. The installed controller never writes these.
release_legacy_power_state()
{
	local shift_mode battery

	[[ -f $INSTALLED_BACKEND ]] || return 0
	grep -Fq 'shift_mode' "$INSTALLED_BACKEND" 2>/dev/null || return 0

	if [[ -r $SHIFT_FILE && -w $SHIFT_FILE ]]; then
		IFS= read -r shift_mode < "$SHIFT_FILE"
		if [[ $shift_mode == turbo || $shift_mode == eco ]]; then
			printf 'comfort\n' > "$SHIFT_FILE"
			printf 'released MSI Shift: %s -> comfort (0.1.x leftover)\n' \
				"$shift_mode"
		fi
	fi

	if [[ -r $BATTERY_FILE && -w $BATTERY_FILE ]]; then
		IFS= read -r battery < "$BATTERY_FILE"
		if [[ $battery == on ]]; then
			printf 'off\n' > "$BATTERY_FILE"
			printf 'released MSI super_battery: on -> off (0.1.x leftover)\n'
		fi
	fi
}

# Upgrade a logged-in GNOME user from the retired four-profile extension.
# The GTK OSD is only a non-GNOME fallback; stopping it prevents two panels
# until the updated session environment is picked up.
configure_gnome_user()
{
	local user_id login_user runtime_dir
	user_id=${SUDO_UID:-${PKEXEC_UID:-}}
	[[ $user_id =~ ^[0-9]+$ && $user_id -ne 0 ]] || return 0
	login_user=$(getent passwd "$user_id" | cut -d: -f1)
	[[ -n $login_user ]] || return 0
	runtime_dir="/run/user/${user_id}"
	[[ -S ${runtime_dir}/bus ]] || return 0

	local -a user_session=(runuser -u "$login_user" -- env
		"XDG_RUNTIME_DIR=${runtime_dir}"
		"DBUS_SESSION_BUS_ADDRESS=unix:path=${runtime_dir}/bus")
	"${user_session[@]}" gnome-extensions disable \
		"$LEGACY_EXTENSION_UUID" >/dev/null 2>&1 || true
	"${user_session[@]}" gnome-extensions enable \
		"$EXTENSION_UUID" >/dev/null 2>&1 || true
	"${user_session[@]}" systemctl --user stop \
		msi-profile-osd.service >/dev/null 2>&1 || true
}

[[ ${EUID} -eq 0 ]] || die 'run this installer as root'
[[ -r /sys/class/dmi/id/sys_vendor ]] || die 'DMI vendor is unavailable'
[[ $(</sys/class/dmi/id/sys_vendor) == 'Micro-Star International Co., Ltd.' ]] ||
	die 'unsupported vendor; refusing to touch the embedded controller'
[[ $(</sys/class/dmi/id/product_name) == 'Thin GF63 12VE' ]] ||
	die 'unsupported model; this release only supports MSI Thin GF63 12VE'
[[ -r ${SYSFS_BASE}/fw_version ]] ||
	die 'msi-ec is not loaded; install a version supporting this laptop first'
[[ $(<"${SYSFS_BASE}/fw_version") == '16R8IMS1.107' ]] ||
	die 'unsupported EC firmware; refusing to write unknown EC registers'

for command in python3 systemctl; do
	command -v "$command" >/dev/null || die "missing dependency: $command"
done

release_legacy_power_state

install -Dm0755 "${SOURCE_DIR}/msi-profile-control" \
	/usr/local/sbin/msi-profile-control
install -Dm0755 "${SOURCE_DIR}/msi-profile-hotkeyd" \
	/usr/local/sbin/msi-profile-hotkeyd
install -Dm0755 "${SOURCE_DIR}/msi-profile-osd" \
	/usr/local/bin/msi-profile-osd
install -Dm0755 "${SOURCE_DIR}/msi-profile-doctor" \
	/usr/local/bin/msi-profile-doctor
install -Dm0755 "${SOURCE_DIR}/msi-profile-monitor" \
	/usr/local/bin/msi-profile-monitor
install -Dm0644 "${SOURCE_DIR}/msi-profile-hotkeyd.service" \
	/etc/systemd/system/msi-profile-hotkeyd.service
install -Dm0644 "${SOURCE_DIR}/msi-profile-osd.service" \
	/etc/systemd/user/msi-profile-osd.service
install -Dm0644 "${SOURCE_DIR}/90-msi-gf63-hotkeys.hwdb" \
	/etc/udev/hwdb.d/90-msi-gf63-hotkeys.hwdb
install -Dm0644 "${SOURCE_DIR}/msi-profile-control.conf" \
	/etc/msi-profile-control.conf
install -Dm0644 "${SOURCE_DIR}/gnome-extension/extension.js" \
	"${EXTENSION_DIR}/extension.js"
install -Dm0644 "${SOURCE_DIR}/gnome-extension/metadata.json" \
	"${EXTENSION_DIR}/metadata.json"
install -Dm0644 "${SOURCE_DIR}/gnome-extension/stylesheet.css" \
	"${EXTENSION_DIR}/stylesheet.css"

/usr/bin/systemd-hwdb update
/usr/bin/udevadm trigger --subsystem-match=input --action=change
/usr/bin/systemctl daemon-reload
/usr/bin/systemctl enable msi-profile-hotkeyd.service
/usr/bin/systemctl restart msi-profile-hotkeyd.service
/usr/bin/systemctl --global enable msi-profile-osd.service
configure_gnome_user

printf '\nInstalled successfully.\n'
printf 'GNOME OSD: %s\n' "$EXTENSION_UUID"
printf 'Other desktops: log out/in once to start the GTK OSD.\n'
printf 'Support report: msi-profile-doctor\n'
printf 'Fan telemetry: msi-profile-monitor --duration 60 -o session.csv\n'
