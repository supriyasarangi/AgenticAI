# SIP Calculator

A Systematic Investment Plan (SIP) calculator: FastAPI backend, plain HTML/JS
frontend (no build step), and live inflation data from the World Bank API to
show an inflation-adjusted maturity value alongside the nominal one.

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Run

```bash
.venv/bin/uvicorn backend.main:app --reload --port 8000
```

Open http://localhost:8000/ in a browser.

## Test

```bash
.venv/bin/python -m pytest tests/ -v
```

## API

- `POST /api/calculate` — body `{monthly_investment, annual_return_rate, years, country_code, include_inflation_adjustment}` → invested amount, estimated returns, maturity value, and (if available) inflation-adjusted real values.
- `GET /api/inflation/{country_code}` — latest CPI inflation % for a country.
- `GET /api/suggested-rate/{country_code}` — a suggested "realistic" default annual return (inflation + assumed equity premium).

## MCP server

`mcp_server/inflation_mcp_server.py` exposes the same inflation/SIP logic as MCP
tools (`get_inflation_rate`, `suggest_default_return_rate`, `check_maturity_value`)
so Claude Code can query live inflation data or regression-check the SIP math
without touching the browser. Registered in `.mcp.json` and authorized in
`.claude/settings.local.json`.

Standalone smoke test (no MCP client needed):

```bash
.venv/bin/python -c "
from mcp_server.inflation_mcp_server import get_inflation_rate, suggest_default_return_rate
print(get_inflation_rate('IN'))
print(suggest_default_return_rate('IN'))
"
```

Interactive inspector:

```bash
.venv/bin/mcp dev mcp_server/inflation_mcp_server.py
```

## Dev-time subagent

`.claude/agents/backend-engineer.md` defines a Claude Code subagent scoped to
maintaining the FastAPI backend (`backend/`, `tests/`) — not the frontend or
MCP server.
