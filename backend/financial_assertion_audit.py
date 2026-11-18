"""Fixed-original financial assertion arithmetic audit, not qualified growth."""
import argparse,datetime as dt,hashlib,json,re,zipfile
from decimal import Decimal,localcontext,ROUND_HALF_UP
from fractions import Fraction
from pathlib import Path
import issuer_revenue_comparison as revenue
import issuer_quarterly_results as results
import company_revenue_finding as vita_revenue
import company_loss_finding as vita_loss
from source_prepared_correspondence import audit as vita_audit
from material_agreement_screen import build as inventory_audit
from frozen_outcome_source_review import inspect as txmd_context,ACC as TXMD_ACC,RAW_SHA as TXMD_SHA
from financial_admission_rehearsal import plain
from filing_registrant_identity import strict
from openfigi_evidence import read_pinned
from financial_pair_candidates import sha,write_private
PINS={'ieh_revenue': {'path': 'web/company-findings/ieh-reported-revenue.json', 'bytes': 4778, 'sha256': '74c4fff28c44a4213993cfa487b7745006a71a23d9274f5cbdd5516257719002'}, 'ieh_results': {'path': 'web/company-findings/ieh-reported-quarterly-results.json', 'bytes': 8936, 'sha256': 'dbfc2234fce3275894fe908331f57f1ca0cd1f0bbedbebceccb2868f067ad18a'}, 'vita_revenue': {'path': 'web/company-findings/vitaspring-revenue.json', 'bytes': 5874, 'sha256': '56b604c79e02b7ca45f5bf3cf46c3fc2b5d6cb1957324ed2ccb761d4ce38d98b'}, 'vita_loss': {'path': 'web/company-findings/vitaspring-net-loss.json', 'bytes': 7545, 'sha256': '854a68cd119b608e34a081b562f7070b27dbfc009f518cb28d3aeac57bfef835'}, 'txmd_annotation': {'path': 'web/company-findings/frozen-outcome-txmd-source-review.json', 'bytes': 5885, 'sha256': 'fe7fc58256104bae75d7c5822f03a5a625e7c03cc8c6cbaa575cab218654953f'}}
POLICY_SHA='69b856309123380dd824dd2537d62e6596ffab56edc05812aedb370ad3eab7eb'
N=r'[0-9]{1,12}(?:\.[0-9]{1,6})?'
Q=r'(?:first|second|third|fourth)'
TXMD=re.compile(r'The Company recorded \$(?P<current>'+N+r') (?P<current_scale>million|thousand) in license revenue for the (?P<current_quarter>'+Q+r') quarter of (?P<current_year>20[0-9]{2}), an increase of \$(?P<increase>'+N+r') (?P<increase_scale>million|thousand), or (?P<percent>'+N+r')%, compared to \$(?P<prior>'+N+r') (?P<prior_scale>million|thousand) in license revenue for the (?P<prior_quarter>'+Q+r') quarter of (?P<prior_year>20[0-9]{2})\. The increase is primarily attributable to the achievement of an (?P<product>IMVEXXY) sales-based milestone by (?P<counterparty>Knight) relating to IMVEXXY sales for the year ended (?P<sales_end>December 31, 20[0-9]{2}), resulting in a \$(?P<milestone>'+N+r') (?P<milestone_scale>million|thousand) milestone payment that was recognized and confirmed by Knight in the (?P<recognition_quarter>'+Q+r') quarter of (?P<recognition_year>20[0-9]{2})\.')
SCALES={'units':1,'thousand':1000,'million':1000000}
def digest(b):return hashlib.sha256(b).hexdigest()
def dec(v):
 if not isinstance(v,str) or not re.fullmatch(r'-?[0-9]{1,20}(?:\.[0-9]{1,10})?',v):raise ValueError('bounded finite decimal string required')
 return Decimal(v)
def scaled(v,scale):
 if scale not in SCALES:raise ValueError('unsupported scale')
 with localcontext() as c:c.prec=100;return format(dec(v)*SCALES[scale],'f')
def fraction_result(f,places):
 if type(places)is not int or not 0<=places<=6:raise ValueError('rounding precision')
 with localcontext() as c:
  c.prec=100;n=Decimal(f.numerator)/Decimal(f.denominator);rounded=n.quantize(Decimal(1).scaleb(-places),rounding=ROUND_HALF_UP)
 return {'numerator':str(f.numerator),'denominator':str(f.denominator),'rounded_value':format(rounded,'f'),'decimal_places':places,'rounding_rule_for_check':'ROUND_HALF_UP_NOT_INFERRED_ISSUER_POLICY'}
def arithmetic(current,prior,precision_basis,reported_increase=None,reported_percent=None,percent_places=1):
 if precision_basis not in ('REPORTED_UNSCALED_LITERALS','DECLARED_INLINE_NUMERIC_VALUES','DISPLAYED_MIXED_SCALE_LITERALS'):raise ValueError('precision basis')
 a=dec(current);b=dec(prior)
 with localcontext() as c:c.prec=100;delta=format(a-b,'f')
 out={'basis':precision_basis,'current_normalized_literal':current,'prior_normalized_literal':prior,'signed_difference_of_literals':delta,'difference_status':'DISPLAY_LITERAL_ARITHMETIC_NOT_UNROUNDED_CHANGE' if precision_basis=='DISPLAYED_MIXED_SCALE_LITERALS' else 'CALCULATED_SIGNED_DIFFERENCE_FROM_REPORTED_VALUES','reported_increase':reported_increase,'reported_percent':reported_percent,'endpoint_percentage_check':None,'reported_increase_percentage_check':None,'percentage_abstention':None,'true_unrounded_change':None,'accounting_comparability_verified':False,'qualified_growth':False}
 if reported_increase is not None:dec(reported_increase)
 if reported_percent is not None:dec(reported_percent)
 if b<=0:out['percentage_abstention']='ZERO_COMPARISON_BASE_UNDEFINED' if b==0 else 'NEGATIVE_BASE_NOT_PRESENTED_AS_GROWTH';return out
 f=(Fraction(a)-Fraction(b))*100/Fraction(b);check=fraction_result(f,percent_places)
 check['meaning']='DISPLAY_LITERAL_RATIO_NOT_TRUE_GROWTH' if precision_basis=='DISPLAYED_MIXED_SCALE_LITERALS' else 'REPORTED_ENDPOINT_ARITHMETIC_NOT_ACCOUNTING_COMPARABILITY'
 check['matches_reported_percent_at_check_precision']=None if reported_percent is None else Decimal(check['rounded_value'])==dec(reported_percent);out['endpoint_percentage_check']=check
 if reported_increase is not None:
  second=fraction_result(Fraction(dec(reported_increase))*100/Fraction(b),percent_places);second['meaning']='REPORTED_INCREASE_OVER_DISPLAYED_PRIOR_INTERNAL_CLAIM_CHECK';second['matches_reported_percent_at_check_precision']=None if reported_percent is None else Decimal(second['rounded_value'])==dec(reported_percent);out['reported_increase_percentage_check']=second
 return out

def txmd_extract(raw):
 # Reuse the strict document/encoding/inventory checks, not the old finditer license parser.
 revenue.extract(raw);matches=[]
 for d in re.finditer(rb'<DOCUMENT>.*?</DOCUMENT>',raw,re.S):
  header=d[0].split(b'<TEXT>',1)[0]
  if re.findall(rb'^<TYPE>([^\r\n]+)',header,re.M)!=[b'EX-99.1']:continue
  names=re.findall(rb'^<FILENAME>([^\r\n]+)',header,re.M)
  if len(names)!=1 or not re.fullmatch(rb'[A-Za-z0-9_.-]{1,100}',names[0]):raise ValueError('exhibit filename')
  excluded=[(x.start(),x.end()) for x in re.finditer(rb'<!--.*?(?:-->|$)|<(script|style)\b[^>]*>.*?(?:</\1\s*>|$)',d[0],re.S|re.I)]
  for p in re.finditer(rb'<(p|td)\b[^>]*>.*?</\1>',d[0],re.S|re.I):
   if any(p.start()<b and p.end()>a for a,b in excluded):continue
   text=plain(p[0]);m=TXMD.fullmatch(text)
   if not m:continue
   start,end=d.start()+p.start(),d.start()+p.end();stack=[]
   for tag in re.finditer(rb'<(/?)(blockquote|q)\b[^>]*>',raw[:end],re.I):
    if tag.start()>=start:raise ValueError('quoted financial paragraph')
    if tag[1]:
     if not stack or stack.pop()!=tag[2].lower():raise ValueError('ambiguous quote context')
    else:stack.append(tag[2].lower())
   if stack:raise ValueError('quoted context')
   if m['current_quarter']!=m['prior_quarter'] or int(m['current_year'])!=int(m['prior_year'])+1:raise ValueError('unsupported period relationship')
   vals={k:m[k] for k in m.groupdict()};spans={}
   for k in ('current','prior','increase','percent','milestone'):
    a,b=m.span(k);spans[k]={'character_start':a,'character_end':b,'utf8_sha256':digest(text[a:b].encode())}
   matches.append({'values_as_reported':vals,'normalized_literal_spans':spans,'paragraph_span':{'byte_start':start,'byte_end':end,'sha256':digest(p[0])},'exhibit_sha256':digest(d[0]),'exhibit_filename':names[0].decode(),'source_paragraph_text':text})
 return {'status':'NOT_SUPPORTED_GRAMMAR' if not matches else 'AMBIGUOUS_MULTIPLE_SUPPORTED_PARAGRAPHS' if len(matches)>1 else 'ONE_SUPPORTED_FULL_PARAGRAPH','records':matches}

def equivalent(a,b):return {k:v for k,v in a.items() if k!='generated_at'}=={k:v for k,v in b.items() if k!='generated_at'}
def pair(metric,current,prior,unit,currency,periods,precision,evidence,**claims):
 return {'metric':metric,'current_value_for_arithmetic':current,'prior_value_for_arithmetic':prior,'unit_as_reported':unit,'currency_iso':currency,'periods_as_reported':periods,'source_evidence':evidence,'arithmetic':arithmetic(current,prior,precision,**claims),'first_public_utc':None,'comparability_verified':False,'training_ready':False,'execution_ready':False}

def build(root,archive,vita_config,policy_path):
 root=Path(root);policy,n=read_pinned(policy_path,POLICY_SHA,10000)
 if vita_config.get('archive_sha')!=policy['vita_archive_sha256']:raise ValueError('Vita inventory pin')
 for name,pin in policy['existing_module_versions'].items():
  if '/' in name or sha(root/'backend'/name)!=pin:raise ValueError('frozen adapter version')
 old={}
 for key,p in PINS.items():
  old[key],n=read_pinned(root/p['path'],p['sha256'],p['bytes'])
  if n!=p['bytes']:raise ValueError('released source size')
 inv=inventory_audit(archive)
 if inv['provenance']['archive_sha256']!=policy['original_archive_sha256'] or len(inv['packages'])!=10:raise ValueError('frozen inventory')
 private=[];packages=[]
 with zipfile.ZipFile(archive) as z:
  receipts={r['accession']:r for r in [strict(line) for line in z.read('manifest.jsonl').splitlines()]}
  for item in inv['packages']:
   raw=z.read(item['source_sha256']+'.txt')
   header=raw.split(b'</SEC-HEADER>',1)[0];form=re.findall(rb'CONFORMED SUBMISSION TYPE:\s*([^\r\n]+)',header)
   if form!=[b'8-K']:raise ValueError('fixed inventory form/amendment changed')
   dates={}
   for field,label in [(b'FILED AS OF DATE','filing_date_as_reported'),(b'CONFORMED PERIOD OF REPORT','report_date_as_reported')]:
    vals=re.findall(field+rb':\s*([0-9]{8})\s*\n',header)
    if len(vals)!=1:raise ValueError('unique source header date required')
    dates[label]=dt.datetime.strptime(vals[0].decode(),'%Y%m%d').date().isoformat()
   ieh=revenue.extract(raw);tx=txmd_extract(raw);pairs=[];status='NOT_SUPPORTED_GRAMMAR';annotation=None
   base={**dates,'amendment_as_filed':False,'source_request_utc_as_recorded':receipts[item['accession']]['request_utc'],'package_id':item['accession'],'accession':item['accession'],'form_as_filed':'8-K','filers_as_reported':item['filers_as_reported'],'source_url':item['source_url'],'source_sha256':item['source_sha256'],'source_observed_utc_as_recorded':item['source_observed_utc_as_recorded'],'first_public_utc':None}
   if ieh['status']=='AMBIGUOUS_MULTIPLE_COMPARISONS' or tx['status']=='AMBIGUOUS_MULTIPLE_SUPPORTED_PARAGRAPHS':status='AMBIGUOUS_MULTIPLE_SUPPORTED_PARAGRAPHS'
   elif ieh['status']=='ONE_REPORTED_TEXT_COMPARISON':
    if item['accession']!=revenue.ACC or item['source_sha256']!=revenue.RAW_SHA:raise ValueError('unsupported matched issuer requires review')
    r,receipt=revenue.load_source(archive);card,e=revenue.build(r,receipt);more,more_private=results.build(r,receipt,old['ieh_revenue'])
    if not equivalent(card,old['ieh_revenue']) or not equivalent(more,old['ieh_results']):raise ValueError('released IEH finding mismatch')
    c=card['comparison'];periods={'current_end':c['current_period_end'],'prior_end':c['prior_period_end'],'current_start':None,'prior_start':None,'basis':'ISSUER_REPORTED_QUARTER_ENDS_NOT_INDEPENDENT_DURATION'}
    pairs.append(pair('Revenues',c['current_value'],c['prior_value'],'dollars_as_reported',None,periods,'REPORTED_UNSCALED_LITERALS',{'paragraph_span':c['evidence_span'],'exhibit_sha256':c['document_sha256'],'exhibit_filename':c['filename'],'released_source_key':'ieh_revenue'},reported_percent=c['reported_percent_increase'],percent_places=0))
    for x in more['metrics']:
     a,b=x['facts'];p={**periods,'current_fiscal_label':a['fiscal_period_label_as_reported'],'prior_fiscal_label':b['fiscal_period_label_as_reported']}
     pairs.append(pair(x['metric'],a['signed_value'],b['signed_value'],x['unit_as_reported'],None,p,'REPORTED_UNSCALED_LITERALS',{'released_source_key':'ieh_results','source_evidence':more['source_evidence'],'facts_as_reported':x['facts']}))
    private.append({'package_id':item['accession'],'evidence':more_private});status='SUPPORTED_REPORTED_ASSERTIONS_NOT_COMPARABILITY'
   elif tx['status']=='ONE_SUPPORTED_FULL_PARAGRAPH':
    if item['accession']!=TXMD_ACC or item['source_sha256']!=TXMD_SHA or [f['cik'] for f in item['filers_as_reported']]!=['0000025743']:raise ValueError('license issuer identity')
    contextual=txmd_context(raw)
    if contextual!=old['txmd_annotation']['finding']:raise ValueError('released TXMD period annotation changed')
    r=tx['records'][0];v=r['values_as_reported']
    if r['exhibit_sha256']!=contextual['document_sha256'] or r['exhibit_filename']!=contextual['filename']:raise ValueError('license paragraph exhibit identity')
    current=scaled(v['current'],v['current_scale']);prior=scaled(v['prior'],v['prior_scale']);increase=scaled(v['increase'],v['increase_scale'])
    evidence={k:x for k,x in r.items() if k!='source_paragraph_text'}
    periods={'current_quarter_as_reported':v['current_quarter']+' quarter '+v['current_year'],'prior_quarter_as_reported':v['prior_quarter']+' quarter '+v['prior_year'],'current_end_declared_in_exhibit_body':contextual['body_reported_period']['end'],'current_start':None,'prior_end':None,'prior_start':None,'exact_comparable_durations_verified':False}
    one=pair('LicenseRevenueNotVerifiedTotalGAAPRevenue',current,prior,'display_scaled_dollars_as_reported',None,periods,'DISPLAYED_MIXED_SCALE_LITERALS',evidence,reported_increase=increase,reported_percent=v['percent'],percent_places=1)
    one['assertion_review_status']='DISPLAYED_ROUNDED_VALUES_NOT_EXACT_RECONCILIATION';one['display_precision']={'current_literal':v['current'],'current_scale':v['current_scale'],'prior_literal':v['prior'],'prior_scale':v['prior_scale'],'actual_unrounded_values':None,'rounding_policy':None}
    one['issuer_reported_attribution']={'basis':'ISSUER_REPORTED_NOT_CAUSALLY_VERIFIED','product':v['product'],'counterparty_as_reported':v['counterparty'],'milestone_literal':v['milestone'],'milestone_scale':v['milestone_scale'],'milestone_normalized_display_value':scaled(v['milestone'],v['milestone_scale']),'sales_year_end_as_reported':v['sales_end'],'recognition_quarter_as_reported':v['recognition_quarter']+' quarter '+v['recognition_year']}
    one['interpretation']='Displayed endpoint arithmetic does not reconcile the issuer-reported increase or percentage. Precision and context require review; this is not proof of an accounting error, and no hidden values or rounding policy are inferred.'
    pairs=[one];annotation={k:contextual[k] for k in ('description','body_reported_period','description_period_as_reported','description_body_period_conflict','conflict_resolution')};annotation['released_source_key']='txmd_annotation';private.append({'package_id':item['accession'],'evidence':tx});status='SUPPORTED_REPORTED_ASSERTIONS_NOT_COMPARABILITY'
   packages.append({**base,'status':status,'metric_pairs':pairs,'source_period_conflict':annotation,'unsupported_meaning':'No supported whole-context grammar in this explicitly pinned package, not no results/event.' if not pairs else None})
 if sha(archive)!=policy['original_archive_sha256']:raise ValueError('archive changed')
 if vita_config['archive_sha']!=policy['vita_archive_sha256']:raise ValueError('Vita inventory pin')
 s,rows=vita_audit(**vita_config);receipt,_=read_pinned(vita_config['manifest'],vita_config['manifest_sha'],100000);a=vita_revenue.build(s,rows,receipt);b=vita_loss.build(s,rows,receipt)
 if not equivalent(a,old['vita_revenue']) or not equivalent(b,old['vita_loss']):raise ValueError('released Vita source mismatch')
 pairs=[]
 for key,card,metric in [('vita_revenue',a,'Revenues'),('vita_loss',b,'NetIncomeLoss')]:
  x,y=card['facts'];periods={'current_start':x['period_start'],'current_end':x['period_end'],'prior_start':y['period_start'],'prior_end':y['period_end'],'basis':'EXACT_RETAINED_INLINE_CONTEXTS_NOT_FULL_ACCOUNTING_COMPARABILITY'}
  pairs.append(pair(metric,x['value'],y['value'],'USD', 'USD',periods,'DECLARED_INLINE_NUMERIC_VALUES',{'released_source_key':key,'facts_as_reported':card['facts'],'original_member_sha256':card['provenance']['original_member_sha256'],'original_archive_sha256':card['provenance']['original_archive_sha256']}))
 packages.append({'filing_date_as_reported':a['filing']['filing_date_as_reported'],'report_date_as_reported':a['filing']['period_of_report'],'amendment_as_filed':False,'source_request_utc_as_recorded':None,'package_id':a['filing']['accession'],'accession':a['filing']['accession'],'form_as_filed':a['filing']['form'],'filers_as_reported':[{'cik':a['issuer']['cik'],'name_as_filed':a['issuer']['name_as_filed']}],'source_url':a['filing']['source_primary_document_url'],'source_sha256':a['provenance']['original_member_sha256'],'source_observed_utc_as_recorded':None,'local_source_verified_utc':a['provenance']['source_local_verified_utc'],'first_public_utc':None,'status':'SUPPORTED_REPORTED_ASSERTIONS_NOT_COMPARABILITY','metric_pairs':pairs,'source_period_conflict':None,'unsupported_meaning':None})
 private.append({'package_id':a['filing']['accession'],'source_summary':s,'source_results':rows})
 counts={'packages':len(packages),'supported_packages':sum(bool(x['metric_pairs']) for x in packages),'unsupported_packages':sum(not x['metric_pairs'] for x in packages),'metric_pairs':sum(len(x['metric_pairs']) for x in packages)}
 if counts!={'packages':11,'supported_packages':3,'unsupported_packages':8,'metric_pairs':7}:raise ValueError('changed frozen audit results require review')
 public={'schema_version':1,'id':'fixed-eleven-original-financial-assertion-audit','status':'SOURCE_REPORTED_ASSERTION_AND_ARITHMETIC_REVIEW_NOT_QUALIFIED_GROWTH','generated_at':dt.datetime.now(dt.timezone.utc).isoformat(),'policy':policy,'policy_sha256':POLICY_SHA,'released_sources':PINS,'counts':counts,'packages':sorted(packages,key=lambda x:x['accession']),'limitations':['This is exhaustive only within the explicitly pinned ten-8K archive plus one VitaSpring XBRL ZIP, not all retained sources, the entire Library or a statistical sample. Local policy chronology is not authenticated preregistration.','Supported source grammar and arithmetic consistency do not establish accounting truth, exact comparability, novelty, earnings quality, future returns or current profitability.','Displayed precision is preserved. No actual unrounded value, inferred rounding rule, margin, share count, diluted EPS or GAAP metric substitution is invented.','Reported-increase consistency and endpoint-display arithmetic are different checks. A mismatch can require reconciliation without establishing source error.','Negative or zero baselines abstain from percentage growth. First-public, decision-time availability, security identity and outcome qualification remain unknown.','All old source artifacts, parsers, reports, scanner/queue memberships and trading safeguards remain unchanged. No provider request or order is made.'],'next_action':'Open the exact issuer source context, reconcile precision and period/metric definitions, and review underlying statements before interpreting the assertions.','qualified_growth_count':0,'qualified_outcomes':0,'provider_requests_made':False,'training_ready':False,'execution_ready':False}
 return public,private

def save(root,archive,vita_config,policy_path,out):
 out=Path(out).resolve()
 if out.exists() or not out.parent.is_dir() or out.is_relative_to(Path(__file__).resolve().parents[1]):raise ValueError('new private output required')
 out.mkdir(mode=0o700);write_private(out/'INCOMPLETE',{});public,private=build(root,archive,vita_config,policy_path);write_private(out/'evidence.json',private);write_private(out/'finding.json',public);write_private(out/'COMPLETE.json',{'evidence_sha256':sha(out/'evidence.json'),'finding_sha256':sha(out/'finding.json')});(out/'INCOMPLETE').unlink();return public
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',default=str(Path(__file__).resolve().parents[1]));p.add_argument('--archive',required=True);p.add_argument('--vita-config',required=True);p.add_argument('--policy',required=True);p.add_argument('--out',required=True);a=p.parse_args()
 with Path(a.vita_config).open('rb') as f:raw=f.read(20001)
 if len(raw)>20000:raise ValueError('config bound')
 print(json.dumps(save(a.root,a.archive,strict(raw),a.policy,a.out)['counts']))
