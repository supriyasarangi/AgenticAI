---
type: community
members: 12
---

# SIP Calculation Engine

**Members:** 12 nodes

## Members
- [[Deflate a future nominal value to today's purchasing power.]] - rationale - backend/sip_calculator.py
- [[Standard SIP compound-interest formula. M = P x ({1 + in - 1}  i) x (1 +…]] - rationale - backend/sip_calculator.py
- [[backend-engineer Subagent]] - document - .claude/agents/backend-engineer.md
- [[calculate_sip()]] - code - backend/sip_calculator.py
- [[inflation_adjust()]] - code - backend/sip_calculator.py
- [[requirements.txt]] - document - requirements.txt
- [[sip_calculator.py]] - code - backend/sip_calculator.py
- [[test_inflation_adjust()]] - code - tests/test_sip_calculator.py
- [[test_normal_case()]] - code - tests/test_sip_calculator.py
- [[test_short_duration()]] - code - tests/test_sip_calculator.py
- [[test_sip_calculator.py]] - code - tests/test_sip_calculator.py
- [[test_zero_return_rate()]] - code - tests/test_sip_calculator.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/SIP_Calculation_Engine
SORT file.name ASC
```

## Connections to other communities
- 8 edges to [[_COMMUNITY_FastAPI Backend Layer]]
- 7 edges to [[_COMMUNITY_Inflation Rate Tools]]
- 3 edges to [[_COMMUNITY_World Bank API Integration]]
- 1 edge to [[_COMMUNITY_Frontend UI Components]]

## Top bridge nodes
- [[backend-engineer Subagent]] - degree 9, connects to 4 communities
- [[requirements.txt]] - degree 5, connects to 3 communities
- [[calculate_sip()]] - degree 11, connects to 2 communities
- [[inflation_adjust()]] - degree 8, connects to 2 communities
- [[sip_calculator.py]] - degree 5, connects to 2 communities