# Graph Report - Day_4  (2026-09-19)

## Corpus Check
- Corpus is ~1,950 words - fits in a single context window. You may not need a graph.

## Summary
- 66 nodes · 122 edges · 6 communities (5 shown, 1 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 15 edges (avg confidence: 0.88)
- Token cost: 73,343 input · 0 output

## Community Hubs (Navigation)
- Inflation Rate Tools
- World Bank API Integration
- FastAPI Backend Layer
- SIP Calculation Engine
- Frontend UI Components

## God Nodes (most connected - your core abstractions)
1. `calculate_sip()` - 11 edges
2. `get_latest_inflation()` - 10 edges
3. `backend-engineer Subagent` - 9 edges
4. `calculate()` - 8 edges
5. `inflation_adjust()` - 8 edges
6. `README.md (SIP Calculator project)` - 8 edges
7. `frontend/index.html (SIP Calculator page)` - 8 edges
8. `suggest_default_annual_return()` - 6 edges
9. `check_maturity_value()` - 6 edges
10. `get_inflation_rate()` - 5 edges

## Surprising Connections (you probably didn't know these)
- `backend-engineer Subagent` --references--> `calculate_sip()`  [EXTRACTED]
  .claude/agents/backend-engineer.md → backend/sip_calculator.py
- `get_inflation_rate()` --references--> `World Bank API (inflation data source)`  [EXTRACTED]
  mcp_server/inflation_mcp_server.py → README.md
- `check_maturity_value()` --shares_data_with--> `calculate_sip()`  [EXTRACTED]
  mcp_server/inflation_mcp_server.py → backend/sip_calculator.py
- `test_normal_case()` --calls--> `calculate_sip()`  [EXTRACTED]
  tests/test_sip_calculator.py → backend/sip_calculator.py
- `test_short_duration()` --calls--> `calculate_sip()`  [EXTRACTED]
  tests/test_sip_calculator.py → backend/sip_calculator.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **SIP Maturity Calculation Flow (UI, Backend, MCP)** — frontend_index_sip_form, backend_main, backend_sip_calculator_calculate_sip, mcp_server_inflation_mcp_server_check_maturity_value [INFERRED 0.75]
- **World Bank Inflation Data Access Pattern** — backend_worldbank_client, readme_world_bank_api, mcp_server_inflation_mcp_server_get_inflation_rate, mcp_server_inflation_mcp_server_suggest_default_return_rate [INFERRED 0.75]
- **backend-engineer Subagent Ownership Scope** — claude_agents_backend_engineer_subagent, backend_main, backend_worldbank_client, backend_schemas, backend_sip_calculator_calculate_sip, tests_test_sip_calculator [EXTRACTED 1.00]

## Communities (6 total, 1 thin omitted)

### Community 0 - "Inflation Rate Tools"
Cohesion: 0.17
Nodes (15): inflation(), suggested_rate(), get_latest_inflation(), Rough heuristic: nominal SIP return default = latest inflation + an assumed…, Fetch the most recent annual CPI inflation % for a country from the World Bank…, suggest_default_annual_return(), get, check_maturity_value() (+7 more)

### Community 1 - "World Bank API Integration"
Cohesion: 0.18
Nodes (11): .claude/settings.local.json, #suggest-btn (Suggest a realistic rate), httpx, .venv/bin/python, sip-inflation, get_inflation_rate(), Fetch the latest annual CPI inflation rate for a country from the World Bank…, README.md (SIP Calculator project) (+3 more)

### Community 2 - "FastAPI Backend Layer"
Cohesion: 0.29
Nodes (10): calculate(), InflationInfo, SIPRequest, SIPResponse, BaseModel, fastapi, fastapi_staticfiles, post (+2 more)

### Community 3 - "SIP Calculation Engine"
Cohesion: 0.29
Nodes (9): calculate_sip(), inflation_adjust(), Standard SIP compound-interest formula. M = P x ({[1 + i]^n - 1} / i) x (1 +…, Deflate a future nominal value to today's purchasing power., backend-engineer Subagent, test_inflation_adjust(), test_normal_case(), test_short_duration() (+1 more)

### Community 4 - "Frontend UI Components"
Cohesion: 0.18
Nodes (10): form, suggestBtn, suggestCaption, frontend/index.html (SIP Calculator page), #inflation-block, #inflation-unavailable fallback message, #results section, #sip-form (+2 more)

## Knowledge Gaps
- **6 isolated node(s):** `.venv/bin/python`, `form`, `suggestBtn`, `suggestCaption`, `.claude/settings.local.json` (+1 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 24 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `backend-engineer Subagent` connect `SIP Calculation Engine` to `Inflation Rate Tools`, `World Bank API Integration`, `FastAPI Backend Layer`, `Frontend UI Components`?**
  _High betweenness centrality (0.227) - this node is a cross-community bridge._
- **Why does `frontend/index.html (SIP Calculator page)` connect `Frontend UI Components` to `World Bank API Integration`, `SIP Calculation Engine`?**
  _High betweenness centrality (0.202) - this node is a cross-community bridge._
- **Why does `README.md (SIP Calculator project)` connect `World Bank API Integration` to `Inflation Rate Tools`, `SIP Calculation Engine`, `Frontend UI Components`?**
  _High betweenness centrality (0.147) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `calculate()` (e.g. with `InflationInfo` and `SIPRequest`) actually correct?**
  _`calculate()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `.venv/bin/python`, `form`, `suggestBtn` to the rest of the system?**
  _6 weakly-connected nodes found - possible documentation gaps or missing edges._