"""Deterministic navigation over specifically released evidence, not a market scan."""
import argparse, hashlib, json, re, unicodedata
from collections import Counter
from pathlib import Path
from openfigi_evidence import read_pinned
from research_retrieval import load_verified
from research_dossier import resolve
PINS = {'queue': {'path': 'web/company-findings/research-lead-index-v3.json', 'bytes': 281154, 'sha256': '3d8db27dc45ed84fa44d5604e1839aa2aa9e1f263f2ed9e18cef04aed7a0e4e3'}, 'vitaspring_revenue': {'path': 'web/company-findings/vitaspring-revenue.json', 'bytes': 5874, 'sha256': '56b604c79e02b7ca45f5bf3cf46c3fc2b5d6cb1957324ed2ccb761d4ce38d98b'}, 'vitaspring_loss': {'path': 'web/company-findings/vitaspring-net-loss.json', 'bytes': 7545, 'sha256': '854a68cd119b608e34a081b562f7070b27dbfc009f518cb28d3aeac57bfef835'}, 'keycorp': {'path': 'web/company-findings/keycorp-cusip-evidence.json', 'bytes': 6571, 'sha256': 'c451a39274292eaf2bfac6c88227bf4fae6bf2a28dbcfefdbc716681970365de'}, 'xerox_identity': {'path': 'web/company-findings/xerox-filing-identity.json', 'bytes': 4171, 'sha256': 'db91d59be91d6c534a165605519943afe740d84e97411060280fec620f1b256c'}, 'agreements': {'path': 'web/company-findings/material-agreements.json', 'bytes': 17710, 'sha256': '533a3f597c6f8349cc6dc7d004813365e8932f671ff68230e485cbc3739298b1'}, 'votes': {'path': 'web/company-findings/shareholder-votes.json', 'bytes': 16556, 'sha256': '466a0f86399cbcf9ab6f1419d8c63005b52bab3527ddf8ba9da60584796fc1cf'}, 'revenue_candidates': {'path': 'web/company-findings/revenue-review-sample.json', 'bytes': 27359, 'sha256': 'e1f1fcdda7e59c2953d10416d52968a90a47efc615a3d933b8b0c1f4fc58d431'}, 'financial': {'path': 'web/company-findings/financial-review.json', 'bytes': 930170, 'sha256': '423c730d0bd1d3382b8a7369d8edffc5f5014266396ae913a96336f39d75a53b'}, 'catalog': {'path': 'web/disclosure-catalog/filings.json', 'bytes': 215476, 'sha256': 'e9ff960153c9ea13c4afd3ba049a46e61d30699989c126303ca093c81451c036'}, 'manifest': {'path': 'web/disclosure-catalog/summary.json', 'bytes': 2512, 'sha256': 'd4b42d28e603da94ed5d7fe230d404884191af692213078c834e152a470cf003'}, 'insider': {'path': 'web/company-findings/financial-insider-links.json', 'bytes': 1000234, 'sha256': 'eaab47ce78279906a17b7b52a9cd6b6cc241faf9ddd9ff349f90823e968ef13c'}, 'ieh': {'path': 'web/company-findings/ieh-reported-revenue.json', 'bytes': 4778, 'sha256': '74c4fff28c44a4213993cfa487b7745006a71a23d9274f5cbdd5516257719002'}, 'holdings': {'path': 'docs/research/holdings-figi-2026-11-17.json', 'bytes': 3034, 'sha256': '291ee57c7c3c7531e401d42cffb71c95864b41d36cbd9e3f3ef342e0e1e1f7aa'}, 'mapping': {'path': 'docs/research/openfigi-watchlist-2026-11-17.json', 'bytes': 7107, 'sha256': 'dce3ef5535d2e265f83d1be179ea248d078a2b60ce415118f12e43ce1b908b0c'}, 'emerson': {'path': 'web/company-findings/emerson-note-offering.json', 'bytes': 3566, 'sha256': '0d5d4625c4456b84ccc269a0b5c65a5632808c66ac167adbca2d6bd60ae401e2'}, 'watchlist_insider': {'path': 'web/insider-review/cards.json', 'bytes': 60464, 'sha256': 'd4a32de705461db6bc64a0ba661004300909c85471c369083aa54689238abe28'}}
OUTPUT='web/research-scanner/v1/index.json'
CATEGORIES=('FINANCIAL_CONTEXT','INSIDER_FILING','ACQUISITION_DISPOSAL_DISCLOSURE','REPORTED_REVENUE','REPORTED_FINANCING','REPORTED_LOSS','SECURITY_CONTEXT','FILER_IDENTITY','REPORTED_EXCHANGE','REPORTED_VOTES','REVENUE_CANDIDATE')
STATES=('ORIGINAL_REVIEW_REQUIRED','SOURCE_REVIEWED_WITH_LIMITS')
MAX_BYTES=1600000

def encoded(obj):return (json.dumps(obj,ensure_ascii=True,sort_keys=True,separators=(',',':'))+'\n').encode()
def digest(obj):return hashlib.sha256(encoded(obj)).hexdigest()
def pointer(obj,path):
 if path=='':return obj
 for p in path.lstrip('/').split('/'):
  p=p.replace('~1','/').replace('~0','~');obj=obj[int(p)] if isinstance(obj,list) else obj[p]
 return obj
def assoc(cik,names,role='SOURCE_ISSUER'):
 if not isinstance(cik,str) or not re.fullmatch('[0-9]{10}',cik) or int(cik)==0:raise ValueError('CIK')
 if not isinstance(names,list) or not names or any(not isinstance(n,str) or not n or len(n)>500 or any(unicodedata.category(c).startswith('C') for c in n) for n in names):raise ValueError('name')
 return {'issuer_cik':cik,'names_as_reported':sorted(set(names)),'role':role}
def clock(label,value):return {'meaning':label,'value_as_reported':value}

def project(data):
 queue=data['queue'];entries=queue['records'];records=[];ids=set();refs=set()
 def add(key,path,category,state,associations,title,summary,dates,link,unknowns,next_action):
  source=pointer(data[key],path);ref=(key,path)
  if ref in refs:raise ValueError('duplicate source reference')
  refs.add(ref)
  if category not in CATEGORIES or state not in STATES or not associations or len({a['issuer_cik'] for a in associations})!=len(associations):raise ValueError('category or identity')
  ci=sorted(a['issuer_cik'] for a in associations)
  rid=key+':'+hashlib.sha256(path.encode()).hexdigest()[:24]
  if rid in ids:raise ValueError('ID collision')
  ids.add(rid)
  accessions=sorted({x['accession'] for x in source.get('observations',[])}) if category=='FINANCIAL_CONTEXT' else [source['filing']['accession']] if 'filing' in source else [source['accession']] if 'accession' in source else []
  if any(not re.fullmatch('[0-9]{10}-[0-9]{2}-[0-9]{6}',a) for a in accessions):raise ValueError('accession')
  records.append({'source_accessions':accessions,'navigation_status':'EXISTING_PAGE_OR_SECTION_NOT_AUTOMATIC_RECORD_SELECTION','id':rid,'category':category,'evidence_state':state,'issuer_associations':associations,'title':title,'summary':summary,'clocks':dates,'first_public_utc':None,'source_ref':{'key':key,'json_pointer':path,'object_sha256':digest(source)},'investigation_path':link,'dossier_ciks':[c for c in ci if c in qcis],'unknowns':unknowns,'next_action':next_action,'training_ready':False,'execution_ready':False})
 qcis={e['issuer_cik'] for e in entries}
 if len(qcis)!=108 or len(entries)!=108:raise ValueError('queue census')
 common=['No first-public or decision-time availability is established.','Issuer CIK is not a verified security mapping; no outcome, prediction or trade qualification.']
 for entry in entries:
  ci=entry['issuer_cik']
  for r in resolve(data['financial']['records'],entry['financial_case_ids'],ci,lambda x:x['id']):
   i=data['financial']['records'].index(r)
   dates=[clock('prepared_rounded_context_end_not_exact_period',r['reported_end_date'])]+[clock('filing_date_as_filed',o['filing_date_as_filed']) for o in r['observations']]
   add('financial',f'/records/{i}','FINANCIAL_CONTEXT','ORIGINAL_REVIEW_REQUIRED',[assoc(ci,r['issuer_names_as_filed'])],r['metric']+' · repeated prepared context', 'Reported relation: '+r['numeric_relation']+'. This is not growth, comparability or a restatement determination.',dates,'financial-review.html?cik='+ci,common+['Prepared dates are rounded; original accounting durations, scope and amendment lineage need review.'],'Inspect each source accession and original context before comparing values.')
  key='watchlist_insider' if 'watchlist_insider' in entry['source_keys'] else 'insider' if 'insider' in entry['source_keys'] else None
  if key:
   field='filings' if key=='watchlist_insider' else 'insider_filings'
   for r in resolve(data[key][field],entry['insider_filing_refs'],ci,lambda x:x['batch_id']+':'+x['accession']):
    i=data[key][field].index(r)
    add(key,f'/{field}/{i}','INSIDER_FILING','ORIGINAL_REVIEW_REQUIRED',[assoc(ci,[r['issuer_name_as_filed']])],r['form_as_filed']+' · '+r['accession'],str(r['selected_transaction_rows'])+' selected reported P/S rows. Codes include open-market OR private activity; counts are not unique trades or people.',[clock('filing_date_as_filed',r['filing_date']),clock('transaction_date_min_as_filed',r['transaction_date_min']),clock('transaction_date_max_as_filed',r['transaction_date_max']),clock('filing_batch',r['batch_id'])],'financial-review.html#research-queue',common+['Original filing/footnotes and amendment context require review. No intent, plan applicability or cause is inferred.'],r['review_questions'][0])
  for r in resolve(data['catalog'],entry['disclosure_accessions'],ci,lambda x:x['accession']):
   i=data['catalog'].index(r)
   add('catalog',f'/{i}','ACQUISITION_DISPOSAL_DISCLOSURE','ORIGINAL_REVIEW_REQUIRED',[assoc(ci,[r['issuer_name_as_filed']])],r['form_as_filed']+' · acquisition/disposal concepts',str(r['disclosure_records'])+' selected disclosure contexts, not confirmed deals.',[clock('filing_date_as_filed',r['filing_date'])],'disclosures.html#filing-'+r['accession'],common+['Concept presence does not establish a transaction, announcement date, target, value or materiality.'],'Read the exact filing and selected disclosure contexts before classifying any event.')
  if entry.get('finding_ref'):
   key='ieh' if 'ieh' in entry['source_keys'] else 'emerson';r=data[key]
   if r['id']!=entry['finding_ref'] or r['issuer']['cik']!=ci or r['filing']['accession']!=entry['source_accession']:raise ValueError('reported identity')
   names=[r['issuer'].get('name_as_reported') or r['issuer'].get('name_as_filed')]
   summary=r['finding'] if isinstance(r.get('finding'),str) else 'Emerson reported completion of previously announced EUR 750 million notes; not independent settlement, net proceeds or current debt balance.'
   add(key,'','REPORTED_REVENUE' if key=='ieh' else 'REPORTED_FINANCING','SOURCE_REVIEWED_WITH_LIMITS',[assoc(ci,names)],r.get('title','Issuer-reported note completion'),summary,([clock(k,r['filing'][k]) for k in ('filing_date_as_reported','report_date_as_reported','release_date_as_reported')]+[clock('retrieved_utc_as_recorded',r['provenance']['retrieved_utc_as_recorded'])] if key=='ieh' else [clock('source_observed_as_recorded',r['filing']['observed_utc']),clock('reported_completion_date',r['facts']['reported_completion_date']),clock('reported_prior_pricing_filing_date',r['facts']['reported_prior_pricing_filing_date'])]),entry['evidence_url'],r.get('blockers',r['limitations']),entry['next_action'])
 for key,cat,link in [('vitaspring_revenue','REPORTED_REVENUE','company.html#company-finding'),('vitaspring_loss','REPORTED_LOSS','company.html#net-loss')]:
  r=data[key]
  add(key,'',cat,'SOURCE_REVIEWED_WITH_LIMITS',[assoc(r['issuer']['cik'],[r['issuer']['name_as_filed']])],r['title'],r['finding'],[clock('filing_date_as_reported',r['filing']['filing_date_as_reported']),clock('report_period_as_filed',r['filing']['period_of_report']),clock('source_local_verified_not_download_or_first_public',r['provenance']['source_local_verified_utc'])]+[clock('source_exact_period',{'start':f['period_start'],'end':f['period_end']}) for f in r['facts']],link,r['blockers'],r['next_research_steps'][0])
 r=data['keycorp']
 add('keycorp','','SECURITY_CONTEXT','SOURCE_REVIEWED_WITH_LIMITS',[assoc(r['issuer_cik_as_filed'],[r['issuer_name_as_filed']])],'Later KeyCorp security-class evidence',r['finding'],[clock('disclosure_date_as_reported',r['disclosure_date_as_reported']),clock('planned_redemption_not_completion',r['planned_redemption_date_as_reported']),clock('source_observed_as_recorded',r['provenance']['source_observed_utc_as_recorded'])],'datasets.html#ftd-directory',r['limitations'],'Review the later notice and conflicting historical class labels; do not backdate this security description.')
 r=data['xerox_identity']
 add('xerox_identity','','FILER_IDENTITY','SOURCE_REVIEWED_WITH_LIMITS',[assoc(f['cik'],[f['name_as_filed']],'SEPARATE_EXPLICIT_FILER') for f in r['identity_evidence']['filers']],'Xerox · two separate filing registrants',r['finding'],[clock('filing_date_as_reported',r['filing_date_as_reported'])]+[clock(a['role']+'_observation',a['observed_utc_as_recorded']) for a in r['associations']],'financial-review.html#xerox-identity',r['limitations'],'Attribute each fact or obligation to its explicit registrant; never merge the two CIKs.')
 for key,field,cat,title,summary,link in [('agreements','reviewed_finding','REPORTED_EXCHANGE','Xerox · reported exchange with separate obligor roles','Issuer-reported previously announced exchange: Holdings old notes and common shares are distinct from Xerox Corporation new notes. No net-debt, transaction-value or independent-settlement inference.','financial-review.html#material-agreements'),('votes','reviewed_plan','REPORTED_VOTES','H&R Block · votes and conditional plan authorization','Three reported proposal vote tables and conditional 6,500,000-share base authorization. This is not actual issuance, net available capacity or dilution.','financial-review.html#shareholder-votes')]:
  matches=[(i,p) for i,p in enumerate(data[key]['packages']) if p.get(field)]
  if len(matches)!=1:raise ValueError('screen finding census')
  i,r=matches[0];f=r[field]
  dates=[clock('source_observed_as_recorded',r['source_observed_utc_as_recorded'])]+[clock(k,f[k]) for k in (('settlement_date_as_reported','support_agreement_date_as_reported','exchange_agreement_date_as_reported') if key=='agreements' else ('meeting_date_as_reported',))]
  add(key,f'/packages/{i}',cat,'SOURCE_REVIEWED_WITH_LIMITS',[assoc(x['cik'],[x['name_as_filed']],'SEPARATE_EXPLICIT_FILER') for x in r['filers_as_reported']],title,summary,dates,link,data[key]['limitations'],'Inspect the source-reviewed terms and explicit entity roles; retain all conditional or unknown quantities.')
 for i,r in enumerate(data['revenue_candidates']['packets']):
  add('revenue_candidates',f'/packets/{i}','REVENUE_CANDIDATE','ORIGINAL_REVIEW_REQUIRED',[assoc(r['issuer_cik'],[r['issuer_name_as_filed']])],'Prepared revenue pair · original contexts required','Two source-reported revenue values are available for inspection. No absolute or percentage change is calculated; exact periods and accounting comparability remain unverified.',[clock('filing_date_as_filed_YYYYMMDD',r['filing_date_as_filed']),clock('report_period_as_filed_YYYYMMDD',r['submission_report_period_as_filed'])]+[clock('prepared_rounded_context_date_YYYYMMDD',f['reported_context_date_as_filed']) for f in r['facts']],'financial-review.html#revenue-candidates',data['revenue_candidates']['limitations'],r['next_review_action'])
 records.sort(key=lambda r:(min(x['issuer_cik'] for x in r['issuer_associations']),r['category'],r['id']))
 counts={'evidence_records':len(records),'distinct_associated_issuer_ciks':len({x['issuer_cik'] for r in records for x in r['issuer_associations']}),'by_category':dict(sorted(Counter(r['category'] for r in records).items())),'by_state':dict(sorted(Counter(r['evidence_state'] for r in records).items())),'by_source':dict(sorted(Counter(r['source_ref']['key'] for r in records).items()))}
 if counts['distinct_associated_issuer_ciks']!=117 or len(records)!=905:raise ValueError('changed released evidence census')
 return {'schema_version':1,'status':'RETAINED_EVIDENCE_NAVIGATION_NOT_MARKET_SCREEN_OR_SIGNALS','sources':PINS,'counts':counts,'records':records,'coverage':{'existing_dossier_ciks':sorted(qcis),'scope':'Selected records from the fixed 108-company dossier snapshot, six later reviewed findings, and five separately selected revenue candidates. Not all issuers, filings, securities or market events.','family_selection':{'financial':'All 605 referenced repeated contexts in the fixed queue.','insider':'All 282 referenced filings in the fixed queue, not all retained insider records.','disclosure':'Five queue-linked filings, not the complete 466-filing catalog.','reported':'Two queue findings plus six later specifically listed reviewed findings.','revenue_candidates':'All five packets from the separately frozen prepared-revenue sampling policy.'},'absence_meaning':'No scanner result is absence only from this included evidence set. It is not no company activity or full source coverage.','holdings_company_assessment':'NOT_ASSESSED_MISSING_VERIFIED_ISSUER_SECURITY_MAPPING'},'limitations':['Records are evidence units, not deduplicated economic events, independent observations or ranked opportunities.','CIK groups source associations only. Names are as reported, not verified current identities. Dual filers remain separate; no fact is propagated between them.','Source-specific clocks remain distinct. Filing, report, planned, settlement, observation and audit dates are not interchangeable or first-public timestamps.','Original-reviewed means narrow source extraction reviewed, not financial truth, full accounting comparability, event novelty or a qualified outcome.','No new provider collection, private values, forecasts, recommendations, probabilities or trading activation.'],'provider_requests_made':False,'training_ready':False,'execution_ready':False}

def build_package(root):
 data={}
 for key,m in PINS.items():
  data[key],size=read_pinned(Path(root)/m['path'],m['sha256'],m['bytes'])
  if size!=m['bytes']:raise ValueError('source bytes')
 if load_verified(root)!=data['queue']:raise ValueError('queue rebuild')
 result=project(data);payloads={};buckets={f'{i:02x}':[] for i in range(64)}
 for r in result['records']:
  b=f"{hashlib.sha256(r['id'].encode()).digest()[0]%64:02x}";r['detail_bucket']=b
  ref=r['source_ref'];buckets[b].append({'id':r['id'],'source_ref':ref,'source_record':pointer(data[ref['key']],ref['json_pointer'])})
 result['detail_shards']={}
 for b,rows in buckets.items():
  rows.sort(key=lambda x:x['id']);path=f'web/research-scanner/v1/details/{b}.json'
  raw=encoded({'schema_version':1,'bucket':b,'records':rows})
  if len(raw)>300000:raise ValueError('detail shard bound')
  payloads[path]=raw;result['detail_shards'][b]={'path':path,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'record_ids':[r['id'] for r in rows]}
 payloads[OUTPUT]=encoded(result)
 if len(payloads[OUTPUT])>MAX_BYTES or sum(map(len,payloads.values()))>8000000:raise ValueError('output bound')
 return result,payloads

def build(root):return build_package(root)[0]

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',default=str(Path(__file__).resolve().parents[1]));a=p.parse_args();print(encoded(build(a.root)).decode(),end='')
if __name__=='__main__':main()
