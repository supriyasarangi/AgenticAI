# Evaluation

Purpose: produce a concrete, defensible answer to "how do we know it's not making
things up" for an R&D audience. Three independent checks, run against a shared golden
set, plus one aggregate report.

## Golden set

`eval/golden_set.jsonl` — approximately 20–30 hand-curated examples, each with:
`question`, `therapeutic_area`, `jurisdiction`, `expected_source_types`,
`expected_key_facts`, `expected_citations`.

Coverage requirements:
- Every therapeutic area from [`domain-model.md`](domain-model.md) appears at least
  once.
- Every jurisdiction appears at least once.
- A few **adversarial cases** where evidence is intentionally thin or contradictory —
  these test that confidence scoring and the Verifier correctly flag low
  confidence/"Unverified" rather than the Synthesizer papering over the gap.

## Retrieval quality

`eval/retrieval_eval.py` — precision@k / recall@k against the golden set's
`expected_source_types` and expected documents, measured **per source type
separately** (literature vs. trials vs. regulatory), since retrieval difficulty
differs across them (e.g. regulatory documents are far fewer and more precisely
targeted than literature).

## Citation faithfulness / groundedness

`eval/faithfulness_eval.py` — for each generated claim, an independent LLM-judge call
(Opus 5, deliberately **separate from the pipeline's own Verifier** to avoid grading
its own homework) checks whether the cited chunk text actually entails the claim.
Reports:
- **Faithfulness rate** — % of claims judged grounded by the independent judge.
- **Hallucination rate** — % of claims with no valid/resolvable citation. This should
  be ~0% by construction (the Synthesizer's schema rejects uncited sentences — see
  [`architecture.md`](architecture.md) §5) — a non-zero rate here signals a
  schema-enforcement bug, not just a quality gap, and should be treated as a defect.

## Confidence calibration

`eval/calibration_eval.py` — buckets claims by predicted confidence tier
(High/Medium/Low) and checks, on the golden set, whether "High" claims are in fact
judged fully grounded/corroborated more often than "Low" claims: a simple reliability
diagram, not formal statistical calibration (appropriate for POC scale — see
[`non-functional.md`](non-functional.md)).

## Aggregate report

`eval/run_eval.py` runs the full pipeline over the golden set and produces one report
(JSON + printed summary) combining:
- Retrieval precision/recall per source type
- Faithfulness rate
- Hallucination rate
- Calibration buckets

This report is the artifact shown to stakeholders as evidence the system's citation
and confidence claims hold up, not just its ability to produce fluent answers.
