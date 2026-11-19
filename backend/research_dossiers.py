"""Publish reviewed documentary context; never score, forecast or qualify a trade."""
import argparse
from pathlib import Path

from research_readiness import BASE, SNAPSHOTS, _read_pin, sha
from research_scanner import digest, encoded, pointer

REVIEW_ID = 'documentary-dossiers-v1'
REVIEW = {
 "research-88f4fe3fecb3853d4c6596aa": (
   "Capital-allocation flexibility: the board authorized up to US$2 billion of common-stock repurchases on November 18, excluding related fees.",
   "The authorization requires no purchase quantity, has no expiry and can be suspended or discontinued. No completed purchases or spending were reported in this filing.",
   "Actual execution, cash used, authenticated first-public time and market effect are not established. A repeat metadata observation does not establish novelty.",
   "Check subsequent issuer repurchase tables and cash-flow disclosures. Reported suspension or explicitly zero purchases in a defined period would weaken an execution hypothesis; silence would not.",
 ),
 "research-579cbc6379374c3e15ecc040": (
   "The 10-Q reports CAD 500,000 for a calendar-2025 IMVEXXY milestone recognized in the quarter ended September 30, 2026. Management reports that the future royalty rate itself did not change.",
   "The separate calendar-2026 milestone amount owed was reduced from CAD 1 million to approximately CAD 100,000 after historical overpayments. Management expects lower royalty revenue than in periods paid using a higher rate.",
   "Actual collections, Q4 accounting effects, realized future revenue and first-public timing are unqualified. The separate 8-K does not share the companion 10-Q clock.",
   "Reconcile Notes 8 and 14, the royalty MD&A and subsequent accounting and cash disclosures by sales year. Weaker later royalty revenue or cash collections would warrant revisiting a persistence hypothesis, not inferring a share-price effect.",
 ),
 "research-8c7136cab8d9326a1a59d2c1": (
   "The issuer's release compares reported quarterly revenue of $10,700,084 with $7,077,592; the exact ratio supports its rounded 51% figure.",
   "The comparison comes from the issuer's release, not independent reconciliation to the original 10-Q. Exact quarter starts and explicit ISO currency are not in the reviewed paragraph.",
   "Comparable accounting scope, policy changes, amendments, durability and first-public availability are unknown.",
   "Check the original quarterly statements, comparative notes and any amendments. A scope or accounting-basis mismatch would undermine the like-for-like interpretation; the reported numbers would remain a documented claim.",
 ),
 "research-7253201ee772377d2b27c59b": (
   "The same retained 10-Q reports a $107,817 narrower net loss for May–July 2025 compared with May–July 2024.",
   "Both periods were loss-making and both report zero revenue. No percentage revenue-growth inference can be made on that zero comparison base.",
   "The causes, sustainability and full accounting comparability of the historical change are not established; these are not current financial results.",
   "Compare the original statements and accounting notes with a later admissible filing. A one-off item or a noncomparable reporting basis would weaken a recurring improvement interpretation.",
 ),
 "research-7948e74920350b55c780bfa5": (
   "The issuer reports shareholder approval of its 2026 Long Term Incentive Plan. The reviewed plan summary gives a 6,500,000 common-share base for awards.",
   "Adjustments and deductions for relevant awards under the prior plan apply. The base is not shares issued, actual dilution, or a shareholder-approval percentage calculated by the system.",
   "The actual award deductions, net share reserve and subsequent issuances are unknown.",
   "Check the full plan and proxy, then compare award and issuance disclosures. Different net capacity or realized issuance would change a dilution scenario; plan approval alone cannot establish one.",
 ),
 "research-c236f672e91604559e99f903": (
   "Emerson reports completing its previously announced EUR 750 million note offering, with 4.000% coupon and 2032 maturity year.",
   "The issuer describes a previously priced financing. This is not independent settlement verification or a new pricing event; coupon is not yield.",
   "Net proceeds, existing debt retired, balance-sheet effect and first-public time are unknown.",
   "Reconcile later debt rollforwards, proceeds and uses. A difference between actual proceeds and principal, or offsetting repayments, would change any net funding interpretation.",
 ),
 "research-4c01192f934e6179415a76dc": (
   "The issuer reports exchanging Holdings notes due 2028 for a package including new Xerox Corporation notes due 2030 and Holdings common shares; this documents a later stated maturity for the replacement notes.",
   "The new notes carry a higher stated coupon (10.250% versus 5.500% on the old notes) and the package includes 3,872,062 Holdings shares. Preserve the separate issuer, guarantor and equity roles.",
   "Independent settlement, equity value, net debt change, transaction value and economic benefit are not established.",
   "Reconcile the full agreement, subsequent debt and share statements, and cash costs at the correct entity. A later maturity does not establish improved economics once higher coupon and equity consideration are accounted for.",
 ),
}


def build(root):
    root = Path(root)
    artifacts = {}
    seen = set()
    for path, size, checksum in SNAPSHOTS:
        manifest = _read_pin(root, path, size, checksum)
        if manifest['execution_ready'] is not False or manifest['training_ready'] is not False:
            raise ValueError('A non-executable ranking is required')
        pin = manifest['snapshot']
        if pin['path'] != BASE + 'snapshots/' + pin['sha256'] + '.json':
            raise ValueError('Unexpected snapshot path')
        snap = _read_pin(root, pin['path'], pin['bytes'], pin['sha256'])
        if snap['execution_ready'] is not False or snap['training_ready'] is not False:
            raise ValueError('A non-executable ranking is required')
        sources = {}
        notes = []
        for idea in snap['ideas']:
            refs = []
            for source in idea['source_records']:
                ref = source['source_ref']
                key = ref['key']
                file = snap['source_pins'][key]
                if key not in sources:
                    sources[key] = _read_pin(root, file['path'], file['bytes'], file['sha256'])
                if digest(pointer(sources[key], ref['json_pointer'])) != ref['object_sha256']:
                    raise ValueError('Documentary source record does not match rank provenance')
                refs.append({'source_id': source['id'], 'accessions': source['source_accessions'],
                             'object_sha256': ref['object_sha256'], 'json_pointer': ref['json_pointer'],
                             'path': file['path'], 'file_sha256': file['sha256']})
            if not refs:
                raise ValueError('A documentary dossier requires pinned source evidence')
            favorable, counterweight, unknowns, next_step = REVIEW[idea['id']]
            seen.add(idea['id'])
            notes.append({'thesis_id': idea['id'], 'favorable_evidence': favorable,
                          'counterweight': counterweight, 'unknowns': unknowns,
                          'investigate_or_weaken': next_step, 'sources': refs})
        raw = encoded({'schema_version': 1, 'review_id': REVIEW_ID, 'snapshot': pin, 'notes': notes})
        artifacts[BASE + 'dossiers/' + sha(raw) + '.json'] = raw
    if seen != REVIEW.keys():
        raise ValueError('The reviewed dossier scope changed')
    return artifacts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--write', action='store_true', help='create missing immutable objects')
    args = parser.parse_args()
    for name, raw in build(args.root).items():
        if args.write:
            path = args.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            try:
                with path.open('xb') as handle:
                    handle.write(raw)
            except FileExistsError:
                if path.read_bytes() != raw:
                    raise ValueError('Refusing to replace an immutable artifact: ' + name)
        print(f'{len(raw)} bytes  {name}')


if __name__ == '__main__':
    main()
