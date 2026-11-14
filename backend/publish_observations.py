"""Explicitly rebuild existing branch-source Pages after a token-authored push.

No Pages settings changes, PAT, raw prices, or trading. Fail closed if publishing
source changed, commit is superseded, build fails, or served JSON differs.
"""
import hashlib
import json
import re
import subprocess
import time
from pathlib import Path
from urllib.request import urlopen

REPOSITORY = 'JeremyHennessy/CatalystRadar'
SITE = 'https://jeremyhennessy.github.io/CatalystRadar/web/app-data.json'


def publish(expected, payload, api, fetch, sleep=time.sleep, attempts=30):
    if not re.fullmatch(r'[0-9a-f]{40}', expected):
        raise ValueError('Expected exact commit SHA')
    config = api('GET', '/pages')
    if config.get('build_type', 'legacy') != 'legacy' or config.get('source') != {'branch': 'main', 'path': '/'}:
        raise RuntimeError('Existing Pages source differs; no settings were changed')
    if api('GET', '/git/ref/heads/main')['object']['sha'] != expected:
        raise RuntimeError('Public main advanced; refusing a mismatched build')
    api('POST', '/pages/builds')
    digest = hashlib.sha256(payload).digest()
    for attempt in range(attempts):
        build = api('GET', '/pages/builds/latest')
        if build.get('commit') == expected:
            if build.get('status') == 'errored' or (build.get('error') or {}).get('message'):
                raise RuntimeError('Pages build failed')
            if build.get('status') == 'built':
                if hashlib.sha256(fetch(SITE + '?commit=' + expected)).digest() == digest:
                    return expected
        if attempt + 1 < attempts:
            sleep(10)
    raise RuntimeError('Exact Pages commit and served dashboard were not verified before timeout')


def github_api(method, suffix):
    result = subprocess.run(['gh', 'api', '--method', method,
                             f'repos/{REPOSITORY}{suffix}'],
                            check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def fetch(url):
    with urlopen(url, timeout=20) as response:
        return response.read()


if __name__ == '__main__':
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    publish(head, Path('web/app-data.json').read_bytes(), github_api, fetch)
    print('Verified exact public commit and served dashboard JSON; paper-only.')
