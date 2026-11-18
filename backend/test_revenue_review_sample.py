import copy,json,sqlite3,tempfile,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
import revenue_review_sample as m
from financial_pair_candidates import audit as pair_audit
from sec_prepared_data import MEMBERS
class RevenueReviewSampleTests(unittest.TestCase):
 def pair(self,cik=1,accession='a',filed='20260801',rowid=1):
  accession=f'{int(cik):010d}-26-{sum(map(ord,accession)):06d}'
  n=dict(rowid=rowid,adsh=accession,tag='Revenues',version='us-gaap/2026',ddate='20260630',qtrs='1',uom='USD',segments='',coreg='',value='0.0000',footnote='')
  return dict(issuer_cik_as_filed=str(cik),accession=accession,filing_date_as_filed=filed,submission_period='20260630',current=n,prior=dict(n,rowid=rowid+1,ddate='20250630',value='12.3000'))
 def test_selection_no_values_and_normalized_exclusion(self):
  pairs=[self.pair(cik=i,accession=str(i)) for i in range(1,9)];pairs.append(self.pair(2,'later','20260901',50))
  chosen,counts=m.select({'q3':pairs},{'0000000001'})
  self.assertEqual(['0000000002','0000000003','0000000004','0000000005','0000000006'],[x[0] for x in chosen]);self.assertEqual('0000000002-26-000536',chosen[0][2]['accession']);self.assertEqual(1,counts['excluded_existing_queue_pairs'])
  changed=copy.deepcopy(pairs)
  for p in changed:p['current']['value']='-999999999999'
  self.assertEqual([(c,b,p['accession']) for c,b,p,a in chosen],[(c,b,p['accession']) for c,b,p,a in m.select({'q3':changed},{'0000000001'})[0]])
 def test_complete_ties_duplicate_and_no_replacement(self):
  pairs=[self.pair(i,str(i)) for i in range(1,6)];pairs.append(self.pair(1,'1',rowid=20))
  self.assertEqual(1,m.select({'q3':list(reversed(pairs))},set())[0][0][2]['current']['rowid'])
  with self.assertRaises(ValueError):m.select({'q3':pairs+[pairs[0]]},set())
  with self.assertRaises(ValueError):m.select({'q3':pairs},{'0000000002'})
 def test_other_metrics_excluded(self):
  pairs=[self.pair(i,str(i)) for i in range(1,7)];pairs[-1]['current']['tag']='NetIncomeLoss'
  self.assertEqual(1,m.select({'q3':pairs},set())[1]['excluded_other_metric_pairs'])
 def fixture(self,root):
  tables={k:[] for k in ('sub.txt','num.txt','tag.txt','pre.txt')}
  def row(member,**kw):return dict({k:'' for k in m.SCHEMAS[member]},**kw)
  tables['tag.txt']=[row('tag.txt',tag='Revenues',version='us-gaap/2026',custom='0',abstract='0',datatype='monetary',iord='D',doc='UNPUBLISHED TAXONOMY TEXT')]
  for i in range(1,6):
   acc=f'000000{i:04d}-26-000001'
   tables['sub.txt'].append(row('sub.txt',adsh=acc,cik=str(i),name='SYNTHETIC '+str(i),form='10-Q/A' if i==1 else '10-Q',period='20260630',fp='Q2',fy='2026',filed='20260801',accepted='2026-08-01 16:00:00.0',bas1='PRIVATE ADDRESS'))
   for date,value in [('20260630','0.0000'),('20250630','12.3000')]:tables['num.txt'].append(row('num.txt',adsh=acc,tag='Revenues',version='us-gaap/2026',ddate=date,qtrs='1',uom='USD',value=value))
   tables['pre.txt'].append(row('pre.txt',adsh=acc,tag='Revenues',version='us-gaap/2026',inpth='0',stmt='IS',plabel='Revenue'))
  db=root/'source.sqlite';conn=sqlite3.connect(db)
  for member,rows in tables.items():
   fields=m.SCHEMAS[member];table='financial_'+member[:-4];conn.execute('CREATE TABLE '+table+'('+','.join('"'+x+'" TEXT' for x in fields)+')')
   conn.executemany('INSERT INTO '+table+' VALUES('+','.join('?' for x in fields)+')',[tuple(r[x] for x in fields) for r in rows])
  conn.commit();conn.close();archive=root/'source.zip'
  with zipfile.ZipFile(archive,'w') as z:
   for member in MEMBERS['financial']:
    z.writestr(member,'\t'.join(m.SCHEMAS[member])+'\n'+''.join('\t'.join(r[x] for x in m.SCHEMAS[member])+'\n' for r in tables[member]) if member in tables else 'Synthetic readme')
  summary,pairs=pair_audit(db,m.sha(db),archive,m.sha(archive));return db,archive,summary,pairs
 def test_end_to_end_exact_values_privacy_and_raw_disagreement(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);db,archive,summary,pairs=self.fixture(root);package=root/'original.zip';package.write_bytes(b'synthetic')
   receipt={'zip_sha256':m.sha(package),'zip_byte_count':9,'accession':'unmatched'}
   plan={'inputs':{'q3':{'files':{}}},'queue':{},**{k:None for k in ('policy_version','created_at_utc','selection','metrics','issuer_limit','tie_break_fields','duplicate_tie_policy')}}
   with patch.object(m,'inputs',return_value=(plan,{'q3':pairs},{'q3':summary},set())),patch.object(m,'original_screen',return_value={'packages':[],'provenance':{}}),patch.object(m,'read_pinned',return_value=(receipt,1)):
    kwargs=dict(root=root,workspace=root,plan_path='unused',plan_sha='a'*64,databases={'q3_2026_filing_batch':str(db)},archives={'q3_2026_filing_batch':str(archive)},original_zip='unused',original_receipt='unused',original_package=package)
    result=m.audit(**kwargs);self.assertEqual(5,len(result['packets']));p=result['packets'][0];self.assertTrue(p['amendment_as_filed']);self.assertEqual('0.0000',p['facts'][0]['value_as_reported']);self.assertEqual('12.3000',p['facts'][1]['value_as_reported']);self.assertIsNone(p['percentage_change']);self.assertFalse(p['comparability_verified']);self.assertNotIn('PRIVATE ADDRESS',json.dumps(result));self.assertNotIn('UNPUBLISHED TAXONOMY TEXT',json.dumps(result))
    dest=root/'completed';m.run(dest,**kwargs);self.assertFalse((dest/'INCOMPLETE').exists());self.assertEqual(m.sha(dest/'review.json'),json.loads((dest/'COMPLETE.json').read_text())['review_sha256'])
    # Rewrite raw NUM but retain DB; updated archive pin must still fail field correspondence.
    with zipfile.ZipFile(archive) as z:contents={n:z.read(n) for n in z.namelist()}
    contents['num.txt']=contents['num.txt'].replace(b'12.3000',b'13.3000')
    with zipfile.ZipFile(archive,'w') as z:
     for name,raw in contents.items():z.writestr(name,raw)
    summary['source_archive_sha256']=m.sha(archive)
    for pair in pairs:pair['source_archive_sha256']=m.sha(archive)
    with self.assertRaisesRegex(ValueError,'archive/DB disagreement'):m.audit(**kwargs)
 def test_failure_keeps_incomplete(self):
  with tempfile.TemporaryDirectory() as td,patch.object(m,'audit',side_effect=ValueError('rejected')):
   out=Path(td)/'failed'
   with self.assertRaises(ValueError):m.run(out)
   self.assertTrue((out/'INCOMPLETE').exists());self.assertFalse((out/'COMPLETE.json').exists())
 def test_published_scope(self):
  path=Path(__file__).resolve().parents[1]/'web/company-findings/revenue-review-sample.json'
  if not path.exists():self.skipTest('publication copy pending')
  x=json.loads(path.read_bytes());self.assertEqual(5,len(x['packets']));self.assertEqual(40628,x['counts']['input_pairs'])
  for p in x['packets']:
   self.assertIsNone(p['percentage_change']);self.assertIsNone(p['absolute_change']);self.assertFalse(p['comparability_verified']);self.assertFalse(p['original_filing_text_checked']);self.assertEqual(2,len(p['facts']))
if __name__=='__main__':unittest.main()
