/* Conservative opt-in app navigation. Unverified history never triggers navigation. */
(function (host) {
  'use strict';
  const pages = new Set(['collectors.html', 'company-ieh.html', 'company.html', 'datasets.html', 'disclosures.html', 'financial-review.html', 'index.html', 'insider-conflicts.html', 'insider-review.html', 'operations.html', 'trade-ideas.html', 'trade-tracker.html']);
  // The app focuses this plain live status after changing the company view; it is not a control.
  const status = 'p#company-work-detail-state[role="status"][aria-live="polite"][tabindex="-1"]';
  const blocked = 'input,textarea,select,button,a,form,summary,details,iframe,object,embed,audio,video,[contenteditable]' +
    `,[role]:not(${status}),[tabindex]:not(${status})`;
  function editableOrControl(event) {
    const path = typeof event.composedPath === 'function' ? event.composedPath() : [event.target];
    return path.some(node => node && (node.isContentEditable ||
      (typeof node.closest === 'function' && node.closest(blocked))));
  }
  function eligibleEvent(event) {
    return event.key === 'Backspace' && !event.defaultPrevented && !event.repeat &&
      !event.isComposing && !(typeof event.getModifierState === 'function' && event.getModifierState('AltGraph')) && !event.altKey && !event.ctrlKey && !event.metaKey && !event.shiftKey &&
      !editableOrControl(event);
  }
  function appURL(value, root) {
    try {
      const url = new URL(value);
      const base = new URL(root);
      if (url.origin !== base.origin || !url.pathname.startsWith(base.pathname)) return false;
      const leaf = url.pathname.slice(base.pathname.length);
      return pages.has(leaf);
    } catch (_) { return false; }
  }
  function previousAppEntry(nav, href, root) {
    try {
      if (!nav || !nav.canGoBack || typeof nav.entries !== 'function' || typeof nav.back !== 'function') return null;
      const current = nav.currentEntry;
      if (!current || !Number.isInteger(current.index) || current.index < 1 || current.url !== href || !appURL(href, root)) return null;
      const previous = nav.entries().filter(entry => entry.index === current.index - 1);
      // WHATWG entries() is the contiguous same-origin history list, not global history.
      // Require its immediate predecessor and additionally restrict it to our app allowlist.
      return previous.length === 1 && previous[0].key && appURL(previous[0].url, root) ? previous[0] : null;
    } catch (_) { return null; }
  }
  function install(win, root) {
    const handler = event => {
      if (!eligibleEvent(event) || !appURL(win.location.href, root)) return;
      // Suppress legacy browser Backspace navigation even on direct/unsupported routes.
      event.preventDefault();
      if (!previousAppEntry(win.navigation, win.location.href, root)) return;
      try {
        const result = win.navigation.back();
        // A cancelled traversal must never fall back to unverified history.back().
        if (result && result.committed) result.committed.catch(() => {});
        if (result && result.finished) result.finished.catch(() => {});
      } catch (_) { /* No fallback. */ }
    };
    win.addEventListener('keydown', handler);
    return () => win.removeEventListener('keydown', handler);
  }
  const api = { eligibleEvent, appURL, previousAppEntry, install };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else if (host.document.currentScript && host.document.currentScript.src) {
    install(host, new URL('.', host.document.currentScript.src).href);
  }
})(typeof window !== 'undefined' ? window : globalThis);
