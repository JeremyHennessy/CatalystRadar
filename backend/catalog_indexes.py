"""Reproduce metadata catalog from hash-verified archived SEC daily indexes."""
import csv,hashlib,json,argparse
from pathlib import Path

def catalog(root,output):
 manifest=[json.loads(s) for s in (root/'manifest.jsonl').read_text().splitlines()]
 result=[]
 for path in sorted(root.glob('master.*.idx')):
  raw=path.read_bytes();sha=hashlib.sha256(raw).hexdigest()
  if not any(x.get('path')==path.name and x.get('sha256')==sha and x.get('url','').startswith('https://www.sec.gov/Archives/edgar/daily-index/') for x in manifest):raise ValueError('unverified index '+path.name)
  text=raw.decode('latin-1')
  if not any(h in text for h in ['CIK|Company Name|Form Type|Date Filed|File Name','CIK|Company Name|Form Type|Date Filed|Filename']):raise ValueError('index header')
  for line in text.splitlines():
   x=line.split('|')
   if len(x)==5 and x[0].isdigit() and x[2] in ('8-K','8-K/A'):
    if x[3].replace('-','')!=path.name.split('.')[1]:raise ValueError('date mismatch')
    result.append({'issuer_cik':x[0],'issuer_name':x[1],'form':x[2],'filing_date_raw':x[3],'source_index_sha256':sha,'original_url':'https://www.sec.gov/Archives/'+x[4],'status':'INDEX_DISCOVERY_ONLY_NOT_SCREENED'})
 if len({x['original_url'] for x in result})!=len(result):raise ValueError('duplicate filing URLs require explicit resolution')
 with output.open('x') as f:
  fields=['issuer_cik','issuer_name','form','filing_date_raw','source_index_sha256','original_url','status'];w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(result)
 return {'rows':len(result),'distinct_issuers':len({x['issuer_cik'] for x in result})}
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--root',required=True);a.add_argument('--output',required=True);x=a.parse_args();print(json.dumps(catalog(Path(x.root),Path(x.output))))
