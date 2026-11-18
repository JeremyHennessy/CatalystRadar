import copy,json,tempfile,unittest
from pathlib import Path
import insider_full_review as m
import test_insider_review_cards as fixtures

class FullReviewTests(unittest.TestCase):
 def get(self,root):return fixtures.ReviewCardTests().fixture(root)[:2]
 def test_real_logic_synthetic_rows_privacy_and_limits(self):
  with tempfile.TemporaryDirectory() as td:
   rows,subs=self.get(Path(td));cards,q,counts=m.project_all('2026q3',rows,subs)
   self.assertEqual(counts['selected_transaction_rows'],1);self.assertEqual(q,[])
   c=cards[0];self.assertEqual(set(c),set(m.CARD_FIELDS)|{'source_transaction_bundle_sha256'})
   self.assertEqual(c['diagnostic_row_counts']['PURCHASE_SALE_DIRECTION_CONTRADICTION'],1)
   self.assertFalse(c['training_ready']);self.assertFalse(c['execution_ready']);self.assertFalse(c['original_reviewed'])
   for s in ['Private owner context','2.50','1.25','TRANS_PRICEPERSHARE','FOOTNOTE_TXT','transaction_fields_as_filed','source_transaction_rowids']:self.assertNotIn(s,json.dumps(c))
   index,p=m.package(cards,q,[{'counts':counts}]);self.assertEqual(index['counts']['all_selected_transaction_rows'],1);self.assertEqual(len(p),257)
   for pin in index['detail_shards']:
    self.assertEqual(m.digest(p[pin['path']]),pin['sha256']);self.assertEqual(len(p[pin['path']]),pin['byte_count'])
   self.assertEqual(m.package(cards,q,[{'counts':counts}]),(index,p))
 def test_whole_filing_quarantine_and_no_malformed_value_echo(self):
  with tempfile.TemporaryDirectory() as td:
   rows,subs=self.get(Path(td))
   for field,value in [('ISSUERCIK','BAD_PRIVATE_VALUE'),('DOCUMENT_TYPE','BAD_PRIVATE_VALUE'),('FILING_DATE','BAD_PRIVATE_VALUE')]:
    rr=copy.deepcopy(rows);ss=copy.deepcopy(subs);rr[0]['submission_as_filed'][field]=value;ss[rr[0]['accession']][field]=value
    cards,q,c=m.project_all('2026q3',rr,ss);self.assertFalse(cards);self.assertEqual(c['quarantined_rows'],1);self.assertEqual(q[0]['selected_transaction_rows'],1);self.assertNotIn(value,json.dumps(q))
    idx,_=m.package(cards,q,[{'counts':c}]);self.assertEqual(idx['counts']['all_selected_transaction_rows'],1)
 def test_duplicate_and_cross_batch_identity_fail_closed(self):
  with tempfile.TemporaryDirectory() as td:
   rows,subs=self.get(Path(td))
   with self.assertRaises(ValueError):m.project_all('2026q3',rows+rows,subs)
   cards,q,c=m.project_all('2026q3',rows,subs)
   with self.assertRaises(ValueError):m.package(cards+cards,q,[{'counts':c}])
   second=copy.deepcopy(cards[0]);second['batch_id']='2026q2'
   with self.assertRaises(ValueError):m.package(cards+[second],q,[{'counts':c}])
 def test_non_ps_not_selected_and_date_unknown_retained(self):
  with tempfile.TemporaryDirectory() as td:
   rows,subs=self.get(Path(td));rows[0]['transaction_fields_as_filed']['TRANS_DATE']=''
   cards,_,_=m.project_all('2026q3',rows,subs);self.assertEqual(cards[0]['invalid_transaction_date_rows'],1);self.assertIsNone(cards[0]['transaction_date_min'])
   rows[0]['transaction_fields_as_filed']['TRANS_CODE']='G';cards,q,c=m.project_all('2026q3',rows,subs);self.assertEqual(c['selected_transaction_rows'],0)
 def test_conservation_and_byte_bounds(self):
  with tempfile.TemporaryDirectory() as td:
   rows,subs=self.get(Path(td));cards,q,c=m.project_all('2026q3',rows,subs)
   with self.assertRaises(ValueError):m.package(cards,q,[{'counts':{'selected_transaction_rows':2}}])
   old=m.LIMITS['shard_bytes'];m.LIMITS['shard_bytes']=1
   try:
    with self.assertRaises(ValueError):m.package(cards,q,[{'counts':c}])
   finally:m.LIMITS['shard_bytes']=old
 def test_row_bundle_order_independent_but_bound(self):
  with tempfile.TemporaryDirectory() as td:
   rows,subs=self.get(Path(td));b=copy.deepcopy(rows[0]);b['source_rowid']+=1;b['transaction_key']='987';rr=rows+[b]
   self.assertEqual(m.row_bundle(rr),m.row_bundle(rr[::-1]));b['source_row_sha256']='f'*64;self.assertNotEqual(m.row_bundle(rows+[b]),m.row_bundle(rows))

 def test_malformed_accession_never_echoed(self):
  with tempfile.TemporaryDirectory() as td:
   rows,subs=self.get(Path(td));rows[0]['accession']='PRIVATE_SECRET_IN_MALFORMED_ACCESSION'
   cards,q,c=m.project_all('2026q3',rows,subs)
   self.assertFalse(cards);self.assertIsNone(q[0]['accession']);self.assertNotIn('PRIVATE_SECRET',json.dumps(q));self.assertEqual(len(q[0]['quarantine_id']),64)
   idx,_=m.package(cards,q,[{'counts':c}]);self.assertEqual(idx['counts']['all_selected_transaction_rows'],1)

 def test_released_static_package_integrity_membership_and_conservation(self):
  root=Path(__file__).resolve().parents[1];idx=json.loads((root/m.BASE/'index.json').read_text());self.assertEqual(len(idx['detail_shards']),256)
  directory={x['issuer_cik']:x for x in idx['issuers']};self.assertEqual(len(directory),len(idx['issuers']));seen=set();accessions=set();total=0
  for pin in idx['detail_shards']:
   self.assertEqual(pin['path'],m.BASE+'details/'+pin['bucket']+'.json');raw=(root/pin['path']).read_bytes();self.assertEqual(len(raw),pin['byte_count']);self.assertEqual(m.digest(raw),pin['sha256'])
   shard=json.loads(raw);self.assertEqual(shard['bucket'],pin['bucket']);self.assertEqual([i['issuer_cik'] for i in shard['issuers']],pin['issuer_ciks'])
   for issuer in shard['issuers']:
    c=issuer['issuer_cik'];self.assertNotIn(c,seen);seen.add(c);self.assertEqual(m.bucket(c),pin['bucket']);d=directory[c];self.assertEqual(len(issuer['filings']),d['filings']);self.assertEqual(sum(f['selected_transaction_rows'] for f in issuer['filings']),d['selected_transaction_rows'])
    for f in issuer['filings']:
     self.assertEqual(f['issuer_cik'],c);self.assertEqual(set(f),set(m.CARD_FIELDS)|{'source_transaction_bundle_sha256'});self.assertNotIn(f['accession'],accessions);accessions.add(f['accession']);total+=f['selected_transaction_rows']
     for key in ['training_ready','execution_ready','original_reviewed']:self.assertIs(f[key],False)
     self.assertIsNone(f['first_public_utc']);self.assertIsNone(f['decision_utc'])
  self.assertEqual(seen,set(directory));self.assertEqual(total,idx['counts']['selected_transaction_rows']);self.assertEqual(len(accessions),idx['counts']['filings']);self.assertEqual(total+sum(q['selected_transaction_rows'] for q in idx['quarantine']),sum(s['counts']['selected_transaction_rows'] for s in idx['sources']))
