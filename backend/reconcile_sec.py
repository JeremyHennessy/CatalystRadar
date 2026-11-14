"""Reconcile archived issuer API discoveries against official daily indexes.
Only complete past UTC calendar days; missing/invalid indexes block coverage.
"""
import argparse,datetime as dt,json,re,hashlib,html
from pathlib import Path
from discover_sec import Archive,parse,stamp

def reconcile(root,user_agent,output="reconciliation.json",cached=False):
 report=json.loads((root/'report.json').read_text());universe=json.loads((root/'universe.json').read_text());ciks={int(x['cik']) for x in universe}
 start=parse(report['requested_window_start']).date();end=parse(report['cutoff']).date()
 today=dt.datetime.now(dt.timezone.utc).date()
 if end>=today: end=today-dt.timedelta(days=1) # cannot call partial current daily index complete
 arc=Archive(root,user_agent);found=set();errors=[];days=[];closed=[]
 manifest=[json.loads(x) for x in (root/'manifest.jsonl').read_text().splitlines()]
 def saved(label,url):
  matches=[x for x in manifest if x.get('path')==label and x.get('url')==url and x.get('sha256')]
  if not matches:return None,{}
  raw=(root/label).read_bytes();entry=matches[-1]
  if hashlib.sha256(raw).hexdigest()!=entry['sha256']:raise ValueError('cached evidence hash mismatch')
  return raw,entry
 calendar_url='https://www.sec.gov/submit-filings/filer-support-resources/edgar-calendar'
 cal,calmeta=saved('edgar-calendar.html',calendar_url)
 if cal is None and not cached:cal,calmeta=arc.get(calendar_url,'edgar-calendar.html')
 # Explicit, narrow manually-reviewed calendar exception. Other missing dates remain errors.
 nov11verified=False
 if cal:
  plain=html.unescape(re.sub('<[^>]+>',' ',cal.decode('utf-8')))
  nov11verified=all(t in plain for t in ['Federal Holidays in 2026','Veterans Day','Wednesday, November 11'])
 
 day=start
 while day<=end:
  if day==dt.date(2026,11,11) and nov11verified:
   closed.append({'date':day.isoformat(),'reason':'SEC EDGAR Veterans Day closure','source_sha256':calmeta['sha256']})
  elif day.weekday()<5:
   quarter=(day.month-1)//3+1;label='master.'+day.strftime('%Y%m%d')+'.idx'
   url=f'https://www.sec.gov/Archives/edgar/daily-index/{day.year}/QTR{quarter}/{label}'
   raw,meta=saved(label,url) if cached else arc.get(url,label);days.append(day.isoformat())
   if raw is None:errors.append(label+': unavailable; do not assume exchange holiday equals SEC closure')
   else:
    text=raw.decode('latin-1')
    if not any(h in text for h in ('CIK|Company Name|Form Type|Date Filed|Filename','CIK|Company Name|Form Type|Date Filed|File Name')):errors.append(label+': invalid header')
    else:
     for line in text.splitlines():
      cells=line.split('|')
      if len(cells)==5 and cells[0].isdigit() and int(cells[0]) in ciks and cells[2] in ('8-K','8-K/A'):
       acc=cells[4].rsplit('/',1)[-1].removesuffix('.txt')
       if re.fullmatch(r'\d{10}-\d{2}-\d{6}',acc):found.add(acc)
       else:errors.append(label+': invalid accession path')
  day+=dt.timedelta(days=1)
 api={x['accession'] for x in report['events'] if start<=dt.date.fromisoformat(x['filing_date_raw'])<=end}
 result={'checked_utc':stamp(),'scope':'DECLARED_ISSUERS_AND_COMPLETE_PAST_FILING_DAYS_ONLY','start_filing_day':start.isoformat(),'end_filing_day':end.isoformat(),'days_requested':days,'verified_closed_days':closed,'calendar_scope':'Nov11 2026 verified exception only; all other missing weekdays fail','index_accessions':sorted(found),'api_accessions':sorted(api),'missing_from_api':sorted(found-api),'missing_from_indexes':sorted(api-found),'errors':errors,'status':'MATCHED' if not errors and found==api else 'INCOMPLETE_OR_MISMATCH','not_verified':['First issuer public-release timestamps','Truth of extracted catalysts','Market prices and halts','Whole-market coverage']}
 with (root/output).open('x') as f:json.dump(result,f,indent=2)
 return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--user-agent',required=True);p.add_argument('--output',default='reconciliation.json');p.add_argument('--cached',action='store_true');a=p.parse_args();print(json.dumps(reconcile(Path(a.root),a.user_agent,a.output,a.cached),indent=2))
