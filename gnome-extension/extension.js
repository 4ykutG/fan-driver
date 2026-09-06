// SPDX-License-Identifier: GPL-3.0-or-later
import Clutter from 'gi://Clutter';
import Gio from 'gi://Gio';
import GLib from 'gi://GLib';
import St from 'gi://St';

import {Extension} from 'resource:///org/gnome/shell/extensions/extension.js';
import * as Main from 'resource:///org/gnome/shell/ui/main.js';

const STATE_FILE = '/run/msi-profile-control/osd-state';
const HIDE_DELAY_MS = 1800;

// Icons are bundled as stroke-style SVGs so the panel matches the GTK OSD
// used on other desktops, independent of the icon theme.
const ICON_SVG = {
    'auto': `
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="88" height="88"
     fill="none" stroke="#fff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
  <circle cx="12" cy="12" r="2"/>
  <path d="M12 10c-1-4.8 1.4-7.2 4.4-6.6 2.6.5 2.8 3.5.8 5.2C15.8 9.8 14 10.2 12 10z"/>
  <path d="M13.7 13c4.7 1.5 5.5 4.8 3.4 7-1.8 1.9-4.5.6-5-2-.3-1.8.3-3.5 1.6-5z"/>
  <path d="M10.3 13c-3.6 3.3-6.8 2.5-7.7-.4-.8-2.5 1.6-4.3 4-3.3 1.7.7 2.9 2 3.7 3.7z"/>
</svg>`,
    'silent': `
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="88" height="88"
     fill="none" stroke="#fff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
  <path d="M20.5 14.2A8.7 8.7 0 1 1 9.8 3.5a7.2 7.2 0 0 0 10.7 10.7z"/>
</svg>`,
    'max': `
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="88" height="88"
     fill="none" stroke="#fff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
  <circle cx="12" cy="12" r="8.5"/>
  <circle cx="12" cy="12" r="1.7"/>
  <path d="M12 10.3c-.8-4 1.1-6 3.7-5.5 2.3.4 2.4 3 .7 4.5-1.2 1-2.7 1.3-4.4 1z"/>
  <path d="M13.5 12.9c3.8 1.2 4.5 3.9 2.7 5.8-1.6 1.6-3.8.5-4.2-1.7-.3-1.5.3-2.9 1.5-4.1z"/>
  <path d="M10.5 12.9c-3 2.7-5.5 2-6.3-.4-.7-2.2 1.4-3.7 3.4-2.8 1.4.5 2.4 1.6 2.9 3.2z"/>
</svg>`,
};

const MODES = [
    {id: 'auto', name: 'OTOMATİK'},
    {id: 'silent', name: 'SESSİZ'},
    {id: 'max', name: 'MAKSİMUM FAN'},
];

export default class MsiProfileOsdExtension extends Extension {
    enable() {
        this._lastSeq = null;
        this._hideTimeout = 0;
        this._buildOverlay();

        this._stateFile = Gio.File.new_for_path(STATE_FILE);
        this._readState(true);
        this._monitor = this._stateFile.monitor_file(
            Gio.FileMonitorFlags.WATCH_MOVES, null);
        this._monitor.set_rate_limit(50);
        this._monitor.connect('changed', (monitor, file, other, event) => {
            if (event === Gio.FileMonitorEvent.CHANGES_DONE_HINT ||
                event === Gio.FileMonitorEvent.CREATED ||
                event === Gio.FileMonitorEvent.MOVED_IN ||
                event === Gio.FileMonitorEvent.RENAMED)
                this._readState(false);
        });
    }

    disable() {
        this._monitor?.cancel();
        this._monitor = null;
        this._stateFile = null;
        if (this._hideTimeout) {
            GLib.source_remove(this._hideTimeout);
            this._hideTimeout = 0;
        }
        this._overlay?.remove_all_transitions();
        this._overlay?.destroy();
        this._overlay = null;
        this._cards = null;
        this._status = null;
    }

    _buildOverlay() {
        this._overlay = new St.BoxLayout({
            vertical: true,
            style_class: 'msi-profile-osd',
            reactive: false,
            can_focus: false,
            visible: false,
            opacity: 0,
        });

        const title = new St.Label({
            text: 'MSI FAN CONTROL',
            style_class: 'msi-profile-title',
            x_align: Clutter.ActorAlign.CENTER,
        });
        const row = new St.BoxLayout({
            style_class: 'msi-profile-row',
            x_align: Clutter.ActorAlign.CENTER,
        });

        this._cards = new Map();
        for (const item of MODES) {
            const card = new St.BoxLayout({
                vertical: true,
                style_class: 'msi-profile-card',
                x_align: Clutter.ActorAlign.CENTER,
            });
            const gicon = Gio.BytesIcon.new(new GLib.Bytes(
                new TextEncoder().encode(ICON_SVG[item.id])));
            const icon = new St.Icon({
                gicon,
                style_class: 'msi-profile-icon',
                x_align: Clutter.ActorAlign.CENTER,
                opacity: 184,
            });
            card.add_child(icon);
            card.add_child(new St.Label({
                text: item.name,
                style_class: 'msi-profile-name',
                x_align: Clutter.ActorAlign.CENTER,
            }));
            row.add_child(card);
            this._cards.set(item.id, {card, icon});
        }

        this._status = new St.Label({
            style_class: 'msi-profile-status',
            x_align: Clutter.ActorAlign.CENTER,
        });

        this._overlay.add_child(title);
        this._overlay.add_child(row);
        this._overlay.add_child(this._status);
        Main.uiGroup.add_child(this._overlay);
    }

    _positionOverlay() {
        // Center on the primary monitor; the stage spans all monitors, so
        // stage-relative constraints would land between them.
        const monitor = Main.layoutManager.primaryMonitor ??
            Main.layoutManager.monitors[0];
        if (!monitor)
            return;
        const [, natWidth] = this._overlay.get_preferred_width(-1);
        const [, natHeight] = this._overlay.get_preferred_height(natWidth);
        this._overlay.set_position(
            monitor.x + Math.round((monitor.width - natWidth) / 2),
            monitor.y + Math.round(monitor.height * 0.42 - natHeight / 2));
    }

    _readState(initial) {
        let state;
        try {
            const [, contents] = this._stateFile.load_contents(null);
            state = JSON.parse(new TextDecoder().decode(contents));
        } catch {
            return;
        }
        if (state.seq === this._lastSeq)
            return;
        this._lastSeq = state.seq;
        if (!initial)
            this._render(state);
    }

    _render(state) {
        const highlight = state.phase === 'preview'
            ? state.selected
            : (state.mode ?? state.profile);

        for (const [id, {card, icon}] of this._cards) {
            const active = id === highlight;
            card.set_style_class_name(active
                ? `msi-profile-card msi-profile-card-active msi-active-${id}`
                : 'msi-profile-card');
            icon.opacity = active ? 255 : 184;
        }

        if (state.phase === 'preview') {
            this._status.set_style_class_name('msi-profile-status');
            this._status.text = 'Seçmek için Fn+F7 • bırakınca uygulanır';
        } else if (state.phase === 'error') {
            this._status.set_style_class_name(
                'msi-profile-status msi-profile-warning');
            this._status.text = state.message ?? 'Hata';
        } else {
            this._status.set_style_class_name('msi-profile-status');
            const fanText = state.boost === 'on' ? 'Maksimum' :
                (state.fan === 'silent' ? 'Sessiz' : 'Otomatik');
            const suffix = state.message && state.message !== 'ok'
                ? `  •  ${state.message}` : '';
            this._status.text = `CPU ${state.temp}°C  •  Fan ${fanText}${suffix}`;
        }

        this._positionOverlay();
        this._overlay.remove_all_transitions();
        this._overlay.opacity = 255;
        this._overlay.show();

        if (this._hideTimeout) {
            GLib.source_remove(this._hideTimeout);
            this._hideTimeout = 0;
        }
        if (state.phase !== 'preview') {
            this._hideTimeout = GLib.timeout_add(
                GLib.PRIORITY_DEFAULT, HIDE_DELAY_MS, () => {
                    this._hideTimeout = 0;
                    this._overlay.ease({
                        opacity: 0,
                        duration: 220,
                        mode: Clutter.AnimationMode.EASE_OUT_QUAD,
                        onComplete: () => this._overlay.hide(),
                    });
                    return GLib.SOURCE_REMOVE;
                });
        }
    }
}
