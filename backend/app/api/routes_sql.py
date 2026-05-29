from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.sql_analysis import ApiResponse, SqlAnalyzeRequest, SqlRiskCheckRequest
from app.services.sql_analyzer_service import analyze_sql, build_analysis_record
from app.services.sql_risk_service import check_sql_risk

router = APIRouter(prefix="/sql", tags=["sql"])


@router.post("/analyze", response_model=ApiResponse)
def analyze_sql_api(payload: SqlAnalyzeRequest, db: Session = Depends(get_db)) -> ApiResponse:
    result = analyze_sql(payload.raw_sql)
    record = build_analysis_record(payload.raw_sql, result)
    db.add(record)
    db.commit()
    return ApiResponse(data=result)


@router.post("/risk-check", response_model=ApiResponse)
def risk_check_api(payload: SqlRiskCheckRequest) -> ApiResponse:
    return ApiResponse(data=check_sql_risk(payload.raw_sql))
