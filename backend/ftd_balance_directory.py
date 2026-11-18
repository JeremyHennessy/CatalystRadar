"""Full retained FTD CUSIP directory; per-date balances, not summed flows."""
import argparse,hashlib,json,re
from pathlib import Path
from ftd_balance_series import audit
MAX_INDEX=3000000
MAX_SHARD=1500000

def encode(value):return (json.dumps(value,ensure_ascii=True,sort_keys=True,separators=(',',':'))+'\n').encode()
def digest(data):return hashlib.sha256(data).hexdigest()
def bucket(cusip):return format(hashlib.sha256(cusip.encode('ascii')).digest()[0]%64,'02x')
def build(archive,database):
 report=audit(archive,database,all_cusips=True)
 shards={format(i,'02x'):{'version':1,'bucket':format(i,'02x'),'series':[]} for i in range(64)};entries=[]
 for series in report.pop('series'):
  ci=series['cusip_as_reported'];obs=series['observations'];b=bucket(ci)
  record={'cusip_as_reported':ci,'reported_observations':len(obs),'unreported_date_slots':series['unreported_date_slots'],'observations':obs}
  shards[b]['series'].append(record)
  entries.append([ci,len(obs),sorted({o['symbol_as_reported'] for o in obs}),sorted({o['description_as_reported'] for o in obs})])
 payloads={f'shard-{b}.json':encode(s) for b,s in shards.items()}
 if any(len(data)>MAX_SHARD for data in payloads.values()):raise ValueError('shard size')
 report.update(identity_scope='SOURCE_CUSIP_ONLY_NOT_VERIFIED_ISSUER_OR_CURRENT_SECURITY',issuer_mapping_verified=False,current_security_identity_verified=False,
  entry_columns=['cusip_as_reported','reported_observations','symbols_as_reported','descriptions_as_reported'],entries=entries,
  sharding='first SHA256 byte of ASCII CUSIP modulo64, lowercase two-digit hex; fixed shard-{bucket}.json',
  shards={b:{'path':f'shard-{b}.json','bytes':len(payloads[f'shard-{b}.json']),'sha256':digest(payloads[f'shard-{b}.json']),'cusips':len(s['series']),'reported_rows':sum(x['reported_observations'] for x in s['series'])} for b,s in shards.items()},
  search_scope='Exact CUSIP, explicit literal CUSIP prefix, or exact source-reported symbol filter. Preserve all matching CUSIPs; labels are not current identity or issuer mapping.')
 index=encode(report)
 if len(index)>MAX_INDEX:raise ValueError('index size')
 payloads['index.json']=index
 return payloads

def search(index,query,*,field='cusip',limit=20,offset=0):
 # Input is an already verified generated directory, not arbitrary external JSON.
 if field not in ('cusip','cusip_prefix','symbol') or type(limit) is not int or not 1<=limit<=100 or type(offset) is not int or not 0<=offset<=20000:raise ValueError('query bounds')
 if not isinstance(query,str) or not 1<=len(query)<=32 or not query.strip() or any(ord(c)<32 or ord(c)>126 for c in query):raise ValueError('literal ASCII query')
 if (field=='cusip' and not re.fullmatch('[A-Z0-9*@#]{9}',query)) or (field=='cusip_prefix' and (len(query)>9 or not re.fullmatch('[A-Z0-9*@#]+',query))):raise ValueError('CUSIP query')
 matches=[e for e in index['entries'] if (e[0]==query if field=='cusip' else e[0].startswith(query) if field=='cusip_prefix' else query in e[2])]
 return {'status':'MATCHES_IN_RETAINED_FILE' if matches else 'NO_MATCH_IN_RETAINED_FILE_NOT_ZERO_BALANCE','field':field,'total_matching_cusips':len(matches),'multiple_cusips_match':len(matches)>1,'offset':offset,'results':[{'cusip_as_reported':e[0],'reported_observations':e[1],'symbols_as_reported':e[2],'descriptions_as_reported':e[3],'shard':index['shards'][bucket(e[0])]} for e in matches[offset:offset+limit]],'next_offset':offset+limit if offset+limit<len(matches) else None}

def save(payloads,out):
 # Separate namespace permits exactly two-hex shards; no path taken from source data.
 root=Path(out).resolve()
 if root.exists() or not root.parent.is_dir() or root.is_relative_to(Path(__file__).resolve().parents[1]):raise ValueError('new private output required')
 root.mkdir(mode=0o700,exist_ok=False);(root/'INCOMPLETE').write_text('Incomplete build\n');(root/'INCOMPLETE').chmod(0o600)
 for name,data in payloads.items():
  if not re.fullmatch(r'(index|shard-[0-3][0-9a-f])\.json',name):raise ValueError('output path')
  with (root/name).open('xb') as f:f.write(data)
  (root/name).chmod(0o600)
  if (root/name).read_bytes()!=data:raise ValueError('persisted bytes')
 (root/'COMPLETE.json').write_bytes(encode({n:{'bytes':len(b),'sha256':digest(b)} for n,b in payloads.items()}));(root/'COMPLETE.json').chmod(0o600);(root/'INCOMPLETE').unlink()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--archive',required=True);p.add_argument('--database',required=True);p.add_argument('--out',required=True);a=p.parse_args();save(build(a.archive,a.database),a.out)
