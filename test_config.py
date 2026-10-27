import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


class ConfigTests(unittest.TestCase):
    def run_isolated(self, script, config=None):
        with tempfile.TemporaryDirectory() as folder:
            for name in ('Tool.py', 'ToolDesktop.py'):
                shutil.copyfile(Path(__file__).parent / name, Path(folder) / name)
            if config is not None:
                (Path(folder) / 'config.local.json').write_text(
                    json.dumps(config), encoding='utf-8')
            return subprocess.run([sys.executable, '-c', script], cwd=folder,
                                  capture_output=True, text=True, encoding='utf-8')

    def test_checkout_without_local_config_has_no_credentials(self):
        result = self.run_isolated('''
import Tool
import ToolDesktop
assert Tool.GAME_KEY == '' and Tool.SECRET_KEY == ''
assert Tool.LIVE_EVENTS_FILE == Tool.os.path.join(Tool.BASE_DIR, 'live-events.json')
config = ToolDesktop.RunConfig()
config.validate()
config.dry_run = False
try:
    config.validate()
except ValueError:
    pass
else:
    raise AssertionError('Missing credentials accepted')
''')
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_local_config_reaches_cli_desktop_and_event_payload(self):
        result = self.run_isolated('''
import Tool
import ToolDesktop
assert Tool.GAME_KEY == 'test-game' and Tool.SECRET_KEY == 'test-secret'
assert ToolDesktop.RunConfig().game_key == 'test-game'
generator = Tool.ScalableAndroidTrafficGenerator(Tool.GAME_KEY, Tool.SECRET_KEY)
payload = generator._create_event_payload('user', {'user_id': 'test-user'}, 'test-session', 1)[0]
assert payload['android_bundle_id'] == 'com.example.test'
assert payload['android_app_signature'] == 'test-signature'
assert payload['build'] == 'test-build'
assert Tool.LIVE_EVENTS_FILE == Tool.os.path.join(Tool.BASE_DIR, 'sample-events.json')
''', dict(game_key='test-game', secret_key='test-secret',
          android_bundle_id='com.example.test', android_app_signature='test-signature',
          build='test-build', live_events_file='sample-events.json'))
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_invalid_config_is_rejected_without_echoing_values(self):
        for config in ([], {'secret_key': ['sensitive-test-value']}):
            with self.subTest(config_type=type(config).__name__):
                result = self.run_isolated('import Tool', config)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('config.local.json', result.stderr)
                self.assertNotIn('sensitive-test-value', result.stderr)

    def test_cli_without_credentials_stops_before_sending(self):
        result = self.run_isolated('''
import runpy
from unittest.mock import patch
with patch('requests.post', side_effect=AssertionError('Network forbidden')):
    runpy.run_path('Tool.py', run_name='__main__')
''')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('config.local.json', result.stderr)
        self.assertNotIn('Network forbidden', result.stderr)


if __name__ == '__main__':
    unittest.main()
