"""Allowlisted public projection of independently reviewed original SEC facts."""
import argparse,json,hashlib
from pathlib import Path
from completed_note_offering import build

AUDIT_SHA='f5d8a356480a66e2a3ef4d0ea65956c4be4876e205f4dae3476a32868c68f7a8'
def project(audit):
    if hashlib.sha256(json.dumps(audit,sort_keys=True,separators=(',',':')).encode()).hexdigest()!=AUDIT_SHA:
        raise ValueError('reviewed audit changed')
    found=[r for r in audit['rows'] if r['status']=='SOURCE_REPORTED_DEBT_COMPLETION']
    if len(audit['rows'])!=10 or len(found)!=1 or audit['reported_completion_count']!=1:
        raise ValueError('reviewed projection scope changed')
    r=found[0]
    if r['accession']!='0001140361-26-043782' or r['issuer_cik']!='0000032604' or len(r['facts'])!=1:
        raise ValueError('reviewed issuer/source changed')
    f=r['facts'][0]
    return {'version':1,'id':'emerson-reported-note-completion',
        'status':'SOURCE_REPORTED_DEBT_COMPLETION_NOT_TRADE_SIGNAL',
        'issuer':{'cik':r['issuer_cik'],'name_as_reported':f['issuer_name_as_reported'],'ticker':None,'security_mapping_verified':False},
        'filing':{'accession':r['accession'],'source_url':r['source_url'],'source_sha256':r['source_sha256'],'observed_utc':r['observed_utc'],'first_public_utc':None},
        'facts':f,
        'coverage':{'selected_originals':10,'supported_findings':1,'unsupported_originals':9,
            'selection':audit['selection'],'abstentions':[{'accession':x['accession'],'status':x['status']} for x in audit['rows'] if x is not r],
            'absence_is_not_no_financing':True},
        'provenance':{'archive_sha256':audit['archive_sha256'],'manifest_sha256':audit['manifest_sha256'],
            'processor':'completed_note_offering.py','projection':'company_note_projection.py'},
        'limitations':audit['limitations'],'training_ready':False,'execution_ready':False,'qualified_outcomes':0}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('archive');p.add_argument('output');a=p.parse_args()
    result=project(build(a.archive))
    with Path(a.output).open('x') as f:json.dump(result,f,indent=2);f.write('\n')
