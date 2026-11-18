"""Retained Item 1.01 screen with one manually source-reviewed exchange projection."""
import argparse,datetime as dt,re,zipfile
from pathlib import Path
from financial_admission_rehearsal import plain
from filing_registrant_identity import ZIP_SHA,MANIFEST_SHA,RAW_SHA,digest,strict,span,extract as filers
from financial_pair_candidates import sha,write_private
ITEM='Entry into a Material Definitive Agreement'

def screen(raw):
 if type(raw)is not bytes or not 0<len(raw)<=25000000:raise ValueError('source bounds')
 raw.decode('utf-8','strict')
 if b'\0' in raw or raw.count(b'<SEC-HEADER>')!=1 or raw.count(b'</SEC-HEADER>')!=1:raise ValueError('header inventory')
 hs=raw.index(b'<SEC-HEADER>');he=raw.index(b'</SEC-HEADER>')
 if not hs<he<=100000:raise ValueError('header bounds')
 items=re.findall(rb'^ITEM INFORMATION:[ \t]*([^\r\n]+)',raw[hs:he],re.M)
 matches=[x for x in items if x.decode('ascii')==ITEM]
 if len(matches)>1:raise ValueError('duplicate item declaration')
 docs=list(re.finditer(rb'<DOCUMENT>.*?</DOCUMENT>',raw,re.S))
 if not docs or raw.count(b'<DOCUMENT>')!=len(docs) or raw.count(b'</DOCUMENT>')!=len(docs) or any(m[0].count(b'<DOCUMENT>')!=1 for m in docs):raise ValueError('document inventory')
 prim=[];exhibits=[]
 for d in docs:
  h=d[0].split(b'<TEXT>',1)[0];types=re.findall(rb'^<TYPE>([^\r\n]+)',h,re.M);names=re.findall(rb'^<FILENAME>([^\r\n]+)',h,re.M)
  if len(types)!=1 or len(names)!=1 or b'<TEXT>' not in d[0] or not re.fullmatch(rb'[A-Za-z0-9_.-]{1,160}',names[0]):raise ValueError('document fields')
  kind=types[0].decode('ascii');name=names[0].decode('ascii')
  record={'type_as_filed':kind,'filename':name,'source_span':span(raw,d.start(),d.end())}
  if kind in ('8-K','8-K/A'):prim.append(record)
  if re.fullmatch(r'EX-(?:4|10)\.[0-9]{1,3}',kind):exhibits.append(record)
 if len(prim)!=1:raise ValueError('primary ambiguity')
 return {'status':'AMENDMENT_REQUIRES_REVIEW' if prim[0]['type_as_filed']=='8-K/A' else 'ITEM_1_01_DECLARED_REQUIRES_DOCUMENT_REVIEW' if matches else 'NO_ITEM_1_01_HEADER_DECLARATION_NOT_NO_AGREEMENT','item_1_01_declared':bool(matches),'primary':prim[0],'contract_or_security_exhibits':exhibits,'event_verified':False}

def reviewed_exchange(raw):
 if digest(raw)!=RAW_SHA:raise ValueError('reviewed original pin')
 p=raw[27877:29552];text=plain(p)
 checks=['On November 13, 2026','completed the previously announced exchange transactions','dated as of October 29, 2026','5.500% Senior Notes due 2028 of Holdings','$173,679,000 aggregate principal amount','$121,086,000 aggregate principal amount of 10.250%','due 2030 newly issued by Xerox','3,872,062 shares of common stock','of Holdings']
 if not all(s in text for s in checks):raise ValueError('reviewed source terms')
 if 'Xerox Corporation, as issuer, Xerox Holdings Corporation, as parent guarantor' not in plain(raw[43266:43803]) or 'Exchange Agreement, dated as of November 13, 2026' not in plain(raw[46000:46461]):raise ValueError('reviewed instrument roles/dates')
 if 'Holdings issued 3,872,062 shares' not in plain(raw[41461:41840]):raise ValueError('equity issuer scope')
 return {'status':'ISSUER_REPORTED_COMPLETED_EXCHANGE_NOT_INDEPENDENT_SETTLEMENT','settlement_date_as_reported':'2026-11-13','support_agreement_date_as_reported':'2026-10-29','exchange_agreement_date_as_reported':'2026-11-13','previously_announced_as_reported':True,'exchanged_old_notes':{'obligor_cik':'0001770450','obligor_name':'Xerox Holdings Corporation','principal_as_reported':'173679000','unit_as_reported':'dollars','currency_iso':None,'coupon_percent_as_reported':'5.500','maturity_year_as_reported':'2028'},'new_notes':{'issuer_cik':'0000108772','issuer_name':'Xerox Corporation','principal_as_reported':'121086000','unit_as_reported':'dollars','currency_iso':None,'coupon_percent_as_reported':'10.250','maturity_year_as_reported':'2030','parent_guarantor_cik':'0001770450'},'equity_component':{'issuer_cik':'0001770450','issuer_name':'Xerox Holdings Corporation','common_shares_as_reported':'3872062','share_price':None,'equity_value':None},'source_spans':{'exchange_paragraph':span(raw,27877,29552),'equity_issuance_paragraph':span(raw,41461,41840),'indenture_roles_table_row':span(raw,43266,43803),'exchange_agreement_table_row':span(raw,46000,46461)},'independent_settlement_verified':False,'net_debt_change':None,'transaction_value':None,'economic_gain':None,'training_ready':False,'execution_ready':False}

def build(archive):
 if Path(archive).stat().st_size>64000000 or sha(archive)!=ZIP_SHA:raise ValueError('archive pin')
 rows=[]
 with zipfile.ZipFile(archive) as z:
  ns=z.namelist()
  if len(ns)>64 or len(ns)!=len(set(ns)) or sum(i.file_size for i in z.infolist())>32000000 or z.getinfo('manifest.jsonl').file_size>20000:raise ValueError('archive bounds')
  manifest=z.read('manifest.jsonl')
  if digest(manifest)!=MANIFEST_SHA:raise ValueError('manifest pin')
  rs=[strict(x) for x in manifest.splitlines()]
  if len(rs)!=10 or len({r['accession'] for r in rs})!=10:raise ValueError('cohort inventory')
  for r in sorted(rs,key=lambda r:r['accession']):
   name=r['sha256']+'.txt'
   if r['archive_file']!=name or z.getinfo(name).file_size!=r['byte_count'] or r['byte_count']>25000000:raise ValueError('member binding')
   raw=z.read(name)
   if digest(raw)!=r['sha256'] or r['status']!='ARCHIVED_IDENTITY_VERIFIED':raise ValueError('source pin/status')
   identity=filers(raw,r['accession']);ids=[f['cik'] for f in identity['filers']]
   if r['issuer_cik'].zfill(10) not in ids or r['url']!=f'https://www.sec.gov/Archives/edgar/data/{int(r["issuer_cik"])}/{r["accession"].replace("-","")}/{r["accession"]}.txt':raise ValueError('identity/URL')
   a,b=[dt.datetime.fromisoformat(r[k]) for k in ('request_utc','retrieved_utc')]
   if a.tzinfo is None or b.tzinfo is None or not a<=b<=dt.datetime.now(dt.timezone.utc) or r['first_public_utc']is not None or r['historical_availability_verified']is not False:raise ValueError('clock scope')
   result=screen(raw);finding=None
   if r['sha256']==RAW_SHA:
    if ids!=['0001770450','0000108772'] or result['status']!='ITEM_1_01_DECLARED_REQUIRES_DOCUMENT_REVIEW':raise ValueError('reviewed identity/category')
    finding=reviewed_exchange(raw)
   rows.append({'accession':r['accession'],'filers_as_reported':[{'cik':f['cik'],'name_as_filed':f['name_as_filed']} for f in identity['filers']],'source_url':r['url'],'source_sha256':r['sha256'],'source_bytes':len(raw),'source_observed_utc_as_recorded':r['retrieved_utc'],'first_public_utc':None,'historical_availability_verified':False,'reviewed_finding':finding,**result})
 if sha(archive)!=ZIP_SHA:raise ValueError('archive changed')
 return {'version':1,'category':'MATERIAL_DEFINITIVE_AGREEMENT_HEADER_AND_ORIGINAL_REVIEW','selection':'ALL_TEN_RETAINED_PACKAGES_FIXED_HEADER_RULE_RETROSPECTIVE_NOT_REPRESENTATIVE','counts':{'packages':len(rows),'item_1_01_declared':sum(r['item_1_01_declared'] for r in rows),'source_reviewed_findings':sum(r['reviewed_finding']is not None for r in rows),'no_item_declaration':sum(not r['item_1_01_declared'] for r in rows)},'packages':rows,'provenance':{'archive_sha256':ZIP_SHA,'manifest_sha256':MANIFEST_SHA},'limitations':['All ten retained packages are screened by exact filed header item, not a market-wide or unbiased discovery sample.','No Item1.01 declaration means no such header label in this package, not no contract, material agreement or corporate event.','Exhibit4/10 inventory is document evidence, not proof every listed instrument is new, effective or independently executed.','Only the exact independently inspected Xerox original receives a structured exchange finding; the general screen does not parse legal obligations automatically.','Xerox Corporation and Xerox Holdings Corporation remain distinct. Debt, guarantee and equity roles are attributed only to explicit reviewed context.','The source says previously announced and completed; this is issuer reporting, not independent settlement or first-public authentication.','Dollar symbols do not independently establish ISO currency. No par-value-as-price, total consideration, equity value, net debt change, return or economic gain is computed.','Public output excludes full narrative, contacts and addresses. Training and execution remain disabled.'], 'training_ready':False,'execution_ready':False}

def save(archive,out):
 out=Path(out).resolve()
 if out.exists() or not out.parent.is_dir() or out.is_relative_to(Path(__file__).resolve().parents[1]):raise ValueError('new private output required')
 out.mkdir(mode=0o700);write_private(out/'INCOMPLETE',{});result=build(archive);write_private(out/'agreements.json',result);write_private(out/'COMPLETE.json',{'agreements_sha256':sha(out/'agreements.json')});(out/'INCOMPLETE').unlink();return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--archive',required=True);p.add_argument('--out',required=True);a=p.parse_args();save(a.archive,a.out)
