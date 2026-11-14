"""Paper-only primary-evidence classifier. No network, broker or order execution."""
import json, hashlib, argparse, math
from datetime import datetime, timezone
from pathlib import Path
from decimal import Decimal

def utc(x):
    d=datetime.fromisoformat(x.replace('Z','+00:00'))
    if d.tzinfo is None: raise ValueError('timezone required')
    return d.astimezone(timezone.utc)

def growth_at_least(new,old,pct):
    return old>0 and Decimal(str(new))>=Decimal(str(old))*(Decimal(1)+Decimal(str(pct)))

def fraction_at_least(value,base,pct):
    return base>0 and Decimal(str(value))>=Decimal(str(base))*Decimal(str(pct))

def classify(e, cutoff, root, expected_previous_session=None):
    out={'event_id':e.get('event_id'),'ticker':e.get('ticker'),'status':'BLOCKED','signals':[], 'reasons':[],'mode':'PAPER_OBSERVATION_ONLY'}
    try:
        cut=utc(cutoff); known=utc(e['observed_utc']); public=utc(e['first_public_utc']); review=utc(e['review_complete_utc'])
        retrievals=[utc(x['retrieved_utc']) for x in e['sources']]
        retrievals.append(utc(e['market_data_observed_utc']))
        if not retrievals or review<max(retrievals): raise ValueError('review predates required evidence')
        known=max([known,review]+retrievals)
        out['knowledge_utc']=known.isoformat()
        if known>cut or public>cut or public>known: raise ValueError('future or inconsistent knowledge')
        if (cut-public).total_seconds()>96*3600: raise ValueError('stale event beyond 96h')
        if e['source_verified_primary'] is not True or e['timestamp_verified'] is not True: raise ValueError('unverified source/timestamp')
        # Byte equality is provenance only; reviewer must verify factual extraction separately.
        for src in e['sources']:
            path=(Path(root)/src['path']).resolve()
            if Path(root).resolve() not in path.parents: raise ValueError('source outside evidence root')
            if hashlib.sha256(path.read_bytes()).hexdigest()!=src['sha256']: raise ValueError('evidence hash mismatch')
            if utc(src['retrieved_utc'])>cut: raise ValueError('source retrieved after freeze')
        if not e['sources'] or e['extraction_verified'] is not True: raise ValueError('missing verified extraction')
        if e['same_event_deduplicated'] is not True or e['amendment_unresolved'] is not False: raise ValueError('event lineage unresolved')
        if e['security_type']!='COMMON_STOCK' or e['exchange'] not in ('NYSE','NASDAQ'): raise ValueError('outside universe')
        for name in ('previous_close','adv20_usd'):
            if type(e[name]) not in (int,float) or not math.isfinite(e[name]): raise ValueError('nonfinite/invalid market numeric')
        if not expected_previous_session or e['market_data_asof_session']!=expected_previous_session or e['session_calendar_verified'] is not True: raise ValueError('wrong/unverified market session')
        if e['previous_close']<5 or e['adv20_usd']<10000000: raise ValueError('price/liquidity floor')
        if utc(e['market_data_observed_utc'])>cut or e['market_data_verified'] is not True: raise ValueError('unverified market data')
        if e['halt_status_verified'] is not True or e['halted'] is not False or e['corporate_action_unresolved'] is not False: raise ValueError('halt/corporate action')
        f=e['facts']
        if not isinstance(f,dict): raise ValueError('facts must be object')
        numeric_fields={'gaap_revenue_yoy','gaap_revenue','prior_gaap_revenue','gaap_eps','prior_gaap_eps','gaap_eps_yoy','prior_guidance_midpoint','new_guidance_midpoint','annual_revenue','firm_minimum_value','pre_event_market_cap','new_authorization_value'}
        for name in numeric_fields & f.keys():
            if type(f[name]) not in (int,float) or not math.isfinite(f[name]): raise ValueError('nonfinite/invalid numeric fact')
        for value in f.values():
            if isinstance(value,float) and not math.isfinite(value): raise ValueError('nonfinite fact')
        if e['event_type']=='EARNINGS':
            if (f.get('comparable_periods') is True) and f.get('total_gaap_diluted_eps_basis') is True and f.get('same_share_basis') is True and f.get('prior_gaap_revenue',0)>0 and f.get('prior_gaap_eps',0)>0 and growth_at_least(f.get('gaap_revenue',0),f['prior_gaap_revenue'],.10) and growth_at_least(f.get('gaap_eps',0),f['prior_gaap_eps'],.10):
                out['signals'].append('EARNINGS_GROWTH')
            if (f.get('guidance_same_basis_horizon') is True) and f.get('prior_guidance_midpoint',0)>0 and growth_at_least(f.get('new_guidance_midpoint',0),f['prior_guidance_midpoint'],.05):
                out['signals'].append('GUIDANCE_RAISE')
        if e['event_type']=='CONTRACT' and f.get('customer_revenue_contract') is True and f.get('issuer_is_seller') is True and f.get('financing_or_recapitalization') is False and (f.get('binding') is True) and (f.get('firm_minimum_not_options') is True) and f.get('annual_revenue',0)>0 and fraction_at_least(f.get('firm_minimum_value',0),f['annual_revenue'],.05):
            out['signals'].append('MATERIAL_CONTRACT_BACKLOG_NOT_REVENUE')
        if e['event_type']=='BUYBACK' and f.get('common_stock_authorization') is True and (f.get('incremental_authorization') is True) and f.get('pre_event_market_cap',0)>0 and fraction_at_least(f.get('new_authorization_value',0),f['pre_event_market_cap'],.03):
            out['signals'].append('BUYBACK_AUTHORIZATION_NOT_EXECUTION')
        out['status']='OBSERVE' if out['signals'] else 'NO_SIGNAL'
    except (KeyError,ValueError,TypeError,OSError) as err:
        out['reasons'].append(str(err))
    return out

def run(events,cutoff,root,expected_previous_session=None):
    ids=[x.get('event_id') for x in events]
    if len(ids)!=len(set(ids)): raise ValueError('duplicate event IDs: resolve lineage before batch')
    results=[classify(e,cutoff,root,expected_previous_session) for e in events]
    return sorted(results,key=lambda x:(utc(x['knowledge_utc']) if x.get('knowledge_utc') else datetime.max.replace(tzinfo=timezone.utc),str(x.get('event_id',''))))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('input');ap.add_argument('--cutoff',required=True);ap.add_argument('--evidence-root',required=True);ap.add_argument('--output',required=True);ap.add_argument('--prior-session',required=True);a=ap.parse_args()
    result={'mode':'PAPER_OBSERVATION_ONLY','cutoff':a.cutoff,'results':run(json.loads(Path(a.input).read_text()),a.cutoff,a.evidence_root,a.prior_session),'fills':[]}
    with open(a.output,'x') as f:json.dump(result,f,indent=2)
