"""Offline parser for a pinned Treasury par-yield snapshot, not executable prices."""
import argparse
import datetime as dt
from decimal import Decimal, localcontext
import hashlib
import json
import os
from pathlib import Path
import re
import xml.etree.ElementTree as ET

BASE='web/market-context/treasury-202611/'
MONTH='202611'
URL='https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/xml?data=daily_treasury_yield_curve&field_tdr_date_value_month='+MONTH
RAW_SHA='cfd253bd6330538ed93bc1a876fb8c197742adacd82a131955cc83304233239e'
RECEIPT_SHA='fb924dac57a9cdaf0bb202e10c0121f742bfcb17b1768a9bc6ac34306ded8127'
A='{http://www.w3.org/2005/Atom}';D='{http://schemas.microsoft.com/ado/2007/08/dataservices}';M='{http://schemas.microsoft.com/ado/2007/08/dataservices/metadata}'
XML='{http://www.w3.org/XML/1998/namespace}'
FEED_BASE='https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/xml'
ITEM_BASE=FEED_BASE+'-item?data=daily_treasury_yield_curve'
MATURITIES=('BC_1MONTH','BC_1_5MONTH','BC_2MONTH','BC_3MONTH','BC_4MONTH','BC_6MONTH','BC_1YEAR','BC_2YEAR','BC_3YEAR','BC_5YEAR','BC_7YEAR','BC_10YEAR','BC_20YEAR','BC_30YEAR')
FIELDS=MATURITIES+('BC_30YEARDISPLAY',)
MAX_BYTES=1000000

def encoded(obj):return (json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)+'\n').encode()
def sha(raw):return hashlib.sha256(raw).hexdigest()
def unique(pairs):
    result={}
    for k,v in pairs:
        if k in result:raise ValueError('duplicate JSON key')
        result[k]=v
    return result

def read(path,limit):
    with Path(path).open('rb') as f:raw=f.read(limit+1)
    if len(raw)>limit:raise ValueError('input byte bound')
    return raw

def utc(value):
    if not isinstance(value,str) or not re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{1,6})?(?:Z|\+00:00)',value):raise ValueError('UTC timestamp')
    return dt.datetime.fromisoformat(value.replace('Z','+00:00'))

def leaf(node,attrs):
    if node.attrib!=attrs or len(node):raise ValueError('leaf schema')
    return node.text or ''

def children(node,tags):
    result={}
    for child in node:
        if child.tag not in tags or child.tag in result:raise ValueError('unexpected/duplicate element')
        result[child.tag]=child
    if set(result)!=set(tags):raise ValueError('missing element')
    return result

def parse(raw,month):
    if type(raw) is not bytes or not 1<=len(raw)<=MAX_BYTES or not isinstance(month,str) or not re.fullmatch('[0-9]{6}',month):raise ValueError('input bounds/month')
    dt.date(int(month[:4]),int(month[4:]),1)
    text=raw.decode('utf-8-sig')
    if '\x00' in text or '<!DOCTYPE' in text.upper() or '<!ENTITY' in text.upper():raise ValueError('DTD/entities/unsupported encoding')
    declaration=re.match(r'<\?xml[^?]*\?>',text)
    if declaration and not re.search(r'encoding=[\"\']utf-8[\"\']',declaration[0],re.I):raise ValueError('UTF8 declaration required')
    root=ET.fromstring(text)
    if root.tag!=A+'feed' or root.attrib!={XML+'base':FEED_BASE} or len(list(root.iter()))>1500:raise ValueError('feed namespace/schema/bound')
    entries=[x for x in root if x.tag==A+'entry']
    if not 1<=len(entries)<=31:raise ValueError('entry count')
    metadata=ET.Element('metadata')
    metadata.extend(x for x in root if x.tag!=A+'entry')
    meta=children(metadata,[A+x for x in ('title','id','updated','link')])
    if leaf(meta[A+'title'],{'type':'text'})!='DailyTreasuryYieldCurveRateData' or leaf(meta[A+'id'],{})!=ITEM_BASE:raise ValueError('feed identity')
    feed_updated=leaf(meta[A+'updated'],{});utc(feed_updated)
    leaf(meta[A+'link'],{'rel':'self','title':'DailyTreasuryYieldCurveRateData','href':'DailyTreasuryYieldCurveRateData'})
    rows=[];ids=set();dates=set()
    for entry in entries:
        if entry.attrib:raise ValueError('entry attributes')
        parts=children(entry,[A+x for x in ('id','title','updated','author','link','category','content')])
        if leaf(parts[A+'title'],{'type':'text'}):raise ValueError('unexpected title text')
        if parts[A+'author'].attrib:raise ValueError('author attributes')
        author=children(parts[A+'author'],[A+'name'])
        if leaf(author[A+'name'],{}):raise ValueError('unexpected author text')
        updated=leaf(parts[A+'updated'],{});utc(updated)
        leaf(parts[A+'category'],{'term':'TreasuryDataWarehouseModel.DailyTreasuryYieldCurveRateDatum','scheme':'http://schemas.microsoft.com/ado/2007/08/dataservices/scheme'})
        content=parts[A+'content']
        if content.attrib!={'type':'application/xml'}:raise ValueError('content type')
        props=children(content,[M+'properties'])[M+'properties']
        if props.attrib:raise ValueError('properties attributes')
        fields=children(props,[D+x for x in ('Id','NEW_DATE')+FIELDS])
        identifier=leaf(fields[D+'Id'],{M+'type':'Edm.Int32'})
        if not re.fullmatch('[1-9][0-9]{0,9}',identifier) or int(identifier)>2147483647 or identifier in ids:raise ValueError('duplicate/invalid ID')
        date_literal=leaf(fields[D+'NEW_DATE'],{M+'type':'Edm.DateTime'})
        if not re.fullmatch('[0-9]{4}-[0-9]{2}-[0-9]{2}T00:00:00',date_literal):raise ValueError('source observation date')
        date=dt.date.fromisoformat(date_literal[:10])
        if date.strftime('%Y%m')!=month or date.isoformat() in dates:raise ValueError('duplicate/out-of-month date')
        entry_id=leaf(parts[A+'id'],{})
        if entry_id!=ITEM_BASE+'&id='+identifier:raise ValueError('entry source ID mismatch')
        leaf(parts[A+'link'],{'rel':'edit','title':'DailyTreasuryYieldCurveRateDatum','href':'/resource-center/data-chart-center/interest-rates/pages/xml-item?data=daily_treasury_yield_curve&id='+identifier})
        rates={}
        for field in FIELDS:
            node=fields[D+field]
            if node.attrib=={M+'type':'Edm.Double',M+'null':'true'}:
                if len(node) or (node.text or '').strip():raise ValueError('null with value')
                rates[field]=None
            else:
                value=leaf(node,{M+'type':'Edm.Double'})
                if not re.fullmatch(r'-?[0-9]{1,3}(?:\.[0-9]{1,4})?',value) or abs(Decimal(value))>100:raise ValueError('finite bounded decimal rate')
                rates[field]=value
        with localcontext() as ctx:
            ctx.prec=32
            spread=None if rates['BC_2YEAR'] is None or rates['BC_10YEAR'] is None else format((Decimal(rates['BC_10YEAR'])-Decimal(rates['BC_2YEAR']))*100,'f')
        rows.append({'source_id':identifier,'source_entry_url':entry_id,'observation_date':date.isoformat(),'source_NEW_DATE':date_literal,'source_entry_updated':updated,'rates_percent_as_reported':rates,'null_source_fields':[k for k,v in rates.items() if v is None],'ten_year_minus_two_year_basis_points':spread,'spread_status':'UNAVAILABLE_SOURCE_NULL' if spread is None else 'EXACT_DECIMAL_DIFFERENCE_OF_REPORTED_PAR_YIELDS'})
        ids.add(identifier);dates.add(date.isoformat())
    return {'source_feed_updated':feed_updated,'records':sorted(rows,key=lambda r:r['observation_date'])}

def build(raw,receipt_raw):
    if sha(raw)!=RAW_SHA or sha(receipt_raw)!=RECEIPT_SHA:raise ValueError('pinned source/receipt hash mismatch')
    receipt=json.loads(receipt_raw.decode('utf-8'),object_pairs_hook=unique,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('nonfinite JSON')))
    expected={'url','request_utc','maximum_bytes','timeout_seconds','redirects_allowed','retries','http_status','content_type','byte_count','sha256','outcome','finish_utc'}
    if set(receipt)!=expected or receipt['url']!=URL or type(receipt['http_status']) is not int or receipt['http_status']!=200 or receipt['content_type']!='text/xml; charset=UTF-8' or receipt['byte_count']!=len(raw) or receipt['sha256']!=sha(raw) or receipt['redirects_allowed'] is not False or receipt['retries']!=0 or receipt['maximum_bytes']!=MAX_BYTES or receipt['timeout_seconds']!=30 or receipt['outcome']!='RETAINED_RESPONSE_NOT_YET_VALIDATED':raise ValueError('capture receipt schema')
    requested=utc(receipt['request_utc']);finished=utc(receipt['finish_utc'])
    if not requested<=finished or (finished-requested).total_seconds()>30:raise ValueError('capture clock consistency')
    parsed=parse(raw,MONTH)
    if utc(parsed['source_feed_updated'])>finished or any(utc(r['source_entry_updated'])>finished or dt.date.fromisoformat(r['observation_date'])>finished.date() for r in parsed['records']):raise ValueError('source dates after observation')
    return {'schema_version':1,'status':'RETAINED_TREASURY_PAR_YIELD_CONTEXT_NOT_EXECUTABLE_QUOTES','requested_month':MONTH,'source':{'agency':'U.S. Treasury, Office of Debt Management','dataset_identifier':'015-DO-020','license':'CC0','license_evidence_url':'https://catalog.data.gov/dataset/interest-rate-statistics-daily-treasury-yield-curve-rates','feed_documentation_url':'https://home.treasury.gov/treasury-daily-interest-rate-xml-feed','request_url':URL,'raw_xml':{'path':BASE+'response.xml','bytes':len(raw),'sha256':sha(raw)},'capture_receipt':{'path':BASE+'receipt.json','bytes':len(receipt_raw),'sha256':sha(receipt_raw)},'request_utc':receipt['request_utc'],'observed_finish_utc':receipt['finish_utc'],'http_status':receipt['http_status'],'content_type':receipt['content_type']},'maturity_fields':list(MATURITIES),'additional_display_fields':['BC_30YEARDISPLAY'],'units':'ANNUAL_PERCENT_PAR_YIELD_AS_REPORTED','counts':{'source_dates':len(parsed['records']),'maturities_per_date':len(MATURITIES),'additional_display_fields_per_date':1,'null_rate_cells':sum(len(r['null_source_fields']) for r in parsed['records'])},**parsed,'first_public_utc':None,'full_month_complete':False,'historical_vintage_availability_verified':False,'training_ready':False,'execution_ready':False,'equity_returns_derived':False,'limitations':['This is one partial November 2026 response observed on November 18, not the completed month, a live feed or a guarantee all eligible dates are present.','Treasury fitted par yields are rate context, not executable bond prices, transactions, returns or a forecast. The two-year/ten-year difference is exact arithmetic on reported yields, not an investable trade.','NEW_DATE carries a midnight literal without timezone and is treated only as an observation date. Feed/entry updated fields are source-declared metadata, not per-observation first-public times. Capture request/finish times are separate.','All 14 maturity fields and the separate 30-year display field are retained; the display field is not counted as a new maturity. No interpolation, forward-fill, synthetic zero, calendar completion or omitted-date explanation is inferred.','Explicit source nulls remain null; a missing required field is a schema error. These are current retained response values, not authenticated historical release vintages; revisions and earlier availability are unverified.','CC0 is supported by this specific agency dataset listing; no broader permission over Treasury website content, logos or third-party series is asserted.']}

def save(raw_path,receipt_path,out):
    out=Path(out);out.mkdir(parents=True,exist_ok=False,mode=0o700)
    def write(name,data):
        fd=os.open(out/name,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(fd,'wb') as f:f.write(data)
    write('INCOMPLETE',b'not complete\n')
    result=build(read(raw_path,MAX_BYTES),read(receipt_path,10000));data=encoded(result)
    if len(data)>100000:raise ValueError('output bound')
    write('rates.json',data);write('COMPLETE',encoded({'rates.json':{'bytes':len(data),'sha256':sha(data)}}));(out/'INCOMPLETE').unlink()
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--raw',required=True);p.add_argument('--receipt',required=True);p.add_argument('--out',required=True);args=p.parse_args()
    save(args.raw,args.receipt,args.out)
