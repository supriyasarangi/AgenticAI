---
source_file: "backend/main.py"
type: "code"
community: "FastAPI Backend Layer"
location: "L12"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/FastAPI_Backend_Layer
---

# calculate()

## Connections
- [[InflationInfo]] - `uses` [INFERRED]
- [[SIPRequest]] - `uses` [INFERRED]
- [[SIPResponse]] - `uses` [INFERRED]
- [[calculate_sip()]] - `calls` [EXTRACTED]
- [[get_latest_inflation()]] - `calls` [EXTRACTED]
- [[inflation_adjust()]] - `calls` [EXTRACTED]
- [[main.py]] - `contains` [EXTRACTED]
- [[post]] - `references` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/FastAPI_Backend_Layer