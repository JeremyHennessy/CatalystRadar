"""Render a public-safe, saved observation panel. No network or collector actions."""
from datetime import datetime
from html import escape
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INPUT = 'web/collector-observation-20261118T1233Z.json'
START = '<!-- saved-observation-start -->'
END = '<!-- saved-observation-end -->'

def render(d):
    if d['schema_version'] != 1 or d['scope'] != 'SAVED_READ_ONLY_OBSERVATION_NOT_LIVE' or d['collection_triggered'] is not False or d['new_collection_verified'] is not False:
        raise ValueError('Not a read-only observation')
    if [c['id'] for c in d['collectors']] != ['sec', 'private_prices']:
        raise ValueError('Unexpected collectors')
    fallback = d['fallback']
    if fallback['status'] != 'REPORTED_CAS_ABORT_BEFORE_SUBMISSION' or fallback['source_requests'] is not None or fallback['submitted'] is not None:
        raise ValueError('Unverified fallback state')
    asof = datetime.fromisoformat(d['as_of'].replace('Z', '+00:00'))
    e = lambda value: escape(str(value), quote=True)
    out = [START, '<section class="panel" aria-labelledby="observation-title"><h2 id="observation-title">Later saved collection check</h2>', f'<p>Checked through {e(d["as_of"])} UTC. Saved evidence, not live monitoring.</p>']
    for c in d['collectors']:
        if c['dispatch_status'] != 'UNOBSERVED':
            raise ValueError('Unexpected dispatch status')
        receipt = datetime.fromisoformat(c['latest_successful_receipt'])
        seconds = int((asof - receipt).total_seconds())
        if seconds < 0 or any(datetime.fromisoformat(s.replace('Z', '+00:00')) > asof for s in c['slots_utc']):
            raise ValueError('Future observation')
        prefix = 'https://github.com/JeremyHennessy/' + ('CatalystRadar' if c['id'] == 'sec' else 'CatalystRadar-Private') + '/actions/runs/'
        if not c['latest_run_url'].startswith(prefix) or not c['latest_run_url'][len(prefix):].isdigit():
            raise ValueError('Unexpected source URL')
        out += [f'<h3>{e(c["name"])}</h3><p><strong>Scheduled dispatch unobserved, not a source failure.</strong> Configured slots checked: {e(", ".join(c["slots_utc"]))}.</p>', f'<p>Last successful saved receipt: {e(c["latest_successful_receipt"])} ({seconds // 3600}h {(seconds % 3600) // 60}m old at this checkpoint). {e(c["coverage"])}</p>', f'<p>{e(c["latest_run_status"])} {e(c["publication_status"])}</p><a href="{e(c["latest_run_url"])}">Inspect latest reviewed workflow run{ " (private access required)" if c["id"] == "private_prices" else ""} ↗</a>']
    out += ['<h3>Reported fallback preparation stop · execution receipt unavailable</h3>', f'<p>{e(fallback["explanation"])}</p>', '<ul>' + ''.join('<li>' + e(x) + '</li>' for x in d['limitations']) + '</ul>', f'<a href="{INPUT.removeprefix("web/")}">Read this saved observation and source references ↗</a></section>', END]
    return '\n'.join(out)

if __name__ == '__main__':
    panel = render(json.loads((ROOT / INPUT).read_text()))
    path = ROOT / 'web/collectors.html'
    html = path.read_text()
    if START in html:
        html = html[:html.index(START)] + panel + html[html.index(END)+len(END):]
    else:
        html = html.replace('<section class="panel"><h2>Workflow', panel + '<section class="panel"><h2>Workflow', 1)
        if START not in html:
            # Keep the existing workflow audit and its scripts untouched.
            pos = html.index('<section class="panel">', html.index('</section>'))
            html = html[:pos] + panel + html[pos:]
    path.write_text(html)
