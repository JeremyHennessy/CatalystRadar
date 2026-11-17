"""Offline, source-pinned current Nasdaq Listed snapshot validation. No network."""
import argparse
from collections import Counter
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path
import re
from openfigi_evidence import read_pinned, stamp
from financial_pair_candidates import publish, write_private

URL = 'https://nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt'
HEADER = ['Symbol','Security Name','Market Category','Test Issue','Financial Status','Round Lot Size','ETF','NextShares']
LIMIT = 2_000_000

def parse(raw):
    if not 1 <= len(raw) <= LIMIT: raise ValueError('source size bound')
    text = raw.decode('ascii')
    if any(ord(c)<32 and c not in '\r\n' for c in text): raise ValueError('control character')
    lines = text.splitlines()
    if len(lines)<3 or len(lines)>20002 or lines[0].split('|')!=HEADER: raise ValueError('schema or row bound')
    footer=lines[-1].split('|')
    if len(footer)!=8 or any(footer[1:]): raise ValueError('invalid footer fields')
    m=re.fullmatch(r'File Creation Time: ([0-9]{8}[0-9]{2}:[0-9]{2})',footer[0])
    if not m: raise ValueError('invalid footer')
    created=datetime.strptime(m[1],'%m%d%Y%H:%M')
    rows=[];seen=set()
    for number,line in enumerate(lines[1:-1],2):
        fields=line.split('|')
        if len(fields)!=8: raise ValueError('row width')
        r=dict(zip(HEADER,fields));symbol=r['Symbol']
        # Dotted symbology test symbols occur in the real file; retain them as tests.
        if not re.fullmatch(r'[A-Z][A-Z0-9]{0,4}(?:\.[A-Z])?',symbol) or symbol in seen: raise ValueError('invalid or duplicate symbol')
        if '.' in symbol and r['Test Issue']!='Y': raise ValueError('unsupported non-test symbol grammar')
        if not 1<=len(r['Security Name'])<=1000 or not r['Security Name'].strip(): raise ValueError('invalid name')
        for field,values in [('Market Category',{'Q','G','S'}),('Financial Status',set('NDEQGHJK')),('Test Issue',{'Y','N'}),('ETF',{'Y','N'}),('NextShares',{'Y','N'})]:
            if r[field] not in values: raise ValueError('unsupported field code')
        if not re.fullmatch('[1-9][0-9]{0,5}',r['Round Lot Size']): raise ValueError('invalid round lot')
        seen.add(symbol);rows.append({'source_line_number':number,'fields':r})
    return rows,m[1],created

def audit(source,source_sha,receipt_path,receipt_sha,watchlist_path,watchlist_sha):
    with Path(source).open('rb') as f: raw=f.read(LIMIT+1)
    if hashlib.sha256(raw).hexdigest()!=source_sha: raise ValueError('source hash mismatch')
    receipt,_=read_pinned(receipt_path,receipt_sha,20000)
    expected={'url','requested_at','maximum_bytes','maximum_attempts','status','bytes','sha256','finished_at'}
    if not isinstance(receipt,dict) or set(receipt)!=expected: raise ValueError('receipt schema')
    if receipt['url']!=URL or type(receipt['status']) is not int or receipt['status']!=200 or receipt['sha256']!=source_sha or type(receipt['bytes']) is not int or receipt['bytes']!=len(raw): raise ValueError('receipt identity/status mismatch')
    if type(receipt['maximum_bytes']) is not int or receipt['maximum_bytes']!=LIMIT or type(receipt['maximum_attempts']) is not int or receipt['maximum_attempts']!=1: raise ValueError('unsupported collection bounds')
    if stamp(receipt['requested_at'])>stamp(receipt['finished_at']): raise ValueError('clock order')
    rows,creation,naive=parse(raw)
    # Unknown source timezone: only reject a date impossible in any civil timezone.
    if naive.date()>stamp(receipt['finished_at']).date()+timedelta(days=1): raise ValueError('future source date')
    watchlist,_=read_pinned(watchlist_path,watchlist_sha,20000)
    if not isinstance(watchlist,list) or not 1<=len(watchlist)<=100: raise ValueError('watchlist bounds')
    symbols=[]
    for w in watchlist:
        if not isinstance(w,dict) or set(w)!={'ticker','cik'} or not isinstance(w['ticker'],str) or not re.fullmatch('[A-Z][A-Z0-9.]{0,14}',w['ticker']) or not isinstance(w['cik'],str) or not re.fullmatch('[0-9]{1,10}',w['cik']) or not int(w['cik']): raise ValueError('watchlist schema')
        if w['ticker'] in symbols: raise ValueError('duplicate watchlist symbol')
        symbols.append(w['ticker'])
    by_symbol={r['fields']['Symbol']:r for r in rows};matches=[]
    for symbol in symbols:
        row=by_symbol.get(symbol)
        matches.append({'query_ticker':symbol,'disposition':'SYMBOL_PRESENT_CURRENT_NASDAQ_FILE' if row else 'NOT_IN_THIS_NASDAQ_FILE',
                        'source_line_number':row['source_line_number'] if row else None,
                        'flags':{k:row['fields'][k] for k in HEADER[2:]} if row else None,
                        'issuer_cik_link_verified':False,'historical_security_link_verified':False})
    summary={'schema_version':1,'status':'CURRENT_NASDAQ_LISTED_REFERENCE_ONLY','source_url':URL,'source_sha256':source_sha,'source_bytes':len(raw),'receipt_sha256':receipt_sha,'watchlist_sha256':watchlist_sha,
             'requested_at':receipt['requested_at'],'observed_at':receipt['finished_at'],'source_creation_text':creation,'source_creation_timezone':None,'source_creation_utc':None,
             'record_count':len(rows),'unique_symbols':len(by_symbol),'counts':{k:dict(sorted(Counter(r['fields'][k] for r in rows).items())) for k in HEADER[2:]},
             'watchlist_symbol_matches':sum(m['source_line_number'] is not None for m in matches),'watchlist_comparison':matches,'training_ready':False,'execution_ready':False,
             'limitations':['Only current Nasdaq-listed file, not all exchanges, historical universe or delisting completeness.',
              'Retained test issues, ETF and NextShares flags are not automatic common-equity qualification; non-ETF does not prove common stock.',
              'Financial Status is a listing-compliance classification, not trading-halt, quote or executable-liquidity evidence.',
              'Symbol equality is not verified CIK or historical security ownership; absence only describes this file.',
              'Footer timezone is unspecified in reviewed source definition; no UTC conversion or precise freshness assertion.',
              'Current local observation cannot be backdated. No prices, adjusted returns, corporate-action completeness or training admission.']}
    return summary,{'receipt':receipt,'rows':rows}

def main():
    p=argparse.ArgumentParser()
    for name in ['source','source-sha256','receipt','receipt-sha256','watchlist','watchlist-sha256','output-directory']:p.add_argument('--'+name,required=True)
    a=p.parse_args();out=Path(a.output_directory).resolve()
    if out.is_relative_to(Path(__file__).resolve().parents[1]) or not out.parent.is_dir(): raise ValueError('private trusted parent outside checkout required')
    out.mkdir(mode=0o700,exist_ok=False);write_private(out/'INCOMPLETE',{'status':'INCOMPLETE_NOT_USABLE'})
    summary,evidence=audit(a.source,a.source_sha256,a.receipt,a.receipt_sha256,a.watchlist,a.watchlist_sha256)
    publish(out,summary,evidence);print(json.dumps(summary))

if __name__=='__main__': main()
