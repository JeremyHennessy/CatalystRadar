import unittest,tempfile
from pathlib import Path
from unittest.mock import patch
import shareholder_vote_research as m
HEAD='Votes For Votes Against Abstentions Broker Non-Votes '
def table(values='100 20 3 0'):return ('<table><tr><td>'+HEAD+values+'</td></tr></table>').encode()
def package(body,item=True,kind='8-K'):
 return b'<SEC-HEADER>\n'+(b'ITEM INFORMATION:\t'+m.ITEM+b'\n' if item else b'')+b'</SEC-HEADER>\n<DOCUMENT>\n<TYPE>'+kind.encode()+b'\n<FILENAME>vote.htm\n<TEXT>'+body+b'</TEXT></DOCUMENT>'
class VoteTests(unittest.TestCase):
 def test_exact_counts_no_ratio(self):
  r=m.screen(package(table('1,000 200 30 0')));self.assertEqual(len(r['tables']),1);t=r['tables'][0];self.assertEqual(list(t['values'].values()),['1000','200','30','0']);self.assertIsNone(t['proposal_identity']);self.assertIsNone(t['approval_percentage']);self.assertFalse(t['approval_inferred_from_counts'])
 def test_unsupported_not_zero(self):
  for s in ['Director Name '+HEAD+'Some Person 1 2 3 4',HEAD+'1 2 3',HEAD+'1 2 3 4 5',HEAD+'1,00 2 3 4',HEAD+'-1 2 3 4',HEAD+'NaN 2 3 4']:
   self.assertIsNone(m.table_values(('<table>'+s+'</table>').encode()))
  r=m.screen(package(b'<table>Director Name '+HEAD.encode()+b'Example 1 2 3 4</table>'));self.assertEqual(r['unsupported_vote_tables'],1);self.assertEqual(r['tables'],[])
 def test_amendment_and_header_absence(self):
  self.assertEqual(m.screen(package(table(),kind='8-K/A'))['tables'],[])
  r=m.screen(package(table(),item=False));self.assertIn('NOT_NO_VOTE',r['status']);self.assertEqual(r['tables'],[])
 def test_duplicate_tables_remain_distinct(self):
  r=m.screen(package(table()+table()));self.assertEqual(len(r['tables']),2);self.assertNotEqual(r['tables'][0]['source_span']['byte_start'],r['tables'][1]['source_span']['byte_start'])
 def test_unsafe_and_oversized_table(self):
  for b in [b'<table><table>'+HEAD.encode()+b'1 2 3 4</table></table>',b'<table>'+b'x'*20001+b'</table>']:
   with self.assertRaises(ValueError):m.table_values(b)
  self.assertIsNone(m.table_values(b'<table><script>'+HEAD.encode()+b'1 2 3 4</script></table>'))
 def test_hidden_whole_tables_excluded(self):
  for a,b in [(b'<!--',b'-->'),(b'<script>',b'</script>'),(b'<style>',b'</style>')]:self.assertEqual(m.screen(package(a+table()+b))['tables'],[])
 def test_pin_and_completion(self):
  with self.assertRaises(ValueError):m.reviewed_plan(b'not pinned',{})
  with tempfile.TemporaryDirectory() as t:
   out=Path(t)/'result'
   with patch.object(m,'build',side_effect=ValueError('pin')):
    with self.assertRaises(ValueError):m.save('bad',out)
   self.assertTrue((out/'INCOMPLETE').exists());self.assertFalse((out/'COMPLETE.json').exists())
if __name__=='__main__':unittest.main()
