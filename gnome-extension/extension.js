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
    'super-battery': `
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="88" height="88"
     fill="none" stroke="#fff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
  <rect x="2" y="7.5" width="16.5" height="9" rx="2.5"/>
  <path d="M21.5 10.5v3" stroke-width="2.2"/>
  <path d="M11.2 9.2 8.8 12h3.2l-2.4 2.8"/>
</svg>`,
    'silent': `
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="88" height="88"
     fill="none" stroke="#fff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
  <path d="M20.5 14.2A8.7 8.7 0 1 1 9.8 3.5a7.2 7.2 0 0 0 10.7 10.7z"/>
</svg>`,
    'balanced': `
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="88" height="88"
     fill="none" stroke="#fff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
  <path d="M3.5 16.5a8.5 8.5 0 0 1 17 0"/>
  <path d="M12 16.5V9.8"/>
  <circle cx="12" cy="16.5" r="1.3" fill="#fff" stroke="none"/>
  <path d="M6.3 11l1.2 1.2M17.7 11l-1.2 1.2"/>
</svg>`,
    'performance': `
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="88" height="88"
     fill="none" stroke="#fff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
  <path d="M12 2.8c2.7 2.2 4 5.3 4 8.6v2.4l-4 2.4-4-2.4v-2.4c0-3.3 1.3-6.4 4-8.6z"/>
  <circle cx="12" cy="9.5" r="1.7"/>
  <path d="M8 13.5l-2.6 2.9h2.9"/>
  <path d="M16 13.5l2.6 2.9h-2.9"/>
  <path d="M12 18.6v2.6"/>
</svg>`,
};

const PROFILES = [
    {id: 'super-battery', name: 'SÜPER PİL'},
    {id: 'silent', name: 'SESSİZ'},
    {id: 'balanced', name: 'DENGELİ'},
    {id: 'performance', name: 'PERFORMANS'},
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
            text: 'MSI USER SCENARIO',
            style_class: 'msi-profile-title',
            x_align: Clutter.ActorAlign.CENTER,
        });
        const row = new St.BoxLayout({
            style_class: 'msi-profile-row',
            x_align: Clutter.ActorAlign.CENTER,
        });

        this._cards = new Map();
        for (const item of PROFILES) {
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
            : state.profile;

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
            const fanText = state.boost === 'on' ? 'Maksimum' : 'Otomatik';
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
