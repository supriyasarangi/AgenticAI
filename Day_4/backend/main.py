from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from backend.otel_setup import configure_otel
from backend.schemas import InflationInfo, SIPRequest, SIPResponse
from backend.sip_calculator import calculate_sip, inflation_adjust
from backend.worldbank_client import get_latest_inflation, suggest_default_annual_return

app = FastAPI(title="SIP Calculator")
tracer = configure_otel(app)


@app.post("/api/calculate", response_model=SIPResponse)
def calculate(request: SIPRequest) -> SIPResponse:
    core = calculate_sip(request.monthly_investment, request.annual_return_rate, request.years)
    response = SIPResponse(
        monthly_investment=request.monthly_investment,
        annual_return_rate=request.annual_return_rate,
        years=request.years,
        **core,
    )

    if request.include_inflation_adjustment:
        with tracer.start_as_current_span(
            "inflation_adjustment", attributes={"country_code": request.country_code}
        ):
            info = get_latest_inflation(request.country_code)
            response.inflation = InflationInfo(**info)
            if info.get("ok"):
                response.real_maturity_value = inflation_adjust(
                    core["maturity_value"], info["inflation_rate_pct"], request.years
                )
                response.real_estimated_returns = round(
                    response.real_maturity_value - core["invested_amount"], 2
                )

    return response


@app.get("/api/inflation/{country_code}")
def inflation(country_code: str) -> dict:
    return get_latest_inflation(country_code)


@app.get("/api/suggested-rate/{country_code}")
def suggested_rate(country_code: str, real_equity_premium_pct: float = 7.0) -> dict:
    info = get_latest_inflation(country_code)
    if not info.get("ok"):
        return info
    suggested = suggest_default_annual_return(info["inflation_rate_pct"], real_equity_premium_pct)
    return {
        **info,
        "assumed_real_premium_pct": real_equity_premium_pct,
        "suggested_annual_return_pct": suggested,
    }


app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
