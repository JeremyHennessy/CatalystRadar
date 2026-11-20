import base64
import copy
import json
from pathlib import Path
import unittest

import research_abstention_journal as j
import research_server_receipt as verifier

ROOT = Path(__file__).resolve().parents[1]
RANK = '28e8b1d7b80a34de480ad03e9bdf7a5d18b65fdf5816239968f2f2fd52e6196a'
HEAD = '1' * 40
DEADLINE = '2026-11-20T21:00:00Z'
PFX = '/repos/JeremyHennessy/CatalystRadar'
RUN = 123
BRANCH = 'work/research-freeze-synthetic'
CREATED = '2026-11-20T16:00:00Z'


def blob(value):
    return verifier.hashlib.sha1(b'blob ' + str(len(value)).encode() + b'\0' + value).hexdigest()


class ResearchServerTests(unittest.TestCase):
    def setUp(self):
        snapshot = (ROOT / f'web/trade-ideas/v1/snapshots/{RANK}.json').read_bytes()
        refs = json.loads(snapshot)['source_pins']
        sources = {'coherent': (ROOT / refs['coherent']['path']).read_bytes()}
        raw, _ = j.append(
            [], expected_tip=j.ZERO, clock=lambda: '2026-11-20T15:59:00Z',
            command_id='synthetic-server-test', snapshot_raw=snapshot, snapshot_sha256=RANK,
            thesis_id='research-88f4fe3fecb3853d4c6596aa', issuer_cik='0000820318',
            accession='0001193125-26-467737', deadline_utc=DEADLINE,
            reasons=['MISSING_MARKET_DATA'], source_bytes=sources)
        self.record = raw[0]
        self.kw = dict(run_id=RUN, head_sha=HEAD, branch=BRANCH, record_sha256=j.sha(self.record),
                       expected_deadline=DEADLINE, checked_at='2026-11-20T18:00:00Z',
                       snapshot_raw=snapshot, source_bytes=sources)
        self.repo = {'id': 1457970410, 'full_name': 'JeremyHennessy/CatalystRadar', 'private': False}
        self.run = dict(id=RUN, head_sha=HEAD, head_branch=BRANCH, event='push', run_attempt=1,
                        workflow_id=418487000, path='.github/workflows/ci.yml',
                        actor={'id': 23260892}, repository=self.repo,
                        head_repository=dict(self.repo), created_at=CREATED,
                        status='completed', conclusion='success')
        self.requested = []
        self.mount()

    def mount(self):
        path = 'research/abstention-freezes/' + self.kw['record_sha256'] + '.json'
        tree = lambda n: str(n) * 40

        def entry(path, sha, kind='tree', mode='040000'):
            return dict(path=path, sha=sha, type=kind, mode=mode)

        def payload(path, data):
            return dict(type='file', path=path, encoding='base64', sha=blob(data),
                        size=len(data), content=base64.encodebytes(data).decode())

        rsha = blob(self.record)
        self.doc_path = PFX + '/contents/' + path + '?ref=' + HEAD
        self.mock = {
            PFX + f'/actions/runs/{RUN}': self.run,
            PFX + '/git/commits/' + HEAD: {'sha': HEAD, 'tree': {'sha': tree(2)}},
            self.doc_path: payload(path, self.record),
        }
        paths = {
            2: [entry('.github', tree(3)), entry('research', tree(4))],
            3: [entry('workflows', tree(5))],
            4: [entry('abstention-freezes', tree(6))],
            5: [entry('ci.yml', verifier.WORKFLOW_BLOB, 'blob', '100644')],
            6: [entry(path.rsplit('/', 1)[-1], rsha, 'blob', '100644')],
        }
        for index, items in paths.items():
            self.mock[PFX + '/git/trees/' + tree(index)] = {
                'sha': tree(index), 'truncated': False, 'tree': items}

    def verify(self, **changes):
        def fetch(k):
            self.requested.append(k)
            return self.mock[k]
        return verifier.verify(fetch=fetch, **(self.kw | changes))

    def test_exact_record_and_ci_status_separate(self):
        result = self.verify()
        self.assertEqual(result['server_created_at'], CREATED)
        self.assertEqual(result['record_git_blob_sha'], blob(self.record))
        self.assertEqual(result['record_sha256'], j.sha(self.record))
        self.assertEqual(result['decision'], 'ABSTAIN')
        self.assertTrue(result['ci_success_observed'])
        self.assertFalse(result['trading_ready'])
        self.assertFalse(result['outcome_qualified'])
        self.assertIn(self.doc_path, self.requested)
        self.run.update(status='in_progress', conclusion=None)
        self.assertFalse(self.verify()['ci_success_observed'])

    def test_wrong_branch_actor_repo_event_run_attempt_and_workflow(self):
        original = copy.deepcopy(self.run)
        for k, v in [('id', True), ('actor', {'id': 1}), ('head_branch', 'main'),
                     ('head_sha', 'a'*40), ('event', 'pull_request'), ('event', 'workflow_dispatch'),
                     ('run_attempt', 2), ('workflow_id', '418487000'), ('path', 'other.yml'),
                     ('head_repository', dict(self.repo, id=1)),
                     ('repository', dict(self.repo, private=True))]:
            with self.subTest(key=k, value=v):
                self.run.clear()
                self.run.update(original | {k: v})
                with self.assertRaises(ValueError):
                    self.verify()

    def test_late_future_self_reported_clocks_and_altered_cutoff(self):
        for created in (DEADLINE, '2026-11-20T15:58:59Z', '2026-11-20T19:01:00Z',
                        '2026-11-20T16:00:00+00:00'):
            with self.subTest(created=created):
                self.run['created_at'] = created
                with self.assertRaises(ValueError):
                    self.verify()
        self.run['created_at'] = CREATED
        with self.assertRaises(ValueError):
            self.verify(expected_deadline='2026-11-23T21:00:00Z')

    def test_altered_git_tree_shape_and_nonregular_file(self):
        tree = self.mock[PFX + '/git/trees/' + '6'*40]
        for k, v in [('truncated', True), ('sha', 'a'*40)]:
            old = tree[k]
            tree[k] = v
            with self.assertRaises(ValueError):
                self.verify()
            tree[k] = old
        tree['tree'][0]['mode'] = '120000'
        with self.assertRaises(ValueError):
            self.verify()

    def test_workflow_pin_and_wrong_bytes_rejected(self):
        tree = self.mock[PFX + '/git/trees/' + '5'*40]
        tree['tree'][0]['sha'] = 'a'*40
        with self.assertRaisesRegex(ValueError, 'unreviewed GitHub workflow'):
            self.verify()
        tree['tree'][0]['sha'] = verifier.WORKFLOW_BLOB
        self.mock[self.doc_path]['content'] = 'bad base64!'
        with self.assertRaises(ValueError):
            self.verify()

    def test_rebuilt_source_evidence_not_just_internal_chain(self):
        record = json.loads(self.record)
        record['command']['audit']['decisions_sha256'] = 'e'*64
        record['command_sha256'] = j.digest(record['command'])
        record['sha256'] = j.digest({k: v for k, v in record.items() if k != 'sha256'})
        self.record = j.encoded(record)
        self.kw['record_sha256'] = j.sha(self.record)
        self.mount()
        with self.assertRaisesRegex(ValueError, 'pinned research evidence'):
            self.verify()

    def test_unauthorized_ref_and_read_failure(self):
        for args in ({'branch': 'main'}, {'run_id': True}, {'record_sha256': '../secrets'}):
            with self.assertRaises(ValueError):
                self.verify(**args)
        self.assertEqual(self.requested, [])
        self.mock.pop(self.doc_path)
        with self.assertRaises(KeyError):
            self.verify()
