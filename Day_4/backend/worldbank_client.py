import httpx

WORLD_BANK_BASE = "https://api.worldbank.org/v2"
INFLATION_INDICATOR = "FP.CPI.TOTL.ZG"  # inflation, consumer prices, annual %


def get_latest_inflation(country_code: str = "IN") -> dict:
    """Fetch the most recent annual CPI inflation % for a country from the World Bank API.

    Returns {"ok": True, "country_code", "year", "inflation_rate_pct"} on success,
    or {"ok": False, "error", "country_code"} on any failure (network, no data, etc.).
    Never raises - always returns a dict so callers can degrade gracefully.
    """
    url = f"{WORLD_BANK_BASE}/country/{country_code}/indicator/{INFLATION_INDICATOR}"
    try:
        resp = httpx.get(url, params={"format": "json", "per_page": 20}, timeout=5.0)
        resp.raise_for_status()
        payload = resp.json()
        if not isinstance(payload, list) or len(payload) < 2 or not payload[1]:
            return {"ok": False, "error": "NO_DATA", "country_code": country_code}
        records = sorted(
            (r for r in payload[1] if r.get("value") is not None),
            key=lambda r: int(r["date"]),
            reverse=True,
        )
        if not records:
            return {"ok": False, "error": "NO_NON_NULL_VALUE", "country_code": country_code}
        latest = records[0]
        return {
            "ok": True,
            "country_code": country_code,
            "year": int(latest["date"]),
            "inflation_rate_pct": round(float(latest["value"]), 2),
        }
    except httpx.HTTPError as exc:
        return {"ok": False, "error": f"HTTP_ERROR: {exc}", "country_code": country_code}


def suggest_default_annual_return(inflation_rate_pct: float, real_equity_premium_pct: float = 7.0) -> float:
    """Rough heuristic: nominal SIP return default = latest inflation + an assumed
    long-run real equity premium (default 7%). This is a UI-default suggestion,
    not investment advice.
    """
    return round(inflation_rate_pct + real_equity_premium_pct, 2)
