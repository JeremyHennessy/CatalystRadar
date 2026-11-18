"""Narrow source-reported operating/net/basic-EPS extraction; no accounting admission."""
import argparse,datetime as dt,hashlib,json,re
from decimal import Decimal,localcontext
from pathlib import Path
import issuer_revenue_comparison as revenue
from financial_pair_candidates import sha,write_private
from openfigi_evidence import read_pinned
REVENUE_PATH='web/company-findings/ieh-reported-revenue.json'
REVENUE_SHA='74c4fff28c44a4213993cfa487b7745006a71a23d9274f5cbdd5516257719002'
REVENUE_BYTES=4778
M=revenue.MONEY;Q=revenue.Q
PATTERN=re.compile(r'For the quarter ended (?P<current_end>'+revenue.DATE+r'), (?P<label>[A-Z][A-Za-z0-9 &.-]{0,60}) had revenues of \$(?P<revenue_current>'+M+r') as compared to \$(?P<revenue_prior>'+M+r') for the quarter ended (?P<prior_end>'+revenue.DATE+r'), reflecting a (?P<reported_percent>[0-9]{1,3})% increase; an operating (?P<op_current_term>profit) of \$(?P<op_current>'+M+r') for (?P<op_current_period>'+Q+r') as compared to an operating (?P<op_prior_term>loss) of \$(?P<op_prior>'+M+r') for (?P<op_prior_period>'+Q+r'); net (?P<net_current_term>income) of \$(?P<net_current>'+M+r') for (?P<net_current_period>'+Q+r') as compared to a net (?P<net_prior_term>loss) of \$(?P<net_prior>'+M+r') for (?P<net_prior_period>'+Q+r'); and a basic (?P<eps_current_term>gain) per share of \$(?P<eps_current>\.[0-9]{1,4}) for (?P<eps_current_period>'+Q+r') as compared to a basic (?P<eps_prior_term>loss) per share of \$(?P<eps_prior>\.[0-9]{1,4}) for (?P<eps_prior_period>'+Q+r')\.')
METRICS=(('op','OperatingProfitLoss','dollars_as_reported'),('net','NetIncomeLoss','dollars_as_reported'),('eps','BasicEarningsLossPerShare','dollars_per_basic_share_as_reported'))

def signed(literal,term):
 n=Decimal(literal.replace(',',''))
 if not n.is_finite() or n<=0:raise ValueError('positive literal with explicit sign term required')
 if term not in ('profit','income','gain','loss'):raise ValueError('unsupported sign term')
 return format(n.copy_negate() if term=='loss' else n,'f')

def extract(raw):
 evidence=revenue.extract(raw)
 if evidence['status']!='ONE_REPORTED_TEXT_COMPARISON':raise ValueError('exactly one supported paragraph required')
 source=evidence['records'][0];text=source['source_paragraph_text'];m=PATTERN.fullmatch(text)
 if not m:raise ValueError('unsupported full results paragraph')
 # Do not permit fiscal label mismatches to silently become one comparison.
 current={m[p+'_current_period'] for p,_,_ in METRICS};prior={m[p+'_prior_period'] for p,_,_ in METRICS}
 if len(current)!=1 or len(prior)!=1:raise ValueError('inconsistent fiscal labels')
 current_label=next(iter(current));prior_label=next(iter(prior))
 if current_label.split(' quarter ')[0]!=prior_label.split(' quarter ')[0] or int(current_label[-4:])!=int(prior_label[-4:])+1:raise ValueError('unsupported fiscal comparison labels')
 # Quoted paragraphs are not accepted as affirmative source prose by this module.
 start,end=source['evidence_span']['byte_start'],source['evidence_span']['byte_end'];stack=[]
 for tag in re.finditer(rb'<(/?)(blockquote|q)\b[^>]*>',raw[:end],re.I):
  if tag.start()>=start:raise ValueError('quoted paragraph unsupported')
  name=tag[2].lower()
  if tag[1]:
   if not stack or stack.pop()!=name:raise ValueError('ambiguous quote context')
  else:stack.append(name)
 if stack:raise ValueError('quoted context unsupported')
 rows=[]
 for prefix,metric,unit in METRICS:
  a=signed(m[prefix+'_current'],m[prefix+'_current_term']);b=signed(m[prefix+'_prior'],m[prefix+'_prior_term'])
  with localcontext() as c:
   c.prec=80;delta=format(Decimal(a)-Decimal(b),'f')
  facts=[]
  for role,val,label in [('current',a,current_label),('prior',b,prior_label)]:
   key=prefix+'_'+role;lo,hi=m.span(key)
   facts.append({'comparison_role':role,'signed_value':val,'literal_as_reported':m[key],'sign_term_as_reported':m[key+'_term'],'fiscal_period_label_as_reported':label,'period_end_as_reported':source[role+'_period_end'],'period_start':None,'normalized_literal_span':{'character_start':lo,'character_end':hi,'utf8_sha256':hashlib.sha256(text[lo:hi].encode()).hexdigest()}})
  rows.append({'metric':metric,'unit_as_reported':unit,'currency_symbol_as_reported':'$','currency_iso':None,'facts':facts,'absolute_difference_current_minus_prior':delta,'difference_unit':unit,'difference_basis':'CALCULATED_SIGNED_DIFFERENCE_FROM_REPORTED_AMOUNTS','percentage_change':None,'percentage_change_reason':'NEGATIVE_PRIOR_BASELINE_NO_GROWTH_PERCENTAGE','accounting_comparability_verified':False})
 return {'status':'ONE_ISSUER_REPORTED_RESULTS_PARAGRAPH','issuer_short_label':m['label'],'current_fiscal_label_as_reported':current_label,'prior_fiscal_label_as_reported':prior_label,'metrics':rows,'source':source,'training_ready':False,'execution_ready':False}

def build(raw,receipt,prior):
 # Reuse the existing reviewed original identity/receipt/grammar checks unchanged.
 reviewed,old_evidence=revenue.build(raw,receipt)
 if prior.get('id')!=reviewed['id'] or prior['issuer']!=reviewed['issuer'] or prior['filing']!=reviewed['filing'] or prior['comparison']!=reviewed['comparison'] or prior['provenance']!=reviewed['provenance']:raise ValueError('existing revenue source correspondence')
 result=extract(raw);source=result['source']
 if result['issuer_short_label']!='IEH' or result['current_fiscal_label_as_reported']!='2nd quarter fiscal year 2027' or result['prior_fiscal_label_as_reported']!='2nd quarter fiscal year 2026':raise ValueError('reviewed period identity')
 if source['evidence_span']!=prior['comparison']['evidence_span'] or source['document_sha256']!=prior['comparison']['document_sha256']:raise ValueError('same paragraph required')
 out={'schema_version':1,'id':'ieh-reported-quarterly-operating-net-basic-results','status':'ISSUER_REPORTED_FINANCIAL_RESULTS_NOT_INDEPENDENTLY_COMPARABLE','generated_at':dt.datetime.now(dt.timezone.utc).isoformat(),'issuer':prior['issuer'],'filing':prior['filing'],'metrics':result['metrics'],'revenue_cross_reference':{'path':REVENUE_PATH,'bytes':REVENUE_BYTES,'sha256':REVENUE_SHA,'finding_id':prior['id'],'same_accession_cik_and_paragraph_verified':True},'source_evidence':{'exhibit_filename':source['filename'],'document_sha256':source['document_sha256'],'paragraph_span':source['evidence_span'],'normalized_text_method':'financial_admission_rehearsal.plain; character spans and UTF-8 substring hashes are not raw byte spans'},'provenance':prior['provenance'],'interpretation':['The issuer reports an operating profit versus an operating loss, net income versus a net loss, and basic EPS gain versus basic EPS loss in the stated quarters. These are source-reported results, not independently audited accounting truth.','Absolute differences are exact subtraction of the signed reported values. No percentage growth from a negative prior baseline is presented.','Basic EPS is not diluted EPS; no weighted-average shares, share dilution, margin, implied currency or earnings quality is inferred.','Fiscal labels FY2027 Q2 and FY2026 Q2 accompany quarter ends September 30, 2026 and September 30, 2025. Exact start dates and ISO currency remain unknown.','This uses the same retained EX-99.1 paragraph as the prior revenue finding. It is additional metrics, not independent confirmation or a new economic event.','The underlying quarterly statements, accounting scope/policies, amendments and full comparability remain unreviewed. Source retrieval is retrospective, not first-public timing or evidence of a current catalyst.'],'next_action':'Review the original quarterly statements and notes for exact durations, ISO currency, accounting scope and comparative basis before any further financial interpretation.','accounting_comparability_verified':False,'historical_security_mapping_verified':False,'original_10q_checked':False,'first_public_utc':None,'probability':None,'price_target':None,'return_estimate':None,'training_ready':False,'execution_ready':False}
 return out,result

def save(root,archive,out):
 out=Path(out).resolve()
 if out.exists() or out.is_relative_to(Path(__file__).resolve().parents[1]) or not out.parent.is_dir():raise ValueError('new trusted private output required')
 out.mkdir(mode=0o700);write_private(out/'INCOMPLETE',{})
 prior,n=read_pinned(Path(root)/REVENUE_PATH,REVENUE_SHA,REVENUE_BYTES)
 if n!=REVENUE_BYTES:raise ValueError('revenue source size')
 raw,receipt=revenue.load_source(archive);public,private=build(raw,receipt,prior)
 write_private(out/'evidence.json',private);write_private(out/'finding.json',public);write_private(out/'COMPLETE.json',{'evidence_sha256':sha(out/'evidence.json'),'finding_sha256':sha(out/'finding.json')});(out/'INCOMPLETE').unlink();return public
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',default=str(Path(__file__).resolve().parents[1]));p.add_argument('--archive',required=True);p.add_argument('--out',required=True);a=p.parse_args();print(save(a.root,a.archive,a.out)['id'])
