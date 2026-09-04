# SPDX-License-Identifier: GPL-3.0-or-later
import importlib.machinery
import pathlib
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
hotkeyd = importlib.machinery.SourceFileLoader(
    'msi_profile_hotkeyd_settings', str(ROOT / 'msi-profile-hotkeyd')).load_module()


class SettingsTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.path = pathlib.Path(self.tempdir.name) / 'settings.conf'
        self.old_path = hotkeyd.CONFIG_FILE
        hotkeyd.CONFIG_FILE = str(self.path)

    def tearDown(self):
        hotkeyd.CONFIG_FILE = self.old_path
        self.tempdir.cleanup()

    def test_valid_settings(self):
        self.path.write_text(
            '[daemon]\n'
            'game_scan_interval = 1.5\n'
            'game_exit_delay = 12\n'
            'guard_interval = 30\n', encoding='utf-8')
        self.assertEqual(hotkeyd.read_settings(), {
            'game_scan_interval': 1.5,
            'game_exit_delay': 12.0,
            'guard_interval': 30.0,
        })

    def test_invalid_and_out_of_range_values_use_defaults(self):
        self.path.write_text(
            '[daemon]\n'
            'game_scan_interval = 0.01\n'
            'game_exit_delay = not-a-number\n'
            'guard_interval = 99999\n', encoding='utf-8')
        self.assertEqual(hotkeyd.read_settings(), {
            'game_scan_interval': hotkeyd.GAME_SCAN_INTERVAL,
            'game_exit_delay': hotkeyd.GAME_EXIT_DELAY,
            'guard_interval': hotkeyd.GUARD_INTERVAL,
        })

    def test_missing_file_uses_defaults(self):
        self.assertEqual(hotkeyd.read_settings(), {
            key: limits[0] for key, limits in hotkeyd.SETTING_RANGES.items()
        })


if __name__ == '__main__':
    unittest.main()
