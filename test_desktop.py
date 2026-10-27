import json
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import ToolDesktop as desktop


class DesktopTests(unittest.TestCase):
    def config(self, **kwargs):
        kwargs.setdefault('game_key', 'test-game')
        kwargs.setdefault('secret_key', 'test-secret')
        return desktop.RunConfig(duration_min=0.001, duration_max=0.001,
                                 action_min=0.001, action_max=0.001, **kwargs)

    def test_invalid_counts_and_times_are_rejected(self):
        for values in ({'users': 0}, {'sessions': 0}, {'workers': 0},
                       {'duration_min': 10, 'duration_max': 1},
                       {'action_min': float('nan')}, {'returning_percent': 101}):
            with self.subTest(values=values), self.assertRaises(ValueError):
                desktop.RunConfig(**values).validate()

    def test_json_returning_keeps_highest_session_and_lifetime(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'events.json'
            source.write_text(json.dumps([
                {'user_id': 'existing', 'session_num': 4, 'lifetime_session_length': 50},
                {'user_id': 'existing', 'session_num': 2, 'lifetime_session_length': 100}
            ]), encoding='utf-8')
            config = self.config(mode='json', json_path=str(source))
            runner = desktop.DesktopRunner(config, Path(folder) / 'state.txt')
            active, roster = runner.prepare()
            self.assertEqual(len(active), 1)
            self.assertEqual(active[0]['user_id'], 'existing')
            self.assertEqual(active[0]['session_num'], 4)
            self.assertEqual(active[0]['lifetime_session_length'], 100)

    def test_insufficient_returning_does_not_create_users(self):
        with tempfile.TemporaryDirectory() as folder:
            runner = desktop.DesktopRunner(self.config(mode='saved'), Path(folder) / 'state.txt')
            with self.assertRaisesRegex(ValueError, 'user'):
                runner.prepare()

    def test_dry_run_never_sends_and_does_not_change_real_state(self):
        with tempfile.TemporaryDirectory() as folder:
            state = Path(folder) / 'state.txt'
            state.write_text('old,2,1,samsung,SM-G781N,android 13,10\n', encoding='utf-8')
            before = state.read_bytes()
            runner = desktop.DesktopRunner(self.config(sessions=2), state)
            with patch('Tool.requests.post', side_effect=AssertionError('Network forbidden')):
                result = runner.run()
            self.assertEqual(result['completed'], 2)
            self.assertEqual(state.read_bytes(), before)

    def test_real_mode_persists_each_completed_session(self):
        with tempfile.TemporaryDirectory() as folder:
            state = Path(folder) / 'state.txt'
            runner = desktop.DesktopRunner(self.config(dry_run=False, sessions=2), state)
            with patch('Tool.ScalableAndroidTrafficGenerator._send'):
                result = runner.run()
            self.assertEqual(result['completed'], 2)
            self.assertEqual(state.read_text().split(',')[1], '2')

    def test_stop_before_start_creates_no_sessions(self):
        with tempfile.TemporaryDirectory() as folder:
            stop = threading.Event()
            stop.set()
            runner = desktop.DesktopRunner(self.config(), Path(folder) / 'state.txt', stop=stop)
            self.assertEqual(runner.run()['completed'], 0)

    def test_stop_interrupts_active_session_and_skips_remaining(self):
        with tempfile.TemporaryDirectory() as folder:
            stop = threading.Event()
            runner = desktop.DesktopRunner(desktop.RunConfig(sessions=3),
                                           Path(folder) / 'state.txt', stop=stop)
            started = time.monotonic()
            timer = threading.Timer(0.05, stop.set)
            timer.start()
            try:
                result = runner.run()
            finally:
                timer.cancel()
            self.assertEqual(result['completed'], 1)
            self.assertLess(time.monotonic() - started, 2)

    def test_session_end_failure_does_not_advance_saved_state(self):
        with tempfile.TemporaryDirectory() as folder:
            state = Path(folder) / 'state.txt'
            state.write_text('old,2,1,samsung,SM-G781N,android 13,10\n', encoding='utf-8')
            before = state.read_bytes()
            runner = desktop.DesktopRunner(self.config(mode='saved', dry_run=False), state)

            def send(endpoint, payload):
                if isinstance(payload, list) and payload[0]['category'] == 'session_end':
                    raise RuntimeError('Simulated server failure')

            with patch.object(runner.generator, '_send', side_effect=send):
                result = runner.run()
            self.assertEqual(result, {'completed': 0, 'failed': 1})
            self.assertEqual(state.read_bytes(), before)

    def test_new_mode_preserves_unselected_existing_users(self):
        with tempfile.TemporaryDirectory() as folder:
            state = Path(folder) / 'state.txt'
            state.write_text('old,2,1,samsung,SM-G781N,android 13,10\n', encoding='utf-8')
            runner = desktop.DesktopRunner(self.config(dry_run=False), state)
            with patch('Tool.ScalableAndroidTrafficGenerator._send'):
                runner.run()
            lines = state.read_text().splitlines()
            self.assertEqual(len(lines), 2)
            old = lines[0].split(',')
            self.assertEqual(old[:2], ['old', '2'])
            self.assertEqual(float(old[2]), 1)
            self.assertEqual(old[3:], ['samsung', 'SM-G781N', 'android 13', '10'])

    def test_json_rejects_wrong_shape(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'events.json'
            source.write_text('{"events": []}', encoding='utf-8')
            runner = desktop.DesktopRunner(self.config(mode='json', json_path=str(source)),
                                           Path(folder) / 'state.txt')
            with self.assertRaises(ValueError):
                runner.prepare()

    def test_mixed_counts_and_pool_cap(self):
        with tempfile.TemporaryDirectory() as folder:
            state = Path(folder) / 'state.txt'
            state.write_text('old,2,1,samsung,SM-G781N,android 13,10\n', encoding='utf-8')
            runner = desktop.DesktopRunner(self.config(mode='mixed', users=2, returning_percent=50), state)
            active, roster = runner.prepare()
            self.assertEqual(len(active), 2)
            self.assertEqual(sum(p['session_num'] > 0 for p in active), 1)
            with patch('ToolDesktop.MAX_TOTAL_USERS', 1), self.assertRaises(ValueError):
                runner.prepare()


if __name__ == '__main__':
    unittest.main()
