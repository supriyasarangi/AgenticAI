from typing import Optional

from pydantic import BaseModel, Field


class SIPRequest(BaseModel):
    monthly_investment: float = Field(..., gt=0)
    annual_return_rate: float = Field(..., ge=0, le=100)
    years: float = Field(..., gt=0, le=60)
    country_code: str = Field("IN", min_length=2, max_length=3)
    include_inflation_adjustment: bool = True


class InflationInfo(BaseModel):
    ok: bool
    country_code: str
    year: Optional[int] = None
    inflation_rate_pct: Optional[float] = None
    error: Optional[str] = None


class SIPResponse(BaseModel):
    monthly_investment: float
    annual_return_rate: float
    years: float
    months: int
    invested_amount: float
    estimated_returns: float
    maturity_value: float
    inflation: Optional[InflationInfo] = None
    real_maturity_value: Optional[float] = None
    real_estimated_returns: Optional[float] = None
