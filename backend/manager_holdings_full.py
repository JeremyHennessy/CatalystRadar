"""Offline per-filing shards of reviewed fields; no numeric economic aggregation."""
import argparse,hashlib,json,re
from pathlib import Path
from manager_holdings_sample import build

def encoded(value):
    return (json.dumps(value,indent=2)+'\n').encode()

def project(audit):
    if audit['scope']!='COMPLETE_SELECTED_FILING_ROWS_NOT_COMPLETE_PORTFOLIO':raise ValueError('full audit required')
    files={};entries=[]
    for filing in audit['filings']:
        acc=filing['accession']
        if not re.fullmatch(r'\d{10}-\d{2}-\d{6}',acc):raise ValueError('accession')
        if filing['displayed_rows']!=filing['source_holding_rows'] or filing['omitted_from_sample_rows']!=0 or len(filing['holdings'])!=filing['source_holding_rows']:raise ValueError('incomplete rows')
        name=acc+'.json'
        if name in files:raise ValueError('duplicate filing')
        payload={'version':1,'scope':audit['scope'],'source':audit['source'],'filing':filing,'limitations':audit['limitations'],'training_ready':False,'execution_ready':False}
        data=encoded(payload)
        if len(data)>1000000:raise ValueError('shard byte bound')
        files[name]=data
        entries.append({k:filing[k] for k in ('manager_cik','accession','report_period_as_filed','source_holding_rows')}|{'path':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
    manifest={'version':1,'scope':audit['scope'],'selection':audit['selection'],'source':audit['source'],'filings':entries,'limitations':audit['limitations'],'training_ready':False,'execution_ready':False}
    files['manifest.json']=encoded(manifest)
    return files

def write_bundle(files,destination):
    # All source validation and serialization finishes before any output is created.
    target=Path(destination);target.mkdir(exist_ok=False)
    for name,data in files.items():
        with (target/name).open('xb') as f:f.write(data)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('database');p.add_argument('archive');p.add_argument('destination');a=p.parse_args()
    files=project(build(a.database,a.archive,all_selected_rows=True));write_bundle(files,a.destination)
