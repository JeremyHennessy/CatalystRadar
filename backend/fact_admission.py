"""Strict per-family fact completeness; not factual verification or a signal."""
import math

CONTRACTS = {
    'EARNINGS_GROWTH': {
        'event_type':'EARNINGS',
        'bool':('comparable_periods','total_gaap_diluted_eps_basis','same_share_basis'),
        'number':('gaap_revenue','prior_gaap_revenue','gaap_eps','prior_gaap_eps')},
    'GUIDANCE_RAISE': {
        'event_type':'EARNINGS',
        'bool':('guidance_same_basis_horizon',),
        'number':('prior_guidance_midpoint','new_guidance_midpoint')},
    'MATERIAL_CONTRACT_BACKLOG_NOT_REVENUE': {
        'event_type':'CONTRACT',
        'bool':('customer_revenue_contract','issuer_is_seller','financing_or_recapitalization','binding','firm_minimum_not_options'),
        'number':('firm_minimum_value','annual_revenue')},
    'BUYBACK_AUTHORIZATION_NOT_EXECUTION': {
        'event_type':'BUYBACK',
        'bool':('common_stock_authorization','incremental_authorization'),
        'number':('new_authorization_value','pre_event_market_cap')},
}

def finite_number(value):
    try:return type(value) in (int,float) and math.isfinite(value)
    except (OverflowError,TypeError):return False

def admit_facts(family, facts):
    """Require every operand, retaining missing/invalid fields rather than zeros.

    A COMPLETE result only validates types/presence. It does not establish truth,
    comparability, source evidence, event applicability or any common trade gate.
    Explicit False, zero and negative finite values are present, not missing.
    """
    if family not in CONTRACTS:raise ValueError('unknown rule family')
    spec=CONTRACTS[family]
    if not isinstance(facts,dict):facts={}
    missing=[];invalid=[]
    for kind in ('bool','number'):
        for name in spec[kind]:
            if name not in facts or facts[name] is None:missing.append(name);continue
            value=facts[name]
            valid=type(value) is bool if kind=='bool' else finite_number(value)
            if not valid:invalid.append(name)
    return {'family':family,'required_event_type':spec['event_type'],
            'status':'UNKNOWN' if missing or invalid else 'COMPLETE_FACT_TYPES_ONLY',
            'missing_fields':sorted(missing),'invalid_fields':sorted(invalid),
            'source_verified':False,'qualified':False,'signal':None}

def unknown_families():
    return {family:admit_facts(family,{}) for family in CONTRACTS}

def classify_family(family,event,cutoff,evidence_root,expected_previous_session=None):
    """Explicit opt-in wrapper; never called by scanner or frozen experiment.

    Only invoke the existing classifier after all selected-family facts exist.
    Its common evidence/security/time/market gates still apply. Other families'
    signals are not returned as this family's result. No orders are created.
    """
    admission=admit_facts(family,event.get('facts'))
    out={'family':family,'admission':admission,'status':'UNKNOWN','signal':None,
         'qualified':False,'reason':None}
    if event.get('event_type')!=admission['required_event_type']:
        out['reason']='EVENT_TYPE_MAPPING_UNRESOLVED';return out
    if admission['status']=='UNKNOWN':
        out['reason']='REQUIRED_FACTS_MISSING_OR_INVALID';return out
    from radar import classify
    classified=classify(event,cutoff,evidence_root,expected_previous_session)
    out['common_gate_status']=classified['status']
    if classified['status']=='BLOCKED':
        out['status']='BLOCKED';out['reason']='COMMON_EVIDENCE_GATE';out['gate_reasons']=classified['reasons']
    else:
        out['status']='RULE_MATCH_RESEARCH_ONLY' if family in classified['signals'] else 'NO_RULE_MATCH'
        out['signal']=family if family in classified['signals'] else None
    return out
