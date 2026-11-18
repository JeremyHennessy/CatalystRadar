import json
import unittest
from private_response_receipt import classify, receipt, MAX_BYTES

CLOCK = '2026-11-18T15:43:00Z'
SECRET = 'synthetic-do-not-echo-secret'

def candidate():
    return {'Meta Data': {'2. Symbol': 'SYNTH', '3. Last Refreshed': '2026-11-16', '5. Time Zone': 'US/Eastern'},
            'Time Series (Daily)': {'2026-11-16': {k:'1' for k in ['1. open','2. high','3. low','4. close','5. volume']}}}

def run(body, status=200):
    return classify(transport='RESPONSE_RECEIVED', http_status=status, body=body)

class ResponseReceiptTests(unittest.TestCase):
    def test_status_not_body_claim(self):
        for status,expected in [(401,'HTTP_AUTHENTICATION_FAILURE'),(403,'HTTP_ACCESS_DENIED'),(429,'HTTP_RATE_LIMITED'),(302,'HTTP_REDIRECT_RESPONSE'),(500,'HTTP_OTHER_NON200'),(204,'HTTP_OTHER_NON200')]:
            self.assertEqual(run(SECRET.encode(),status),expected)
    def test_provider_reasons_remain_unknown(self):
        for key in ['Information','Note','Error Message']:
            for message in ['premium access','rate limit','invalid API key',SECRET]:
                self.assertEqual(run(json.dumps({key:message}).encode()),'PROVIDER_MESSAGE_REASON_UNRESOLVED')
            data=candidate();data[key]=SECRET
            self.assertEqual(run(json.dumps(data).encode()),'CONFLICTING_PROVIDER_ENVELOPE')
    def test_no_empty_success(self):
        self.assertEqual(run(b''),'EMPTY_RESPONSE_UNQUALIFIED')
        data=candidate();data['Time Series (Daily)']={}
        self.assertEqual(run(json.dumps(data).encode()),'EMPTY_SERIES_UNQUALIFIED')
    def test_duplicates_bad_encoding_nonfinite_and_deep_json(self):
        cases=[b'\xff',b'{',b'{"x":NaN}',b'{"x":Infinity}',b'{"x":1,"x":2}',b'{"x":{"y":1,"y":2}}']
        for raw in cases:self.assertEqual(run(raw),'INVALID_OR_AMBIGUOUS_JSON')
        self.assertIn(run(b'['*2000+b'0'+b']'*2000),('INVALID_OR_AMBIGUOUS_JSON','UNEXPECTED_SCHEMA'))
    def test_bounds(self):
        self.assertEqual(run(b'x'*MAX_BYTES),'RESPONSE_BOUND_REACHED_UNQUALIFIED')
        self.assertEqual(run(b'x'*(MAX_BYTES+1)),'RESPONSE_BOUND_REACHED_UNQUALIFIED')
        data=candidate();data['Time Series (Daily)']={str(i):{} for i in range(101)}
        self.assertEqual(run(json.dumps(data).encode()),'UNEXPECTED_COMPACT_COVERAGE')
    def test_shape_is_not_validation(self):
        data=candidate()
        # Intentionally invalid date/symbol/timezone/OHLCV remains only a candidate;
        # the existing admission validators must reject before any retention.
        data['Meta Data']['5. Time Zone']='not-a-timezone'
        data['Time Series (Daily)']={'not-a-date':{k:SECRET for k in next(iter(data['Time Series (Daily)'].values()))}}
        self.assertEqual(run(json.dumps(data).encode()),'DAILY_RESPONSE_CANDIDATE_NOT_VALIDATED')
        r=receipt(observed_utc=CLOCK,transport='RESPONSE_RECEIVED',http_status=200,body=json.dumps(data).encode())
        self.assertNotIn(SECRET,json.dumps(r))
        for k,v in r.items():
            if k.endswith('_verified') or k.endswith('_ready') or k in ('retry_authorized','collection_enabled'):self.assertIs(v,False)
    def test_malformed_schema(self):
        for data in [None,[],{}, {'Meta Data':{},'Time Series (Daily)':[]},dict(candidate(),extra=SECRET)]:
            self.assertEqual(run(json.dumps(data).encode()),'UNEXPECTED_SCHEMA')
        for path in ['meta','row']:
            data=candidate()
            if path=='meta':data['Meta Data']['2. Symbol']=42
            else:data['Time Series (Daily)']['2026-11-16']={'secret':SECRET}
            self.assertEqual(run(json.dumps(data).encode()),'UNEXPECTED_SCHEMA')
    def test_transport_no_request_guess(self):
        for state,expected in [('NETWORK_FAILURE','NETWORK_FAILURE_REPORTED'),('NOT_ATTEMPTED','NOT_ATTEMPTED_REPORTED'),('UNKNOWN','REQUEST_STATE_UNKNOWN')]:
            self.assertEqual(classify(transport=state),expected)
            with self.assertRaises(ValueError):classify(transport=state,http_status=200,body=b'')
    def test_invalid_inputs_and_clocks(self):
        for status in [True,None,'200',99,600]:
            with self.assertRaises(ValueError):run(b'',status)
        with self.assertRaises(ValueError):classify(transport='SECRET')
        for clock in ['2026-11-18',SECRET,None]:
            with self.assertRaises(ValueError):receipt(observed_utc=clock,transport='UNKNOWN')
        r=receipt(observed_utc='2026-11-18T10:43:00-05:00',transport='UNKNOWN')
        self.assertEqual(r['observed_utc_as_supplied'],'2026-11-18T15:43:00+00:00')
    def test_secret_safe_all_projected_branches(self):
        for body in [SECRET.encode(),json.dumps({'Note':SECRET}).encode(),json.dumps({SECRET:1, 'x':2}).encode(),b'']:
            for status in [200,401,403,429,500]:
                r=receipt(observed_utc=CLOCK,transport='RESPONSE_RECEIVED',http_status=status,body=body)
                self.assertNotIn(SECRET,json.dumps(r))
                self.assertEqual(set(r),{'schema_version','scope','observed_utc_as_supplied','clock_independently_verified','classification','http_status_as_supplied','quota_reason_verified','collection_success_verified','source_validation_verified','persistence_verified','publication_verified','retry_authorized','collection_enabled','execution_ready','training_ready'})

    def test_float_overflow_at_every_depth(self):
        for token in [b'1e999', b'-1e999']:
            for raw in [token,b'{"x":'+token+b'}',b'{"nested":{"value":'+token+b'}}']:
                self.assertEqual(run(raw),'INVALID_OR_AMBIGUOUS_JSON')
            raw=json.dumps(candidate()).encode().replace(b'"1"',token)
            self.assertEqual(run(raw),'INVALID_OR_AMBIGUOUS_JSON')
