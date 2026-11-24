"""One-shot CatalystRadar PR qualification; fixture GETs on local loopback only."""
import argparse
import contextlib
from functools import partial
import hashlib
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
from threading import Thread
import time
from urllib.error import HTTPError
from urllib.parse import unquote, urlsplit
from urllib.request import ProxyHandler, build_opener, Request

MAIN = 'f945c1ddae74afdfc2b9674cdf1c2818a0737f2e'
PINS = {
    209: ('63415f81536946520d512ceda9e304ec5b5c4c06',
          'e487323df0c2573b33a1a877ea211e35f94958c4',
          '2880dd0864f272c1928c1193811dca3c29a722a4'),
    213: ('ad11c14e3af883de417e755a97003facbe3bc1c1',
          'a6d4f32bd9be8fd617ea94d67a9939afd07675a2',
          '0df6b2f9091631e315518d69cfbebde59e64ce75'),
}
ARCHIVE_SHA = '303486e59722e1a7059430e3b3d70219dcd10a47f9c069957169294ab8cff4a1'
ARCHIVE = f'/research/abstention-freezes/{ARCHIVE_SHA}.json'
TRACKER = '/web/trade-tracker.html'
ELEMENT = 'element-6066-11e4-a52e-4f735466cecf'
HTTP = build_opener(ProxyHandler({}))


def need(condition, description):
    if not condition:
        raise RuntimeError(description)


def verify(root, pr):
    sha, tree, head = PINS[pr]
    def git(*args):
        return subprocess.check_output(['git', '-C', root, *args], timeout=8)
    need(git('show', '-s', '--format=%H %T %P').decode().strip() ==
         f'{sha} {tree} {MAIN} {head}', f'PR {pr} exact checkout mismatch')
    need(not git('status', '--porcelain'), f'PR {pr} checkout dirty')
    raw_entries = git('ls-files', '-s', '-z', '--', 'web', 'data', 'research', 'docs').decode().split('\0')
    entries = (entry.split('\t', 1) for entry in raw_entries if entry)
    tracked = frozenset('/' + pathname for info, pathname in entries
                        if info.split(' ', 1)[0] in ('100644', '100755')
                        and (root / pathname).resolve().is_relative_to(root.resolve()))
    raw = (root / ARCHIVE[1:]).read_bytes()
    need(len(raw) == 1607 and hashlib.sha256(raw).hexdigest() == ARCHIVE_SHA, 'archive pin')
    old_html = git('show', f'{MAIN}:web/trade-tracker.html')
    need(b'id="tracker-search"' not in old_html and b'id="tracker-outcome"' in old_html,
         'old markup fixture unexpectedly changed')
    print(f'PR {pr}: commit={sha} tree={tree} parents={MAIN},{head}', flush=True)
    return tracked, raw, old_html


class Files(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Security-Policy',
                         "default-src 'self'; style-src 'self' 'unsafe-inline'; "
                         "img-src 'self' data:; object-src 'none'; base-uri 'none'")
        super().end_headers()

    def do_GET(self):
        path = unquote(urlsplit(self.path).path, errors='strict')
        if path not in self.server.allowed:
            return self.send_error(404)
        if path == ARCHIVE:
            self.server.reads += 1
            if self.server.mode == 'missing':
                return self.send_error(404)
            if self.server.mode == 'damaged':
                return self.fixture(b'!' + self.server.archive[1:], 'application/json')
        if path == TRACKER and self.server.mode == 'legacy':
            return self.fixture(self.server.legacy, 'text/html; charset=utf-8')
        super().do_GET()

    def fixture(self, data, media_type):
        self.send_response(200)
        self.send_header('Content-Type', media_type)
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)


@contextlib.contextmanager
def server(root, pr):
    paths, archive, old_html = verify(root, pr)
    with ThreadingHTTPServer(('127.0.0.1', 0), partial(Files, directory=root)) as s:
        s.allowed, s.archive, s.legacy = paths, archive, old_html
        s.reads, s.mode = 0, 'normal'
        t = Thread(target=s.serve_forever, daemon=True)
        t.start()
        try:
            yield s, f'http://127.0.0.1:{s.server_port}'
        finally:
            s.shutdown()
            t.join(timeout=3)


def eventually(f, failure, seconds=10):
    limit = time.monotonic() + seconds
    while time.monotonic() < limit:
        if f():
            return
        time.sleep(.06)
    raise RuntimeError(failure)


class RejectProxy(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def reject(self):
        self.server.rejected += 1
        self.send_error(403, 'Non-loopback browsing denied by QA fixture')

    do_GET = do_HEAD = do_POST = do_CONNECT = do_OPTIONS = reject


@contextlib.contextmanager
def deny_proxy():
    with ThreadingHTTPServer(('127.0.0.1', 0), RejectProxy) as s:
        s.rejected = 0
        t = Thread(target=s.serve_forever, daemon=True)
        t.start()
        try:
            yield s
        finally:
            s.shutdown()
            t.join(timeout=3)


class Driver:
    def __init__(self, port):
        self.base = f'http://127.0.0.1:{port}'
        self.sid = ''

    def api(self, method, path, args=None):
        data = None if args is None else json.dumps(args).encode()
        request = Request(self.base + path, data, {'Content-Type':'application/json'}, method=method)
        try:
            with HTTP.open(request, timeout=8) as reply:
                return json.load(reply)['value']
        except HTTPError as e:
            value = json.load(e).get('value', {})
            raise RuntimeError(f'WebDriver {value.get("error")}: {value.get("message")}') from None

    def cmd(self, method, path, args=None):
        return self.api(method, f'/session/{self.sid}{path}', args)

    def js(self, expression):
        return self.cmd('POST', '/execute/sync', {'script':'return ' + expression, 'args':[]})

    def goto(self, url):
        self.cmd('POST', '/url', {'url':url})

    def el(self, selector):
        return self.cmd('POST', '/element', {'using':'css selector','value':selector})[ELEMENT]

    def click(self, selector):
        self.cmd('POST', f'/element/{self.el(selector)}/click', {})

    def fill(self, selector, value, replace=True):
        eid = self.el(selector)
        if replace:
            self.cmd('POST', f'/element/{eid}/clear', {})
        if value:
            self.cmd('POST', f'/element/{eid}/value', {'text':value})

    def key(self, value):
        self.cmd('POST', '/actions', {'actions':[{'type':'key','id':'keyboard','actions':[
            {'type':'keyDown','value':value}, {'type':'keyUp','value':value}]}]})
        self.cmd('DELETE', '/actions')

    def view(self, mobile):
        width, height = (390,844) if mobile else (1366,900)
        self.cmd('POST', '/goog/cdp/execute', {'cmd':'Emulation.setDeviceMetricsOverride','params':
                 {'width':width,'height':height,'deviceScaleFactor':1,'mobile':mobile}})
        return width

    def context(self, width):
        actual = self.js('({secure:isSecureContext, crypto:!!globalThis.crypto?.subtle, '
                         'nav:!!window.navigation?.entries, width:innerWidth, '
                         'scroll:document.documentElement.scrollWidth})')
        need(actual['secure'] and actual['crypto'] and actual['nav'], f'essential browser APIs unavailable: {actual}')
        need(actual['width'] == width and actual['scroll'] <= width + 1, f'viewport or overflow: {actual}')
        return actual


@contextlib.contextmanager
def browser(chrome, driver, proxy):
    # Runner is disposable. Do not install or use Selenium Manager/browser downloads.
    with socket.socket() as temp:
        temp.bind(('127.0.0.1', 0))
        port = temp.getsockname()[1]
    chrome_ver = subprocess.check_output([chrome, '--version'], text=True, timeout=6).strip()
    driver_ver = subprocess.check_output([driver, '--version'], text=True, timeout=6).strip()
    match = lambda text: re.search(r'\b(\d+\.\d+\.\d+\.\d+)\b', text)
    need(match(chrome_ver) is not None and match(driver_ver) is not None
         and match(chrome_ver)[1] == match(driver_ver)[1], 'Chrome/ChromeDriver version mismatch')
    print(f'{chrome_ver}; {driver_ver}; ImageOS={os.getenv("ImageOS", "unknown")}; '
          f'ImageVersion={os.getenv("ImageVersion", "unknown")}', flush=True)
    with subprocess.Popen([driver, f'--port={port}', '--allowed-ips=127.0.0.1'],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) as proc:
        wd = Driver(port)
        def ready():
            need(proc.poll() is None, 'ChromeDriver exited during startup')
            try:
                return wd.api('GET', '/status').get('ready')
            except OSError:
                return False
        try:
            eventually(ready, 'ChromeDriver did not become ready', seconds=4)
            result = wd.api('POST', '/session', {'capabilities':{'alwaysMatch':{
                'browserName':'chrome','pageLoadStrategy':'eager','goog:chromeOptions':{
                    'binary':chrome, 'args':['--headless=new','--disable-background-networking',
                     '--disable-component-update','--disable-sync','--no-first-run',
                     f'--proxy-server=http://127.0.0.1:{proxy.server_port}', '--proxy-bypass-list=127.0.0.1',
                     '--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE localhost']}}}})
            wd.sid = result['sessionId']
            wd.cmd('POST','/timeouts',{'pageLoad': 8000,'script': 3000,'implicit': 0})
            yield wd
        finally:
            if wd.sid:
                with contextlib.suppress(OSError, RuntimeError):
                    wd.cmd('DELETE','')
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=3)


def verified(d, filters=True):
    return d.js('!document.querySelector("#tracker-record").hidden && '
                '!document.querySelector("#tracker-outcome").hidden && '
                '!document.querySelector("#tracker-reload").disabled && '
                'document.querySelector("#tracker-state").textContent.includes("1 archived research decision verified") && '
                + ('!document.querySelector("#tracker-filters").hidden' if filters else
                   '!document.querySelector("#tracker-filters")'))


def tracker(d, s, base, width):
    d.goto(base+'/web/trade-ideas.html?snapshot=release-2')
    selector = 'a[href="trade-tracker.html#tracker-record"]'
    eventually(lambda: d.js(f'!!document.querySelector({json.dumps(selector)})'), 'real Coherent Tracker link not rendered')
    d.click(selector)
    eventually(lambda: verified(d), 'matching Tracker did not verify')
    need(d.js('location.hash') == '#tracker-record', 'Coherent deep link lost')
    context = d.context(width)
    for term in ['Coherent','0000820318','0001193125-26-467737','data rights']:
        d.fill('#tracker-search', term)
        need(d.js('document.querySelector("#tracker-matches").textContent.includes("1 of 1")'),
             f'search failed: {term}')
    d.fill('#tracker-search','nonmatching fixture')
    need(d.js('document.querySelector("#tracker-matches").textContent.includes("No verified decisions match") && '
              'document.querySelector("#tracker-record").hidden && document.querySelector("#tracker-outcome").hidden'),
         'empty search leaked record-aware outcome')
    d.fill('#tracker-search','CoherentX')
    d.key('\ue003')
    need(d.js('document.querySelector("#tracker-search").value') == 'Coherent' and
         d.js('location.pathname') == TRACKER and verified(d), 'Backspace intercepted editable input')
    d.click('main h1')
    need(d.js('document.activeElement === document.body'), 'search did not blur to page')
    d.key('\ue003')
    eventually(lambda: d.js('location.pathname.endsWith("/trade-ideas.html")'), 'blurred Backspace did not go back')
    d.click(selector)
    eventually(lambda: verified(d), 'Tracker journey retry did not verify')
    for mode in ['missing','damaged']:
        s.mode = mode
        before = s.reads
        d.click('#tracker-reload')
        eventually(lambda: d.js('document.querySelector("#tracker-state").textContent.includes("could not be verified") && '
                               'document.querySelector("#tracker-record").hidden && document.querySelector("#tracker-outcome").hidden && '
                               'document.querySelector("#tracker-filters").hidden && !document.querySelector("#tracker-reload").disabled') and
                   s.reads == before+1, f'{mode} archive did not fail closed')
        s.mode = 'normal'
        d.click('#tracker-reload')
        eventually(lambda: verified(d), f'{mode} archive recovery failed')
    s.mode = 'legacy'
    d.goto(base+TRACKER+'?qa=legacy#tracker-record')
    eventually(lambda: verified(d, filters=False), 'baseline HTML plus current script did not verify')
    d.context(width)
    d.click('#tracker-reload')
    eventually(lambda: verified(d, filters=False), 'legacy reload failed')
    s.mode='normal'
    print(f'PR 213 {width}px {context}: linked navigation, filter/no-match, input and blurred Backspace, '
          '404/corrupt/retry, legacy mixed assets PASS', flush=True)


def command_center(d, _, base, width):
    d.goto(base+'/web/index.html')
    need(d.js('document.querySelector("h1").textContent') == 'Command Center','wrong home')
    d.key('\ue004')  # Tab
    need(d.js('document.activeElement.matches("a.skip")'),'skip link not first keyboard stop')
    d.key('\ue007')  # Enter
    need(d.js('location.hash') == '#main','skip target mismatch')
    context = d.context(width)
    for link, pathname, fragment in [
        ('trade-ideas.html','/web/trade-ideas.html',''),
        ('trade-tracker.html','/web/trade-tracker.html',''),
        ('datasets.html#company-investigation','/web/datasets.html','#company-investigation'),
        ('collectors.html','/web/collectors.html',''),
    ]:
        d.goto(base+'/web/index.html')
        selector = f'aside.sidebar nav a[href="{link}"]'
        d.click(selector)
        eventually(lambda: d.js('location.pathname+location.hash') == pathname+fragment,
                   f'Command Center route broken: {link}')
        if link == 'trade-tracker.html':
            eventually(lambda: verified(d, filters=False), 'legacy Tracker not verified after opening from #209')
    print(f'PR 209 {width}px {context}: visible Command Center, skip keyboard, four real routes, '
          'legacy Tracker integrity PASS', flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('pr213',type=Path)
    parser.add_argument('pr209',type=Path)
    parser.add_argument('--verify-only',action='store_true')
    a = parser.parse_args()
    if a.verify_only:
        for root, pr in [(a.pr213,213),(a.pr209,209)]:
            verify(root,pr)
        return
    chrome = next((p for x in ['google-chrome','google-chrome-stable','chromium'] if (p:=shutil.which(x))),None)
    driver = shutil.which('chromedriver')
    if not driver and os.environ.get('CHROMEWEBDRIVER') == '/usr/local/share/chromedriver-linux64':
        driver = shutil.which('/usr/local/share/chromedriver-linux64/chromedriver')
    need(chrome and driver, 'preinstalled Chrome and ChromeDriver required; no installation attempted')
    with deny_proxy() as proxy, browser(chrome,driver,proxy) as d:
        for root, pr, checks in [(a.pr213,213,tracker),(a.pr209,209,command_center)]:
            with server(root,pr) as (s,base):
                for mobile in [False,True]:
                    checks(d,s,base,d.view(mobile))
        print(f'Browser non-loopback proxy requests rejected: {proxy.rejected}', flush=True)


if __name__ == '__main__':
    main()
