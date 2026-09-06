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

    def test_valid_guard_interval(self):
        self.path.write_text('[daemon]\nguard_interval = 30\n', encoding='utf-8')
        self.assertEqual(hotkeyd.read_settings(), {'guard_interval': 30.0})

    def test_invalid_guard_interval_uses_default(self):
        self.path.write_text('[daemon]\nguard_interval = 99999\n', encoding='utf-8')
        self.assertEqual(hotkeyd.read_settings(), {
            'guard_interval': hotkeyd.GUARD_INTERVAL})

    def test_missing_file_uses_default(self):
        self.assertEqual(hotkeyd.read_settings(), {
            'guard_interval': hotkeyd.GUARD_INTERVAL})


if __name__ == '__main__':
    unittest.main()
