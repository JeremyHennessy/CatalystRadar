"""Source-content adjudication for the existing frozen outcome case, not a label."""
import argparse,hashlib,json,re,zipfile
from pathlib import Path
from historical_outcome_audit import build as frozen_audit
from continuing_operations_evidence import extract as continuing_extract
from financial_admission_rehearsal import plain
from private_prices import unique_object

ACC='0001213900-26-119681';CIK='0000025743'
ZIP_SHA='0f92e2c02a597b14f08c29395ae2fc9b87f2db580016e632c8d76c3059e449c0'
MANIFEST_SHA='ac6316ad597b9a931613c71e4f1442425f5f83c873d47ba17192f0c1b6a2274a'
RAW_SHA='e69ffeb2329ad596f652619d63e6c9195ad2b411258315b259fee04a2f131c47'
DESCRIPTION='PRESS RELEASE FROM THERAPEUTICSMD, INC., DATED NOVEMBER 13, 2026, ENTITLED "THERAPEUTICSMD ANNOUNCES SECOND QUARTER 2026 FINANCIAL RESULTS."'
TITLE='TherapeuticsMD Announces Third Quarter 2026 Financial Results'
INTRO='BOCA RATON, Fla.--(BUSINESS WIRE)—November 13, 2026 -- TherapeuticsMD, Inc. (“TherapeuticsMD” or the “Company”) (NASDAQ: TXMD), a company that owns rights to pharmaceutical royalties, today reported financial results for the three months ended September 30, 2026.'
HEADINGS=['Third Quarter 2026 Financial Results','Net Income from Continuing Operations']

def sha(raw):return hashlib.sha256(raw).hexdigest()
def ref(raw,start,end):return {'byte_start':start,'byte_end':end,'sha256':sha(raw[start:end])}

def inspect(raw):
    if type(raw) is not bytes or not 0<len(raw)<=25_000_000:raise ValueError('bounded source bytes required')
    raw.decode('utf-8')
    if b'\0' in raw or re.search(rb'<!\s*(?:DOCTYPE|ENTITY)',raw,re.I):raise ValueError('unsupported encoding/declarations')
    docs=list(re.finditer(rb'<DOCUMENT>.*?</DOCUMENT>',raw,re.S))
    if not docs or len(docs)!=raw.count(b'<DOCUMENT>') or len(docs)!=raw.count(b'</DOCUMENT>'):raise ValueError('malformed inventory')
    exhibits=[]
    for d in docs:
        h=d[0].split(b'<TEXT>',1)[0]
        kinds=re.findall(rb'^<TYPE>([^\r\n]+)',h,re.M)
        if len(kinds)!=1 or d[0].count(b'<TEXT>')!=1 or d[0].count(b'</TEXT>')!=1:raise ValueError('document header')
        if kinds[0].strip()==b'EX-99.1':exhibits.append(d)
    if len(exhibits)!=1:raise ValueError('unique results exhibit required')
    d=exhibits[0];h=d[0].split(b'<TEXT>',1)[0]
    descriptions=list(re.finditer(rb'^<DESCRIPTION>([^\r\n]+)',h,re.M));names=re.findall(rb'^<FILENAME>([^\r\n]+)',h,re.M)
    if len(descriptions)!=1 or descriptions[0][1].decode()!=DESCRIPTION or names!=[b'ea031220401ex99-1.htm']:raise ValueError('reviewed description/filename changed')
    excluded=[(m.start(),m.end()) for m in re.finditer(rb'<!--.*?(?:-->|$)|<(script|style)\b[^>]*>.*?(?:</\1\s*>|$)',d[0],re.S|re.I)]
    paragraphs=[m for m in re.finditer(rb'<(p|td)\b[^>]*>.*?</\1>',d[0],re.S|re.I) if not any(m.start()<b and m.end()>a for a,b in excluded)]
    anchors=[]
    for text in [TITLE,INTRO]+HEADINGS:
        matches=[m for m in paragraphs if plain(m[0])==text]
        if len(matches)!=1:raise ValueError('unique reviewed content anchor required')
        m=matches[0];anchors.append({'text_as_reported':text,'source_span':ref(raw,d.start()+m.start(),d.start()+m.end())})
    starts=[a['source_span']['byte_start'] for a in anchors]
    if starts!=sorted(starts):raise ValueError('reviewed context order changed')
    evidence=continuing_extract(raw)
    records=evidence['records']
    if len(records)!=1:raise ValueError('unique continuing operations paragraph required')
    item=records[0]
    # Existing parser's null current period and all other qualification fields are untouched.
    span=item.get('source_span') or item.get('evidence_span')
    if span is None:raise ValueError('source paragraph span required')
    if not starts[-1]<span['byte_start']<span['byte_end']<=d.end():raise ValueError('paragraph not in reviewed context')
    description=descriptions[0]
    return {'filename':'ea031220401ex99-1.htm','document_sha256':sha(d[0]),'description':{'text_as_reported':DESCRIPTION,'source_span':ref(raw,d.start()+description.start(),d.start()+description.end())},'body_anchors':anchors,'continuing_operations_evidence':item,'body_reported_period':{'end':'2026-09-30','start':None,'duration_as_reported':'three months','quarter_as_reported':'third quarter 2026','status':'BODY_DECLARATION_NOT_ACCOUNTING_COMPARABILITY'},'description_period_as_reported':'second quarter 2026','description_body_period_conflict':True,'conflict_resolution':'UNRESOLVED_NO_SILENT_CORRECTION','source_content_reviewed':True,'financial_comparability_verified':False}

def build(root,archive):
    frozen=frozen_audit(root)
    if len(frozen['selected'])!=1 or frozen['selected'][0]['event_id']!=ACC or frozen['selected'][0]['issuer_cik']!=CIK:raise ValueError('frozen selection changed')
    p=Path(archive)
    if p.stat().st_size>20_000_000:raise ValueError('archive size bound')
    zipped=p.read_bytes()
    if sha(zipped)!=ZIP_SHA:raise ValueError('archive pin')
    import io
    with zipfile.ZipFile(io.BytesIO(zipped)) as z:
        if len(z.namelist())!=len(set(z.namelist())):raise ValueError('duplicate archive member')
        manifest=z.read('manifest.jsonl');raw=z.read(RAW_SHA+'.txt')
    if sha(manifest)!=MANIFEST_SHA or sha(raw)!=RAW_SHA:raise ValueError('member pins')
    receipts=[json.loads(x,object_pairs_hook=unique_object) for x in manifest.splitlines()]
    matches=[r for r in receipts if r['accession']==ACC]
    if len(matches)!=1:raise ValueError('receipt ambiguity')
    r=matches[0]
    if r['issuer_cik']!='25743' or r['archive_file']!=RAW_SHA+'.txt' or r['sha256']!=RAW_SHA or r['byte_count']!=len(raw) or r['status']!='ARCHIVED_IDENTITY_VERIFIED':raise ValueError('receipt identity')
    url='https://www.sec.gov/Archives/edgar/data/25743/000121390026119681/0001213900-26-119681.txt'
    if r['url']!=url:raise ValueError('source URL')
    finding=inspect(raw)
    return {'schema_version':1,'status':'FROZEN_OUTCOME_CASE_SOURCE_CONTENT_REVIEW_NOT_QUALIFIED_OUTCOME','accession':ACC,'issuer_cik':CIK,'selection_policy':frozen['policy']['id'],'selection_changed':False,'frozen_input_sha256':frozen['input_sha256'],'source':{'url':url,'link_status':'RETAINED_RECEIPT_NOT_NEW_FETCH','archive_sha256':ZIP_SHA,'manifest_sha256':MANIFEST_SHA,'filing_sha256':RAW_SHA,'filing_bytes':len(raw),'recorded_retrieved_utc':r['retrieved_utc'],'retrieval_clock_independently_authenticated':False},'finding':finding,'first_public_utc':None,'decision_utc':None,'entry_session':None,'endpoint_session':None,'return_value':None,'qualified_outcomes':0,'training_ready':False,'execution_ready':False,'remaining_dependencies':frozen['selected'][0]['missing_dependencies'],'limitations':['Source content is now explicitly reviewed for this unchanged frozen case; header-only classification is not the full evidence anymore.','The body declares third-quarter results while exhibit description declares second-quarter. Both are preserved; this review does not adjudicate accounting truth or silently fix the source.','Continuing-operations earnings and reported combined basic/diluted EPS are not total-company GAAP/comparability proof. Rounded prior EPS 0.00 must not become an exact-zero denominator.','Release date is not first-public time. Retained observation does not establish novelty, historical availability or a frozen decision.','No prices, inferred ticker joins, returns, performance metrics, orders or changes to frozen evidence are introduced.']}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root');p.add_argument('archive');p.add_argument('output');a=p.parse_args();out=Path(a.output)
    result=build(a.root,a.archive)
    with out.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
