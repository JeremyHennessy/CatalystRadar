# Local TXMD companion verification

The complete original response is retained separately and is not published with this note.
The public note is a narrow paraphrase of the issuer's statements, not a complete
financial analysis, payment confirmation or outcome qualification. The optional
milestone-share calculation is deliberately omitted. The separate existing 8-K
publisher-clock sidecar is hash-bound, not rewritten. Its acceptance clock and the
10-Q header yield a 122-second difference, not a public disclosure ordering.
Index URLs are references, not claims that index response bytes were retained.

## Original reproduction

Run the following manually against the retained complete submission and this
checkout. `lxml` is used only for this manual verification, not a new CI dependency.
The exact full response is pinned before parsing. Only the unique primary 10-Q
HTML contributes text. Offsets are Unicode character positions in whitespace-
normalized `text_content()`, and hashes cover UTF-8 substrings, NOT raw bytes.
The primary HTML hash covers the exact raw `<html` through `</html>` byte slice.

```python
import hashlib, json, re
from pathlib import Path
from lxml import html
raw = Path('0001213900-26-119697.txt').read_bytes()
note = json.loads(Path('web/company-findings/txmd-companion-10q.json').read_text())
assert len(raw) == note['source']['raw_bytes']
assert hashlib.sha256(raw).hexdigest() == note['source']['raw_sha256']
assert b'<ACCEPTANCE-DATETIME>20261113160749' in raw
assert b'0001213900-26-119697' in raw.split(b'<DOCUMENT>', 1)[0]
docs = list(re.finditer(rb'<DOCUMENT>.*?</DOCUMENT>', raw, re.S))
selected = [d for d in docs if re.search(rb'<TYPE>10-Q\s', d[0].split(b'<TEXT>',1)[0])]
assert len(selected) == 1
primary = selected[0][0]
assert b'<FILENAME>ea0308826-10q_therapeutics.htm' in primary.split(b'<TEXT>',1)[0]
body = primary[primary.index(b'<html'):primary.rindex(b'</html>')+7]
assert hashlib.sha256(body).hexdigest() == note['source']['primary_html_sha256']
normalized = ' '.join(html.fromstring(body).text_content().split())
for key, span in note['source']['evidence_spans'].items():
    text = normalized[span['normalized_character_start']:span['normalized_character_end']]
    assert hashlib.sha256(text.encode('utf-8')).hexdigest() == span['normalized_utf8_sha256'], key
print('Verified original, primary HTML, header and all three source spans')
```

The author executed this verification on the actual 4,487,035-byte retained
response. Automated fixture-free tests separately verify the source pins, unchanged
8-K clock sidecar, milestone-year/recognition distinctions, no readiness promotion
and displayed caveats. They do not stand in for original-document review.
