#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
set -Eeuo pipefail

readonly SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
configure_cs2=false
target_user="${SUDO_USER:-}"

usage()
{
	printf 'usage: sudo ./gaming-setup.sh [--configure-cs2] [--user USER]\n'
}

while (($#)); do
	case "$1" in
		--configure-cs2) configure_cs2=true ;;
		--user)
			shift
			(($#)) || { usage >&2; exit 2; }
			target_user=$1
			;;
		-h|--help) usage; exit 0 ;;
		*) usage >&2; exit 2 ;;
	esac
	shift
done

[[ ${EUID} -eq 0 ]] || { printf 'error: run as root\n' >&2; exit 1; }
if [[ -z $target_user && -n ${PKEXEC_UID:-} ]]; then
	target_user=$(getent passwd "$PKEXEC_UID" | cut -d: -f1)
fi
[[ -n $target_user && $target_user != root ]] || {
	printf 'error: cannot determine desktop user; pass --user USER\n' >&2
	exit 1
}
user_home=$(getent passwd "$target_user" | cut -d: -f6)
[[ -n $user_home && -d $user_home ]] || {
	printf 'error: cannot find home for %s\n' "$target_user" >&2
	exit 1
}

command -v pacman >/dev/null || {
	printf 'error: automatic gaming dependency setup currently supports Arch/CachyOS\n' >&2
	exit 1
}
pacman -S --needed --noconfirm \
	gamemode lib32-gamemode mangohud lib32-mangohud nvidia-prime
install -Dm0755 "${SOURCE_DIR}/msi-game-run" /usr/local/bin/msi-game-run

if $configure_cs2; then
	if pgrep -u "$target_user" -x steam >/dev/null 2>&1; then
		printf 'error: close Steam before editing CS2 launch options\n' >&2
		exit 2
	fi
	runuser -u "$target_user" -- /usr/bin/python3 \
		"${SOURCE_DIR}/configure-steam-cs2.py" "$user_home"
fi

printf 'Gaming dependencies installed. Steam launch option: msi-game-run %%command%%\n'
