import hashlib,unittest
from event_document_links import relate

SENTENCE=b'The full text of the press release and the presentation issued in connection with Investor Day 2026 are furnished as Exhibit 99.1 and Exhibit 99.2, respectively, to this Current Report on Form 8-K.'
def doc(typ,name,body):return b'<DOCUMENT>\n<TYPE>'+typ+b'\n<FILENAME>'+name+b'\n<TEXT>'+body+b'</TEXT></DOCUMENT>'
def fixture(text=SENTENCE):return doc(b'8-K',b'main.htm',b'<div>'+text+b'</div>')+doc(b'EX-99.1',b'release.htm',b'release')+doc(b'EX-99.2',b'slides.htm',b'slides')
class EventLinksTests(unittest.TestCase):
 def test_explicit_bundle_not_full_event_group(self):
  r=relate(fixture(),'1','acc');b=r['bundles'][0]
  self.assertEqual(r['status'],'EXPLICIT_SAME_EVENT_EXHIBIT_BUNDLE');self.assertEqual(len(b['linked_documents']),2)
  self.assertFalse(r['global_event_group_complete']);self.assertFalse(r['cross_filing_dedup_verified'])
  self.assertIsNone(b['economic_event_date']);self.assertIsNone(b['independent_sample_count'])
 def test_evidence_hashes_offsets(self):
  raw=fixture();b=relate(raw,'1','a')['bundles'][0]
  for s in [b['relationship_evidence_span'],b['primary_document']]+b['linked_documents']:
   self.assertEqual(s['sha256'],hashlib.sha256(raw[s['byte_start']:s['byte_end']]).hexdigest())
 def test_similar_titles_without_explicit_link_not_grouped(self):
  self.assertEqual(relate(fixture(b'Investor Day 2026 Exhibit99.1 Exhibit99.2'),'1','a')['bundles'],[])
 def test_missing_or_duplicate_exhibit_held(self):
  for raw in [fixture().replace(b'EX-99.2',b'EX-99.3'),fixture()+doc(b'EX-99.1',b'other.htm',b'other')]:
   self.assertEqual(relate(raw,'1','a')['status'],'LINKED_EXHIBIT_MISSING_OR_DUPLICATED')
 def test_duplicate_primary_held(self):
  raw=fixture()+doc(b'8-K',b'other.htm',b'<div>'+SENTENCE+b'</div>')
  self.assertEqual(relate(raw,'1','a')['status'],'PRIMARY_FORM_MISSING_AMENDED_OR_AMBIGUOUS')
 def test_amendment_never_replaces_event(self):
  self.assertEqual(relate(fixture().replace(b'<TYPE>8-K\n',b'<TYPE>8-K/A\n'),'1','a')['bundles'],[])
 def test_hidden_and_duplicate_link_held(self):
  for start,end in [(b'<!--',b'-->'),(b'<script>',b'</script>'),(b'<style>',b'</style>')]:
   self.assertEqual(relate(fixture(start+SENTENCE+end),'1','a')['bundles'],[])
  self.assertEqual(relate(fixture(SENTENCE+SENTENCE),'1','a')['status'],'AMBIGUOUS_MULTIPLE_PRIMARY_LINKS')
 def test_link_only_in_exhibit_not_primary(self):
  raw=fixture(b'no link')+doc(b'EX-99.3',b'other.htm',b'<div>'+SENTENCE+b'</div>')
  self.assertEqual(relate(raw,'1','a')['bundles'],[])
 def test_filename_collision_held(self):
  self.assertEqual(relate(fixture().replace(b'slides.htm',b'release.htm'),'1','a')['status'],'LINKED_EXHIBIT_FILENAME_CONFLICT')
 def test_accession_scope_not_cross_filing(self):
  self.assertNotEqual(relate(fixture(),'1','a')['bundles'][0]['bundle_id'],relate(fixture(),'1','b')['bundles'][0]['bundle_id'])

 def test_malformed_duplicate_not_silently_discarded(self):
  extra=doc(b'EX-99.1',b'other.htm',b'other').replace(b'<FILENAME>',b'<TYPE>EX-99.1\n<FILENAME>')
  r=relate(fixture()+extra,'1','a');self.assertEqual(r['status'],'MALFORMED_DOCUMENT_INVENTORY');self.assertEqual(r['malformed_documents'],1)
 def test_body_metadata_tags_not_header(self):
  raw=fixture().replace(b'>slides</TEXT>',b'>slides\n<TYPE>EX-99.3\n<FILENAME>inbody.htm\n</TEXT>')
  self.assertEqual(relate(raw,'1','a')['status'],'EXPLICIT_SAME_EVENT_EXHIBIT_BUNDLE')
