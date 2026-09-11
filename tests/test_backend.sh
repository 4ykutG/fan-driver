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
printf 'auto\nsilent\n' > "${SYSFS}/available_fan_modes"
printf 'comfort\n' > "${SYSFS}/shift_mode"
printf 'unchanged\n' > "${SYSFS}/power_profile"
printf 'auto\n' > "${SYSFS}/fan_mode"
printf 'off\n' > "${SYSFS}/cooler_boost"
printf '65\n' > "${SYSFS}/cpu/realtime_temperature"

export MSI_PROFILE_TESTING=1
export MSI_PROFILE_SYSFS_BASE="$SYSFS"
export MSI_PROFILE_STATE_DIR="$STATE"
export MSI_PROFILE_LOCK_FILE="${TEST_DIR}/control.lock"
export MSI_PROFILE_PRODUCT_FILE="${DMI}/product"
export MSI_PROFILE_VENDOR_FILE="${DMI}/vendor"

backend="${ROOT_DIR}/msi-profile-control"

# The runtime source must not even name interfaces outside the fan boundary.
if grep -Eq 'powerprofilesctl|shift_mode|super_battery|game-start|game-stop' \
	"$backend"; then
	printf 'backend contains a forbidden power/game control reference\n' >&2
	exit 1
fi

assert_value()
{
	local expected=$1 file=$2 actual
	IFS= read -r actual < "$file"
	[[ $actual == "$expected" ]] || {
		printf 'expected %s in %s, got %s\n' "$expected" "$file" "$actual" >&2
		exit 1
	}
}

# All three modes change fan controls only.
"$backend" set silent >/dev/null
assert_value silent "${SYSFS}/fan_mode"
assert_value off "${SYSFS}/cooler_boost"
assert_value comfort "${SYSFS}/shift_mode"
assert_value unchanged "${SYSFS}/power_profile"

# At 90 C the safety override starts without changing the selected mode.
printf '90\n' > "${SYSFS}/cpu/realtime_temperature"
output=$("$backend" guard)
assert_value on "${SYSFS}/cooler_boost"
assert_value silent "${STATE}/state"
[[ $output == *$'status\tsilent\t90\tsilent\ton\t90°C üzeri: Cooler Boost' ]]

# Hysteresis keeps boost running until the machine has actually cooled.
printf '80\n' > "${SYSFS}/cpu/realtime_temperature"
"$backend" guard >/dev/null
assert_value on "${SYSFS}/cooler_boost"
printf '75\n' > "${SYSFS}/cpu/realtime_temperature"
"$backend" guard >/dev/null
assert_value off "${SYSFS}/cooler_boost"
assert_value silent "${SYSFS}/fan_mode"

# Maximum fan is fixed Cooler Boost; cycle then returns to automatic.
"$backend" set max >/dev/null
assert_value auto "${SYSFS}/fan_mode"
assert_value on "${SYSFS}/cooler_boost"
"$backend" cycle >/dev/null
assert_value auto "${STATE}/state"
assert_value off "${SYSFS}/cooler_boost"

# Even an explicit silent request cannot defeat the 90 C safety override.
printf '94\n' > "${SYSFS}/cpu/realtime_temperature"
"$backend" set silent >/dev/null
assert_value silent "${SYSFS}/fan_mode"
assert_value on "${SYSFS}/cooler_boost"
assert_value comfort "${SYSFS}/shift_mode"
assert_value unchanged "${SYSFS}/power_profile"

# A 0.1.x profile name left in the state file must not be read back as
# Maximum Fan. The guard sets cooler_boost itself, so inferring the mode from
# it would latch the fan on: max forces boost on, boost on reads back as max.
printf 'balanced\n' > "${STATE}/state"
printf 'on\n' > "${SYSFS}/cooler_boost"
printf '60\n' > "${SYSFS}/cpu/realtime_temperature"
output=$("$backend" guard)
assert_value off "${SYSFS}/cooler_boost"
assert_value silent "${SYSFS}/fan_mode"
[[ $output == *$'status\tsilent\t60\tsilent\toff\t'* ]] || {
	printf 'stale state did not fall back to the fan mode: %s\n' "$output" >&2
	exit 1
}

# Unknown firmware fails closed without changing any setting.
printf 'UNKNOWN.999\n' > "${SYSFS}/fw_version"
if "$backend" set max >/dev/null 2>&1; then
	printf 'unknown firmware unexpectedly succeeded\n' >&2
	exit 1
fi
assert_value silent "${SYSFS}/fan_mode"
assert_value comfort "${SYSFS}/shift_mode"

printf 'backend fan-only integration tests: ok\n'
