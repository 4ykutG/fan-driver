# SPDX-License-Identifier: GPL-3.0-or-later
import importlib.machinery
import pathlib
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
monitor = importlib.machinery.SourceFileLoader(
    'msi_profile_monitor', str(ROOT / 'msi-profile-monitor')).load_module()


class MonitorTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tempdir.name)
        self.old_root = monitor.ROOT
        monitor.ROOT = self.root

    def tearDown(self):
        monitor.ROOT = self.old_root
        self.tempdir.cleanup()

    def write(self, name, value):
        path = self.root / name.lstrip('/')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value + '\n', encoding='utf-8')

    def test_sample_contains_only_hardware_telemetry(self):
        base = '/sys/devices/platform/msi-ec'
        self.write(f'{base}/fan_mode', 'auto')
        self.write(f'{base}/cooler_boost', 'on')
        self.write(f'{base}/cpu/realtime_temperature', '82')
        self.write(f'{base}/cpu/realtime_fan_speed', '150')
        self.write(f'{base}/gpu/realtime_temperature', '60')
        self.write(f'{base}/gpu/realtime_fan_speed', '0')
        self.write('/sys/class/hwmon/hwmon2/name', 'msi_wmi_platform')
        self.write('/sys/class/hwmon/hwmon2/fan1_input', '7058')
        self.write('/run/msi-profile-control/state', 'max')

        row = monitor.sample(2.5)
        self.assertEqual(tuple(row), monitor.FIELDS)
        self.assertEqual(row['selected_fan_mode'], 'max')
        self.assertEqual(row['cpu_fan_rpm'], '7058')
        forbidden = {'username', 'hostname', 'serial', 'process', 'path', 'token'}
        keys = ' '.join(row).lower()
        for name in forbidden:
            self.assertNotIn(name, keys)

    def test_bounds(self):
        self.assertEqual(monitor.bounded_float('2.5', 0.5, 60), 2.5)
        with self.assertRaises(Exception):
            monitor.bounded_float('0.1', 0.5, 60)


if __name__ == '__main__':
    unittest.main()
