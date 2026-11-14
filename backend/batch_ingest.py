"""Bounded latest-day SEC full-text archival and observational extraction.
Document classifications are not bullish signals. No decisions or orders.
"""
import argparse,csv,datetime as dt,hashlib,json,re,html
from pathlib import Path
from zoneinfo import ZoneInfo
from discover_sec import Archive,stamp

def extract(raw,accession,issuer_cik=None):
 if b'<SEC-DOCUMENT>' not in raw or accession.encode() not in raw:raise ValueError('invalid original SEC submission')
 headers=raw.split(b'<DOCUMENT>',1)[0]
 accession_header=re.search(rb'ACCESSION NUMBER:\s*([^\r\n]+)',headers)
 if not accession_header or accession_header.group(1).decode().strip()!=accession:raise ValueError('accession header mismatch')
 header_ciks=sorted(set(int(x) for x in re.findall(rb'CENTRAL INDEX KEY:\s*(\d+)',headers)))
 if issuer_cik is not None and int(issuer_cik) not in header_ciks:raise ValueError('issuer absent from filing header')
 a=re.search(rb'<ACCEPTANCE-DATETIME>(\d{14})',headers)
 if not a:raise ValueError('acceptance header absent')
 # EDGAR complete submission acceptance header is Eastern local time, not UTC.
 local=dt.datetime.strptime(a.group(1).decode(),'%Y%m%d%H%M%S').replace(tzinfo=ZoneInfo('America/New_York'))
 accepted=local.astimezone(dt.timezone.utc).isoformat()
 docs=[];items=set()
 for match in re.finditer(rb'<DOCUMENT>(.*?)</DOCUMENT>',raw,re.S):
  block=match.group(1)
  typ=re.search(rb'<TYPE>([^\r\n]+)',block);name=re.search(rb'<FILENAME>([^\r\n]+)',block)
  if not typ:continue
  kind=typ.group(1).decode('ascii',errors='replace').strip()
  if not (kind in ('8-K','8-K/A') or re.match(r'^EX-(?:99|10)(?:\.|$)',kind)):continue
  text=html.unescape(re.sub(r'<[^>]*>',' ',block.decode('utf-8',errors='replace')))
  text=' '.join(text.split())
  # Only label headings in report; references are possible, so explicitly unverified.
  labels=sorted(set(re.findall(r'\bItem\s+([1-9]\.\d{2})\b',text,re.I))) if kind in ('8-K','8-K/A') else []
  items.update(labels)
  docs.append({'type':kind,'filename':name.group(1).decode(errors='replace') if name else None,'raw_document_byte_start':match.start(),'raw_document_byte_end':match.end(),'raw_document_sha256':hashlib.sha256(match.group(0)).hexdigest(),'item_mentions_not_verified_headings':labels,'word_count_approx':len(text.split()),'possible_earnings_release':kind.startswith('EX-99') and bool(re.search(r'financial results|quarter.*results|results.*quarter',text,re.I))})
 return {'header_ciks':header_ciks,'multi_entity_header':len(header_ciks)>1,'sec_accepted_utc':accepted,'acceptance_header_raw':a.group(1).decode(),'acceptance_timezone_interpretation':'America/New_York','first_public_utc':None,'first_public_status':'UNVERIFIED_MAY_PRECEDE_SEC_ACCEPTANCE','header_item_descriptions':[x.decode(errors='replace').strip() for x in re.findall(rb'ITEM INFORMATION:\s*([^\r\n]+)',headers)],'selected_document_inventory':docs,'item_mentions_not_verified_headings':sorted(items),'classification':'OBSERVATIONAL_DOCUMENT_INVENTORY_ONLY','eligible_catalyst':False}

def run(index_root,out,filing_day,limit,agent):
 if not 1<=limit<=20:raise ValueError('bounded limit 1..20')
 out.mkdir(parents=True,exist_ok=False)
 index=index_root/f'master.{filing_day}.idx';raw=index.read_bytes();sha=hashlib.sha256(raw).hexdigest()
 manifests=[json.loads(x) for x in (index_root/'manifest.jsonl').read_text().splitlines()]
 if not any(m.get('path')==index.name and m.get('sha256')==sha for m in manifests):raise ValueError('unverified source index')
 lines=[]
 for line in raw.decode('latin-1').splitlines():
  x=line.split('|')
  if len(x)==5 and x[0].isdigit() and x[2]=='8-K':
   if x[3].replace('-','')!=filing_day:raise ValueError('index row date mismatch')
   lines.append({'cik':x[0],'issuer':x[1],'form':x[2],'filing_date_raw':x[3],'path':x[4]})
 lines.sort(key=lambda x:(int(x['cik']),x['path']))
 selected=[];seen=set()
 for r in lines:
  if r['cik'] in seen:continue
  selected.append(r);seen.add(r['cik'])
  if len(selected)==limit:break
 selection={'created_utc':stamp(),'source_index':str(index),'source_index_sha256':sha,'filing_day':filing_day,'rule':'first distinct issuer CIKs ascending numeric, first accession path lexical, form8-K only','limit':limit,'eligible_index_rows':len(lines),'selected':selected,'purpose':'technical ingestion sample, not investment universe or selection'}
 (out/'selection.json').write_text(json.dumps(selection,indent=2))
 arc=Archive(out,agent);results=[];blocked=False
 for row in selected:
  acc=row['path'].rsplit('/',1)[-1].removesuffix('.txt')
  event={'issuer_cik':row['cik'],'issuer':row['issuer'],'accession':acc,'status':'PENDING','observed_utc':None}
  if blocked:event.update(status='NOT_ATTEMPTED_AFTER_HTTP_BLOCK');results.append(event);continue
  url='https://www.sec.gov/Archives/'+row['path']
  body,meta=arc.get(url,acc+'.txt');event['archive']=meta;event['observed_utc']=meta['retrieved_utc']
  if body is None:
   event.update(status='FETCH_FAILED');blocked='403' in meta.get('error','') or '429' in meta.get('error','')
  else:
   try:
    event.update(extract(body,acc,row['cik']));event['status']='ARCHIVED_NOT_ELIGIBLE'
    if dt.datetime.fromisoformat(event['sec_accepted_utc'])>dt.datetime.fromisoformat(event['observed_utc']):raise ValueError('future acceptance relative to retrieval')
   except Exception as e:event.update(status='PARSE_FAILED',error=str(e))
  results.append(event)
  # Checkpoint after each document; no simulated events generated.
  with (out/'results.jsonl').open('a') as f:f.write(json.dumps(event)+'\n')
 summary={'completed_utc':stamp(),'selected':len(selected),'archived':sum(r['status']=='ARCHIVED_NOT_ELIGIBLE' for r in results),'results':results,'mode':'OBSERVATION_ONLY','first_public_timestamps_verified':0,'eligible_catalysts':0,'orders':[],'fills':[],'coverage':'BOUNDED_DETERMINISTIC_TECHNICAL_SAMPLE_NOT_COMPLETE_MARKET','max_request_rate_per_second':0.5}
 (out/'summary.json').write_text(json.dumps(summary,indent=2));return summary
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--index-root',required=True);p.add_argument('--output',required=True);p.add_argument('--filing-day',required=True);p.add_argument('--limit',type=int,default=10);p.add_argument('--user-agent',required=True);a=p.parse_args();r=run(Path(a.index_root),Path(a.output),a.filing_day,a.limit,a.user_agent);print(json.dumps({k:v for k,v in r.items() if k!='results'},indent=2))
