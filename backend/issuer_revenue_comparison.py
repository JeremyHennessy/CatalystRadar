"""Bounded prose extraction plus one retained-source IEH review card. No network."""
import argparse,datetime as dt,hashlib,json,re,zipfile
from decimal import Decimal,localcontext,ROUND_HALF_UP
from fractions import Fraction
from pathlib import Path
from financial_admission_rehearsal import plain
from financial_pair_candidates import sha,write_private
from private_prices import unique_object

ZIP_SHA='0f92e2c02a597b14f08c29395ae2fc9b87f2db580016e632c8d76c3059e449c0'
RAW_SHA='601bce6d1a5d0337271ece9abb6ddf2b91ed84ac42d33806deb4ae378b9418e0'
MANIFEST_SHA='ac6316ad597b9a931613c71e4f1442425f5f83c873d47ba17192f0c1b6a2274a'
ACC='0001174947-26-000991';CIK='50292'
MONTHS='January February March April May June July August September October November December'.split()
DATE=r'(?:'+ '|'.join(MONTHS)+r') [1-9][0-9]?, 20[0-9]{2}'
MONEY=r'(?:[1-9][0-9]{0,2}(?:,[0-9]{3}){1,4}|[0-9]{1,15})(?:\.[0-9]{1,2})?'
Q=r'[1-4](?:st|nd|rd|th) quarter fiscal year 20[0-9]{2}'
# Entire paragraph only; this is intentionally a narrow supported grammatical form.
PATTERN=re.compile(r'For the quarter ended (?P<current_end>'+DATE+r'), (?P<label>[A-Z][A-Za-z0-9 &.-]{0,60}) had revenues of \$(?P<current>'+MONEY+r') as compared to \$(?P<prior>'+MONEY+r') for the quarter ended (?P<prior_end>'+DATE+r'), reflecting a (?P<reported_percent>[0-9]{1,3})% increase; an operating profit of \$'+MONEY+r' for '+Q+r' as compared to an operating loss of \$'+MONEY+r' for '+Q+r'; net income of \$'+MONEY+r' for '+Q+r' as compared to a net loss of \$'+MONEY+r' for '+Q+r'; and a basic gain per share of \$\.[0-9]{1,4} for '+Q+r' as compared to a basic loss per share of \$\.[0-9]{1,4} for '+Q+r'\.')

def digest(raw):return hashlib.sha256(raw).hexdigest()
def iso(s):
 month,day,year=s.replace(',','').split();return dt.date(int(year),MONTHS.index(month)+1,int(day)).isoformat()
def exact_ratio(current,prior):
 a=Decimal(current.replace(',',''));b=Decimal(prior.replace(',',''))
 if not a.is_finite() or not b.is_finite() or not a>b>0:raise ValueError('positive increasing comparison required')
 f=(Fraction(a)-Fraction(b))*100/Fraction(b)
 with localcontext() as c:
  c.prec=80;percent=Decimal(f.numerator)/Decimal(f.denominator)
  return {'difference':format(a-b,'f'),'percent_fraction_numerator':str(f.numerator),'percent_fraction_denominator':str(f.denominator),'percent_rounded_two_decimals':format(percent.quantize(Decimal('.01'),rounding=ROUND_HALF_UP),'f'),'percent_rounded_whole':int(percent.quantize(Decimal('1'),rounding=ROUND_HALF_UP))}

def extract(raw):
 if not isinstance(raw,bytes) or not 0<len(raw)<=25_000_000:raise ValueError('bounded filing required')
 # No XML entity parser; only strict UTF-8 supported. Reject declaration ambiguity/NUL.
 raw.decode('utf-8')
 if b'\0' in raw or re.search(rb'<!\s*(?:DOCTYPE|ENTITY)',raw,re.I):raise ValueError('unsupported declarations/encoding')
 docs=list(re.finditer(rb'<DOCUMENT>.*?</DOCUMENT>',raw,re.S))
 if not docs or raw.count(b'<DOCUMENT>')!=len(docs) or raw.count(b'</DOCUMENT>')!=len(docs):raise ValueError('malformed document inventory')
 records=[]
 for doc in docs:
  header=doc[0].split(b'<TEXT>',1)[0];types=re.findall(rb'^<TYPE>([^\r\n]+)',header,re.M);names=re.findall(rb'^<FILENAME>([^\r\n]+)',header,re.M)
  if len(types)!=1 or len(names)!=1 or doc[0].count(b'<TEXT>')!=1 or doc[0].count(b'</TEXT>')!=1:raise ValueError('document header')
  if types[0].strip()!=b'EX-99.1':continue
  filename=names[0].strip().decode()
  if not re.fullmatch(r'[A-Za-z0-9_.-]{1,100}',filename):raise ValueError('unsafe filename')
  excluded=[(m.start(),m.end()) for m in re.finditer(rb'<!--.*?(?:-->|$)|<(script|style)\b[^>]*>.*?(?:</\1\s*>|$)',doc[0],re.S|re.I)]
  for p in re.finditer(rb'<p\b[^>]*>.*?</p>',doc[0],re.S|re.I):
   if any(p.start()<b and p.end()>a for a,b in excluded):continue
   m=PATTERN.fullmatch(plain(p[0]))
   if not m:continue
   a,b=iso(m['current_end']),iso(m['prior_end'])
   if a<=b:raise ValueError('period ordering')
   ratio=exact_ratio(m['current'],m['prior'])
   records.append({'issuer_short_label':m['label'],'current_value':m['current'].replace(',',''),'prior_value':m['prior'].replace(',',''),'current_period_end':a,'prior_period_end':b,'period_label':'quarter ended','current_period_start':None,'prior_period_start':None,'currency_symbol_as_reported':'$','currency_iso':None,'reported_percent_increase':m['reported_percent'],'arithmetic':ratio,'reported_percent_matches_nearest_whole':int(m['reported_percent'])==ratio['percent_rounded_whole'],'filename':filename,'document_sha256':digest(doc[0]),'evidence_span':{'byte_start':doc.start()+p.start(),'byte_end':doc.start()+p.end(),'sha256':digest(p[0])},'source_paragraph_text':plain(p[0]),'issuer_assertion_independently_verified':False,'accounting_comparability_verified':False})
 return {'status':'NO_SUPPORTED_COMPARISON' if not records else 'AMBIGUOUS_MULTIPLE_COMPARISONS' if len(records)>1 else 'ONE_REPORTED_TEXT_COMPARISON','records':records,'training_ready':False,'execution_ready':False}

def load_source(path):
 p=Path(path)
 if p.stat().st_size>64_000_000 or sha(p)!=ZIP_SHA:raise ValueError('source ZIP pin/bound')
 with zipfile.ZipFile(p) as z:
  names=z.namelist()
  if len(names)>64 or len(set(names))!=len(names) or any('/' in n or '\\' in n or n in {'.','..'} for n in names) or sum(i.file_size for i in z.infolist())>32_000_000:raise ValueError('ZIP inventory')
  if z.getinfo('manifest.jsonl').file_size>20_000 or z.getinfo(RAW_SHA+'.txt').file_size!=207107:raise ValueError('member bound')
  manifest=z.read('manifest.jsonl');raw=z.read(RAW_SHA+'.txt')
 if digest(manifest)!=MANIFEST_SHA or digest(raw)!=RAW_SHA or sha(p)!=ZIP_SHA:raise ValueError('source bytes changed')
 receipts=[json.loads(line,object_pairs_hook=unique_object,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('invalid constant'))) for line in manifest.splitlines()]
 matches=[x for x in receipts if x.get('accession')==ACC]
 if len(matches)!=1:raise ValueError('receipt ambiguity')
 r=matches[0];url=f'https://www.sec.gov/Archives/edgar/data/{CIK}/{ACC.replace("-","")}/{ACC}.txt'
 if r.get('issuer_cik')!=CIK or r.get('archive_file')!=RAW_SHA+'.txt' or r.get('byte_count')!=len(raw) or r.get('sha256')!=RAW_SHA or r.get('status')!='ARCHIVED_IDENTITY_VERIFIED' or r.get('url')!=url or r.get('first_public_utc') is not None or r.get('historical_availability_verified') is not False:raise ValueError('receipt identity')
 clocks=[dt.datetime.fromisoformat(r[k]) for k in ('request_utc','retrieved_utc')]
 if any(t.tzinfo is None for t in clocks) or not clocks[0]<=clocks[1]<=dt.datetime.now(dt.timezone.utc):raise ValueError('receipt clocks')
 header=raw.split(b'</SEC-HEADER>',1)[0]
 if not raw.startswith(b'<SEC-DOCUMENT>') or b'<DOCUMENT>' in header or re.findall(rb'ACCESSION NUMBER:\s*([^\r\n]+)',header)!=[ACC.encode()] or re.findall(rb'CENTRAL INDEX KEY:\s*([0-9]+)',header)!=[b'0000050292']:raise ValueError('header identity')
 for key,value in [(b'CONFORMED SUBMISSION TYPE',b'8-K'),(b'FILED AS OF DATE',b'20261113'),(b'CONFORMED PERIOD OF REPORT',b'20261112')]:
  if re.findall(re.escape(key)+rb':\s*([^\r\n]+)',header)!=[value]:raise ValueError('header dates/form')
 return raw,r

def build(raw,receipt):
 expected_url=f'https://www.sec.gov/Archives/edgar/data/{CIK}/{ACC.replace("-","")}/{ACC}.txt'
 if receipt.get('url')!=expected_url or receipt.get('issuer_cik')!=CIK or receipt.get('accession')!=ACC or receipt.get('sha256')!=RAW_SHA or receipt.get('byte_count')!=len(raw) or receipt.get('first_public_utc') is not None or receipt.get('historical_availability_verified') is not False:raise ValueError('card receipt binding')
 clocks=[dt.datetime.fromisoformat(receipt[k]) for k in ('request_utc','retrieved_utc')]
 if any(t.tzinfo is None for t in clocks) or not clocks[0]<=clocks[1]<=dt.datetime.now(dt.timezone.utc):raise ValueError('card receipt clocks')
 if digest(raw)!=RAW_SHA:raise ValueError('reviewed source required')
 e=extract(raw)
 if e['status']!='ONE_REPORTED_TEXT_COMPARISON':raise ValueError('unsupported source comparison')
 r=e['records'][0]
 if (r['issuer_short_label'],r['current_value'],r['prior_value'],r['current_period_end'],r['prior_period_end'],r['reported_percent_increase'],r['filename'])!=('IEH','10700084','7077592','2026-09-30','2025-09-30','51','ex99-1.htm') or not r['reported_percent_matches_nearest_whole']:raise ValueError('reviewed case mismatch')
 public={k:v for k,v in r.items() if k not in {'source_paragraph_text','issuer_short_label','issuer_assertion_independently_verified'}}
 return {'version':1,'id':'ieh-reported-quarterly-revenue','status':'ISSUER_REPORTED_COMPARISON_NOT_INDEPENDENTLY_COMPARABLE','generated_at':dt.datetime.now(dt.timezone.utc).isoformat(),'issuer':{'cik':'0000050292','name_as_filed':'IEH Corp','ticker':None,'security_mapping_verified':False},'title':'IEH reported higher quarterly revenue; accounting and timing review remains open','finding':'The retained release reports revenue of $10,700,084 for the quarter ended September 30, 2026 versus $7,077,592 for the quarter ended September 30, 2025, and states a 51% increase. Exact arithmetic is consistent with that rounded percentage; this is not independent accounting comparability or a trading signal.',
 'research_disposition':'REPORTED_REVENUE_COMPARISON_FOR_ORIGINAL_REPORT_REVIEW','comparison':public,'filing':{'accession':ACC,'form':'8-K','filing_date_as_reported':'2026-11-13','report_date_as_reported':'2026-11-12','release_date_as_reported':'2026-11-12','exhibit':'EX-99.1','exhibit_filename':'ex99-1.htm','retained_source_url':receipt['url'],'source_url_basis':'EXACT_RETAINED_RECEIPT_URL_NOT_FRESHLY_REQUESTED','source_current_access_verified':False},
 'provenance':{'retained_zip_sha256':ZIP_SHA,'manifest_sha256':MANIFEST_SHA,'original_submission_sha256':RAW_SHA,'original_submission_bytes':len(raw),'request_utc_as_recorded':receipt['request_utc'],'retrieved_utc_as_recorded':receipt['retrieved_utc'],'first_public_utc':None,'historical_availability_verified':False,'exact_source_context_reviewed':True,'original_10q_checked':False,'prepared_workspace_join_verified':False},
 'blockers':['Dollar symbols are reported; an explicit ISO currency code and exact quarter start dates are not stated in the supported paragraph. None are inferred.','The issuer supplies this comparison. Its underlying 10-Q, accounting policies, scope, amendments and comparability have not been independently checked.','Recorded November14 retrieval is retrospective, not first-public timing or proof of a current/new catalyst.','No matching context in the retained395-context archive-fact workspace was found; no forced prepared-data join is made.','Security identity, permitted outcomes and decision-time availability remain unverified.'],
 'next_research_steps':['Review the original quarterly financial statements and notes to establish currency, exact durations, scope and any restatement before treating growth as comparable.','Reconcile release/filing chronology and prior disclosures before classifying novelty.','Keep this as a reported financial research question, not a recommendation or probability.'],
 'training_ready':False,'execution_ready':False,'probability':None,'price_target':None,'return_estimate':None,'limitations':['Exact arithmetic validates only consistency of reported numbers, not accounting truth or business quality.','Only revenue is extracted from the supported paragraph. Other operating results, backlog and forecasts are not promoted to qualified facts.','No private contact/address or full narrative is published. Evidence offsets/hash bind the exact private original paragraph.','The reusable parser recognizes a narrow full-paragraph grammar; other formats are unsupported and multiple matches remain ambiguous.']},e

def save(path,out):
 out=Path(out).resolve()
 if out.exists() or out.is_relative_to(Path(__file__).resolve().parents[1]) or not out.parent.is_dir():raise ValueError('new trusted private output required')
 out.mkdir(mode=0o700);write_private(out/'INCOMPLETE',{});raw,r=load_source(path);card,evidence=build(raw,r);write_private(out/'evidence.json',evidence);write_private(out/'finding.json',card);write_private(out/'COMPLETE.json',{'evidence_sha256':sha(out/'evidence.json'),'finding_sha256':sha(out/'finding.json')});(out/'INCOMPLETE').unlink();return card
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--archive',required=True);p.add_argument('--out',required=True);a=p.parse_args();c=save(a.archive,a.out);print(c['id'])
