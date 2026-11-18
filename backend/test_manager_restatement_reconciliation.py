import copy,csv,io,json,sqlite3,tempfile,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
import manager_restatement_reconciliation as m
ROOT=Path(__file__).resolve().parents[1];A='0000000001-26-000001';B='0000000001-26-000002'
def info(a=A,k='1',value='10',n=1):
 d=dict.fromkeys(m.SCHEMAS['INFOTABLE.tsv'],'');d.update(ACCESSION_NUMBER=a,INFOTABLE_SK=k,NAMEOFISSUER='Private issuer',CUSIP='123456789',VALUE=value);return m.rawrow(d,n)
def fixture():
 t={k:[] for k in m.TOTALS}
 for n,(a,form,date,amend) in enumerate([(A,'13F-HR','01-JUL-2026','N'),(B,'13F-HR/A','02-JUL-2026','Y')],1):
  s={'ACCESSION_NUMBER':a,'SUBMISSIONTYPE':form,'FILING_DATE':date,'CIK':'1','PERIODOFREPORT':'30-JUN-2026'}
  c=dict.fromkeys(m.SCHEMAS['COVERPAGE.tsv'],'');c.update(ACCESSION_NUMBER=a,REPORTCALENDARORQUARTER='30-JUN-2026',ISAMENDMENT=amend,AMENDMENTNO='1' if amend=='Y' else '',AMENDMENTTYPE='RESTATEMENT' if amend=='Y' else '',REPORTTYPE='13F HOLDINGS REPORT')
  z=dict.fromkeys(m.SCHEMAS['SUMMARYPAGE.tsv'],'');z.update(ACCESSION_NUMBER=a,TABLEENTRYTOTAL='2',ISCONFIDENTIALOMITTED='')
  for key,d in [('SUBMISSION',s),('COVERPAGE',c),('SUMMARYPAGE',z)]:t[key].append(m.rawrow(d,n))
 return t
class ReconciliationTests(unittest.TestCase):
 def test_exact_multiset_preserves_duplicate_multiplicity(self):
  l=[info(k='1'),info(k='2',n=2),info(k='3',value='20',n=3)];r=[info(B,'4'),info(B,'5',value='30',n=5)]
  x,p=m.multiset(l,r);self.assertEqual(x,{'original_source_rows':3,'amendment_source_rows':2,'exact_matched_row_multiplicity':1,'original_unmatched_row_multiplicity':2,'amendment_unmatched_row_multiplicity':1});self.assertEqual(sum(q['exact_matched_multiplicity'] for q in p),1)
 def test_no_numeric_normalization_or_unique_security_matching(self):
  x,_=m.multiset([info(value='10')],[info(B,value='10.0')]);self.assertEqual(x['exact_matched_row_multiplicity'],0)
  a=info();b=info(B);b['fields']['TITLEOFCLASS']='different';self.assertEqual(m.multiset([a],[b])[0]['exact_matched_row_multiplicity'],0)
  self.assertEqual(len(m.FIELDS),13);self.assertNotIn('ACCESSION_NUMBER',m.FIELDS);self.assertNotIn('INFOTABLE_SK',m.FIELDS)
 def test_fixed_selection_and_each_exclusion(self):
  t=fixture();c,p,n,*_=m.choose(t);self.assertEqual((len(c),len(p)),(1,1))
  for table,field,value,reason in [('SUBMISSION','FILING_DATE','01-JUL-2026','ORIGINAL_FILING_DATE_NOT_STRICTLY_EARLIER'),('COVERPAGE','REPORTTYPE','13F COMBINATION REPORT','NOT_BOTH_HOLDINGS_REPORT'),('COVERPAGE','REPORTCALENDARORQUARTER','31-MAR-2026','COVER_SUB_PERIOD_MISMATCH')]:
   t=fixture();t[table][1]['fields'][field]=value;c,p,*_=m.choose(t);self.assertEqual(p,[]);self.assertIn(reason,c[0]['exclusion_reasons'])
  t=fixture();t['COVERPAGE'][1]['fields']['AMENDMENTNO']='2';c,p,n,*_=m.choose(t);self.assertEqual(c,[]);self.assertEqual(n['pre_candidate_exclusion_counts']['NOT_EXPLICIT_ORIGINAL_AND_FIRST_RESTATEMENT'],1)
 def test_identity_duplicates_and_missing_join_fail(self):
  for label in m.TOTALS:
   t=fixture();t[label].append(copy.deepcopy(t[label][0]))
   with self.assertRaises(ValueError):m.choose(t)
  t=fixture();t['SUBMISSION'][0]['fields']['CIK']='bad'
  with self.assertRaises(ValueError):m.choose(t)
  t=fixture();t['COVERPAGE'].pop()
  with self.assertRaises(ValueError):m.choose(t)
 def test_confidential_unknown_and_zero_rows_not_zero_portfolio(self):
  _,_,_,s,c,z=m.choose(fixture());r=m.filing(A,s,c,z,0);self.assertEqual(r['confidential_omitted_as_reported'],'UNKNOWN_BLANK_AS_REPORTED');self.assertEqual(r['info_presence'],'NO_SOURCE_ROWS_NOT_VERIFIED_ZERO_HOLDINGS');self.assertFalse(r['summary_count_matches_retained_rows'])
  r=m.filing(A,s,c,{},0);self.assertFalse(r['summary_present']);self.assertIsNone(r['summary_count_matches_retained_rows']);self.assertEqual(m.flag('private text'),'UNKNOWN_REDACTED')
 def test_full_selected_source_correspondence_and_mismatch(self):
  from sec_13f_data import MEMBERS
  with tempfile.TemporaryDirectory() as td:
   a=Path(td)/'a.zip';d=Path(td)/'db';t=fixture();t['INFOTABLE']=[info(A,'1',n=1),info(A,'2',n=2),info(B,'3',n=3)]
   with sqlite3.connect(d) as db,zipfile.ZipFile(a,'w') as z:
    for member in MEMBERS:
     label=member.split('.')[0]
     if label not in t:z.writestr(member,b'');continue
     fields=m.SCHEMAS[member];buf=io.StringIO();w=csv.writer(buf,delimiter='\t',lineterminator='\n');w.writerow(fields);db.execute('create table holdings_'+label.lower()+' ('+','.join('"'+k+'" TEXT' for k in fields)+')')
     for r in t[label]:
      v=[r['fields'][f] for f in fields];w.writerow(v);db.execute('insert into holdings_'+label.lower()+' values ('+','.join('?' for f in fields)+')',v)
     z.writestr(member,buf.getvalue())
   with patch.object(m,'ZIP_BYTES',a.stat().st_size),patch.object(m,'ZIP_SHA',m.sha(a)),patch.object(m,'DB_SHA',m.sha(d)),patch.object(m,'TOTALS',dict.fromkeys(m.TOTALS,2)),patch.object(m,'INFO_TOTAL',3):
    c,p,n,s,cover,summ,ii,pins=m.verify(a,d);self.assertEqual(len(p),1);self.assertEqual(len(ii[A]),2);self.assertEqual(ii[B][0],t['INFOTABLE'][2])
   with sqlite3.connect(d) as db:db.execute("update holdings_infotable set VALUE='changed' where INFOTABLE_SK='3'")
   with patch.object(m,'ZIP_BYTES',a.stat().st_size),patch.object(m,'ZIP_SHA',m.sha(a)),patch.object(m,'DB_SHA',m.sha(d)),patch.object(m,'TOTALS',dict.fromkeys(m.TOTALS,2)),patch.object(m,'INFO_TOTAL',3):
    with self.assertRaisesRegex(ValueError,'correspondence'):m.verify(a,d)
 def test_source_pin_and_failed_completion(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'bad';p.write_bytes(b'bad')
   with self.assertRaises(ValueError):m.verify(p,p)
   out=Path(td)/'fail'
   with self.assertRaises(ValueError):m.save(p,p,p,out)
   self.assertTrue((out/'INCOMPLETE').exists());self.assertFalse((out/'reconciliation.json').exists());self.assertFalse((out/'COMPLETE.json').exists())
   out=Path(td)/'done'
   with patch.object(m,'build',return_value=({'safe':True},[])):m.save(p,p,p,out)
   self.assertEqual(out.stat().st_mode&511,448);self.assertEqual((out/'reconciliation.json').stat().st_mode&511,384)
 def test_public_actual_counts_conservation_and_privacy(self):
  d=json.loads((ROOT/'web/manager-restatement-reconciliation.json').read_bytes());self.assertEqual(len(d['candidate_groups']),36);self.assertEqual(len(d['pairs']),32);self.assertEqual(d['counts']['pairs_both_omitted_flags_explicit_N'],7);self.assertEqual(d['counts']['selected_INFO_rows'],14640)
  self.assertEqual(d['policy_sha256'],m.digest(m.canonical(m.POLICY)))
  for p in d['pairs']:
   r=p['reconciliation'];self.assertEqual(r['exact_matched_row_multiplicity']+r['original_unmatched_row_multiplicity'],r['original_source_rows']);self.assertEqual(r['exact_matched_row_multiplicity']+r['amendment_unmatched_row_multiplicity'],r['amendment_source_rows']);self.assertFalse(p['complete_holdings_verified']);self.assertFalse(p['supersession_verified']);self.assertEqual(set(r),{'original_source_rows','amendment_source_rows','exact_matched_row_multiplicity','original_unmatched_row_multiplicity','amendment_unmatched_row_multiplicity'})
  first=next(p for p in d['pairs'] if p['manager_cik']=='0000765443');self.assertEqual(first['reconciliation'],{'original_source_rows':340,'amendment_source_rows':340,'exact_matched_row_multiplicity':282,'original_unmatched_row_multiplicity':58,'amendment_unmatched_row_multiplicity':58})
  self.assertNotIn('comparison_fields',d['pairs'][0]);self.assertNotIn('Private issuer',json.dumps(d))
if __name__=='__main__':unittest.main()
