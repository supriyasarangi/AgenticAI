# Intent

## Problem

R&D teams researching a drug, target, or indication need to pull together evidence from
fragmented, heterogeneous sources — peer-reviewed literature, preprints, clinical trial
registries, and regulatory documents from multiple jurisdictions. Today this is manual:
a researcher runs separate searches on PubMed, ClinicalTrials.gov, and agency websites,
reads dozens of documents, and manually judges which findings are trustworthy and how
they relate to each other. Two failure modes recur:

1. **Wrong or incomplete evidence** — a relevant regulatory precedent or trial result is
   missed because it lived in a source the researcher didn't think to check, or wasn't
   scoped to the right jurisdiction/therapeutic area.
2. **Unverifiable claims** — a summary asserts something ("Drug X showed a 30% reduction
   in Y") without a clear, checkable link back to the exact sentence in the exact source
   document that supports it. When a claim can't be traced, it can't be trusted for
   R&D decision-making, and it certainly can't be cited in an internal report or
   regulatory submission.

## What we're building

An **agentic RAG system** that lets an R&D user scope a question to a **therapeutic area**
and a **regulatory jurisdiction**, retrieves evidence from literature, clinical trials, and
regulatory sources within that scope, and returns an answer where:

- Every claim is broken out and **cited to an exact source passage** (document, exact span,
  URL/DOI/registry ID).
- Every claim carries a **judged, explainable confidence level** (not just an LLM's
  say-so) based on source authority, corroboration across independent sources, recency,
  and an independent verification check.
- The user can **inspect the underlying evidence** behind any claim, not just the
  synthesized answer.

This is the core value proposition: *find the right evidence, judge confidence in it,
and trace every claim to its source.*

## Who it's for

R&D scientists and medical/regulatory affairs staff doing literature review and early
drug-discovery intelligence work — people who need to move faster than manual
multi-source search allows, but cannot accept unsourced or overconfident claims.

## What "done" looks like for this POC

A local, runnable demo where a user:
1. Picks a therapeutic area (e.g. oncology) and a jurisdiction (e.g. FDA).
2. Asks a question in natural language.
3. Gets back an answer whose every sentence is citation-backed, with a confidence tier
   and rationale per claim, and can click through to the underlying evidence chunk.
4. Can see a small evaluation report showing the system's retrieval quality, citation
   faithfulness, and confidence calibration on a hand-built golden set — i.e. proof the
   system doesn't fabricate.

## Explicit non-goals (for this phase)

- **Not production-grade.** No auth, no multi-tenancy, no cloud deployment, no
  horizontal scaling. See [`non-functional.md`](non-functional.md).
- **Not a regulatory-submission tool.** Outputs support internal R&D research; they are
  not formatted or validated for submission to any agency.
- **Not exhaustive source coverage on day one.** EMA/ICH/PMDA/MHRA connectors start as
  small curated seed sets (no clean public APIs for most of these), not full crawlers.
  See [`units-of-work.md`](units-of-work.md) Phase 6.
- **Not a general-purpose chatbot.** Every query must be domain-scoped; the system is not
  designed to answer open-ended questions outside the therapeutic-area/jurisdiction model.
