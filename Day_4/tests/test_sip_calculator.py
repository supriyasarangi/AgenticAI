from backend.sip_calculator import calculate_sip, inflation_adjust


def test_normal_case():
    result = calculate_sip(monthly_investment=5000, annual_return_rate=12, years=10)
    assert result["months"] == 120
    assert result["invested_amount"] == 600000.0
    assert result["maturity_value"] > result["invested_amount"]
    assert result["estimated_returns"] == round(result["maturity_value"] - result["invested_amount"], 2)


def test_zero_return_rate():
    result = calculate_sip(monthly_investment=1000, annual_return_rate=0, years=5)
    assert result["invested_amount"] == 60000.0
    assert result["maturity_value"] == 60000.0
    assert result["estimated_returns"] == 0.0


def test_short_duration():
    result = calculate_sip(monthly_investment=1000, annual_return_rate=12, years=1 / 12)
    assert result["months"] == 1
    assert result["invested_amount"] == 1000.0
    assert result["maturity_value"] > result["invested_amount"]


def test_inflation_adjust():
    real_value = inflation_adjust(nominal_value=100000, inflation_rate_pct=5, years=10)
    assert real_value < 100000
    assert real_value == round(100000 / (1.05 ** 10), 2)
