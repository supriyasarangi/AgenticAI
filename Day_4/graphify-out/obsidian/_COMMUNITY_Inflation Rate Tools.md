---
type: community
members: 16
---

# Inflation Rate Tools

**Members:** 16 nodes

## Members
- [[Fetch the most recent annual CPI inflation % for a country from the World Bank…]] - rationale - backend/worldbank_client.py
- [[Independently recompute SIP maturity value (and inflation-adjusted 'real'…]] - rationale - mcp_server/inflation_mcp_server.py
- [[Rough heuristic nominal SIP return default = latest inflation + an assumed…]] - rationale - backend/worldbank_client.py
- [[Suggest a realistic nominal annual SIP return default for a country, computed…]] - rationale - mcp_server/inflation_mcp_server.py
- [[check_maturity_value()]] - code - mcp_server/inflation_mcp_server.py
- [[get]] - code
- [[get_latest_inflation()]] - code - backend/worldbank_client.py
- [[inflation()]] - code - backend/main.py
- [[inflation_mcp_server.py]] - code - mcp_server/inflation_mcp_server.py
- [[mcp_server_mcpserver]] - concept
- [[pathlib]] - concept
- [[suggest_default_annual_return()]] - code - backend/worldbank_client.py
- [[suggest_default_return_rate()]] - code - mcp_server/inflation_mcp_server.py
- [[suggested_rate()]] - code - backend/main.py
- [[sys]] - concept
- [[tool]] - code

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Inflation_Rate_Tools
SORT file.name ASC
```

## Connections to other communities
- 7 edges to [[_COMMUNITY_World Bank API Integration]]
- 7 edges to [[_COMMUNITY_SIP Calculation Engine]]
- 5 edges to [[_COMMUNITY_FastAPI Backend Layer]]

## Top bridge nodes
- [[inflation_mcp_server.py]] - degree 15, connects to 2 communities
- [[get_latest_inflation()]] - degree 10, connects to 2 communities
- [[suggest_default_annual_return()]] - degree 6, connects to 2 communities
- [[check_maturity_value()]] - degree 6, connects to 1 community
- [[suggested_rate()]] - degree 4, connects to 1 community