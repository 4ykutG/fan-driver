# SPDX-License-Identifier: GPL-3.0-or-later
import importlib.machinery
import pathlib
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
doctor = importlib.machinery.SourceFileLoader(
    'msi_profile_doctor', str(ROOT / 'msi-profile-doctor')).load_module()


class DoctorTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tempdir.name)
        self.old_root = doctor.ROOT
        self.old_run = doctor.run
        doctor.ROOT = self.root
        doctor.run = lambda *command, **kwargs: None

    def tearDown(self):
        doctor.ROOT = self.old_root
        doctor.run = self.old_run
        self.tempdir.cleanup()

    def write(self, name, value):
        path = self.root / name.lstrip('/')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value + '\n', encoding='utf-8')

    def supported_hardware(self):
        self.write('/sys/class/dmi/id/sys_vendor',
                   'Micro-Star International Co., Ltd.')
        self.write('/sys/class/dmi/id/product_name', 'Thin GF63 12VE')
        self.write('/sys/devices/platform/msi-ec/fw_version', '16R8IMS1.107')
        self.write('/sys/class/hwmon/hwmon7/name', 'msi_wmi_platform')
        self.write('/sys/class/hwmon/hwmon7/fan1_input', '3609')

    def test_supported_machine(self):
        self.supported_hardware()
        report = doctor.build_report()
        self.assertTrue(report['hardware']['supported'])
        self.assertTrue(report['ec']['driver_loaded'])
        self.assertEqual(report['ec']['cpu_fan_rpm'], '3609')

    def test_unknown_firmware_is_unsupported(self):
        self.supported_hardware()
        self.write('/sys/devices/platform/msi-ec/fw_version', 'UNKNOWN.999')
        report = doctor.build_report()
        self.assertFalse(report['hardware']['supported'])

    def test_report_has_no_identity_fields(self):
        self.supported_hardware()
        report = doctor.build_report()
        flattened = dict(doctor.flatten(report))
        forbidden = {'username', 'hostname', 'serial', 'steam', 'token'}
        keys = ' '.join(flattened).lower()
        for name in forbidden:
            self.assertNotIn(name, keys)


if __name__ == '__main__':
    unittest.main()
