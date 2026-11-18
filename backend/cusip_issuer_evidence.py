"""One pinned retrospective issuer/security disclosure; never a historical mapping."""
import argparse, datetime as dt, hashlib, json, re, sqlite3, zipfile
from pathlib import Path
from filing_registrant_identity import ZIP_SHA, MANIFEST_SHA, extract, strict, digest, span
from financial_pair_candidates import sha, write_private
RAW_SHA='7ee77f6bef8c0f9639a5a695f0119cab7d57dc917d961bd3bdef5af6e2df9e42'
ACC='0001628280-26-073875'
CUSIP='493267702'
FTD_SHA='360491837fa5a8fd45d9d7c3b6b06a19324954bc839e203f2ad6235e88b14cae'
HOLDINGS_SHA='5117bb2573288481d336dde11232ffb8bc64cb04a495f0fc179a64bf0e2aafda'

def rowhash(row):
 return digest(json.dumps(list(row),ensure_ascii=True,separators=(',',':')).encode())

def source_evidence(raw):
 if digest(raw)!=RAW_SHA:raise ValueError('original pin')
 header=extract(raw,ACC)
 if [(f['cik'],f['name_as_filed']) for f in header['filers']]!=[('0000091576','KEYCORP /NEW/')]:raise ValueError('issuer identity')
 docs=list(re.finditer(rb'<DOCUMENT>.*?</DOCUMENT>',raw,re.S))
 selected=[m for m in docs if b'<TYPE>EX-99.1\n' in m[0][:200] and b'<FILENAME>exhibit991pressreleasedate.htm\n' in m[0][:200]]
 if len(selected)!=1 or raw.count(b'493267702')!=1:raise ValueError('source ambiguity')
 m=selected[0];at=raw.index(CUSIP.encode());start=raw.rfind(b'<div',m.start(),at);end=raw.index(b'</div>',at)+6
 paragraph=raw[start:end]
 for phrase in (b'November 13, 2026',b'1&#47;40th',b'Series E Fixed-to-Floating Rate Perpetual Non-Cumulative Preferred Stock',b'December 15, 2026',b'intention to redeem'):
  if phrase not in paragraph:raise ValueError('reviewed source context')
 return {'filers':header['filers'],'exhibit_filename':'exhibit991pressreleasedate.htm','exhibit_span':span(raw,m.start(),m.end()),'disclosure_span':span(raw,start,end),'cusip_span':span(raw,at,at+9)}

def selected_rows(ftd,holdings):
 # Exact CUSIP only. Never use source ticker, issuer name or manager CIK to join.
 with sqlite3.connect('file:'+str(Path(ftd).resolve())+'?mode=ro',uri=True) as d:
  rows=d.execute('SELECT rowid,* FROM ftd WHERE cusip=? ORDER BY settlement_date',(CUSIP,)).fetchall()
  if len(rows)!=4 or [r[1] for r in rows]!=['20261016','20261019','20261021','20261026']:raise ValueError('reviewed FTD scope')
  f=[{'source_rowid':r[0],'settlement_date_as_reported':r[1],'cusip_as_reported':r[2],'symbol_as_reported':r[3],'description_as_reported':r[5],'full_source_row_sha256':rowhash(r[1:])} for r in rows]
 with sqlite3.connect('file:'+str(Path(holdings).resolve())+'?mode=ro',uri=True) as d:
  rows=d.execute('SELECT rowid,* FROM holdings_infotable WHERE CUSIP=? ORDER BY rowid',(CUSIP,)).fetchall()
  if len(rows)!=2:raise ValueError('reviewed 13F scope')
  h=[]
  for r in rows:
   sub=d.execute('SELECT rowid,* FROM holdings_submission WHERE ACCESSION_NUMBER=?',(r[1],)).fetchall()
   if len(sub)!=1:raise ValueError('submission identity')
   s=sub[0]
   h.append({'source_rowid':r[0],'accession':r[1],'name_as_reported':r[3],'class_as_reported':r[4],'cusip_as_reported':r[5],'full_source_row_sha256':rowhash(r[1:]),'submission_rowid':s[0],'submission_row_sha256':rowhash(s[1:]),'filing_date_as_reported':s[2],'form_as_reported':s[3],'report_period_as_reported':s[5]})
  if [r['class_as_reported'] for r in h]!=['PUBLIC','Common Stock']:raise ValueError('reviewed class labels')
 return f,h

def build(archive,ftd,holdings):
 for p,pin in ((archive,ZIP_SHA),(ftd,FTD_SHA),(holdings,HOLDINGS_SHA)):
  if sha(p)!=pin:raise ValueError('input pin')
 with zipfile.ZipFile(archive) as z:
  ns=z.namelist()
  if len(ns)>64 or len(ns)!=len(set(ns)) or sum(x.file_size for x in z.infolist())>32000000:raise ValueError('archive bounds')
  if z.getinfo(RAW_SHA+'.txt').file_size!=250966 or z.getinfo('manifest.jsonl').file_size>20000:raise ValueError('member bounds')
  raw=z.read(RAW_SHA+'.txt');manifest=z.read('manifest.jsonl')
 if digest(manifest)!=MANIFEST_SHA:raise ValueError('manifest pin')
 rs=[strict(x) for x in manifest.splitlines()];rs=[r for r in rs if r['accession']==ACC]
 if len(rs)!=1:raise ValueError('receipt count')
 r=rs[0];url=f'https://www.sec.gov/Archives/edgar/data/91576/{ACC.replace("-","")}/{ACC}.txt'
 if (r['issuer_cik'],r['sha256'],r['byte_count'],r['url'],r['status'],r['first_public_utc'],r['historical_availability_verified'])!=('91576',RAW_SHA,len(raw),url,'ARCHIVED_IDENTITY_VERIFIED',None,False):raise ValueError('receipt binding')
 a,b=[dt.datetime.fromisoformat(r[k]) for k in ('request_utc','retrieved_utc')]
 if a.tzinfo is None or b.tzinfo is None or not a<=b<=dt.datetime.now(dt.timezone.utc):raise ValueError('receipt clocks')
 e=source_evidence(raw);f,h=selected_rows(ftd,holdings)
 for p,pin in ((archive,ZIP_SHA),(ftd,FTD_SHA),(holdings,HOLDINGS_SHA)):
  if sha(p)!=pin:raise ValueError('input changed')
 return {'version':1,'id':'keycorp-retrospective-cusip-evidence','status':'RETROSPECTIVE_EXACT_CUSIP_REVIEW_NOT_HISTORICAL_MAPPING','issuer_cik_as_filed':'0000091576','issuer_name_as_filed':'KEYCORP /NEW/','cusip_as_reported':CUSIP,'accession':ACC,'disclosure_date_as_reported':'2026-11-13','source_url':url,'exhibit_url':url.rsplit('/',1)[0]+'/exhibit991pressreleasedate.htm','links_constructed_not_fetched_this_audit':True,'issuer_reported_security_description':'Depositary shares each representing a 1/40th ownership interest in Series E Fixed-to-Floating Rate Perpetual Non-Cumulative Preferred Stock','notice_status':'INTENTION_TO_REDEEM_NOT_VERIFIED_COMPLETION','planned_redemption_date_as_reported':'2026-12-15','source_evidence':e,'ftd_exact_cusip_records':f,'holdings_exact_cusip_records':h,'finding':'The later issuer disclosure provides class context for the same CUSIP string in four earlier FTD rows and two earlier 13F records. One 13F record says Common Stock; original labels remain unchanged and require review.','provenance':{'original_zip_sha256':ZIP_SHA,'original_member_sha256':RAW_SHA,'manifest_sha256':MANIFEST_SHA,'ftd_database_sha256':FTD_SHA,'holdings_database_sha256':HOLDINGS_SHA,'source_observed_utc_as_recorded':r['retrieved_utc'],'first_public_utc':None},'limitations':['November issuer evidence is later than the October settlement dates and June holdings report periods. No historical effective interval or contemporary availability is established.','Exact CUSIP string correspondence is a retrospective review lead, not a verified historical identity join, correction of filed class labels or conversion between preferred and common shares.','Notice of intended redemption is not completed redemption, current listing or current security status.','13F manager identity is not held issuer identity. No position values, quantities, ownership flows or trades are inferred.','FTD amounts are net outstanding settlement failures, not short interest or manipulation; no amounts or daily sums are published here.','This single retained issuer disclosure is not a complete CUSIP master, class history or corporate-action feed.'], 'historical_mapping_verified':False,'class_labels_corrected':False,'current_security_identity_verified':False,'redemption_completion_verified':False,'training_ready':False,'execution_ready':False}

def save(archive,ftd,holdings,out):
 out=Path(out).resolve()
 if out.exists() or not out.parent.is_dir() or out.is_relative_to(Path(__file__).resolve().parents[1]):raise ValueError('new private output required')
 out.mkdir(mode=0o700);write_private(out/'INCOMPLETE',{});result=build(archive,ftd,holdings);write_private(out/'annotation.json',result);write_private(out/'COMPLETE.json',{'annotation_sha256':sha(out/'annotation.json')});(out/'INCOMPLETE').unlink();return result
if __name__=='__main__':
 p=argparse.ArgumentParser()
 for key in ('archive','ftd','holdings','out'):p.add_argument('--'+key,required=True)
 a=p.parse_args();save(a.archive,a.ftd,a.holdings,a.out)
