(function (host) {
  'use strict';

  const RECORD_SHA = '303486e59722e1a7059430e3b3d70219dcd10a47f9c069957169294ab8cff4a1';
  const RECORD_BYTES = 1607;
  const RECORD_PATH = '../research/abstention-freezes/' + RECORD_SHA + '.json';
  const CIK = '0000820318';
  const ACCESSION = '0001193125-26-467737';
  const THESIS = 'research-88f4fe3fecb3853d4c6596aa';
  const SOURCE_SNAPSHOT = '28e8b1d7b80a34de480ad03e9bdf7a5d18b65fdf5816239968f2f2fd52e6196a';
  const RANK_CONTEXT = Object.freeze({rank: 1, score: 80, assessedWeight: 80});
  const REASONS = Object.freeze({
    MISSING_MARKET_DATA: 'Qualified market data is missing',
    UNVERIFIED_CORPORATE_ACTIONS: 'Corporate-action continuity is unverified',
    UNVERIFIED_DATA_RIGHTS: 'Data use rights are unverified',
    UNVERIFIED_SECURITY_IDENTITY: 'Effective-dated security identity is unverified',
    UNVERIFIED_SOURCE_AVAILABILITY: 'Historical source availability is unverified',
    UNVERIFIED_TRADING_SESSION: 'Actual trading-session evidence is unverified',
  });

  // Separately verified via authenticated GitHub API; not a browser API lookup.
  // This is one saved existence bound for RECORD_SHA, not a statement of live run status.
  const RECEIPT = Object.freeze({
    recordSha: RECORD_SHA,
    runId: '44749797754',
    head: '37fe448d8841310c7e61baa7280a7dc8b2457712',
    createdUtc: '2026-11-20T14:03:21Z',
    checkedUtc: '2026-11-20T14:05:23Z',
  });

  async function readBounded(response, expectedBytes) {
    if (!response.ok || !response.body) throw new Error('archive unavailable');
    const reader = response.body.getReader();
    const bytes = new Uint8Array(expectedBytes);
    let size = 0;
    try {
      for (;;) {
        const {done, value} = await reader.read();
        if (done) break;
        if (size + value.byteLength > bytes.length) throw new Error('archive length mismatch');
        bytes.set(value, size);
        size += value.byteLength;
      }
      if (size !== bytes.length) throw new Error('archive length mismatch');
      return bytes;
    } catch (error) {
      await reader.cancel().catch(() => {});
      throw error;
    } finally {
      reader.releaseLock();
    }
  }

  function validateRecord(record) {
    const command = record?.command;
    if (record?.version !== 1 || record.sequence !== 1 || record.decision !== 'ABSTAIN' ||
        record.clock_basis !== 'LOCAL_SYSTEM_CLOCK_NOT_AUTHENTICATED' ||
        record.timing_status !== 'LOCAL_CLOCK_BEFORE_DEADLINE_UNAUTHENTICATED' ||
        record.receipt_status !== 'MISSING' || record.prospective_eligible !== false ||
        record.execution_ready !== false || record.training_ready !== false ||
        record.recorded_utc !== '2026-11-20T14:03:03Z' ||
        command?.command_id !== 'coherent-abstain-20261120' ||
        command.issuer_cik !== CIK || command.accession !== ACCESSION ||
        command.thesis_id !== THESIS || command.receipt_pin !== null ||
        command.deadline_utc !== '2026-11-20T21:00:00Z' ||
        command.snapshot_sha256 !== SOURCE_SNAPSHOT ||
        command.snapshot_cutoff_utc !== '2026-11-19T20:10:08Z' ||
        JSON.stringify(command.reasons) !== JSON.stringify(Object.keys(REASONS))) {
      throw new Error('unexpected archived decision');
    }
    return record;
  }

  // A record is admitted only through a pinned descriptor and its own validator.
  // Ranking labels and paper ledger entries are not an archive inventory.
  const CATALOG = Object.freeze([Object.freeze({
    id: THESIS, path: RECORD_PATH, sha: RECORD_SHA, bytes: RECORD_BYTES,
    title: 'Coherent Corp. share repurchase authorization', validate: validateRecord,
    render, outcome: 'tracker-outcome',
  })]);

  async function loadRecord(fetch, subtle, signal, entry = CATALOG[0]) {
    const response = await fetch(entry.path, {cache: 'no-cache', redirect: 'error', signal});
    const bytes = await readBounded(response, entry.bytes);
    const digest = [...new Uint8Array(await subtle.digest('SHA-256', bytes))]
      .map(byte => byte.toString(16).padStart(2, '0')).join('');
    if (digest !== entry.sha) throw new Error('archive hash mismatch');
    return entry.validate(JSON.parse(new TextDecoder('utf-8', {fatal: true}).decode(bytes)));
  }

  async function loadCatalog(fetch, subtle, signal) {
    const seen = new Set();
    const records = [];
    for (const entry of CATALOG) {
      if (seen.has(entry.id)) throw new Error('duplicate archive identity');
      seen.add(entry.id);
      records.push({entry, record: await loadRecord(fetch, subtle, signal, entry)});
    }
    return records;
  }

  function filterRecords(records, query, decision) {
    const terms = query.toLowerCase().trim().split(/\s+/).filter(Boolean);
    return records.filter(({entry, record}) => {
      const {issuer_cik, accession, thesis_id, reasons} = record.command;
      const searchable = [entry.title, issuer_cik, accession, thesis_id, record.decision,
        ...reasons.flatMap(key => [key, REASONS[key]])].join(' ').toLowerCase();
      return (!decision || record.decision === decision) && terms.every(term => searchable.includes(term));
    });
  }

  function render(doc, record) {
    const el = (tag, text) => {
      const node = doc.createElement(tag);
      if (text !== undefined) node.textContent = text;
      return node;
    };
    const link = (href, label) => {
      const node = el('a', label);
      node.href = href;
      return node;
    };
    const card = el('article');
    card.className = 'idea-card';
    const tag = el('p', 'ABSTAIN · NOT ACTIONABLE');
    tag.className = 'tag caution';
    card.append(tag, el('h2', 'Coherent Corp. share repurchase authorization'),
      el('p', 'CIK ' + record.command.issuer_cik + ' · Filing accession ' + record.command.accession),
      el('p', 'From retrospective release 2: rank ' + RANK_CONTEXT.rank + ', research priority ' + RANK_CONTEXT.score + '/100, assessed evidence weight ' + RANK_CONTEXT.assessedWeight + '/100. This score is not a forecast.'),
      el('p', 'Verified security mapping and current price: unavailable. Expected return: unknown. No trade executed by this record.'),
      el('p', 'The filing reports board authorization, not completed repurchases. This record documents an abstention, not an order.'));

    const clocks = el('div');
    clocks.className = 'idea-grid';
    const local = el('div');
    local.append(el('h3', 'Decision record · local clock, unauthenticated'),
      el('p', record.recorded_utc),
      el('p', 'Declared deadline: ' + record.command.deadline_utc),
      el('p', 'Ranking snapshot cutoff: ' + record.command.snapshot_cutoff_utc),
      el('p', 'The archived record contains no embedded receipt and remains ineligible for prospective evaluation.'));
    const receipt = el('div');
    receipt.append(el('h3', 'Latest verified receipt · saved GitHub evidence'),
      el('p', 'Exact archive bytes existed by ' + RECEIPT.createdUtc + ' (first-attempt push run creation).'),
      el('p', 'Run completed successfully, verified ' + RECEIPT.checkedUtc + '.'),
      el('p', 'This bounds file existence only. It does not authenticate the local decision clock, first-public time or an outcome. It is not a live GitHub check.'),
      link('https://github.com/JeremyHennessy/CatalystRadar/actions/runs/' + RECEIPT.runId, 'Inspect GitHub run ' + RECEIPT.runId));
    clocks.append(local, receipt);
    card.append(clocks);
    const timeline = el('ol');
    const clock = record.command.source_observation_clocks[0].value_as_reported;
    timeline.append(el('li', clock + ' · First saved metadata observation, not first-public time.'),
      el('li', record.command.snapshot_cutoff_utc + ' · Retrospective shortlist cutoff.'),
      el('li', record.recorded_utc + ' · ABSTAIN saved, local clock unauthenticated.'),
      el('li', RECEIPT.createdUtc + ' · Exact bytes bound by GitHub run creation.'));
    card.append(el('h3', 'Evidence and decision timeline'), timeline);

    const blockers = el('ul');
    for (const reason of record.command.reasons) blockers.append(el('li', REASONS[reason]));
    card.append(el('h3', 'Why this case abstained'), blockers);
    const links = el('div');
    links.className = 'idea-links';
    links.append(link('collectors.html#coherent-saved-case', 'Open Coherent source review'),
      link('datasets.html?company_cik=' + CIK + '#company-investigation', 'Open Coherent company dossier'),
      link('trade-ideas.html?snapshot=release-2#' + THESIS, 'Open frozen shortlist case'));
    card.append(links);
    const pins = el('details');
    pins.append(el('summary', 'Archive integrity and receipt details'),
      el('p', 'SHA-256 of exact archive bytes: ' + RECEIPT.recordSha),
      el('p', 'GitHub run head: ' + RECEIPT.head),
      link(RECORD_PATH, 'Read the immutable archived record'));
    card.append(pins);
    return card;
  }

  function install(win) {
    const doc = win.document;
    const state = doc.getElementById('tracker-state');
    const slot = doc.getElementById('tracker-record');
    const button = doc.getElementById('tracker-reload');
    const outcome = doc.getElementById('tracker-outcome');
    const controls = doc.getElementById('tracker-filters');
    const search = doc.getElementById('tracker-search');
    const decision = doc.getElementById('tracker-decision');
    const matches = doc.getElementById('tracker-matches');
    let records = [];
    function updateMatches() {
      const found = filterRecords(records, search.value, decision.value);
      slot.replaceChildren(...found.map(({entry, record}) => entry.render(doc, record)));
      slot.hidden = !found.length;
      outcome.hidden = !found.some(({entry}) => entry.outcome === 'tracker-outcome');
      matches.textContent = found.length
        ? `${found.length} of ${records.length} verified decisions shown.`
        : 'No verified decisions match. Change the company search or decision filter.';
    }
    let initialAnchor = win.location?.hash === '#tracker-record';
    async function refresh() {
      button.disabled = true;
      controls.hidden = true;
      matches.textContent = '';
      records = [];
      slot.hidden = true;
      outcome.hidden = true;
      slot.replaceChildren();
      state.textContent = 'Checking the saved archive. No decision verified yet.';
      const controller = new AbortController();
      const timeout = win.setTimeout(() => controller.abort(), 10000);
      try {
        if (!win.crypto?.subtle) throw new Error('integrity checking unavailable');
        records = await loadCatalog(win.fetch.bind(win), win.crypto.subtle, controller.signal);
        const selected = decision.value;
        const options = ['', ...new Set(records.map(({record}) => record.decision))];
        decision.replaceChildren(...options.map(value => {
          const option = doc.createElement('option');
          option.value = value;
          option.textContent = value || 'All decisions';
          return option;
        }));
        decision.value = options.includes(selected) ? selected : '';
        controls.hidden = false;
        updateMatches();
        if (initialAnchor) slot.scrollIntoView?.({block: 'start'});
        initialAnchor = false;
        state.textContent = `${records.length} archived research decision${records.length === 1 ? '' : 's'} verified by byte count and SHA-256.`;
      } catch (_) {
        state.textContent = 'The saved decision could not be verified. No record or receipt is displayed.';
      } finally {
        win.clearTimeout(timeout);
        button.disabled = false;
      }
    }
    search.addEventListener('input', updateMatches);
    decision.addEventListener('change', updateMatches);
    button.addEventListener('click', refresh);
    return refresh();
  }

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = {loadRecord, loadCatalog, filterRecords, validateRecord, render, install, RECORD_PATH, SOURCE_SNAPSHOT, RANK_CONTEXT};
  } else {
    install(host);
  }
})(typeof window !== 'undefined' ? window : globalThis);
