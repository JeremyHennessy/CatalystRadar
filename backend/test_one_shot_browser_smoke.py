"""Candidate integration for the existing CI test discovery, QA branch only."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

QA_REF = 'refs/heads/qa/catalyst-render-20261124'
GATE = {
    'GITHUB_ACTIONS': 'true',
    'GITHUB_EVENT_NAME': 'push',
    'GITHUB_REF': QA_REF,
    'GITHUB_REPOSITORY': 'JeremyHennessy/CatalystRadar',
    'GITHUB_RUN_ATTEMPT': '1',
    'GITHUB_WORKFLOW': 'Validate paper-only application',
}
PUBLIC_REMOTE = 'https://github.com/JeremyHennessy/CatalystRadar.git'
MAIN = 'f945c1ddae74afdfc2b9674cdf1c2818a0737f2e'


class OneShotBrowserSmoke(unittest.TestCase):
    def test_exact_two_preview_trees(self):
        if any(os.environ.get(key) != value for key,value in GATE.items()):
            self.skipTest('isolated CatalystRadar public QA branch, first push execution only')
        event_path = Path(os.environ['GITHUB_EVENT_PATH'])
        with event_path.open('rb') as file:
            payload = file.read(1_000_001)
        self.assertLessEqual(len(payload), 1_000_000)
        event = json.loads(payload)
        creation = event.get('created') is True and event.get('before') == '0' * 40
        first_ff = event.get('created') is False and event.get('before') == MAIN
        if (not (creation or first_ff) or event.get('deleted') is not False
                or event.get('ref') != QA_REF or event.get('after') != os.environ['GITHUB_SHA']):
            self.skipTest('only creation or first fast-forward from pinned main is eligible')
        self.assertEqual(os.environ.get('RUNNER_ENVIRONMENT'), 'github-hosted')
        self.assertEqual(os.environ.get('RUNNER_OS'), 'Linux')
        deadline = time.monotonic() + 180

        def budget(seconds):
            left = deadline - time.monotonic()
            self.assertGreater(left, 0, 'hosted smoke time budget exhausted')
            return min(seconds, left)

        with tempfile.TemporaryDirectory(prefix='catalyst-public-browser-') as tmp:
            temp = Path(tmp)
            env = {key: os.environ[key] for key in ('PATH', 'SSL_CERT_FILE', 'SSL_CERT_DIR')
                   if key in os.environ}
            env.update(HOME=tmp, XDG_CONFIG_HOME=tmp, GIT_CONFIG_NOSYSTEM='1',
                       GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_COUNT='0',
                       GIT_TERMINAL_PROMPT='0', GIT_ASKPASS='/bin/false')

            def git(*args, capture=False, seconds=10):
                result = subprocess.run(['git', *map(str, args)], cwd=temp, env=env,
                                        check=True, timeout=budget(seconds), capture_output=capture)
                return result.stdout.decode().strip() if capture else None

            git('init','--quiet','repo')
            git('-C','repo','fetch','--quiet','--no-tags','--depth=2',PUBLIC_REMOTE,
                '+refs/heads/main:refs/qa/main',
                '+refs/pull/209/merge:refs/qa/209',
                '+refs/pull/213/merge:refs/qa/213',seconds=30)
            self.assertEqual(git('-C','repo','rev-parse','refs/qa/main',capture=True),MAIN)
            for pr in (209,213):
                git('-C','repo','worktree','add','--quiet','--detach',
                    temp/f'pr{pr}',f'refs/qa/{pr}')
            # No GitHub credentials forwarded to the browser/loopback fixtures.
            smoke_env = {key: os.environ[key] for key in
                         ('PATH', 'ImageOS', 'ImageVersion', 'LANG', 'LC_ALL', 'CHROMEWEBDRIVER')
                         if key in os.environ}
            smoke_env.update(HOME=tmp, XDG_CONFIG_HOME=tmp)
            sys.stdout.flush()
            subprocess.run([sys.executable,'-B',
                str(Path(__file__).with_name('browser_smoke_test_harness.py')),
                str(temp/'pr213'),str(temp/'pr209')],env=smoke_env,cwd=temp,
                check=True,timeout=budget(130))
