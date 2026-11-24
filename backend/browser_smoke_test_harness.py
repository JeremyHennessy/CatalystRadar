"""One-shot CatalystRadar PR qualification; fixture GETs on local loopback only."""
import argparse
import contextlib
from functools import partial
import hashlib
from http.server import BaseHTTPRequestHandler, SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import socket
import subprocess
from threading import Lock, Thread
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
IP = '127.0.0.1'
COHERENT = '/web/collectors.html#coherent-saved-case'
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

    def do_HEAD(self):
        self.send_response(405)
        self.send_header('Allow', 'GET')
        self.send_header('Content-Length', '0')
        self.end_headers()

    def do_GET(self):
        path = unquote(urlsplit(self.path).path, errors='strict')
        if self.path == self.server.canary_path:
            host = self.headers.get('Host')
            if host != f'{IP}:{self.server.server_port}':
                return self.send_error(400)
            self.server.canary_receipts.append((self.command, self.path, host))
            return self.fixture(self.server.canary_body, 'text/html; charset=utf-8')
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
    with ThreadingHTTPServer((IP, 0), partial(Files, directory=root)) as s:
        s.allowed, s.archive, s.legacy = paths, archive, old_html
        s.reads, s.mode = 0, 'normal'
        s.canary_path = '/__catalyst_qa__/' + secrets.token_hex(16)
        s.canary_body = (f'<!doctype html><meta charset="utf-8"><title>Catalyst QA canary</title>'
                         f'<main id="qa-canary">{s.canary_path}</main>').encode('utf-8')
        s.canary_receipts = []
        t = Thread(target=s.serve_forever, daemon=True)
        t.start()
        try:
            yield s, f'http://{IP}:{s.server_port}'
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


class RejectProxy(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def reject(self):
        self.log_denial()

    def log_denial(self):
        # Mark the specific request only after the deny response was sent.
        self.send_error(403, 'Non-loopback browsing denied by QA fixture')
        with self.server.receipt_lock:
            self.server.rejected += 1
            if self.path in self.server.canary_targets:
                self.server.canary_denials.add((self.command, self.path, 403))

    do_GET = do_HEAD = do_POST = do_CONNECT = do_OPTIONS = reject


@contextlib.contextmanager
def deny_proxy():
    with ThreadingHTTPServer((IP, 0), RejectProxy) as s:
        s.rejected = 0
        s.receipt_lock = Lock()
        s.canary_targets, s.canary_denials = set(), set()
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

    def digest(self, value):
        return self.cmd('POST', '/execute/async', {'script':
            'const done=arguments[arguments.length-1]; '
            'crypto.subtle.digest("SHA-256",new TextEncoder().encode(arguments[0]))'
            '.then(bytes=>done(Array.from(new Uint8Array(bytes),x=>x.toString(16).padStart(2,"0")).join("")),'
            '()=>done(null));', 'args': [value]})

    def goto(self, url):
        self.cmd('POST', '/url', {'url':url})

    def back(self):
        self.cmd('POST', '/back', {})

    @contextlib.contextmanager
    def disposable_tab(self):
        original = self.cmd('GET', '/window')
        canary = self.cmd('POST', '/window/new', {'type': 'tab'})['handle']
        self.cmd('POST', '/window', {'handle': canary})
        try:
            yield
        finally:
            self.cmd('DELETE', '/window')
            self.cmd('POST', '/window', {'handle': original})

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


def chrome_network_args(proxy_port, fixture_ports):
    # Chrome normally bypasses its proxy for localhost AND link-local targets.
    # Subtract the default set, then allow only the two allocated fixture ports.
    bypass = '<-loopback>;' + ';'.join(f'{IP}:{port}' for port in fixture_ports)
    return [f'--proxy-server=http://{IP}:{proxy_port}', f'--proxy-bypass-list={bypass}',
            f'--host-resolver-rules=MAP * ^NOTFOUND, EXCLUDE {IP}']


def startup_canary(d, proxy, fixtures):
    nonce = secrets.token_hex(16)
    clear_url = f'http://qa-http-{nonce}.invalid:8080/deny'
    tls_target = f'qa-tls-{nonce}.invalid:443'
    expected_denials = {('GET', clear_url, 403), ('CONNECT', tls_target, 403)}
    # Register exact unresolvable test hosts only. No production host ever used.
    with proxy.receipt_lock:
        proxy.canary_targets.update((clear_url, tls_target))

    def denied():
        with proxy.receipt_lock:
            return expected_denials <= proxy.canary_denials

    try:
        with d.disposable_tab():
            for fixture, base in fixtures:
                expected_host = f'{IP}:{fixture.server_port}'
                url = f'http://{expected_host}{fixture.canary_path}'
                need(url == base + fixture.canary_path, 'fixture canary lost pinned port')
                d.goto(url)
                need(d.js('({url:location.href, nonce:document.querySelector("#qa-canary")?.textContent, '
                          'secure:isSecureContext, crypto:typeof crypto?.subtle?.digest==="function", '
                          'nav:typeof window.navigation?.entries==="function"})') ==
                     {'url': url, 'nonce': fixture.canary_path, 'secure': True, 'crypto': True, 'nav': True},
                     'fixture did not render marker and browser APIs at pinned origin')
                need(d.digest(fixture.canary_path) == hashlib.sha256(fixture.canary_path.encode()).hexdigest(),
                     'Web Crypto did not reproduce the pinned canary SHA-256')
                need(('GET', fixture.canary_path, expected_host) in fixture.canary_receipts,
                     'fixture server did not observe its pinned GET')

            for url in (clear_url, 'https://' + tls_target + '/deny'):
                # Depending on Chrome, 403 may render normally or surface as a WebDriver
                # error. Neither outcome counts without the proxy's exact 403 receipt.
                with contextlib.suppress(RuntimeError):
                    d.goto(url)
            eventually(denied, 'proxy did not report both exact test 403 receipts', seconds=3)
    except (OSError, RuntimeError) as exc:
        raise RuntimeError(f'INFRASTRUCTURE: startup canary failed before app tests: {exc}') from exc
    print('Startup canary PASS: exact secure fixture reads, Web Crypto, Navigation API, '
          'reserved .invalid GET and CONNECT denied', flush=True)


@contextlib.contextmanager
def browser(chrome, driver, proxy, fixture_ports):
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
                     *chrome_network_args(proxy.server_port, fixture_ports)]}}}})
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
    def open_tracker():
        eventually(lambda: d.js(f'!!document.querySelector({json.dumps(selector)})'),
                   'real Coherent Tracker link not rendered')
        d.click(selector)

    open_tracker()
    eventually(lambda: verified(d), 'matching Tracker did not verify')
    need(d.js('location.hash') == '#tracker-record', 'Coherent deep link lost')
    context = d.context(width)
    if width == 390:
        d.back()  # Native WebDriver traversal; not app Backspace or a JS click.
        ideas = '/web/trade-ideas.html?snapshot=release-2'
        eventually(lambda: d.js('location.pathname+location.search') == ideas,
                   'mobile-emulated browser Back did not restore frozen Ideas URL')
        open_tracker()
        eventually(lambda: verified(d), 'mobile-emulated Tracker did not verify after browser Back')
    d.click(f'a[href="{COHERENT.removeprefix("/web/")}"]')
    eventually(lambda: d.js('location.pathname+location.hash') == COHERENT,
               'Tracker source review link did not reach the exact saved evidence')
    if not d.js('document.querySelector("#coherent-saved-case").open'):
        d.click('#coherent-saved-case > summary')
    need(d.js('document.querySelector("#coherent-saved-case").open && '
              '!!document.querySelector("#coherent-saved-case [data-cohr-cik=\"0000820318\"]") && '
              '!!document.querySelector("#coherent-saved-case [data-cohr-accession=\"0001193125-26-467737\"]")'),
         'exact CIK and accession missing from opened saved source evidence')
    d.back()
    eventually(lambda: d.js('location.pathname+location.hash') == TRACKER+'#tracker-record' and verified(d),
               'browser Back from saved evidence did not restore verified Tracker')
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
    open_tracker()
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
          'native Back (mobile-emulated), saved-source round trip, 404/corrupt/retry, '
          'legacy mixed assets PASS', flush=True)


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
    with deny_proxy() as proxy, server(a.pr213,213) as fixture213, server(a.pr209,209) as fixture209:
        fixtures = (fixture213, fixture209)
        with browser(chrome,driver,proxy,[s.server_port for s,_ in fixtures]) as d:
            startup_canary(d, proxy, fixtures)
            for checks, (s,base) in zip((tracker,command_center),fixtures,strict=True):
                for mobile in [False,True]:
                    checks(d,s,base,d.view(mobile))
            print(f'Browser non-fixture proxy requests rejected: {proxy.rejected}', flush=True)


if __name__ == '__main__':
    main()
