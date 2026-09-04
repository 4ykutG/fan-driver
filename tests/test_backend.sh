#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
set -Eeuo pipefail

readonly ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
readonly TEST_DIR="$(mktemp -d)"
trap 'rm -rf "$TEST_DIR"' EXIT

readonly SYSFS="${TEST_DIR}/sysfs"
readonly STATE="${TEST_DIR}/state"
readonly DMI="${TEST_DIR}/dmi"
mkdir -p "${SYSFS}/cpu" "$STATE" "$DMI"

printf 'Micro-Star International Co., Ltd.\n' > "${DMI}/vendor"
printf 'Thin GF63 12VE\n' > "${DMI}/product"
printf '16R8IMS1.107\n' > "${SYSFS}/fw_version"
printf 'eco\ncomfort\nturbo\n' > "${SYSFS}/available_shift_modes"
printf 'auto\nsilent\n' > "${SYSFS}/available_fan_modes"
printf 'comfort\n' > "${SYSFS}/shift_mode"
printf 'auto\n' > "${SYSFS}/fan_mode"
printf 'off\n' > "${SYSFS}/cooler_boost"
printf 'off\n' > "${SYSFS}/super_battery"
printf '65\n' > "${SYSFS}/cpu/realtime_temperature"

export MSI_PROFILE_TESTING=1
export MSI_PROFILE_SYSFS_BASE="$SYSFS"
export MSI_PROFILE_STATE_DIR="$STATE"
export MSI_PROFILE_LOCK_FILE="${TEST_DIR}/control.lock"
export MSI_PROFILE_PRODUCT_FILE="${DMI}/product"
export MSI_PROFILE_VENDOR_FILE="${DMI}/vendor"
export MSI_PROFILE_POWERPROFILESCTL=/bin/true

backend="${ROOT_DIR}/msi-profile-control"

assert_value()
{
	local expected=$1 file=$2 actual
	IFS= read -r actual < "$file"
	[[ $actual == "$expected" ]] || {
		printf 'expected %s in %s, got %s\n' "$expected" "$file" "$actual" >&2
		exit 1
	}
}

"$backend" set balanced >/dev/null
assert_value comfort "${SYSFS}/shift_mode"
assert_value off "${SYSFS}/cooler_boost"

"$backend" game-start >/dev/null
assert_value turbo "${SYSFS}/shift_mode"
assert_value on "${SYSFS}/cooler_boost"
[[ -e ${STATE}/game-active ]]

# A manual low-power request cannot break the active game lock.
"$backend" set silent >/dev/null
assert_value turbo "${SYSFS}/shift_mode"
assert_value on "${SYSFS}/cooler_boost"

# Heat soak keeps Cooler Boost on after returning to Balanced.
printf '85\n' > "${SYSFS}/cpu/realtime_temperature"
"$backend" game-stop >/dev/null
assert_value comfort "${SYSFS}/shift_mode"
assert_value on "${SYSFS}/cooler_boost"
[[ ! -e ${STATE}/game-active ]]

# Daily-use hysteresis releases Cooler Boost only after cooling down.
printf '70\n' > "${SYSFS}/cpu/realtime_temperature"
"$backend" guard >/dev/null
assert_value off "${SYSFS}/cooler_boost"

# Unknown firmware must fail closed without touching the EC profile.
printf 'UNKNOWN.999\n' > "${SYSFS}/fw_version"
if "$backend" set performance >/dev/null 2>&1; then
	printf 'unknown firmware unexpectedly succeeded\n' >&2
	exit 1
fi
assert_value comfort "${SYSFS}/shift_mode"

printf 'backend integration tests: ok\n'
