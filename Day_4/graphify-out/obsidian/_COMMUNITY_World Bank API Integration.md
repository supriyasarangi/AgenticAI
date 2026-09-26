---
type: community
members: 13
---

# World Bank API Integration

**Members:** 13 nodes

## Members
- [[suggest-btn (Suggest a realistic rate)]] - code - frontend/index.html
- [[dot-claudesettings.local.json]] - document - README.md
- [[dot-mcp.json]] - code - .mcp.json
- [[dot-venvbinpython]] - code - .mcp.json
- [[Fetch the latest annual CPI inflation rate for a country from the World Bank…]] - rationale - mcp_server/inflation_mcp_server.py
- [[GET apiinflation{country_code}]] - concept - README.md
- [[GET apisuggested-rate{country_code}]] - concept - README.md
- [[README.md (SIP Calculator project)]] - document - README.md
- [[World Bank API (inflation data source)]] - concept - README.md
- [[get_inflation_rate()]] - code - mcp_server/inflation_mcp_server.py
- [[httpx]] - concept
- [[sip-inflation]] - code - .mcp.json
- [[worldbank_client.py]] - code - backend/worldbank_client.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/World_Bank_API_Integration
SORT file.name ASC
```

## Connections to other communities
- 7 edges to [[_COMMUNITY_Inflation Rate Tools]]
- 3 edges to [[_COMMUNITY_SIP Calculation Engine]]
- 2 edges to [[_COMMUNITY_Frontend UI Components]]
- 1 edge to [[_COMMUNITY_FastAPI Backend Layer]]

## Top bridge nodes
- [[worldbank_client.py]] - degree 10, connects to 3 communities
- [[README.md (SIP Calculator project)]] - degree 8, connects to 3 communities
- [[get_inflation_rate()]] - degree 5, connects to 1 community
- [[suggest-btn (Suggest a realistic rate)]] - degree 2, connects to 1 community