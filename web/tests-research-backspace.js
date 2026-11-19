'use strict';
const assert = require('node:assert/strict');
const { eligibleEvent, appURL, previousAppEntry, install } = require('./research-backspace.js');
const root = 'https://example.test/CatalystRadar/web/';
const a = root + 'datasets.html'; const b = root + 'financial-review.html?cik=1#source';
function event(extra = {}) { return { key: 'Backspace', target: { closest: () => null }, preventDefault() { this.prevented = true; }, ...extra }; }
function navigation(previous = a) { return { canGoBack: true, currentEntry: { index: 2, url: b }, entries: () => [{ index: 1, key: 'prior', url: previous }], back() { this.called = true; return {}; } }; }
assert(eligibleEvent(event()));
for (const key of ['defaultPrevented', 'repeat', 'isComposing', 'altKey', 'ctrlKey', 'metaKey', 'shiftKey']) assert(!eligibleEvent(event({ [key]: true })));
assert(!eligibleEvent(event({ key: 'Delete' })));
assert(!eligibleEvent(event({ getModifierState: key => key === 'AltGraph' })));
assert(!eligibleEvent(event({ target: { closest: () => ({}) } })));
assert(!eligibleEvent(event({ composedPath: () => [{ isContentEditable: true }] })));
assert(!eligibleEvent(event({ composedPath: () => [{ closest: () => null }, { closest: () => ({}) }] })));
// Model the one programmatically focused status; any actual control or editable ancestor still matches.
const statusSelector = 'p#company-work-detail-state[role="status"][aria-live="polite"][tabindex="-1"]';
const status = { closest(selector) {
  assert(selector.includes('[role]:not(' + statusSelector + ')'));
  assert(selector.includes('[tabindex]:not(' + statusSelector + ')'));
  return null;
} };
assert(eligibleEvent(event({ target: status })));
assert(!eligibleEvent(event({ target: { ...status, isContentEditable: true } })));
assert(!eligibleEvent(event({ composedPath: () => [status, { closest: () => ({}) }] })));
assert(appURL(a, root));
for (const bad of ['https://other.test/CatalystRadar/web/index.html', root + '../index.html', root + 'nested/index.html', root + 'data.json', root + 'unknown.html', root + '%2findex.html']) assert(!appURL(bad, root));
assert(previousAppEntry(navigation(), b, root));
for (const nav of [null, {}, { ...navigation(), canGoBack: false }, { ...navigation(), currentEntry: { index: 0, url: b } }, { ...navigation(), entries: () => [{ index: 0, key: 'gap', url: a }] }, navigation('https://elsewhere.test/'), { ...navigation(), entries: () => [{ index: 1, key: '1', url: a }, { index: 1, key: '2', url: a }] }]) assert.equal(previousAppEntry(nav, b, root), null);
assert.equal(previousAppEntry(navigation(), a, root), null);
let listener; const win = { navigation: navigation(), location: { href: b }, addEventListener: (_, f) => { listener = f; }, removeEventListener: (_, f) => { assert.equal(f, listener); } };
const uninstall = install(win, root); const yes = event({ target: status }); listener(yes); assert(yes.prevented && win.navigation.called);
win.navigation = undefined; win.history = { length: 100, back() { throw Error('Forbidden fallback'); } }; const no = event(); listener(no); assert(no.prevented);
win.navigation = navigation();
for (const guarded of [event({ target: { closest: () => ({}) } }), event({ ctrlKey: true }), event({ defaultPrevented: true })]) {
  listener(guarded);
  assert(!guarded.prevented);
  assert(!win.navigation.called);
}
let fallbackCalls = 0;
win.history.back = () => { fallbackCalls++; };
let attempts = 0;
win.navigation.back = () => { attempts++; throw Error('Traversal cancelled synchronously'); };
const thrown = event();
assert.doesNotThrow(() => listener(thrown));
assert(thrown.prevented);
assert.equal(attempts, 1);
assert.equal(fallbackCalls, 0);
const unhandled = [];
const onUnhandled = reason => unhandled.push(reason);
process.on('unhandledRejection', onUnhandled);
win.navigation.back = () => {
  attempts++;
  return { committed: Promise.reject(Error('Commit cancelled')), finished: Promise.reject(Error('Finish cancelled')) };
};
const rejected = event(); listener(rejected);
assert(rejected.prevented);
assert.equal(attempts, 2);
setImmediate(() => {
  process.removeListener('unhandledRejection', onUnhandled);
  assert.deepEqual(unhandled, []);
  assert.equal(fallbackCalls, 0);
  assert.equal(attempts, 2);
  uninstall();
  console.log('Research Backspace conservative navigation checks passed');
});

assert(appURL(root+'trade-ideas.html',root));assert(!appURL(root+'trade-ideas-other.html',root));assert(!appURL(root+'nested/trade-ideas.html',root));
