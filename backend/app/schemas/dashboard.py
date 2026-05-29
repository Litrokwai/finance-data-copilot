from pydantic import BaseModel


class DashboardSummary(BaseModel):
    total_analysis_count: int
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    recent_analysis_count: int
    trend: list[dict[str, int | str]]
