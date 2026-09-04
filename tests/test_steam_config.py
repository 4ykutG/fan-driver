# SPDX-License-Identifier: GPL-3.0-or-later
import importlib.util
import pathlib
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    'steam_config', ROOT / 'configure-steam-cs2.py')
steam_config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(steam_config)


VDF = '''"UserLocalConfigStore"
{
    "Software"
    {
        "Valve"
        {
            "Steam"
            {
                "apps"
                {
                    "730"
                    {
                        "Playtime"        "42"
                    }
                }
            }
        }
    }
}
'''


class SteamConfigTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.path = pathlib.Path(self.tempdir.name) / 'localconfig.vdf'
        self.path.write_text(VDF, encoding='utf-8')

    def tearDown(self):
        self.tempdir.cleanup()

    def test_adds_launch_option_and_backup(self):
        self.assertTrue(steam_config.configure(self.path))
        result = self.path.read_text(encoding='utf-8')
        self.assertIn('"LaunchOptions"\t\t"msi-game-run %command%"', result)
        self.assertEqual(len(list(self.path.parent.glob('*.backup-*'))), 1)

    def test_is_idempotent(self):
        self.assertTrue(steam_config.configure(self.path))
        self.assertFalse(steam_config.configure(self.path))
        result = self.path.read_text(encoding='utf-8')
        self.assertEqual(result.count('"LaunchOptions"'), 1)

    def test_preserves_existing_arguments(self):
        text = VDF.replace(
            '                        "Playtime"        "42"',
            '                        "LaunchOptions"  "%command% -novid"\n'
            '                        "Playtime"        "42"')
        self.path.write_text(text, encoding='utf-8')
        steam_config.configure(self.path)
        result = self.path.read_text(encoding='utf-8')
        self.assertIn('"msi-game-run %command% -novid"', result)


if __name__ == '__main__':
    unittest.main()
