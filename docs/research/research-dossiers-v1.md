# Documentary thesis dossiers v1

The separately pinned dossiers add favorable evidence, counterpoints,
unresolved questions and concrete next checks to each frozen research thesis.
They cover the original five-idea ranking and the later seven-idea ranking.
They are research context, not directional signals, market forecasts, trading
plans, or reconstructions of what was known before prices moved.

Each overlay binds its archive exactly by path, byte count and SHA-256. Each
note binds its thesis ID in ranked order and every associated source record by
accession, file pin and canonical object SHA-256 at the ranking's JSON pointer.
The builder checks the retained files and objects offline, rather than trusting
the overlay's text or a fresh search result. Review text was independently
prepared against the retained documents, not generated from market outcomes.
The app checks the overlay's own published digest and all source identities
against the already verified ranking. A failing overlay does not remove the
ranking or readiness assessment. The original ranking and assessments, their
clocks, scoring, membership, and all source data are unchanged.

- Offline rebuild: `python backend/research_dossiers.py`. Add `--write` to
  create missing immutable artifacts; the tool refuses to overwrite conflicts.
- Check: `python -m unittest discover -s backend -p 'test_research_dossiers.py'`,
  `node web/tests-trade-ideas.js`, and `python backend/verify_public_state.py`.
