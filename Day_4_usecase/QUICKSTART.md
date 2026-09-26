# Quick Start — Phase 5 Demo UI

## Installation

```bash
# 1. Set API key
export ANTHROPIC_API_KEY="your-key-here"

# 2. Install dependencies
pip install -r requirements.txt
```

## Run the UI

```bash
streamlit run ui/app.py
```

Opens at: http://localhost:8501

## What to Try

### 1. Use Domain Selection

- Select **Therapeutic Area** (e.g., "Oncology")
- Select **Jurisdiction** (e.g., "FDA")
- Notice: Submit button is greyed out until BOTH are selected

### 2. Submit a Query

Examples:
- "What is the FDA approval status for immunotherapy in metastatic melanoma?"
- "Compare safety profiles across FDA and EMA approvals"
- "What clinical trial data supports the efficacy?"

### 3. Explore Results

**Tab 1: Synthesized Answer**
- Read the answer with inline citations [1], [2], etc.
- Click on confidence badges (🟢🟡🟠🔴) to see rationale
- Scroll to "Citation References" to see full source details
- Click URLs/DOIs to go directly to sources

**Tab 2: Agent Trace**
- Expand each node to see what changed during execution
- Notice timing for each pipeline stage
- Understand how evidence was processed

**Tab 3: Evidence Explorer**
- Filter by source type: Literature | Clinical Trials | Regulatory
- Filter by citation status: All | Cited | Uncited
- Sort by: Similarity Score | Recency
- Read full chunk text for any evidence item

## Test Integration

```bash
python test_ui_integration.py
```

Should show: "5/5 tests passed"

## Key Features

✅ **Domain Selection (R1)**
- Both therapeutic area and jurisdiction required
- No silent defaults
- Scope shown at top of results

✅ **Citations (R3)**
- Inline numbered citations [1], [2], etc.
- Reference list with exact source passages
- Clickable URLs/DOIs

✅ **Confidence Tiers (R4)**
- Per-claim badges: High (🟢), Medium (🟡), Low (🟠), Unverified (🔴)
- Human-readable rationale
- Based on explainable inputs

✅ **Evidence Inspector (R6)**
- All retrieved chunks visible
- Filterable and sortable
- Shows what was available vs. what was used

✅ **Agent Trace**
- See all 8 pipeline stages
- Understand why the answer was produced
- For R&D audiences

## Demo Mode

During Phase 0–3, the UI uses **mock data** that demonstrates all features:
- Realistic evidence chunks
- Varying confidence tiers
- Multiple citation sources
- Complete agent trace

Once backend Phase 1+ is complete, mock data is automatically replaced with real retrieval results.

## Troubleshooting

### Port 8501 already in use
```bash
streamlit run ui/app.py --server.port 8502
```

### Missing ANTHROPIC_API_KEY
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
streamlit run ui/app.py
```

### Dependencies missing
```bash
pip install -r requirements.txt --upgrade
```

## Documentation

- **Full guide:** `UI_GUIDE.md`
- **Implementation details:** `PHASE_5_IMPLEMENTATION.md`
- **Requirements:** `docs/requirements.md` (R1, R3, R4, R6)
- **Architecture:** `docs/architecture.md` (§6, §8)
- **Domain model:** `docs/domain-model.md` (therapeutic areas, jurisdictions)

## Next Steps

### For Demo
- Share link: Once multi-user mode is added (Phase 6+)
- Export results: UI can be extended to save/share reports

### For Backend Work
- Phase 1: Implement literature retrieval → UI gets real PubMed chunks
- Phase 2: Add clinical trials + regulatory → UI gets all sources
- Phase 3: Add ranking + confidence scoring → UI gets real confidence tiers
- Phase 4: Add synthesis + verification → UI gets real answers

**No UI code changes needed** — all backend phases flow into the same `orchestration/graph.run_query_pipeline()` contract.

## Architecture

```
┌─────────────────────────────────────────────┐
│   Streamlit UI (ui/app.py)                  │
│                                             │
│  - Domain selection (R1)                    │
│  - Query input                              │
│  - Result display (3 tabs)                  │
│  - Citation rendering (R3, R4)              │
│  - Evidence explorer (R6)                   │
│  - Agent trace                              │
└────────────┬────────────────────────────────┘
             │
             │ run_query_pipeline(
             │   query,
             │   therapeutic_area,
             │   jurisdiction
             │ )
             │
             ▼
┌─────────────────────────────────────────────┐
│   Backend: orchestration/graph.py           │
│                                             │
│  Phase 0: Stub (passes state through)       │
│  Phase 1: Literature retrieval              │
│  Phase 2: Multi-source retrieval            │
│  Phase 3: Ranking + confidence              │
│  Phase 4: Synthesis + verification          │
└─────────────────────────────────────────────┘
```

## Summary

| Component | Status | Lines |
|-----------|--------|-------|
| UI App | ✅ Complete | 813 |
| Backend Contract | ✅ Ready | 288 |
| Documentation | ✅ Complete | 800+ |
| Integration Tests | ✅ Pass 5/5 | 269 |

**Ready for Phase 1–4 backend work to proceed in parallel.**
