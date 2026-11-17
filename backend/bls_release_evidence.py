"""Bounded, offline evidence extraction from two supported BLS release layouts."""
import argparse,hashlib,json,re,subprocess,tempfile,resource
from datetime import datetime,timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from financial_pair_candidates import publish,write_private
from openfigi_evidence import read_pinned,stamp,digest

def evidence(text,pattern):
    matches=list(re.finditer(pattern,text))
    if len(matches)!=1:raise ValueError('missing or ambiguous supported statement')
    m=matches[0]
    return {'text_start':m.start(),'text_end':m.end(),'text':m.group(),'extracted_text_span_sha256':digest(m.group().encode()),'groups':m.groupdict(),'semantic_context_verified':False}

def parse(text,kind,observed_at):
    if kind not in ('empsit','cpi') or len(text)>1000000 or '\x00' in text:raise ValueError('unsupported release')
    first=text.split('\f')[0]
    clock=evidence(first,r'8:30 a\.m\. \(ET\) (?P<weekday>Monday|Tuesday|Wednesday|Thursday|Friday), (?P<month>[A-Z][a-z]+) (?P<day>\d{1,2}), (?P<year>\d{4})')
    header=first[:clock['text_start']]
    if not re.fullmatch(r'\s*Transmission of material in this (?:news )?release is embargoed until\s+USDL-\d{2}-\d{4}\s*',header):raise ValueError('unsupported embargo header')
    g=clock['groups'];local=datetime.strptime(f"{g['month']} {g['day']} {g['year']} 08:30",'%B %d %Y %H:%M').replace(tzinfo=ZoneInfo('America/New_York'))
    if local.strftime('%A')!=g['weekday'] or local.astimezone(timezone.utc)>stamp(observed_at):raise ValueError('invalid declared release clock')
    title='THE EMPLOYMENT SITUATION' if kind=='empsit' else 'CONSUMER PRICE INDEX'
    ref=evidence(first,title+r'\s+[—–-]\s+(?P<month>[A-Z]+) (?P<year>\d{4})')
    reference=datetime.strptime(ref['groups']['month']+' '+ref['groups']['year'],'%B %Y').strftime('%Y-%m')
    if reference>=local.strftime('%Y-%m'):raise ValueError('unsupported reference month')
    if kind=='empsit':
        facts=[evidence(first,r'Total nonfarm payroll employment rose by (?P<payroll_increase>[0-9]{1,3}(?:,[0-9]{3})*) in (?P<month>[A-Z][a-z]+), and the unemployment rate changed\s+little at (?P<unemployment_rate>[0-9]{1,2}\.[0-9]) percent, the U\.S\. Bureau of Labor Statistics reported today\.')]
        revisions=[evidence(text,r'The change in total nonfarm payroll employment for (?P<prior_month>[A-Z][a-z]+) was revised up by (?P<prior_revision>[0-9,]+), from \+(?P<prior_old>[0-9,]+)\s+to \+(?P<prior_new>[0-9,]+), and the change for (?P<recent_month>[A-Z][a-z]+) was revised up by (?P<recent_revision>[0-9,]+), from \+(?P<recent_old>[0-9,]+) to \+(?P<recent_new>[0-9,]+)\.')]
        missing=[]
    else:
        facts=[evidence(first,r'The Consumer Price Index for All Urban Consumers \(CPI-U\) increased (?P<headline_mom>[0-9]{1,2}\.[0-9]) percent on a seasonally\s+adjusted basis in (?P<month>[A-Z][a-z]+) after rising (?P<prior_mom>[0-9]{1,2}\.[0-9]) percent in (?P<prior_month>[A-Z][a-z]+), the U\.S\. Bureau of Labor Statistics\s+reported today\.'),evidence(first,r'The index for all items less food and energy rose (?P<core_mom>[0-9]{1,2}\.[0-9]) percent in (?P<month>[A-Z][a-z]+), as it did in (?P<prior_month>[A-Z][a-z]+) and\s+(?P<earlier_month>[A-Z][a-z]+)\.')]
        revisions=[]
        missing=[evidence(first,r'BLS did not collect survey data for October 2025 because of a lapse in appropriations\.[\s\S]*?BLS cannot publish 12-month\s+percent changes for October 2026 for indexes where October 2025 data are unavailable\.')]
    if any(f['groups'].get('month','').upper()!=ref['groups']['month'] for f in facts):raise ValueError('headline reference mismatch')
    return {'kind':kind,'reference_month':reference,'declared_embargo_utc':local.astimezone(timezone.utc).isoformat(),'observed_at':observed_at,'clock_evidence':clock,'reference_evidence':ref,'headline_evidence':facts,'revision_evidence':revisions,'missing_comparator_evidence':missing,'authenticated_first_public_at':None,'historical_decision_availability_verified':False,'consensus':None,'surprise':None,'training_ready':False}

def cap_output():resource.setrlimit(resource.RLIMIT_FSIZE,(2000000,2000000))

def audit(pdf,pdf_sha,receipt,receipt_sha,kind):
    with Path(pdf).open('rb') as f:raw=f.read(10000001)
    if len(raw)>10000000 or digest(raw)!=pdf_sha or not raw.startswith(b'%PDF-'):raise ValueError('PDF hash/bounds mismatch')
    r,_=read_pinned(receipt,receipt_sha,20000)
    expected={'source_url','method','authentication','requested_at','http_status','content_type','status','bytes','sha256','finished_at'}
    if not isinstance(r,dict) or set(r)!=expected or r['method']!='GET' or r['authentication']!='NONE' or r['http_status']!=200 or r['content_type']!='application/pdf' or r['status']!='RETAINED_NOT_YET_VERIFIED' or r['sha256']!=pdf_sha or r['bytes']!=len(raw):raise ValueError('unsupported receipt')
    if stamp(r['requested_at'])>stamp(r['finished_at']):raise ValueError('inverted observation clock')
    # PDF bytes on stdin guarantee extraction uses the exact hash-checked buffer.
    with tempfile.TemporaryFile() as output:
        subprocess.run(['pdftotext','-layout','-','-'],input=raw,stdout=output,stderr=subprocess.DEVNULL,timeout=30,check=True,preexec_fn=cap_output)
        output.seek(0);extracted=output.read(2000001)
    if len(extracted)>=2000000:raise ValueError('text bounds')
    text=extracted.decode('utf-8');result=parse(text,kind,r['finished_at'])
    expected_url='https://www.bls.gov/news.release/archives/'+kind+'_'+datetime.fromisoformat(result['declared_embargo_utc']).strftime('%m%d%Y')+'.pdf'
    if r['source_url']!=expected_url:raise ValueError('URL/declared date mismatch')
    summary={'schema_version':1,'status':'ARCHIVED_RELEASE_DECLARATION_NOT_AUTHENTICATED_FIRST_PUBLIC_TIME','kind':kind,'source_url':r['source_url'],'pdf_sha256':pdf_sha,'receipt_sha256':receipt_sha,'extracted_text_sha256':digest(extracted),'pdf_bytes':len(raw),'reference_month':result['reference_month'],'declared_embargo_utc':result['declared_embargo_utc'],'observed_at':r['finished_at'],'headline_statement_count':len(result['headline_evidence']),'revision_statement_count':len(result['revision_evidence']),'missing_comparator_statement_count':len(result['missing_comparator_evidence']),'training_ready':False,'execution_ready':False,'limitations':['Release-stated embargo is not authenticated historical public availability. Retrieved now, not available to a past system decision.','Values are this archived release snapshot and can be revised; no consensus or surprise established.','Text spans/hash refer to pdftotext UTF-8 extraction, not raw PDF byte ranges or full table interpretation.','Two narrowly supported release layouts only; unsupported wording/signs fail matching. Literal matches require manual semantic context review, not automatic fact admission. No annual CPI comparator invented.']}
    return summary,{'receipt':r,'release_evidence':result,'extracted_text':text}

def run(pdf,pdf_sha,receipt,receipt_sha,kind,output_directory):
    out=Path(output_directory).resolve()
    if out.is_relative_to(Path(__file__).resolve().parents[1]) or not out.parent.is_dir():raise ValueError('trusted private parent required')
    out.mkdir(mode=0o700,exist_ok=False);write_private(out/'INCOMPLETE',{'status':'INCOMPLETE_NOT_USABLE'})
    summary,evidence_=audit(pdf,pdf_sha,receipt,receipt_sha,kind);publish(out,summary,evidence_)
    return summary

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ('pdf','pdf-sha','receipt','receipt-sha','kind','output-directory'):p.add_argument('--'+n,required=True)
    a=p.parse_args();print(json.dumps(run(**vars(a))))
