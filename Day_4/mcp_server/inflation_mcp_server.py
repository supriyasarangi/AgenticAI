import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root, so `backend` is importable

from mcp.server.mcpserver import MCPServer

from backend.sip_calculator import calculate_sip, inflation_adjust
from backend.worldbank_client import get_latest_inflation, suggest_default_annual_return

mcp = MCPServer("sip-inflation")


@mcp.tool()
def get_inflation_rate(country_code: str = "IN") -> dict:
    """Fetch the latest annual CPI inflation rate for a country from the World Bank API.

    Read-only, no side effects. Use this to check what real-world inflation currently
    is for a given ISO country code (e.g. IN, US, GB) before deciding on assumptions
    for the SIP calculator's UI defaults or documentation.
    """
    return get_latest_inflation(country_code)


@mcp.tool()
def suggest_default_return_rate(country_code: str = "IN", real_equity_premium_pct: float = 7.0) -> dict:
    """Suggest a realistic nominal annual SIP return default for a country, computed as
    latest CPI inflation + an assumed long-run real equity premium (default 7%).

    This is a rough heuristic for populating a UI default, not investment advice.
    """
    info = get_latest_inflation(country_code)
    if not info.get("ok"):
        return info
    suggested = suggest_default_annual_return(info["inflation_rate_pct"], real_equity_premium_pct)
    return {
        **info,
        "assumed_real_premium_pct": real_equity_premium_pct,
        "suggested_nominal_annual_return_pct": suggested,
    }


@mcp.tool()
def check_maturity_value(
    monthly_investment: float,
    annual_return_rate_pct: float,
    years: float,
    country_code: str = "IN",
) -> dict:
    """Independently recompute SIP maturity value (and inflation-adjusted 'real' value)
    for the given inputs, using the same math as the running web app. Use this to
    spot-check or regression-test the FastAPI /api/calculate endpoint's numbers without
    needing to curl or open the browser.
    """
    core = calculate_sip(monthly_investment, annual_return_rate_pct, years)
    info = get_latest_inflation(country_code)
    if info.get("ok"):
        core["real_maturity_value"] = inflation_adjust(core["maturity_value"], info["inflation_rate_pct"], years)
        core["inflation_used"] = info
    return {"ok": True, **core}


if __name__ == "__main__":
    mcp.run()
