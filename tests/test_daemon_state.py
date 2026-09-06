# SPDX-License-Identifier: GPL-3.0-or-later
import importlib.machinery
import pathlib
import unittest
from unittest import mock


ROOT = pathlib.Path(__file__).resolve().parents[1]
hotkeyd = importlib.machinery.SourceFileLoader(
    'msi_profile_hotkeyd_state', str(ROOT / 'msi-profile-hotkeyd')).load_module()


def result(mode='auto', boost='off', message='ok'):
    return {
        'result': 'applied', 'mode': mode, 'profile': mode,
        'temp': '70', 'fan': 'silent' if mode == 'silent' else 'auto',
        'boost': boost, 'message': message,
    }


class DaemonStateTests(unittest.TestCase):
    def setUp(self):
        self.daemon = hotkeyd.HotkeyDaemon()
        self.events = []
        self.daemon.publish = (
            lambda phase, **fields: self.events.append((phase, fields)))

    def tearDown(self):
        self.daemon.selector.close()

    def test_initial_sync_publishes_fan_mode(self):
        with mock.patch.object(hotkeyd, 'run_backend',
                               return_value=result('silent')):
            self.daemon.sync_current()
        self.assertEqual(self.daemon.current, 'silent')
        self.assertEqual(self.events[-1][0], 'sync')
        self.assertEqual(self.events[-1][1]['mode'], 'silent')

    def test_fn_f7_cycles_only_three_fan_modes(self):
        self.daemon.current = 'auto'
        with mock.patch.object(hotkeyd.time, 'monotonic', return_value=10):
            self.daemon.handle_press()
        self.assertEqual(self.daemon.pending, 'silent')
        self.assertEqual(self.events[-1][1]['selected'], 'silent')

        with mock.patch.object(hotkeyd, 'run_backend',
                               return_value=result('silent')) as backend:
            self.daemon.commit()
        backend.assert_called_once_with('set', 'silent')
        self.assertEqual(self.daemon.current, 'silent')

    def test_guard_publishes_automatic_boost_transition(self):
        self.daemon.current = 'silent'
        self.daemon.last_boost = 'off'
        hot = result('silent', 'on', '90°C üzeri: Cooler Boost')
        with mock.patch.object(hotkeyd, 'run_backend', return_value=hot):
            self.daemon.run_guard()
        self.assertEqual(self.events[-1][0], 'applied')
        self.assertEqual(self.events[-1][1]['boost'], 'on')


if __name__ == '__main__':
    unittest.main()
