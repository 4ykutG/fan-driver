# SPDX-License-Identifier: GPL-3.0-or-later
import importlib.machinery
import pathlib
import unittest
from unittest import mock


ROOT = pathlib.Path(__file__).resolve().parents[1]
hotkeyd = importlib.machinery.SourceFileLoader(
    'msi_profile_hotkeyd_state', str(ROOT / 'msi-profile-hotkeyd')).load_module()


def result(profile='performance', boost='on'):
    return {
        'result': 'applied',
        'profile': profile,
        'temp': '70',
        'fan': 'auto',
        'boost': boost,
        'message': 'ok',
    }


class DaemonStateTests(unittest.TestCase):
    def setUp(self):
        self.daemon = hotkeyd.HotkeyDaemon()
        self.daemon.game_active = False
        self.events = []
        self.daemon.publish = (
            lambda phase, **fields: self.events.append((phase, fields)))

    def tearDown(self):
        self.daemon.selector.close()

    @mock.patch.object(hotkeyd, 'log')
    @mock.patch.object(hotkeyd, 'running_games', return_value=['cs2'])
    def test_game_start_locks_performance(self, _games, _log):
        with mock.patch.object(
                hotkeyd, 'run_backend', return_value=result()) as backend:
            self.daemon.scan_game_state()

        backend.assert_called_once_with('game-start')
        self.assertTrue(self.daemon.game_active)
        self.assertEqual(self.daemon.current, 'performance')
        self.assertEqual(self.events[-1][0], 'applied')
        self.assertEqual(self.events[-1][1]['message'], 'Oyun modu: cs2')

    @mock.patch.object(hotkeyd, 'log')
    @mock.patch.object(hotkeyd, 'running_games', return_value=[])
    def test_game_exit_uses_grace_period(self, _games, _log):
        self.daemon.game_active = True
        clock = {'now': 100.0}

        def backend_call(action):
            self.assertEqual(action, 'game-stop')
            return result('balanced', 'off')

        with mock.patch.object(
                hotkeyd.time, 'monotonic', side_effect=lambda: clock['now']), \
                mock.patch.object(hotkeyd, 'run_backend',
                                  side_effect=backend_call) as backend:
            self.daemon.scan_game_state()
            self.assertEqual(backend.call_count, 0)
            clock['now'] = 107.9
            self.daemon.scan_game_state()
            self.assertEqual(backend.call_count, 0)
            clock['now'] = 108.0
            self.daemon.scan_game_state()

        backend.assert_called_once_with('game-stop')
        self.assertFalse(self.daemon.game_active)
        self.assertEqual(self.daemon.current, 'balanced')
        self.assertEqual(self.events[-1][1]['message'],
                         'Oyun kapandı: Dengeli mod')

    def test_initial_sync_publishes_readable_state(self):
        with mock.patch.object(
                hotkeyd, 'run_backend',
                return_value=result('balanced', 'off')):
            self.daemon.sync_current()

        self.assertEqual(self.daemon.current, 'balanced')
        self.assertEqual(self.events[-1][0], 'sync')
        self.assertEqual(self.events[-1][1]['profile'], 'balanced')


if __name__ == '__main__':
    unittest.main()
