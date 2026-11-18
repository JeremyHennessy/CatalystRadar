"""Retained SEC FILER identity annotation; never merge issuers or assign facts."""
import argparse,datetime as dt,hashlib,json,re,zipfile
from pathlib import Path
from financial_pair_candidates import sha,write_private
from private_prices import unique_object
ZIP_SHA='0f92e2c02a597b14f08c29395ae2fc9b87f2db580016e632c8d76c3059e449c0'
RAW_SHA='1e6110051c0653b7ac636de5bee60ec2feed9a91c59621470ac5fd0dafb1234e'
MANIFEST_SHA='ac6316ad597b9a931613c71e4f1442425f5f83c873d47ba17192f0c1b6a2274a'
META_SHA='7c6399e2da54dc6adc8ebc3578ba46c366611b25aa7ddec51eee4c7532c8a243'
SCAN_SHA='fbc6dc9b0287a113ab2f2ecdd61f4a7810fad525040c0afdbb37e1ea056f8db9'
SCAN_PATH='data/sec-observations/20261117T195421146121Z.json'
ACC='0001193125-26-460692'
def digest(raw):return hashlib.sha256(raw).hexdigest()
def strict(raw):return json.loads(raw,object_pairs_hook=unique_object,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('nonfinite JSON')))
def span(raw,start,end):return {'byte_start':start,'byte_end':end,'sha256':digest(raw[start:end])}
def extract(raw,accession):
 if not isinstance(raw,bytes) or not 0<len(raw)<=25000000 or not re.fullmatch('[0-9]{10}-[0-9]{2}-[0-9]{6}',accession):raise ValueError('source bounds/identity')
 if not raw.startswith(b'<SEC-DOCUMENT>') or raw.count(b'<SEC-HEADER>')!=1 or raw.count(b'</SEC-HEADER>')!=1:raise ValueError('header inventory')
 start=raw.index(b'<SEC-HEADER>');end=raw.index(b'</SEC-HEADER>')+len(b'</SEC-HEADER>')
 if not start<end<=100000:raise ValueError('header bound')
 h=raw[start:end];h.decode('ascii')
 if b'\0' in h or b'<DOCUMENT>' in h or re.search(rb'<!\s*(?:DOCTYPE|ENTITY)',h,re.I):raise ValueError('unsupported header')
 if re.findall(rb'^ACCESSION NUMBER:[ \t]*([^\r\n]+)',h,re.M)!=[accession.encode()]:raise ValueError('accession')
 filers=list(re.finditer(rb'^FILER:[ \t]*\r?$',h,re.M))
 if not 1<=len(filers)<=10:raise ValueError('filer bounds')
 records=[]
 for n,m in enumerate(filers):
  bs=m.end();be=filers[n+1].start() if n+1<len(filers) else len(h)
  block=h[bs:be]
  fields={}
  for label in ('COMPANY CONFORMED NAME','CENTRAL INDEX KEY'):
   hits=list(re.finditer(rb'^[ \t]+COMPANY DATA:[ \t]*\r?$',block,re.M))
   values=list(re.finditer(rb'^[ \t]+'+label.encode()+rb':[ \t]*([^\r\n]+)',block,re.M))
   if len(hits)!=1 or len(values)!=1:raise ValueError('filer field ambiguity')
   v=values[0]
   boundary=re.search(rb'^[ \t]+FILING VALUES:',block,re.M)
   if not boundary or not hits[0].end()<v.start()<boundary.start():raise ValueError('filer field role')
   fields[label]=(v[1].decode(),span(raw,start+bs+v.start(1),start+bs+v.end(1)))
  ci,ci_span=fields['CENTRAL INDEX KEY'];name,name_span=fields['COMPANY CONFORMED NAME']
  if not re.fullmatch('[0-9]{10}',ci) or int(ci)==0 or not 1<=len(name)<=200 or any(ord(c)<32 for c in name):raise ValueError('filer field shape')
  records.append({'cik':ci,'name_as_filed':name,'role':'FILER','field_spans':{'cik':ci_span,'name':name_span}})
 ciks=[r['cik'] for r in records]
 if len(set(ciks))!=len(ciks) or re.findall(rb'CENTRAL INDEX KEY:[ \t]*([^\r\n]+)',h)!=[x.encode() for x in ciks]:raise ValueError('duplicate/unclassified identity')
 return {'accession':accession,'filers':records,'multiple_filers':len(records)>1,'header_span':span(raw,start,end),'entities_interchangeable':False,'facts_propagated_between_filers':False,'security_mapping_verified':False}

def pinned(path,pin,bound):
 p=Path(path)
 with p.open('rb') as f:raw=f.read(bound+1)
 if len(raw)>bound or digest(raw)!=pin:raise ValueError('pinned bytes')
 return raw

def build(archive,root):
 archive=Path(archive);root=Path(root)
 if archive.stat().st_size>64000000 or sha(archive)!=ZIP_SHA:raise ValueError('ZIP pin')
 with zipfile.ZipFile(archive) as z:
  names=z.namelist()
  if len(names)>64 or len(set(names))!=len(names) or any('/' in n or '\\' in n for n in names) or sum(x.file_size for x in z.infolist())>32000000:raise ValueError('ZIP bounds')
  if z.getinfo(RAW_SHA+'.txt').file_size!=1983577 or z.getinfo('manifest.jsonl').file_size>20000:raise ValueError('member bounds')
  raw=z.read(RAW_SHA+'.txt');manifest=z.read('manifest.jsonl')
 if digest(raw)!=RAW_SHA or digest(manifest)!=MANIFEST_SHA or sha(archive)!=ZIP_SHA:raise ValueError('retained bytes')
 receipts=[strict(line) for line in manifest.splitlines()];rs=[r for r in receipts if r['accession']==ACC]
 if len(rs)!=1:raise ValueError('receipt identity')
 receipt=rs[0];url=f'https://www.sec.gov/Archives/edgar/data/108772/{ACC.replace("-","")}/{ACC}.txt'
 if receipt['issuer_cik']!='108772' or receipt['sha256']!=RAW_SHA or receipt['byte_count']!=len(raw) or receipt['url']!=url or receipt['status']!='ARCHIVED_IDENTITY_VERIFIED' or receipt['first_public_utc'] is not None or receipt['historical_availability_verified'] is not False:raise ValueError('receipt binding')
 e=extract(raw,ACC)
 if [(r['cik'],r['name_as_filed']) for r in e['filers']]!=[('0001770450','Xerox Holdings Corp'),('0000108772','XEROX CORP')]:raise ValueError('reviewed filers')
 meta=strict(pinned(root/('data/sec-snapshots/'+META_SHA+'.json'),META_SHA,200000))
 scan=strict(pinned(root/SCAN_PATH,SCAN_SHA,200000))
 source=[s for s in scan['sources'] if s['sha256']==META_SHA]
 recent=meta['filings']['recent'];indices=[n for n,a in enumerate(recent['accessionNumber']) if a==ACC]
 if len(source)!=1 or len(indices)!=1 or meta['cik']!='0001770450' or meta['name']!='Xerox Holdings Corp' or source[0]['status']!=200 or source[0]['byte_count']!=106090:raise ValueError('metadata association')
 i=indices[0]
 if (recent['form'][i],recent['filingDate'][i],recent['fileNumber'][i])!=('8-K','2026-11-13','001-39013'):raise ValueError('metadata filing')
 clocks=[dt.datetime.fromisoformat(t) for t in (receipt['request_utc'],receipt['retrieved_utc'],source[0]['request_utc'],source[0]['retrieved_utc'])]
 if any(c.tzinfo is None for c in clocks) or not clocks[0]<=clocks[1]<=clocks[2]<=clocks[3]<=dt.datetime.now(dt.timezone.utc):raise ValueError('observation clocks')
 return {'version':1,'id':'xerox-dual-filer-identity','status':'BOTH_CIKS_EXPLICIT_FILERS_NOT_INTERCHANGEABLE','accession':ACC,'form':'8-K','filing_date_as_reported':'2026-11-13','identity_evidence':e,
 'finding':'The retained submission explicitly lists Xerox Holdings Corp (0001770450) and XEROX CORP (0000108772) as separate FILER entries. Different CIK associations for this accession are supported by the two-filer header; neither CIK is replaced or merged.',
 'associations':[{'role':'RETAINED_ORIGINAL_ARCHIVE_RECEIPT','cik':'0000108772','source_url':url,'source_sha256':RAW_SHA,'observed_utc_as_recorded':receipt['retrieved_utc']},{'role':'RETAINED_SUBMISSIONS_METADATA','cik':'0001770450','source_url':source[0]['url'],'source_sha256':META_SHA,'observed_utc_as_recorded':source[0]['retrieved_utc']}],
 'provenance':{'retained_zip_sha256':ZIP_SHA,'manifest_sha256':MANIFEST_SHA,'original_submission_sha256':RAW_SHA,'original_submission_bytes':len(raw),'metadata_snapshot_sha256':META_SHA,'metadata_scan_sha256':SCAN_SHA,'first_public_utc':None,'historical_availability_verified':False,'current_source_access_verified':False},
 'limitations':['Co-filing establishes two named filing registrants, not interchangeable legal entities, a corporate hierarchy or a verified security relationship.','A fact or obligation must be attributed to its explicit document context; nothing is propagated from one filer to the other.','Existing saved issuer associations, discrepancy history and held research reports remain unchanged. This is a separate first-layer identity annotation.','Names and CIKs are header-as-filed. No current name/ticker mapping, first-public timestamp, event novelty or financial qualification is inferred.','Only allowlisted identity fields and byte-span hashes are published; no addresses, contacts, signatures or full source narrative.'],
 'training_ready':False,'execution_ready':False,'issuer_merge_performed':False,'facts_reassigned':False}

def save(archive,root,out):
 out=Path(out).resolve()
 if out.exists() or not out.parent.is_dir() or out.is_relative_to(Path(__file__).resolve().parents[1]):raise ValueError('new private output required')
 out.mkdir(mode=0o700);write_private(out/'INCOMPLETE',{});result=build(archive,root);write_private(out/'annotation.json',result);write_private(out/'COMPLETE.json',{'annotation_sha256':sha(out/'annotation.json')});(out/'INCOMPLETE').unlink();return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--archive',required=True);p.add_argument('--root',required=True);p.add_argument('--out',required=True);a=p.parse_args();save(a.archive,a.root,a.out)
