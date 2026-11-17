"""Synthetic responses using documented example identifiers, not training examples."""
import copy,json,tempfile,unittest
from pathlib import Path
from openfigi_evidence import validate,figi_valid,read_pinned,digest,URL,audit

class FigiTests(unittest.TestCase):
    def fixture(self):
        request=[{'idType':'TICKER','idValue':'IBM','exchCode':'US','marketSecDes':'Equity','includeUnlistedEquities':True}]
        row={'figi':'BBG000BLNNH6','name':'Synthetic issuer','ticker':'IBM','exchCode':'US','compositeFIGI':'BBG000BLNNH6','securityType':'Common Stock','marketSector':'Equity','shareClassFIGI':'BBG001S5S399','securityType2':'Common Stock','securityDescription':'Synthetic'}
        response=[{'data':[row]}]
        receipt={'source_url':URL,'method':'POST','authentication':'NONE','request_sha256':'a'*64,'requested_at':'2026-11-17T00:00:00+00:00','http_status':200,'response_sha256':'b'*64,'response_bytes':10,'status':'RETAINED_NOT_YET_VALIDATED','headers':{'Content-Type':'application/json','Date':None,'ratelimit-limit':None,'ratelimit-remaining':None,'ratelimit-reset':None},'finished_at':'2026-11-17T00:00:01+00:00'}
        return request,response,receipt,'a'*64,'b'*64
    def test_identifier_checksum(self):
        self.assertTrue(figi_valid('BBG000BLNNH6'));self.assertTrue(figi_valid('BBG000BLNQ16'))
        for bad in ['BBG000BLNNH7','BBG000BLNAH6','invalid',None]:self.assertFalse(figi_valid(bad))
    def test_one_current_candidate_not_verified_link(self):
        rows,counts,shared=validate(*self.fixture());self.assertEqual(counts,{'SINGLE_CURRENT_CANDIDATE':1});self.assertEqual(shared,0)
        self.assertFalse(rows[0]['issuer_cik_link_verified']);self.assertFalse(rows[0]['historical_ticker_ownership_verified']);self.assertFalse(rows[0]['active_listing_verified'])
        self.assertNotIn('name',str(rows));self.assertNotIn('Synthetic',str(rows))
    def test_ambiguity_preserved(self):
        args=self.fixture();other=dict(args[1][0]['data'][0],figi='BBG000BLNQ16');args[1][0]['data'].append(other)
        rows,counts,_=validate(*args);self.assertEqual(counts,{'AMBIGUOUS_CURRENT_CANDIDATES':1});self.assertEqual(len(rows[0]['candidates']),2)
    def test_errors_and_no_results(self):
        for result,reason in [({'warning':'No identifier found'},'NO_MAPPING_WARNING'),({'error':'No data'},'PROVIDER_ERROR'),({'data':[]},'NO_MAPPING_RETURNED')]:
            args=self.fixture();args[1][0]=result;self.assertEqual(validate(*args)[1],{reason:1})
    def test_misalignment_duplicates_and_schema_reject(self):
        for change in ['ticker','exchCode','marketSector','figi','extra','duplicate']:
            args=self.fixture();row=args[1][0]['data'][0]
            if change=='extra':row['secret']='unexpected'
            elif change=='duplicate':args[1][0]['data'].append(copy.deepcopy(row))
            else:row[change]='wrong'
            with self.subTest(change=change),self.assertRaises(ValueError):validate(*args)
        args=self.fixture();args[1].clear()
        with self.assertRaises(ValueError):validate(*args)
    def test_clock_hash_and_scope_fail_closed(self):
        for key,value in [('http_status',403),('authentication','KEY'),('finished_at','2026-11-16T00:00:00+00:00'),('finished_at','2099-01-01T00:00:00+00:00'),('request_sha256','0'*64)]:
            args=self.fixture();args[2][key]=value
            with self.assertRaises(ValueError):validate(*args)
        args=self.fixture();args[0][0]['includeUnlistedEquities']=False
        with self.assertRaises(ValueError):validate(*args)
    def test_pinned_bytes_and_strict_json(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'input'
            for raw in [b'{"a":1,"a":2}',b'{"unused":NaN}',b'{"a":Infinity}']:
                p.write_bytes(raw)
                with self.assertRaises(ValueError):read_pinned(p,digest(raw),100)
            p.write_bytes(b'{}')
            with self.assertRaises(ValueError):read_pinned(p,'0'*64,100)
            with self.assertRaises(ValueError):read_pinned(p,digest(b'{}'),1)
    def test_complete_file_audit(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);request,response,receipt,_,_=self.fixture();a=json.dumps(request).encode();b=json.dumps(response).encode()
            receipt.update(request_sha256=digest(a),response_sha256=digest(b),response_bytes=len(b));c=json.dumps(receipt).encode()
            for name,raw in [('request',a),('response',b),('receipt',c)]:(root/name).write_bytes(raw)
            summary,private=audit(root/'request',digest(a),root/'response',digest(b),root/'receipt',digest(c))
            self.assertEqual(summary['candidate_count'],1);self.assertEqual(private['response'],response);self.assertFalse(summary['training_ready'])
