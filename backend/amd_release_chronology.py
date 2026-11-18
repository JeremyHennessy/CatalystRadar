"""Manual primary-page review cross-reference; not authenticated historical news timing."""
import argparse,copy,datetime as dt,json,re
from decimal import Decimal,localcontext
from pathlib import Path
from company_offering_notices import canonical,digest,pinned_json,sha
SAMPLE_PATH='web/company-findings/revenue-review-sample.json'
SAMPLE_SHA='e1f1fcdda7e59c2953d10416d52968a90a47efc615a3d933b8b0c1f4fc58d431'
NOTE_SHA='8ed2087d4a0a2608295e2e4099a13b1e8c9570e54d45594d895ef237670d6b4c'
ID='f9d8ff71357ad53a181de86ad2295164d300026976bfe2fb926ba0bdb481cd41'
CIK='0000002488';ACC='0000002488-26-000123'
SUB='c9a625ff65076cc6e00b7eea4213297945859489ed347de5459ff57ff7982afa'
NUM={'current':'d3925ad89d15e62a1956f4fe9162a1224f7d63d490beeed063aa46e3d2337f31','prior':'3252b0dd7cac6990cadc00cfd202ecd50ff583ecdf91d578b0de90354be9b90f'}
URLS={'q2_release':'https://ir.amd.com/news-events/press-releases/detail/1295/amd-reports-second-quarter-2026-financial-results','later_release':'https://ir.amd.com/news-events/press-releases/detail/1303/amd-reports-third-quarter-2026-financial-results'}
def calendar(s):
 if not isinstance(s,str) or not re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}',s):raise ValueError('calendar date')
 return dt.date.fromisoformat(s)
def amount(s):
 if not isinstance(s,str) or not re.fullmatch(r'[0-9]{1,15}(?:\.[0-9]{1,6})?',s):raise ValueError('prepared decimal')
 return Decimal(s)
def millions(s,unit):
 if unit!='$M' or not isinstance(s,str) or not re.fullmatch(r'(?:[0-9]{1,3}(?:,[0-9]{3})+|[0-9]{1,9})',s):raise ValueError('display unit/amount')
 with localcontext() as c:c.prec=40;return Decimal(s.replace(',',''))*Decimal(1000000)
def project(sample,note):
 candidates=[p for p in sample['packets'] if p.get('id')==ID]
 if len(candidates)!=1:raise ValueError('unique sample ID')
 p=candidates[0]
 if (p['issuer_cik'],p['accession'],p['source_sub_row_sha256'],p['form_as_filed'],p['fiscal_year_as_filed'],p['fiscal_period_as_filed'])!=(CIK,ACC,SUB,'10-Q','2026','Q2'):raise ValueError('sample binding')
 if len(p['facts'])!=2 or {f['candidate_role'] for f in p['facts']}!={'current','prior'}:raise ValueError('fact identity')
 facts={f['candidate_role']:f for f in p['facts']}
 for role,f in facts.items():
  if f['source_row_sha256']!=NUM[role] or f['unit_as_reported']!='USD' or f['metric']!='RevenueFromContractWithCustomerExcludingAssessedTax' or f['taxonomy_as_reported']!='us-gaap/2026' or f['quarters_as_reported']!='1' or f['segments_as_reported']!='' or f['coreg_as_reported']!='':raise ValueError('fact scope')
 if note['issuer_cik']!=CIK or note['sample_accession']!=ACC or note['method']!='OFFICIAL_ISSUER_WEB_PAGES_READ_VIA_WEB_SEARCH_OPEN' or note['original_http_bytes_retained'] is not False or note['authenticated_historical_first_public_utc'] is not None:raise ValueError('manual evidence status')
 q=note['q2_release'];later=note['later_release']
 for key,r in [('q2_release',q),('later_release',later)]:
  if r['url']!=URLS[key] or r['table']!='GAAP Quarterly Financial Results' or r['unit_as_displayed']!='$M':raise ValueError('reviewed primary citation/table')
 if (q['fiscal_label'],q['prior_fiscal_label'],q['metric'],later['fiscal_label'])!=('Q2 2026','Q2 2025','Revenue','Q3 2026'):raise ValueError('fiscal/metric labels')
 observed=calendar(note['verification_date_utc']);early=calendar(q['source_declared_date']);late=calendar(later['source_declared_date']);filed=dt.datetime.strptime(p['filing_date_as_filed'],'%Y%m%d').date()
 if not early<filed<late<=observed or observed>dt.datetime.now(dt.timezone.utc).date():raise ValueError('strict calendar ordering only')
 checks=[]
 for role,label,display in [('current',q['fiscal_label'],q['current_display']),('prior',q['prior_fiscal_label'],q['prior_display'])]:
  scaled=millions(display,q['unit_as_displayed'])
  if scaled!=amount(facts[role]['value_as_reported']):raise ValueError('scaled displayed amount mismatch')
  checks.append({'candidate_role':role,'issuer_table_fiscal_label':label,'issuer_table_display':display,'issuer_table_unit_as_displayed':'$M','display_scaled_decimal':format(scaled,'f'),'prepared_value_as_reported':facts[role]['value_as_reported'],'prepared_unit_as_reported':'USD','source_num_rowid':facts[role]['source_num_rowid'],'source_num_row_sha256':NUM[role],'numeric_scaled_equality':True,'currency_iso_equivalence_independently_verified':False,'accounting_comparability_verified':False})
 if millions(later['q2_comparative_display'],later['unit_as_displayed'])!=amount(facts['current']['value_as_reported']):raise ValueError('later comparative mismatch')
 return {'schema_version':1,'id':'amd-sampled-q2-release-chronology','sample_binding':{'path':SAMPLE_PATH,'sha256':SAMPLE_SHA,'bytes':27359,'packet_id':ID,'issuer_cik':CIK,'accession':ACC,'source_sub_row_sha256':SUB,'source_num_row_sha256':NUM},'statuses':['PRIOR_DATED_MATCHING_ISSUER_RELEASE_OBSERVED','LATER_QUARTER_RELEASE_OBSERVED'],'interpretation':'An earlier source-dated matching issuer release was observed in this review, and a later-quarter release was also observed. The sampled Q2 filing is not evidence of a new current announcement.','prepared_filing_date_as_filed':filed.isoformat(),'manual_review':{'verification_date_utc':note['verification_date_utc'],'method':note['method'],'curated_note_sha256':NOTE_SHA,'hash_scope':'MANUAL_REVIEW_NOTE_BYTES_NOT_WEBSITE_OR_HTTP_BYTES','original_http_bytes_retained':False,'intraday_observation_utc':None,'authenticated_first_public_utc':None},'earlier_source_dated_release':copy.deepcopy(q),'later_quarter_release':copy.deepcopy(later),'display_scaled_checks':checks,'later_q2_comparative_numeric_equality':True,'calendar_order_check':{'earlier_declared_date_before_filing_date':True,'later_declared_date_after_filing_date':True,'later_declared_date_not_after_review_date':True,'intraday_order_verified':False},'original_xbrl_retention_gap_resolved':False,'first_public_utc':None,'current_announcement_verified':False,'earliest_announcement_verified':False,'economic_event_deduplication_verified':False,'issuer_news_coverage_complete':False,'comparability_verified':False,'growth_calculated':False,'training_ready':False,'execution_ready':False,'provider_requests_made_by_generator':False,'limitations':list(note['limits'])+['The note hash identifies manually curated review evidence only; it does not authenticate page bytes, HTTP status or historical availability.','The issuer table displays $M; no independent ISO-currency conclusion is added to the prepared USD label. Numeric scale equality is not currency or accounting scope equivalence.','This annotation binds one exact packet and its SUB/NUM rows, not all AMD filings, a ticker, a security or an issuer-wide current state.','Source fiscal labels are retained; exact original XBRL start/end contexts remain unverified. No filename/context-date inference or percentage calculation is performed.'],'next_review_action':'Treat this as a historical Q2 review candidate; inspect original exact contexts and fuller issuer chronology before making any novelty or comparable-financial claim.'}
def build(root,note_path):return project(pinned_json(Path(root)/SAMPLE_PATH,SAMPLE_SHA,27359),pinned_json(note_path,NOTE_SHA,20000))
def save(root,note_path,out):
 out=Path(out).resolve()
 if out.exists() or not out.parent.is_dir() or out.is_relative_to(Path(__file__).resolve().parents[1]):raise ValueError('new private destination')
 out.mkdir(mode=0o700)
 def write(n,v):
  p=out/n;p.write_bytes(canonical(v));p.chmod(0o600)
 write('INCOMPLETE',{});d=build(root,note_path)
 if len(canonical(d))>15000:raise ValueError('output bound')
 write('annotation.json',d);write('COMPLETE.json',{'annotation_sha256':sha(out/'annotation.json')});(out/'INCOMPLETE').unlink();return d
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',default=str(Path(__file__).resolve().parents[1]));p.add_argument('--note',required=True);p.add_argument('--out',required=True);a=p.parse_args();save(a.root,a.note,a.out)
