from copy import deepcopy
from decimal import Decimal
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET
import treasury_yield_context as t

ROOT=Path(__file__).resolve().parents[1]
RAW=(ROOT/t.BASE/'response.xml').read_bytes()
RECEIPT=(ROOT/t.BASE/'receipt.json').read_bytes()

def fixture(change):
 root=ET.fromstring(RAW);change(root);return ET.tostring(root,encoding='utf-8',xml_declaration=True)
def props(root):return root.find(t.A+'entry').find(t.A+'content').find(t.M+'properties')

class Treasury(unittest.TestCase):
 def test_actual_reproduction_all_fields_and_spreads(self):
  actual=t.build(RAW,RECEIPT)
  self.assertEqual(t.encoded(actual),(ROOT/t.BASE/'rates.json').read_bytes())
  self.assertEqual(actual['counts'],{'source_dates':11,'maturities_per_date':14,'additional_display_fields_per_date':1,'null_rate_cells':0})
  entries=ET.fromstring(RAW).findall(t.A+'entry')
  for entry,record in zip(entries,actual['records']):
   p=entry.find(t.A+'content').find(t.M+'properties')
   self.assertEqual(record['rates_percent_as_reported'],{field:p.find(t.D+field).text for field in t.FIELDS})
   self.assertEqual(record['source_NEW_DATE'],p.find(t.D+'NEW_DATE').text)
  self.assertEqual([Decimal(r['ten_year_minus_two_year_basis_points']) for r in actual['records']],list(map(Decimal,[32,34,32,38,35,32,25,24,27,29,30])))
  self.assertIsNone(actual['first_public_utc']);self.assertFalse(actual['full_month_complete'])
 def test_null_not_zero_and_missing_rejected(self):
  def null(root):
   p=props(root).find(t.D+'BC_2YEAR');p.set(t.M+'null','true');p.text=None
  parsed=t.parse(fixture(null),t.MONTH)['records'][0]
  self.assertIsNone(parsed['rates_percent_as_reported']['BC_2YEAR']);self.assertIsNone(parsed['ten_year_minus_two_year_basis_points'])
  self.assertEqual(parsed['spread_status'],'UNAVAILABLE_SOURCE_NULL')
  with self.assertRaises(ValueError):t.parse(fixture(lambda r:props(r).remove(props(r).find(t.D+'BC_2YEAR'))),t.MONTH)
  with self.assertRaises(ValueError):t.parse(fixture(lambda r:props(r).find(t.D+'BC_2YEAR').set(t.M+'null','true')),t.MONTH)
 def test_duplicate_ids_dates_properties(self):
  def duplicate_id(root):
   es=root.findall(t.A+'entry');es[1].find(t.A+'content').find(t.M+'properties').find(t.D+'Id').text='349'
  def duplicate_date(root):
   es=root.findall(t.A+'entry');es[1].find(t.A+'content').find(t.M+'properties').find(t.D+'NEW_DATE').text='2026-11-02T00:00:00'
  for mutate in (duplicate_id,duplicate_date,lambda r:props(r).append(deepcopy(props(r)[0]))):
   with self.assertRaises(ValueError):t.parse(fixture(mutate),t.MONTH)
 def test_unexpected_namespace_field_type_and_metadata(self):
  for mutate in (lambda r:setattr(props(r)[0],'tag','{evil}Id'),lambda r:ET.SubElement(props(r),t.D+'BC_UNKNOWN'),lambda r:props(r).find(t.D+'BC_2YEAR').set(t.M+'type','Edm.String'),lambda r:setattr(r.find(t.A+'entry').find(t.A+'author').find(t.A+'name'),'text','Unexpected Person')):
   with self.assertRaises(ValueError):t.parse(fixture(mutate),t.MONTH)
 def test_bounded_exact_decimals_and_encoding(self):
  for value in ('NaN','Infinity','1e2','1.00001','100.01','-100.01','',' 4.5 '):
   with self.assertRaises(ValueError):t.parse(fixture(lambda r:setattr(props(r).find(t.D+'BC_2YEAR'),'text',value)),t.MONTH)
  malicious=RAW.decode().replace('<feed','<!DOCTYPE feed [<!ENTITY x "expanded">]><feed',1)
  for encoding in ('utf-8','utf-16','utf-16-le','utf-16-be','utf-32','utf-32-le','utf-32-be'):
   with self.assertRaises((ValueError,UnicodeError)):t.parse(malicious.encode(encoding),t.MONTH)
  with self.assertRaises(ValueError):t.parse(b'x'*(t.MAX_BYTES+1),t.MONTH)
 def test_dates_identity_and_display_preservation(self):
  for date in ('2026-12-01T00:00:00','2026-11-02T12:00:00','2026-11-02T00:00:00Z','2026-11-31T00:00:00'):
   with self.assertRaises(ValueError):t.parse(fixture(lambda r:setattr(props(r).find(t.D+'NEW_DATE'),'text',date)),t.MONTH)
  with self.assertRaises(ValueError):t.parse(fixture(lambda r:setattr(r.find(t.A+'entry').find(t.A+'id'),'text','https://evil.test')),t.MONTH)
  x=t.parse(fixture(lambda r:setattr(props(r).find(t.D+'BC_30YEARDISPLAY'),'text','5.29')),t.MONTH)
  self.assertEqual(x['records'][0]['rates_percent_as_reported']['BC_30YEAR'],'5.28')
  self.assertEqual(x['records'][0]['rates_percent_as_reported']['BC_30YEARDISPLAY'],'5.29')
 def test_pins_and_receipt_validation(self):
  with self.assertRaises(ValueError):t.build(RAW+b' ',RECEIPT)
  with self.assertRaises(ValueError):t.build(RAW,RECEIPT+b' ')
  for key,value in [('url','https://evil.test'),('http_status',403),('redirects_allowed',True),('finish_utc','2026-11-18T17:00:00Z'),('request_utc','2026-11-18T17:00:00Z')]:
   obj=json.loads(RECEIPT);obj[key]=value;raw=t.encoded(obj)
   with patch.object(t,'RECEIPT_SHA',t.sha(raw)):
    with self.assertRaises(ValueError):t.build(RAW,raw)
  duplicate=RECEIPT.decode().replace('{','{"http_status":200,',1).encode()
  with patch.object(t,'RECEIPT_SHA',t.sha(duplicate)):
   with self.assertRaises(ValueError):t.build(RAW,duplicate)
 def test_fail_closed_save_modes_and_completion(self):
  with tempfile.TemporaryDirectory() as temp:
   out=Path(temp)/'ok';t.save(ROOT/t.BASE/'response.xml',ROOT/t.BASE/'receipt.json',out)
   self.assertEqual(os.stat(out).st_mode&0o777,0o700)
   for p in out.iterdir():self.assertEqual(os.stat(p).st_mode&0o777,0o600)
   self.assertFalse((out/'INCOMPLETE').exists());self.assertEqual(json.loads((out/'COMPLETE').read_text())['rates.json']['sha256'],t.sha((out/'rates.json').read_bytes()))
   bad=Path(temp)/'bad'
   with patch.object(t,'RAW_SHA','0'*64):
    with self.assertRaises(ValueError):t.save(ROOT/t.BASE/'response.xml',ROOT/t.BASE/'receipt.json',bad)
   self.assertTrue((bad/'INCOMPLETE').exists());self.assertFalse((bad/'rates.json').exists());self.assertFalse((bad/'COMPLETE').exists())
if __name__=='__main__':unittest.main()
