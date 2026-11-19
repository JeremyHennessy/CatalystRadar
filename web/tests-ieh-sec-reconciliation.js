'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),crypto=require('node:crypto');
const v=require('./ieh-sec-reconciliation');
const read=p=>fs.readFileSync(__dirname+'/'+p);
const hash=buf=>crypto.createHash('sha256').update(buf).digest('hex');
const bytes=read(v.PATH),d=JSON.parse(bytes);
assert.equal(bytes.length,v.SIZE);assert.equal(hash(bytes),v.SHA);
const archived=read('company-findings/ieh-reported-revenue.json'),base=JSON.parse(archived);
assert.equal(hash(archived),d.archived_revenue_sha256);
assert.equal(base.issuer.cik,d.issuer_cik);
assert.equal(base.filing.accession,d.filings[1].accession);
assert.deepEqual([base.comparison.current_value,base.comparison.prior_value].map(Number),d.filings[1].revenue);
assert.equal(v.validate(d),d);
for(const mutate of [
  x=>x.filings[1].revenue[0]++,x=>x.filings[0].revenue[1]--,
  x=>x.filings[1].operating_income[1]=104380,x=>x.quarter_ends[0]='2026-06-30',
  x=>x.issuer_cik='0000000001',x=>x.filings.reverse(),
  x=>x.filings[1].acceptance_utc=x.filings[0].acceptance_utc,
  x=>x.acceptance_gap_seconds++,x=>x.exhibit_date_as_reported='2026-11-13',
  x=>x.first_public_utc=x.filings[0].acceptance_utc,x=>x.whole_document_novelty_evaluated=true,
  x=>x.accounting_comparability_verified=true,x=>x.execution_ready=true,
  x=>x.duplicate_revenue_in_later_accepted_filing=false,x=>x.revenue_growth_pct_4dp='51.1826',
  x=>x.filings[1].document_url='javascript:alert(1)',x=>x.filings[0].index_url=x.filings[1].index_url
]){
  const bad=structuredClone(d);mutate(bad);assert.throws(()=>v.validate(bad));
}
assert.match(read('company-ieh.html').toString(),/ieh-sec-reconciliation\.js\?v=20261119-reconciliation/);
assert.match(read('company-ieh.html').toString(),/id="ieh-sec-reconciliation-body"/);
class Node{
  constructor(tag){this.tag=tag;this.children=[];this.textContent='';}
  append(...nodes){this.children.push(...nodes);}
  replaceChildren(...nodes){this.children=nodes;}
  set innerHTML(_){throw Error('Unsafe HTML');}
}
const root=new Node('div');
const doc={getElementById:id=>id==='ieh-sec-reconciliation-body'?root:null,createElement:t=>new Node(t)};
const flat=n=>[n,...n.children.flatMap(flat)];
const load=corrupt=>v.init(doc,crypto.webcrypto,async(path,opt)=>{
  assert.equal(path,v.PATH);assert.equal(opt.cache,'no-store');assert.ok(opt.signal);
  const b=Uint8Array.from(bytes);if(corrupt)b[8]^=1;
  return{ok:true,arrayBuffer:async()=>b.buffer};
});
(async()=>{
  await load(false);
  const nodes=flat(root),all=nodes.map(n=>n.textContent).join(' ');
  for(const s of ['51.1825%','24h 38m 26s later','exhibit itself is dated November 12','Acceptance order does not establish','Do not count it as a separate revenue surprise','Archived rankings and qualification are unchanged'])assert.ok(all.includes(s),s);
  assert.deepEqual(nodes.filter(n=>n.tag==='a').map(n=>n.href),d.filings.flatMap(f=>[f.document_url,f.index_url]));
  await load(true);
  assert.equal(root.children.length,1);assert.match(root.children[0].textContent,/could not be verified/);
  assert.equal(flat(root).filter(n=>n.tag==='a').length,0);
  console.log('IEH supplemental SEC reconciliation: exact links, duplicate scope, temporal boundaries, frozen evidence and corrupt overlay pass');
})().catch(e=>{console.error(e);process.exitCode=1;});
