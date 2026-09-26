def calculate_sip(monthly_investment: float, annual_return_rate: float, years: float) -> dict:
    """Standard SIP compound-interest formula.

    M = P x ({[1 + i]^n - 1} / i) x (1 + i), where P = monthly investment,
    i = monthly rate = annual_rate / 12 / 100, n = number of months.
    """
    months = round(years * 12)
    invested_amount = monthly_investment * months
    if annual_return_rate == 0:
        maturity_value = invested_amount
    else:
        i = annual_return_rate / 12 / 100
        maturity_value = monthly_investment * (((1 + i) ** months - 1) / i) * (1 + i)
    estimated_returns = maturity_value - invested_amount
    return {
        "months": months,
        "invested_amount": round(invested_amount, 2),
        "estimated_returns": round(estimated_returns, 2),
        "maturity_value": round(maturity_value, 2),
    }


def inflation_adjust(nominal_value: float, inflation_rate_pct: float, years: float) -> float:
    """Deflate a future nominal value to today's purchasing power."""
    return round(nominal_value / ((1 + inflation_rate_pct / 100) ** years), 2)
