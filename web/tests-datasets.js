'use strict';
const assert=require('assert'),fs=require('fs'),vm=require('vm');
const crypto=require('crypto');
const manifest=JSON.parse(fs.readFileSync(__dirname+'/prepared/summary.json'));
const issuerBytes=fs.readFileSync(__dirname+'/prepared/issuers.json');
assert.equal(issuerBytes.length,manifest.issuer_metadata.byte_count);
assert.equal(crypto.createHash('sha256').update(issuerBytes).digest('hex'),manifest.issuer_metadata.sha256);
const coverage=JSON.parse(issuerBytes);assert.equal(coverage.length,manifest.issuer_counts.union);
assert.equal(new Set(coverage.map(r=>r.cik)).size,coverage.length);
assert.equal(coverage.filter(r=>r.financial_submissions>0).length,manifest.issuer_counts.financial);
assert.equal(coverage.filter(r=>r.insider_submissions>0).length,manifest.issuer_counts.insider);
coverage.forEach(r=>{assert.deepEqual(Object.keys(r).sort(),['cik','financial_submissions','insider_submissions','names','reported_tickers']);assert(/^\d{10}$/.test(r.cik));});
const {secSource,format}=require('./datasets.js');assert(secSource('https://www.sec.gov/files/data/a.zip'));assert(!secSource('https://evil.test/x.zip'));assert(!secSource('javascript:alert(1)'));assert.equal(format(null),'Unknown');
function elem(){return {textContent:'',value:'',children:[],events:{},append(...x){this.children.push(...x);},replaceChildren(){this.children=[];},addEventListener(k,f){this.events[k]=f;}};}
async function check(fail){
 const nodes={},get=id=>nodes[id]||(nodes[id]=elem());const source=JSON.parse(fs.readFileSync(__dirname+'/prepared/summary.json'));const issuers=JSON.parse(fs.readFileSync(__dirname+'/prepared/issuers.json'));
 const context={document:{getElementById:get,createElement:elem},fetch:async url=>({ok:!fail,json:async()=>url.endsWith('summary.json')?source:issuers})};vm.createContext(context);vm.runInContext(fs.readFileSync(__dirname+'/datasets.js','utf8'),context);await new Promise(r=>setImmediate(r));
 if(fail){assert(get('dataset-status').textContent.includes('unavailable'));assert.equal(get('dataset-issuers').children.length,0);return;}
 assert.equal(get('dataset-issuers').children.length,100);assert(get('dataset-status').textContent.includes('Historical baseline'));get('dataset-search').value='NO_MATCH_UNLIKELY_8293';get('dataset-search').events.input();assert.equal(get('dataset-issuers').children.length,0);get('dataset-search').value=issuers[0].cik;get('dataset-search').events.input();assert(get('dataset-issuers').children.length>0);
}
(async()=>{await check(false);await check(true);console.log('Prepared dataset UI counts, filtering, unavailable state and source URL checks passed.');})().catch(e=>{console.error(e);process.exit(1);});
