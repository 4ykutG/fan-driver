# SPDX-License-Identifier: GPL-3.0-or-later
import importlib.machinery
import os
import pathlib
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
hotkeyd = importlib.machinery.SourceFileLoader(
    'msi_profile_hotkeyd', str(ROOT / 'msi-profile-hotkeyd')).load_module()


class GameDetectionTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.proc = pathlib.Path(self.tempdir.name) / 'proc'
        self.proc.mkdir()
        self.old_proc_root = hotkeyd.PROC_ROOT
        hotkeyd.PROC_ROOT = str(self.proc)

    def tearDown(self):
        hotkeyd.PROC_ROOT = self.old_proc_root
        self.tempdir.cleanup()

    def process(self, pid, exe, environ=b'', cmdline=b''):
        directory = self.proc / str(pid)
        directory.mkdir()
        (directory / 'exe').symlink_to(exe)
        (directory / 'environ').write_bytes(environ)
        (directory / 'cmdline').write_bytes(cmdline)

    def test_native_steam_game(self):
        self.process(100, '/home/user/.local/share/Steam/steamapps/common/Game/bin/game')
        self.assertEqual(hotkeyd.process_game_label('100', set()), 'game')

    def test_steam_runtime_helper_is_ignored(self):
        self.process(
            101,
            '/home/user/.local/share/Steam/steamapps/common/'
            'SteamLinuxRuntime_sniper/pressure-vessel/bin/pressure-vessel-wrap')
        self.assertIsNone(hotkeyd.process_game_label('101', set()))

    def test_proton_game_uses_steam_app_id(self):
        self.process(
            102,
            '/home/user/.local/share/Steam/steamapps/common/'
            'SteamLinuxRuntime_sniper/var/wine64-preloader',
            b'SteamAppId=12345\0',
            b'wine64-preloader\0Z:\\game.exe\0')
        self.assertEqual(hotkeyd.process_game_label('102', set()), 'Steam 12345')

    def test_explicit_non_steam_game(self):
        self.process(103, '/opt/games/my-game')
        self.assertEqual(
            hotkeyd.process_game_label('103', {'my-game'}), 'my-game')

    def test_unrelated_process_environment_is_not_read(self):
        self.process(
            106, '/usr/bin/bash', b'SteamAppId=730\0',
            b'bash\0/home/user/steamapps/common/Game/game.exe\0')
        original_reader = hotkeyd.read_proc_file

        def reject_environment_read(pid, name, **kwargs):
            if name == 'environ':
                self.fail('unrelated process environment was read')
            return original_reader(pid, name, **kwargs)

        hotkeyd.read_proc_file = reject_environment_read
        try:
            self.assertIsNone(hotkeyd.process_game_label('106', set()))
        finally:
            hotkeyd.read_proc_file = original_reader

    def test_running_games_is_unique_and_sorted(self):
        self.process(104, '/opt/games/zeta')
        self.process(105, '/opt/games/alpha')
        old_reader = hotkeyd.read_configured_games
        hotkeyd.read_configured_games = lambda: {'zeta', 'alpha'}
        try:
            self.assertEqual(hotkeyd.running_games(), ['alpha', 'zeta'])
        finally:
            hotkeyd.read_configured_games = old_reader


if __name__ == '__main__':
    unittest.main()
