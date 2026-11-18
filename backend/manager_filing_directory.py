"""Bounded full-batch reporting-manager metadata directory, never positions."""
import argparse,hashlib,json,re
from pathlib import Path
from manager_period_research import audit,cik

MAX_SHARD=2000000
MAX_DIRECTORY=1000000

def encoded(value):return (json.dumps(value,ensure_ascii=True,sort_keys=True,separators=(',',':'))+'\n').encode()
def digest(data):return hashlib.sha256(data).hexdigest()
def bucket(ci):return format(int(ci)%16,'x')

def build(database,database_sha,archive,archive_sha):
 report=audit(database,database_sha,archive,archive_sha,all_managers=True)
 shards={format(i,'x'):{'version':1,'bucket':format(i,'x'),'managers':[]} for i in range(16)}
 entries=[]
 for manager in report['managers']:
  ci=manager['manager_cik'];b=bucket(ci)
  # Shared interpretation is held in the directory, not repeated per manager.
  record={k:manager[k] for k in ('manager_cik','filings_in_retained_batch','report_periods_as_filed','filings')}
  shards[b]['managers'].append(record)
  entries.append([ci,len(record['filings']),len(record['report_periods_as_filed'])])
 payloads={f'shard-{b}.json':encoded(shard) for b,shard in shards.items()}
 if any(len(v)>MAX_SHARD for v in payloads.values()):raise ValueError('shard size')
 directory={k:report[k] for k in ('version','status','selection_mode','selection','counts','source_scope','training_ready','execution_ready','limitations')}
 directory.update(identity_role='REPORTING_MANAGER_NOT_HELD_ISSUER',history_complete=False,positions_assessed=False,trade_flows_assessed=False,
  entry_columns=['manager_cik','filings_in_retained_batch','distinct_report_periods_as_filed'],entries=entries,
  sharding='lowercase hexadecimal of numeric CIK modulo 16; fixed shard-{bucket}.json',
  shards={b:{'path':f'shard-{b}.json','bytes':len(payloads[f'shard-{b}.json']),'sha256':digest(payloads[f'shard-{b}.json']),'managers':len(s['managers']),'filings':sum(m['filings_in_retained_batch'] for m in s['managers'])} for b,s in shards.items()},
  search_scope='Exact normalized manager CIK or literal prefix of unpadded numeric manager CIK only. No name, ticker, company or security resolution. An absent CIK is absent from this batch, not no holdings.')
 data=encoded(directory)
 if len(data)>MAX_DIRECTORY:raise ValueError('directory size')
 payloads['index.json']=data
 return payloads

def search(directory,query,*,exact=True,limit=20,offset=0):
 if type(exact) is not bool or type(limit) is not int or not 1<=limit<=100 or type(offset) is not int or not 0<=offset<=20000:raise ValueError('query bounds')
 normalized=cik(query)
 entries=directory['entries']
 matches=[e for e in entries if e[0]==normalized] if exact else [e for e in entries if str(int(e[0])).startswith(str(int(normalized))) ]
 return {'status':'MATCHES_IN_RETAINED_BATCH' if matches else 'NO_MATCH_IN_RETAINED_BATCH_NOT_NO_HOLDINGS','total_matches':len(matches),'offset':offset,'results':[{'manager_cik':e[0],'filings_in_retained_batch':e[1],'distinct_report_periods_as_filed':e[2],'shard':directory['shards'][bucket(e[0])]} for e in matches[offset:offset+limit]],'next_offset':offset+limit if offset+limit<len(matches) else None}

def write(payloads,output):
 root=Path(output);root.mkdir(mode=0o700,parents=True,exist_ok=False)
 (root/'INCOMPLETE').write_text('Build not completed\n')
 for name,data in payloads.items():
  if not re.fullmatch(r'(index|shard-[0-9a-f])\.json',name):raise ValueError('output path')
  with (root/name).open('xb') as f:f.write(data)
  (root/name).chmod(0o600)
  if (root/name).read_bytes()!=data:raise ValueError('persisted bytes')
 (root/'COMPLETE.json').write_bytes(encoded({name:{'bytes':len(data),'sha256':digest(data)} for name,data in payloads.items()}));(root/'COMPLETE.json').chmod(0o600)
 (root/'INCOMPLETE').unlink()

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 for key in ('database','database-sha','archive','archive-sha','output'):p.add_argument('--'+key,required=True)
 args=vars(p.parse_args());output=args.pop('output');write(build(**args),output)
