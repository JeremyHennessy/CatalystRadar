'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {createHash, webcrypto} = require('node:crypto');
const {loadRecord, loadCatalog, filterRecords, validateRecord, render, install, RECORD_PATH, SOURCE_SNAPSHOT, RANK_CONTEXT} = require('./trade-tracker.js');
const recordBytes = fs.readFileSync(path.join(__dirname, RECORD_PATH));

class Element {
  constructor(tag) { this.tag = tag; this.children = []; this.value = ''; }
  append(...children) { this.children.push(...children); }
  replaceChildren(...children) { this.children = children; }
  addEventListener(name, cb) { this[name] = cb; }
}
const walk = (node) => [node, ...node.children.flatMap(walk)];

(async () => {
  const subtle = webcrypto.subtle;
  const validResponse = () => new Response(recordBytes);
  let reads = 0;
  const record = await loadRecord(async (url, options) => {
    reads++;
    assert.equal(url, RECORD_PATH);
    assert.equal(options.redirect, 'error');
    return validResponse();
  }, subtle);
  assert.equal(reads, 1);
  const records = await loadCatalog(async () => validResponse(), subtle);
  assert.equal(records.length, 1);
  for (const query of ['', 'coherent', '0000820318', '0001193125-26-467737', 'data rights', 'COHERENT 0000820318'])
    assert.equal(filterRecords(records, query, 'ABSTAIN').length, 1);
  assert.equal(filterRecords(records, 'AMD', '').length, 0);
  assert.equal(filterRecords(records, 'Coherent', 'WATCH').length, 0);
  await assert.rejects(loadCatalog(async () => new Response(null, {status: 404}), subtle), /unavailable/);
  assert.equal(record.command.accession, '0001193125-26-467737');
  const snapshotBytes = fs.readFileSync(path.join(__dirname, 'trade-ideas/v1/snapshots', SOURCE_SNAPSHOT + '.json'));
  assert.equal(createHash('sha256').update(snapshotBytes).digest('hex'), record.command.snapshot_sha256);
  const sourceIdea = JSON.parse(snapshotBytes).ideas.find(x => x.id === record.command.thesis_id);
  assert.deepEqual(RANK_CONTEXT, {rank: sourceIdea.rank, score: sourceIdea.research_priority_score,
    assessedWeight: sourceIdea.coverage.known_factor_weight});
  assert.ok(sourceIdea.issuer_associations.some(x => x.issuer_cik === record.command.issuer_cik));
  assert.ok(sourceIdea.source_records.some(x => x.source_accessions.includes(record.command.accession)));
  const tamper = Buffer.from(recordBytes);
  tamper[2] ^= 1;
  await assert.rejects(loadRecord(async () => new Response(tamper), subtle), /hash mismatch/);
  for (const bytes of [recordBytes.subarray(1), Buffer.concat([recordBytes, Buffer.from('\n')])]) {
    await assert.rejects(loadRecord(async () => new Response(bytes), subtle), /length mismatch/);
  }
  await assert.rejects(loadRecord(async () => new Response(null, {status: 404}), subtle), /unavailable/);
  for (const patch of [{execution_ready: true}, {prospective_eligible: true}, {training_ready: true},
    {decision: 'BUY'}, {receipt_status: 'AUTHENTICATED'},
    {command: {...record.command, issuer_cik: '0000000001'}},
    {command: {...record.command, reasons: ['UNVERIFIED_TRADING_SESSION']}}]) {
    assert.throws(() => validateRecord({...record, ...patch}), /unexpected archived decision/);
  }

  const doc = {createElement: (tag) => new Element(tag)};
  const nodes = walk(render(doc, record));
  const presentation = nodes.map(node => node.textContent || '').join(' ');
  assert.match(presentation, /ABSTAIN · NOT ACTIONABLE/);
  assert.match(presentation, /local clock, unauthenticated 2026-11-20T14:03:03Z/);
  assert.match(presentation, /Latest verified receipt.*14:03:21Z.*14:05:23Z/);
  assert.match(presentation, /file existence only/);
  assert.match(presentation, /not a live GitHub check/);
  assert.match(presentation, /remains ineligible for prospective evaluation/);
  assert.match(presentation, /not completed repurchases/);
  assert.equal(nodes.filter(node => node.tag === 'li').length, 10);
  assert.deepEqual(nodes.filter(node => node.tag === 'a').map(a => a.href), [
    'https://github.com/JeremyHennessy/CatalystRadar/actions/runs/44749797754',
    'collectors.html#coherent-saved-case',
    'datasets.html?company_cik=0000820318#company-investigation',
    'trade-ideas.html?snapshot=release-2#research-88f4fe3fecb3853d4c6596aa',
    RECORD_PATH,
  ]);

  const elements = Object.fromEntries(['tracker-state', 'tracker-record', 'tracker-reload', 'tracker-outcome',
    'tracker-filters', 'tracker-search', 'tracker-decision', 'tracker-matches']
    .map(id => [id, new Element('test')]));
  doc.getElementById = (id) => elements[id];
  let fetchAttempts = 0;
  await install({document: doc, crypto: webcrypto, setTimeout, clearTimeout,
    fetch: async (_path, options) => {
      assert.ok(options.signal instanceof AbortSignal);
      return ++fetchAttempts === 1 ? validResponse() : new Response(tamper);
    }});
  assert.equal(elements['tracker-reload'].disabled, false);
  assert.equal(elements['tracker-record'].hidden, false);
  assert.equal(elements['tracker-outcome'].hidden, false);
  assert.match(elements['tracker-state'].textContent, /1 archived research decision verified/);
  assert.equal(elements['tracker-filters'].hidden, false);
  assert.deepEqual(elements['tracker-decision'].children.map(x => x.value), ['', 'ABSTAIN']);
  elements['tracker-search'].value = 'unknown';
  elements['tracker-search'].input();
  assert.match(elements['tracker-matches'].textContent, /No verified decisions match/);
  assert.equal(elements['tracker-outcome'].hidden, true);
  assert.match(elements['tracker-state'].textContent, /1 archived research decision verified/);
  elements['tracker-search'].value = '0000820318';
  elements['tracker-search'].input();
  elements['tracker-decision'].value = 'ABSTAIN';
  elements['tracker-decision'].change();
  assert.match(elements['tracker-matches'].textContent, /1 of 1 verified decisions/);
  assert.equal(elements['tracker-outcome'].hidden, false);
  assert.equal(fetchAttempts, 1);
  await elements['tracker-reload'].click();
  assert.equal(elements['tracker-filters'].hidden, true);
  assert.equal(elements['tracker-matches'].textContent, '');
  assert.equal(elements['tracker-record'].hidden, true);
  assert.equal(elements['tracker-outcome'].hidden, true);
  assert.deepEqual(elements['tracker-record'].children, []);
  assert.match(elements['tracker-state'].textContent, /No record or receipt is displayed/);
  assert.equal(elements['tracker-reload'].disabled, false);
  assert.equal(fetchAttempts, 2);

  const html = fs.readFileSync(path.join(__dirname, 'trade-tracker.html'), 'utf-8');
  assert.match(html, /id="tracker-record"[^>]*hidden/);
  assert.match(html, /Current outcome status/);
  assert.match(html, /No measured outcome, order, fill or return is tracked here/);
  assert.match(html, /No other decisions are tracked on this page yet/);
  assert.match(html, /trade-tracker\.js\?v=20261123-search/);
  console.log('Trade Tracker archive, fail-closed checks, clocks, links and reload tests pass.');
})().catch(error => { console.error(error); process.exitCode = 1; });
