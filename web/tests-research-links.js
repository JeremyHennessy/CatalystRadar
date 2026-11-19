'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const pages = [
  'collectors.html', 'company-ieh.html', 'company.html', 'datasets.html',
  'disclosures.html', 'financial-review.html', 'index.html', 'insider-conflicts.html',
  'insider-review.html', 'operations.html', 'trade-ideas.html',
];
const read = page => fs.readFileSync(path.join(__dirname, page), 'utf8');
const routes = {
  'index.html': ['datasets.html#company-investigation', 'financial-review.html#research-scanner', 'trade-ideas.html'],
  'trade-ideas.html': ['index.html', 'datasets.html#company-investigation', 'financial-review.html#research-scanner'],
  'datasets.html': ['#company-investigation', '#issuer-explorer', 'financial-review.html#research-scanner', 'collectors.html'],
  'financial-review.html': ['datasets.html#company-investigation', '#research-scanner', '#outcome-eligibility', 'collectors.html'],
  'operations.html': ['datasets.html#company-investigation', 'financial-review.html#research-scanner', 'collectors.html'],
};
for (const page of pages) {
  const html = read(page);
  const scripts = html.match(/<script defer src="research-backspace\.js\?v=[a-z0-9-]+"><\/script>/g);
  const expectedVersion = page === 'datasets.html' ? '20261119-status-focus' : ['index.html', 'trade-ideas.html'].includes(page) ? '20261119-trade-ideas' : '20261119-app-history';
  assert.equal(scripts?.length, 1, page);
  assert.ok(scripts[0].includes('?v=' + expectedVersion + '"'), page);
  assert.ok(html.indexOf(scripts[0]) < html.indexOf('</head>'), page);
}
for (const [page, links] of Object.entries(routes)) {
  const navs = Array.from(read(page).matchAll(/<nav\b[^>]*>.*?<\/nav>/gs), m => m[0]);
  for (const link of links) {
    assert(navs.some(nav => nav.includes('href="' + link + '"')), page + ' missing ' + link);
    const [target, fragment] = link.split('#');
    const html = read(target || page);
    if (fragment) assert(html.includes('id="' + fragment + '"'), link + ' target missing');
  }
}
console.log('Research navigation: native links, fragments and per-page shortcut binding pass');
