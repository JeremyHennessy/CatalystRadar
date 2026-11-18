"""Four-column reported vote tables and one reviewed conditional plan authorization."""
import argparse,re,zipfile
from pathlib import Path
from financial_admission_rehearsal import plain
from material_agreement_screen import build as validated_cohort,screen as document_inventory
from filing_registrant_identity import ZIP_SHA,digest,span
from financial_pair_candidates import sha,write_private
ITEM=b'Submission of Matters to a Vote of Security Holders'
RAW_SHA='334e2d3e421d2fc51bb45c89ccca169284bd66b9ed9865292d39b0a3e41a592e'
N=r'(0|[1-9][0-9]{0,2}(?:,[0-9]{3}){0,6}|[1-9][0-9]{0,18})'
TABLE=re.compile(r'Votes For Votes Against Abstentions Broker Non-Votes '+N+' '+N+' '+N+' '+N)
KEYS=('votes_for_as_reported','votes_against_as_reported','abstentions_as_reported','broker_non_votes_as_reported')

def table_values(raw):
 if type(raw)is not bytes or len(raw)>20000 or raw.lower().count(b'<table')!=1 or raw.lower().count(b'</table>')!=1:raise ValueError('table bounds/inventory')
 if re.search(rb'<!--|<(?:script|style)\b',raw,re.I):return None
 m=TABLE.fullmatch(plain(raw))
 if not m:return None
 return dict(zip(KEYS,(s.replace(',','') for s in m.groups())))

def screen(raw):
 inventory=document_inventory(raw);primary=inventory['primary']['source_span'];head=raw[raw.index(b'<SEC-HEADER>'):raw.index(b'</SEC-HEADER>')]
 matches=[m for m in re.findall(rb'^ITEM INFORMATION:[ \t]*([^\r\n]+)',head,re.M) if m==ITEM]
 if len(matches)>1:raise ValueError('duplicate voting item')
 out={'item_5_07_declared':bool(matches),'status':'AMENDMENT_REQUIRES_REVIEW' if inventory['primary']['type_as_filed']=='8-K/A' else 'DECLARED_VOTE_ITEM_REQUIRES_SOURCE_CONTEXT' if matches else 'NO_ITEM_5_07_HEADER_NOT_NO_VOTE','primary':inventory['primary'],'tables':[],'unsupported_vote_tables':0}
 if not matches or inventory['primary']['type_as_filed']!='8-K':return out
 body=raw[primary['byte_start']:primary['byte_end']]
 excluded=[(m.start(),m.end()) for m in re.finditer(rb'<!--.*?(?:-->|$)|<(script|style)\b[^>]*>.*?(?:</\1\s*>|$)',body,re.I|re.S)]
 for t in re.finditer(rb'<table\b[^>]*>.*?</table>',body,re.I|re.S):
  if len(t[0])>20000 or any(t.start()<b and t.end()>a for a,b in excluded):continue
  text=plain(t[0])
  if not all(x in text for x in ('Votes For','Votes Against','Abstentions','Broker Non-Votes')):continue
  values=table_values(t[0])
  if values is None:out['unsupported_vote_tables']+=1;continue
  out['tables'].append({'values':values,'source_span':span(raw,primary['byte_start']+t.start(),primary['byte_start']+t.end()),'proposal_identity':None,'approval_inferred_from_counts':False,'approval_percentage':None})
 return out

def reviewed_plan(raw,result):
 if digest(raw)!=RAW_SHA or not result['item_5_07_declared']:raise ValueError('reviewed source pin')
 expected=[(39867,42582),(43107,45834),(46315,49042)]
 if [(t['source_span']['byte_start'],t['source_span']['byte_end']) for t in result['tables']]!=expected or result['unsupported_vote_tables']!=1:raise ValueError('reviewed tables')
 # Context remains separate from numeric parsing; exact pinned original was independently read.
 labels=[('AUDITOR_RATIFICATION',39129,39867),('ADVISORY_EXECUTIVE_COMPENSATION',42617,43107),('INCENTIVE_PLAN_APPROVAL',45869,46315)]
 for t,(label,start,end) in zip(result['tables'],labels):
  if 'was approved as follows:' not in plain(raw[start:end]):raise ValueError('reported approval context')
  t.update(proposal_identity=label,approval_as_reported=True,context_span=span(raw,start,end))
 text=plain(raw[19647:20429])
 for phrase in ('one business day following shareholder approval','6,500,000, less one share for every one share','under the 2018 Plan after September 11, 2026'):
  if phrase not in text:raise ValueError('authorization conditions')
 if 'Annual Meeting was held on November 10, 2026' not in plain(raw[24044:24435]):raise ValueError('meeting date')
 return {'issuer_cik_as_filed':'0000012659','issuer_name_as_filed':'H&R BLOCK INC','meeting_date_as_reported':'2026-11-10','authorization':{'base_share_amount_as_reported':'6500000','unit':'company common shares available for awards subject to adjustment and deduction','deduction_rule':'Subtract one share for every share subject to an award granted under the 2018 Plan after September 11, 2026.','deduction_quantity':None,'net_available_shares':None,'shares_actually_issued':None,'dilution_percentage':None,'effective_rule_as_reported':'One business day following shareholder approval at the Annual Meeting.','computed_effective_date':None,'source_span':span(raw,19647,20429)},'plan_name_as_reported':'H&R Block, Inc. 2026 Long Term Incentive Plan','summary_not_exhaustive':True,'full_plan_and_proxy_not_comprehensively_reviewed':True,'approval_context_span':span(raw,18753,19591),'meeting_date_span':span(raw,24044,24435),'voting_denominator_rule':None,'total_across_proposals':None,'training_ready':False,'execution_ready':False}

def build(archive):
 # Reuse full ten-member archive/receipt/hash/identity/clock validation, not its findings.
 verified=validated_cohort(archive);rows=[]
 with zipfile.ZipFile(archive) as z:
  for source in verified['packages']:
   raw=z.read(source['source_sha256']+'.txt')
   if digest(raw)!=source['source_sha256']:raise ValueError('source changed')
   result=screen(raw);finding=None
   if source['source_sha256']==RAW_SHA:
    if source['filers_as_reported']!=[{'cik':'0000012659','name_as_filed':'H&R BLOCK INC'}]:raise ValueError('reviewed issuer')
    finding=reviewed_plan(raw,result)
   rows.append({k:source[k] for k in ('accession','filers_as_reported','source_url','source_sha256','source_bytes','source_observed_utc_as_recorded','first_public_utc','historical_availability_verified')}|result|{'reviewed_plan':finding})
 if sha(archive)!=ZIP_SHA:raise ValueError('archive changed')
 return {'version':1,'category':'SHAREHOLDER_VOTE_AND_CONDITIONAL_AUTHORIZATION_RESEARCH','selection':'ALL_TEN_RETAINED_PACKAGES_FIXED_HEADER_AND_TABLE_RULE_RETROSPECTIVE','counts':{'packages':len(rows),'declared_voting_packages':sum(r['item_5_07_declared'] for r in rows),'no_item_declaration':sum(not r['item_5_07_declared'] for r in rows),'supported_four_column_tables':sum(len(r['tables']) for r in rows),'unsupported_vote_tables':sum(r['unsupported_vote_tables'] for r in rows),'source_reviewed_plans':sum(r['reviewed_plan']is not None for r in rows)},'packages':rows,'provenance':verified['provenance'],'limitations':['This is a retained ten-package retrospective diagnostic, not market-wide or prospectively preregistered discovery.','No Item5.07 header does not mean no shareholder vote. Unsupported tables remain unparsed, not zero votes.','Vote categories remain separate source counts; no percentage, legal majority test or sum across proposals is inferred.','Approval comes from the reviewed source context, not from calculating a majority. Advisory compensation voting is not an equity grant.','The issuer summary is qualified by the full plan and proxy; this is not an exhaustive assessment of eligibility, adjustments or legal terms.','Conditional plan authorization is not shares issued or known dilution. Old-plan award deductions and adjustment effects are unknown.','One business day after approval is preserved as a rule; no calendar-derived effective date is assigned.','Filing and meeting dates do not prove earliest public availability. Retained observation was later.','No individual director identities, addresses, contacts or full narrative are published. Existing source files/reports/ledger are unchanged.'], 'training_ready':False,'execution_ready':False}

def save(archive,out):
 out=Path(out).resolve()
 if out.exists() or not out.parent.is_dir() or out.is_relative_to(Path(__file__).resolve().parents[1]):raise ValueError('new private output required')
 out.mkdir(mode=0o700);write_private(out/'INCOMPLETE',{});result=build(archive);write_private(out/'votes.json',result);write_private(out/'COMPLETE.json',{'votes_sha256':sha(out/'votes.json')});(out/'INCOMPLETE').unlink();return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--archive',required=True);p.add_argument('--out',required=True);a=p.parse_args();save(a.archive,a.out)
