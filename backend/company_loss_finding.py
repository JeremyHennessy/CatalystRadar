"""Fixed retained-source net-loss observation; not a profitability/growth signal."""
import argparse,json,re
from pathlib import Path
from decimal import Decimal
from company_revenue_finding import build as revenue_case,CIK,ACCESSION,USD
from source_prepared_correspondence import audit as correspondence
from openfigi_evidence import read_pinned
from financial_pair_candidates import write_private,sha

PERIODS=[('2025-05-01','2025-07-31','-110845',('fid_2251','fid_2284')),('2024-05-01','2024-07-31','-218662',('fid_2252','fid_2315'))]

def build(summary,results,receipt):
 # Reuse the reviewed source identity, receipt-clock and filing guardrails on this same retained filing.
 card=revenue_case(summary,results,receipt);selected={}
 for result in results:
  candidate=result.get('candidate')
  if not candidate:continue
  for f in candidate['source_group']['occurrences']:
   matched=[p for p in PERIODS if f['fact_id'] in p[3]]
   if not matched:continue
   start,end,value,ids=matched[0]
   if f['fact_id'] in selected or result['disposition']!='candidate_numeric_equal' or candidate['numeric_equal'] is not True:raise ValueError('ambiguous or unequal loss evidence')
   if f['concept']!={'namespace':'http://fasb.org/us-gaap/2025','local_name':'NetIncomeLoss'} or f['period']!={'kind':'duration','startDate':start,'endDate':end} or f['unit']!={'kind':'simple','measures':[USD]} or f['dimension_or_scenario_present'] is not False or f['numeric_conversion_verified'] is not True or f['numeric_value']!=value:raise ValueError('unsupported loss context')
   if f['issuer_identifier_as_filed']!='0001697884' or f['issuer_identifier_scheme']!='http://www.sec.gov/CIK' or f['raw_member_sha256']!=summary['raw_member_sha256']:raise ValueError('loss source identity')
   if f['format']!={'namespace':'http://www.xbrl.org/inlineXBRL/transformation/2015-02-26','local_name':'numdotdecimal'} or f['text_untransformed']!=format(abs(int(value)),',') or f['sign_as_filed']!='-' or f['scale_as_filed'] is not None or f['decimals_as_filed']!='0' or f.get('footnote_refs_as_filed') not in (None,''):raise ValueError('loss transformation or footnote')
   num=candidate['prepared_num'];sub=candidate['prepared_submission']
   if sub['adsh']!=ACCESSION or sub['cik']!=CIK or sub['rowid']!=card['provenance']['prepared_submission_rowid'] or sub['name']!=card['issuer']['name_as_filed'] or sub['form']!='10-Q' or sub['period']!='20250731' or sub['filed']!='20260617' or sub['fy']!=card['filing']['fiscal_year_as_filed'] or sub['fp']!=card['filing']['fiscal_period_as_filed']:raise ValueError('loss filing identity')
   if num['adsh']!=ACCESSION or num['tag']!='NetIncomeLoss' or num['version']!='us-gaap/2025' or num['ddate']!=end.replace('-','') or num['qtrs']!='1' or num['uom']!='USD' or num['segments']!='' or num['coreg']!='' or num['footnote']!='' or not re.fullmatch(r'-[0-9]{1,15}(?:\.[0-9]{1,8})?',num['value']) or Decimal(num['value'])!=Decimal(value):raise ValueError('loss prepared correspondence')
   selected[f['fact_id']]={'occurrence':{'fact_id':f['fact_id'],'context_ref':f['context_ref'],'context_serialization_sha256':f['context_serialization_sha256'],'source_literal':f['text_untransformed'],'sign_as_filed':'-','scale_as_filed':None,'declared_decimals':'0'},'prepared_num_rowid':num['rowid'],'prepared_value_as_filed':num['value']}
 if set(selected)!={fid for p in PERIODS for fid in p[3]}:raise ValueError('missing loss occurrences')
 facts=[]
 for start,end,value,ids in PERIODS:
  a,b=[selected[x] for x in ids]
  if a['prepared_num_rowid']!=b['prepared_num_rowid'] or a['prepared_value_as_filed']!=b['prepared_value_as_filed'] or a['occurrence']['context_ref']!=b['occurrence']['context_ref'] or a['occurrence']['context_serialization_sha256']!=b['occurrence']['context_serialization_sha256']:raise ValueError('repeated occurrence conflict')
  facts.append({'concept':'NetIncomeLoss','taxonomy_namespace':'http://fasb.org/us-gaap/2025','value':value,'currency':'USD','period_start':start,'period_end':end,'dimension_or_scenario_present':False,'source_occurrences':[selected[x]['occurrence'] for x in ids],'occurrences_are_not_independent_facts':True,'source_transform':'TRR3 numdotdecimal with explicit negative sign','prepared_num_rowid':a['prepared_num_rowid'],'prepared_value_as_filed':a['prepared_value_as_filed'],'prepared_qtrs':'1','prepared_exact_start_date_verified':False})
 delta=str(int(PERIODS[0][2])-int(PERIODS[1][2]))
 card.update(id='vitaspring-reported-net-loss',title='Historical net-loss evidence: both reported periods remain loss-making',finding='The retained filing reports net losses of $110,845 for May–July 2025 and $218,662 for May–July 2024. The signed reported amount differs by $107,817, a narrower reported loss, not a profit or an earnings-growth percentage.',research_disposition='SOURCE_REPORTED_LOSSES_REQUIRE_ACCOUNTING_AND_TIMING_REVIEW',facts=facts,
  calculation={'metric':'current_minus_prior_reported_net_income_loss','value':delta,'currency':'USD','formula':'(-110845) - (-218662)','interpretation':'Arithmetic difference between two reported signed amounts; both are negative. This is not adjusted/comparable earnings growth.','percentage_growth':None,'percentage_growth_reason':'NEGATIVE_COMPARISON_BASE_NOT_PRESENTED_AS_EARNINGS_GROWTH','causal_explanation':None},
  blockers=['These are historical 2025/2024 periods in a filing reported in June 2026, not current financials or newly announced results.','Both reported values are losses. No percentage earnings growth, profitability turnaround, sustainable improvement or causal explanation is established.','Full accounting comparability, restatement/novelty assessment and earliest public timing are not independently verified.','Issuer CIK is not verified tradable-security identity. No licensed price/outcome or execution evidence is joined.'],
  next_research_steps=['Review the linked original statement and accounting notes to understand the composition of each loss before interpreting their difference.','Reconcile amendments, accounting scope and release history before treating the amounts as comparable or novel.','Establish security identity, decision-time availability and permitted outcome data before predictive evaluation.'])
 card['limitations']=[x for x in card['limitations'] if not x.startswith('Dash-to-zero')]+['The four displayed source occurrences represent two source-local context groups; duplicated presentation is not independent corroboration.','The arithmetic uses exact integer reported dollar amounts. It does not establish constant accounting scope, operating performance, causation or economic significance.']
 return card

def save(config,out):
 out=Path(out).resolve()
 if out.exists() or out.is_relative_to(Path(__file__).resolve().parents[1]) or not out.parent.is_dir():raise ValueError('trusted new private output')
 out.mkdir(mode=0o700);write_private(out/'INCOMPLETE',{});summary,results=correspondence(**config);receipt,_=read_pinned(config['manifest'],config['manifest_sha'],100000);card=build(summary,results,receipt)
 write_private(out/'finding.json',card);write_private(out/'COMPLETE.json',{'finding_sha256':sha(out/'finding.json')});(out/'INCOMPLETE').unlink();return card

if __name__=='__main__':
 from private_prices import unique_object
 p=argparse.ArgumentParser();p.add_argument('--config',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();b=a.config.read_bytes()
 if len(b)>20000:raise ValueError('config bound')
 c=json.loads(b,object_pairs_hook=unique_object,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('invalid constant')));print(json.dumps(save(c,a.out)))
